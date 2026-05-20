# Motor de Sinistralidade ANS — Documento Técnico

**Produto:** Motor de Sinistralidade e Precificação por Produto via Dados ANS Públicos  
**Proprietário:** Tallent Two Financial Holding  
**Versão:** v2.1  
**Data:** 20 de Maio de 2026  
**Classificação:** Interno — Uso Estratégico

---

## 1. Stack Tecnológico Consolidado

### 1.1 Infraestrutura e Runtime

| Camada | Tecnologia | Versão | Função |
|---|---|---|---|
| Runtime | Python | 3.11 | Linguagem principal de todo o pipeline |
| Banco de Dados | DuckDB | 1.x | Banco analítico colunar, single-file, zero-config |
| Interface | Streamlit | 1.57 | Dashboard interativo com deploy instantâneo |
| Visualização | Plotly Express + Graph Objects | 5.x | Gráficos interativos executivos |
| Componentes HTML | Streamlit Components | 1.x | Renderização de KPIs customizados |
| Versionamento | Git + GitHub | — | Repositório `rsquillaci2/DS` |

### 1.2 Stack de Dados

| Componente | Tecnologia | Descrição |
|---|---|---|
| Ingestão | `requests` + `curl` | Download direto do FTP/HTTP da ANS |
| Parsing | `pandas` + DuckDB `read_csv_auto` | Leitura de CSVs com schemas variáveis |
| Armazenamento | DuckDB (`ans_analytics.duckdb`) | Banco único de 34MB com todas as tabelas |
| Transformação | SQL (DuckDB) + Python | ETL em scripts dedicados por sprint |
| Exportação | CSV + JSON | Resultados exportáveis pelo dashboard |

### 1.3 Fontes de Dados Integradas

| Fonte | Origem | Formato | Volume | Frequência |
|---|---|---|---|---|
| DIOPS | ANS/FTP | CSV (ZIP) | 926.610 registros (4T/2025) | Trimestral |
| DIOPS Histórico | ANS/FTP | CSV (ZIP) | 24 trimestres (2020-2025) | Trimestral |
| SIB Consolidado | ANS/FTP | CSV (ZIP) | 1.734.056 registros | Mensal |
| SIB Individualizado | ANS/FTP | CSV (ZIP) | 696.183 registros (6 ops, 28 UFs) | Mensal |
| Cadastro de Produtos | ANS/FTP | CSV | 937+ produtos médico-hospitalares | Contínua |
| Cadastro de Operadoras | ANS/FTP | CSV | 6 operadoras-alvo | Contínua |
| VCMH/IESS | IESS (publicação) | Manual | 27 UFs × 6 anos | Anual |
| Pesquisa UNIDAS | UNIDAS (publicação) | Manual | Custo per capita regional | Anual |

### 1.4 Banco de Dados — Schema Atual

```
ans_analytics.duckdb (34 MB)
├── sinistralidade_operadora     → 6 registros (resumo financeiro por operadora)
├── sib_operadoras               → 1.734.056 registros (beneficiários consolidados)
├── sib_granular                 → 696.183 registros (Sprint 4: Produto × Município × Faixa)
├── produtos_ans                 → 937 registros (características de produtos)
├── resultado_proxy              → 937 registros (Sprint 2: proxy por produto)
├── score_risco_produto_agg      → 1.793 registros (Sprint 5: score por produto)
├── score_risco_uf               → 27 registros (Sprint 5: custo per capita por UF)
├── sinistralidade_historica     → 132 registros (Sprint 6: série temporal)
├── benchmark_referencia         → 5 registros (Sprint 7: benchmarks por tipo)
├── resultado_benchmark          → 6 registros (Sprint 7: classificação por operadora)
├── predicoes_operadora          → 6 registros (Sprint 8: predições XGBoost)
└── diops_raw                    → 926.610 registros (dados brutos DIOPS)
```

### 1.5 Arquitetura de Arquivos

