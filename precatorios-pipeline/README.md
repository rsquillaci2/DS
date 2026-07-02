# Pipeline de Oferta Automatizada de Precatórios Federais

Sprint de viabilidade — 2 semanas.

## Objetivo

Testar a viabilidade técnica de gerar **oferta indicativa 100% automatizada** para intermediação de precatórios federais entre FIDCs e cedentes.

## Arquitetura

```
Fontes (SOF, BGU, DataJud, CVM, DJEN)
        │
        ▼
   ┌─────────┐
   │  INGEST  │  → raw.*
   └─────────┘
        │
        ▼
   ┌───────────┐
   │ TRANSFORM │  → stg.* (normalização)
   └───────────┘
        │
        ▼
   ┌────────┐
   │  GOLD   │  → gold.* (cruzamento CNJ)
   └────────┘
        │
        ▼
   ┌─────────────┐
   │ MOTOR v0    │  → Faixa X–Y indicativa
   └─────────────┘
```

**Padrão Medallion:** raw → stg → gold  
**Banco:** DuckDB (analítico, zero infra)  
**Scheduler:** GitHub Actions (cron diário)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env com sua DATAJUD_API_KEY
python db.py  # Inicializa schemas
```

## Módulos

| Módulo | Fonte | Status |
|--------|-------|--------|
| 1a | SOF/MPO (sentenças judiciais) | 🔲 |
| 1b | BGU (estoque federal) | 🔲 |
| 1c | DataJud (metadados CNJ) | 🔲 stub |
| 2 | CVM FIDC (funding intelligence) | 🔲 |
| 3 | DJEN (cessões observadas) | 🔲 |
| 4 | Normalização + gold | 🔲 |
| 5 | Motor de oferta v0 | 🔲 |

## Restrições

- Escopo 100% federal (sem TJs estaduais)
- DataJud = metadados apenas (nunca valores financeiros)
- Toda oferta é indicativa (disclaimer obrigatório)
- Nenhum contato automatizado com cedente neste sprint

## Definição de Pronto

- [ ] 4 fontes ingerindo de forma agendada
- [ ] Banco gold cruzado por CNJ com métricas de qualidade
- [ ] Mapa de demanda (cessionários ativos) atualizando diariamente
- [ ] Motor v0 respondendo faixa X–Y com premissas explicáveis
- [ ] Relatório de viabilidade com taxa de match e gaps
