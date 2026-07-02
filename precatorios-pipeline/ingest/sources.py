"""URLs e configuração das fontes de dados."""

# === SOF/MPO — Dados Abertos de Sentenças Judiciais ===
# Perspectiva Orçamentária (série consolidada 2008-2025)
SOF_ORCAMENTARIA_URL = (
    "https://www1.siop.planejamento.gov.br/siopdoc/lib/exe/fetch.php/"
    "dados_abertos:sentencas:serie_execucao_orcamentaria_2008-2025.csv"
)

# Perspectiva da Expedição — arquivos anuais (2008–2026)
SOF_EXPEDICAO_BASE_URL = (
    "https://www1.siop.planejamento.gov.br/siopdoc/lib/exe/fetch.php/"
    "dados_abertos:sentencas:expedidos_{year}.csv"
)
SOF_EXPEDICAO_YEARS = list(range(2022, 2027))  # Sprint scope: 2022-2026 (doc pede 2022-2026)

# Índice de correção IPCA (usado na atualização de valores)
SOF_IPCA_URL = (
    "https://www1.siop.planejamento.gov.br/siopdoc/lib/exe/fetch.php/"
    "dados_abertos:sentencas:indice_correcao_ipca.csv"
)

# === CVM — Informes de FIDC ===
CVM_FIDC_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/"
# Formato: inf_diario_fi_{YYYYMM}.csv

# === DataJud (CNJ) ===
DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_trf"
# Endpoints por tribunal: _trf1, _trf2, _trf3, _trf4, _trf5, _trf6

# === DJEN — API Comunica ===
DJEN_API_URL = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
# Busca programática de publicações do Diário de Justiça Eletrônico Nacional
