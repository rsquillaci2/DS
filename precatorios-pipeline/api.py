"""FastAPI — Motor de Oferta Indicativa de Precatórios Federais v0."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from models.motor_oferta import gerar_oferta, buscar_precatorios

app = FastAPI(
    title="Motor de Oferta Indicativa — Precatórios Federais",
    description=(
        "API para geração de ofertas indicativas automatizadas "
        "para intermediação de precatórios federais."
    ),
    version="0.1.0",
)


class OfertaRequest(BaseModel):
    """Request para oferta com parâmetros manuais."""
    tribunal: str
    natureza: str
    exercicio: int
    valor: float


class OfertaResponse(BaseModel):
    """Response da oferta indicativa."""
    numero_cnj: str
    tribunal: str
    natureza: str
    exercicio: int
    valor_nominal: float
    valor_atualizado: float | None
    faixa_oferta: dict
    desagio: dict
    duration_estimada_anos: int
    premissas: dict
    disclaimer: str


@app.get("/")
def root():
    """Health check."""
    return {
        "service": "Motor de Oferta Indicativa v0",
        "status": "operational",
        "version": "0.1.0",
    }


@app.get("/oferta/{numero_cnj}", response_model=OfertaResponse)
def get_oferta(numero_cnj: str):
    """
    Gera oferta indicativa para um precatório dado seu número CNJ ou chave SOF.
    
    Retorna faixa de valor X–Y com premissas explicáveis.
    """
    resultado = gerar_oferta(numero_cnj=numero_cnj)

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"Precatório '{numero_cnj}' não encontrado na base."
        )

    return resultado.to_dict()


@app.post("/oferta/manual", response_model=OfertaResponse)
def post_oferta_manual(request: OfertaRequest):
    """
    Gera oferta indicativa com parâmetros manuais (sem busca no banco).
    
    Útil para simulações ou precatórios não presentes na base.
    """
    resultado = gerar_oferta(
        tribunal=request.tribunal,
        natureza=request.natureza,
        exercicio=request.exercicio,
        valor=request.valor,
    )

    if resultado is None:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível gerar oferta com os parâmetros fornecidos."
        )

    return resultado.to_dict()


@app.get("/precatorios")
def list_precatorios(
    tribunal: str = Query(None, description="Filtrar por tribunal (ex: TRF4)"),
    natureza: str = Query(None, description="Filtrar por natureza (ex: PREVIDÊNCIA)"),
    exercicio: int = Query(None, description="Filtrar por exercício orçamentário"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
):
    """Lista precatórios do banco gold com filtros opcionais."""
    results = buscar_precatorios(
        tribunal=tribunal,
        natureza=natureza,
        exercicio=exercicio,
        limit=limit,
    )
    return {"count": len(results), "precatorios": results}


@app.get("/stats")
def get_stats():
    """Retorna estatísticas do banco gold."""
    from db import get_connection
    con = get_connection()

    total = con.execute("SELECT COUNT(*) FROM gold.precatorios").fetchone()[0]
    valor_total = con.execute("SELECT SUM(valor_nominal) FROM gold.precatorios").fetchone()[0] or 0

    dist_tribunal = con.execute("""
        SELECT tribunal, COUNT(*) as qtd, ROUND(SUM(valor_nominal),2) as total
        FROM gold.precatorios GROUP BY tribunal ORDER BY qtd DESC
    """).fetchall()

    dist_natureza = con.execute("""
        SELECT natureza_credito, COUNT(*) as qtd, ROUND(SUM(valor_nominal),2) as total
        FROM gold.precatorios GROUP BY natureza_credito ORDER BY qtd DESC LIMIT 10
    """).fetchall()

    con.close()

    return {
        "total_precatorios": total,
        "valor_nominal_total": valor_total,
        "valor_medio": valor_total / total if total > 0 else 0,
        "por_tribunal": [{"tribunal": r[0], "qtd": r[1], "valor_total": r[2]} for r in dist_tribunal],
        "por_natureza": [{"natureza": r[0], "qtd": r[1], "valor_total": r[2]} for r in dist_natureza],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
