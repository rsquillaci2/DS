"""Módulo 3 — Robô de cessões no DJEN (Diário de Justiça Eletrônico Nacional).

API Comunica: https://comunicaapi.pje.jus.br/api/v1/comunicacao
Swagger: https://comunica.pje.jus.br/api

NOTA: A API pública do DJEN tem endpoints sem autenticação para consulta.
Endpoints autenticados são de uso exclusivo dos Tribunais.
O endpoint público de busca permite filtrar por conteúdo.

Filtro regex: variações de 'cessão de crédito' + 'precatório'
Extrai: número CNJ, tribunal, cedente, cessionário, valor do crédito cedido
Deduplicação: hash de publicação
"""

import httpx
import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from config import RATE_LIMITS
from logger import get_logger, log_execution

logger = get_logger("ingest.djen")

# API endpoints
DJEN_API_BASE = "https://comunicaapi.pje.jus.br/api/v1"
DJEN_SEARCH_URL = f"{DJEN_API_BASE}/comunicacao"

# Regex para identificar cessões de precatórios
CESSAO_PATTERNS = [
    re.compile(r"cess[ãa]o\s+de\s+cr[ée]dito", re.IGNORECASE),
    re.compile(r"precat[óo]rio", re.IGNORECASE),
]

# Regex para extrair dados da publicação
CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
VALOR_PATTERN = re.compile(r"R\$\s*[\d.,]+")
CEDENTE_PATTERN = re.compile(r"cedente[:\s]+([^,;]+)", re.IGNORECASE)
CESSIONARIO_PATTERN = re.compile(r"cession[áa]rio[:\s]+([^,;]+)", re.IGNORECASE)


def _hash_publication(text: str) -> str:
    """Gera hash SHA256 do texto da publicação para deduplicação."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def _extract_cessao_data(text: str) -> dict | None:
    """Extrai dados estruturados de uma publicação de cessão."""
    # Verificar se é cessão de precatório
    has_cessao = any(p.search(text) for p in CESSAO_PATTERNS)
    if not has_cessao:
        return None

    # Extrair número CNJ
    cnj_match = CNJ_PATTERN.search(text)
    numero_cnj = cnj_match.group(0) if cnj_match else None

    # Extrair valor
    valor_match = VALOR_PATTERN.search(text)
    valor_str = valor_match.group(0) if valor_match else None
    valor = None
    if valor_str:
        try:
            valor = float(
                valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
            )
        except ValueError:
            pass

    # Extrair cedente e cessionário
    cedente_match = CEDENTE_PATTERN.search(text)
    cedente = cedente_match.group(1).strip() if cedente_match else None

    cessionario_match = CESSIONARIO_PATTERN.search(text)
    cessionario = cessionario_match.group(1).strip() if cessionario_match else None

    return {
        "numero_cnj": numero_cnj,
        "cedente": cedente,
        "cessionario": cessionario,
        "valor_credito": valor,
        "hash_publicacao": _hash_publication(text),
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=60))
def _search_djen(params: dict) -> dict | None:
    """Busca na API do DJEN com retry."""
    try:
        resp = httpx.get(
            DJEN_SEARCH_URL,
            params=params,
            timeout=30,
            follow_redirects=True,
        )
        if resp.status_code == 403:
            logger.warning("api_blocked", msg="API retornou 403 — acesso bloqueado por CloudFront")
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning("api_error", status=e.response.status_code)
        return None
    except Exception as e:
        logger.warning("request_failed", error=str(e))
        return None


@log_execution("ingest.djen")
def ingest_cessoes(days_back: int = 30) -> int:
    """
    Ingere cessões de precatórios do DJEN.
    
    NOTA: A API pública do DJEN pode estar bloqueada por CloudFront (403).
    Nesse caso, o módulo registra o erro e retorna 0.
    Em produção, seria necessário:
    1. Solicitar acesso formal ao CNJ, ou
    2. Usar o portal web comunica.pje.jus.br com busca manual, ou
    3. Monitorar cadernos do DJe por tribunal via download direto.
    """
    logger.info("starting", days_back=days_back)

    # Tentar API pública
    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")

    params = {
        "texto": "cessão de crédito precatório",
        "dataInicio": date_from,
        "dataFim": date_to,
        "pagina": 1,
        "tamanhoPagina": 50,
    }

    result = _search_djen(params)

    if result is None:
        logger.warning(
            "api_unavailable",
            msg="API DJEN inacessível (403/CloudFront). "
            "Módulo funcional mas sem dados até acesso ser liberado. "
            "Alternativa: download de cadernos DJe por tribunal."
        )
        print("⚠️  DJEN API: bloqueada (403). Módulo pronto mas sem dados.")
        print("   Alternativas para produção:")
        print("   1. Solicitar acesso formal ao CNJ")
        print("   2. Download de cadernos DJe por tribunal")
        print("   3. Monitorar portal comunica.pje.jus.br")
        return 0

    # Processar resultados
    records = []
    items = result.get("items", result.get("comunicacoes", []))

    for item in items:
        text = item.get("texto", item.get("conteudo", ""))
        data = _extract_cessao_data(text)
        if data:
            data["tribunal"] = item.get("tribunal", item.get("sigla", ""))
            data["data_publicacao"] = item.get("dataPublicacao", item.get("data", ""))
            records.append(data)

    if records:
        import pandas as pd
        df = pd.DataFrame(records)
        con = get_connection()
        # Inserir com deduplicação por hash
        for _, row in df.iterrows():
            try:
                con.execute(
                    """INSERT OR IGNORE INTO raw.djen_cessoes 
                    (numero_cnj, tribunal, cedente, cessionario, valor_credito, 
                     data_publicacao, hash_publicacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    [
                        row.get("numero_cnj"),
                        row.get("tribunal"),
                        row.get("cedente"),
                        row.get("cessionario"),
                        row.get("valor_credito"),
                        row.get("data_publicacao"),
                        row.get("hash_publicacao"),
                    ],
                )
            except Exception:
                pass
        count = con.execute("SELECT COUNT(*) FROM raw.djen_cessoes").fetchone()[0]
        con.close()
        return count

    return len(records)


def run_all():
    """Executa ingestão DJEN."""
    print("=== Ingestão DJEN (Cessões) ===")
    n = ingest_cessoes()
    print(f"  Cessões observadas: {n} registros")
    return n


if __name__ == "__main__":
    run_all()
