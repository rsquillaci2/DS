"""
Fix v4: Forward-fill no nível mais granular antes de agregar.

O problema final: dentro de (operadora, cobertura, tipo_contratacao) existem
MÚLTIPLOS sub-planos distinguidos por tipo_financiamento.
Ex: Santa Helena CE tem "Pre-estabelecido" (114k) e "Não identificado" (56).
O "Pre-estabelecido" não aparece em todos os meses.

Solução: forward-fill por (operadora, cobertura, tipo_contratacao, tipo_financiamento)
e DEPOIS somar tudo por (operadora, cobertura, mes).
"""
import duckdb
import pandas as pd
import numpy as np

print("=== Fix Beneficiários v4: Granularidade máxima ===")

con = duckdb.connect('data/ans_analytics.duckdb')

# 1. Extrair no nível mais granular
print("1. Extraindo dados no nível mais granular...")
df = con.execute("""
    SELECT registro_ans, cobertura, tipo_contratacao, tipo_financiamento, 
           mes_competencia, total_beneficiarios
    FROM sib_operadoras
    ORDER BY registro_ans, cobertura, tipo_contratacao, tipo_financiamento, mes_competencia
""").df()
print(f"   Registros: {len(df):,}")

# Handle NaN in tipo_financiamento
df['tipo_financiamento'] = df['tipo_financiamento'].fillna('NA')

groups = df.groupby(['registro_ans', 'cobertura', 'tipo_contratacao', 'tipo_financiamento'])
total_groups = len(groups)
print(f"   Grupos únicos: {total_groups:,}")

# 2. Forward-fill por grupo granular
print("\n2. Forward-fill por grupo granular...")
all_months = sorted(df['mes_competencia'].unique())

filled_data = []
count = 0

for keys, group in groups:
    count += 1
    if count % 5000 == 0:
        print(f"   {count:,}/{total_groups:,}...")
    
    reg, cob, tipo, fin = keys
    series = group.groupby('mes_competencia')['total_beneficiarios'].sum().sort_index()
    first_month = series.index.min()
    relevant_months = [m for m in all_months if m >= first_month]
    
    series = series.reindex(relevant_months).ffill().dropna()
    
    for mes, total in series.items():
        filled_data.append((reg, cob, int(mes), int(total)))

print(f"   Registros após forward-fill: {len(filled_data):,}")

# 3. Agregar por (operadora, cobertura, mes)
print("\n3. Agregando por (operadora, cobertura, mês)...")
df_filled = pd.DataFrame(filled_data, columns=['registro_ans', 'cobertura', 'mes_competencia', 'total_beneficiarios'])
df_monthly = df_filled.groupby(['registro_ans', 'cobertura', 'mes_competencia'])['total_beneficiarios'].sum().reset_index()
print(f"   Séries mensais: {len(df_monthly):,}")

# 4. Sanity check
print("\n4. Sanity check - Santa Helena (355097) médico-hospitalar:")
check = df_monthly[(df_monthly['registro_ans'] == '355097') & (df_monthly['cobertura'].str.contains('dico'))]
check = check.sort_values('mes_competencia')
cv = check['total_beneficiarios'].std() / check['total_beneficiarios'].mean()
print(f"   CV: {cv:.4f} (era 0.35, target < 0.10)")
print(f"   Últimos 12 meses:")
for _, row in check.tail(12).iterrows():
    print(f"     {int(row['mes_competencia'])}: {int(row['total_beneficiarios']):,}")

# 5. Salvar
print("\n5. Salvando tabela sib_evolucao_temporal...")
con.execute("DROP TABLE IF EXISTS sib_evolucao_temporal")
con.execute("""
    CREATE TABLE sib_evolucao_temporal (
        registro_ans VARCHAR,
        cobertura VARCHAR,
        mes_competencia BIGINT,
        total_beneficiarios BIGINT
    )
""")
con.execute("INSERT INTO sib_evolucao_temporal SELECT * FROM df_monthly")
n = con.execute("SELECT COUNT(*) FROM sib_evolucao_temporal").fetchone()[0]
print(f"   Inseridos: {n:,}")

# 6. Global check
print("\n6. Verificação global:")
stats = con.execute("""
    WITH s AS (
        SELECT registro_ans,
               AVG(total_beneficiarios) as media,
               STDDEV(total_beneficiarios) as desvio,
               COUNT(*) as meses
        FROM sib_evolucao_temporal
        WHERE cobertura LIKE '%dico%'
        GROUP BY registro_ans
        HAVING COUNT(*) > 10
    )
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN (desvio / NULLIF(media, 0)) > 0.3 THEN 1 ELSE 0 END) as cv_high,
        SUM(CASE WHEN (desvio / NULLIF(media, 0)) > 0.15 THEN 1 ELSE 0 END) as cv_med,
        SUM(CASE WHEN (desvio / NULLIF(media, 0)) <= 0.15 THEN 1 ELSE 0 END) as cv_low
    FROM s
""").fetchone()
print(f"   Total operadoras analisadas: {stats[0]}")
print(f"   CV > 0.3 (alta variação): {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
print(f"   CV 0.15-0.3 (moderada): {stats[2]-stats[1]} ({(stats[2]-stats[1])/stats[0]*100:.1f}%)")
print(f"   CV <= 0.15 (suave): {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
print(f"   (Antes: 764 de 893 com CV > 0.3)")

con.close()
print("\nDone!")
