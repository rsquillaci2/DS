"""Módulo 1b — Ingestão BGU: estoque federal de precatórios + RPVs."""

import httpx
import pandas as pd
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from logger import get_logger, log_execution

logger = get_logger("ingest.bgu")

# Tesouro Transparente — Riscos Fiscais (precatórios)
# A API do Tesouro Transparente fornece dados consolidados
BGU_TESOURO_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "9fa5a4d4-3e6f-4f9c-b8a6-2e8e0f5d2b1a/resource/"
    "riscos-fiscais-precatorios/download/riscos_fiscais_precatorios.csv"
)

# Fallback: dados do SIOP sobre estoque
BGU_SIOP_ESTOQUE_URL = (
    "https://www1.siop.planejamento.gov.br/siopdoc/lib/exe/fetch.php/"
    "dados_abertos:sentencas:serie_execucao_orcamentaria_2008-2025.csv"
)


@log_execution("ingest.bgu")
def ingest_estoque_federal() -> int:
    """
    Ingere estoque federal acumulado de precatórios.
    
    Nota: O BGU propriamente dito não tem API pública direta.
    Usamos a série de execução orçamentária do SOF como proxy do estoque,
    complementada com dados do Tesouro Transparente quando disponíveis.
    """
    logger.info("starting", source="bgu_estoque")

    # Tenta Tesouro Transparente primeiro
    try:
        resp = httpx.get(BGU_TESOURO_URL, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        content = resp.content.decode("utf-8")
        sep = ";" if ";" in content[:500] else ","
        df = pd.read_csv(io.StringIO(content), sep=sep, low_memory=False)
        source = "tesouro_transparente"
    except Exception:
        logger.warning("tesouro_fallback", msg="Usando SOF como proxy de estoque")
        # Fallback: extrair estoque da série orçamentária
        try:
            resp = httpx.get(BGU_SIOP_ESTOQUE_URL, timeout=60, follow_redirects=True)
            resp.raise_for_status()
            content = resp.content.decode("latin-1")
            sep = ";" if ";" in content[:500] else ","
            df = pd.read_csv(io.StringIO(content), sep=sep, low_memory=False)
            source = "sof_proxy"
        except Exception as e:
            logger.error("ingest_failed", error=str(e))
            return 0

    if df.empty:
        return 0

    con = get_connection()
    con.execute("DROP TABLE IF EXISTS raw.bgu_estoque_full")
    con.execute(
        "CREATE TABLE raw.bgu_estoque_full AS SELECT *, "
        f"'{source}' as fonte_real, CURRENT_DATE as data_download FROM df"
    )
    count = con.execute("SELECT COUNT(*) FROM raw.bgu_estoque_full").fetchone()[0]
    con.close()
    logger.info("ingested", source=source, rows=count)
    return count


def run_all():
    """Executa ingestão BGU."""
    print("=== Ingestão BGU ===")
    n = ingest_estoque_federal()
    print(f"  Estoque federal: {n} registros")
    return n


if __name__ == "__main__":
    run_all()
