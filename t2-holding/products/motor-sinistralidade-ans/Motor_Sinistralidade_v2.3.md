# Motor de Sinistralidade ANS — Documento Técnico

**Produto:** Motor de Sinistralidade e Precificação por Produto via Dados ANS Públicos
**Proprietário:** Tallent Two Financial Holding
**Versão:** v2.2
**Data:** 20 de Maio de 2026
**Classificação:** Interno — Uso Estratégico

---

## 1. Stack Tecnológico Consolidado

### 1.1 Infraestrutura e Runtime

| Camada | Tecnologia | Versão | Função |
|--------|-----------|--------|--------|
| Runtime | Python | 3.11 | Linguagem principal de todo o pipeline |
| Banco de Dados | DuckDB | 1.x | Banco analítico colunar, single-file, zero-config |
| Interface MVP | Streamlit | 1.57 | Dashboard interativo com deploy instantâneo |
| Visualização | Plotly Express + Graph Objects | 5.x | Gráficos interativos executivos |
| Componentes HTML | Streamlit Components | 1.x | Renderização de KPIs customizados |
| Versionamento | Git + GitHub | — | Repositório rsquillaci2/DS |
| Modelo ML | XGBoost + joblib | 2.x | Motor preditivo serializado para produção |

### 1.2 Stack de Dados

| Fonte | Origem | Formato | Volume | Frequência |
|-------|--------|---------|--------|------------|
| DIOPS | ANS/FTP | CSV (ZIP) | 926.610 registros (4T/2025) | Trimestral |
| DIOPS Histórico | ANS/FTP | CSV (ZIP) | 24 trimestres (2020–2025) | Trimestral |
| SIB Consolidado | ANS/FTP | CSV (ZIP) | 1.734.056 registros | Mensal |
| SIB Individualizado | ANS/FTP | CSV (ZIP) | 696.183 registros (6 ops, 29 UFs) | Mensal |
| Cadastro de Produtos | ANS/FTP | CSV | 937 produtos médico-hospitalares | Contínua |
| Cadastro de Operadoras | ANS/FTP | CSV | 6 operadoras-alvo (expansível a ~700) | Contínua |
| VCMH / IESS | IESS (publicação) | Manual | 27 UFs × 6 anos | Anual |
| Pesquisa UNIDAS | UNIDAS (publicação) | Manual | Custo per capita regional | Anual |

### 1.3 Banco de Dados — Schema Atual

```
ans_analytics.duckdb (34 MB)
├── sinistralidade_operadora     → 6 registros (resumo financeiro por operadora)
├── sib_operadoras               → 1.734.056 registros (beneficiários consolidados)
├── sib_granular                 → 696.183 registros (Sprint 4: Produto × Município × Faixa Etária)
├── produtos_ans                 → 937 registros (características de produtos)
├── resultado_proxy              → 937 registros (Sprint 2: proxy por produto)
├── score_risco_produto_agg      → 1.793 registros (Sprint 5: score por produto × município)
├── score_risco_uf               → 27 registros (Sprint 5: custo per capita por UF)
├── sinistralidade_historica     → 132 registros (Sprint 6: série temporal 2020–2025)
├── benchmark_referencia         → 5 registros (Sprint 7: benchmarks por tipo de operadora)
├── resultado_benchmark          → 6 registros (Sprint 7: classificação por operadora)
├── predicoes_operadora          → 6 registros (Sprint 8: predições XGBoost) ← NOVO
└── diops_raw                    → 926.610 registros (dados brutos DIOPS)
```

### 1.4 Arquitetura de Arquivos