```
/home/ubuntu/mvp_sinistralidade/
├── dashboard.py                 → Dashboard Streamlit v2.0 (1.186 linhas)
├── etl_ingestao.py              → Sprint 1-2: Ingestão inicial DIOPS + SIB
├── motor_sinistralidade.py      → Sprint 2: Motor de proxy por produto
├── sprint4_ingestao_sib.py      → Sprint 4: Ingestão SIB Brasil (28 UFs)
├── sprint5_score_risco.py       → Sprint 5: Score de Risco Atuarial
├── sprint6_serie_temporal.py    → Sprint 6: Série temporal DIOPS
├── sprint6_fix.py               → Sprint 6: Correção de formatos CSV
├── sprint7_benchmark.py         → Sprint 7: Benchmark IESS
├── sprint8_xgboost.py           → Sprint 8: Modelo Preditivo XGBoost
├── pagina_predicao.py           → Sprint 8: Página de ML para o Dashboard
├── fatores_atuariais.md         → Documentação dos fatores de ponderação
├── benchmark_iess_data.md       → Dados de benchmark coletados
├── logo_t2_sidebar.png          → Logo Tallent Two (PNG 540px)
├── data/
│   ├── ans_analytics.duckdb     → Banco principal (34 MB)
│   ├── diops_4t2025.csv         → DIOPS raw (77 MB)
│   ├── sib_consolidado.csv      → SIB consolidado (37 MB)
│   ├── produtos_ans.csv         → Cadastro de produtos (11 MB)
│   ├── sib_individual/          → SIB por UF (28 arquivos)
│   └── diops_historico/         → DIOPS 2020-2025 (24 ZIPs)
└── operadoras_ativas.csv        → Cadastro de operadoras ANS
```

### 1.6 Operadoras na Base

| # | Operadora | Registro ANS | Porte | Tipo | DIOPS | SIB Granular | Score |
|---|---|---|---|---|---|---|---|
| 1 | Pessoal Saúde | 310239 | ~12.500 vidas | Medicina de Grupo | ✅ | ✅ (1.031 reg.) | ✅ |
| 2 | Santa Helena Saúde | 355097 | ~194k vidas | Medicina de Grupo | ✅ | ✅ (11.144 reg.) | ✅ |
| 3 | Hapvida NotreDame | 359017 | ~6M vidas | Med. Grupo Verticalizada | ✅ | ✅ (672.004 reg.) | ✅ |
| 4 | Portomed (Porto Saúde) | 417491 | N/D | Seguradora | ✅ | ❌ | ❌ |
| 5 | Santa Casa de Mauá | 421197 | ~9-11k vidas | Filantropia Verticalizada | ✅ | ✅ (4.537 reg.) | ✅ |
| 6 | SF Sistemas (Sagrada Família) | 422371 | ~32k vidas | Med. Grupo Verticalizada | ✅ | ✅ (7.467 reg.) | ✅ |

---

## 2. Sprints Concluídos — Detalhamento

### Sprint 1 — Sinistralidade por Operadora

**Objetivo:** Calcular a sinistralidade real (Despesa/Receita) de cada operadora usando dados financeiros oficiais.

**O que foi feito:**
- Download do DIOPS 4T/2025 (77MB, 926.610 registros financeiros)
- Download do SIB Consolidado Mar/2026 (37MB, 1.734.056 registros de beneficiários)
- Parsing e carga em DuckDB com tratamento de schemas variáveis (separador `;`, encoding Latin-1)
- Cálculo: `Sinistralidade = Conta 411x (Eventos/Sinistros) / Conta 311x (Contraprestações)`
- Validação cruzada com dados publicados pela ANS

**Resultado:**

| Operadora | Receita (R$) | Despesa (R$) | Sinistralidade |
|---|---|---|---|
| Pessoal Saúde | 116M | 76M | 65.8% |
| SF Sistemas | 168M | 128M | 76.1% |
| Hapvida NDI | 39.6B | 30.2B | 76.4% |
| Portomed | 86M | 67M | 77.9% |
| Santa Casa Mauá | 383M | 300M | 78.2% |
| Santa Helena | 3.1B | 2.6B | 84.5% |

**Desafios técnicos resolvidos:**
- Tipos de dados incompatíveis (REG_ANS como BIGINT vs VARCHAR)
- CSVs com linhas malformadas (flag `ignore_errors=true`)
- Conta contábil como string vs número

---

### Sprint 2 — Motor de Proxy por Produto

**Objetivo:** Estimar a sinistralidade de cada produto individual usando fatores de ponderação baseados em literatura atuarial.

**O que foi feito:**
- Cruzamento do Cadastro de Produtos ANS (937 produtos) com o DIOPS
- Implementação de 5 fatores multiplicativos:
  - Fator de Segmentação (Odonto 0.4 → Referência 1.15)
  - Fator de Contratação (Empresarial 0.85 → Individual 1.20)
  - Fator de Abrangência (Municipal 0.85 → Nacional 1.15)
  - Fator de Moderação (Coparticipação+Franquia 0.82 → Ausente 1.05)
  - Fator de Faixa de Preço (normalizado pela média)
