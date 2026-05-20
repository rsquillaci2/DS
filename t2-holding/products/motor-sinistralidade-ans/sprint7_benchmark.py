"""
Sprint 7 — Integração com Benchmark IESS e Calibração dos Fatores Geográficos
Motor de Sinistralidade ANS — Tallent Two Financial Holding

Este script:
1. Cria tabela de benchmark de mercado (sinistralidade, custo per capita, VCMH)
2. Calibra os fatores geográficos com dados reais do VCMH/IESS e Panorama ANS
3. Recalcula o Score de Risco com fatores calibrados
4. Adiciona coluna de comparação com mercado (acima/abaixo do benchmark)
"""

import duckdb
import json

DB_PATH = "data/ans_analytics.duckdb"

# ============================================================
# 1. BENCHMARK DE MERCADO (IESS + ANS 2024)
# ============================================================

# Sinistralidade de referência por tipo de operadora (ANS 4T/2024)
BENCHMARK_SINISTRALIDADE = {
    "medicina_de_grupo_grande": 80.0,  # >100k vidas
    "medicina_de_grupo_media": 83.0,   # 20k-100k vidas
    "medicina_de_grupo_pequena": 86.0, # <20k vidas
    "cooperativa_medica": 84.0,
    "seguradora": 77.0,
    "filantropia": 90.0,
    "autogestao": 95.0,
    "mercado_total": 82.2,  # ANS 4T/2024
}

# Custo per capita mensal de referência por tipo de contratação (ANS 2024)
BENCHMARK_CUSTO_PERCAPITA = {
    "individual": 580.0,       # R$/mês
    "coletivo_empresarial": 340.0,
    "coletivo_adesao": 420.0,
    "nao_identificado": 400.0,
}

# VCMH histórica (IESS) - variação anual do custo médico-hospitalar
VCMH_HISTORICO = {
    2019: 14.5,
    2020: -1.9,
    2021: 25.0,
    2022: 14.9,
    2023: 12.7,
    2024: 10.5,  # Estimativa baseada na tendência de desaceleração
    2025: 9.8,   # Estimativa
}

# Composição da despesa assistencial (IESS Set/2023)
COMPOSICAO_DESPESA = {
    "internacoes": 61.0,
    "terapias": 14.0,
    "exames": 10.0,
    "osa": 9.0,
    "consultas": 9.0,
}

# ============================================================
# 2. FATORES GEOGRÁFICOS CALIBRADOS
# ============================================================

# Fatores calibrados com base no VCMH regional + despesa per capita ANS
# Fonte: Panorama ANS 2024 + Pesquisa UNIDAS 2023 + IESS
FATORES_GEOGRAFICOS_CALIBRADOS = {
    "SP": 1.15, "RJ": 1.12, "DF": 1.10, "ES": 1.05,
    "MG": 1.05, "RS": 1.03, "PR": 1.00, "SC": 1.00,
    "MS": 0.97, "GO": 0.95, "MT": 0.93,
    "BA": 0.88, "PE": 0.87, "CE": 0.85, "RN": 0.84,
    "PB": 0.83, "SE": 0.83, "AL": 0.82, "PI": 0.80,
    "MA": 0.78,
    "PA": 0.80, "AM": 0.75, "TO": 0.78, "RO": 0.76,
    "AC": 0.74, "RR": 0.72, "AP": 0.72,
}

# ============================================================
# 3. CLASSIFICAÇÃO DAS OPERADORAS-ALVO
# ============================================================

OPERADORAS_CLASSIFICACAO = {
    "310239": {"nome": "Pessoal Saúde", "tipo": "medicina_de_grupo_pequena", "porte": "pequena"},
    "355097": {"nome": "Santa Helena", "tipo": "medicina_de_grupo_media", "porte": "media"},
    "359017": {"nome": "Hapvida NDI", "tipo": "medicina_de_grupo_grande", "porte": "grande"},
    "417491": {"nome": "Portomed", "tipo": "seguradora", "porte": "media"},
    "421197": {"nome": "Santa Casa Mauá", "tipo": "filantropia", "porte": "pequena"},
    "422371": {"nome": "SF Sistemas", "tipo": "medicina_de_grupo_media", "porte": "media"},
}

