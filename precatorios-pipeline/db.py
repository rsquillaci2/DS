"""Banco DuckDB — schemas raw, stg, gold."""

import duckdb
from config import DUCKDB_PATH, DATA_DIR


def get_connection() -> duckdb.DuckDBPyConnection:
    """Retorna conexão ao DuckDB, criando o arquivo se necessário."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DUCKDB_PATH))


def init_schemas():
    """Cria schemas e tabelas base do pipeline."""
    con = get_connection()

    # === Schemas ===
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE SCHEMA IF NOT EXISTS stg")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")

    # === RAW tables ===
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.sof_sentencas (
            id INTEGER PRIMARY KEY DEFAULT(nextval('raw.sof_seq')),
            valor_nominal DOUBLE,
            valor_atualizado DOUBLE,
            tribunal_origem VARCHAR,
            natureza_credito VARCHAR,
            exercicio_orcamentario INTEGER,
            beneficiario VARCHAR,
            numero_cnj VARCHAR,
            data_download DATE DEFAULT CURRENT_DATE,
            fonte VARCHAR DEFAULT 'SOF/MPO'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.bgu_estoque (
            id INTEGER PRIMARY KEY DEFAULT(nextval('raw.bgu_seq')),
            exercicio INTEGER,
            estoque_precatorios DOUBLE,
            estoque_rpv DOUBLE,
            data_publicacao DATE,
            data_download DATE DEFAULT CURRENT_DATE,
            fonte VARCHAR DEFAULT 'BGU'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.datajud_processos (
            id INTEGER PRIMARY KEY DEFAULT(nextval('raw.datajud_seq')),
            numero_cnj VARCHAR,
            tribunal VARCHAR,
            orgao_julgador VARCHAR,
            classe VARCHAR,
            assunto VARCHAR,
            data_ingest DATE DEFAULT CURRENT_DATE
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.cvm_fidc (
            id INTEGER PRIMARY KEY DEFAULT(nextval('raw.cvm_seq')),
            cnpj_fundo VARCHAR,
            nome_fundo VARCHAR,
            pl_total DOUBLE,
            carteira_direitos_creditorios DOUBLE,
            num_cotistas INTEGER,
            data_referencia DATE,
            data_download DATE DEFAULT CURRENT_DATE
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.djen_cessoes (
            id INTEGER PRIMARY KEY DEFAULT(nextval('raw.djen_seq')),
            numero_cnj VARCHAR,
            tribunal VARCHAR,
            cedente VARCHAR,
            cessionario VARCHAR,
            valor_credito DOUBLE,
            data_publicacao DATE,
            hash_publicacao VARCHAR UNIQUE,
            data_ingest DATE DEFAULT CURRENT_DATE
        )
    """)

    # === GOLD tables ===
    con.execute("""
        CREATE TABLE IF NOT EXISTS gold.precatorios (
            numero_cnj VARCHAR PRIMARY KEY,
            tribunal VARCHAR,
            natureza_credito VARCHAR,
            exercicio_orcamentario INTEGER,
            valor_nominal DOUBLE,
            valor_atualizado DOUBLE,
            classe_processual VARCHAR,
            assunto VARCHAR,
            fonte_sof BOOLEAN DEFAULT FALSE,
            fonte_datajud BOOLEAN DEFAULT FALSE,
            fonte_djen BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS gold.fundos_compradores (
            cnpj_fundo VARCHAR,
            nome_fundo VARCHAR,
            pl_total DOUBLE,
            carteira_precatorios DOUBLE,
            pct_precatorios DOUBLE,
            num_cotistas INTEGER,
            data_referencia DATE,
            ranking_apetite INTEGER,
            PRIMARY KEY (cnpj_fundo, data_referencia)
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS gold.cessoes_observadas (
            numero_cnj VARCHAR,
            tribunal VARCHAR,
            cessionario VARCHAR,
            valor_credito DOUBLE,
            data_publicacao DATE,
            mes_ref VARCHAR,
            PRIMARY KEY (numero_cnj, cessionario, data_publicacao)
        )
    """)

    con.close()
    print("✓ Schemas e tabelas inicializados com sucesso.")


def _create_sequences():
    """Cria sequences para IDs auto-incrementais."""
    con = get_connection()
    for seq in [
        "raw.sof_seq", "raw.bgu_seq", "raw.datajud_seq",
        "raw.cvm_seq", "raw.djen_seq"
    ]:
        con.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1")
    con.close()


if __name__ == "__main__":
    # Schemas precisam existir antes das sequences
    con = get_connection()
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE SCHEMA IF NOT EXISTS stg")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    con.close()
    _create_sequences()
    init_schemas()