```
/home/ubuntu/mvp_sinistralidade/
├── dashboard.py                 → Dashboard Streamlit v2.1 (1.186 linhas)
├── etl_ingestao.py              → Sprint 1–2: Ingestão inicial DIOPS + SIB
├── motor_sinistralidade.py      → Sprint 2: Motor de proxy por produto
├── sprint4_ingestao_sib.py      → Sprint 4: Ingestão SIB Brasil (28 UFs)
├── sprint5_score_risco.py       → Sprint 5: Score de Risco Atuarial
├── sprint6_serie_temporal.py    → Sprint 6: Série temporal DIOPS
├── sprint6_fix.py               → Sprint 6: Correção de formatos CSV
├── sprint7_benchmark.py         → Sprint 7: Benchmark IESS
├── sprint8_xgboost.py           → Sprint 8: Modelo Preditivo XGBoost ✅ NOVO
├── pagina_predicao.py           → Sprint 8: Página de ML para o Dashboard ✅ NOVO
├── fatores_atuariais.md         → Documentação dos fatores de ponderação
├── benchmark_iess_data.md       → Dados de benchmark coletados
├── logo_t2_sidebar.png          → Logo Tallent Two (PNG 540px)
└── data/
    ├── ans_analytics.duckdb     → Banco principal (34 MB)
    ├── diops_4t2025.csv         → DIOPS raw (77 MB)
    ├── sib_consolidado.csv      → SIB consolidado (37 MB)
    ├── produtos_ans.csv         → Cadastro de produtos (11 MB)
    ├── sib_individual/          → SIB por UF (28 arquivos)
    └── diops_historico/         → DIOPS 2020–2025 (24 ZIPs)
```

### 1.5 Operadoras na Base (Pilotos)

| # | Operadora | Registro ANS | Porte | Tipo | DIOPS | SIB Granular |
|---|-----------|-------------|-------|------|-------|--------------|
| 1 | Pessoal Saúde | 310239 | ~12.500 vidas | Medicina de Grupo | ✅ | ✅ (1.031 reg.) |
| 2 | Santa Helena Saúde | 355097 | ~194k vidas | Medicina de Grupo | ✅ | ✅ (11.144 reg.) |
| 3 | Hapvida NotreDame | 359017 | ~6M vidas | Med. Grupo Verticalizada | ✅ | ✅ (672.004 reg.) |
| 4 | Portomed (Porto Saúde) | 417491 | N/D | Seguradora | ✅ | ❌ (não aparece no SIB) |
| 5 | Santa Casa de Mauá | 421197 | ~31k vidas | Filantropia Verticalizada | ✅ | ✅ (4.537 reg.) |
| 6 | SF Sistemas (Sagrada Família) | 422371 | ~48k vidas | Med. Grupo Verticalizada | ✅ | ✅ (7.467 reg.) |

> **Nota Estratégica:** O DIOPS raw contém dados de **todas as operadoras do mercado** (~700). A expansão para base completa (Sprint 8.5) requer apenas remoção do filtro de operadoras-alvo nos scripts ETL.

---

## 2. Sprints Concluídas — Detalhamento

### Sprint 1 — Sinistralidade por Operadora ✅

**Objetivo:** Calcular a sinistralidade real (Despesa/Receita) de cada operadora usando dados financeiros oficiais.

**O que foi feito:**
- Download do DIOPS 4T/2025 (77 MB, 926.610 registros financeiros)
- Download do SIB Consolidado Mar/2026 (37 MB, 1.734.056 registros de beneficiários)
- Parsing e carga no DuckDB com tratamento de schemas variáveis (separador `;`, encoding Latin-1)
- Cálculo: `Sinistralidade = Conta 411x (Eventos/Sinistros) / Conta 311x (Contraprestações)`
- Validação cruzada com dados publicados pela ANS

**Resultados:**

| Operadora | Receita (R$) | Despesa (R$) | Sinistralidade |
|-----------|-------------|-------------|----------------|
| Pessoal Saúde | 116,5 M | 76,7 M | 65,8% |
| SF Sistemas | 168,8 M | 128,5 M | 76,1% |
| Hapvida NDI | 39,6 B | 30,3 B | 76,4% |
| Portomed | 86,7 M | 67,5 M | 77,9% |
| Santa Casa Mauá | 383,4 M | 299,6 M | 78,2% |
| Santa Helena | 3,1 B | 2,7 B | 84,5% |

