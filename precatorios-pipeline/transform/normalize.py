"""Módulo 4 — Normalização e banco gold unificado.

Camada stg: padronizar número CNJ, nomes de tribunal, natureza do crédito.
Camada gold: fato central gold.precatorios cruzando SOF × DataJud × cessões.
Chave primária: número CNJ (formato padronizado).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_connection
from logger import get_logger, log_execution

logger = get_logger("transform.normalize")


def _normalize_cnj(raw: str) -> str | None:
    """
    Normaliza número CNJ para formato padrão: NNNNNNN-DD.AAAA.J.TR.OOOO
    Aceita variações com/sem pontuação.
    """
    if not raw or raw == "nan" or raw == "None":
        return None

    # Remove tudo que não é dígito
    digits = re.sub(r"\D", "", str(raw))

    if len(digits) == 20:
        # Formato: NNNNNNN DD AAAA J TR OOOO
        return f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:20]}"
    elif len(digits) == 7:
        # Apenas chave SOF (sem CNJ completo)
        return None

    return None


def _normalize_tribunal(raw: str) -> str:
    """Padroniza nome de tribunal."""
    if not raw or raw == "nan":
        return "DESCONHECIDO"

    raw = str(raw).strip().upper()

    # Mapeamento de variações
    mappings = {
        "TRIBUNAL REGIONAL FEDERAL DA 1": "TRF1",
        "TRIBUNAL REGIONAL FEDERAL DA 2": "TRF2",
        "TRIBUNAL REGIONAL FEDERAL DA 3": "TRF3",
        "TRIBUNAL REGIONAL FEDERAL DA 4": "TRF4",
        "TRIBUNAL REGIONAL FEDERAL DA 5": "TRF5",
        "TRIBUNAL REGIONAL FEDERAL DA 6": "TRF6",
        "TRIBUNAL DE JUSTIÇA DO DISTRITO": "TJDFT",
        "JUSTIÇA FEDERAL": "JF",
        "JUSTIÇA ESTADUAL": "JE",
    }

    for key, value in mappings.items():
        if key in raw:
            return value

    # Se já é sigla curta
    if len(raw) <= 6:
        return raw

    return raw[:30]


def _normalize_natureza(raw: str) -> str:
    """Padroniza natureza do crédito (Class_NFGC do SOF)."""
    if not raw or raw == "nan":
        return "OUTROS"
    return str(raw).strip().upper()


@log_execution("transform.normalize")
def build_stg_precatorios() -> int:
    """Constrói tabela stg.precatorios a partir de raw.sof_expedidos."""
    con = get_connection()

    # Verificar se raw.sof_expedidos existe
    try:
        count = con.execute("SELECT COUNT(*) FROM raw.sof_expedidos").fetchone()[0]
        logger.info("source_count", table="raw.sof_expedidos", rows=count)
    except Exception:
        logger.error("table_missing", table="raw.sof_expedidos")
        con.close()
        return 0

    # Extrair dados relevantes
    df = con.execute("""
        SELECT 
            "Chave" as chave,
            "Exercício" as exercicio,
            "Código do Tribunal" as cod_tribunal,
            "Nome do Tribunal" as nome_tribunal,
            "Tipo de Causa" as tipo_causa,
            "Valor Original do Precatório" as valor_original,
            "Valor Atualizado" as valor_atualizado,
            "Class_NFGC" as natureza,
            "Class_Tribunais" as class_tribunais,
            "DataInicio" as data_inicio,
            "DataFim" as data_fim
        FROM raw.sof_expedidos
    """).df()

    # Normalizar
    df["tribunal_norm"] = df["nome_tribunal"].apply(_normalize_tribunal)
    df["natureza_norm"] = df["natureza"].apply(_normalize_natureza)

    # Converter valores numéricos
    df["valor_nominal"] = df["valor_original"].apply(
        lambda x: float(str(x).replace(",", ".")) if x and str(x) != "nan" else None
    )
    df["valor_atual"] = df["valor_atualizado"].apply(
        lambda x: float(str(x).replace(",", ".")) if x and str(x) != "nan" else None
    )
    df["exercicio_int"] = df["exercicio"].apply(
        lambda x: int(float(x)) if x and str(x) != "nan" else None
    )

    # Gravar em stg
    con.execute("DROP TABLE IF EXISTS stg.precatorios")
    con.execute("""
        CREATE TABLE stg.precatorios AS 
        SELECT 
            chave,
            exercicio_int as exercicio,
            cod_tribunal,
            tribunal_norm as tribunal,
            tipo_causa,
            valor_nominal,
            valor_atual,
            natureza_norm as natureza,
            class_tribunais,
            data_inicio,
            data_fim
        FROM df
        WHERE valor_nominal IS NOT NULL
    """)

    final_count = con.execute("SELECT COUNT(*) FROM stg.precatorios").fetchone()[0]
    con.close()
    logger.info("stg_built", rows=final_count)
    return final_count


@log_execution("transform.normalize")
def build_gold_precatorios() -> int:
    """
    Constrói gold.precatorios — tabela fato central.
    Cruza SOF (stg) com DataJud (quando disponível).
    """
    con = get_connection()

    try:
        stg_count = con.execute("SELECT COUNT(*) FROM stg.precatorios").fetchone()[0]
    except Exception:
        logger.error("stg_missing")
        con.close()
        return 0

    # Construir gold a partir de stg (SOF é a fonte principal)
    con.execute("DROP TABLE IF EXISTS gold.precatorios")
    con.execute("""
        CREATE TABLE gold.precatorios AS
        SELECT 
            chave as numero_cnj,
            tribunal,
            natureza as natureza_credito,
            exercicio as exercicio_orcamentario,
            valor_nominal,
            valor_atual as valor_atualizado,
            tipo_causa as classe_processual,
            natureza as assunto,
            TRUE as fonte_sof,
            FALSE as fonte_datajud,
            FALSE as fonte_djen,
            CURRENT_TIMESTAMP as updated_at
        FROM stg.precatorios
    """)

    # Tentar cruzar com DataJud (se houver dados)
    try:
        datajud_count = con.execute("SELECT COUNT(*) FROM raw.datajud_processos").fetchone()[0]
        if datajud_count > 0:
            # Atualizar flag fonte_datajud onde houver match
            con.execute("""
                UPDATE gold.precatorios 
                SET fonte_datajud = TRUE
                WHERE numero_cnj IN (SELECT numero_cnj FROM raw.datajud_processos)
            """)
            match_count = con.execute(
                "SELECT COUNT(*) FROM gold.precatorios WHERE fonte_datajud = TRUE"
            ).fetchone()[0]
            logger.info("datajud_match", matched=match_count, total=stg_count)
    except Exception:
        logger.info("datajud_not_available")

    final_count = con.execute("SELECT COUNT(*) FROM gold.precatorios").fetchone()[0]
    con.close()
    logger.info("gold_built", rows=final_count)
    return final_count


@log_execution("transform.normalize")
def compute_quality_metrics() -> dict:
    """Calcula métricas de qualidade do banco gold."""
    con = get_connection()

    metrics = {}

    try:
        total = con.execute("SELECT COUNT(*) FROM gold.precatorios").fetchone()[0]
        metrics["total_registros"] = total

        # Cobertura por fonte
        sof = con.execute("SELECT COUNT(*) FROM gold.precatorios WHERE fonte_sof").fetchone()[0]
        datajud = con.execute("SELECT COUNT(*) FROM gold.precatorios WHERE fonte_datajud").fetchone()[0]
        djen = con.execute("SELECT COUNT(*) FROM gold.precatorios WHERE fonte_djen").fetchone()[0]

        metrics["cobertura_sof"] = sof / total if total > 0 else 0
        metrics["cobertura_datajud"] = datajud / total if total > 0 else 0
        metrics["cobertura_djen"] = djen / total if total > 0 else 0

        # Taxa de match SOF↔DataJud
        metrics["match_sof_datajud"] = datajud / sof if sof > 0 else 0

        # Nulos em campos críticos
        nulos_valor = con.execute(
            "SELECT COUNT(*) FROM gold.precatorios WHERE valor_nominal IS NULL"
        ).fetchone()[0]
        nulos_tribunal = con.execute(
            "SELECT COUNT(*) FROM gold.precatorios WHERE tribunal IS NULL OR tribunal = 'DESCONHECIDO'"
        ).fetchone()[0]

        metrics["pct_nulo_valor"] = nulos_valor / total if total > 0 else 0
        metrics["pct_nulo_tribunal"] = nulos_tribunal / total if total > 0 else 0

        # Distribuição por tribunal
        dist_tribunal = con.execute("""
            SELECT tribunal, COUNT(*) as qtd, 
                   ROUND(AVG(valor_nominal), 2) as valor_medio,
                   ROUND(SUM(valor_nominal), 2) as valor_total
            FROM gold.precatorios 
            WHERE valor_nominal IS NOT NULL
            GROUP BY tribunal 
            ORDER BY qtd DESC 
            LIMIT 10
        """).df()
        metrics["top_tribunais"] = dist_tribunal.to_dict("records")

        # Distribuição por natureza
        dist_natureza = con.execute("""
            SELECT natureza_credito, COUNT(*) as qtd,
                   ROUND(SUM(valor_nominal), 2) as valor_total
            FROM gold.precatorios 
            GROUP BY natureza_credito 
            ORDER BY qtd DESC 
            LIMIT 10
        """).df()
        metrics["top_naturezas"] = dist_natureza.to_dict("records")

        # Distribuição por exercício
        dist_exercicio = con.execute("""
            SELECT exercicio_orcamentario, COUNT(*) as qtd,
                   ROUND(SUM(valor_nominal), 2) as valor_total
            FROM gold.precatorios 
            WHERE exercicio_orcamentario IS NOT NULL
            GROUP BY exercicio_orcamentario 
            ORDER BY exercicio_orcamentario DESC
        """).df()
        metrics["por_exercicio"] = dist_exercicio.to_dict("records")

    except Exception as e:
        logger.error("metrics_error", error=str(e))

    con.close()
    return metrics


def run_all():
    """Executa normalização completa."""
    print("=== Módulo 4: Normalização e Gold ===")

    print("\n1. Construindo stg.precatorios...")
    n1 = build_stg_precatorios()
    print(f"   → {n1} registros normalizados")

    print("\n2. Construindo gold.precatorios...")
    n2 = build_gold_precatorios()
    print(f"   → {n2} registros no gold")

    print("\n3. Métricas de qualidade:")
    metrics = compute_quality_metrics()
    print(f"   Total: {metrics.get('total_registros', 0)}")
    print(f"   Cobertura SOF: {metrics.get('cobertura_sof', 0):.1%}")
    print(f"   Cobertura DataJud: {metrics.get('cobertura_datajud', 0):.1%}")
    print(f"   Match SOF↔DataJud: {metrics.get('match_sof_datajud', 0):.1%}")
    print(f"   Nulos valor: {metrics.get('pct_nulo_valor', 0):.1%}")
    print(f"   Nulos tribunal: {metrics.get('pct_nulo_tribunal', 0):.1%}")

    if metrics.get("top_tribunais"):
        print("\n   Top tribunais:")
        for t in metrics["top_tribunais"][:5]:
            print(f"     {t['tribunal']}: {t['qtd']} prec. (média R$ {t.get('valor_medio', 0):,.0f})")

    return metrics


if __name__ == "__main__":
    run_all()