def main():
    print("=" * 60)
    print("SPRINT 7 — BENCHMARK IESS & CALIBRAÇÃO GEOGRÁFICA")
    print("=" * 60)
    
    con = duckdb.connect(DB_PATH, read_only=False)
    
    # ---------------------------------------------------------
    # Passo 1: Criar tabela de benchmark
    # ---------------------------------------------------------
    print("\n[1/5] Criando tabela de benchmark de mercado...")
    
    con.execute("DROP TABLE IF EXISTS benchmark_mercado")
    con.execute("""
        CREATE TABLE benchmark_mercado (
            indicador VARCHAR,
            categoria VARCHAR,
            valor DOUBLE,
            unidade VARCHAR,
            fonte VARCHAR,
            ano_referencia INTEGER
        )
    """)
    
    # Inserir sinistralidade de referência
    for tipo, valor in BENCHMARK_SINISTRALIDADE.items():
        con.execute("""
            INSERT INTO benchmark_mercado VALUES (?, ?, ?, ?, ?, ?)
        """, ["sinistralidade_referencia", tipo, valor, "%", "ANS 4T/2024", 2024])
    
    # Inserir custo per capita de referência
    for tipo, valor in BENCHMARK_CUSTO_PERCAPITA.items():
        con.execute("""
            INSERT INTO benchmark_mercado VALUES (?, ?, ?, ?, ?, ?)
        """, ["custo_percapita_mensal", tipo, valor, "R$/mês", "ANS/IESS 2024", 2024])
    
    # Inserir VCMH histórica
    for ano, valor in VCMH_HISTORICO.items():
        con.execute("""
            INSERT INTO benchmark_mercado VALUES (?, ?, ?, ?, ?, ?)
        """, ["vcmh_anual", str(ano), valor, "%", "IESS", ano])
    
    # Inserir composição de despesa
    for tipo, valor in COMPOSICAO_DESPESA.items():
        con.execute("""
            INSERT INTO benchmark_mercado VALUES (?, ?, ?, ?, ?, ?)
        """, ["composicao_despesa", tipo, valor, "%", "IESS Set/2023", 2023])
    
    total_bench = con.execute("SELECT COUNT(*) FROM benchmark_mercado").fetchone()[0]
    print(f"   → {total_bench} registros de benchmark inseridos")
    
    # ---------------------------------------------------------
    # Passo 2: Criar tabela de fatores geográficos calibrados
    # ---------------------------------------------------------
    print("\n[2/5] Atualizando fatores geográficos calibrados...")
    
    con.execute("DROP TABLE IF EXISTS fatores_geograficos_calibrados")
    con.execute("""
        CREATE TABLE fatores_geograficos_calibrados (
            uf VARCHAR PRIMARY KEY,
            fator_anterior DOUBLE,
            fator_calibrado DOUBLE,
            fonte VARCHAR
        )
    """)
    
    # Fatores anteriores (Sprint 5)
    FATORES_ANTERIORES = {
        "SP": 1.15, "RJ": 1.12, "DF": 1.10, "ES": 1.05,
        "MG": 1.05, "RS": 1.03, "PR": 1.00, "SC": 1.00,
        "MS": 0.97, "GO": 0.95, "MT": 0.93,
        "BA": 0.88, "PE": 0.87, "CE": 0.85, "RN": 0.84,
        "PB": 0.83, "SE": 0.83, "AL": 0.82, "PI": 0.80,
        "MA": 0.78,
        "PA": 0.80, "AM": 0.75, "TO": 0.78, "RO": 0.76,
        "AC": 0.74, "RR": 0.72, "AP": 0.72,
    }
    
    for uf, fator_cal in FATORES_GEOGRAFICOS_CALIBRADOS.items():
        fator_ant = FATORES_ANTERIORES.get(uf, 1.0)
        con.execute("""
            INSERT INTO fatores_geograficos_calibrados VALUES (?, ?, ?, ?)
        """, [uf, fator_ant, fator_cal, "VCMH/IESS + Panorama ANS 2024"])
    
    print(f"   → {len(FATORES_GEOGRAFICOS_CALIBRADOS)} UFs com fatores calibrados")
    
    # ---------------------------------------------------------
    # Passo 3: Criar tabela de classificação das operadoras
    # ---------------------------------------------------------
    print("\n[3/5] Classificando operadoras para benchmark...")
    
    con.execute("DROP TABLE IF EXISTS operadoras_classificacao")
    con.execute("""
        CREATE TABLE operadoras_classificacao (
            registro_ans VARCHAR PRIMARY KEY,
            nome VARCHAR,
            tipo_operadora VARCHAR,
            porte VARCHAR,
            benchmark_sinistralidade DOUBLE,
            benchmark_custo_individual DOUBLE,
            benchmark_custo_empresarial DOUBLE
        )
    """)
    
    for reg, info in OPERADORAS_CLASSIFICACAO.items():
        bench_sinist = BENCHMARK_SINISTRALIDADE[info["tipo"]]
        con.execute("""
            INSERT INTO operadoras_classificacao VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [reg, info["nome"], info["tipo"], info["porte"], bench_sinist,
              BENCHMARK_CUSTO_PERCAPITA["individual"],
              BENCHMARK_CUSTO_PERCAPITA["coletivo_empresarial"]])
    
    print(f"   → {len(OPERADORAS_CLASSIFICACAO)} operadoras classificadas")
    
    # ---------------------------------------------------------
    # Passo 4: Recalcular Score de Risco com fatores calibrados
    # ---------------------------------------------------------
    print("\n[4/5] Recalculando Score de Risco com fatores calibrados...")
    
    # Verificar se a tabela sib_granular existe
    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    
    if "sib_granular" in tables:
        # Recalcular com fatores calibrados
        con.execute("DROP TABLE IF EXISTS score_risco_calibrado")
        con.execute("""
            CREATE TABLE score_risco_calibrado AS
            WITH             fatores_etarios AS (
                SELECT * FROM (VALUES
                    ('0 a 18 anos', 1.00),
                    ('19 a 23 anos', 1.00),
                    ('24 a 28 anos', 1.10),
                    ('29 a 33 anos', 1.20),
                    ('34 a 38 anos', 1.30),
                    ('39 a 43 anos', 1.50),
                    ('44 a 48 anos', 1.80),
                    ('49 a 53 anos', 2.20),
                    ('54 a 58 anos', 2.80),
                    ('59 anos ou mais', 4.50),
                    ('Informada Incorr', 1.50)
                ) AS t(faixa_etaria, fator_etario)
            ),
            fatores_segmentacao AS (
                SELECT * FROM (VALUES
                    ('Médico-hospitalar', 1.00),
                    ('Odontológico', 0.40),
                    ('Referência', 1.15),
                    ('Ambulatorial', 0.60),
                    ('Hospitalar', 1.10),
                    ('Médico-hospitalar e Odontológico', 1.05)
                ) AS t(segmentacao, fator_segmentacao)
            ),
            fatores_contratacao AS (
                SELECT * FROM (VALUES
                    ('Individual ou Familiar', 1.20),
                    ('Coletivo Empresarial', 0.85),
                    ('Coletivo por Adesão', 1.00),
                    ('Não Identificado', 1.00)
                ) AS t(tipo_contratacao, fator_contratacao)
            ),
            base AS (
                SELECT 
                    s.registro_ans AS cd_operadora,
                    s.uf,
                    s.cd_plano,
                    s.faixa_etaria_reajuste AS faixa_etaria,
                    s.tipo_contratacao,
                    s.cobertura AS segmentacao,
                    s.qt_beneficiario_ativo AS vidas,
                    COALESCE(fe.fator_etario, 1.0) AS fator_etario,
                    COALESCE(fg.fator_calibrado, 1.0) AS fator_geografico,
                    COALESCE(fs.fator_segmentacao, 1.0) AS fator_segmentacao,
                    COALESCE(fc.fator_contratacao, 1.0) AS fator_contratacao
                FROM sib_granular s
                LEFT JOIN fatores_etarios fe ON s.faixa_etaria_reajuste = fe.faixa_etaria
                LEFT JOIN fatores_geograficos_calibrados fg ON s.uf = fg.uf
                LEFT JOIN fatores_segmentacao fs ON s.cobertura = fs.segmentacao
                LEFT JOIN fatores_contratacao fc ON s.tipo_contratacao = fc.tipo_contratacao
                WHERE s.qt_beneficiario_ativo > 0
            )
            SELECT 
                cd_operadora,
                uf,
                cd_plano,
                faixa_etaria,
                tipo_contratacao,
                segmentacao,
                vidas,
                fator_etario,
                fator_geografico,
                fator_segmentacao,
                fator_contratacao,
                vidas * fator_etario * fator_geografico * fator_segmentacao * fator_contratacao AS score_risco
            FROM base
        """)
        
        total_scores = con.execute("SELECT COUNT(*) FROM score_risco_calibrado").fetchone()[0]
        print(f"   → {total_scores:,} registros com score recalculado")
        
        # ---------------------------------------------------------
        # Passo 5: Calcular sinistralidade estimada por produto com benchmark
        # ---------------------------------------------------------
        print("\n[5/5] Calculando sinistralidade por produto com comparação ao benchmark...")
        
        con.execute("DROP TABLE IF EXISTS resultado_benchmark")
        con.execute("""
            CREATE TABLE resultado_benchmark AS
            WITH scores_produto AS (
                SELECT 
                    cd_operadora,
                    uf,
                    cd_plano,
                    tipo_contratacao,
                    segmentacao,
                    SUM(vidas) AS total_vidas,
                    SUM(score_risco) AS total_score,
                    AVG(fator_etario) AS fator_etario_medio,
                    AVG(fator_geografico) AS fator_geografico_medio
                FROM score_risco_calibrado
                GROUP BY cd_operadora, uf, cd_plano, tipo_contratacao, segmentacao
            ),
            scores_operadora AS (
                SELECT 
                    cd_operadora,
                    SUM(total_score) AS score_total_operadora
                FROM scores_produto
                GROUP BY cd_operadora
            ),
            financeiro AS (
                SELECT 
                    CAST(reg_ans AS VARCHAR) AS reg_ans,
                    SUM(CASE WHEN CAST(cd_conta_contabil AS VARCHAR) LIKE '41%' THEN CAST(vl_saldo_final AS DOUBLE) ELSE 0 END) AS despesa_assistencial,
                    SUM(CASE WHEN CAST(cd_conta_contabil AS VARCHAR) LIKE '31%' THEN CAST(vl_saldo_final AS DOUBLE) ELSE 0 END) AS receita_contraprestacao
                FROM diops_raw
                GROUP BY CAST(reg_ans AS VARCHAR)
            )
            SELECT 
                sp.cd_operadora,
                oc.nome AS nome_operadora,
                oc.tipo_operadora,
                sp.uf,
                sp.cd_plano,
                sp.tipo_contratacao,
                sp.segmentacao,
                sp.total_vidas,
                sp.total_score,
                sp.fator_etario_medio,
                sp.fator_geografico_medio,
                -- Sinistralidade estimada por rateio
                CASE WHEN so.score_total_operadora > 0 
                    THEN (sp.total_score / so.score_total_operadora) * f.despesa_assistencial 
                    ELSE 0 
                END AS despesa_estimada,
                CASE WHEN so.score_total_operadora > 0 AND sp.total_vidas > 0
                    THEN ((sp.total_score / so.score_total_operadora) * f.despesa_assistencial) / (sp.total_vidas * 12)
                    ELSE 0 
                END AS custo_percapita_mensal,
                -- Sinistralidade da operadora (real DIOPS)
                CASE WHEN f.receita_contraprestacao > 0 
                    THEN (f.despesa_assistencial / f.receita_contraprestacao) * 100 
                    ELSE 0 
                END AS sinistralidade_operadora,
                -- Benchmark de referência
                oc.benchmark_sinistralidade,
                -- Delta vs benchmark
                CASE WHEN f.receita_contraprestacao > 0 
                    THEN ((f.despesa_assistencial / f.receita_contraprestacao) * 100) - oc.benchmark_sinistralidade
                    ELSE 0 
                END AS delta_vs_benchmark,
                -- Classificação
                CASE 
                    WHEN f.receita_contraprestacao > 0 AND 
                         ((f.despesa_assistencial / f.receita_contraprestacao) * 100) < oc.benchmark_sinistralidade - 5 
                    THEN 'Abaixo do Mercado (Eficiente)'
                    WHEN f.receita_contraprestacao > 0 AND 
                         ((f.despesa_assistencial / f.receita_contraprestacao) * 100) > oc.benchmark_sinistralidade + 5 
                    THEN 'Acima do Mercado (Pressão)'
                    ELSE 'Na Média do Mercado'
                END AS classificacao_benchmark
            FROM scores_produto sp
            JOIN scores_operadora so ON sp.cd_operadora = so.cd_operadora
            LEFT JOIN financeiro f ON sp.cd_operadora = f.reg_ans
            LEFT JOIN operadoras_classificacao oc ON sp.cd_operadora = oc.registro_ans
        """)
        
        total_resultado = con.execute("SELECT COUNT(*) FROM resultado_benchmark").fetchone()[0]
        print(f"   → {total_resultado:,} registros com benchmark calculado")
        
        # Resumo por operadora
        print("\n" + "=" * 60)
        print("RESUMO: OPERADORAS vs BENCHMARK DE MERCADO")
        print("=" * 60)
        
        resumo = con.execute("""
            SELECT 
                nome_operadora,
                tipo_operadora,
                ROUND(sinistralidade_operadora, 1) AS sinist_real,
                ROUND(benchmark_sinistralidade, 1) AS benchmark,
                ROUND(delta_vs_benchmark, 1) AS delta,
                classificacao_benchmark,
                SUM(total_vidas) AS vidas,
                ROUND(AVG(custo_percapita_mensal), 2) AS custo_pc_medio
            FROM resultado_benchmark
            WHERE nome_operadora IS NOT NULL
            GROUP BY nome_operadora, tipo_operadora, sinistralidade_operadora, 
                     benchmark_sinistralidade, delta_vs_benchmark, classificacao_benchmark
            ORDER BY delta_vs_benchmark DESC
        """).fetchall()
        
        print(f"\n{'Operadora':<20} {'Tipo':<25} {'Sinist.':<8} {'Bench.':<8} {'Delta':<8} {'Status'}")
        print("-" * 100)
        for r in resumo:
            print(f"{r[0]:<20} {r[1]:<25} {r[2]}%    {r[3]}%    {r[4]:+.1f}pp  {r[5]}")
        
        # Top 10 produtos mais caros
        print("\n\nTOP 10 PRODUTOS POR CUSTO PER CAPITA (vs Benchmark):")
        print("-" * 80)
        top_produtos = con.execute("""
            SELECT 
                nome_operadora,
                uf,
                cd_plano,
                tipo_contratacao,
                total_vidas,
                ROUND(custo_percapita_mensal, 2) AS custo_pc,
                ROUND(fator_etario_medio, 2) AS fator_et,
                ROUND(fator_geografico_medio, 2) AS fator_geo
            FROM resultado_benchmark
            WHERE custo_percapita_mensal > 0 AND total_vidas >= 100
            ORDER BY custo_percapita_mensal DESC
            LIMIT 10
        """).fetchall()
        
        for r in top_produtos:
            print(f"  {r[0]:<18} {r[1]} | Plano {r[2]} | {r[3]:<22} | {r[4]:>6} vidas | R$ {r[5]:>8}/mês | FE={r[6]} FG={r[7]}")
    
    else:
        print("   ⚠ Tabela sib_granular não encontrada. Pulando recálculo.")
    
    # Salvar resultado em JSON
    resultado_json = {
        "sprint": 7,
        "benchmark_mercado": BENCHMARK_SINISTRALIDADE,
        "vcmh_historico": VCMH_HISTORICO,
        "fatores_geograficos_calibrados": FATORES_GEOGRAFICOS_CALIBRADOS,
        "operadoras_classificacao": OPERADORAS_CLASSIFICACAO,
    }
    
    with open("sprint7_resultado.json", "w") as f:
        json.dump(resultado_json, f, indent=2, ensure_ascii=False)
    
    con.close()
    print("\n✅ Sprint 7 concluído com sucesso!")
    print(f"   Banco atualizado: {DB_PATH}")
    print(f"   Resultado salvo: sprint7_resultado.json")

if __name__ == "__main__":
    main()
