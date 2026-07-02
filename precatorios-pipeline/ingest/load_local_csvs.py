"""Carrega CSVs já baixados (via wget) para o DuckDB usando pandas como parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from db import get_connection
from logger import get_logger

logger = get_logger("ingest.load_local")
DATA_DIR = Path(__file__).parent.parent / "data"


def load_expedidos():
    """Carrega todos os expedidos_YYYY.csv para raw.sof_expedidos."""
    con = get_connection()
    files = sorted(DATA_DIR.glob("expedidos_*.csv"))

    if not files:
        print("Nenhum arquivo expedidos_*.csv encontrado em data/")
        return 0

    con.execute("DROP TABLE IF EXISTS raw.sof_expedidos")

    all_dfs = []
    for f in files:
        year = f.stem.split("_")[1]
        print(f"  Carregando {f.name} (ano {year})...")
        try:
            df = pd.read_csv(
                f, sep=";", encoding="utf-8",
                on_bad_lines="skip", engine="python", quoting=3
            )
            df["data_download"] = pd.Timestamp.now().date()
            all_dfs.append(df)
            print(f"    → {len(df)} registros")
        except Exception as e:
            print(f"    ⚠️ Erro: {e}")

    if not all_dfs:
        return 0

    combined = pd.concat(all_dfs, ignore_index=True)
    # Todas as colunas como string para evitar conflitos de tipo
    combined = combined.astype(str)

    con.execute("CREATE TABLE raw.sof_expedidos AS SELECT * FROM combined")
    final_count = con.execute("SELECT COUNT(*) FROM raw.sof_expedidos").fetchone()[0]
    print(f"\n  Total raw.sof_expedidos: {final_count} registros")

    # Mostrar colunas
    cols = con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='raw' AND table_name='sof_expedidos'"
    ).fetchall()
    print(f"  Colunas: {[c[0] for c in cols]}")

    con.close()
    return final_count


def load_execucao_orcamentaria():
    """Verifica se execução orçamentária já foi ingerida."""
    con = get_connection()
    try:
        count = con.execute("SELECT COUNT(*) FROM raw.sof_execucao_orcamentaria").fetchone()[0]
        if count > 0:
            print(f"  raw.sof_execucao_orcamentaria já tem {count} registros (ok)")
            con.close()
            return count
    except Exception:
        print("  raw.sof_execucao_orcamentaria não existe ainda — será criada na ingestão SOF")
    con.close()
    return 0


if __name__ == "__main__":
    print("=== Carregando CSVs locais para DuckDB ===")
    n1 = load_execucao_orcamentaria()
    n2 = load_expedidos()
    print(f"\n✓ Total ingerido: {n1 + n2} registros")