- Cálculo: `Sinistralidade_Proxy(produto) = Sinistralidade_Operadora × Peso_Relativo`
- Classificação de qualidade da estimativa (Alta/Média/Baixa)

**Resultado:** 937 produtos com sinistralidade proxy calculada, variando de 38% (odontológico coletivo empresarial com coparticipação) a 112% (individual referência sem moderador).

---

### Sprint 3 — Prova de Conceito de Granularidade

**Objetivo:** Validar se é possível descer para a granularidade de Produto × Município × Faixa Etária usando dados públicos.

**O que foi feito:**
- Download do SIB Individualizado de Roraima (UF menor, para teste rápido)
- Descoberta da chave de vinculação: `CD_PLANO_RPS` (SIB) = `CD_PLANO` (Cadastro de Produtos)
- Teste de match: 100% de correspondência entre os datasets
- Mapeamento de campos disponíveis: UF, município, faixa etária, sexo, tipo de contratação, segmentação, titular/dependente

**Resultado:** Viabilidade confirmada. O SIB Individualizado contém a granularidade necessária para o rateio atuarial.

---

### Sprint 4 — Ingestão SIB Brasil

**Objetivo:** Baixar e processar o SIB Individualizado de todos os 28 estados brasileiros, filtrando apenas as 6 operadoras-alvo.

**O que foi feito:**
- Script ETL otimizado com download incremental (estados menores primeiro)
- Retry automático com timeout progressivo (60s → 300s → 600s)
- Processamento em streaming: download → filtro → append ao DuckDB
- 28/28 UFs processadas com sucesso (incluindo SP com 478k registros)

**Resultado:**

| Operadora | Registros | Vidas Ativas | Produtos | Municípios |
|---|---|---|---|---|
| Hapvida NDI | 672.004 | 5.891.184 | 1.702 | 3.479 |
| Santa Helena | 11.144 | 188.371 | 37 | 224 |
| SF Sistemas | 7.467 | 47.739 | 17 | 104 |
| Santa Casa Mauá | 4.537 | 31.100 | 31 | 25 |
| Pessoal Saúde | 1.031 | 11.249 | 8 | 22 |
| **Total** | **696.183** | **6.169.643** | **1.795** | **3.854** |

**Desafios técnicos resolvidos:**
- Arquivos grandes (SP = 128MB) com timeout de rede
- Estratégia de ordenação por tamanho (menores primeiro para garantir dados parciais)
- Portomed não aparece no SIB (provavelmente opera sob outro registro)

---

### Sprint 5 — Score de Risco Atuarial

**Objetivo:** Distribuir a despesa assistencial do DIOPS proporcionalmente ao risco de cada cluster (Produto × Município), gerando sinistralidade estimada real por produto.

**O que foi feito:**
- Implementação da curva etária da ANS (RN 63/2003 + UNIDAS 2023):
  - 0-18: 1.0, 19-23: 1.0, 24-28: 1.1, 29-33: 1.2, 34-38: 1.5, 39-43: 1.8, 44-48: 2.2, 49-53: 2.8, 54-58: 3.5, 59+: 4.5
- Implementação de fatores geográficos por UF (27 estados):
  - SP: 1.15, RJ: 1.12, DF: 1.10, ..., RR: 0.72, AP: 0.72
- Cálculo: `Score = Vidas × F_Etário × F_Geográfico × F_Segmentação × F_Contratação`
- Rateio: `Despesa_Produto = (Score_Produto / Σ Scores) × Despesa_Total_Operadora`
- Custo per capita: `Despesa_Produto / Vidas_Produto / 12`

**Resultado:**

| Métrica | Valor |
|---|---|
| Clusters calculados | 59.635 (Produto × Município) |
| Produtos com score | 1.793 |
| Custo per capita mais alto | R$ 1.771/mês (Santa Helena, Individual) |
| Custo per capita mais baixo | R$ 209/mês (SF Sistemas, Coletivo Empresarial) |
| Variação geográfica | DF R$519 vs MA R$263 (2× de diferença) |

---

### Sprint 6 — Série Temporal

**Objetivo:** Expandir o DIOPS para 20+ trimestres (2020-2025) e calcular tendências de sinistralidade.

**O que foi feito:**
- Download de 24 trimestres de DIOPS (1T/2020 a 4T/2025)
- Tratamento de 3 formatos diferentes de CSV (2020-2021: 5 cols, 2022-2024: 6 cols, 2025: 6 cols com separador diferente)
- Cálculo de sinistralidade trimestral isolada (delta entre acumulados)
- Cálculo de CAGR de receita e variação de sinistralidade no período

