# Motor de Sinistralidade ANS — MCP Server

## Visão Geral

Servidor MCP (Model Context Protocol) que expõe o Motor de Sinistralidade ANS como ferramenta consultável por agentes de IA (Claude Desktop, Manus, Cursor, etc.).

**Versão:** 1.0 (Sprint 9)  
**Autor:** Ricardo Squillaci — Tallent Two Financial Holding  
**Base de dados:** 943 operadoras | DIOPS 4T/2025 | SIB Mar/2026  

---

## Tools Disponíveis

| Tool | Descrição | Parâmetros |
|------|-----------|------------|
| `buscar_operadora` | Busca por nome ou registro ANS | `termo` (str) |
| `ficha_operadora` | Ficha completa com financeiro, benchmark, vidas e predição | `registro_ans` (str) |
| `ranking_sinistralidade` | Top N por sinistralidade (maior ou menor) | `top_n` (int), `ordem` (str) |
| `ranking_receita` | Top N por volume de receita | `top_n` (int) |
| `benchmark_modalidade` | Referências de mercado por tipo de operadora | — |
| `serie_temporal` | Série histórica trimestral (até 24 trimestres) | `registro_ans`, `ultimos_trimestres` |
| `evolucao_beneficiarios` | Evolução mensal de vidas | `registro_ans`, `ultimos_meses` |
| `predicao_operadora` | Predição XGBoost para próximo trimestre | `registro_ans` |
| `comparar_operadoras` | Comparação lado a lado (até 10) | `registros_ans` (list) |
| `distribuicao_mercado` | Estatísticas gerais do mercado | — |

---

## Instalação

```bash
# Dependências
pip install mcp duckdb

# Testar localmente
cd /home/ubuntu/mvp_sinistralidade
python3 mcp_server.py
```

---

## Configuração no Claude Desktop

Adicionar ao `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "motor-sinistralidade-ans": {
      "command": "python3",
      "args": ["/home/ubuntu/mvp_sinistralidade/mcp_server.py"],
      "env": {}
    }
  }
}
```

---

## Configuração no Manus

Adicionar como Custom MCP via `manus-config`:

```json
{
  "name": "motor-sinistralidade-ans",
  "command": "python3",
  "args": ["/home/ubuntu/mvp_sinistralidade/mcp_server.py"],
  "transport": "stdio"
}
```

---

## Exemplos de Uso

### Buscar operadora
```
"Busque a operadora Hapvida no motor de sinistralidade"
→ buscar_operadora(termo="Hapvida")
```

### Análise completa
```
"Faça uma análise completa da Santa Helena Saúde"
→ buscar_operadora → ficha_operadora → serie_temporal → evolucao_beneficiarios → predicao_operadora
```

### Comparativo
```
"Compare Hapvida, Bradesco e SulAmérica"
→ comparar_operadoras(registros_ans=["368253", "5711", "6246"])
```

### Visão de mercado
```
"Como está o mercado de saúde suplementar?"
→ distribuicao_mercado() + benchmark_modalidade()
```

---

## Prompts Pré-configurados

O servidor inclui 2 prompts prontos:

1. **analise_operadora** — Gera roteiro completo para análise de uma operadora
2. **comparativo_mercado** — Gera roteiro para análise de um segmento

---

## Fontes de Dados

| Fonte | Competência | Registros |
|-------|-------------|-----------|
| DIOPS (ANS) | 4T/2025 | 943 operadoras |
| SIB Consolidado (ANS) | Mar/2026 | 321.677 registros |
| Cadastro de Produtos (ANS) | Mai/2026 | 42.000+ planos |
| Modelo XGBoost v2 | Mai/2026 | R²=0.71, MAE=5.79pp |

---

## Arquitetura

```
mcp_server.py (stdio transport)
    ↓
DuckDB (read-only)
    ↓
ans_analytics.duckdb
    ├── sinistralidade_operadora (943 ops)
    ├── sinistralidade_historica (20.353 registros)
    ├── resultado_benchmark (809 ops)
    ├── predicoes_xgboost (880 ops)
    ├── sib_evolucao_temporal (beneficiários)
    └── operadoras_classificacao (nomes/modalidade)
```
