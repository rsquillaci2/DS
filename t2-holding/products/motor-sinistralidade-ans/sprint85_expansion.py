"""
Sprint 8.5 — Expansão para Mercado Completo
Etapa 1: Expandir DIOPS para todas as operadoras (sem filtro)
Etapa 2: Recalcular série temporal 2020-2025 para todas
Etapa 3: Expandir SIB consolidado para todas
Etapa 4: Recalcular benchmarks com base expandida
"""
import duckdb
import os
import glob

DATA_DIR = "/home/ubuntu/mvp_sinistralidade/data"
DB_PATH = f"{DATA_DIR}/ans_analytics.duckdb"

def expand_diops():
    """Expande DIOPS para todas as operadoras (remove filtro de 6)."""
    con = duckdb.connect(DB_PATH)
    
    print("=" * 70)
    print("SPRINT 8.5 — EXPANSÃO PARA MERCADO COMPLETO")
    print("=" * 70)
    
    # =========================================================
    # ETAPA 1: DIOPS 4T2025 — Todas as operadoras
    # =========================================================
    print("\n[ETAPA 1/4] Expandindo DIOPS 4T2025 para todas as operadoras...")
    
    diops_path = f"{DATA_DIR}/diops/4T2025.csv"
    
    # Recriar diops_operadoras SEM filtro de registro_ans
    con.execute("""
        CREATE OR REPLACE TABLE diops_operadoras AS
        SELECT 
            DATA as data_referencia,
            CAST(REG_ANS AS VARCHAR) as registro_ans,
            CAST(CD_CONTA_CONTABIL AS VARCHAR) as conta_contabil,
            DESCRICAO as descricao_conta,
            CAST(VL_SALDO_FINAL AS DOUBLE) as valor_saldo_final
        FROM read_csv_auto(?, 
            delim=';', header=true, decimal_separator=',', sample_size=10000)
    """, [diops_path])
    
    n_total = con.execute("SELECT COUNT(*) FROM diops_operadoras").fetchone()[0]
    n_ops = con.execute("SELECT COUNT(DISTINCT registro_ans) FROM diops_operadoras").fetchone()[0]
    print(f"   Registros DIOPS carregados: {n_total:,}")
    print(f"   Operadoras únicas: {n_ops}")
    
    # Recalcular sinistralidade para TODAS as operadoras
    con.execute("""
        CREATE OR REPLACE TABLE sinistralidade_operadora AS
        SELECT 
            registro_ans,
            SUM(CASE WHEN conta_contabil LIKE '31%' AND LENGTH(conta_contabil) <= 4 
                THEN valor_saldo_final ELSE 0 END) as receita_contraprestacoes,
            SUM(CASE WHEN conta_contabil LIKE '41%' AND LENGTH(conta_contabil) <= 4 
                THEN valor_saldo_final ELSE 0 END) as despesa_assistencial,
            CASE 
                WHEN SUM(CASE WHEN conta_contabil LIKE '31%' AND LENGTH(conta_contabil) <= 4 
                    THEN valor_saldo_final ELSE 0 END) > 0
                THEN SUM(CASE WHEN conta_contabil LIKE '41%' AND LENGTH(conta_contabil) <= 4 
                    THEN valor_saldo_final ELSE 0 END) / 
                     SUM(CASE WHEN conta_contabil LIKE '31%' AND LENGTH(conta_contabil) <= 4 
                    THEN valor_saldo_final ELSE 0 END)
                ELSE NULL
            END as sinistralidade_total
        FROM diops_operadoras
        GROUP BY registro_ans
        HAVING SUM(CASE WHEN conta_contabil LIKE '31%' AND LENGTH(conta_contabil) <= 4 
            THEN valor_saldo_final ELSE 0 END) > 0
    """)
    
    n_sinist = con.execute("SELECT COUNT(*) FROM sinistralidade_operadora").fetchone()[0]
    avg_sinist = con.execute("SELECT AVG(sinistralidade_total) FROM sinistralidade_operadora WHERE sinistralidade_total BETWEEN 0 AND 2").fetchone()[0]
    print(f"   Operadoras com sinistralidade calculada: {n_sinist}")
    print(f"   Sinistralidade média do mercado: {avg_sinist*100:.1f}%")
    
    # Distribuição por faixas
    dist = con.execute("""
        SELECT 
            CASE 
                WHEN sinistralidade_total < 0.5 THEN '< 50%'
                WHEN sinistralidade_total < 0.7 THEN '50-70%'
                WHEN sinistralidade_total < 0.8 THEN '70-80%'
                WHEN sinistralidade_total < 0.9 THEN '80-90%'
                WHEN sinistralidade_total < 1.0 THEN '90-100%'
                ELSE '> 100%'
            END as faixa,
            COUNT(*) as n
        FROM sinistralidade_operadora
        WHERE sinistralidade_total IS NOT NULL AND sinistralidade_total > 0
        GROUP BY faixa
        ORDER BY faixa
    """).fetchall()
    print("\n   Distribuição de sinistralidade:")
    for d in dist:
        print(f"     {d[0]:>10s}: {d[1]:>4} operadoras")
    
    # =========================================================
    # ETAPA 2: Série Temporal — Todos os trimestres para todas
    # =========================================================
    print("\n[ETAPA 2/4] Expandindo série temporal (24 trimestres × todas operadoras)...")
    
    historico_dir = f"{DATA_DIR}/diops_historico"
    historico_files = sorted(glob.glob(f"{historico_dir}/*.csv"))
    
    # Criar tabela de série temporal expandida
    con.execute("DROP TABLE IF EXISTS sinistralidade_historica")
    con.execute("""
        CREATE TABLE sinistralidade_historica (
            registro_ans VARCHAR,
            trimestre VARCHAR,
            receita DOUBLE,
            despesa DOUBLE,
            sinistralidade DOUBLE,
            tipo_despesa VARCHAR DEFAULT 'assistencial'
        )
    """)
    
    for f in historico_files:
        basename = os.path.basename(f).replace('.csv', '')
        trimestre = basename.upper()
        
        try:
            con.execute(f"""
                INSERT INTO sinistralidade_historica (registro_ans, trimestre, receita, despesa, sinistralidade)
                SELECT 
                    CAST(REG_ANS AS VARCHAR) as registro_ans,
                    '{trimestre}' as trimestre,
                    SUM(CASE WHEN CAST(CD_CONTA_CONTABIL AS VARCHAR) LIKE '31%' 
                        AND LENGTH(CAST(CD_CONTA_CONTABIL AS VARCHAR)) <= 4 
                        THEN CAST(VL_SALDO_FINAL AS DOUBLE) ELSE 0 END) as receita,
                    SUM(CASE WHEN CAST(CD_CONTA_CONTABIL AS VARCHAR) LIKE '41%' 
                        AND LENGTH(CAST(CD_CONTA_CONTABIL AS VARCHAR)) <= 4 
                        THEN CAST(VL_SALDO_FINAL AS DOUBLE) ELSE 0 END) as despesa,
                    CASE 
                        WHEN SUM(CASE WHEN CAST(CD_CONTA_CONTABIL AS VARCHAR) LIKE '31%' 
                            AND LENGTH(CAST(CD_CONTA_CONTABIL AS VARCHAR)) <= 4 
                            THEN CAST(VL_SALDO_FINAL AS DOUBLE) ELSE 0 END) > 0
                        THEN SUM(CASE WHEN CAST(CD_CONTA_CONTABIL AS VARCHAR) LIKE '41%' 
                            AND LENGTH(CAST(CD_CONTA_CONTABIL AS VARCHAR)) <= 4 
                            THEN CAST(VL_SALDO_FINAL AS DOUBLE) ELSE 0 END) / 
                             SUM(CASE WHEN CAST(CD_CONTA_CONTABIL AS VARCHAR) LIKE '31%' 
                            AND LENGTH(CAST(CD_CONTA_CONTABIL AS VARCHAR)) <= 4 
                            THEN CAST(VL_SALDO_FINAL AS DOUBLE) ELSE 0 END)
                        ELSE NULL
                    END as sinistralidade
                FROM read_csv_auto('{f}', delim=';', header=true, decimal_separator=',', 
                     sample_size=10000, ignore_errors=true)
                GROUP BY registro_ans
                HAVING receita > 0
            """)
            n_inserted = con.execute(f"SELECT COUNT(*) FROM sinistralidade_historica WHERE trimestre = '{trimestre}'").fetchone()[0]
            print(f"   {trimestre}: {n_inserted} operadoras")
        except Exception as e:
            print(f"   {trimestre}: ERRO - {e}")
    
    total_hist = con.execute("SELECT COUNT(*) FROM sinistralidade_historica").fetchone()[0]
    ops_hist = con.execute("SELECT COUNT(DISTINCT registro_ans) FROM sinistralidade_historica").fetchone()[0]
    print(f"\n   Total série temporal: {total_hist:,} registros ({ops_hist} operadoras × 24 trimestres)")
    
    # =========================================================
    # ETAPA 3: SIB Consolidado — Expandir para todas
    # =========================================================
    print("\n[ETAPA 3/4] Expandindo SIB consolidado para todas as operadoras...")
    
    sib_path = f"{DATA_DIR}/sib/beneficiarios_operadora_carteira.csv"
    
    # Recriar sib_operadoras SEM filtro
    con.execute("""
        CREATE OR REPLACE TABLE sib_operadoras AS
        SELECT 
            CAST(CD_OPERADORA AS VARCHAR) as registro_ans,
            GR_MODALIDADE as modalidade,
            COBERTURA as cobertura,
            GR_CONTRATACAO as tipo_contratacao,
            TIPO_FINANCIAMENTO as tipo_financiamento,
            MES as mes_competencia,
            SUM(NR_BENEF) as total_beneficiarios
        FROM read_csv_auto(?, delim=';', header=true, sample_size=10000, ignore_errors=true)
        GROUP BY ALL
    """, [sib_path])
    
    n_sib = con.execute("SELECT COUNT(*) FROM sib_operadoras").fetchone()[0]
    n_ops_sib = con.execute("SELECT COUNT(DISTINCT registro_ans) FROM sib_operadoras").fetchone()[0]
    print(f"   Registros SIB consolidado: {n_sib:,}")
    print(f"   Operadoras no SIB: {n_ops_sib}")
    
    # Expandir produtos_operadoras SEM filtro
    print("\n   Expandindo cadastro de produtos...")
    produtos_path = f"{DATA_DIR}/produtos/caracteristicas_produtos.csv"
    if os.path.exists(produtos_path):
        con.execute("""
            CREATE OR REPLACE TABLE produtos_operadoras AS
            SELECT 
                ID_PLANO,
                CD_PLANO as codigo_produto_ans,
                NM_PLANO as nome_produto,
                CAST(REGISTRO_OPERADORA AS VARCHAR) as registro_ans,
                GR_SGMT_ASSISTENCIAL as segmentacao,
                GR_CONTRATACAO as tipo_contratacao,
                COBERTURA as cobertura,
                TIPO_FINANCIAMENTO as tipo_financiamento,
                ABRANGENCIA_COBERTURA as abrangencia,
                FATOR_MODERADOR as fator_moderador,
                SITUACAO_PLANO as situacao
            FROM read_csv_auto(?, delim=';', header=true, sample_size=10000, ignore_errors=true)
            WHERE SITUACAO_PLANO = 'Ativo'
        """, [produtos_path])
        
        n_prod = con.execute("SELECT COUNT(*) FROM produtos_operadoras").fetchone()[0]
        n_ops_prod = con.execute("SELECT COUNT(DISTINCT registro_ans) FROM produtos_operadoras").fetchone()[0]
        print(f"   Produtos ativos: {n_prod:,} ({n_ops_prod} operadoras)")
    
    # =========================================================
    # ETAPA 4: Benchmark expandido com percentis reais
    # =========================================================
    print("\n[ETAPA 4/4] Recalculando benchmarks com base expandida...")
    
    # Classificar operadoras por modalidade usando o CSV de cadastro
    con.execute("""
        CREATE OR REPLACE TABLE operadoras_classificacao AS
        SELECT 
            CAST(REGISTRO_OPERADORA AS VARCHAR) as registro_ans,
            COALESCE(Nome_Fantasia, Razao_Social) as nome_operadora,
            Modalidade as modalidade,
            UF as uf_sede
        FROM read_csv_auto('/home/ubuntu/mvp_sinistralidade/operadoras_ativas.csv', 
             delim=';', header=true, ignore_errors=true)
    """)
    
    n_cadastro = con.execute("SELECT COUNT(*) FROM operadoras_classificacao").fetchone()[0]
    print(f"   Operadoras no cadastro: {n_cadastro}")
    
    # Calcular benchmark por modalidade (percentis reais do mercado)
    con.execute("""
        CREATE OR REPLACE TABLE resultado_benchmark AS
        SELECT 
            s.registro_ans,
            oc.nome_operadora,
            oc.modalidade,
            s.sinistralidade_total as sinistralidade_real,
            s.receita_contraprestacoes as receita,
            s.despesa_assistencial as despesa,
            -- Benchmark = mediana da modalidade
            MEDIAN(s.sinistralidade_total) OVER (PARTITION BY oc.modalidade) as benchmark_modalidade,
            -- Percentil dentro da modalidade
            PERCENT_RANK() OVER (PARTITION BY oc.modalidade ORDER BY s.sinistralidade_total) as percentil_modalidade,
            -- Percentil geral
            PERCENT_RANK() OVER (ORDER BY s.sinistralidade_total) as percentil_geral,
            -- Classificação
            CASE 
                WHEN s.sinistralidade_total < MEDIAN(s.sinistralidade_total) OVER (PARTITION BY oc.modalidade) * 0.9
                    THEN 'Eficiente'
                WHEN s.sinistralidade_total > MEDIAN(s.sinistralidade_total) OVER (PARTITION BY oc.modalidade) * 1.1
                    THEN 'Sob Pressão'
                ELSE 'Na Média'
            END as classificacao
        FROM sinistralidade_operadora s
        LEFT JOIN operadoras_classificacao oc ON s.registro_ans = oc.registro_ans
        WHERE s.sinistralidade_total IS NOT NULL 
          AND s.sinistralidade_total > 0 
          AND s.sinistralidade_total < 2
    """)
    
    n_bench = con.execute("SELECT COUNT(*) FROM resultado_benchmark").fetchone()[0]
    print(f"   Operadoras com benchmark calculado: {n_bench}")
    
    # Resumo por classificação
    classif = con.execute("""
        SELECT classificacao, COUNT(*) as n, 
               AVG(sinistralidade_real)*100 as avg_sinist
        FROM resultado_benchmark
        GROUP BY classificacao
        ORDER BY avg_sinist
    """).fetchall()
    print("\n   Distribuição por classificação:")
    for c in classif:
        print(f"     {c[0]:>12s}: {c[1]:>4} operadoras (média {c[2]:.1f}%)")
    
    # Resumo por modalidade
    modal = con.execute("""
        SELECT modalidade, COUNT(*) as n, 
               AVG(sinistralidade_real)*100 as avg_sinist,
               MEDIAN(sinistralidade_real)*100 as med_sinist
        FROM resultado_benchmark
        WHERE modalidade IS NOT NULL
        GROUP BY modalidade
        ORDER BY n DESC
        LIMIT 10
    """).fetchall()
    print("\n   Top 10 modalidades:")
    for m in modal:
        print(f"     {m[0]:>35s}: {m[1]:>4} ops | Média: {m[2]:.1f}% | Mediana: {m[3]:.1f}%")
    
    # =========================================================
    # RESUMO FINAL
    # =========================================================
    print("\n" + "=" * 70)
    print("RESUMO DA EXPANSÃO")
    print("=" * 70)
    
    tables_info = con.execute("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns c 
                WHERE c.table_name = t.table_name) as cols
        FROM information_schema.tables t
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()
    
    for t in tables_info:
        count = con.execute(f"SELECT COUNT(*) FROM \"{t[0]}\"").fetchone()[0]
        print(f"  {t[0]:>35s}: {count:>10,} registros")
    
    con.close()
    print(f"\n✅ Banco expandido salvo em: {DB_PATH}")


if __name__ == "__main__":
    expand_diops()