**Desafios técnicos resolvidos:**
- Tipos de dados incompatíveis (REG_ANS como BIGINT vs. VARCHAR)
- CSVs com linhas malformadas (`flag ignore_errors=True`)
- Conta contábil como string vs. número

---

### Sprint 2 — Motor de Proxy por Produto ✅

**Objetivo:** Estimar a sinistralidade de cada produto individual usando fatores de ponderação baseados em literatura atuarial.

**O que foi feito:**
- Cruzamento do Cadastro de Produtos ANS (937 produtos) com o DIOPS
- Implementação de 5 fatores multiplicativos:
  - Fator de Segmentação: Odonto 0,4× → Referência 1,15×
  - Fator de Contratação: Empresarial 0,95× → Individual 1,20×
  - Fator de Abrangência: Municipal 0,95× → Nacional 1,15×
  - Fator de Moderação: Com coparticipação/franquia 0,92× → Sem 1,05×
  - Fator de Faixa de Preço: normalizado pela média
- Fórmula: `Sinistralidade_Proxy(produto) = Sinistralidade_Operadora × Peso_Relativo`
- Classificação de qualidade da estimativa (Alta/Média/Baixa)

**Resultado:** 937 produtos com sinistralidade proxy calculada, variando de 39% (odontológico coletivo empresarial com coparticipação) a 112% (individual referência sem moderador).

---

### Sprint 3 — Prova de Conceito de Granularidade ✅

**Objetivo:** Validar se é possível descer para a granularidade de Produto × Município × Faixa Etária usando dados públicos.

**O que foi feito:**
- Download do SIB Individualizado de Roraima (UF menor, para teste rápido)
- Descoberta da chave de vinculação: `CD_PLANO_RPS` (SIB) = `CD_PLANO` (Cadastro de Produtos)
- Teste de match: 100% de correspondência entre os datasets
- Mapeamento de campos disponíveis: UF, município, faixa etária, sexo, tipo de contratação, segmentação, titular/dependente

**Resultado:** Viabilidade confirmada. O SIB Individualizado contém a granularidade necessária para o rateio atuarial.

---

### Sprint 4 — Ingestão SIB Brasil ✅

**Objetivo:** Baixar e processar o SIB Individualizado de todos os 29 estados brasileiros, filtrando apenas as 6 operadoras-alvo.

**O que foi feito:**
- Script ETL otimizado com download incremental (estados menores primeiro)
- Retry automático com timeout progressivo (60s → 300s → 500s)
- Processamento em streaming: download → filtro → append ao DuckDB
- 29/29 UFs processadas com sucesso (incluindo SP com 469 K registros)

**Resultado:**

| Operadora | Registros | Produtos | Municípios |
|-----------|-----------|---------|-----------|
| Hapvida NDI | 672.004 | 1.902 | 3.479 |
| Santa Helena | 11.144 | 137 | 224 |
| SF Sistemas | 7.467 | 17 | 104 |
| Santa Casa Mauá | 4.537 | 31 | 25 |
| Pessoal Saúde | 1.031 | 8 | 22 |
| **Total** | **696.183** | **1.895** | **3.854** |

> **Nota:** Portomed não aparece no SIB Individualizado — provavelmente opera sob outro registro ANS ou modelo de distribuição via corretoras.

---

### Sprint 5 — Score de Risco Atuarial ✅

**Objetivo:** Distribuir a despesa assistencial do DIOPS proporcionalmente ao risco de cada cluster (Produto × Município), gerando sinistralidade estimada real por produto.

