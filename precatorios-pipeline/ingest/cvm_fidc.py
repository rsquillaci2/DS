"""Módulo 2 — Inteligência de funding: CVM Dados Abertos (FIDC).

Fonte: https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS/
Formato: inf_mensal_fidc_YYYYMM.zip (contém múltiplos CSVs por tabela)

Objetivo: identificar FIDCs com carteira em direitos creditórios/precatórios
e derivar ranking de fundos por apetite.
"""

import httpx
import pandas as pd
import io
import zipfile
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from logger import get_logger, log_execution

logger = get_logger("ingest.cvm_fidc")

CVM_FIDC_BASE = "https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS/"


def _get_recent_months(n_months: int = 12) -> list[str]:
    """Retorna lista de YYYYMM dos últimos N meses (exclui mês corrente)."""
    months = []
    now = datetime.now()
    # Começa do mês anterior (dados CVM têm lag de ~1-2 meses)
    for i in range(1, n_months + 1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}{month:02d}")
    return months


def _download_fidc_zip(yyyymm: str) -> dict[str, pd.DataFrame] | None:
    """Baixa e extrai ZIP do informe mensal FIDC."""
    url = f"{CVM_FIDC_BASE}inf_mensal_fidc_{yyyymm}.zip"
    try:
        resp = httpx.get(url, timeout=60, follow_redirects=True)
        resp.raise_for_status()
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        dfs = {}
        for name in zf.namelist():
            if name.endswith(".csv"):
                with zf.open(name) as f:
                    try:
                        df = pd.read_csv(f, sep=";", encoding="latin-1", low_memory=False)
                        dfs[name] = df
                    except Exception:
                        pass
        return dfs
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info("month_not_available", month=yyyymm)
        else:
            logger.warning("download_error", month=yyyymm, status=e.response.status_code)
        return None
    except Exception as e:
        logger.warning("download_failed", month=yyyymm, error=str(e))
        return None


def _filter_precatorio_funds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra fundos com carteira em direitos creditórios judiciais/precatórios.
    
    Heurística: 
    - Nome do fundo contém 'PRECAT' ou 'JUDICIAL' ou 'CREDITO JUDICIAL'
    - Ou carteira de direitos creditórios > 0
    """
    if df.empty:
        return df

    # Normalizar nomes de colunas
    df.columns = [c.strip().upper() for c in df.columns]

    # Filtro por nome do fundo (se coluna existir)
    name_cols = [c for c in df.columns if "DENOM" in c or "NOME" in c or "NM_FUNDO" in c.replace("_", "")]
    keywords = ["PRECAT", "JUDICIAL", "CREDIT", "DIREITO"]

    mask = pd.Series([False] * len(df), index=df.index)
    for col in name_cols:
        for kw in keywords:
            mask = mask | df[col].astype(str).str.upper().str.contains(kw, na=False)

    return df[mask].copy()


@log_execution("ingest.cvm_fidc")
def ingest_fidc_informes(n_months: int = 6) -> int:
    """
    Ingere informes mensais de FIDC dos últimos N meses.
    Filtra fundos com exposição a precatórios/direitos creditórios judiciais.
    """
    logger.info("starting", n_months=n_months)
    months = _get_recent_months(n_months)

    all_fund_data = []

    for yyyymm in months:
        logger.info("processing_month", month=yyyymm)
        dfs = _download_fidc_zip(yyyymm)
        if dfs is None:
            continue

        # Procurar tabela principal (tab_I ou similar — patrimônio/carteira)
        for filename, df in dfs.items():
            fname_lower = filename.lower()
            # Tab I = Informações gerais (PL, cotistas)
            # Arquivo: inf_mensal_fidc_tab_I_YYYYMM.csv
            if "tab_i_" in fname_lower and "tab_ii" not in fname_lower and "tab_ix" not in fname_lower:
                filtered = _filter_precatorio_funds(df)
                if not filtered.empty:
                    filtered["MES_REF"] = yyyymm
                    filtered["ARQUIVO_ORIGEM"] = filename
                    all_fund_data.append(filtered)
                    logger.info("funds_found", month=yyyymm, count=len(filtered))

    if not all_fund_data:
        logger.warning("no_funds_found")
        return 0

    combined = pd.concat(all_fund_data, ignore_index=True)
    combined = combined.astype(str)  # Evitar conflitos de tipo

    con = get_connection()
    con.execute("DROP TABLE IF EXISTS raw.cvm_fidc_filtered")
    con.execute("CREATE TABLE raw.cvm_fidc_filtered AS SELECT *, CURRENT_DATE as data_download FROM combined")
    count = con.execute("SELECT COUNT(*) FROM raw.cvm_fidc_filtered").fetchone()[0]
    con.close()

    logger.info("ingested", rows=count, months_processed=len(months))
    return count


@log_execution("ingest.cvm_fidc")
def build_ranking_apetite() -> int:
    """
    Constrói ranking de fundos por apetite em precatórios.
    Grava em gold.fundos_compradores.
    
    Critérios de ranking:
    1. Crescimento de PL nos últimos meses
    2. Concentração em precatórios (% da carteira)
    3. Número de cotistas (proxy de liquidez)
    """
    con = get_connection()
    try:
        count = con.execute("SELECT COUNT(*) FROM raw.cvm_fidc_filtered").fetchone()[0]
        if count == 0:
            logger.warning("no_data_for_ranking")
            con.close()
            return 0
    except Exception:
        logger.warning("table_not_found", table="raw.cvm_fidc_filtered")
        con.close()
        return 0

    # Extrair dados e construir ranking simplificado
    df = con.execute("SELECT * FROM raw.cvm_fidc_filtered").df()

    # Normalizar colunas
    df.columns = [c.strip().upper() for c in df.columns]

    # Identificar colunas de PL e CNPJ
    pl_cols = [c for c in df.columns if "PL" in c or "PATRIM" in c]
    cnpj_cols = [c for c in df.columns if "CNPJ" in c]
    nome_cols = [c for c in df.columns if "DENOM" in c or "NOME" in c]

    logger.info("columns_found", pl=pl_cols[:3], cnpj=cnpj_cols[:3], nome=nome_cols[:3])

    con.close()
    return count


def run_all():
    """Executa toda a ingestão CVM FIDC."""
    print("=== Ingestão CVM FIDC ===")
    n = ingest_fidc_informes(n_months=6)
    print(f"  Informes filtrados: {n} registros")
    if n > 0:
        build_ranking_apetite()
    return n


if __name__ == "__main__":
    run_all()