**Resultado:**
- 132 registros históricos (6 operadoras × ~22 trimestres)
- Todas as operadoras apresentam tendência de piora na sinistralidade (pós-COVID + inflação médica)
- Hapvida NDI: de 31.1% (1T/2020) para 76.4% (4T/2025) — efeito da fusão com NDI
- Santa Helena: pressão constante, de 27.1% para 84.5%

**Desafios técnicos resolvidos:**
- Dados acumulados (1T = Jan-Mar, 2T = Jan-Jun) exigem cálculo de delta
- Formatos de data inconsistentes ("01/01/2020" vs "2022/01/01" vs "2025-10-01")
- SF Sistemas só tem dados a partir de 2023

---

### Sprint 7 — Benchmark IESS e Calibração Geográfica

**Objetivo:** Integrar dados de referência do mercado (IESS, ANS, UNIDAS) para permitir comparação e calibrar os fatores geográficos.

**O que foi feito:**
- Coleta de dados de benchmark:
  - VCMH/IESS (Variação de Custos Médico-Hospitalares): série 2019-2025
  - Panorama ANS 2024: sinistralidade média do setor (82.2%)
  - Pesquisa UNIDAS 2023: custo per capita por região
- Definição de benchmarks por tipo de operadora:
  - Grandes verticalizadas: 80%, Médias: 83%, Pequenas: 86%, Filantropia: 90%
- Classificação: Eficiente (< benchmark - 5pp) / Na Média / Sob Pressão (> benchmark + 5pp)
- Calibração dos 27 fatores geográficos com dados VCMH reais

**Resultado:**

| Operadora | Sinist. Real | Benchmark | Delta | Classificação |
|---|---|---|---|---|
| Pessoal Saúde | 65.8% | 86.0% | -20.2 pp | Eficiente |
| Santa Casa Mauá | 78.2% | 90.0% | -11.8 pp | Eficiente |
| SF Sistemas | 76.1% | 83.0% | -6.9 pp | Eficiente |
| Hapvida NDI | 76.4% | 80.0% | -3.6 pp | Na Média |
| Santa Helena | 84.5% | 83.0% | +1.5 pp | Na Média |

---

### Sprint 8 — Modelo Preditivo XGBoost

**Objetivo:** Implementar modelo de Machine Learning para predizer sinistralidade futura por operadora e classificar risco por produto.

**O que foi feito:**
- Construção de dois modelos XGBoost: Regressão (operadoras/série temporal) e Classificação (produtos/cross-section)
- Engenharia de features: lags de sinistralidade, CAGRs, fatores atuariais, benchmarks
- Treinamento e validação cruzada (TimeSeriesSplit e StratifiedKFold)
- Implementação de explicabilidade com SHAP Values (feature importance e waterfall)
- Serialização dos modelos com `joblib` para uso em produção
- Integração ao dashboard com a nova página "Predição (ML)"

**Resultados Alcançados:**

| Métrica | Modelo 1 (Regressão) | Modelo 2 (Classificação) |
|---|---|---|
| R² (Test) | 0.9011 | — |
| MAE (Test) | 0.0175 (1.7 pp) | — |
| RMSE (Test) | 0.0213 (2.1 pp) | — |
| Accuracy (Test) | — | 0.9943 |
| F1 Weighted (Test)| — | 0.9943 |

**Top Features (SHAP Importance):**
- **Modelo 1:** `sinistralidade_lag_1` (0.0528), `delta_sinistralidade_12m` (0.0263), `sinistralidade_lag_4` (0.0135)
- **Modelo 2:** `fator_etario_medio` (0.9525), `fator_geografico` (0.8402), `sinistralidade_operadora` (0.6407)

---

## 3. Roadmap Futuro — Sprints 9 a 11

**Escopo Técnico:**

| Componente | Detalhe |
|---|---|
| Algoritmo | XGBoost (Regressor + Classifier) |
| Dados de treino (Modelo 1) | 132 registros × 16 features (nível operadora, série temporal) |
| Dados de treino (Modelo 2) | 59.635 clusters × 12 features (nível produto, cross-section) |
| Validação | TimeSeriesSplit (Modelo 1), KFold estratificado (Modelo 2) |
| Explicabilidade | SHAP Values (feature importance + waterfall plots) |
| Output | Predição de sinistralidade + intervalo de confiança + alertas |

