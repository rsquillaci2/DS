"""
Sprint 5 — Score de Risco Atuarial e Rateio Financeiro
Motor de Sinistralidade ANS — Tallent Two

Calcula a sinistralidade estimada por Produto × Município × Faixa Etária
usando fatores de ponderação atuarial (etário, geográfico, segmentação, contratação).
"""

import duckdb
import pandas as pd
import numpy as np
import json
import os

DB_PATH = "/home/ubuntu/mvp_sinistralidade/data/ans_analytics.duckdb"

# =========================================================
# FATORES ATUARIAIS
# =========================================================

# Fator Etário — Curva em J (baseado em RN 63/2003 + UNIDAS 2023)
# Representa o custo relativo por faixa etária
FATOR_ETARIO = {
    "0 a 18 anos": 1.00,
    "00 a 18": 1.00,
    "0 a 18": 1.00,
    "19 a 23 anos": 0.80,
    "19 a 23": 0.80,
    "24 a 28 anos": 0.90,
    "24 a 28": 0.90,
    "29 a 33 anos": 1.00,
    "29 a 33": 1.00,
    "34 a 38 anos": 1.10,
    "34 a 38": 1.10,
    "39 a 43 anos": 1.30,
    "39 a 43": 1.30,
    "44 a 48 anos": 1.60,
    "44 a 48": 1.60,
    "49 a 53 anos": 2.00,
    "49 a 53": 2.00,
    "54 a 58 anos": 2.80,
    "54 a 58": 2.80,
    "59 anos ou mais": 4.50,
    "59 ou mais": 4.50,
    "59 ou +": 4.50,
}

# Fator Geográfico — Custo relativo por UF
# Baseado em diferenças regionais de custo de rede (DATASUS SIH + VCMH/IESS)
FATOR_GEOGRAFICO = {
    "AC": 0.75, "AL": 0.82, "AM": 0.78, "AP": 0.72,
    "BA": 0.88, "CE": 0.85, "DF": 1.12, "ES": 0.95,
    "GO": 1.00, "MA": 0.78, "MG": 0.95, "MS": 0.95,
    "MT": 0.92, "PA": 0.80, "PB": 0.82, "PE": 0.88,
    "PI": 0.78, "PR": 1.00, "RJ": 1.10, "RN": 0.85,
    "RO": 0.80, "RR": 0.72, "RS": 1.02, "SC": 1.00,
    "SE": 0.82, "SP": 1.15, "TO": 0.78,
}

# Fator de Segmentação Assistencial
FATOR_SEGMENTACAO = {
    "Odontológico": 0.40,
    "Ambulatorial": 0.70,
    "Hospitalar com obstetrícia": 0.95,
    "Hospitalar sem obstetrícia": 0.85,
    "Ambulatorial + Hospitalar com obstetrícia": 1.10,
    "Ambulatorial + Hospitalar sem obstetrícia": 1.05,
    "Referência": 1.15,
}

# Fator de Tipo de Contratação
FATOR_CONTRATACAO = {
    "Coletivo empresarial": 0.85,
    "Coletivo Empresarial": 0.85,
    "Coletivo por adesão": 0.95,
    "Coletivo por Adesão": 0.95,
    "Individual ou familiar": 1.20,
    "Individual ou Familiar": 1.20,
    "Individual": 1.20,
}


def get_fator_etario(faixa):
    """Retorna o fator etário para uma faixa, com fallback fuzzy."""
    if faixa in FATOR_ETARIO:
        return FATOR_ETARIO[faixa]
    # Fuzzy match
    faixa_lower = str(faixa).lower().strip()
    for key, val in FATOR_ETARIO.items():
        if key.lower() in faixa_lower or faixa_lower in key.lower():
            return val
    # Se contém "59" ou "mais", é a última faixa
    if "59" in str(faixa) or "mais" in str(faixa).lower() or "+" in str(faixa):
        return 4.50
    # Default: faixa média
    return 1.30


def get_fator_geografico(uf):
    """Retorna o fator geográfico para uma UF."""
    return FATOR_GEOGRAFICO.get(str(uf).upper().strip(), 1.00)


