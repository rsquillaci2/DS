"""
Fix: Inserir as 10 operadoras que estão em sinistralidade_operadora
mas não em operadoras_classificacao (problema de zero-padding no registro ANS).

O CSV operadoras_ativas.csv usa formato zero-padded (005711), mas o DIOPS
armazena sem zeros (5711). O sprint85_expansion.py populou operadoras_classificacao
a partir do CSV, mas o JOIN falhou para esses 10 registros.
"""
import duckdb

con = duckdb.connect('data/ans_analytics.duckdb')

# Map the 10 missing operadoras with their correct names from the CSV
# (found via LIKE search in the CSV)
missing_operadoras = [
    ('5711', 'BRADESCO SAUDE', 'Seguradora Especializada em Saúde', 'SP'),
    ('6246', 'SULAMÉRICA', 'Seguradora Especializada em Saúde', 'RJ'),
    ('582', 'PORTO SEGURO SAÚDE', 'Seguradora Especializada em Saúde', 'SP'),
    ('701', 'SEGUROS UNIMED', 'Seguradora Especializada em Saúde', 'SP'),
    ('317233', 'RISO PLANO ODONTOLÓGICO', 'Odontologia de Grupo', 'SP'),
    ('884', 'ITAUSEG SAÚDE', 'Seguradora Especializada em Saúde', 'SP'),
    ('515', 'ALLIANZ SAÚDE', 'Seguradora Especializada em Saúde', 'SP'),
    ('420051', 'HC HCPF', 'Autogestão', 'SP'),
    ('401871', 'CAMED', 'Autogestão', 'CE'),
    ('410071', 'REAL GRANDEZA', 'Autogestão', 'RJ'),
]

# Let's verify from the CSV what the actual names are
print("Verifying names from operadoras_ativas.csv...")
padded_codes = [f"{int(m[0]):06d}" for m in missing_operadoras]
for i, (code, name, mod, uf) in enumerate(missing_operadoras):
    padded = f"{int(code):06d}"
    r = con.execute(f"""
        SELECT REGISTRO_OPERADORA, Nome_Fantasia, Razao_Social, Modalidade, UF
        FROM read_csv_auto('operadoras_ativas.csv')
        WHERE REGISTRO_OPERADORA = '{padded}'
    """).fetchall()
    if r:
        fantasia = r[0][1] if r[0][1] else None
        razao = r[0][2]
        mod_csv = r[0][3]
        uf_csv = r[0][4]
        display_name = fantasia if fantasia else razao
        print(f"  {code} ({padded}): {display_name} | Mod={mod_csv} | UF={uf_csv}")
        # Update our list with actual data
        missing_operadoras[i] = (code, display_name, mod_csv if mod_csv else mod, uf_csv if uf_csv else uf)
    else:
        print(f"  {code} ({padded}): NOT FOUND in CSV, using manual: {name}")

# Insert into operadoras_classificacao
print("\nInserting into operadoras_classificacao...")
for code, name, mod, uf in missing_operadoras:
    con.execute("""
        INSERT INTO operadoras_classificacao (registro_ans, nome_operadora, modalidade, uf_sede)
        VALUES (?, ?, ?, ?)
    """, [code, name, mod, uf])
    print(f"  Inserted: {code} = {name} ({mod})")

# Verify
print("\nVerification:")
r = con.execute("""
    SELECT registro_ans, nome_operadora, modalidade
    FROM operadoras_classificacao
    WHERE registro_ans IN ('5711', '6246', '582', '701', '317233', '884', '515', '420051', '401871', '410071')
""").fetchall()
for row in r:
    print(f"  {row[0]}: {row[1]} ({row[2]})")

# Also fix: update the sprint85_expansion logic to handle zero-padding in future runs
# For now, let's also check if there are still any operadoras without names
total_missing = con.execute("""
    SELECT COUNT(*)
    FROM sinistralidade_operadora s
    LEFT JOIN operadoras_classificacao o ON s.registro_ans = o.registro_ans
    WHERE o.registro_ans IS NULL
""").fetchone()[0]
print(f"\nRemaining operadoras without names: {total_missing}")

con.close()
print("\nDone!")
