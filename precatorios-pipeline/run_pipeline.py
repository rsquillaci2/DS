"""Orquestrador principal — executa pipeline completo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import init_schemas, _create_sequences, get_connection
from ingest.load_local_csvs import load_expedidos, load_execucao_orcamentaria
from ingest.cvm_fidc import ingest_fidc_informes
from ingest.djen import ingest_cessoes
from ingest.datajud import ingest_metadados
from transform.normalize import build_stg_precatorios, build_gold_precatorios, compute_quality_metrics


def run_full_pipeline():
    """Executa pipeline completo de ingestão → normalização → gold."""
    print("=" * 60)
    print("  PIPELINE DE PRECATÓRIOS FEDERAIS — Execução Completa")
    print("=" * 60)

    # 1. Init DB
    print("\n[1/6] Inicializando banco de dados...")
    con = get_connection()
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE SCHEMA IF NOT EXISTS stg")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    con.close()
    _create_sequences()
    init_schemas()

    # 2. Ingestão SOF
    print("\n[2/6] Ingestão SOF/MPO...")
    n_exec = load_execucao_orcamentaria()
    n_exp = load_expedidos()
    print(f"   SOF: {n_exec + n_exp} registros")

    # 3. Ingestão CVM
    print("\n[3/6] Ingestão CVM FIDC...")
    n_cvm = ingest_fidc_informes(n_months=3)
    print(f"   CVM: {n_cvm} registros")

    # 4. Ingestão DJEN
    print("\n[4/6] Ingestão DJEN...")
    n_djen = ingest_cessoes()
    print(f"   DJEN: {n_djen} registros")

    # 5. Ingestão DataJud
    print("\n[5/6] Ingestão DataJud...")
    n_datajud = ingest_metadados()
    print(f"   DataJud: {n_datajud} registros")

    # 6. Normalização
    print("\n[6/6] Normalização e Gold...")
    build_stg_precatorios()
    build_gold_precatorios()
    metrics = compute_quality_metrics()

    # Relatório
    print("\n" + "=" * 60)
    print("  RESULTADO")
    print("=" * 60)
    print(f"  Total gold: {metrics.get('total_registros', 0):,} precatórios")
    print(f"  Cobertura SOF: {metrics.get('cobertura_sof', 0):.1%}")
    print(f"  Cobertura DataJud: {metrics.get('cobertura_datajud', 0):.1%}")
    print(f"  Match SOF↔DataJud: {metrics.get('match_sof_datajud', 0):.1%}")
    print(f"  Nulos valor: {metrics.get('pct_nulo_valor', 0):.1%}")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    run_full_pipeline()