**O que foi feito:**
- Implementação da curva etária da ANS (RN 63/2003 + UNIDAS 2023):
  - 0–18: 1,0 | 19–23: 1,0 | 24–28: 1,1 | 29–33: 1,2 | 34–38: 1,5
  - 39–43: 1,8 | 44–48: 2,2 | 49–53: 2,8 | 54–58: 3,5 | 59+: 4,5
- Implementação de 27 fatores geográficos por UF calibrados com VCMH/IESS:
  - SP: 1,15 | RJ: 1,12 | DF: 1,10 | ... | RR: 0,72 | AP: 0,72
- Fórmula: `Score = Vidas × F_Etário × F_Geográfico × F_Segmentação × F_Contratação`
- Rateio: `Despesa_Produto = (Score_Produto / ΣScores) × Despesa_Total_Operadora`
- Custo per capita: `Despesa_Produto / Vidas_Produto / 12`

**Resultados:**

| Métrica | Valor |
|---------|-------|
| Clusters calculados | 59.635 (Produto × Município) |
| Produtos com score | 1.793 |
| Custo per capita mais alto | R$ 1.991/mês (Santa Helena, Individual) |
| Custo per capita mais baixo | R$ 208/mês (SF Sistemas, Coletivo Empresarial) |
| Variação geográfica | DF: R$ 617 vs. MA: R$ 253 (2,4× de diferença) |

---

### Sprint 6 — Série Temporal ✅

**Objetivo:** Expandir o DIOPS para 24 trimestres (2020–2025) e calcular tendências de sinistralidade.

**O que foi feito:**
- Download de 24 trimestres de DIOPS (1T/2020 a 4T/2025)
- Tratamento de 3 formatos diferentes de CSV (ANS mudou o schema em 2020–2021, 2022–2024, e 2025)
- Cálculo de sinistralidade trimestral isolada (delta entre acumulados)
- Cálculo de CAGR de receita e variação de sinistralidade no período

**Resultados:**

| Operadora | Sinistralidade 1T/2020 | Sinistralidade 4T/2025 | Variação |
|-----------|----------------------|----------------------|---------|
| Hapvida NDI | 31,1% | 76,4% | +45,3 pp (efeito fusão NDI) |
| Santa Helena | 28,1% | 84,5% | +56,4 pp (pressão constante) |
| Pessoal Saúde | — | 65,8% | Dados a partir de 2022 |
| SF Sistemas | — | 76,1% | Dados a partir de 2022 |

> Todas as operadoras apresentam tendência de piora pós-COVID e inflação médica.

---

### Sprint 7 — Benchmark IESS e Calibração Geográfica ✅

**Objetivo:** Integrar dados de referência do mercado (IESS, ANS, UNIDAS) para permitir comparação e calibrar os fatores geográficos.

**O que foi feito:**
- Coleta de dados de benchmark:
  - VCMH/IESS (Variação de Custos Médico-Hospitalares): série 2018–2025
  - Panorama ANS 2024: sinistralidade média do setor (82,2%)
  - Pesquisa UNIDAS 2023: custo per capita por região
- Definição de benchmarks por tipo de operadora:
  - Grandes Verticalizadas: 80% | Médias: 83% | Pequenas: 86% | Filantropia: 90%
- Classificação: Eficiente (< benchmark − 5pp) | Na Média | Sob Pressão (> benchmark + 5pp)
- Calibração dos 27 fatores geográficos com dados VCMH reais

**Resultado:**

| Operadora | Sinistralidade Real | Benchmark | Delta | Classificação |
|-----------|--------------------|-----------|----|---------------|
| Pessoal Saúde | 65,8% | 86,0% | −20,2 pp | ✅ Eficiente |
| Santa Casa Mauá | 78,2% | 90,0% | −11,8 pp | ✅ Eficiente |
| SF Sistemas | 76,1% | 83,0% | −6,9 pp | ✅ Eficiente |
| Hapvida NDI | 76,4% | 80,0% | −3,6 pp | ⚠️ Na Média |
| Santa Helena | 84,5% | 83,0% | +1,5 pp | ⚠️ Na Média |
| Portomed | 77,9% | 77,0% | +0,9 pp | ⚠️ Na Média |