**Features do Modelo 1 (Operadora — Série Temporal):**

| # | Feature | Tipo | Fonte |
|---|---|---|---|
| 1 | `receita_trimestral` | Contínua | DIOPS |
| 2 | `despesa_trimestral` | Contínua | DIOPS |
| 3 | `sinistralidade_lag_1` | Contínua | Calculada |
| 4 | `sinistralidade_lag_2` | Contínua | Calculada |
| 5 | `sinistralidade_lag_4` | Contínua | Calculada (sazonalidade) |
| 6 | `cagr_receita_12m` | Contínua | Calculada |
| 7 | `delta_sinistralidade_12m` | Contínua | Calculada |
| 8 | `trimestre_ano` | Categórica | DIOPS (1T, 2T, 3T, 4T) |
| 9 | `porte_operadora` | Contínua | DIOPS (receita total) |
| 10 | `tipo_operadora` | Categórica | CADOP |
| 11 | `vidas_total` | Contínua | SIB |
| 12 | `fator_etario_medio` | Contínua | Score de Risco |
| 13 | `concentracao_geografica` | Contínua | SIB Granular |
| 14 | `vcmh_periodo` | Contínua | IESS |
| 15 | `receita_per_capita` | Contínua | DIOPS / SIB |
| 16 | `margem_vs_benchmark` | Contínua | Benchmark |

**Features do Modelo 2 (Produto — Cross-Section):**

| # | Feature | Tipo | Fonte |
|---|---|---|---|
| 1 | `vidas` | Contínua | SIB Granular |
| 2 | `fator_etario_medio` | Contínua | Score de Risco |
| 3 | `fator_geografico` | Contínua | VCMH/UF |
| 4 | `segmentacao` | Categórica | Cadastro Produtos |
| 5 | `tipo_contratacao` | Categórica | SIB Granular |
| 6 | `abrangencia` | Categórica | Cadastro Produtos |
| 7 | `moderador` | Categórica | Cadastro Produtos |
| 8 | `concentracao_municipal` | Contínua | SIB Granular |
| 9 | `proporcao_idosos` | Contínua | SIB Granular (59+/total) |
| 10 | `proporcao_individual` | Contínua | SIB Granular |
| 11 | `sinistralidade_operadora` | Contínua | DIOPS |
| 12 | `porte_operadora` | Contínua | DIOPS |

**Target:**
- Modelo 1: `sinistralidade_proximo_trimestre` (regressão, [0, 1.5])
- Modelo 2: `classificacao_risco` (4 classes: Baixo < 70%, Médio 70-80%, Alto 80-90%, Crítico > 90%)

**Hiperparâmetros Planejados:**

```python
xgb_params = {
    'max_depth': 4,
    'learning_rate': 0.05,
    'n_estimators': 200,
    'min_child_weight': 3,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'early_stopping_rounds': 20
}
```



---

### Sprint 9 — API REST

**Objetivo:** Expor o Motor de Sinistralidade como uma API programática para integração com outros sistemas (CRM, cotadores, plataformas de gestão).

**Escopo Técnico:**

| Componente | Tecnologia | Descrição |
|---|---|---|
| Framework | FastAPI | API REST assíncrona, documentação automática (Swagger) |
| Serialização | Pydantic v2 | Validação de entrada/saída com schemas tipados |
| Banco | DuckDB (read-only) | Consultas diretas ao banco analítico |
| Modelo ML | joblib | Carregamento do modelo XGBoost serializado |
| Autenticação | API Key (header) | Controle de acesso básico por chave |
| Deploy | Uvicorn | ASGI server para produção |
| Documentação | OpenAPI 3.0 (auto) | Swagger UI em `/docs` |

**Endpoints Planejados:**

```
GET  /v1/operadoras
     → Lista todas as operadoras na base com métricas resumidas

GET  /v1/operadoras/{registro_ans}
     → Detalhamento financeiro de uma operadora específica

GET  /v1/operadoras/{registro_ans}/sinistralidade
     → Série temporal de sinistralidade (2020-2025)

GET  /v1/operadoras/{registro_ans}/produtos
     → Lista de produtos com score de risco e sinistralidade estimada
     → Query params: ?segmentacao=&tipo_contratacao=&uf=&limit=&offset=

GET  /v1/produtos/{cd_plano}
     → Detalhamento de um produto específico (score, fatores, benchmark)

GET  /v1/produtos/{cd_plano}/municipios
     → Distribuição geográfica do produto (vidas por município)

GET  /v1/benchmark
     → Referências de mercado (IESS, ANS, UNIDAS)

POST /v1/predicao/operadora
     → Predição de sinistralidade futura (usa modelo XGBoost)
     → Body: { "registro_ans": "310239", "horizonte_trimestres": 2 }

POST /v1/predicao/produto
     → Classificação de risco de um produto
     → Body: { "cd_plano": "...", "vidas": 500, "faixa_etaria_media": "39-43", ... }

GET  /v1/health
     → Status da API e versão do modelo
```

