"""Módulo 5 — Motor de Oferta Indicativa v0.

Dado um número CNJ (ou tribunal + natureza + exercício), retorna faixa de valor X–Y.

Curva de deságio estimada por: tribunal × natureza × exercício orçamentário.
Calibrada com:
  - Duration implícita no exercício previsto (SOF/BGU)
  - Benchmarks públicos de mercado (parametrizáveis)

DISCLAIMER: Toda oferta é indicativa, sujeita a due diligence e confirmação de saldo.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_connection
from logger import get_logger

logger = get_logger("models.motor_oferta")

# === Benchmarks de mercado (parametrizáveis) ===
# Deságio base por duration (anos até pagamento estimado)
# Fonte: mercado secundário de precatórios federais (estimativas públicas 2024-2026)
DESAGIO_BASE = {
    0: 0.05,   # Pagamento no exercício corrente
    1: 0.12,   # 1 ano
    2: 0.18,   # 2 anos
    3: 0.24,   # 3 anos
    4: 0.30,   # 4 anos
    5: 0.35,   # 5+ anos
}

# Ajuste por tribunal (liquidez/risco)
AJUSTE_TRIBUNAL = {
    "TRF1": 0.02,   # Maior volume, mais líquido
    "TRF2": 0.01,
    "TRF3": 0.01,
    "TRF4": 0.00,   # Maior volume, benchmark
    "TRF5": 0.03,   # Menor volume
    "TRF6": 0.03,
    "JF": 0.02,
    "JE": 0.05,     # Estadual (fora do escopo, mas para completude)
    "TJDFT": 0.02,
}

# Ajuste por natureza do crédito
AJUSTE_NATUREZA = {
    "PREVIDÊNCIA": -0.02,      # Alta liquidez, muitos compradores
    "TRIBUTÁRIO": -0.01,       # Boa liquidez
    "ADMINISTRATIVO": 0.01,
    "PESSOAL": 0.02,
    "OUTROS": 0.03,
}

# Spread de incerteza (faixa X–Y)
SPREAD_BASE = 0.05  # ±5% sobre o deságio central


@dataclass
class OfertaIndicativa:
    """Resultado do motor de oferta."""
    numero_cnj: str
    tribunal: str
    natureza: str
    exercicio: int
    valor_nominal: float
    valor_atualizado: float | None
    desagio_min: float
    desagio_max: float
    valor_oferta_min: float
    valor_oferta_max: float
    duration_estimada: int
    premissas: dict
    disclaimer: str = (
        "Oferta indicativa, sujeita a due diligence e confirmação de saldo. "
        "Valores estimados com base em benchmarks públicos de mercado."
    )

    def to_dict(self) -> dict:
        return {
            "numero_cnj": self.numero_cnj,
            "tribunal": self.tribunal,
            "natureza": self.natureza,
            "exercicio": self.exercicio,
            "valor_nominal": self.valor_nominal,
            "valor_atualizado": self.valor_atualizado,
            "faixa_oferta": {
                "min": round(self.valor_oferta_min, 2),
                "max": round(self.valor_oferta_max, 2),
                "moeda": "BRL",
            },
            "desagio": {
                "min_pct": round(self.desagio_min * 100, 2),
                "max_pct": round(self.desagio_max * 100, 2),
            },
            "duration_estimada_anos": self.duration_estimada,
            "premissas": self.premissas,
            "disclaimer": self.disclaimer,
        }


def _estimate_duration(exercicio: int) -> int:
    """Estima duration (anos até pagamento) baseado no exercício orçamentário."""
    current_year = datetime.now().year
    if exercicio is None:
        return 3  # Default conservador
    duration = exercicio - current_year
    return max(0, min(duration, 5))  # Cap em 0-5 anos


def _get_desagio(duration: int, tribunal: str, natureza: str) -> tuple[float, float]:
    """Calcula deságio central e faixa."""
    # Base por duration
    base = DESAGIO_BASE.get(min(duration, 5), 0.35)

    # Ajustes
    adj_tribunal = AJUSTE_TRIBUNAL.get(tribunal, 0.02)
    adj_natureza = AJUSTE_NATUREZA.get(natureza, 0.02)

    desagio_central = base + adj_tribunal + adj_natureza
    desagio_central = max(0.03, min(desagio_central, 0.50))  # Bounds: 3%-50%

    desagio_min = desagio_central - SPREAD_BASE
    desagio_max = desagio_central + SPREAD_BASE

    return max(0.01, desagio_min), min(0.55, desagio_max)


def gerar_oferta(numero_cnj: str = None, tribunal: str = None,
                 natureza: str = None, exercicio: int = None,
                 valor: float = None) -> OfertaIndicativa | None:
    """
    Gera oferta indicativa para um precatório.
    
    Args:
        numero_cnj: Número CNJ ou chave SOF do precatório
        tribunal: Tribunal (se não fornecer CNJ)
        natureza: Natureza do crédito (se não fornecer CNJ)
        exercicio: Exercício orçamentário (se não fornecer CNJ)
        valor: Valor nominal (se não fornecer CNJ)
    
    Returns:
        OfertaIndicativa ou None se não encontrado
    """
    con = get_connection()

    # Buscar no gold
    if numero_cnj:
        result = con.execute("""
            SELECT numero_cnj, tribunal, natureza_credito, exercicio_orcamentario,
                   valor_nominal, valor_atualizado
            FROM gold.precatorios
            WHERE numero_cnj = ?
            LIMIT 1
        """, [str(numero_cnj)]).fetchone()

        if result:
            numero_cnj = result[0]
            tribunal = result[1]
            natureza = result[2]
            exercicio = result[3]
            valor_nominal = result[4]
            valor_atualizado = result[5]
        else:
            con.close()
            return None
    else:
        # Usar parâmetros fornecidos
        valor_nominal = valor
        valor_atualizado = None
        if not all([tribunal, natureza, exercicio, valor]):
            con.close()
            return None

    con.close()

    # Calcular oferta
    try:
        exercicio_int = int(float(exercicio)) if exercicio else None
    except (ValueError, TypeError):
        exercicio_int = None

    duration = _estimate_duration(exercicio_int)
    desagio_min, desagio_max = _get_desagio(duration, tribunal or "", natureza or "")

    try:
        vn = float(valor_nominal) if valor_nominal else 0
    except (ValueError, TypeError):
        vn = 0

    if vn <= 0:
        return None

    valor_oferta_max = vn * (1 - desagio_min)
    valor_oferta_min = vn * (1 - desagio_max)

    premissas = {
        "desagio_base_duration": DESAGIO_BASE.get(min(duration, 5), 0.35),
        "ajuste_tribunal": AJUSTE_TRIBUNAL.get(tribunal, 0.02),
        "ajuste_natureza": AJUSTE_NATUREZA.get(natureza, 0.02),
        "spread_incerteza": SPREAD_BASE,
        "duration_estimada": duration,
        "exercicio_referencia": exercicio_int,
        "ano_corrente": datetime.now().year,
        "fonte_calibracao": "Benchmarks públicos mercado secundário 2024-2026",
        "nota": "Sem dado transacional real (AGU Portaria 225/2026 ainda não ativo)",
    }

    return OfertaIndicativa(
        numero_cnj=str(numero_cnj),
        tribunal=tribunal or "DESCONHECIDO",
        natureza=natureza or "OUTROS",
        exercicio=exercicio_int or 0,
        valor_nominal=vn,
        valor_atualizado=float(valor_atualizado) if valor_atualizado else None,
        desagio_min=desagio_min,
        desagio_max=desagio_max,
        valor_oferta_min=valor_oferta_min,
        valor_oferta_max=valor_oferta_max,
        duration_estimada=duration,
        premissas=premissas,
    )


def buscar_precatorios(tribunal: str = None, natureza: str = None,
                       exercicio: int = None, limit: int = 10) -> list[dict]:
    """Busca precatórios no gold com filtros opcionais."""
    con = get_connection()

    query = "SELECT numero_cnj, tribunal, natureza_credito, exercicio_orcamentario, valor_nominal FROM gold.precatorios WHERE 1=1"
    params = []

    if tribunal:
        query += " AND tribunal = ?"
        params.append(tribunal)
    if natureza:
        query += " AND natureza_credito = ?"
        params.append(natureza)
    if exercicio:
        query += " AND exercicio_orcamentario = ?"
        params.append(exercicio)

    query += f" ORDER BY valor_nominal DESC LIMIT {limit}"

    results = con.execute(query, params).fetchall()
    con.close()

    return [
        {
            "numero_cnj": r[0],
            "tribunal": r[1],
            "natureza": r[2],
            "exercicio": r[3],
            "valor_nominal": r[4],
        }
        for r in results
    ]