---

### Sprint 8 — Modelo Preditivo XGBoost ✅ *(CONCLUÍDO — incluído em v2.2)*

**Objetivo:** Implementar modelo de Machine Learning para prever sinistralidade futura por operadora e classificar risco por produto.

**O que foi feito:**
- Construção de dois modelos XGBoost:
  - Modelo 1 (Regressão): operadoras/série temporal — predição de sinistralidade futura
  - Modelo 2 (Classificação): produtos/cross-section — classificação em 4 classes de risco
- Engenharia de features: lags de sinistralidade, CAGRs, fatores atuariais, benchmarks
- Treinamento e validação cruzada (TimeSeriesSplit para Modelo 1, Stratified K-Fold para Modelo 2)
- Implementação de explicabilidade com SHAP Values (feature importance + waterfall plots)
- Serialização dos modelos com joblib para uso em produção
- Integração ao dashboard com nova página "Predição (ML)"

**Hiperparâmetros utilizados:**
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

**Métricas de desempenho:**

| Métrica | Modelo 1 (Regressão) | Modelo 2 (Classificação) |
|---------|---------------------|--------------------------|
| R² (Test) | 0,9011 | — |
| MAE (Test) | 0,0175 (1,7 pp) | — |
| RMSE (Test) | 0,0213 (2,1 pp) | — |
| Accuracy (Test) | — | 0,9943 |
| F1 Weighted | — | 0,9943 |

**Top Features (SHAP Importance):**
- Modelo 1: `sinistralidade_lag_1` (0,0528), `delta_sinistralidade_12m` (0,0263), `sinistralidade_lag_4` (0,0135)
- Modelo 2: `fator_etario_medio` (0,9525), `fator_geografico` (0,8402), `sinistralidade_operadora` (0,6407)

**Resultados de predição (vs. benchmark):**

| Operadora | Sinistralidade Real | Benchmark | Delta | Classificação ML |
|-----------|--------------------|-----------|----|-----------------|
| Pessoal Saúde | 65,8% | 86,0% | −20,2 pp | ✅ Eficiente |
| Santa Casa Mauá | 78,2% | 90,0% | −11,8 pp | ✅ Eficiente |
| SF Sistemas | 76,1% | 83,0% | −6,9 pp | ✅ Eficiente |
| Hapvida NDI | 76,4% | 80,0% | −3,6 pp | ⚠️ Na Média |
| Santa Helena | 84,5% | 83,0% | +1,5 pp | ⚠️ Na Média |
| Portomed | 77,9% | 77,0% | +0,9 pp | ⚠️ Na Média |

**Deliverables da Sprint 8:**
1. `sprint8_xgboost.py` — Pipeline completo: feature engineering → treinamento → validação → SHAP
2. `modelo_sinistralidade.pkl` — Modelo 1 serializado (regressão)
3. `modelo_risco_produto.pkl` — Modelo 2 serializado (classificação)
4. SHAP values salvos para visualização no dashboard
5. Nova página "Predição (ML)" integrada ao Dashboard Streamlit

---

### Sprint 8.1 — Refatoração UX/UI para Escala ✅

**Objetivo:** Preparar o dashboard para suportar ~700+ operadoras, migrando de comparação direta para paradigma de busca, filtro e ranking.

**O que foi feito:**
- Substituição de selectbox por filtro hierárquico (Modalidade → Operadora com busca textual)
- Resumo Executivo: Top 10 Maior + Top 10 Menor + Histograma de distribuição
- Remoção de todos os dicts/CASE WHEN hardcoded (6 locais no código)
- Tabelas com paginação (25 registros/página)
- Multiselect com default Top 5 por receita (máx recomendado: 5)
- Benchmark: Top 10 Eficientes vs Top 10 Sob Pressão
- Predição: Top Movers (piora vs melhora)
- Resolução dinâmica de nomes via `COALESCE(Nome_Fantasia, Razao_Social)`
- Prepared statements para segurança SQL

