"""
Motor de Sinistralidade ANS
Plataforma de Inteligência Analítica — Tallent Two Financial Holding
v2.1 — Redesign Executivo
"""
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import streamlit.components.v1 as components

# =========================================================
# CONFIGURAÇÃO
# =========================================================
APP_VERSION = "v2.1"
DB_PATH = "/home/ubuntu/mvp_sinistralidade/data/ans_analytics.duckdb"
LOGO_PATH = "/home/ubuntu/mvp_sinistralidade/logo_t2_sidebar.png"

st.set_page_config(
    page_title="Motor de Sinistralidade — Tallent Two",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PALETA — EXECUTIVO FINANCEIRO
# =========================================================
# Cor principal: teal/petróleo profundo (conforme briefing)
PRIMARY = "#1B4B5A"
PRIMARY_LIGHT = "#24667A"
PRIMARY_MUTED = "#3D8A9E"
SURFACE = "#FAFBFC"
SURFACE_WARM = "#F8F9FA"
GOLD = "#B8860B"
GOLD_MUTED = "#9A7209"
BORDER = "#E2E8F0"
BORDER_SUBTLE = "#F1F5F9"
TEXT_PRIMARY = "#1A202C"
TEXT_SECONDARY = "#4A5568"
TEXT_MUTED = "#718096"
WHITE = "#FFFFFF"
SUCCESS = "#0D9488"
WARNING = "#D97706"
ERROR = "#DC2626"

CHART_COLORS = [PRIMARY, PRIMARY_MUTED, "#5BA4B5", "#7DBDCC", GOLD, "#A0AEC0"]
PIE_COLORS = [PRIMARY, PRIMARY_LIGHT, PRIMARY_MUTED, "#5BA4B5", GOLD]

# =========================================================
# CSS — EXECUTIVE DESIGN SYSTEM
# =========================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* === GLOBAL === */
    .block-container {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}
    
    h1, h2, h3 {{
        font-family: 'Inter', sans-serif;
        color: {TEXT_PRIMARY};
        font-weight: 600;
    }}
    
    /* === SIDEBAR === */
    div[data-testid="stSidebar"] {{
        background: {WHITE};
        border-right: 1px solid {BORDER};
    }}
    div[data-testid="stSidebar"] .stMarkdown {{
        color: {TEXT_PRIMARY};
    }}
    div[data-testid="stSidebar"] label {{
        color: {TEXT_SECONDARY} !important;
    }}
    div[data-testid="stSidebar"] .stRadio label {{
        color: {TEXT_SECONDARY} !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        background: {SURFACE};
        border-radius: 6px;
    }}
    
    /* === HEADER EXECUTIVO === */
    .exec-header {{
        padding: 0 0 1.5rem 0;
        border-bottom: 1px solid {BORDER};
        margin-bottom: 1.5rem;
    }}
    .exec-header .product-name {{
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin: 0;
        letter-spacing: -0.02em;
    }}
    .exec-header .product-subtitle {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: {TEXT_MUTED};
        margin: 0.25rem 0 0 0;
        font-weight: 400;
    }}
    .exec-header .data-badge {{
        display: inline-block;
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 0.2rem 0.6rem;
        font-size: 0.7rem;
        color: {TEXT_MUTED};
        font-weight: 500;
        margin-top: 0.5rem;
    }}
    
    /* === KPI CARDS === */
    .kpi-row {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }}
    .kpi-card {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
    }}
    .kpi-card .kpi-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {TEXT_MUTED};
        margin-bottom: 0.4rem;
    }}
    .kpi-card .kpi-value {{
        font-family: 'Inter', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        line-height: 1.2;
        letter-spacing: -0.02em;
    }}
    .kpi-card .kpi-context {{
        font-size: 0.7rem;
        margin-top: 0.4rem;
        font-weight: 400;
        color: {TEXT_MUTED};
    }}
    .kpi-card .kpi-context.positive {{ color: {SUCCESS}; font-weight: 500; }}
    .kpi-card .kpi-context.negative {{ color: {ERROR}; font-weight: 500; }}
    .kpi-card .kpi-context.warning {{ color: {WARNING}; font-weight: 500; }}
    
    /* === SECTION HEADERS === */
    .section-title {{
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: {TEXT_PRIMARY};
        margin: 0 0 0.25rem 0;
    }}
    .section-subtitle {{
        font-size: 0.78rem;
        color: {TEXT_MUTED};
        font-weight: 400;
        margin: 0 0 1rem 0;
    }}
    
    /* === TABLES === */
    .stDataFrame thead tr th {{
        background-color: {SURFACE} !important;
        color: {TEXT_PRIMARY} !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        border-bottom: 2px solid {BORDER} !important;
    }}
    .stDataFrame tbody tr:nth-child(even) {{
        background-color: {SURFACE} !important;
    }}
    
    /* === FOOTER === */
    .t2-footer {{
        text-align: center;
        padding: 2rem 0 1rem 0;
        margin-top: 3rem;
        border-top: 1px solid {BORDER};
    }}
    .t2-footer-text {{
        font-family: 'Inter', sans-serif;
        font-size: 0.68rem;
        color: {TEXT_MUTED};
        letter-spacing: 0.04em;
    }}
    
    /* === CAPTIONS === */
    .caption {{
        font-size: 0.7rem;
        color: {TEXT_MUTED};
        margin-top: 0.5rem;
    }}
    
    /* === DIVIDERS === */
    .divider {{
        border: none;
        border-top: 1px solid {BORDER};
        margin: 2rem 0;
    }}
    .divider-subtle {{
        border: none;
        border-top: 1px solid {BORDER_SUBTLE};
        margin: 1.5rem 0;
    }}
    
    /* === SELECTBOX === */
    .stSelectbox label, .stMultiSelect label {{
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {TEXT_MUTED} !important;
        font-weight: 500 !important;
    }}
    
    /* === DOWNLOAD BUTTON === */
    .stDownloadButton button {{
        background-color: {WHITE} !important;
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {BORDER} !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
    }}
    .stDownloadButton button:hover {{
        background-color: {SURFACE} !important;
        border-color: {PRIMARY} !important;
    }}
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {{
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: {TEXT_SECONDARY} !important;
    }}
    
    /* === PLOTLY TOOLBAR HIDE === */
    .modebar {{
        display: none !important;
    }}
    
    /* === INSIGHT BOX === */
    .insight-box {{
        background: {SURFACE};
        border-left: 3px solid {PRIMARY};
        border-radius: 0 6px 6px 0;
        padding: 1rem 1.25rem;
        margin: 1.5rem 0;
        font-size: 0.85rem;
        color: {TEXT_SECONDARY};
        line-height: 1.6;
    }}
    .insight-box strong {{
        color: {TEXT_PRIMARY};
    }}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def render_kpis(kpis_list):
    """Renderiza KPIs como blocos de decisão executivos.
    Cada item: (label, value, context_text, context_type)
    context_type: 'neutral', 'positive', 'negative', 'warning'
    """
    cards_html = ""
    for kpi in kpis_list:
        label = kpi[0]
        value = kpi[1]
        context = kpi[2] if len(kpi) > 2 else ""
        ctx_type = kpi[3] if len(kpi) > 3 else "neutral"
        
        context_html = ""
        if context:
            ctx_class = f"kpi-context {ctx_type}" if ctx_type != "neutral" else "kpi-context"
            context_html = f'<div class="{ctx_class}">{context}</div>'
        
        cards_html += f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {context_html}
        </div>
        """
    
    full_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; background: transparent; }}
        .kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 0; }}
        .kpi-card {{ background: {WHITE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 1.25rem 1.5rem; }}
        .kpi-card .kpi-label {{ font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; color: {TEXT_MUTED}; margin-bottom: 0.4rem; }}
        .kpi-card .kpi-value {{ font-size: 1.75rem; font-weight: 700; color: {TEXT_PRIMARY}; line-height: 1.2; letter-spacing: -0.02em; }}
        .kpi-card .kpi-context {{ font-size: 0.7rem; margin-top: 0.4rem; font-weight: 400; color: {TEXT_MUTED}; }}
        .kpi-card .kpi-context.positive {{ color: {SUCCESS}; font-weight: 500; }}
        .kpi-card .kpi-context.negative {{ color: {ERROR}; font-weight: 500; }}
        .kpi-card .kpi-context.warning {{ color: {WARNING}; font-weight: 500; }}
    </style>
    <div class="kpi-row">{cards_html}</div>
    """
    n_cards = len(kpis_list)
    height = 120 if n_cards <= 4 else 130
    components.html(full_html, height=height)


