"""
Sprint 6 FIX — Reprocessar DIOPS histórico com formatos heterogêneos.
Os CSVs da ANS mudaram de formato:
  - 2020-2021: 5 cols (DATA;REG_ANS;CD_CONTA_CONTABIL;DESCRICAO;VL_SALDO_FINAL), data "dd/mm/yyyy"
  - 2022-2024: 6 cols (+VL_SALDO_INICIAL), data "yyyy/mm/dd"
  - 2025: 6 cols, data "yyyy-mm-dd"
"""
import os
import duckdb
import json

DB_PATH = "data/ans_analytics.duckdb"
DATA_DIR = "data/diops_historico"

OPERADORAS = ['310239', '355097', '359017', '417491', '421197', '422371']
OPS_FILTER = ",".join([f"'{r}'" for r in OPERADORAS])

con = duckdb.connect(DB_PATH, read_only=False)

# Dropar tabelas antigas
con.execute("DROP TABLE IF EXISTS diops_historico")
con.execute("DROP TABLE IF EXISTS sinistralidade_historica")

# Criar tabela com schema unificado
con.execute("""
    CREATE TABLE diops_historico (
        trimestre VARCHAR,
        registro_ans VARCHAR,
        cd_conta_contabil VARCHAR,
        descricao VARCHAR,
        vl_saldo_final DOUBLE
    )
""")

# Processar cada CSV individualmente com tratamento de formato
csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')])
print(f"Processando {len(csv_files)} arquivos...")

for csv_file in csv_files:
    filepath = os.path.join(DATA_DIR, csv_file)
    trimestre_label = csv_file.replace('.csv', '').upper()
    
    # Detectar número de colunas
    with open(filepath, 'r', encoding='latin-1', errors='replace') as f:
        header = f.readline().strip()
    
    n_cols = header.count(';') + 1
    
    try:
        if n_cols == 5:
            # Formato antigo: DATA;REG_ANS;CD_CONTA_CONTABIL;DESCRICAO;VL_SALDO_FINAL
            con.execute(f"""
                INSERT INTO diops_historico
                SELECT 
                    '{trimestre_label}' as trimestre,
                    CAST("REG_ANS" AS VARCHAR) as registro_ans,
                    "CD_CONTA_CONTABIL" as cd_conta_contabil,
                    "DESCRICAO" as descricao,
                    CAST(REPLACE(REPLACE("VL_SALDO_FINAL", '.', ''), ',', '.') AS DOUBLE) as vl_saldo_final
                FROM read_csv_auto('{filepath}', delim=';', header=true, 
                    ignore_errors=true, all_varchar=true)
                WHERE CAST("REG_ANS" AS VARCHAR) IN ({OPS_FILTER})
            """)
        else:
            # Formato novo: DATA;REG_ANS;CD_CONTA_CONTABIL;DESCRICAO;VL_SALDO_INICIAL;VL_SALDO_FINAL
            con.execute(f"""
                INSERT INTO diops_historico
                SELECT 
                    '{trimestre_label}' as trimestre,
                    CAST("REG_ANS" AS VARCHAR) as registro_ans,
                    "CD_CONTA_CONTABIL" as cd_conta_contabil,
                    "DESCRICAO" as descricao,
                    CAST(REPLACE(REPLACE("VL_SALDO_FINAL", '.', ''), ',', '.') AS DOUBLE) as vl_saldo_final
                FROM read_csv_auto('{filepath}', delim=';', header=true, 
                    ignore_errors=true, all_varchar=true)
                WHERE CAST("REG_ANS" AS VARCHAR) IN ({OPS_FILTER})
            """)
        
        count = con.execute(f"SELECT COUNT(*) FROM diops_historico WHERE trimestre = '{trimestre_label}'").fetchone()[0]
        print(f"  [OK] {trimestre_label}: {count:,} registros")
    except Exception as e:
        print(f"  [WARN] {trimestre_label}: {str(e)[:100]}")

# Total
total = con.execute("SELECT COUNT(*) FROM diops_historico").fetchone()[0]
print(f"\nTotal consolidado: {total:,} registros")

# Verificar trimestres
trimestres = con.execute("SELECT DISTINCT trimestre FROM diops_historico ORDER BY trimestre").fetchall()
print(f"Trimestres: {[t[0] for t in trimestres]}")

# Agora calcular sinistralidade histórica
# Receita = Conta '3' (RECEITAS total) ou somar contas 311* (Contraprestações)
# Despesa Assistencial = Somar contas 411* (Eventos/Sinistros)