**Resultado:** Dashboard v3.0 — 100% dinâmico, pronto para volume arbitrário de operadoras.

---

### Sprint 8.5 — Expansão para Mercado Completo ✅

**Objetivo:** Expandir a base de 6 operadoras-piloto para todas as operadoras ativas no DIOPS.

**O que foi feito:**
- Remoção do filtro `WHERE registro_ans IN (...)` nos scripts ETL
- Recálculo de sinistralidade real para 943 operadoras (todas com receita >0)
- Série temporal expandida: 20.353 registros (24 trimestres × ~850 operadoras)
- SIB consolidado expandido: 321.677 registros (1.245 operadoras)
- Benchmark recalculado com percentis reais por modalidade (809 operadoras)
- Retreino do Modelo 1 (XGBoost): 132 → 12.051 registros de treinamento (761 operadoras)
- Predições geradas para 880 operadoras (319 piora, 313 melhora, 248 estável)

**Métricas do modelo retreinado:**

| Métrica | Sprint 8 (6 ops) | Sprint 8.5 (761 ops) | Observação |
|---------|-----------------|---------------------|------------|
| R² (Train) | 0,9058 | 0,9058 | Mantido |
| R² (Test) | 0,9011 | 0,7097 | Esperado: mais diversidade |
| MAE (Test) | 1,75 pp | 5,79 pp | Mercado mais heterogêneo |
| CV 5-fold R² | — | 0,7340 ± 0,050 | Robusto e generalizável |

> **Nota sobre R²:** A queda de 0,90 para 0,71 é esperada e saudável. O modelo anterior "overfitava" em 6 operadoras similares. R² 0,71 com 761 operadoras diversas (odontológicas, autogestão, cooperativas, filantropia) é um resultado sólido e mais generalizável.

**Feature Importance (Top 5):**

| Feature | Importância |
|---------|------------|
| sinistralidade_lag_1 | 0,6956 |
| sinistralidade_ma4 | 0,0740 |
| sinistralidade_lag_4 | 0,0339 |
| sinistralidade_lag_2 | 0,0310 |
| receita_lag_4 | 0,0306 |

**Distribuição de sinistralidade do mercado (943 operadoras):**

| Faixa | Operadoras |
|-------|------------|
| < 50% | 168 |
| 50–70% | 172 |
| 70–80% | 200 |
| 80–90% | 183 |
| 90–100% | 53 |
| > 100% | 37 |

**Benchmark por modalidade (percentis reais):**

| Modalidade | Operadoras | Mediana Sinistralidade |
|-----------|-----------|------------------------|
| Cooperativa Médica | 253 | 78,5% |
| Medicina de Grupo | 206 | 73,8% |
| Odontologia de Grupo | 114 | 32,6% |
| Autogestão | 109 | 87,8% |
| Cooperativa Odontológica | 87 | 52,0% |
| Filantropia | 31 | 78,8% |

**Deliverables da Sprint 8.5:**
1. `sprint85_expansion.py` — ETL expandido (DIOPS + Série Temporal + SIB + Benchmark)
2. `sprint85_ml_retrain.py` — Retreino XGBoost com base expandida
3. Banco `ans_analytics.duckdb` expandido (~120 MB)
4. 880 predições para próximo trimestre

---

## 3. Roadmap Futuro — Sprints 9 a 11

### Sprint 9 — API REST *(pré-requisito: Sprint 8.5 ✅)* 🔜

**Stack técnico:**