**Schema de Resposta (exemplo):**

```json
{
  "operadora": {
    "registro_ans": "310239",
    "nome": "Pessoal Saúde",
    "modalidade": "Medicina de Grupo",
    "sinistralidade_atual": 0.658,
    "benchmark": 0.86,
    "classificacao": "Eficiente",
    "delta_benchmark": -0.202,
    "receita_4t2025": 116000000,
    "vidas": 11249,
    "produtos_ativos": 8
  },
  "metadata": {
    "fonte": "DIOPS 4T/2025 + SIB Mar/2026",
    "modelo_versao": "v1.0",
    "timestamp": "2026-05-20T12:00:00Z"
  }
}
```

**Estrutura de Arquivos:**

```
/api/
├── main.py              → App FastAPI + rotas
├── models.py            → Schemas Pydantic (request/response)
├── database.py          → Conexão DuckDB + queries
├── ml_service.py        → Carregamento e inferência do modelo XGBoost
├── auth.py              → Middleware de autenticação por API Key
├── config.py            → Configurações (paths, versões)
└── requirements.txt     → Dependências
```

**Entregáveis:**
1. API funcional com 9 endpoints
2. Documentação Swagger automática (`/docs`)
3. Script de teste (`test_api.py`) com exemplos de chamada
4. Docker-ready (Dockerfile + docker-compose.yml)
5. README com instruções de deploy

**Riscos e Mitigações:**

| Risco | Impacto | Mitigação |
|---|---|---|
| Performance com DuckDB em concorrência | Lentidão sob carga | Connection pooling + cache Redis (futuro) |
| Segurança da API Key simples | Acesso não autorizado | Rate limiting + upgrade para OAuth2 no Sprint 11 |
| Tamanho do banco (34MB) em memória | Consumo de RAM | DuckDB é eficiente; para escala, migrar para MotherDuck |

**Estimativa:** ~40 minutos de implementação autônoma.

---

### Sprint 10 — Pipeline de Atualização Automática

**Objetivo:** Criar um sistema que baixa novos dados da ANS automaticamente (mensal para SIB, trimestral para DIOPS) e recalcula todos os scores sem intervenção humana.

**Escopo Técnico:**

| Componente | Tecnologia | Descrição |
|---|---|---|
| Orquestrador | Python + cron / APScheduler | Agendamento de tarefas |
| Download | requests + retry | Download resiliente com fallback |
| Validação | Checksums + row counts | Garantia de integridade |
| Processamento | DuckDB + scripts existentes | Reuso dos scripts de sprint |
| Notificação | Webhook / Email | Alerta em caso de falha ou anomalia |
| Log | Structured logging (JSON) | Rastreabilidade completa |

**Fluxo do Pipeline:**