def section_header(title, subtitle=""):
    """Header de seção limpo e executivo."""
    st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="section-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def page_footer():
    """Footer institucional discreto."""
    st.markdown(f"""
    <div class="t2-footer">
        <p class="t2-footer-text">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</p>
    </div>
    """, unsafe_allow_html=True)


def apply_layout(fig, height=380, show_legend=False):
    """Layout de gráfico executivo: limpo, sem toolbar, tipografia profissional."""
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12, color=TEXT_SECONDARY),
        margin=dict(l=0, r=0, t=24, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        showlegend=show_legend,
        legend=dict(font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        coloraxis_showscale=False
    )
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=11, color=TEXT_MUTED))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=BORDER_SUBTLE, zeroline=False, tickfont=dict(size=11, color=TEXT_MUTED))
    return fig


# =========================================================
# DATA LAYER
# =========================================================
@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data
def load_operadoras_data():
    con = get_connection()
    df = con.execute("""
        SELECT 
            CAST(s.registro_ans AS VARCHAR) as registro_ans,
            o.Nome_Fantasia as nome_operadora,
            o.Modalidade as modalidade,
            s.receita_contraprestacoes as receita,
            s.despesa_assistencial as despesa,
            s.sinistralidade_total as sinistralidade
        FROM sinistralidade_operadora s
        LEFT JOIN read_csv_auto('/home/ubuntu/mvp_sinistralidade/operadoras_ativas.csv', 
            delim=';', header=true) o
        ON CAST(s.registro_ans AS VARCHAR) = o.REGISTRO_OPERADORA
        WHERE s.sinistralidade_total IS NOT NULL
        ORDER BY s.receita_contraprestacoes DESC
    """).df()
    return df


@st.cache_data
def load_beneficiarios():
    con = get_connection()
    df = con.execute("""
        SELECT registro_ans, tipo_contratacao, cobertura, mes_competencia, total_beneficiarios
        FROM sib_operadoras
        ORDER BY mes_competencia
    """).df()
    return df


@st.cache_data
def load_produtos_proxy():
    con = get_connection()
    try:
        return con.execute("SELECT * FROM resultado_proxy").df()
    except:
        return pd.DataFrame()