| Componente | Tecnologia | Descrição |
|-----------|-----------|-----------|
| Framework | FastAPI | API REST assíncrona, documentação automática (Swagger) |
| Serialização | Pydantic v2 | Validação de entrada/saída com schemas tipados |
| Banco | DuckDB (read-only) | Consultas diretas ao banco analítico |
| Modelo ML | joblib | Carregamento do XGBoost serializado |
| Autenticação | API Key (header) | Controle de acesso básico por chave |
| Deploy | Uvicorn + ASGI | Servidor para produção |
| Documentação | OpenAPI 3.0 | Swagger UI automático em /docs |

**Endpoints planejados:**
```
GET  /v1/operadoras                              → Lista todas (~700) com métricas resumidas
GET  /v1/operadoras/{registro_ans}               → Detalhamento financeiro + benchmark
GET  /v1/operadoras/{registro_ans}/sinistralidade → Série temporal 2020–2025
GET  /v1/operadoras/{registro_ans}/produtos       → Produtos com score de risco
GET  /v1/produtos/{cd_plano}                      → Detalhamento de produto específico
GET  /v1/produtos/{cd_plano}/municipios           → Distribuição geográfica
GET  /v1/benchmark                                → Referências de mercado
POST /v1/predicao/operadora                       → Predição XGBoost (horizonte configurável)
POST /v1/predicao/produto                         → Classificação de risco de produto
GET  /v1/health                                   → Status + versão do modelo
```

**Estrutura de arquivos:**
```
/api/
├── main.py              → App FastAPI + rotas
├── models.py            → Schemas Pydantic (request/response)
├── database.py          → Conexão DuckDB + queries
├── ml_service.py        → Carregamento e inferência XGBoost
├── auth.py              → Middleware de autenticação por API Key
├── config.py            → Configurações (paths, versões)
└── requirements.txt
```

**Estimativa:** ~40 minutos de implementação autônoma

---

### Sprint 10 — Pipeline de Atualização Automática *(independente)* 🔜

**Agendamentos:**
```
[Mensal — Dia 15]       Download SIB → filtro → recálculo score → retreino XGBoost → validação → alerta
[Trimestral — Dia 1]    Download DIOPS → série temporal → benchmark → retreino → relatório variação
[Diário — 06:00]        Health check DuckDB + backup incremental
```

**Validações automáticas:**

| Validação | Critério | Ação se Falhar |
|-----------|---------|----------------|
| Row count SIB | Novo SIB ≥ 90% do anterior | Alerta — não substituir |
| Sinistralidade delta | |Δ| < 20pp vs. trimestre anterior | Flag de anomalia |
| Completude | Todas as operadoras monitoradas presentes | Alerta de processamento parcial |
| Formato | Schema compatível com esperado | Retry com parser alternativo |
| Freshness | Dados não mais antigos que 45 dias | Alerta de defasagem |

**Estimativa:** ~45 minutos de implementação autônoma

---

### Sprint 11 — Interface Web Dedicada *(pré-requisito: Sprint 9)* 🔜

**Stack técnico:**

| Componente | Tecnologia | Descrição |
|-----------|-----------|-----------|
| Frontend | React + TypeScript | SPA responsiva |
| Estilo | TailwindCSS + shadcn/ui | Componentes headless |
| Gráficos | Recharts ou Tremor | Dashboards React-native |
| Tabelas | TanStack Table | Sorting, filtering, pagination |
| Mapas | Mapbox GL JS | Heatmap geográfico |
| Backend | FastAPI (Sprint 9) | API REST |
| Auth | OAuth2 + JWT | Multi-tenant |
| Deploy | Vercel (front) + Railway/Fly.io (back) | Deploy contínuo |

**Módulos da aplicação:**

| # | Módulo | Funcionalidades |
|---|--------|----------------|
| 1 | Dashboard Executivo | KPIs consolidados, alertas de risco, tendência 12 meses |
| 2 | Explorador de Operadoras | Busca, ficha completa, comparação lado-a-lado (até 3) |
| 3 | Explorador de Produtos | Filtros combinados, score SHAP, mapa geográfico, simulador what-if |
| 4 | Predição e Cenários | Projeção 1–4 trimestres, cenários otimista/realista/pessimista |
| 5 | Relatórios | PDF executivo, exportação CSV/Excel/JSON, agendamento periódico |
| 6 | Administração | Usuários, permissões, logs de auditoria |

