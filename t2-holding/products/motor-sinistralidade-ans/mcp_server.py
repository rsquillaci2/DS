"""
Motor de Sinistralidade ANS — MCP Server
=========================================
Expõe o Motor de Sinistralidade como servidor MCP para consulta por agentes de IA.

Tools disponíveis:
- buscar_operadora: Busca operadoras por nome ou registro ANS
- ficha_operadora: Ficha completa de uma operadora
- ranking_sinistralidade: Top N operadoras por sinistralidade
- ranking_receita: Top N operadoras por receita
- benchmark_modalidade: Benchmarks por modalidade
- serie_temporal: Série histórica trimestral
- evolucao_beneficiarios: Evolução mensal de vidas
- predicao_operadora: Predição ML do próximo trimestre
- comparar_operadoras: Comparação lado a lado
- distribuicao_mercado: Estatísticas gerais do mercado

Autor: Ricardo Squillaci — Tallent Two Financial Holding
Sprint 9 — Mai/2026
"""

import os
import json
import duckdb
from mcp.server.fastmcp import FastMCP

# ─── Configuração ────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ans_analytics.duckdb")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "operadoras_ativas.csv")

mcp = FastMCP("Motor de Sinistralidade ANS")


def get_db():
    """Retorna conexão read-only ao DuckDB."""
    return duckdb.connect(DB_PATH, read_only=True)


def resolve_nome(con, registro_ans) -> str:
    """Resolve o nome de exibição de uma operadora."""
    result = con.execute(f"""
        SELECT COALESCE(o.Nome_Fantasia, o.Razao_Social) as nome
        FROM read_csv_auto('{CSV_PATH}') o
        WHERE LPAD(CAST(? AS VARCHAR), 6, '0') = o.REGISTRO_OPERADORA
        LIMIT 1
    """, [str(registro_ans)]).fetchone()
    if result and result[0] and result[0].strip():
        return result[0].strip()
    # Fallback para operadoras_classificacao
    result = con.execute("""
        SELECT nome_operadora FROM operadoras_classificacao
        WHERE registro_ans = ? LIMIT 1
    """, [str(registro_ans)]).fetchone()
    return result[0] if result and result[0] else f"Operadora {registro_ans}"


# ─── Schema real do banco ────────────────────────────────────────────────────
# sinistralidade_operadora: registro_ans, receita_contraprestacoes, despesa_assistencial, sinistralidade_total
# sinistralidade_historica: registro_ans, trimestre, receita, despesa, sinistralidade, tipo_despesa
# resultado_benchmark: registro_ans, nome_operadora, modalidade, sinistralidade_real, receita, despesa, benchmark_modalidade, percentil_modalidade, percentil_geral, classificacao
# predicoes_xgboost: registro_ans, sinistralidade_atual, sinistralidade_predita, delta, tendencia
# sib_evolucao_temporal: registro_ans, cobertura, mes_competencia, total_beneficiarios
# operadoras_classificacao: registro_ans, nome_operadora, modalidade, uf_sede