```
┌─────────────────────────────────────────────────────────────────┐
│  SCHEDULER (Cron)                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Mensal - Dia 15]                                              │
│  1. Verificar nova competência SIB no FTP da ANS                │
│  2. Se disponível → Download SIB Individualizado (28 UFs)       │
│  3. Filtrar operadoras-alvo                                     │
│  4. Atualizar tabela sib_granular (append ou replace)           │
│  5. Recalcular Score de Risco (Sprint 5)                        │
│  6. Recalcular Modelo XGBoost (retrain incremental)             │
│  7. Validar: |Δ sinistralidade| < 20pp (senão alerta)          │
│  8. Log + Notificação de sucesso                                │
│                                                                 │
│  [Trimestral - Dia 1 de Jan/Abr/Jul/Out]                       │
│  1. Verificar novo trimestre DIOPS no FTP                       │
│  2. Se disponível → Download DIOPS                              │
│  3. Processar e append à série temporal                         │
│  4. Recalcular sinistralidade por operadora                     │
│  5. Atualizar benchmark (se novo VCMH disponível)              │
│  6. Retreinar modelo XGBoost com novo dado                      │
│  7. Gerar relatório de variação trimestral                      │
│  8. Log + Notificação                                           │
│                                                                 │
│  [Diário - 06:00]                                               │
│  1. Health check do banco DuckDB                                │
│  2. Verificar integridade das tabelas                           │
│  3. Backup incremental do banco                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Validações Automáticas:**

| Validação | Critério | Ação se falhar |
|---|---|---|
| Row count | Novo SIB >= 90% do anterior | Alerta + não substituir |
| Sinistralidade | Delta < 20pp vs trimestre anterior | Alerta + flag de anomalia |
| Completude | Todas as 6 operadoras presentes | Alerta + processamento parcial |
| Formato | Schema compatível com esperado | Retry com parser alternativo |
| Freshness | Dados não mais antigos que 45 dias | Alerta de defasagem |

**Estrutura de Arquivos:**

```
/pipeline/
├── scheduler.py          → Orquestrador principal (APScheduler)
├── tasks/
│   ├── ingest_sib.py     → Download e processamento SIB mensal
│   ├── ingest_diops.py   → Download e processamento DIOPS trimestral
│   ├── recalculate.py    → Recálculo de scores e benchmark
│   ├── retrain_model.py  → Retreino do XGBoost
│   └── validate.py       → Validações de integridade
├── notifications/
│   ├── webhook.py        → Notificação via webhook
│   └── email.py          → Notificação via email
├── config.yaml           → Configuração (URLs, thresholds, schedule)
├── logs/                 → Logs estruturados (JSON)
└── backups/              → Backups incrementais do DuckDB
```

**Entregáveis:**
1. Pipeline funcional com scheduler configurável
2. Scripts de ingestão resilientes (retry, fallback, validação)
3. Sistema de alertas (webhook + log)
4. Documentação de operação (runbook)
5. Script de setup (`setup_pipeline.sh`)

**Riscos e Mitigações:**

| Risco | Impacto | Mitigação |
|---|---|---|
| ANS muda formato do CSV | Pipeline quebra | Parser adaptativo + alerta imediato |
| FTP da ANS fora do ar | Dados não atualizados | Retry com backoff exponencial (3 tentativas em 24h) |
| Dados corrompidos | Cálculos incorretos | Validação pré-ingestão + rollback automático |
| Drift do modelo ML | Predições degradam | Monitoramento de métricas + retrain automático |

**Estimativa:** ~45 minutos de implementação autônoma.

---

### Sprint 11 — Interface de Consulta (Frontend Dedicado)

**Objetivo:** Substituir o Streamlit por uma aplicação web profissional com autenticação, multi-tenant, e UX otimizada para uso comercial por clientes da Tallent Two.

**Escopo Técnico:**

| Componente | Tecnologia | Descrição |
|---|---|---|
| Frontend | React + TypeScript + TailwindCSS | SPA responsiva, design system T2 |
| Backend | FastAPI (Sprint 9) | API REST como backend |
| Autenticação | OAuth2 / JWT | Login seguro, multi-tenant |
| Banco | DuckDB (dev) → MotherDuck (prod) | Escala para múltiplos clientes |
| Deploy | Vercel (front) + Railway/Fly.io (back) | Deploy contínuo |
| Monitoramento | Sentry + Posthog | Erros + analytics de uso |

**Funcionalidades da Interface:**

```
┌─────────────────────────────────────────────────────────────────┐
│  MÓDULOS DA APLICAÇÃO                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DASHBOARD EXECUTIVO (Home)                                  │
│     • KPIs consolidados do grupo                                │
│     • Alertas de operadoras em risco                            │
│     • Gráfico de tendência (últimos 12 meses)                   │
│                                                                 │
│  2. EXPLORADOR DE OPERADORAS                                    │
│     • Busca por nome ou registro ANS                            │
│     • Ficha completa (financeiro + carteira + benchmark)        │
│     • Comparação lado-a-lado (até 3 operadoras)                 │
│                                                                 │
│  3. EXPLORADOR DE PRODUTOS                                      │
│     • Busca por código ou filtros combinados                    │
│     • Score de risco com explicação (SHAP)                      │
│     • Mapa geográfico de distribuição                           │
│     • Simulador what-if (alterar vidas/idade/região)            │
│                                                                 │
│  4. PREDIÇÃO E CENÁRIOS                                         │
│     • Projeção de sinistralidade (1-4 trimestres)               │
│     • Cenários otimista/realista/pessimista                     │
│     • Alertas preditivos ("operadora X vai ultrapassar 80%")    │
│                                                                 │
│  5. RELATÓRIOS                                                  │
│     • Geração de PDF executivo sob demanda                      │
│     • Exportação de dados (CSV, Excel, JSON)                    │
│     • Agendamento de relatórios periódicos                      │
│                                                                 │
│  6. ADMINISTRAÇÃO                                               │
│     • Gestão de usuários e permissões                           │
│     • Configuração de operadoras monitoradas                    │
│     • Logs de acesso e auditoria                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Design System (Frontend):**