def get_fator_segmentacao(seg):
    """Retorna o fator de segmentação."""
    if seg in FATOR_SEGMENTACAO:
        return FATOR_SEGMENTACAO[seg]
    seg_lower = str(seg).lower().strip()
    for key, val in FATOR_SEGMENTACAO.items():
        if key.lower() in seg_lower or seg_lower in key.lower():
            return val
    # Defaults por keyword
    if "odonto" in seg_lower:
        return 0.40
    if "ambulat" in seg_lower and "hospit" in seg_lower:
        return 1.10
    if "ambulat" in seg_lower:
        return 0.70
    if "hospit" in seg_lower:
        return 0.90
    if "refer" in seg_lower:
        return 1.15
    return 1.00


def get_fator_contratacao(tipo):
    """Retorna o fator de contratação."""
    if tipo in FATOR_CONTRATACAO:
        return FATOR_CONTRATACAO[tipo]
    tipo_lower = str(tipo).lower().strip()
    if "empresarial" in tipo_lower:
        return 0.85
    if "ades" in tipo_lower:
        return 0.95
    if "individual" in tipo_lower or "familiar" in tipo_lower:
        return 1.20
    return 1.00


def main():
    print("=" * 60)
    print("SPRINT 5 — Score de Risco Atuarial e Rateio Financeiro")
    print("=" * 60)
    
    # Conectar ao banco
    con = duckdb.connect(DB_PATH, read_only=False)
    
    # =========================================================
    # ETAPA 1: Carregar dados granulares do SIB
    # =========================================================
    print("\n[1/5] Carregando dados granulares do SIB...")
    
    df_sib = con.execute("""
        SELECT 
            registro_ans,
            razao_social,
            cd_plano,
            uf,
            municipio,
            faixa_etaria,
            sexo,
            tipo_vinculo,
            tipo_contratacao,
            cobertura,
            segmentacao,
            abrangencia,
            qt_beneficiario_ativo
        FROM sib_granular
        WHERE qt_beneficiario_ativo > 0
    """).df()
    
    print(f"   Registros carregados: {len(df_sib):,}")
    print(f"   Operadoras: {df_sib['registro_ans'].nunique()}")
    print(f"   Produtos: {df_sib['cd_plano'].nunique()}")
    
    # =========================================================
    # ETAPA 2: Calcular fatores para cada registro
    # =========================================================
    print("\n[2/5] Calculando fatores de risco para cada cluster...")
    
    df_sib['f_etario'] = df_sib['faixa_etaria'].apply(get_fator_etario)
    df_sib['f_geografico'] = df_sib['uf'].apply(get_fator_geografico)
    df_sib['f_segmentacao'] = df_sib['segmentacao'].apply(get_fator_segmentacao)
    df_sib['f_contratacao'] = df_sib['tipo_contratacao'].apply(get_fator_contratacao)
    
    # Score de risco por cluster
    df_sib['score_risco'] = (
        df_sib['qt_beneficiario_ativo'] *
        df_sib['f_etario'] *
        df_sib['f_geografico'] *
        df_sib['f_segmentacao'] *
        df_sib['f_contratacao']
    )
    
    print(f"   Score total calculado: {df_sib['score_risco'].sum():,.0f}")
    print(f"   Score médio por registro: {df_sib['score_risco'].mean():.2f}")
    
    # =========================================================
    # ETAPA 3: Carregar dados financeiros (DIOPS)
    # =========================================================
    print("\n[3/5] Carregando dados financeiros do DIOPS...")
    
    df_financeiro = con.execute("""
        SELECT 
            CAST(registro_ans AS VARCHAR) as registro_ans,
            receita_contraprestacoes as receita,
            despesa_assistencial as despesa,
            sinistralidade_total
        FROM sinistralidade_operadora
        WHERE sinistralidade_total IS NOT NULL
    """).df()
    
    print(f"   Operadoras com dados financeiros: {len(df_financeiro)}")
    for _, row in df_financeiro.iterrows():
        print(f"     {row['registro_ans']}: Receita R$ {row['receita']/1e6:.1f}M | Despesa R$ {row['despesa']/1e6:.1f}M | Sinist. {row['sinistralidade_total']*100:.1f}%")
    
    # =========================================================
    # ETAPA 4: Rateio Financeiro por Produto
    # =========================================================
    print("\n[4/5] Executando rateio financeiro por produto...")
    
    resultados = []
    
    for _, op in df_financeiro.iterrows():
        reg_ans = str(op['registro_ans']).strip()
        despesa_total = op['despesa']
        receita_total = op['receita']
        sinist_total = op['sinistralidade_total']
        
        # Filtrar SIB para esta operadora
        df_op = df_sib[df_sib['registro_ans'].astype(str).str.strip() == reg_ans]
        
        if df_op.empty:
            print(f"   SKIP {reg_ans}: sem dados no SIB granular")
            continue
        
        score_total_op = df_op['score_risco'].sum()
        vidas_total_op = df_op['qt_beneficiario_ativo'].sum()
        
        if score_total_op == 0:
            continue
        
        # Agregar por produto × município
        df_prod_mun = df_op.groupby(['cd_plano', 'uf', 'municipio', 'segmentacao', 
                                      'tipo_contratacao', 'abrangencia']).agg({
            'qt_beneficiario_ativo': 'sum',
            'score_risco': 'sum',
            'f_etario': 'mean',
            'f_geografico': 'first',
            'f_segmentacao': 'first',
            'f_contratacao': 'first',
        }).reset_index()
        
        # Calcular rateio
        df_prod_mun['pct_score'] = df_prod_mun['score_risco'] / score_total_op
        df_prod_mun['despesa_estimada'] = df_prod_mun['pct_score'] * despesa_total
        df_prod_mun['receita_estimada'] = df_prod_mun['pct_score'] * receita_total
        df_prod_mun['sinistralidade_estimada'] = np.where(
            df_prod_mun['receita_estimada'] > 0,
            df_prod_mun['despesa_estimada'] / df_prod_mun['receita_estimada'],
            sinist_total
        )
        
        # Custo per capita estimado
        df_prod_mun['custo_per_capita_mensal'] = np.where(
            df_prod_mun['qt_beneficiario_ativo'] > 0,
            (df_prod_mun['despesa_estimada'] / df_prod_mun['qt_beneficiario_ativo']) / 12,
            0
        )
        
        # Classificação de risco
        df_prod_mun['classificacao_risco'] = pd.cut(
            df_prod_mun['sinistralidade_estimada'],
            bins=[0, 0.65, 0.75, 0.85, 1.0, float('inf')],
            labels=['Baixo', 'Moderado', 'Elevado', 'Crítico', 'Insustentável']
        )
        
        # Adicionar metadados
        df_prod_mun['registro_ans'] = reg_ans
        df_prod_mun['razao_social'] = df_op['razao_social'].iloc[0]
        df_prod_mun['sinist_total_operadora'] = sinist_total
        
        resultados.append(df_prod_mun)
        
        n_produtos = df_prod_mun['cd_plano'].nunique()
        n_municipios = df_prod_mun['municipio'].nunique()
        print(f"   {reg_ans} ({df_op['razao_social'].iloc[0][:30]}): {n_produtos} produtos × {n_municipios} municípios = {len(df_prod_mun):,} clusters")
    
    # =========================================================
    # ETAPA 5: Consolidar e salvar resultados
    # =========================================================
    print("\n[5/5] Consolidando resultados...")
    
    if not resultados:
        print("   ERRO: Nenhum resultado gerado!")
        con.close()
        return
    
    df_resultado = pd.concat(resultados, ignore_index=True)
    
    print(f"   Total de clusters: {len(df_resultado):,}")
    print(f"   Operadoras processadas: {df_resultado['registro_ans'].nunique()}")
    print(f"   Produtos únicos: {df_resultado['cd_plano'].nunique()}")
    print(f"   Municípios únicos: {df_resultado['municipio'].nunique()}")
    
    # Estatísticas de sinistralidade
    print(f"\n   Sinistralidade Estimada (por cluster):")
    print(f"     Média: {df_resultado['sinistralidade_estimada'].mean()*100:.1f}%")
    print(f"     Mediana: {df_resultado['sinistralidade_estimada'].median()*100:.1f}%")
    print(f"     P10: {df_resultado['sinistralidade_estimada'].quantile(0.10)*100:.1f}%")
    print(f"     P90: {df_resultado['sinistralidade_estimada'].quantile(0.90)*100:.1f}%")
    
    # Distribuição por classificação de risco
    print(f"\n   Distribuição por Classificação de Risco:")
    for cls, count in df_resultado['classificacao_risco'].value_counts().items():
        pct = count / len(df_resultado) * 100
        print(f"     {cls}: {count:,} clusters ({pct:.1f}%)")
    
    # Salvar no DuckDB
    print("\n   Salvando tabela 'score_risco_produto' no DuckDB...")
    
    # Drop se existir
    con.execute("DROP TABLE IF EXISTS score_risco_produto")
    
    # Criar tabela
    con.execute("""
        CREATE TABLE score_risco_produto AS 
        SELECT * FROM df_resultado
    """)
    
    # Verificar
    count = con.execute("SELECT COUNT(*) FROM score_risco_produto").fetchone()[0]
    print(f"   Tabela criada com {count:,} registros")
    
    # Criar visão agregada por produto (sem município)
    con.execute("DROP TABLE IF EXISTS score_risco_produto_agg")
    con.execute("""
        CREATE TABLE score_risco_produto_agg AS
        SELECT 
            registro_ans,
            razao_social,
            cd_plano,
            segmentacao,
            tipo_contratacao,
            abrangencia,
            SUM(qt_beneficiario_ativo) as vidas_total,
            SUM(score_risco) as score_total,
            SUM(despesa_estimada) as despesa_estimada,
            SUM(receita_estimada) as receita_estimada,
            CASE WHEN SUM(receita_estimada) > 0 
                 THEN SUM(despesa_estimada) / SUM(receita_estimada)
                 ELSE NULL END as sinistralidade_estimada,
            AVG(custo_per_capita_mensal) as custo_per_capita_medio,
            AVG(f_etario) as fator_etario_medio,
            COUNT(DISTINCT municipio) as municipios,
            COUNT(DISTINCT uf) as ufs,
            sinist_total_operadora
        FROM score_risco_produto
        GROUP BY registro_ans, razao_social, cd_plano, segmentacao, 
                 tipo_contratacao, abrangencia, sinist_total_operadora
        ORDER BY despesa_estimada DESC
    """)
    
    count_agg = con.execute("SELECT COUNT(*) FROM score_risco_produto_agg").fetchone()[0]
    print(f"   Tabela agregada criada com {count_agg:,} produtos")
    
    # Criar visão por operadora × UF
    con.execute("DROP TABLE IF EXISTS score_risco_uf")
    con.execute("""
        CREATE TABLE score_risco_uf AS
        SELECT 
            registro_ans,
            razao_social,
            uf,
            SUM(qt_beneficiario_ativo) as vidas,
            SUM(score_risco) as score_total,
            SUM(despesa_estimada) as despesa_estimada,
            CASE WHEN SUM(receita_estimada) > 0 
                 THEN SUM(despesa_estimada) / SUM(receita_estimada)
                 ELSE NULL END as sinistralidade_uf,
            AVG(custo_per_capita_mensal) as custo_per_capita,
            COUNT(DISTINCT cd_plano) as produtos,
            COUNT(DISTINCT municipio) as municipios
        FROM score_risco_produto
        GROUP BY registro_ans, razao_social, uf
        ORDER BY despesa_estimada DESC
    """)
    
    count_uf = con.execute("SELECT COUNT(*) FROM score_risco_uf").fetchone()[0]
    print(f"   Tabela por UF criada com {count_uf:,} registros")
    
    # Salvar resumo em JSON
    resumo = {
        "sprint": 5,
        "descricao": "Score de Risco Atuarial e Rateio Financeiro",
        "total_clusters": int(count),
        "total_produtos_agregados": int(count_agg),
        "total_registros_uf": int(count_uf),
        "operadoras_processadas": int(df_resultado['registro_ans'].nunique()),
        "sinistralidade_media": float(df_resultado['sinistralidade_estimada'].mean()),
        "sinistralidade_mediana": float(df_resultado['sinistralidade_estimada'].median()),
        "fatores_utilizados": {
            "etario": "Curva em J (RN 63/2003 + UNIDAS 2023)",
            "geografico": "VCMH regional por UF (IESS + DATASUS proxy)",
            "segmentacao": "Tipo de cobertura assistencial",
            "contratacao": "Individual vs Coletivo"
        }
    }
    
    with open("/home/ubuntu/mvp_sinistralidade/sprint5_resultado.json", "w") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)
    
    con.close()
    
    print("\n" + "=" * 60)
    print("SPRINT 5 CONCLUÍDO!")
    print(f"  Clusters gerados: {count:,}")
    print(f"  Produtos agregados: {count_agg:,}")
    print(f"  Visões por UF: {count_uf:,}")
    print("=" * 60)


if __name__ == "__main__":
    main()