# =========================================================
# SIDEBAR — NAVEGAÇÃO ESTRATÉGICA
# =========================================================
with st.sidebar:
    # Logo
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=180)
    
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:1.05rem; font-weight:700; color:{TEXT_PRIMARY}; margin:0; line-height:1.3;">Motor de Sinistralidade</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.75rem; color:{TEXT_MUTED}; margin:0.2rem 0 1.2rem 0;">Inteligência analítica para saúde suplementar</p>', unsafe_allow_html=True)
    
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:0 0 1rem 0;">', unsafe_allow_html=True)
    
    # Navegação em 5 grupos
    pagina = st.radio(
        "Navegação",
        ["Resumo Executivo", "Operadoras", "Produtos e Proxy", "Tendência e Benchmark", "Predição (ML)", "Metodologia"],
        label_visibility="collapsed"
    )
    
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:1.2rem 0 0.8rem 0;">', unsafe_allow_html=True)
    
    # Fontes
    st.markdown(f'<p style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; color:{TEXT_MUTED}; margin-bottom:0.4rem; font-weight:500;">Fontes de Dados</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0.15rem 0;">DIOPS 4T/2025</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0.15rem 0;">SIB Individualizado Mar/2026</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0.15rem 0;">Cadastro de Produtos ANS</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{PRIMARY}; margin:0.5rem 0 0 0; font-weight:600;">696.183 registros granulares</p>', unsafe_allow_html=True)
    
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:1rem 0 0.5rem 0;">', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.62rem; color:{TEXT_MUTED}; letter-spacing:0.04em;">{APP_VERSION} — Tallent Two Financial Holding</p>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 1: RESUMO EXECUTIVO
# =========================================================
if pagina == "Resumo Executivo":
    # CAMADA 1: Header Executivo
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Motor de Sinistralidade ANS</p>
        <p class="product-subtitle">Análise comparativa de sinistralidade e precificação por produto via dados abertos</p>
        <span class="data-badge">Competência: DIOPS 4T/2025 · SIB Mar/2026 · 6 operadoras</span>
    </div>
    """, unsafe_allow_html=True)
    
    # CAMADA 2: Filtros (na home, sem filtros globais — são os dados consolidados)
    
    # CAMADA 3: Conteúdo Analítico
    df_ops = load_operadoras_data()
    df_benef = load_beneficiarios()
    
    receita_total = df_ops['receita'].sum()
    sinist_media = df_ops['despesa'].sum() / df_ops['receita'].sum()
    total_vidas = df_benef[df_benef['mes_competencia'] == df_benef['mes_competencia'].max()]['total_beneficiarios'].sum()
    
    # KPIs
    sinist_status = "negative" if sinist_media > 0.80 else ("warning" if sinist_media > 0.75 else "positive")
    sinist_context = "Acima do limiar de 80%" if sinist_media > 0.80 else ("Zona de atenção" if sinist_media > 0.75 else "Dentro do esperado")
    
    render_kpis([
        ("Operadoras Analisadas", str(len(df_ops)), "Amostra selecionada"),
        ("Receita Total", f"R$ {receita_total/1e9:.2f} bi", "Contraprestações 4T/2025"),
        ("Sinistralidade Ponderada", f"{sinist_media*100:.1f}%", sinist_context, sinist_status),
        ("Vidas na Base", f"{total_vidas:,.0f}", "Último mês disponível"),
    ])
    
    # Gráfico Principal (herói)
    section_header("Sinistralidade por Operadora", "Despesa assistencial sobre receita de contraprestações — DIOPS 4T/2025")
    
    df_chart = df_ops.copy()
    df_chart['sinistralidade_pct'] = df_chart['sinistralidade'] * 100
    df_chart['nome_display'] = df_chart['nome_operadora'].fillna(df_chart['registro_ans'])
    
    fig = px.bar(
        df_chart.sort_values('sinistralidade_pct', ascending=True),
        x='sinistralidade_pct', y='nome_display', orientation='h',
        color='sinistralidade_pct',
        color_continuous_scale=[[0, SUCCESS], [0.5, WARNING], [1, ERROR]],
        range_color=[60, 90],
        labels={'sinistralidade_pct': 'Sinistralidade (%)', 'nome_display': ''},
        text=df_chart.sort_values('sinistralidade_pct', ascending=True)['sinistralidade_pct'].apply(lambda x: f'{x:.1f}%')
    )
    fig = apply_layout(fig, height=320)
    fig.update_traces(textposition='outside', textfont=dict(size=12, color=TEXT_PRIMARY, family="Inter"))
    fig.add_vline(x=75, line_dash="dot", line_color=TEXT_MUTED, 
                  annotation_text="Referência 75%", annotation_font_size=10, annotation_font_color=TEXT_MUTED)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # Gráfico Secundário
    section_header("Receita vs Despesa Assistencial", "Comparação em bilhões de reais")
    
    df_comp = df_chart[['nome_display', 'receita', 'despesa']].copy()
    df_comp['receita_bi'] = df_comp['receita'] / 1e9
    df_comp['despesa_bi'] = df_comp['despesa'] / 1e9
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name='Receita', y=df_comp['nome_display'], x=df_comp['receita_bi'],
                          orientation='h', marker_color=PRIMARY, text=df_comp['receita_bi'].apply(lambda x: f'R$ {x:.1f}B' if x > 1 else f'R$ {x*1000:.0f}M')))
    fig2.add_trace(go.Bar(name='Despesa', y=df_comp['nome_display'], x=df_comp['despesa_bi'],
                          orientation='h', marker_color=ERROR, opacity=0.7, text=df_comp['despesa_bi'].apply(lambda x: f'R$ {x:.1f}B' if x > 1 else f'R$ {x*1000:.0f}M')))
    fig2 = apply_layout(fig2, height=300, show_legend=True)
    fig2.update_layout(barmode='group', xaxis_title="R$ bilhões")
    fig2.update_traces(textposition='outside', textfont=dict(size=10))
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
    
    # Bloco interpretativo
    maior_sinist = df_chart.loc[df_chart['sinistralidade_pct'].idxmax()]
    menor_sinist = df_chart.loc[df_chart['sinistralidade_pct'].idxmin()]
    st.markdown(f"""
    <div class="insight-box">
        <strong>Leitura analítica:</strong> A operadora com maior pressão assistencial é 
        <strong>{maior_sinist['nome_display']}</strong> ({maior_sinist['sinistralidade_pct']:.1f}%), 
        enquanto <strong>{menor_sinist['nome_display']}</strong> apresenta o melhor resultado ({menor_sinist['sinistralidade_pct']:.1f}%). 
        A sinistralidade ponderada do grupo ({sinist_media*100:.1f}%) está {"acima" if sinist_media > 0.80 else "dentro"} 
        da referência setorial de 80%.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # Tabela detalhada
    section_header("Detalhamento Financeiro", "Dados consolidados por operadora")
    df_display = df_ops[['registro_ans', 'nome_operadora', 'modalidade', 'receita', 'despesa', 'sinistralidade']].copy()
    df_display.columns = ['Registro ANS', 'Operadora', 'Modalidade', 'Receita', 'Despesa Assistencial', 'Sinistralidade']
    df_display['Receita'] = df_display['Receita'].apply(lambda x: f"R$ {x/1e6:,.1f} M")
    df_display['Despesa Assistencial'] = df_display['Despesa Assistencial'].apply(lambda x: f"R$ {x/1e6:,.1f} M")
    df_display['Sinistralidade'] = df_display['Sinistralidade'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CAMADA 4: Governança (acordeão)
    with st.expander("Fontes e metodologia"):
        st.markdown(f"""
        **Fontes:** DIOPS/ANS (Demonstrações Contábeis 4T/2025), SIB/ANS (Beneficiários Mar/2026).  
        **Cálculo:** Sinistralidade = Despesa Assistencial (conta 411x) / Receita de Contraprestações (conta 311x).  
        **Limitação:** Dados agregados por operadora; granularidade por produto estimada via modelo de alocação atuarial.
        """)
    
    page_footer()


# =========================================================
# PÁGINA 2: OPERADORAS
# =========================================================
elif pagina == "Operadoras":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Análise por Operadora</p>
        <p class="product-subtitle">Detalhamento financeiro, carteira e distribuição geográfica</p>
    </div>
    """, unsafe_allow_html=True)
    
    df_ops = load_operadoras_data()
    df_benef = load_beneficiarios()
    
    # Filtro
    opcoes = df_ops['nome_operadora'].fillna(df_ops['registro_ans']).tolist()
    registros = df_ops['registro_ans'].tolist()
    selected_nome = st.selectbox("Operadora", opcoes)
    idx = opcoes.index(selected_nome)
    selected_reg = registros[idx]
    op_data = df_ops[df_ops['registro_ans'] == selected_reg].iloc[0]
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # KPIs
    sinist_val = op_data['sinistralidade'] * 100
    sinist_status = "negative" if sinist_val > 80 else ("warning" if sinist_val > 75 else "positive")
    sinist_ctx = "Acima de 80%" if sinist_val > 80 else ("Zona de atenção" if sinist_val > 75 else "Saudável")
    
    render_kpis([
        ("Receita (4T/2025)", f"R$ {op_data['receita']/1e6:,.1f} M", "Contraprestações"),
        ("Despesa Assistencial", f"R$ {op_data['despesa']/1e6:,.1f} M", "Eventos e sinistros"),
        ("Sinistralidade", f"{sinist_val:.1f}%", sinist_ctx, sinist_status),
    ])
    
    df_benef_op = df_benef[df_benef['registro_ans'] == selected_reg]
    
    if not df_benef_op.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            section_header("Tipo de Contratação")
            df_contrat = df_benef_op.groupby('tipo_contratacao')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_contrat, values='total_beneficiarios', names='tipo_contratacao',
                        color_discrete_sequence=PIE_COLORS, hole=0.5)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col_right:
            section_header("Cobertura Assistencial")
            df_cob = df_benef_op.groupby('cobertura')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_cob, values='total_beneficiarios', names='cobertura',
                        color_discrete_sequence=PIE_COLORS, hole=0.5)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Evolução temporal
        st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
        section_header("Evolução de Beneficiários", "Cobertura médico-hospitalar — meses com dados parciais removidos")
        df_med = df_benef_op[df_benef_op['cobertura'].str.contains('dico', case=False, na=False)]
        df_evol = df_med.groupby('mes_competencia')['total_beneficiarios'].sum().reset_index()
        df_evol = df_evol.sort_values('mes_competencia')
        
        mediana = df_evol['total_beneficiarios'].median()
        df_evol = df_evol[df_evol['total_beneficiarios'] >= mediana * 0.5]
        df_evol['mes_date'] = pd.to_datetime(df_evol['mes_competencia'].astype(str) + '01', format='%Y%m%d')
        df_evol = df_evol.sort_values('mes_date')
        
        fig = px.area(df_evol, x='mes_date', y='total_beneficiarios',
                     labels={'mes_date': '', 'total_beneficiarios': 'Beneficiários'},
                     color_discrete_sequence=[PRIMARY])
        fig = apply_layout(fig, height=260)
        fig.update_layout(xaxis=dict(dtick="M6", tickformat="%b/%Y"))
        fig.update_traces(line=dict(width=2), fillcolor=f"rgba(27,75,90,0.06)")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Dados de beneficiários não disponíveis para esta operadora no dataset consolidado.")
    
    # Granularidade (Sprint 4)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    section_header("Granularidade — Produto, Município e Faixa Etária", "SIB Individualizado — 28 UFs — Competência Mar/2026")
    
    try:
        con = get_connection()
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        ufs_list = con.execute(f"SELECT DISTINCT uf FROM sib_granular WHERE registro_ans = '{selected_reg}' ORDER BY uf").df()['uf'].tolist()
        with col_f1:
            sel_uf = st.selectbox("UF:", ["Todas"] + ufs_list, key="op_uf")
        
        segs = con.execute(f"SELECT DISTINCT segmentacao FROM sib_granular WHERE registro_ans = '{selected_reg}' AND segmentacao IS NOT NULL ORDER BY segmentacao").df()['segmentacao'].tolist()
        with col_f2:
            sel_seg = st.selectbox("Segmentação:", ["Todas"] + segs, key="op_seg")
        
        contrats = con.execute(f"SELECT DISTINCT tipo_contratacao FROM sib_granular WHERE registro_ans = '{selected_reg}' ORDER BY tipo_contratacao").df()['tipo_contratacao'].tolist()
        with col_f3:
            sel_contr = st.selectbox("Contratação:", ["Todas"] + contrats, key="op_contr")
        
        where_clauses = [f"registro_ans = '{selected_reg}'"]
        if sel_uf != "Todas":
            where_clauses.append(f"uf = '{sel_uf}'")
        if sel_seg != "Todas":
            where_clauses.append(f"segmentacao = '{sel_seg}'")
        if sel_contr != "Todas":
            where_clauses.append(f"tipo_contratacao = '{sel_contr}'")
        where_sql = "WHERE " + " AND ".join(where_clauses)
        
        stats = con.execute(f"""
            SELECT SUM(qt_beneficiario_ativo) as vidas, COUNT(DISTINCT cd_plano) as produtos,
                   COUNT(DISTINCT municipio) as municipios
            FROM sib_granular {where_sql}
        """).fetchone()
        
        if stats[0] and stats[0] > 0:
            vidas_fmt = f"{stats[0]/1e6:.2f}M" if stats[0] > 1e6 else f"{stats[0]/1e3:.0f}k"
            render_kpis([
                ("Vidas", vidas_fmt, "Beneficiários ativos"),
                ("Produtos", f"{stats[1]:,}", "Planos registrados"),
                ("Municípios", f"{stats[2]:,}", "Cobertura geográfica"),
            ])
            
            # Top municípios
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                section_header("Top 10 Municípios")
                df_mun = con.execute(f"""
                    SELECT municipio || ' (' || uf || ')' as municipio_uf, SUM(qt_beneficiario_ativo) as vidas
                    FROM sib_granular {where_sql}
                    GROUP BY municipio, uf ORDER BY vidas DESC LIMIT 10
                """).df()
                fig = px.bar(df_mun, x='vidas', y='municipio_uf', orientation='h',
                            color_discrete_sequence=[PRIMARY], text='vidas')
                fig = apply_layout(fig, height=300)
                fig.update_traces(textposition='outside', texttemplate='%{text:,.0f}', textfont=dict(size=10))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            with col_g2:
                section_header("Distribuição Etária")
                df_idade = con.execute(f"""
                    SELECT faixa_etaria_reajuste as faixa, SUM(qt_beneficiario_ativo) as vidas
                    FROM sib_granular {where_sql}
                    WHERE faixa_etaria_reajuste IS NOT NULL
                    GROUP BY faixa_etaria_reajuste ORDER BY faixa
                """).df()
                fig = px.bar(df_idade, x='faixa', y='vidas', color_discrete_sequence=[PRIMARY_MUTED],
                            labels={'faixa': '', 'vidas': 'Beneficiários'})
                fig = apply_layout(fig, height=300)
                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sem dados granulares disponíveis para esta operadora com os filtros selecionados.")
    except Exception as e:
        st.warning(f"Dados granulares indisponíveis: {e}")
    
    page_footer()


# =========================================================
# PÁGINA 3: PRODUTOS E PROXY
# =========================================================
elif pagina == "Produtos e Proxy":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Produtos e Proxy de Sinistralidade</p>
        <p class="product-subtitle">Estimativa de sinistralidade por produto via modelo de alocação atuarial</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Score de Risco (Sprint 5)
    try:
        con = get_connection()
        
        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        ops = con.execute("SELECT DISTINCT razao_social FROM score_risco_produto_agg ORDER BY razao_social").df()['razao_social'].tolist()
        with col_f1:
            op_sel = st.selectbox("Operadora:", ["Todas"] + ops, key="sr_op")
        segs = con.execute("SELECT DISTINCT segmentacao FROM score_risco_produto_agg WHERE segmentacao IS NOT NULL ORDER BY segmentacao").df()['segmentacao'].tolist()
        with col_f2:
            seg_sel = st.selectbox("Segmentação:", ["Todas"] + segs, key="sr_seg")
        contrats = con.execute("SELECT DISTINCT tipo_contratacao FROM score_risco_produto_agg ORDER BY tipo_contratacao").df()['tipo_contratacao'].tolist()
        with col_f3:
            contr_sel = st.selectbox("Contratação:", ["Todas"] + contrats, key="sr_contr")
        
        where_parts = []
        if op_sel != "Todas":
            where_parts.append(f"razao_social = '{op_sel}'")
        if seg_sel != "Todas":
            where_parts.append(f"segmentacao = '{seg_sel}'")
        if contr_sel != "Todas":
            where_parts.append(f"tipo_contratacao = '{contr_sel}'")
        where_score = "WHERE " + " AND ".join(where_parts) if where_parts else ""
        
        st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
        
        # KPIs
        kpi_data = con.execute(f"""
            SELECT COUNT(DISTINCT cd_plano) as produtos, SUM(vidas_total) as vidas,
                   SUM(despesa_estimada) as despesa, AVG(sinistralidade_estimada) as sinist,
                   AVG(custo_per_capita_medio) as custo_pc
            FROM score_risco_produto_agg {where_score}
        """).fetchone()
        
        vidas_fmt = f"{kpi_data[1]/1e6:.2f}M" if kpi_data[1] and kpi_data[1] > 1e6 else f"{kpi_data[1]/1e3:.0f}k" if kpi_data[1] else "0"
        desp_fmt = f"R$ {kpi_data[2]/1e9:.2f} bi" if kpi_data[2] and kpi_data[2] > 1e9 else f"R$ {kpi_data[2]/1e6:.0f} M" if kpi_data[2] else "N/A"
        
        render_kpis([
            ("Produtos", f"{kpi_data[0]:,}" if kpi_data[0] else "0", "Com score calculado"),
            ("Vidas", vidas_fmt, "Beneficiários ativos"),
            ("Despesa Estimada", desp_fmt, "Alocação proporcional"),
            ("Custo Per Capita", f"R$ {kpi_data[4]:,.0f}/mês" if kpi_data[4] else "N/A", "Média ponderada"),
        ])
        
        # Gráfico principal: Custo por Operadora
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            section_header("Custo Per Capita por Operadora")
            df_op_custo = con.execute(f"""
                SELECT 
                    CASE 
                        WHEN razao_social LIKE '%PESSOAL%' THEN 'Pessoal Saúde'
                        WHEN razao_social LIKE '%SANTA CASA%' THEN 'Sta Casa Mauá'
                        WHEN razao_social LIKE '%SANTA HELENA%' THEN 'Sta Helena'
                        WHEN razao_social LIKE '%SF SISTEMAS%' THEN 'SF Sistemas'
                        WHEN razao_social LIKE '%NOTRE DAME%' THEN 'Hapvida NDI'
                        ELSE razao_social
                    END as operadora,
                    AVG(custo_per_capita_medio) as custo_pc,
                    SUM(vidas_total) as vidas,
                    AVG(sinistralidade_estimada) as sinist
                FROM score_risco_produto_agg {where_score}
                GROUP BY operadora ORDER BY custo_pc DESC
            """).df()
            
            fig = px.bar(df_op_custo, x='operadora', y='custo_pc',
                        color_discrete_sequence=[PRIMARY],
                        labels={'operadora': '', 'custo_pc': 'R$/mês'},
                        text=df_op_custo['custo_pc'].apply(lambda x: f'R$ {x:.0f}'))
            fig = apply_layout(fig, height=350)
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col_g2:
            section_header("Custo Per Capita por UF")
            df_uf = con.execute(f"""
                SELECT uf, custo_per_capita, vidas, produtos
                FROM score_risco_uf
                ORDER BY custo_per_capita DESC
                LIMIT 15
            """).df()
            
            if not df_uf.empty:
                fig = px.bar(df_uf, x='uf', y='custo_per_capita',
                            color_discrete_sequence=[PRIMARY_MUTED],
                            labels={'uf': '', 'custo_per_capita': 'R$/mês'},
                            text=df_uf['custo_per_capita'].apply(lambda x: f'R${x:.0f}'))
                fig = apply_layout(fig, height=350)
                fig.update_traces(textposition='outside', textfont_size=9)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
        
        # Ranking de Produtos
        section_header("Ranking de Produtos por Custo Per Capita", "Ordenado por maior custo estimado mensal por beneficiário")
        
        df_ranking = con.execute(f"""
            SELECT 
                CASE 
                    WHEN razao_social LIKE '%PESSOAL%' THEN 'Pessoal Saúde'
                    WHEN razao_social LIKE '%SANTA CASA%' THEN 'Sta Casa Mauá'
                    WHEN razao_social LIKE '%SANTA HELENA%' THEN 'Sta Helena'
                    WHEN razao_social LIKE '%SF SISTEMAS%' THEN 'SF Sistemas'
                    WHEN razao_social LIKE '%NOTRE DAME%' THEN 'Hapvida NDI'
                    ELSE razao_social
                END as "Operadora",
                cd_plano as "Produto",
                segmentacao as "Segmentação",
                tipo_contratacao as "Contratação",
                vidas_total as "Vidas",
                ROUND(custo_per_capita_medio, 0) as "Custo PC (R$/mês)",
                ROUND(sinistralidade_estimada * 100, 1) as "Sinist. (%)",
                ROUND(fator_etario_medio, 2) as "Fator Etário"
            FROM score_risco_produto_agg {where_score}
            ORDER BY custo_per_capita_medio DESC
            LIMIT 50
        """).df()
        
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        
        csv_score = df_ranking.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar ranking (.csv)", csv_score, "score_risco_produtos.csv", "text/csv")
        
        # Metodologia inline
        with st.expander("Como o score de risco é calculado"):
            st.markdown(f"""
            O rateio distribui a despesa assistencial total (DIOPS) entre produtos proporcionalmente ao score:  
            `Score = Vidas × Fator_Etário × Fator_Geográfico × Fator_Segmentação × Fator_Contratação`  
            Fontes: RN 63/2003 (curva etária), VCMH/IESS (geográfico), DIOPS 4T/2025, SIB Mar/2026.
            """)
    
    except Exception as e:
        st.error(f"Erro ao carregar Score de Risco: {e}")
    
    page_footer()


# =========================================================
# PÁGINA 4: TENDÊNCIA E BENCHMARK
# =========================================================
elif pagina == "Tendência e Benchmark":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Tendência e Benchmark</p>
        <p class="product-subtitle">Evolução histórica 2020-2025 e comparação com referências de mercado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- SÉRIE TEMPORAL ---
    try:
        con_st = duckdb.connect(DB_PATH, read_only=True)
        
        df_hist = con_st.execute("""
            SELECT registro_ans, trimestre, receita, despesa, sinistralidade
            FROM sinistralidade_historica
            ORDER BY registro_ans, trimestre
        """).df()
        
        nomes_ops = {
            '310239': 'Pessoal Saúde', '355097': 'Santa Helena', '359017': 'Hapvida NDI',
            '417491': 'Portomed', '421197': 'Santa Casa Mauá', '422371': 'SF Sistemas'
        }
        df_hist['operadora'] = df_hist['registro_ans'].map(nomes_ops)
        
        def trimestre_to_order(t):
            q = int(t[0])
            y = int(t[2:])
            return y * 4 + q
        
        df_hist['ordem'] = df_hist['trimestre'].apply(trimestre_to_order)
        df_hist = df_hist.sort_values(['registro_ans', 'ordem'])
        
        # Calcular sinistralidade trimestral
        records = []
        for reg in df_hist['registro_ans'].unique():
            df_op = df_hist[df_hist['registro_ans'] == reg].sort_values('ordem')
            prev_receita = 0
            prev_despesa = 0
            prev_year = None
            
            for _, row in df_op.iterrows():
                q = int(row['trimestre'][0])
                year = int(row['trimestre'][2:])
                
                if q == 1 or year != prev_year:
                    rec_tri = row['receita']
                    desp_tri = row['despesa']
                    prev_receita = row['receita']
                    prev_despesa = row['despesa']
                    prev_year = year
                else:
                    rec_tri = row['receita'] - prev_receita
                    desp_tri = row['despesa'] - prev_despesa
                    prev_receita = row['receita']
                    prev_despesa = row['despesa']
                
                sinist_tri = desp_tri / rec_tri if rec_tri > 0 else None
                records.append({
                    'registro_ans': reg, 'operadora': nomes_ops.get(reg, reg),
                    'trimestre': row['trimestre'], 'ordem': row['ordem'],
                    'receita_tri': rec_tri, 'despesa_tri': desp_tri, 'sinistralidade_tri': sinist_tri
                })
        
        df_tri = pd.DataFrame(records)
        df_tri = df_tri[df_tri['sinistralidade_tri'].notna()]
        df_tri = df_tri[(df_tri['sinistralidade_tri'] > 0) & (df_tri['sinistralidade_tri'] < 2.0)]
        
        # KPIs de tendência
        sinist_atual = df_tri[df_tri['trimestre'] == '4T2025']['sinistralidade_tri'].mean()
        sinist_2020 = df_tri[df_tri['trimestre'] == '4T2020']['sinistralidade_tri'].mean()
        variacao = ((sinist_atual / sinist_2020) - 1) * 100 if sinist_2020 and sinist_2020 > 0 else 0
        
        render_kpis([
            ("Operadoras", str(df_tri['registro_ans'].nunique()), "Com série histórica"),
            ("Trimestres", str(df_tri['trimestre'].nunique()), "Período 2020-2025"),
            ("Sinistralidade Atual", f"{sinist_atual*100:.1f}%" if sinist_atual else "N/A", 
             "Acima de 80%" if sinist_atual and sinist_atual > 0.8 else "Dentro do esperado",
             "negative" if sinist_atual and sinist_atual > 0.8 else "positive"),
            ("Variação 5 anos", f"{variacao:+.0f}%", 
             "Piora" if variacao > 0 else "Melhora",
             "negative" if variacao > 0 else "positive"),
        ])
        
        st.markdown(f'<p class="caption">Sinistralidade = Despesa Assistencial / Receita. Valores trimestrais isolados (não acumulados).</p>', unsafe_allow_html=True)
        
        # Filtro de operadoras
        ops_disponiveis = sorted(df_tri['operadora'].unique())
        ops_selecionadas = st.multiselect("Operadoras", ops_disponiveis, default=ops_disponiveis, key="st_ops")
        df_filtered = df_tri[df_tri['operadora'].isin(ops_selecionadas)]
        
        # Gráfico principal: Evolução
        section_header("Evolução da Sinistralidade Trimestral", "Despesa assistencial / Receita por trimestre isolado")
        
        fig_line = px.line(
            df_filtered.sort_values('ordem'),
            x='trimestre', y='sinistralidade_tri', color='operadora', markers=True,
            color_discrete_sequence=[PRIMARY, GOLD, '#5BA4B5', '#E07A5F', '#3D405B', '#81B29A']
        )
        fig_line.update_yaxes(tickformat='.0%', title=None)
        fig_line.update_xaxes(title=None, tickangle=-45)
        fig_line.add_hline(y=0.80, line_dash="dash", line_color=ERROR, annotation_text="Alerta 80%", annotation_font_size=10)
        fig_line.add_hline(y=0.70, line_dash="dot", line_color=TEXT_MUTED, annotation_text="Referência 70%", annotation_font_size=10)
        apply_layout(fig_line, height=400, show_legend=True)
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        
        # Tabela de tendências
        section_header("Indicadores de Tendência", "CAGR de receita e variação de sinistralidade no período")
        
        tendencias = []
        for reg in df_hist['registro_ans'].unique():
            df_op = df_hist[df_hist['registro_ans'] == reg]
            df_4t = df_op[df_op['trimestre'].str.startswith('4T')].sort_values('ordem')
            if len(df_4t) >= 2:
                rec_ini = df_4t.iloc[0]['receita']
                rec_fin = df_4t.iloc[-1]['receita']
                n_anos = len(df_4t) - 1
                cagr_rec = ((rec_fin / rec_ini) ** (1/n_anos) - 1) * 100 if rec_ini > 0 else 0
                sin_ini = df_4t.iloc[0]['sinistralidade'] * 100
                sin_fin = df_4t.iloc[-1]['sinistralidade'] * 100
                delta_sin = sin_fin - sin_ini
                tendencias.append({
                    'Operadora': nomes_ops.get(reg, reg),
                    'Receita Atual (R$M)': f"{rec_fin/1e6:.0f}",
                    'CAGR Receita': f"{cagr_rec:.1f}%",
                    'Sinist. Atual': f"{sin_fin:.1f}%",
                    'Delta': f"{delta_sin:+.1f} pp",
                    'Tendência': 'Piora' if delta_sin > 3 else ('Melhora' if delta_sin < -3 else 'Estável')
                })
        
        st.dataframe(pd.DataFrame(tendencias), use_container_width=True, hide_index=True)
        
        con_st.close()
    except Exception as e:
        st.warning(f"Série temporal indisponível: {e}")
    
    # --- BENCHMARK IESS ---
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    section_header("Benchmark de Mercado", "Comparação com indicadores IESS, ANS e UNIDAS 2024")
    
    try:
        con_b = duckdb.connect(DB_PATH, read_only=True)
        
        benchmark_data = con_b.execute("""
            SELECT nome_operadora, tipo_operadora,
                   ROUND(sinistralidade_operadora, 1) AS sinist_real,
                   ROUND(benchmark_sinistralidade, 1) AS benchmark,
                   ROUND(delta_vs_benchmark, 1) AS delta,
                   classificacao_benchmark
            FROM resultado_benchmark
            WHERE nome_operadora IS NOT NULL
            GROUP BY nome_operadora, tipo_operadora, sinistralidade_operadora, 
                     benchmark_sinistralidade, delta_vs_benchmark, classificacao_benchmark
            ORDER BY delta_vs_benchmark
        """).fetchdf()
        
        sinist_mercado = 82.2
        
        # Gráfico comparativo
        fig_bench = go.Figure()
        fig_bench.add_trace(go.Bar(
            x=benchmark_data['nome_operadora'], y=benchmark_data['sinist_real'],
            name='Sinistralidade Real', marker_color=PRIMARY,
            text=benchmark_data['sinist_real'].apply(lambda x: f'{x:.1f}%'), textposition='outside'
        ))
        fig_bench.add_trace(go.Bar(
            x=benchmark_data['nome_operadora'], y=benchmark_data['benchmark'],
            name='Benchmark (Tipo)', marker_color=GOLD,
            text=benchmark_data['benchmark'].apply(lambda x: f'{x:.1f}%'), textposition='outside'
        ))
        fig_bench.add_hline(y=sinist_mercado, line_dash="dash", line_color=ERROR,
                           annotation_text=f"Mercado: {sinist_mercado}%", annotation_font_size=10)
        fig_bench.update_layout(barmode='group', yaxis_range=[0, 100], yaxis_title="Sinistralidade (%)")
        apply_layout(fig_bench, height=380, show_legend=True)
        st.plotly_chart(fig_bench, use_container_width=True, config={'displayModeBar': False})
        
        # Tabela de classificação
        display_df = benchmark_data[['nome_operadora', 'tipo_operadora', 'sinist_real', 'benchmark', 'delta', 'classificacao_benchmark']].copy()
        display_df.columns = ['Operadora', 'Tipo', 'Sinistralidade', 'Benchmark', 'Delta (pp)', 'Classificação']
        display_df['Sinistralidade'] = display_df['Sinistralidade'].apply(lambda x: f'{x:.1f}%')
        display_df['Benchmark'] = display_df['Benchmark'].apply(lambda x: f'{x:.1f}%')
        display_df['Delta (pp)'] = display_df['Delta (pp)'].apply(lambda x: f'{x:+.1f}')
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        con_b.close()
    except Exception as e:
        st.warning(f"Benchmark indisponível: {e}")
    
    with st.expander("Fontes de benchmark"):
        st.markdown("""
        - VCMH/IESS — Variação de Custos Médico-Hospitalares (Edição Abril/2026, data-base Set/2023)
        - Panorama ANS — Saúde Suplementar, 8a Edição (Mar/2025)
        - Pesquisa Nacional UNIDAS 2023 — Custo assistencial per capita por região
        - ANS Dados Econômico-Financeiros 2024 — Sinistralidade 4T/2024: 82.2%
        """)
    
    page_footer()



# =========================================================
# PÁGINA: PREDIÇÃO (SPRINT 8)
# =========================================================
elif pagina == "Predição (ML)":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Modelo Preditivo XGBoost</p>
        <p class="product-subtitle">Predição de sinistralidade e classificação de risco por produto — Sprint 8</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar resultados do modelo
    import json
    models_dir = os.path.join(os.path.dirname(__file__), "data", "models")
    
    try:
        with open(os.path.join(models_dir, "sprint8_resultados.json"), 'r') as f:
            resultados_ml = json.load(f)
        
        # --- CAMADA 2: Métricas dos Modelos ---
        section_header("Performance dos Modelos", "Métricas de avaliação no conjunto de teste")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="background:{SURFACE}; border:1px solid {BORDER}; border-radius:6px; padding:1.2rem; margin-bottom:1rem;">
                <p style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:{TEXT_MUTED}; margin-bottom:0.6rem; font-weight:600;">Modelo 1 — Regressão por Operadora</p>
                <p style="font-size:0.78rem; color:{TEXT_SECONDARY}; margin-bottom:0.8rem;">Prediz sinistralidade do próximo trimestre usando série temporal</p>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.8rem;">
                    <div>
                        <p style="font-size:0.62rem; text-transform:uppercase; color:{TEXT_MUTED}; margin-bottom:0.2rem;">R²</p>
                        <p style="font-size:1.3rem; font-weight:700; color:{PRIMARY}; margin:0;">{resultados_ml['modelo_1_operadora']['r2_test']:.3f}</p>
                    </div>
                    <div>
                        <p style="font-size:0.62rem; text-transform:uppercase; color:{TEXT_MUTED}; margin-bottom:0.2rem;">MAE</p>
                        <p style="font-size:1.3rem; font-weight:700; color:{PRIMARY}; margin:0;">{resultados_ml['modelo_1_operadora']['mae_test']:.1%}</p>
                    </div>
                    <div>
                        <p style="font-size:0.62rem; text-transform:uppercase; color:{TEXT_MUTED}; margin-bottom:0.2rem;">CV MAE</p>
                        <p style="font-size:1.3rem; font-weight:700; color:{PRIMARY}; margin:0;">{resultados_ml['modelo_1_operadora']['cv_mae_mean']:.1%}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background:{SURFACE}; border:1px solid {BORDER}; border-radius:6px; padding:1.2rem; margin-bottom:1rem;">
                <p style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:{TEXT_MUTED}; margin-bottom:0.6rem; font-weight:600;">Modelo 2 — Classificação por Produto</p>
                <p style="font-size:0.78rem; color:{TEXT_SECONDARY}; margin-bottom:0.8rem;">Classifica risco de cada produto (Baixo/Médio/Alto/Crítico)</p>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.8rem;">
                    <div>
                        <p style="font-size:0.62rem; text-transform:uppercase; color:{TEXT_MUTED}; margin-bottom:0.2rem;">Accuracy</p>
                        <p style="font-size:1.3rem; font-weight:700; color:{PRIMARY}; margin:0;">{resultados_ml['modelo_2_produto']['accuracy_test']:.1%}</p>
                    </div>
                    <div>
                        <p style="font-size:0.62rem; text-transform:uppercase; color:{TEXT_MUTED}; margin-bottom:0.2rem;">F1 Weighted</p>
                        <p style="font-size:1.3rem; font-weight:700; color:{PRIMARY}; margin:0;">{resultados_ml['modelo_2_produto']['f1_weighted_test']:.3f}</p>
                    </div>
                    <div>
                        <p style="font-size:0.62rem; text-transform:uppercase; color:{TEXT_MUTED}; margin-bottom:0.2rem;">CV F1</p>
                        <p style="font-size:1.3rem; font-weight:700; color:{PRIMARY}; margin:0;">{resultados_ml['modelo_2_produto']['cv_f1_mean']:.3f}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # --- Predições Próximo Trimestre ---
        section_header("Predições — Próximo Trimestre", "Sinistralidade estimada para 1T/2026 por operadora")
        
        df_pred = pd.DataFrame(resultados_ml['predicoes'])
        
        # Mapa de nomes
        nomes_ops = {
            '310239': 'Pessoal Saúde',
            '355097': 'Santa Helena',
            '359017': 'Hapvida NDI',
            '417491': 'Portomed',
            '421197': 'Santa Casa Mauá',
            '422371': 'SF Sistemas'
        }
        df_pred['operadora'] = df_pred['registro_ans'].map(nomes_ops)
        
        # Gráfico de predição com intervalo de confiança
        fig_pred = go.Figure()
        
        # Barras de sinistralidade atual
        fig_pred.add_trace(go.Bar(
            x=df_pred['operadora'],
            y=df_pred['sinistralidade_atual'],
            name='Atual (4T/2025)',
            marker_color=TEXT_MUTED,
            opacity=0.6
        ))
        
        # Barras de predição
        colors_pred = [SUCCESS if t == 'Melhora' else WARNING for t in df_pred['tendencia']]
        fig_pred.add_trace(go.Bar(
            x=df_pred['operadora'],
            y=df_pred['predicao_proximo_trim'],
            name='Predição (1T/2026)',
            marker_color=colors_pred,
            error_y=dict(
                type='data',
                symmetric=False,
                array=(df_pred['ic_superior'] - df_pred['predicao_proximo_trim']).tolist(),
                arrayminus=(df_pred['predicao_proximo_trim'] - df_pred['ic_inferior']).tolist(),
                color=TEXT_MUTED,
                thickness=1.5
            )
        ))
        
        fig_pred.update_layout(
            barmode='group',
            yaxis_tickformat='.0%',
            yaxis_title='Sinistralidade',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=380,
            margin=dict(l=50, r=20, t=40, b=60),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Inter', size=11, color=TEXT_PRIMARY),
            yaxis=dict(gridcolor='#F3F4F6', gridwidth=1)
        )
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        # Insight box
        melhoram = df_pred[df_pred['tendencia'] == 'Melhora']['operadora'].tolist()
        pioram = df_pred[df_pred['tendencia'] == 'Piora']['operadora'].tolist()
        
        insight_text = f"O modelo prevê **melhora** para {', '.join(melhoram) if melhoram else 'nenhuma'} e **piora** para {', '.join(pioram) if pioram else 'nenhuma'}."
        st.markdown(f"""
        <div style="border-left:3px solid {PRIMARY}; padding:0.8rem 1rem; background:{SURFACE}; margin:1rem 0; border-radius:0 4px 4px 0;">
            <p style="font-size:0.78rem; color:{TEXT_PRIMARY}; margin:0; line-height:1.5;">{insight_text}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- SHAP: Feature Importance ---
        section_header("Explicabilidade (SHAP)", "Fatores que mais influenciam a predição de sinistralidade")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown(f'<p style="font-size:0.72rem; font-weight:600; color:{TEXT_PRIMARY}; margin-bottom:0.5rem;">Modelo 1 — Operadora (Série Temporal)</p>', unsafe_allow_html=True)
            fi_m1_data = resultados_ml['feature_importance_m1'][:8]
            
            # Nomes legíveis
            feature_names_readable = {
                'sinist_lag_1': 'Sinistralidade T-1',
                'delta_sinist_1': 'Variação Trimestral',
                'tendencia_4t': 'Tendência 4 Trim.',
                'sinist_ma4': 'Média Móvel 4T',
                'receita_lag_1': 'Receita T-1',
                'sinist_lag_4': 'Sinistralidade T-4',
                'sinist_lag_2': 'Sinistralidade T-2',
                'receita_lag_4': 'Receita T-4',
                'log_receita': 'Log Receita',
                'trim_num': 'Trimestre (Sazonalidade)',
                'receita_growth_4t': 'Crescimento Receita 12m',
                'tipo_operadora_enc': 'Tipo de Operadora'
            }
            
            fig_shap1 = go.Figure(go.Bar(
                x=[d['shap_mean_abs'] for d in fi_m1_data],
                y=[feature_names_readable.get(d['feature'], d['feature']) for d in fi_m1_data],
                orientation='h',
                marker_color=PRIMARY
            ))
            fig_shap1.update_layout(
                height=280,
                margin=dict(l=140, r=20, t=10, b=30),
                xaxis_title='SHAP Mean |Value|',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter', size=10, color=TEXT_PRIMARY),
                yaxis=dict(autorange='reversed')
            )
            st.plotly_chart(fig_shap1, use_container_width=True)
        
        with col_s2:
            st.markdown(f'<p style="font-size:0.72rem; font-weight:600; color:{TEXT_PRIMARY}; margin-bottom:0.5rem;">Modelo 2 — Produto (Cross-Section)</p>', unsafe_allow_html=True)
            fi_m2_data = resultados_ml['feature_importance_m2'][:8]
            
            feature_names_readable_m2 = {
                'registro_ans_enc': 'Operadora',
                'sinist_total_operadora': 'Sinistralidade da Operadora',
                'custo_per_capita_medio': 'Custo Per Capita',
                'proporcao_score_vidas': 'Score/Vidas',
                'log_vidas': 'Log Vidas',
                'municipios': 'Qtd Municípios',
                'fator_etario_medio': 'Fator Etário Médio',
                'concentracao_geo': 'Concentração Geográfica',
                'segmentacao_enc': 'Segmentação',
                'tipo_contratacao_enc': 'Tipo Contratação',
                'abrangencia_enc': 'Abrangência',
                'ufs': 'Qtd UFs'
            }
            
            fig_shap2 = go.Figure(go.Bar(
                x=[d['shap_mean_abs'] for d in fi_m2_data],
                y=[feature_names_readable_m2.get(d['feature'], d['feature']) for d in fi_m2_data],
                orientation='h',
                marker_color=PRIMARY_MUTED
            ))
            fig_shap2.update_layout(
                height=280,
                margin=dict(l=160, r=20, t=10, b=30),
                xaxis_title='SHAP Mean |Value|',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter', size=10, color=TEXT_PRIMARY),
                yaxis=dict(autorange='reversed')
            )
            st.plotly_chart(fig_shap2, use_container_width=True)
        
        # Interpretação
        st.markdown(f"""
        <div style="border-left:3px solid {PRIMARY}; padding:0.8rem 1rem; background:{SURFACE}; margin:1rem 0; border-radius:0 4px 4px 0;">
            <p style="font-size:0.72rem; font-weight:600; color:{TEXT_PRIMARY}; margin-bottom:0.3rem;">Interpretação SHAP</p>
            <p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0; line-height:1.5;">
                <strong>Modelo 1:</strong> A sinistralidade do trimestre anterior (lag 1) é o fator dominante, seguido pela variação recente e tendência de 4 trimestres. Isso confirma que a sinistralidade tem forte inércia temporal.<br>
                <strong>Modelo 2:</strong> A operadora em si é o fator mais importante (cada uma tem sua estrutura de custo), seguido pela sinistralidade total e custo per capita. Fatores de produto (segmentação, contratação) têm peso menor.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- Tabela de Predições ---
        section_header("Detalhamento das Predições", "Valores numéricos com intervalo de confiança")
        
        df_display = df_pred[['operadora', 'sinistralidade_atual', 'predicao_proximo_trim', 'ic_inferior', 'ic_superior', 'delta_previsto', 'tendencia']].copy()
        df_display.columns = ['Operadora', 'Sinist. Atual', 'Predição 1T/2026', 'IC Inferior', 'IC Superior', 'Delta', 'Tendência']
        
        # Formatar
        for col in ['Sinist. Atual', 'Predição 1T/2026', 'IC Inferior', 'IC Superior', 'Delta']:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.1%}" if abs(x) < 2 else f"{x:.4f}")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Governança
        with st.expander("Governança — Modelo Preditivo"):
            st.markdown(f"""
            **Metodologia:**
            - Modelo 1: XGBoost Regressor com 12 features temporais (lags, médias móveis, tendências)
            - Modelo 2: XGBoost Classifier com 12 features de produto (segmentação, porte, geografia)
            - Validação: Time Series Split (3 folds) para Modelo 1, Stratified K-Fold (5 folds) para Modelo 2
            
            **Limitações:**
            - Modelo 1 treinado com apenas 108 registros (6 operadoras × 18 trimestres úteis)
            - Modelo 2 tem desbalanceamento de classes (97.5% Médio, 2.1% Alto, 0.4% Baixo)
            - Predições assumem continuidade das condições atuais (sem eventos disruptivos)
            - Intervalo de confiança baseado no MAE do teste (±1.7 pp)
            
            **Fontes:**
            - DIOPS 2020-2025 (24 trimestres × 6 operadoras)
            - Score de Risco Sprint 5 (1.793 produtos)
            - XGBoost 2.0 + SHAP 0.44
            """)
    
    except FileNotFoundError:
        st.warning("Modelos ainda não treinados. Execute sprint8_xgboost.py primeiro.")
    
    page_footer()



# =========================================================
# PÁGINA 6: METODOLOGIA
# =========================================================
elif pagina == "Metodologia":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Metodologia e Governança</p>
        <p class="product-subtitle">Modelo de cálculo, fontes de dados, limitações e roadmap de evolução</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Objetivo
    st.markdown(f"""
    <div class="insight-box">
        <strong>Objetivo:</strong> Estimar a sinistralidade por produto a partir de dados públicos da ANS, 
        distribuindo a despesa assistencial total da operadora (DIOPS) entre seus produtos cadastrados, 
        proporcionalmente a fatores de risco conhecidos.
    </div>
    """, unsafe_allow_html=True)
    
    # Modelo
    section_header("Modelo de Cálculo")
    st.code("Sinistralidade_Estimada(produto) = Sinistralidade_Total(operadora) × Peso_Relativo(produto)", language=None)
    st.code("Peso_Relativo = F_Segmentação × F_Contratação × F_Geográfico × F_Etário × F_Moderador", language=None)
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # Fatores
    section_header("Fatores de Ponderação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Segmentação Assistencial**")
        st.markdown("""
| Segmentação | Fator |
|---|---|
| Exclusivamente Odontológico | 0.40 |
| Ambulatorial | 0.70 |
| Hospitalar | 0.90 |
| Ambulatorial + Hospitalar | 1.10 |
| Referência | 1.15 |
""")
        st.markdown("**Abrangência Geográfica**")
        st.markdown("""
| Abrangência | Fator |
|---|---|
| Municipal | 0.85 |
| Grupo de municípios | 0.90 |
| Estadual | 0.95 |
| Grupo de estados | 1.05 |
| Nacional | 1.15 |
""")
    
    with col2:
        st.markdown("**Tipo de Contratação**")
        st.markdown("""
| Contratação | Fator |
|---|---|
| Coletivo empresarial | 0.85 |
| Coletivo por adesão | 0.95 |
| Individual ou Familiar | 1.20 |
""")
        st.markdown("**Mecanismo de Regulação**")
        st.markdown("""
| Moderador | Fator |
|---|---|
| Coparticipação e Franquia | 0.82 |
| Franquia | 0.85 |
| Coparticipação | 0.88 |
| Ausente | 1.05 |
""")
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # Limitações
    section_header("Limitações Conhecidas")
    st.markdown("""
1. **Viés de Mix de Carteira** — Produtos deficitários podem ser subsidiados por rentáveis dentro da mesma operadora
2. **Ausência de NTRP** — Sem acesso às premissas atuariais reais transmitidas à ANS
3. **Defasagem Temporal** — DIOPS trimestral vs SIB mensal podem ter defasagens de até 3 meses
4. **Dados Agregados** — O DIOPS não discrimina despesa por produto, apenas por operadora
5. **Fatores Fixos** — Os pesos de segmentação e contratação são baseados em literatura, não calibrados por operadora
""")
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # Fontes
    section_header("Fontes de Dados")
    st.markdown("""
| Fonte | Período | Frequência |
|---|---|---|
| DIOPS (Demonstrações Contábeis) | 4T/2025 | Trimestral |
| SIB Individualizado (Beneficiários) | Mar/2026 | Mensal |
| Cadastro de Produtos ANS | Mai/2026 | Contínua |
| Cadastro de Operadoras (CADOP) | Mai/2026 | Contínua |
| VCMH/IESS (Benchmark) | Set/2023 | Anual |
| Pesquisa UNIDAS | 2023 | Anual |
""")
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # Roadmap
    section_header("Roadmap de Evolução")
    st.markdown("""
| Sprint | Entrega | Status |
|---|---|---|
| 1 | Sinistralidade por operadora (DIOPS + SIB consolidado) | Concluído |
| 2 | Motor de proxy por produto (fatores de ponderação) | Concluído |
| 3 | Prova de conceito de granularidade (SIB individualizado) | Concluído |
| 4 | Ingestão completa do SIB individualizado — 696k registros | Concluído |
| 5 | Score de risco por produto e município (alocação atuarial) | Concluído |
| 6 | Série temporal (DIOPS 2020-2025) e tendências | Concluído |
| 7 | Integração benchmark IESS e calibração geográfica | Concluído |
| 8 | Modelo preditivo XGBoost | Planejado |
| 9 | API REST e interface de consulta | Planejado |
""")
    
    page_footer()
