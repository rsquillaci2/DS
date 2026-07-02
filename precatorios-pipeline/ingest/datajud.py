"""Módulo 1c — DataJud (CNJ): metadados processuais.

IMPORTANTE: Requer API key do DataJud.
Cadastro em: https://datajud-wiki.cnj.jus.br/
Após obter a chave, configurar DATAJUD_API_KEY no .env

RESTRIÇÃO: Usar apenas para metadados (número CNJ, tribunal, classe, assunto).
NUNCA usar para valores financeiros, fila ou status de pagamento.
"""

import httpx
import time
import sys
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from config import DATAJUD_API_KEY, RATE_LIMITS
from logger import get_logger, log_execution

logger = get_logger("ingest.datajud")

# Tribunais Regionais Federais (escopo federal)
TRIBUNAIS_FEDERAIS = {
    "trf1": "https://api-publica.datajud.cnj.jus.br/api_publica_trf1/_search",
    "trf2": "https://api-publica.datajud.cnj.jus.br/api_publica_trf2/_search",
    "trf3": "https://api-publica.datajud.cnj.jus.br/api_publica_trf3/_search",
    "trf4": "https://api-publica.datajud.cnj.jus.br/api_publica_trf4/_search",
    "trf5": "https://api-publica.datajud.cnj.jus.br/api_publica_trf5/_search",
    "trf6": "https://api-publica.datajud.cnj.jus.br/api_publica_trf6/_search",
}

# Classes processuais relevantes para precatórios
CLASSES_PRECATORIO = [
    "12078",  # Precatório
    "12079",  # RPV - Requisição de Pequeno Valor
]

# Rate limiting
_last_request_time = 0.0
_min_interval = 60.0 / RATE_LIMITS["datajud"]


def _rate_limit():
    """Implementa rate limiting simples."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _min_interval:
        time.sleep(_min_interval - elapsed)
    _last_request_time = time.time()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _search_tribunal(tribunal_url: str, query: dict) -> dict:
    """Faz busca em um tribunal com retry e backoff."""
    _rate_limit()
    headers = {
        "Authorization": f"APIKey {DATAJUD_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(tribunal_url, json=query, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _build_query(classe: str, size: int = 100, from_: int = 0) -> dict:
    """Constrói query Elasticsearch para buscar processos por classe."""
    return {
        "size": size,
        "from": from_,
        "query": {
            "bool": {
                "must": [
                    {"match": {"classe.codigo": classe}}
                ]
            }
        },
        "_source": [
            "numeroProcesso",
            "tribunal",
            "orgaoJulgador.nome",
            "classe.nome",
            "assuntos.nome",
        ],
    }


@log_execution("ingest.datajud")
def ingest_metadados(max_per_tribunal: int = 1000) -> int:
    """
    Ingere metadados processuais do DataJud.
    
    STUB: Funcional apenas com DATAJUD_API_KEY configurada.
    Sem a chave, registra warning e retorna 0.
    """
    if not DATAJUD_API_KEY:
        logger.warning(
            "api_key_missing",
            msg="DATAJUD_API_KEY não configurada. "
            "Cadastre-se em https://datajud-wiki.cnj.jus.br/ e configure no .env"
        )
        print("⚠️  DataJud: API key não configurada (stub mode)")
        print("   Cadastro: https://datajud-wiki.cnj.jus.br/")
        return 0

    total_rows = 0
    all_records = []

    for trf_name, trf_url in TRIBUNAIS_FEDERAIS.items():
        for classe in CLASSES_PRECATORIO:
            logger.info("searching", tribunal=trf_name, classe=classe)
            offset = 0
            while offset < max_per_tribunal:
                query = _build_query(classe, size=100, from_=offset)
                try:
                    result = _search_tribunal(trf_url, query)
                    hits = result.get("hits", {}).get("hits", [])
                    if not hits:
                        break

                    for hit in hits:
                        src = hit.get("_source", {})
                        all_records.append({
                            "numero_cnj": src.get("numeroProcesso"),
                            "tribunal": src.get("tribunal", trf_name.upper()),
                            "orgao_julgador": src.get("orgaoJulgador", {}).get("nome"),
                            "classe": src.get("classe", {}).get("nome"),
                            "assunto": "; ".join(
                                a.get("nome", "") for a in src.get("assuntos", [])
                            ),
                        })

                    offset += len(hits)
                    if len(hits) < 100:
                        break
                except Exception as e:
                    logger.warning("search_error", tribunal=trf_name, error=str(e))
                    break

    if all_records:
        import pandas as pd
        df = pd.DataFrame(all_records)
        con = get_connection()
        con.execute("DELETE FROM raw.datajud_processos")
        con.execute(
            "INSERT INTO raw.datajud_processos (numero_cnj, tribunal, orgao_julgador, classe, assunto) "
            "SELECT numero_cnj, tribunal, orgao_julgador, classe, assunto FROM df"
        )
        total_rows = len(df)
        con.close()

    logger.info("ingested", rows=total_rows)
    return total_rows


def run_all():
    """Executa ingestão DataJud."""
    print("=== Ingestão DataJud ===")
    n = ingest_metadados()
    print(f"  Metadados processuais: {n} registros")
    return n


if __name__ == "__main__":
    run_all()
