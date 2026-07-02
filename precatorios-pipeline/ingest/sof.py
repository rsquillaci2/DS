"""Módulo 1a — Ingestão SOF/MPO: sentenças judiciais e execução orçamentária."""

import httpx
import pandas as pd
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from logger import get_logger, log_execution
from ingest.sources import (
    SOF_ORCAMENTARIA_URL,
    SOF_EXPEDICAO_BASE_URL,
    SOF_EXPEDICAO_YEARS,
    SOF_IPCA_URL,
)

logger = get_logger("ingest.sof")


def _download_csv(url: str, encoding: str = "latin-1", max_mb: int = 100) -> pd.DataFrame | None:
    """Baixa CSV de URL (streaming para arquivos grandes) e retorna DataFrame."""
    try:
        # Streaming download para arquivos grandes
        with httpx.stream("GET", url, timeout=httpx.Timeout(300, connect=15), follow_redirects=True) as resp:
            resp.raise_for_status()
            content_length = int(resp.headers.get("content-length", 0))
            if content_length > max_mb * 1024 * 1024:
                logger.warning("file_too_large", url=url, size_mb=content_length // (1024*1024))
                # Baixar apenas primeiras linhas para sample
            chunks = []
            for chunk in resp.iter_bytes():
                chunks.append(chunk)
            content = b"".join(chunks).decode(encoding, errors="replace")
        sep = ";" if ";" in content[:500] else ","
        return pd.read_csv(io.StringIO(content), sep=sep, low_memory=False)
    except Exception as e:
        logger.warning("download_failed", url=url, error=str(e))
        return None


@log_execution("ingest.sof")
def ingest_execucao_orcamentaria() -> int:
    """Ingere série histórica de execução orçamentária (perspectiva orçamentária)."""
    logger.info("starting", source="execucao_orcamentaria")
    df = _download_csv(SOF_ORCAMENTARIA_URL)
    if df is None or df.empty:
        logger.error("empty_dataframe", source="execucao_orcamentaria")
        return 0

    con = get_connection()
    # Gravar em raw como tabela versionada
    con.execute("DROP TABLE IF EXISTS raw.sof_execucao_orcamentaria")
    con.execute(
        "CREATE TABLE raw.sof_execucao_orcamentaria AS SELECT *, CURRENT_DATE as data_download FROM df"
    )
    count = con.execute("SELECT COUNT(*) FROM raw.sof_execucao_orcamentaria").fetchone()[0]
    con.close()
    logger.info("ingested", source="execucao_orcamentaria", rows=count)
    return count


@log_execution("ingest.sof")
def ingest_expedidos(years: list[int] | None = None) -> int:
    """Ingere dados de expedição por ano (perspectiva da expedição)."""
    if years is None:
        years = SOF_EXPEDICAO_YEARS

    all_dfs = []
    for year in years:
        url = SOF_EXPEDICAO_BASE_URL.format(year=year)
        df = _download_csv(url)
        if df is not None and not df.empty:
            df["ano_expedicao"] = year
            all_dfs.append(df)
            logger.info("year_ok", year=year, rows=len(df))
        else:
            logger.warning("year_skip", year=year)

    if not all_dfs:
        return 0

    combined = pd.concat(all_dfs, ignore_index=True)
    con = get_connection()
    con.execute("DROP TABLE IF EXISTS raw.sof_expedidos")
    con.execute(
        "CREATE TABLE raw.sof_expedidos AS SELECT *, CURRENT_DATE as data_download FROM combined"
    )
    count = con.execute("SELECT COUNT(*) FROM raw.sof_expedidos").fetchone()[0]
    con.close()
    logger.info("ingested", source="expedidos", rows=count, years_ok=len(all_dfs))
    return count


@log_execution("ingest.sof")
def ingest_ipca() -> int:
    """Ingere índice de correção IPCA."""
    df = _download_csv(SOF_IPCA_URL)
    if df is None or df.empty:
        return 0

    con = get_connection()
    con.execute("DROP TABLE IF EXISTS raw.sof_ipca")
    con.execute(
        "CREATE TABLE raw.sof_ipca AS SELECT *, CURRENT_DATE as data_download FROM df"
    )
    count = con.execute("SELECT COUNT(*) FROM raw.sof_ipca").fetchone()[0]
    con.close()
    return count


def run_all():
    """Executa toda a ingestão SOF."""
    print("=== Ingestão SOF/MPO ===")
    n1 = ingest_execucao_orcamentaria()
    print(f"  Execução orçamentária: {n1} registros")
    n2 = ingest_expedidos()
    print(f"  Expedidos: {n2} registros")
    n3 = ingest_ipca()
    print(f"  IPCA: {n3} registros")
    print(f"  Total: {n1 + n2 + n3} registros")
    return n1 + n2 + n3


if __name__ == "__main__":
    run_all()
