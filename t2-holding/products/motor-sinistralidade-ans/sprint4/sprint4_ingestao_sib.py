"""
Sprint 4 — Ingestão SIB Brasil (Individualizado)
Motor de Sinistralidade ANS — Tallent Two Financial Holding

Estratégia:
1. Baixar o ZIP de cada UF para o mês mais recente (202603)
2. Descompactar em streaming
3. Filtrar apenas as 6 operadoras-alvo via DuckDB (leitura direta do CSV)
4. Consolidar em tabela única no banco DuckDB

Operadoras-alvo:
- 310239 (Pessoal Saúde)
- 355097 (Santa Helena Saúde)
- 359017 (Hapvida NotreDame Intermédica)
- 421197 (Santa Casa de Mauá Saúde)
- 422371 (SF Sistemas de Saúde / Sagrada Família)
- 417173 (Portomed - Porto Saúde)
"""

import os
import sys
import time
import subprocess
import duckdb

# Configuração
BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/informacoes_consolidadas_de_beneficiarios-024/202603"
COMPETENCIA = "202603"
DATA_DIR = "data/sib_individual"
DB_PATH = "data/ans_analytics.duckdb"

# Operadoras-alvo (CD_OPERADORA no SIB)
OPERADORAS_ALVO = ['310239', '355097', '359017', '421197', '422371', '417173']

# Todos os estados brasileiros
UFS = [
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR',
    'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO', 'XX'
]

# UFs ordenadas por tamanho estimado (menores primeiro para garantir dados rápidos)
# SP (~128MB), RJ (~80MB), MG (~60MB) são os maiores e ficam por último
UFS_PEQUENAS = ['RR', 'AP', 'AC', 'TO', 'SE', 'RO', 'PI', 'AL', 'PB', 'RN', 'MS', 'MT', 'MA', 'AM', 'XX']
UFS_MEDIAS = ['DF', 'ES', 'GO', 'SC', 'CE', 'PE', 'BA', 'PA', 'PR', 'RS']
UFS_GRANDES = ['MG', 'RJ', 'SP']

os.makedirs(DATA_DIR, exist_ok=True)


def download_uf(uf):
    """Baixa e descompacta o ZIP de uma UF."""
    filename = f"pda-024-icb-{uf}-2026_03.zip"
    url = f"{BASE_URL}/{filename}"
    zip_path = f"{DATA_DIR}/{uf}_{COMPETENCIA}.zip"
    
    if os.path.exists(f"{DATA_DIR}/pda-024-icb-{uf}-2026_03.csv"):
        print(f"  [SKIP] {uf} já descompactado")
        return True
    
    print(f"  [DOWN] Baixando {uf}...", end=" ", flush=True)
    start = time.time()
    
    # Tentar até 3 vezes com timeout progressivo
    max_time = 600 if uf in ['SP', 'RJ', 'MG'] else 300
    for attempt in range(3):
        result = subprocess.run(
            ['curl', '-sL', '--connect-timeout', '30', '--max-time', str(max_time), 
             '--retry', '2', '--retry-delay', '5', '-o', zip_path, url],
            capture_output=True, text=True
        )
        if result.returncode == 0 and os.path.getsize(zip_path) > 1000:
            break
        if attempt < 2:
            print(f"retry {attempt+1}...", end=" ", flush=True)
            time.sleep(5)
    
    if result.returncode != 0 or os.path.getsize(zip_path) < 1000:
        print(f"ERRO download (tentativas esgotadas)")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return False
    
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    elapsed = time.time() - start
    print(f"{size_mb:.1f}MB em {elapsed:.0f}s", end=" ", flush=True)
    
    # Descompactar
    result = subprocess.run(
        ['unzip', '-o', '-q', zip_path, '-d', DATA_DIR],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"ERRO unzip: {result.stderr[:100]}")
        return False
    
    # Remover ZIP para economizar espaço
    os.remove(zip_path)
    print("[OK]")
    return True


