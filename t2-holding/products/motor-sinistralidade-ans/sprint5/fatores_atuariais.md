# Fatores Atuariais — Sprint 5

## 1. Fator Etário (Curva em J) — RN 63/2003 ANS

A ANS define 10 faixas etárias. A regra dos 6× determina que a última faixa (59+) 
não pode custar mais que 6× a primeira (0-18).

Para o Motor de Sinistralidade, usamos fatores de custo relativo baseados em:
- Literatura atuarial brasileira (UNIDAS 2023, IESS Mapa Assistencial)
- Curva de utilização por faixa etária (frequência × custo médio)

| Faixa Etária | Fator de Custo Relativo | Justificativa |
|---|---|---|
| 0 a 18 anos | 1.00 | Base referencial |
| 19 a 23 anos | 0.80 | Menor utilização (jovens saudáveis) |
| 24 a 28 anos | 0.90 | Início de vida adulta |
| 29 a 33 anos | 1.00 | Referência (gestação compensa baixa utilização) |
| 34 a 38 anos | 1.10 | Início de aumento de utilização |
| 39 a 43 anos | 1.30 | Doenças crônicas começam |
| 44 a 48 anos | 1.60 | Aumento significativo |
| 49 a 53 anos | 2.00 | Transição para alto custo |
| 54 a 58 anos | 2.80 | Penúltima faixa, custo elevado |
| 59 anos ou mais | 4.50 | Faixa de maior custo (internações, crônicos) |

**Fonte:** Pesquisa Nacional UNIDAS 2023 (despesa assistencial per capita por faixa etária),
calibrada pela regra 6× da RN 63/2003.

## 2. Fator Geográfico (VCMH Regional)

O VCMH/IESS mede a variação de custos médico-hospitalares. Para o fator geográfico,
usamos a despesa per capita relativa por região/UF, baseada em:
- Panorama ANS (despesa per capita R$332/mês nacional em 2024)
- Diferenças regionais de custo de rede credenciada

| Região / UF | Fator Geográfico | Justificativa |
|---|---|---|
| SP (capital + ABCDMR) | 1.15 | Maior custo de rede, alta complexidade |
| SP (interior) | 1.00 | Referência nacional |
| RJ | 1.10 | Alto custo, rede complexa |
| MG | 0.95 | Custo moderado |
| Sul (PR, SC, RS) | 1.00 | Alinhado à média |
| Nordeste (CE, PE, BA) | 0.85 | Menor custo de rede |
| Norte (AM, PA) | 0.80 | Menor densidade, menor custo |
| Centro-Oeste (GO, DF) | 1.05 | DF puxa para cima |

Para o MVP, usamos uma proxy por UF baseada no custo médio de internação
do DATASUS/SIH (valor médio AIH por UF) normalizado.

## 3. Fator de Segmentação (já implementado no Sprint 2)

| Segmentação | Fator |
|---|---|
| Exclusivamente Odontológico | 0.40 |
| Ambulatorial | 0.70 |
| Hospitalar | 0.90 |
| Ambulatorial + Hospitalar | 1.10 |
| Referência | 1.15 |

## 4. Fator de Contratação (já implementado no Sprint 2)

| Contratação | Fator |
|---|---|
| Coletivo empresarial | 0.85 |
| Coletivo por adesão | 0.95 |
| Individual ou Familiar | 1.20 |

## 5. Fórmula do Score de Risco

Para cada cluster (produto × município × faixa etária):

```
Score_Cluster = Vidas × F_Etário × F_Geográfico × F_Segmentação × F_Contratação
```

Para cada produto:

```
Score_Produto = Σ Score_Cluster (para todos os clusters do produto)
```

Rateio:

```
Despesa_Produto = (Score_Produto / Σ Score_Todos_Produtos) × Despesa_Total_Operadora
```

Sinistralidade estimada:

```
Sinistralidade_Produto = Despesa_Produto / Receita_Estimada_Produto
```

Onde Receita_Estimada_Produto pode ser derivada da proporção de vidas × mensalidade média.