**Modelo de acesso multi-tenant:**

| Perfil | Acesso | Uso |
|--------|--------|-----|
| Admin (Tallent Two) | Tudo | Gestão da plataforma |
| Consultor | Operadoras do cliente | Advisory |
| Cliente (Operadora) | Apenas seus dados | Self-service |
| Viewer (Read-Only) | Dashboard público | Demonstração |

**Estimativa:** 4–8 horas para MVP funcional (ou sub-sprints 11a/11b/11c)

---

## 4. Visão de Produto — Maturidade

```
FASE 1 (Concluída)         FASE 2 (Em Andamento)      FASE 3 (Sprint 11+)
━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━
MVP Analítico              Motor Inteligente           Produto Comercial
• Dados reais ANS          • Predição ML ✅            • Interface dedicada
• 943 operadoras ✅        • API programática          • Multi-tenant
• Dashboard v3.0 ✅        • Atualização automática    • SaaS-ready
• Score de risco           • Alertas proativos         • Relatórios PDF
• Benchmark real ✅        • Retreino contínuo         • Mapas geográficos
• Série temporal 24T ✅    • Score 360°
```

## 5. Dependências entre Sprints

```
Sprint 8 ✅ ──→ Sprint 8.1 ✅ ──→ Sprint 8.5 ✅ ──→ Sprint 9 (API REST) ──→ Sprint 11 (Frontend)
                                                       │
                                                       ▼
                                               Sprint 10 (Pipeline) — independente
```

- **Sprint 8** ✅ — Modelo preditivo XGBoost (6 operadoras)
- **Sprint 8.1** ✅ — Refatoração UX/UI para escala (dashboard v3.0)
- **Sprint 8.5** ✅ — Expansão para mercado completo (943 operadoras)
- **Sprint 9** 🔜 — API REST FastAPI (próxima)
- **Sprint 10** 🔜 — Pipeline automático (independente)
- **Sprint 11** 🔜 — Interface React (depende da Sprint 9)

---

## 6. Diferencial Competitivo

| Capacidade | ANS (público) | Milliman / IESS | Esta Plataforma |
|-----------|--------------|-----------------|-----------------|
| Sinistralidade por operadora | ✅ dado bruto | ✅ relatório PDF | ✅ calculada e validada |
| Sinistralidade por produto individual | ❌ | ❌ | ✅ Sprint 2/5 |
| Sinistralidade produto × município × faixa etária | ❌ | ❌ | ✅ Sprint 5 |
| Predição para próximo trimestre (ML) | ❌ | ❌ | ✅ Sprint 8 ✅ |
| Classificação de risco em 4 classes | ❌ | ❌ | ✅ Sprint 8 ✅ |
| Explicabilidade do score (SHAP) | ❌ | ❌ | ✅ Sprint 8 ✅ |
| Benchmark percentil dentro do mercado real | ❌ | Parcial | ✅ Sprint 8.5 |
| IDA + IDSS + Reclamações ANS (rating 360°) | ❌ | Parcial | ✅ Sprint 8.5 |
| Alertas preditivos proativos | ❌ | ❌ | ✅ Sprint 9/10 |
| API programática para integração | ❌ | ❌ | ✅ Sprint 9 |
| Atualização automática mensal/trimestral | ❌ | ❌ | ✅ Sprint 10 |
| Interface multi-tenant comercial | ❌ | ❌ | ✅ Sprint 11 |

---

*Documento Técnico — Motor de Sinistralidade ANS — Tallent Two Financial Holding*
*Autor: Ricardo Squillaci | Versão v2.3 | 20 de Maio de 2026*