# Primeiro verificar quais contas temos
print("\n=== Verificando contas disponíveis ===")
contas_receita = con.execute("""
    SELECT cd_conta_contabil, descricao, COUNT(*) as n
    FROM diops_historico
    WHERE cd_conta_contabil IN ('3', '31', '311', '312', '313')
       OR (cd_conta_contabil LIKE '311%' AND LENGTH(cd_conta_contabil) <= 4)
    GROUP BY cd_conta_contabil, descricao
    ORDER BY cd_conta_contabil
""").df()
print("Receita:")
print(contas_receita.to_string())

contas_despesa = con.execute("""
    SELECT cd_conta_contabil, descricao, COUNT(*) as n
    FROM diops_historico
    WHERE cd_conta_contabil IN ('4', '41', '411')
       OR (cd_conta_contabil LIKE '411%' AND LENGTH(cd_conta_contabil) <= 5)
    GROUP BY cd_conta_contabil, descricao
    ORDER BY cd_conta_contabil
""").df()
print("\nDespesa Assistencial:")
print(contas_despesa.to_string())

# Estratégia: 
# Receita = conta '3' (total de receitas) — disponível para todos os trimestres
# Despesa Assistencial = somar contas 4111 + 4112 + 4114 + 4117 + 4119 (Eventos/Sinistros por modalidade)
# Se não houver essas contas detalhadas, usar conta '4' como fallback

print("\n=== Calculando Sinistralidade Histórica ===")

con.execute("""
    CREATE TABLE sinistralidade_historica AS
    WITH receitas AS (
        SELECT 
            registro_ans,
            trimestre,
            SUM(vl_saldo_final) as receita
        FROM diops_historico
        WHERE cd_conta_contabil = '3'
        GROUP BY registro_ans, trimestre
    ),
    despesas_assist AS (
        SELECT 
            registro_ans,
            trimestre,
            SUM(vl_saldo_final) as despesa_assistencial
        FROM diops_historico
        WHERE cd_conta_contabil LIKE '411%' AND LENGTH(cd_conta_contabil) = 4
        GROUP BY registro_ans, trimestre
    ),
    despesas_total AS (
        SELECT 
            registro_ans,
            trimestre,
            SUM(vl_saldo_final) as despesa_total
        FROM diops_historico
        WHERE cd_conta_contabil = '4'
        GROUP BY registro_ans, trimestre
    )
    SELECT 
        r.registro_ans,
        r.trimestre,
        r.receita,
        COALESCE(da.despesa_assistencial, dt.despesa_total) as despesa,
        CASE 
            WHEN r.receita > 0 THEN COALESCE(da.despesa_assistencial, dt.despesa_total) / r.receita 
            ELSE NULL 
        END as sinistralidade,
        CASE 
            WHEN da.despesa_assistencial IS NOT NULL THEN 'assistencial'
            ELSE 'total'
        END as tipo_despesa
    FROM receitas r
    LEFT JOIN despesas_assist da ON r.registro_ans = da.registro_ans AND r.trimestre = da.trimestre
    LEFT JOIN despesas_total dt ON r.registro_ans = dt.registro_ans AND r.trimestre = dt.trimestre
    WHERE r.receita > 0
    ORDER BY r.registro_ans, r.trimestre
""")

# Resultado
result = con.execute("""
    SELECT COUNT(*) as registros, 
           COUNT(DISTINCT registro_ans) as operadoras, 
           COUNT(DISTINCT trimestre) as trimestres
    FROM sinistralidade_historica
""").fetchone()
print(f"\nResultado:")
print(f"  Registros: {result[0]}")
print(f"  Operadoras: {result[1]}")
print(f"  Trimestres: {result[2]}")

# Amostra
sample = con.execute("""
    SELECT registro_ans, trimestre, 
           ROUND(receita/1e6, 1) as receita_M,
           ROUND(despesa/1e6, 1) as despesa_M,
           ROUND(sinistralidade * 100, 1) as sinist_pct,
           tipo_despesa
    FROM sinistralidade_historica
    ORDER BY registro_ans, trimestre
    LIMIT 30
""").df()
print(f"\nAmostra:")
print(sample.to_string())

# Exportar resumo
resumo = {
    "total_registros": int(result[0]),
    "operadoras": int(result[1]),
    "trimestres": int(result[2]),
    "periodo": "2020-2025",
    "status": "success"
}
with open("sprint6_resultado.json", "w") as f:
    json.dump(resumo, f, indent=2)

print(f"\n[CONCLUIDO] Sprint 6 — Série Temporal processada!")
con.close()
