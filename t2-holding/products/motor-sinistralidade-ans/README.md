<div align="center">
  <img src="/home/ubuntu/mvp_sinistralidade/logo_t2.png" alt="Tallent Two Logo" width="300">
  
  # Motor de Sinistralidade ANS
  ### Relatório Técnico: Granularidade e Roadmap de Implementação (Rota 1)
  
  **Autor:** Ricardo Squillaci | **Data:** Maio de 2026 | **Classificação:** Confidencial
</div>

---

## 1. Sumário Executivo

A sinistralidade é o indicador mais crítico da saúde suplementar brasileira. No entanto, a visão atual oferecida pelos dados abertos da ANS (via DIOPS) restringe-se ao desempenho consolidado da operadora. Esta agregação gera o **Viés de Mix de Carteira**, mascarando produtos deficitários que são subsidiados por produtos rentáveis, e ocultando riscos de concentração geográfica.

Para resolver este desafio, a **Tallent Two Financial Holding** desenvolveu a prova de conceito do Motor de Sinistralidade ANS. A principal descoberta técnica deste projeto foi a validação do *match perfeito* entre a chave `CD_PLANO_RPS` do SIB Individualizado (Sistema de Informações de Beneficiários) e a chave `CD_PLANO` do Cadastro de Produtos da ANS. 

Esta descoberta viabiliza a **Rota 1 (Alocação Atuarial Aprimorada)**: uma metodologia que permite calcular a sinistralidade granular (Produto × Município) distribuindo a despesa total da operadora de forma proporcional ao risco atuarial de cada cluster, sem a necessidade de infraestrutura massiva para processamento de eventos individuais (TISS).

Este relatório detalha a arquitetura técnica da Rota 1 e estabelece o roadmap completo para sua implementação.

---

## 2. O Desafio da Granularidade

A análise tradicional de operadoras de saúde esbarra em uma limitação estrutural dos dados públicos:

1. **Demonstrações Contábeis (DIOPS):** Fornecem receita e despesa assistencial exatas, mas apenas em nível consolidado (CNPJ/Registro ANS).
2. **Sistema de Informações de Produtos (SIP):** Fornece frequência de utilização (consultas, exames, internações), mas não traz o custo associado a cada evento.
3. **Padrão TISS:** Contém o detalhamento de cada procedimento, mas é uma base massiva (bilhões de linhas) e altamente complexa para ingestão e processamento contínuo.

O risco dessa limitação é a precificação "cega" em operações de M&A, estruturação de novos produtos ou consultoria estratégica, onde a performance de um produto específico (ex: um plano básico no ABC Paulista) é avaliada usando a média da operadora inteira.

---

## 3. A Solução: Rota 1 (Alocação Atuarial Aprimorada)

A Rota 1 contorna a necessidade de processar bilhões de guias médicas do TISS, utilizando modelagem estatística sobre as bases de vidas e finanças. O processo ocorre em três etapas fundamentais:

### Passo 1: Mapeamento de Exposição (SIB + Cadastro)
Através do SIB Individualizado, extraímos a distribuição exata de vidas ativas no mês de competência. O cruzamento com o Cadastro de Produtos permite criar clusters granulares.
* **Granularidade:** Operadora → Produto → Município.
* **Dado chave:** Idade média da carteira naquele cluster específico.

### Passo 2: Score de Risco Atuarial
Com os clusters formados, aplicamos fatores de ponderação baseados em literatura atuarial para calcular o "peso" ou "risco" de cada grupo.
* **Fator Etário:** Baseado na idade média do cluster (curva de custo em J).
* **Fator de Segmentação:** Hospitalar vs. Ambulatorial.
* **Fator Geográfico:** Ajuste de custo médico-hospitalar (VCMH) por região.
* **Resultado:** Um *Score de Risco* normalizado para cada linha (Produto × Município).

### Passo 3: Rateio Financeiro (DIOPS)
A despesa assistencial total da operadora, reportada no DIOPS do trimestre correspondente, é distribuída entre os clusters de forma estritamente proporcional ao Score de Risco calculado no Passo 2.
* **Resultado:** Custo estimado por vida em cada município, para cada produto.
* **Métrica Final:** Sinistralidade Granular Estimada (Despesa Rateada / Receita Estimada).

---

## 4. Roadmap de Implementação (Sprints)

Para materializar a Rota 1 e evoluir o Motor de Sinistralidade para um produto de dados robusto, o seguinte roadmap ágil foi estruturado:

### Fase 1: Fundação (Concluída) ✅
| Sprint | Objetivo | Entregáveis |
|--------|----------|-------------|
| **Sprint 1** | MVP Base | Ingestão DIOPS + SIB Consolidado. Cálculo de sinistralidade agregada. Dashboard inicial. |
| **Sprint 2** | Motor de Proxy | Algoritmo de rateio simples baseado apenas nas características do produto. |
| **Sprint 3** | PoC Granularidade | Prova de conceito cruzando amostra do SIB (Roraima) com Cadastro de Produtos. |

### Fase 2: Implementação da Rota 1 (Curto Prazo) ⏳
| Sprint | Objetivo | Descrição Técnica |
|--------|----------|-------------------|
| **Sprint 4** | Ingestão SIB Brasil | Script ETL otimizado em DuckDB para baixar, descompactar e consolidar o SIB de todos os 27 estados brasileiros, filtrando apenas as operadoras-alvo. |
| **Sprint 5** | Motor de Score Atuarial | Implementação das tabelas de fatores de risco (etário, geográfico, segmentação) e cálculo do Score de Risco para cada cluster (Produto × Município). |
| **Sprint 6** | Rateio Financeiro | Cruzamento do Score de Risco com a despesa do DIOPS, gerando a tabela final de Sinistralidade Granular. Atualização do Dashboard com a nova visão. |

### Fase 3: Evolução e Inteligência (Médio Prazo) 🚀
| Sprint | Objetivo | Descrição Técnica |
|--------|----------|-------------------|
| **Sprint 7** | Série Temporal | Expansão da ingestão para os últimos 20 trimestres (5 anos) do DIOPS e SIB, permitindo análise de tendência (CAGR de despesa e receita). |
| **Sprint 8** | Integração IESS | Incorporação do Mapa Assistencial do IESS como benchmark externo para calibrar os fatores geográficos de custo. |

### Fase 4: Machine Learning (Longo Prazo) 🔮
| Sprint | Objetivo | Descrição Técnica |
|--------|----------|-------------------|
| **Sprint 9** | Modelo Preditivo | Treinamento de modelo XGBoost utilizando a série temporal para prever a sinistralidade futura de um produto com base em suas características e localização. |
| **Sprint 10** | API REST | Disponibilização do Motor como serviço (API) para integração direta com sistemas de precificação e subscrição de clientes da Tallent Two. |

---

## 5. Requisitos de Infraestrutura

A arquitetura atual, baseada em **Python + DuckDB + Streamlit**, provou-se extremamente eficiente para o processamento em memória de arquivos pesados (como o SIB). 

Para a execução da **Fase 2 (Ingestão SIB Brasil)**, que envolve processar aproximadamente 50 milhões de registros mensais, recomenda-se:
* Instância Cloud com mínimo de 16GB RAM (ideal 32GB para processamento in-memory folgado).
* Armazenamento SSD de 100GB (arquivos `.dbc` temporários e banco `.duckdb` consolidado).
* O DuckDB manterá sua performance analítica sub-segundo no Dashboard mesmo com a base completa.

---

<div align="center">
  <p><i>Tallent Two Financial Holding — Governança, Inovação, Responsabilidade, Eficiência.</i></p>
</div>