# ─── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def buscar_operadora(termo: str) -> str:
    """Busca operadoras por nome (parcial) ou registro ANS.
    Retorna lista de operadoras encontradas com registro ANS, nome e sinistralidade.
    Use esta ferramenta primeiro para descobrir o registro_ans de uma operadora.
    
    Args:
        termo: Nome parcial da operadora ou número de registro ANS
    """
    con = get_db()
    
    try:
        if termo.strip().isdigit():
            results = con.execute(f"""
                SELECT s.registro_ans, 
                       COALESCE(o.Nome_Fantasia, o.Razao_Social, c.nome_operadora) as nome,
                       s.sinistralidade_total,
                       s.receita_contraprestacoes,
                       s.despesa_assistencial
                FROM sinistralidade_operadora s
                LEFT JOIN read_csv_auto('{CSV_PATH}') o 
                    ON LPAD(CAST(s.registro_ans AS VARCHAR), 6, '0') = o.REGISTRO_OPERADORA
                LEFT JOIN operadoras_classificacao c ON CAST(s.registro_ans AS VARCHAR) = c.registro_ans
                WHERE CAST(s.registro_ans AS VARCHAR) LIKE '%{termo.strip()}%'
                ORDER BY s.receita_contraprestacoes DESC
                LIMIT 20
            """).fetchall()
        else:
            results = con.execute(f"""
                SELECT s.registro_ans,
                       COALESCE(o.Nome_Fantasia, o.Razao_Social, c.nome_operadora) as nome,
                       s.sinistralidade_total,
                       s.receita_contraprestacoes,
                       s.despesa_assistencial
                FROM sinistralidade_operadora s
                LEFT JOIN read_csv_auto('{CSV_PATH}') o 
                    ON LPAD(CAST(s.registro_ans AS VARCHAR), 6, '0') = o.REGISTRO_OPERADORA
                LEFT JOIN operadoras_classificacao c ON CAST(s.registro_ans AS VARCHAR) = c.registro_ans
                WHERE LOWER(COALESCE(o.Nome_Fantasia, o.Razao_Social, c.nome_operadora, '')) LIKE LOWER('%{termo}%')
                ORDER BY s.receita_contraprestacoes DESC
                LIMIT 20
            """).fetchall()
        
        if not results:
            return f"Nenhuma operadora encontrada para '{termo}'."
        
        output = []
        for r in results:
            output.append({
                "registro_ans": str(r[0]),
                "nome": r[1] or f"Operadora {r[0]}",
                "sinistralidade_pct": round(r[2] * 100, 1) if r[2] else None,
                "receita_milhoes": round(r[3] / 1e6, 1) if r[3] else None,
                "despesa_milhoes": round(r[4] / 1e6, 1) if r[4] else None,
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def ficha_operadora(registro_ans: str) -> str:
    """Retorna ficha completa de uma operadora: dados financeiros, sinistralidade,
    benchmark por modalidade, posição no mercado (percentil), carteira de beneficiários
    e classificação de risco.
    
    Args:
        registro_ans: Número de registro ANS da operadora (ex: '355097')
    """
    con = get_db()
    
    try:
        fin = con.execute("""
            SELECT registro_ans, sinistralidade_total, receita_contraprestacoes, despesa_assistencial
            FROM sinistralidade_operadora
            WHERE registro_ans = ?
        """, [int(registro_ans)]).fetchone()
        
        if not fin:
            return f"Operadora {registro_ans} não encontrada na base DIOPS."
        
        nome = resolve_nome(con, registro_ans)
        
        # Benchmark
        bench = con.execute("""
            SELECT modalidade, benchmark_modalidade, classificacao, 
                   sinistralidade_real - benchmark_modalidade as delta_pp,
                   percentil_geral
            FROM resultado_benchmark
            WHERE registro_ans = ?
        """, [int(registro_ans)]).fetchone()
        
        # Percentil
        total = con.execute("SELECT COUNT(*) FROM sinistralidade_operadora").fetchone()[0]
        abaixo = con.execute("""
            SELECT COUNT(*) FROM sinistralidade_operadora 
            WHERE sinistralidade_total < ?
        """, [fin[1]]).fetchone()[0]
        percentil = round(abaixo / total * 100)
        
        # Beneficiários
        benef = con.execute("""
            SELECT SUM(total_beneficiarios) as total, MAX(mes_competencia) as ultimo_mes
            FROM sib_evolucao_temporal
            WHERE registro_ans = ?
            AND mes_competencia = (SELECT MAX(mes_competencia) FROM sib_evolucao_temporal WHERE registro_ans = ?)
        """, [int(registro_ans), int(registro_ans)]).fetchone()
        
        # Predição
        pred = con.execute("""
            SELECT sinistralidade_predita, delta, tendencia
            FROM predicoes_xgboost
            WHERE registro_ans = ?
        """, [int(registro_ans)]).fetchone()
        
        ficha = {
            "nome": nome,
            "registro_ans": registro_ans,
            "competencia": "4T/2025 (DIOPS)",
            "financeiro": {
                "receita_milhoes": round(fin[2] / 1e6, 1) if fin[2] else None,
                "despesa_assistencial_milhoes": round(fin[3] / 1e6, 1) if fin[3] else None,
                "sinistralidade_pct": round(fin[1] * 100, 1),
            },
            "posicao_mercado": {
                "percentil": percentil,
                "posicao": abaixo + 1,
                "total_operadoras": total,
                "interpretacao": "MAIOR pressão assistencial" if percentil > 70 else "MENOR pressão" if percentil < 30 else "Na média",
            },
            "benchmark": {
                "modalidade": bench[0] if bench else None,
                "referencia_pct": round(bench[1], 1) if bench else None,
                "classificacao": bench[2] if bench else None,
                "delta_pp": round(bench[3], 1) if bench else None,
                "percentil_geral": round(bench[4], 1) if bench else None,
            } if bench else None,
            "beneficiarios": {
                "total_vidas": int(benef[0]) if benef and benef[0] else None,
                "ultimo_mes": benef[1] if benef else None,
            },
            "predicao_ml": {
                "sinistralidade_predita_pct": round(pred[0], 1) if pred else None,
                "variacao_pp": round(pred[1], 1) if pred else None,
                "tendencia": pred[2] if pred else None,
            } if pred else None,
        }
        
        return json.dumps(ficha, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def ranking_sinistralidade(top_n: int = 10, ordem: str = "maior") -> str:
    """Retorna ranking de operadoras por sinistralidade.
    
    Args:
        top_n: Número de operadoras no ranking (padrão: 10, máximo: 50)
        ordem: 'maior' para as mais pressionadas, 'menor' para as mais eficientes
    """
    con = get_db()
    top_n = min(top_n, 50)
    order = "DESC" if ordem == "maior" else "ASC"
    
    try:
        results = con.execute(f"""
            SELECT s.registro_ans,
                   COALESCE(o.Nome_Fantasia, o.Razao_Social, c.nome_operadora) as nome,
                   s.sinistralidade_total,
                   s.receita_contraprestacoes,
                   s.despesa_assistencial
            FROM sinistralidade_operadora s
            LEFT JOIN read_csv_auto('{CSV_PATH}') o 
                ON LPAD(CAST(s.registro_ans AS VARCHAR), 6, '0') = o.REGISTRO_OPERADORA
            LEFT JOIN operadoras_classificacao c ON CAST(s.registro_ans AS VARCHAR) = c.registro_ans
            WHERE s.sinistralidade_total > 0
            ORDER BY s.sinistralidade_total {order}
            LIMIT {top_n}
        """).fetchall()
        
        output = []
        for i, r in enumerate(results, 1):
            output.append({
                "posicao": i,
                "registro_ans": str(r[0]),
                "nome": r[1] or f"Operadora {r[0]}",
                "sinistralidade_pct": round(r[2] * 100, 1),
                "receita_milhoes": round(r[3] / 1e6, 1) if r[3] else None,
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def ranking_receita(top_n: int = 10) -> str:
    """Retorna ranking de operadoras por volume de receita (contraprestações).
    
    Args:
        top_n: Número de operadoras no ranking (padrão: 10, máximo: 50)
    """
    con = get_db()
    top_n = min(top_n, 50)
    
    try:
        results = con.execute(f"""
            SELECT s.registro_ans,
                   COALESCE(o.Nome_Fantasia, o.Razao_Social, c.nome_operadora) as nome,
                   s.receita_contraprestacoes,
                   s.despesa_assistencial,
                   s.sinistralidade_total
            FROM sinistralidade_operadora s
            LEFT JOIN read_csv_auto('{CSV_PATH}') o 
                ON LPAD(CAST(s.registro_ans AS VARCHAR), 6, '0') = o.REGISTRO_OPERADORA
            LEFT JOIN operadoras_classificacao c ON CAST(s.registro_ans AS VARCHAR) = c.registro_ans
            ORDER BY s.receita_contraprestacoes DESC
            LIMIT {top_n}
        """).fetchall()
        
        output = []
        for i, r in enumerate(results, 1):
            output.append({
                "posicao": i,
                "registro_ans": str(r[0]),
                "nome": r[1] or f"Operadora {r[0]}",
                "receita_bilhoes": round(r[2] / 1e9, 2) if r[2] else None,
                "despesa_bilhoes": round(r[3] / 1e9, 2) if r[3] else None,
                "sinistralidade_pct": round(r[4] * 100, 1) if r[4] else None,
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def benchmark_modalidade() -> str:
    """Retorna os benchmarks de sinistralidade por modalidade de operadora.
    Mostra a referência de mercado para cada tipo (Cooperativa Médica, Medicina de Grupo, etc.)."""
    con = get_db()
    
    try:
        results = con.execute("""
            SELECT modalidade, 
                   AVG(benchmark_modalidade) as benchmark_medio,
                   COUNT(*) as operadoras,
                   AVG(sinistralidade_real) as sinistralidade_media_real
            FROM resultado_benchmark
            GROUP BY modalidade
            ORDER BY benchmark_medio DESC
        """).fetchall()
        
        output = []
        for r in results:
            output.append({
                "modalidade": r[0],
                "benchmark_referencia_pct": round(r[1] * 100, 1),
                "operadoras_na_base": r[2],
                "sinistralidade_media_real_pct": round(r[3] * 100, 1) if r[3] else None,
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def serie_temporal(registro_ans: str, ultimos_trimestres: int = 24) -> str:
    """Retorna série histórica de sinistralidade trimestral de uma operadora.
    
    Args:
        registro_ans: Número de registro ANS da operadora
        ultimos_trimestres: Quantidade de trimestres a retornar (padrão: 24)
    """
    con = get_db()
    
    try:
        nome = resolve_nome(con, registro_ans)
        results = con.execute("""
            SELECT trimestre, sinistralidade, receita, despesa
            FROM sinistralidade_historica
            WHERE registro_ans = ?
            ORDER BY trimestre DESC
            LIMIT ?
        """, [int(registro_ans), ultimos_trimestres]).fetchall()
        
        if not results:
            return f"Sem dados históricos para operadora {registro_ans} ({nome})."
        
        output = {
            "nome": nome,
            "registro_ans": registro_ans,
            "trimestres": []
        }
        for r in sorted(results, key=lambda x: x[0]):
            output["trimestres"].append({
                "trimestre": r[0],
                "sinistralidade_pct": round(r[1] * 100, 1) if r[1] else None,
                "receita_milhoes": round(r[2] / 1e6, 1) if r[2] else None,
                "despesa_milhoes": round(r[3] / 1e6, 1) if r[3] else None,
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def evolucao_beneficiarios(registro_ans: str, ultimos_meses: int = 24) -> str:
    """Retorna evolução mensal de beneficiários de uma operadora.
    
    Args:
        registro_ans: Número de registro ANS da operadora
        ultimos_meses: Quantidade de meses a retornar (padrão: 24)
    """
    con = get_db()
    
    try:
        nome = resolve_nome(con, registro_ans)
        results = con.execute("""
            SELECT mes_competencia, SUM(total_beneficiarios) as beneficiarios
            FROM sib_evolucao_temporal
            WHERE registro_ans = ?
            GROUP BY mes_competencia
            ORDER BY mes_competencia DESC
            LIMIT ?
        """, [int(registro_ans), ultimos_meses]).fetchall()
        
        if not results:
            return f"Sem dados de beneficiários para operadora {registro_ans} ({nome})."
        
        output = {
            "nome": nome,
            "registro_ans": registro_ans,
            "evolucao": []
        }
        for r in sorted(results, key=lambda x: x[0]):
            output["evolucao"].append({
                "mes": r[0],
                "beneficiarios": int(r[1]) if r[1] else 0,
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def predicao_operadora(registro_ans: str) -> str:
    """Retorna predição ML (XGBoost) de sinistralidade para o próximo trimestre.
    Inclui sinistralidade predita, variação esperada e tendência.
    
    Args:
        registro_ans: Número de registro ANS da operadora
    """
    con = get_db()
    
    try:
        nome = resolve_nome(con, registro_ans)
        pred = con.execute("""
            SELECT sinistralidade_atual, sinistralidade_predita, delta, tendencia
            FROM predicoes_xgboost
            WHERE registro_ans = ?
        """, [int(registro_ans)]).fetchone()
        
        if not pred:
            return f"Sem predição disponível para operadora {registro_ans} ({nome}). Modelo pode não ter dados suficientes."
        
        output = {
            "nome": nome,
            "registro_ans": registro_ans,
            "modelo": "XGBoost v2 (Sprint 8.5 — 761 operadoras)",
            "metricas_modelo": {
                "r2_test": 0.710,
                "mae_pp": 5.79,
                "cv_5fold": 0.734,
            },
            "predicao": {
                "sinistralidade_atual_pct": round(pred[0] * 100, 1) if pred[0] else None,
                "sinistralidade_predita_pct": round(pred[1] * 100, 1),
                "variacao_esperada_pp": round(pred[2] * 100, 1),
                "tendencia": pred[3],
            },
            "nota": "Predição baseada em tendência histórica, fator etário e modalidade. MAE de 5.79pp indica margem de erro."
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def comparar_operadoras(registros_ans: list[str]) -> str:
    """Compara múltiplas operadoras lado a lado: sinistralidade, receita, benchmark e predição.
    
    Args:
        registros_ans: Lista de registros ANS para comparar (máximo 10)
    """
    con = get_db()
    registros_ans = registros_ans[:10]
    
    try:
        output = []
        for reg in registros_ans:
            nome = resolve_nome(con, reg)
            fin = con.execute("""
                SELECT sinistralidade_total, receita_contraprestacoes, despesa_assistencial
                FROM sinistralidade_operadora WHERE registro_ans = ?
            """, [int(reg)]).fetchone()
            
            bench = con.execute("""
                SELECT modalidade, benchmark_modalidade, classificacao
                FROM resultado_benchmark WHERE registro_ans = ?
            """, [int(reg)]).fetchone()
            
            pred = con.execute("""
                SELECT sinistralidade_predita, delta, tendencia
                FROM predicoes_xgboost WHERE registro_ans = ?
            """, [int(reg)]).fetchone()
            
            benef = con.execute("""
                SELECT SUM(total_beneficiarios) FROM sib_evolucao_temporal
                WHERE registro_ans = ? 
                AND mes_competencia = (SELECT MAX(mes_competencia) FROM sib_evolucao_temporal WHERE registro_ans = ?)
            """, [int(reg), int(reg)]).fetchone()
            
            item = {
                "registro_ans": reg,
                "nome": nome,
                "sinistralidade_pct": round(fin[0] * 100, 1) if fin else None,
                "receita_milhoes": round(fin[1] / 1e6, 1) if fin and fin[1] else None,
                "beneficiarios": int(benef[0]) if benef and benef[0] else None,
                "modalidade": bench[0] if bench else None,
                "benchmark_pct": round(bench[1] * 100, 1) if bench else None,
                "classificacao": bench[2] if bench else None,
                "predicao_pct": round(pred[0] * 100, 1) if pred else None,
                "variacao_pp": round(pred[1] * 100, 1) if pred else None,
                "tendencia": pred[2] if pred else None,
            }
            output.append(item)
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


@mcp.tool()
def distribuicao_mercado() -> str:
    """Retorna estatísticas gerais do mercado de saúde suplementar:
    total de operadoras, receita total, sinistralidade média/mediana,
    distribuição por faixa e operadoras em alerta."""
    con = get_db()
    
    try:
        stats = con.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(receita_contraprestacoes) as receita_total,
                AVG(sinistralidade_total) as media,
                MEDIAN(sinistralidade_total) as mediana,
                STDDEV(sinistralidade_total) as desvio,
                SUM(CASE WHEN sinistralidade_total > 0.80 THEN 1 ELSE 0 END) as acima_80,
                SUM(CASE WHEN sinistralidade_total > 1.00 THEN 1 ELSE 0 END) as acima_100,
                SUM(CASE WHEN sinistralidade_total < 0.50 THEN 1 ELSE 0 END) as abaixo_50
            FROM sinistralidade_operadora
            WHERE sinistralidade_total > 0
        """).fetchone()
        
        por_modal = con.execute("""
            SELECT c.modalidade, 
                   COUNT(*) as qtd,
                   AVG(s.sinistralidade_total) as media_sinist,
                   SUM(s.receita_contraprestacoes) as receita_total
            FROM sinistralidade_operadora s
            JOIN operadoras_classificacao c ON CAST(s.registro_ans AS VARCHAR) = c.registro_ans
            GROUP BY c.modalidade
            ORDER BY receita_total DESC
        """).fetchall()
        
        output = {
            "competencia": "4T/2025 (DIOPS)",
            "mercado": {
                "total_operadoras": stats[0],
                "receita_total_bilhoes": round(stats[1] / 1e9, 1) if stats[1] else None,
                "sinistralidade_media_pct": round(stats[2] * 100, 1),
                "sinistralidade_mediana_pct": round(stats[3] * 100, 1),
                "desvio_padrao_pp": round(stats[4] * 100, 1),
            },
            "alertas": {
                "operadoras_acima_80_pct": int(stats[5]),
                "operadoras_acima_100_pct": int(stats[6]),
                "operadoras_abaixo_50_pct": int(stats[7]),
                "pct_em_alerta": round(stats[5] / stats[0] * 100, 1),
            },
            "por_modalidade": [
                {
                    "modalidade": r[0],
                    "operadoras": r[1],
                    "sinistralidade_media_pct": round(r[2] * 100, 1),
                    "receita_bilhoes": round(r[3] / 1e9, 1) if r[3] else None,
                }
                for r in por_modal
            ]
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    finally:
        con.close()


# ─── Resources ───────────────────────────────────────────────────────────────

@mcp.resource("sinistralidade://info")
def info_motor() -> str:
    """Informações sobre o Motor de Sinistralidade ANS."""
    return json.dumps({
        "nome": "Motor de Sinistralidade ANS",
        "versao": "3.0",
        "sprint": "9 — MCP Server",
        "autor": "Ricardo Squillaci — Tallent Two Financial Holding",
        "fontes": ["DIOPS 4T/2025", "SIB Consolidado Mar/2026", "Cadastro de Produtos ANS"],
        "operadoras_na_base": 943,
        "modelo_ml": "XGBoost v2 (R²=0.71, MAE=5.79pp)",
        "tools_disponiveis": [
            "buscar_operadora", "ficha_operadora", "ranking_sinistralidade",
            "ranking_receita", "benchmark_modalidade", "serie_temporal",
            "evolucao_beneficiarios", "predicao_operadora", "comparar_operadoras",
            "distribuicao_mercado"
        ]
    }, ensure_ascii=False, indent=2)


# ─── Prompts ─────────────────────────────────────────────────────────────────

@mcp.prompt()
def analise_operadora(nome_operadora: str) -> str:
    """Gera prompt para análise completa de uma operadora de saúde."""
    return f"""Faça uma análise completa da operadora "{nome_operadora}" usando as ferramentas do Motor de Sinistralidade ANS:

1. Use `buscar_operadora` para encontrar o registro ANS
2. Use `ficha_operadora` para obter dados financeiros e posição no mercado
3. Use `serie_temporal` para ver a tendência histórica
4. Use `evolucao_beneficiarios` para ver crescimento/retração da carteira
5. Use `predicao_operadora` para ver a projeção ML
6. Use `benchmark_modalidade` para contextualizar vs. pares

Produza um relatório executivo com:
- Resumo financeiro (receita, despesa, sinistralidade)
- Posição competitiva (percentil, benchmark)
- Tendência (melhorando ou piorando)
- Carteira (crescendo ou retraindo)
- Predição para próximo trimestre
- Recomendação (alerta, atenção ou saudável)"""


@mcp.prompt()
def comparativo_mercado(modalidade: str = "Cooperativa Médica") -> str:
    """Gera prompt para análise comparativa de um segmento do mercado."""
    return f"""Analise o segmento "{modalidade}" do mercado de saúde suplementar:

1. Use `distribuicao_mercado` para visão geral
2. Use `benchmark_modalidade` para referências
3. Use `ranking_sinistralidade` (top 10 maior e menor) para extremos
4. Use `ranking_receita` para os maiores players

Produza um relatório com:
- Tamanho do segmento (operadoras, receita, vidas)
- Sinistralidade média vs. benchmark
- Operadoras em alerta (>100%)
- Operadoras eficientes (<70%)
- Tendências e riscos do segmento"""


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