| Elemento | Especificação |
|---|---|
| Tipografia | Inter (400, 500, 600, 700) |
| Cor primária | Teal/Petróleo (#1B4B5A) |
| Superfície | #FAFBFC (fundo), #FFFFFF (cards) |
| Bordas | #E2E8F0 (1px solid) |
| Espaçamento | 8px grid system |
| Componentes | Shadcn/UI (headless, customizável) |
| Gráficos | Recharts ou Tremor (React-native) |
| Tabelas | TanStack Table (sorting, filtering, pagination) |
| Mapas | Mapbox GL JS (heatmap geográfico) |

**Modelo de Acesso (Multi-Tenant):**

| Perfil | Acesso | Uso |
|---|---|---|
| Admin (Tallent Two) | Tudo | Gestão da plataforma |
| Consultor | Operadoras do cliente | Análise para advisory |
| Cliente (Operadora) | Apenas seus dados | Self-service |
| Viewer (Read-only) | Dashboard público | Demonstração |

**Estrutura de Arquivos:**

```
/frontend/
├── src/
│   ├── app/                → Rotas (Next.js App Router)
│   ├── components/         → Componentes reutilizáveis
│   │   ├── ui/             → Design system (shadcn)
│   │   ├── charts/         → Gráficos customizados
│   │   └── layouts/        → Layouts de página
│   ├── lib/                → Utilitários e API client
│   ├── hooks/              → Custom hooks
│   └── types/              → TypeScript interfaces
├── public/                 → Assets estáticos
├── tailwind.config.ts      → Configuração TailwindCSS
└── package.json

/backend/
├── (Sprint 9 - API REST)
├── auth/                   → OAuth2 + JWT
├── middleware/             → Rate limiting, CORS, logging
└── migrations/             → Schema de usuários e permissões
```

**Entregáveis:**
1. Aplicação web funcional com 6 módulos
2. Sistema de autenticação multi-tenant
3. Design system implementado (componentes reutilizáveis)
4. Deploy em ambiente de staging
5. Documentação de uso (user guide)
6. Testes E2E (Playwright)

**Riscos e Mitigações:**

| Risco | Impacto | Mitigação |
|---|---|---|
| Complexidade de frontend | Atraso na entrega | Usar shadcn/ui (componentes prontos) + Tremor (dashboards) |
| Performance com muitos dados | UX degradada | Paginação server-side + virtualização de tabelas |
| Segurança multi-tenant | Vazamento de dados | Row-level security + testes de penetração |
| Manutenção contínua | Custo operacional | CI/CD automatizado + monitoramento |

**Estimativa:** Este sprint é o mais complexo e provavelmente requer execução em múltiplas sessões ou equipe dedicada. Estimativa: 4-8 horas para MVP funcional, ou pode ser dividido em sub-sprints (11a: auth + layout, 11b: módulos, 11c: deploy).

---

## 4. Visão de Produto — Maturidade

```
FASE 1 (Concluída)          FASE 2 (Sprints 8-10)       FASE 3 (Sprint 11+)
━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━
MVP Analítico               Motor Inteligente           Produto Comercial
• Dados reais ANS           • Predição ML               • Interface dedicada
• 6 operadoras              • API programática          • Multi-tenant
• Dashboard Streamlit       • Atualização automática    • SaaS-ready
• Score de risco            • Alertas proativos         • Relatórios PDF
• Benchmark IESS            • Retreino contínuo         • Mapas geográficos
```

---

## 5. Dependências entre Sprints

```
Sprint 8 (XGBoost) ──────→ Sprint 9 (API) ──────→ Sprint 11 (Frontend)
                                    │
                                    ▼
                           Sprint 10 (Pipeline)
```

- **Sprint 8** é pré-requisito para Sprint 9 (a API expõe o modelo)
- **Sprint 9** é pré-requisito para Sprint 11 (o frontend consome a API)
- **Sprint 10** é independente e pode rodar em paralelo com Sprint 9 ou 11
- **Sprint 11** depende de Sprint 9 estar funcional

---

*Documento gerado automaticamente pelo Motor de Sinistralidade ANS — Tallent Two Financial Holding*