def process_uf_to_duckdb(uf, con):
    """Lê o CSV da UF com DuckDB e filtra apenas operadoras-alvo."""
    csv_path = f"{DATA_DIR}/pda-024-icb-{uf}-2026_03.csv"
    
    if not os.path.exists(csv_path):
        print(f"  [SKIP] CSV não encontrado para {uf}")
        return 0
    
    # Usar DuckDB para ler o CSV diretamente e filtrar
    operadoras_filter = "', '".join(OPERADORAS_ALVO)
    
    query = f"""
        INSERT INTO sib_granular
        SELECT 
            ID_CMPT_MOVEL as competencia,
            CD_OPERADORA as registro_ans,
            NM_RAZAO_SOCIAL as razao_social,
            SG_UF as uf,
            CD_MUNICIPIO as cd_municipio,
            NM_MUNICIPIO as municipio,
            TP_SEXO as sexo,
            DE_FAIXA_ETARIA as faixa_etaria,
            DE_FAIXA_ETARIA_REAJ as faixa_etaria_reajuste,
            CD_PLANO as cd_plano,
            DE_CONTRATACAO_PLANO as tipo_contratacao,
            DE_SEGMENTACAO_PLANO as segmentacao,
            DE_ABRG_GEOGRAFICA_PLANO as abrangencia,
            COBERTURA_ASSIST_PLAN as cobertura,
            TIPO_VINCULO as tipo_vinculo,
            CAST(QT_BENEFICIARIO_ATIVO AS INTEGER) as qt_beneficiario_ativo,
            CAST(QT_BENEFICIARIO_ADERIDO AS INTEGER) as qt_beneficiario_aderido,
            CAST(QT_BENEFICIARIO_CANCELADO AS INTEGER) as qt_beneficiario_cancelado
        FROM read_csv('{csv_path}', 
            delim=';', 
            header=true, 
            quote='"',
            ignore_errors=true
        )
        WHERE CD_OPERADORA IN ('{operadoras_filter}')
    """
    
    try:
        con.execute(query)
        count = con.execute(f"""
            SELECT COUNT(*) FROM sib_granular 
            WHERE uf = '{uf}'
        """).fetchone()[0]
        return count
    except Exception as e:
        print(f"  [ERRO] {uf}: {str(e)[:100]}")
        return 0


def main():
    print("=" * 60)
    print("SPRINT 4 — INGESTÃO SIB BRASIL (INDIVIDUALIZADO)")
    print("Motor de Sinistralidade ANS — Tallent Two")
    print("=" * 60)
    print(f"\nCompetência: {COMPETENCIA}")
    print(f"Operadoras-alvo: {len(OPERADORAS_ALVO)}")
    print(f"UFs a processar: {len(UFS)}")
    print()
    
    # Criar tabela no DuckDB
    con = duckdb.connect(DB_PATH, read_only=False)
    
    con.execute("DROP TABLE IF EXISTS sib_granular")
    con.execute("""
        CREATE TABLE sib_granular (
            competencia VARCHAR,
            registro_ans VARCHAR,
            razao_social VARCHAR,
            uf VARCHAR,
            cd_municipio VARCHAR,
            municipio VARCHAR,
            sexo VARCHAR,
            faixa_etaria VARCHAR,
            faixa_etaria_reajuste VARCHAR,
            cd_plano VARCHAR,
            tipo_contratacao VARCHAR,
            segmentacao VARCHAR,
            abrangencia VARCHAR,
            cobertura VARCHAR,
            tipo_vinculo VARCHAR,
            qt_beneficiario_ativo INTEGER,
            qt_beneficiario_aderido INTEGER,
            qt_beneficiario_cancelado INTEGER
        )
    """)
    
    # Processar UFs menores primeiro (download rápido), depois médias, depois grandes
    ufs_ordenadas = UFS_PEQUENAS + UFS_MEDIAS + UFS_GRANDES
    
    total_registros = 0
    ufs_processadas = 0
    ufs_com_dados = 0
    
    for i, uf in enumerate(ufs_ordenadas, 1):
        print(f"\n[{i}/{len(ufs_ordenadas)}] Processando {uf}...")
        
        # Download
        if download_uf(uf):
            # Processar e inserir no DuckDB
            count = process_uf_to_duckdb(uf, con)
            total_registros += count
            ufs_processadas += 1
            if count > 0:
                ufs_com_dados += 1
                print(f"  [DATA] {count:,} registros das operadoras-alvo")
            else:
                print(f"  [VAZIO] Nenhuma operadora-alvo nesta UF")
            
            # Remover CSV para economizar espaço (manter apenas no DuckDB)
            csv_path = f"{DATA_DIR}/pda-024-icb-{uf}-2026_03.csv"
            if os.path.exists(csv_path):
                os.remove(csv_path)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DA INGESTÃO")
    print("=" * 60)
    print(f"UFs processadas: {ufs_processadas}/{len(ufs_ordenadas)}")
    print(f"UFs com dados das operadoras-alvo: {ufs_com_dados}")
    print(f"Total de registros granulares: {total_registros:,}")
    
    # Estatísticas por operadora
    print("\n--- Registros por Operadora ---")
    df = con.execute("""
        SELECT registro_ans, razao_social, 
               COUNT(*) as registros,
               SUM(qt_beneficiario_ativo) as vidas_ativas,
               COUNT(DISTINCT cd_plano) as produtos,
               COUNT(DISTINCT municipio) as municipios
        FROM sib_granular
        GROUP BY registro_ans, razao_social
        ORDER BY vidas_ativas DESC
    """).df()
    print(df.to_string(index=False))
    
    con.close()
    print(f"\n✅ Base granular salva em: {DB_PATH} (tabela: sib_granular)")


if __name__ == "__main__":
    main()
