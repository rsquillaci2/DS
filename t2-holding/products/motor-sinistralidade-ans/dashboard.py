"""
Motor de Sinistralidade ANS
Dashboard Analítico — Tallent Two Financial Holding
v1.0 — Design System Upgrade
"""
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import base64
import os
import streamlit.components.v1 as components

# =========================================================
# CONFIGURAÇÃO
# =========================================================
APP_VERSION = "v1.0"
DB_PATH = "/home/ubuntu/mvp_sinistralidade/data/ans_analytics.duckdb"
LOGO_PATH = "/home/ubuntu/mvp_sinistralidade/logo_t2_sidebar.png"

st.set_page_config(
    page_title="Motor de Sinistralidade ANS — Tallent Two",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# BRAND STYLE — TALLENT TWO DS
# =========================================================
PRIMARY = "#2C3D5B"
PRIMARY_LIGHT = "#3D5278"
PRIMARY_MUTED = "#5A7099"
SURFACE = "#FFF3DE"
GOLD = "#FFD700"
GOLD_MUTED = "#C9A227"
GRAY = "#BEBEBE"
GRAY_500 = "#6B7280"
GRAY_100 = "#F3F4F6"
WHITE = "#FFFFFF"
BLACK = "#000000"
SUCCESS = "#16A34A"
WARNING = "#CA8A04"
ERROR = "#DC2626"

CHART_COLORS = [PRIMARY, PRIMARY_MUTED, "#7D92B3", "#A8B8D0", GOLD_MUTED, "#9CA3AF"]
PIE_COLORS = [PRIMARY, PRIMARY_MUTED, "#7D92B3", "#A8B8D0", GOLD_MUTED]

# =========================================================
# CUSTOM CSS — DESIGN SYSTEM UPGRADE
# =========================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;700;800&family=Roboto:wght@300;400;500;700&display=swap');
    
    /* === GLOBAL === */
    .block-container {{
        font-family: 'Roboto', sans-serif;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}
    
    h1, h2, h3 {{
        font-family: 'Playfair Display', serif;
        color: {PRIMARY};
    }}
    
    /* === SIDEBAR === */
    div[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {PRIMARY} 0%, #1E2D45 100%);
    }}
    div[data-testid="stSidebar"] .stMarkdown {{
        color: {WHITE};
    }}
    div[data-testid="stSidebar"] label {{
        color: rgba(255,243,222,0.85) !important;
    }}
    div[data-testid="stSidebar"] .stRadio label {{
        color: rgba(255,243,222,0.9) !important;
        font-size: 0.88rem !important;
    }}
    div[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        background: rgba(255,255,255,0.08);
        border-radius: 6px;
    }}
    
    /* === PAGE HEADER === */
    .page-header {{
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: 700;
        color: {PRIMARY};
        margin-bottom: 0.15rem;
        line-height: 1.15;
        letter-spacing: -0.02em;
    }}
    .page-subtitle {{
        font-family: 'Roboto', sans-serif;
        font-size: 0.9rem;
        color: {GRAY_500};
        margin-top: 0;
        margin-bottom: 1.2rem;
        font-weight: 400;
    }}
    
    /* === KPI CARDS === */
    .kpi-row {{
        display: flex;
        gap: 16px;
        margin-bottom: 1.5rem;
    }}
    .kpi-card {{
        background: {SURFACE};
        border: 1px solid rgba(44,61,91,0.15);
        border-left: 4px solid {PRIMARY};
        border-radius: 8px;
        padding: 1.1rem 1.2rem;
        flex: 1;
        min-width: 0;
    }}
    .kpi-card .kpi-icon {{
        width: 36px;
        height: 36px;
        background: {PRIMARY};
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.6rem;
    }}
    .kpi-card .kpi-icon svg {{
        width: 18px;
        height: 18px;
        stroke: {GOLD};
        fill: none;
    }}
    .kpi-card .kpi-label {{
        font-family: 'Roboto', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: {GRAY_500};
        margin-bottom: 0.25rem;
    }}
    .kpi-card .kpi-value {{
        font-family: 'Roboto', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: {PRIMARY};
        line-height: 1.2;
    }}
    .kpi-card .kpi-delta {{
        font-size: 0.72rem;
        margin-top: 0.3rem;
        font-weight: 500;
    }}
    .kpi-card .kpi-delta.positive {{ color: {SUCCESS}; }}
    .kpi-card .kpi-delta.negative {{ color: {ERROR}; }}
    .kpi-card .kpi-delta.neutral {{ color: {GRAY_500}; }}
    
    /* === SECTION CARDS === */
    .section-card {{
        background: {WHITE};
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }}
    .section-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #F3F4F6;
    }}
    .section-card-title {{
        font-family: 'Playfair Display', serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: {PRIMARY};
        margin: 0;
    }}
    
    /* === TABLES === */
    .stDataFrame thead tr th {{
        background-color: {PRIMARY} !important;
        color: {WHITE} !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    .stDataFrame tbody tr:nth-child(even) {{
        background-color: {SURFACE} !important;
    }}
    
    /* === FOOTER === */
    .t2-footer {{
        text-align: center;
        padding: 1.5rem 0 1rem 0;
        margin-top: 3rem;
        border-top: 2px solid {GOLD_MUTED};
    }}
    .t2-footer-text {{
        font-family: 'Roboto', sans-serif;
        font-size: 0.72rem;
        color: {GRAY_500};
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}
    
    /* === CAPTIONS === */
    .fonte-caption {{
        font-size: 0.7rem;
        color: #9CA3AF;
        margin-top: 0.3rem;
        font-style: italic;
    }}
    
    /* === DIVIDERS === */
    .gold-divider {{
        border: none;
        border-top: 1px solid {GOLD_MUTED};
        margin: 1.5rem 0;
        opacity: 0.4;
    }}
    .subtle-divider {{
        border: none;
        border-top: 1px solid #F3F4F6;
        margin: 1.2rem 0;
    }}
    
    /* === METRIC OVERRIDE (Streamlit native) === */
    .stMetric > div {{
        background-color: {SURFACE};
        padding: 0.9rem 1rem;
        border-radius: 8px;
        border-left: 4px solid {PRIMARY};
    }}
    .stMetric label {{
        font-family: 'Roboto', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {GRAY_500} !important;
    }}
    .stMetric [data-testid="stMetricValue"] {{
        font-family: 'Roboto', sans-serif !important;
        font-weight: 700 !important;
        color: {PRIMARY} !important;
    }}
    
    /* === SELECTBOX === */
    .stSelectbox label {{
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {GRAY_500} !important;
    }}
    
    /* === DOWNLOAD BUTTON === */
    .stDownloadButton button {{
        background-color: {PRIMARY} !important;
        color: {WHITE} !important;
        border: none !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
    }}
    .stDownloadButton button:hover {{
        background-color: {PRIMARY_LIGHT} !important;
    }}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER: KPI CARD HTML
# =========================================================
def kpi_card(label, value, icon_svg="", delta="", delta_type="neutral"):
    """Gera HTML de um KPI card no padrão DS Tallent Two."""
    delta_html = ""
    if delta:
        delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>'
    
    icon_html = ""
    if icon_svg:
        icon_html = f'<div class="kpi-icon"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icon_svg}</svg></div>'
    
    return f"""
    <div class="kpi-card">
        {icon_html}
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def render_kpis(kpis_list):
    """Renderiza uma row de KPIs usando components.html para evitar sanitizacao de SVG."""
    cards_html = "".join([kpi_card(k[0], k[1], k[2] if len(k) > 2 else "", k[3] if len(k) > 3 else "", k[4] if len(k) > 4 else "neutral") for k in kpis_list])
    
    full_html = f"""
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Roboto', sans-serif; background: transparent; }}
        .kpi-row {{ display: flex; gap: 16px; margin: 0; }}
        .kpi-card {{ background: {SURFACE}; border: 1px solid rgba(44,61,91,0.15); border-left: 4px solid {PRIMARY}; border-radius: 8px; padding: 1.1rem 1.2rem; flex: 1; min-width: 0; }}
        .kpi-card .kpi-icon {{ width: 36px; height: 36px; background: {PRIMARY}; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.6rem; }}
        .kpi-card .kpi-icon svg {{ width: 18px; height: 18px; stroke: {GOLD}; fill: none; }}
        .kpi-card .kpi-label {{ font-size: 0.72rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; color: {GRAY_500}; margin-bottom: 0.25rem; }}
        .kpi-card .kpi-value {{ font-size: 1.5rem; font-weight: 700; color: {PRIMARY}; line-height: 1.2; }}
        .kpi-card .kpi-delta {{ font-size: 0.72rem; margin-top: 0.3rem; font-weight: 500; }}
        .kpi-card .kpi-delta.positive {{ color: {SUCCESS}; }}
        .kpi-card .kpi-delta.negative {{ color: {ERROR}; }}
        .kpi-card .kpi-delta.neutral {{ color: {GRAY_500}; }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <div class="kpi-row">{cards_html}</div>
    """
    n_cards = len(kpis_list)
    height = 140 if n_cards <= 4 else 150
    components.html(full_html, height=height)


# SVG Icons
ICON_USERS = '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
ICON_MONEY = '<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'
ICON_CHART = '<path d="M18 20V10M12 20V4M6 20v-6"/>'
ICON_SHIELD = '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
ICON_MAP = '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>'
ICON_LAYERS = '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>'
ICON_TARGET = '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>'
ICON_TRENDING = '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>'


# =========================================================
# DATA LAYER
# =========================================================
@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data
def load_operadoras_data():
    con = get_connection()
    df_sinist = con.execute("""
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
    return df_sinist


@st.cache_data
def load_beneficiarios():
    con = get_connection()
    df_benef = con.execute("""
        SELECT registro_ans, tipo_contratacao, cobertura, mes_competencia, total_beneficiarios
        FROM sib_operadoras
        ORDER BY mes_competencia
    """).df()
    return df_benef


@st.cache_data
def load_produtos_proxy():
    con = get_connection()
    try:
        df = con.execute("SELECT * FROM resultado_proxy").df()
        return df
    except:
        return pd.DataFrame()


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    # Logo
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200)
    
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-family:Playfair Display,serif; font-size:1.1rem; font-weight:700; color:#FFFFFF; margin:0; line-height:1.3;">Motor de Sinistralidade</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.78rem; color:rgba(255,243,222,0.7); margin:0 0 1rem 0;">Precificação via dados abertos ANS</p>', unsafe_allow_html=True)
    
    st.markdown(f'<hr style="border:none; border-top:1px solid rgba(201,162,39,0.3); margin:0.5rem 0 1rem 0;">', unsafe_allow_html=True)
    
    # Navegação
    pagina = st.radio(
        "Navegação",
        ["Visão Geral", "Análise por Operadora", "Proxy por Produto", "Granularidade", "Score de Risco", "Série Temporal", "Benchmark IESS", "Metodologia"],
        label_visibility="collapsed"
    )
    
    st.markdown(f'<hr style="border:none; border-top:1px solid rgba(201,162,39,0.3); margin:1rem 0 0.8rem 0;">', unsafe_allow_html=True)
    
    # Fontes de dados
    st.markdown('<p style="font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(168,184,208,0.7); margin-bottom:0.5rem;">Fontes de Dados</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.78rem; color:#A8B8D0; margin:0.2rem 0;">DIOPS 4T/2025</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.78rem; color:#A8B8D0; margin:0.2rem 0;">SIB Individualizado Mar/2026</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.78rem; color:#A8B8D0; margin:0.2rem 0;">Cadastro de Produtos ANS</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.78rem; color:{GOLD_MUTED}; margin:0.4rem 0 0 0; font-weight:500;">696.183 registros granulares</p>', unsafe_allow_html=True)
    
    st.markdown(f'<hr style="border:none; border-top:1px solid rgba(201,162,39,0.3); margin:1rem 0 0.5rem 0;">', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.65rem; color:rgba(125,146,179,0.7); letter-spacing:0.05em;">{APP_VERSION} — Tallent Two Financial Holding</p>', unsafe_allow_html=True)


# =========================================================
# PLOTLY LAYOUT DEFAULTS
# =========================================================
PLOTLY_LAYOUT = dict(
    font=dict(family="Roboto, sans-serif", size=12, color="#374151"),
    margin=dict(l=0, r=0, t=30, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    coloraxis_showscale=False
)


def apply_layout(fig, height=350, show_legend=False):
    """Aplica layout padrão T2 a qualquer gráfico Plotly."""
    layout = {**PLOTLY_LAYOUT, "height": height, "showlegend": show_legend}
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F3F4F6", zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F3F4F6", zeroline=False)
    return fig


def section_header(title, subtitle=""):
    """Renderiza um header de seção no padrão DS."""
    sub_html = f'<span style="font-size:0.8rem; color:{GRAY_500}; font-weight:400;">{subtitle}</span>' if subtitle else ""
    st.markdown(f'<div class="section-card-header"><h3 class="section-card-title">{title}</h3>{sub_html}</div>', unsafe_allow_html=True)


def page_footer():
    """Renderiza o footer institucional."""
    st.markdown(f"""
    <div class="t2-footer">
        <p class="t2-footer-text">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# PÁGINA 1: VISÃO GERAL
# =========================================================
if pagina == "Visão Geral":
    st.markdown('<p class="page-header">Sinistralidade Comparativa</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Operadoras selecionadas — Demonstrações Contábeis DIOPS 4T/2025</p>', unsafe_allow_html=True)
    
    df_ops = load_operadoras_data()
    df_benef = load_beneficiarios()
    
    # KPIs
    receita_total = df_ops['receita'].sum()
    sinist_media = df_ops['despesa'].sum() / df_ops['receita'].sum()
    total_vidas = df_benef[df_benef['mes_competencia'] == df_benef['mes_competencia'].max()]['total_beneficiarios'].sum()
    
    render_kpis([
        ("Operadoras", str(len(df_ops)), ICON_USERS),
        ("Receita Total", f"R$ {receita_total/1e9:.2f} bi", ICON_MONEY),
        ("Sinistralidade Ponderada", f"{sinist_media*100:.1f}%", ICON_CHART, "Alerta > 80%" if sinist_media > 0.8 else "Dentro do esperado", "negative" if sinist_media > 0.8 else "positive"),
        ("Vidas (Último Mês)", f"{total_vidas:,.0f}", ICON_USERS),
    ])
    
    st.markdown('<p class="fonte-caption">Base: 6 operadoras selecionadas. Fonte: DIOPS/ANS e SIB/ANS.</p>', unsafe_allow_html=True)
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
    
    # Gráficos
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        section_header("Sinistralidade por Operadora")
        df_chart = df_ops.copy()
        df_chart['sinistralidade_pct'] = df_chart['sinistralidade'] * 100
        df_chart['nome_display'] = df_chart['nome_operadora'].fillna(df_chart['registro_ans'])
        
        fig = px.bar(
            df_chart.sort_values('sinistralidade_pct', ascending=True),
            x='sinistralidade_pct', y='nome_display', orientation='h',
            color='sinistralidade_pct',
            color_continuous_scale=[[0, SUCCESS], [0.5, WARNING], [1, ERROR]],
            range_color=[60, 90],
            labels={'sinistralidade_pct': 'Sinistralidade (%)', 'nome_display': ''}
        )
        fig = apply_layout(fig, height=320)
        fig.add_vline(x=75, line_dash="dot", line_color="#9CA3AF", 
                      annotation_text="Alerta 75%", annotation_font_size=10, annotation_font_color="#9CA3AF")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<p class="fonte-caption">Linha pontilhada: limiar de alerta setorial (75%).</p>', unsafe_allow_html=True)
    
    with col_right:
        section_header("Receita vs Despesa")
        df_comp = df_chart[['nome_display', 'receita', 'despesa']].copy()
        df_comp['receita_bi'] = df_comp['receita'] / 1e9
        df_comp['despesa_bi'] = df_comp['despesa'] / 1e9
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Receita', y=df_comp['nome_display'], x=df_comp['receita_bi'],
                              orientation='h', marker_color=PRIMARY))
        fig2.add_trace(go.Bar(name='Despesa', y=df_comp['nome_display'], x=df_comp['despesa_bi'],
                              orientation='h', marker_color=ERROR))
        fig2 = apply_layout(fig2, height=320, show_legend=True)
        fig2.update_layout(barmode='group', xaxis_title="R$ bilhões")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
    section_header("Resumo Financeiro", "Dados consolidados do período")
    df_display = df_ops[['registro_ans', 'nome_operadora', 'modalidade', 'receita', 'despesa', 'sinistralidade']].copy()
    df_display.columns = ['Registro ANS', 'Operadora', 'Modalidade', 'Receita', 'Despesa Assistencial', 'Sinistralidade']
    df_display['Receita'] = df_display['Receita'].apply(lambda x: f"R$ {x/1e6:,.1f} M")
    df_display['Despesa Assistencial'] = df_display['Despesa Assistencial'].apply(lambda x: f"R$ {x/1e6:,.1f} M")
    df_display['Sinistralidade'] = df_display['Sinistralidade'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    page_footer()


# =========================================================
# PÁGINA 2: ANÁLISE POR OPERADORA
# =========================================================
elif pagina == "Análise por Operadora":
    st.markdown('<p class="page-header">Análise Individual</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Detalhamento financeiro e de carteira por operadora</p>', unsafe_allow_html=True)
    
    df_ops = load_operadoras_data()
    df_benef = load_beneficiarios()
    
    opcoes = df_ops['nome_operadora'].fillna(df_ops['registro_ans']).tolist()
    registros = df_ops['registro_ans'].tolist()
    
    selected_nome = st.selectbox("Operadora:", opcoes)
    idx = opcoes.index(selected_nome)
    selected_reg = registros[idx]
    
    op_data = df_ops[df_ops['registro_ans'] == selected_reg].iloc[0]
    
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
    
    # KPIs
    sinist_val = op_data['sinistralidade'] * 100
    sinist_status = "negative" if sinist_val > 80 else ("neutral" if sinist_val > 75 else "positive")
    sinist_delta = "Acima de 80%" if sinist_val > 80 else ("Atenção" if sinist_val > 75 else "Saudável")
    
    render_kpis([
        ("Receita (4T/2025)", f"R$ {op_data['receita']/1e6:,.1f} M", ICON_MONEY),
        ("Despesa Assistencial", f"R$ {op_data['despesa']/1e6:,.1f} M", ICON_CHART),
        ("Sinistralidade", f"{sinist_val:.1f}%", ICON_SHIELD, sinist_delta, sinist_status),
    ])
    
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
    
    df_benef_op = df_benef[df_benef['registro_ans'] == selected_reg]
    
    if not df_benef_op.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            section_header("Tipo de Contratação")
            df_contrat = df_benef_op.groupby('tipo_contratacao')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_contrat, values='total_beneficiarios', names='tipo_contratacao',
                        color_discrete_sequence=PIE_COLORS, hole=0.45)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            section_header("Cobertura Assistencial")
            df_cob = df_benef_op.groupby('cobertura')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_cob, values='total_beneficiarios', names='cobertura',
                        color_discrete_sequence=PIE_COLORS, hole=0.45)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # Evolução temporal
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        section_header("Evolução de Beneficiários", "Cobertura médico-hospitalar")
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
        fig = apply_layout(fig, height=240)
        fig.update_layout(xaxis=dict(dtick="M6", tickformat="%b/%Y"))
        fig.update_traces(line=dict(width=2.5), fillcolor=f"rgba(44,61,91,0.08)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<p class="fonte-caption">Meses com dados parciais removidos automaticamente (threshold: 50% da mediana).</p>', unsafe_allow_html=True)
    else:
        st.info("Dados de beneficiários não disponíveis para esta operadora no dataset consolidado.")
    
    page_footer()


# =========================================================
# PÁGINA 3: PROXY POR PRODUTO
# =========================================================
elif pagina == "Proxy por Produto":
    st.markdown('<p class="page-header">Sinistralidade Proxy por Produto</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Estimativa baseada em fatores de ponderação atuarial</p>', unsafe_allow_html=True)
    
    df_proxy = load_produtos_proxy()
    
    if df_proxy.empty:
        st.warning("Dados de proxy não disponíveis. Execute o motor de cálculo primeiro.")
    else:
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            ops_disponiveis = df_proxy['nome_operadora'].unique().tolist()
            selected_op = st.selectbox("Operadora:", ["Todas"] + ops_disponiveis)
        with col2:
            segs_disponiveis = df_proxy['segmentacao'].unique().tolist()
            selected_seg = st.selectbox("Segmentação:", ["Todas"] + segs_disponiveis)
        with col3:
            qualidades = df_proxy['qualidade_proxy'].unique().tolist()
            selected_qual = st.selectbox("Qualidade do Proxy:", ["Todas"] + qualidades)
        
        # Aplicar filtros
        df_filtered = df_proxy.copy()
        if selected_op != "Todas":
            df_filtered = df_filtered[df_filtered['nome_operadora'] == selected_op]
        if selected_seg != "Todas":
            df_filtered = df_filtered[df_filtered['segmentacao'] == selected_seg]
        if selected_qual != "Todas":
            df_filtered = df_filtered[df_filtered['qualidade_proxy'] == selected_qual]
        
        st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
        
        # KPIs
        render_kpis([
            ("Produtos Filtrados", f"{len(df_filtered):,}", ICON_LAYERS),
            ("Sinistralidade Proxy Média", f"{df_filtered['sinistralidade_proxy'].mean()*100:.1f}%", ICON_CHART),
            ("Proxy Mínimo", f"{df_filtered['sinistralidade_proxy'].min()*100:.1f}%", ICON_TRENDING),
            ("Proxy Máximo", f"{df_filtered['sinistralidade_proxy'].max()*100:.1f}%", ICON_TARGET),
        ])
        
        st.markdown('<p class="fonte-caption">KPIs calculados sobre o conjunto filtrado.</p>', unsafe_allow_html=True)
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Gráficos
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            section_header("Distribuição da Sinistralidade Proxy")
            fig = px.histogram(
                df_filtered, x=df_filtered['sinistralidade_proxy'] * 100,
                nbins=25, color='segmentacao',
                labels={'x': 'Sinistralidade Proxy (%)', 'count': 'Produtos'},
                color_discrete_sequence=CHART_COLORS
            )
            fig = apply_layout(fig, height=320, show_legend=True)
            fig.add_vline(x=75, line_dash="dot", line_color="#9CA3AF",
                         annotation_text="75%", annotation_font_size=10, annotation_font_color="#9CA3AF")
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            section_header("Por Tipo de Contratação")
            df_box = df_filtered.copy()
            df_box['sinistralidade_pct'] = df_box['sinistralidade_proxy'] * 100
            fig = px.box(df_box, x='tipo_contratacao', y='sinistralidade_pct',
                        color='tipo_contratacao',
                        labels={'sinistralidade_pct': 'Sinistralidade (%)', 'tipo_contratacao': ''},
                        color_discrete_sequence=CHART_COLORS)
            fig = apply_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabela
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        section_header("Detalhamento por Produto", "Top 50 por sinistralidade")
        df_table = df_filtered[['nome_produto', 'segmentacao', 'tipo_contratacao', 
                                'abrangencia', 'fator_moderador', 'peso_calculado',
                                'sinistralidade_proxy', 'qualidade_proxy']].copy()
        df_table['sinistralidade_proxy'] = df_table['sinistralidade_proxy'].apply(lambda x: f"{x*100:.1f}%")
        df_table['peso_calculado'] = df_table['peso_calculado'].apply(lambda x: f"{x:.3f}")
        df_table.columns = ['Produto', 'Segmentação', 'Contratação', 'Abrangência', 
                           'Moderador', 'Peso Calculado', 'Sinistralidade Proxy', 'Qualidade']
        
        st.dataframe(
            df_table.sort_values('Sinistralidade Proxy', ascending=False).head(50),
            use_container_width=True, hide_index=True
        )
        
        # Download
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar dados filtrados (.csv)", csv, "proxy_produtos.csv", "text/csv")
    
    page_footer()


# =========================================================
# PÁGINA 4: GRANULARIDADE (SPRINT 4)
# =========================================================
elif pagina == "Granularidade":
    st.markdown('<p class="page-header">Granularidade por Produto, Município e Faixa Etária</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">SIB Individualizado — 28 UFs — Competência Mar/2026</p>', unsafe_allow_html=True)
    
    try:
        con = get_connection()
        
        # Filtros
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        ops = con.execute("SELECT DISTINCT razao_social FROM sib_granular ORDER BY razao_social").df()['razao_social'].tolist()
        with col_f1:
            sel_op = st.selectbox("Operadora:", ["Todas"] + ops, key="gran_op")
        
        ufs_list = con.execute("SELECT DISTINCT uf FROM sib_granular ORDER BY uf").df()['uf'].tolist()
        with col_f2:
            sel_uf = st.selectbox("UF:", ["Todas"] + ufs_list, key="gran_uf")
        
        coberturas = con.execute("SELECT DISTINCT cobertura FROM sib_granular ORDER BY cobertura").df()['cobertura'].tolist()
        with col_f3:
            sel_cob = st.selectbox("Cobertura:", ["Todas"] + coberturas, key="gran_cob")
        
        segmentacoes = con.execute("SELECT DISTINCT segmentacao FROM sib_granular WHERE segmentacao IS NOT NULL ORDER BY segmentacao").df()['segmentacao'].tolist()
        with col_f4:
            sel_seg = st.selectbox("Segmentação:", ["Todas"] + segmentacoes, key="gran_seg")
        
        # Construir filtro SQL
        where_clauses = []
        if sel_op != "Todas":
            where_clauses.append(f"razao_social = '{sel_op}'")
        if sel_uf != "Todas":
            where_clauses.append(f"uf = '{sel_uf}'")
        if sel_cob != "Todas":
            where_clauses.append(f"cobertura = '{sel_cob}'")
        if sel_seg != "Todas":
            where_clauses.append(f"segmentacao = '{sel_seg}'")
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
        
        # KPIs
        stats = con.execute(f"""
            SELECT 
                SUM(qt_beneficiario_ativo) as vidas,
                COUNT(DISTINCT cd_plano) as produtos,
                COUNT(DISTINCT municipio) as municipios,
                COUNT(DISTINCT registro_ans) as operadoras,
                COUNT(DISTINCT uf) as ufs
            FROM sib_granular {where_sql}
        """).fetchone()
        
        vidas_fmt = f"{stats[0]/1e6:.2f}M" if stats[0] > 1e6 else f"{stats[0]/1e3:.0f}k"
        
        render_kpis([
            ("Vidas Ativas", vidas_fmt, ICON_USERS),
            ("Produtos", f"{stats[1]:,}", ICON_LAYERS),
            ("Municípios", f"{stats[2]:,}", ICON_MAP),
            ("Operadoras", f"{stats[3]}", ICON_SHIELD),
            ("UFs", f"{stats[4]}", ICON_MAP),
        ])
        
        st.markdown('<p class="fonte-caption">Métricas calculadas sobre o filtro selecionado.</p>', unsafe_allow_html=True)
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Gráficos
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            section_header("Top 15 Municípios por Vidas")
            df_mun = con.execute(f"""
                SELECT municipio || ' (' || uf || ')' as municipio_uf, 
                       SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY municipio, uf
                ORDER BY vidas DESC
                LIMIT 15
            """).df()
            
            fig = px.bar(df_mun, x='vidas', y='municipio_uf', orientation='h',
                        labels={'vidas': 'Vidas Ativas', 'municipio_uf': ''},
                        color_discrete_sequence=[PRIMARY])
            fig = apply_layout(fig, height=380)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            section_header("Distribuição por Faixa Etária")
            df_idade = con.execute(f"""
                SELECT faixa_etaria, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY faixa_etaria
                ORDER BY 
                    CASE 
                        WHEN faixa_etaria LIKE '0%' THEN 1
                        WHEN faixa_etaria LIKE '1 a%' THEN 2
                        WHEN faixa_etaria LIKE '5%' THEN 3
                        WHEN faixa_etaria LIKE '10%' THEN 4
                        WHEN faixa_etaria LIKE '15%' THEN 5
                        WHEN faixa_etaria LIKE '18%' THEN 6
                        WHEN faixa_etaria LIKE '19%' THEN 7
                        WHEN faixa_etaria LIKE '20%' THEN 8
                        WHEN faixa_etaria LIKE '25%' THEN 9
                        WHEN faixa_etaria LIKE '30%' THEN 10
                        WHEN faixa_etaria LIKE '35%' THEN 11
                        WHEN faixa_etaria LIKE '40%' THEN 12
                        WHEN faixa_etaria LIKE '45%' THEN 13
                        WHEN faixa_etaria LIKE '50%' THEN 14
                        WHEN faixa_etaria LIKE '55%' THEN 15
                        WHEN faixa_etaria LIKE '59%' THEN 16
                        ELSE 17
                    END
            """).df()
            
            fig = px.bar(df_idade, x='faixa_etaria', y='vidas',
                        labels={'faixa_etaria': 'Faixa Etária', 'vidas': 'Vidas'},
                        color_discrete_sequence=[PRIMARY_MUTED])
            fig = apply_layout(fig, height=380)
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Heatmap
        section_header("Concentração por UF e Segmentação")
        df_heat = con.execute(f"""
            SELECT uf, segmentacao, SUM(qt_beneficiario_ativo) as vidas
            FROM sib_granular {where_sql}
            WHERE segmentacao IS NOT NULL
            GROUP BY uf, segmentacao
        """).df()
        
        if not df_heat.empty:
            df_pivot = df_heat.pivot_table(index='uf', columns='segmentacao', values='vidas', fill_value=0)
            fig = px.imshow(df_pivot, 
                           labels=dict(x="Segmentação", y="UF", color="Vidas"),
                           color_continuous_scale=[[0, "#F9FAFB"], [0.3, "#A8B8D0"], [0.7, PRIMARY_MUTED], [1, PRIMARY]],
                           aspect="auto")
            fig = apply_layout(fig, height=450)
            fig.update_layout(coloraxis_showscale=True)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Tabela por Produto
        section_header("Detalhamento por Produto", "Top 50 por vidas ativas")
        df_prod = con.execute(f"""
            SELECT 
                cd_plano as "Cod. Plano",
                segmentacao as "Segmentacao",
                tipo_contratacao as "Contratacao",
                abrangencia as "Abrangencia",
                COUNT(DISTINCT municipio) as "Municipios",
                COUNT(DISTINCT uf) as "UFs",
                SUM(qt_beneficiario_ativo) as "Vidas Ativas",
                COUNT(DISTINCT faixa_etaria) as "Faixas Etarias"
            FROM sib_granular {where_sql}
            GROUP BY cd_plano, segmentacao, tipo_contratacao, abrangencia
            ORDER BY "Vidas Ativas" DESC
            LIMIT 50
        """).df()
        
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
        
        # Download
        csv_gran = df_prod.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar tabela (.csv)", csv_gran, "granularidade_produtos.csv", "text/csv")
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Composição
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            section_header("Titular vs Dependente")
            df_vinc = con.execute(f"""
                SELECT tipo_vinculo, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY tipo_vinculo
            """).df()
            fig = px.pie(df_vinc, values='vidas', names='tipo_vinculo',
                        color_discrete_sequence=PIE_COLORS, hole=0.45)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_v2:
            section_header("Tipo de Contratação")
            df_cont = con.execute(f"""
                SELECT tipo_contratacao, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY tipo_contratacao
            """).df()
            fig = px.pie(df_cont, values='vidas', names='tipo_contratacao',
                        color_discrete_sequence=CHART_COLORS, hole=0.45)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar dados granulares: {e}")
    
    page_footer()


# =========================================================
# PÁGINA 5: SCORE DE RISCO (Sprint 5)
# =========================================================
elif pagina == "Score de Risco":
    st.markdown('<p class="page-header">Score de Risco Atuarial</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Sinistralidade estimada por Produto x Município x Faixa Etária (Rateio Financeiro)</p>', unsafe_allow_html=True)
    
    try:
        con = get_connection()
        
        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        
        ops_score = con.execute("SELECT DISTINCT razao_social FROM score_risco_produto_agg ORDER BY razao_social").df()['razao_social'].tolist()
        
        with col_f1:
            op_sel = st.selectbox("Operadora", ["Todas"] + ops_score, key="score_op")
        
        with col_f2:
            seg_opts = con.execute("SELECT DISTINCT segmentacao FROM score_risco_produto_agg WHERE segmentacao IS NOT NULL ORDER BY segmentacao").df()['segmentacao'].tolist()
            seg_sel = st.selectbox("Segmentação", ["Todas"] + seg_opts, key="score_seg")
        
        with col_f3:
            contr_opts = con.execute("SELECT DISTINCT tipo_contratacao FROM score_risco_produto_agg WHERE tipo_contratacao IS NOT NULL ORDER BY tipo_contratacao").df()['tipo_contratacao'].tolist()
            contr_sel = st.selectbox("Contratação", ["Todas"] + contr_opts, key="score_contr")
        
        # Construir filtros SQL
        filters = []
        if op_sel != "Todas":
            filters.append(f"razao_social = '{op_sel}'")
        if seg_sel != "Todas":
            filters.append(f"segmentacao = '{seg_sel}'")
        if contr_sel != "Todas":
            filters.append(f"tipo_contratacao = '{contr_sel}'")
        
        where_score = "WHERE " + " AND ".join(filters) if filters else ""
        
        st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
        
        # KPIs
        kpi_data = con.execute(f"""
            SELECT 
                COUNT(*) as produtos,
                SUM(vidas_total) as vidas,
                SUM(despesa_estimada) as despesa,
                AVG(sinistralidade_estimada) as sinist_media,
                AVG(custo_per_capita_medio) as custo_pc
            FROM score_risco_produto_agg {where_score}
        """).df()
        
        vidas_v = kpi_data['vidas'].iloc[0]
        vidas_fmt = f"{vidas_v/1e6:.2f}M" if vidas_v > 1e6 else f"{vidas_v/1e3:.0f}k"
        desp_v = kpi_data['despesa'].iloc[0]
        sinist_v = kpi_data['sinist_media'].iloc[0] * 100
        custo_v = kpi_data['custo_pc'].iloc[0]
        
        render_kpis([
            ("Produtos", f"{int(kpi_data['produtos'].iloc[0]):,}", ICON_LAYERS),
            ("Vidas", vidas_fmt, ICON_USERS),
            ("Despesa Estimada", f"R$ {desp_v/1e9:.2f}B", ICON_MONEY),
            ("Sinistralidade Média", f"{sinist_v:.1f}%", ICON_CHART, "Acima de 80%" if sinist_v > 80 else "Dentro do esperado", "negative" if sinist_v > 80 else "positive"),
            ("Custo Per Capita/Mês", f"R$ {custo_v:.0f}", ICON_TARGET),
        ])
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Gráfico 1: Custo Per Capita por Operadora
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            section_header("Custo Per Capita por Operadora")
            df_op_custo = con.execute(f"""
                SELECT 
                    CASE 
                        WHEN razao_social LIKE '%PESSOAL%' THEN 'Pessoal Saúde'
                        WHEN razao_social LIKE '%SANTA CASA%' THEN 'Santa Casa Mauá'
                        WHEN razao_social LIKE '%SANTA HELENA%' THEN 'Santa Helena'
                        WHEN razao_social LIKE '%SF SISTEMAS%' THEN 'SF Sistemas'
                        WHEN razao_social LIKE '%NOTRE DAME%' THEN 'Hapvida NDI'
                        ELSE razao_social
                    END as operadora,
                    AVG(custo_per_capita_medio) as custo_pc,
                    SUM(vidas_total) as vidas,
                    AVG(sinistralidade_estimada) as sinist
                FROM score_risco_produto_agg {where_score}
                GROUP BY operadora
                ORDER BY custo_pc DESC
            """).df()
            
            fig = px.bar(df_op_custo, x='operadora', y='custo_pc',
                        color='sinist', color_continuous_scale=[[0, SUCCESS], [0.5, GOLD_MUTED], [1, ERROR]],
                        labels={'operadora': '', 'custo_pc': 'R$/mês', 'sinist': 'Sinistralidade'},
                        text=df_op_custo['custo_pc'].apply(lambda x: f'R$ {x:.0f}'))
            fig = apply_layout(fig, height=380)
            fig.update_traces(textposition='outside')
            fig.update_layout(coloraxis_colorbar=dict(title="Sinist.", tickformat=".0%"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
            section_header("Sinistralidade por Contratação")
            df_contr = con.execute(f"""
                SELECT 
                    tipo_contratacao,
                    AVG(sinistralidade_estimada) as sinist,
                    AVG(custo_per_capita_medio) as custo_pc,
                    SUM(vidas_total) as vidas
                FROM score_risco_produto_agg {where_score}
                GROUP BY tipo_contratacao
                ORDER BY sinist DESC
            """).df()
            
            fig = px.bar(df_contr, x='tipo_contratacao', y='custo_pc',
                        color='sinist', color_continuous_scale=[[0, SUCCESS], [0.5, GOLD_MUTED], [1, ERROR]],
                        labels={'tipo_contratacao': '', 'custo_pc': 'R$/mês', 'sinist': 'Sinistralidade'},
                        text=df_contr['custo_pc'].apply(lambda x: f'R$ {x:.0f}'))
            fig = apply_layout(fig, height=380)
            fig.update_traces(textposition='outside')
            fig.update_layout(coloraxis_colorbar=dict(title="Sinist.", tickformat=".0%"))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Gráfico 2: Mapa de Custo por UF
        section_header("Custo Per Capita por UF", "Fator geográfico baseado em VCMH/IESS")
        
        filters_uf = []
        if op_sel != "Todas":
            filters_uf.append(f"razao_social = '{op_sel}'")
        where_uf = "WHERE " + " AND ".join(filters_uf) if filters_uf else ""
        
        df_uf = con.execute(f"""
            SELECT uf, vidas, sinistralidade_uf as sinist, custo_per_capita, produtos, municipios
            FROM score_risco_uf {where_uf}
            ORDER BY custo_per_capita DESC
        """).df()
        
        if not df_uf.empty:
            fig = px.bar(df_uf, x='uf', y='custo_per_capita',
                        color='custo_per_capita', 
                        color_continuous_scale=[[0, PRIMARY_MUTED], [0.5, GOLD_MUTED], [1, ERROR]],
                        labels={'uf': 'UF', 'custo_per_capita': 'R$/mês'},
                        hover_data=['vidas', 'produtos', 'municipios'],
                        text=df_uf['custo_per_capita'].apply(lambda x: f'R${x:.0f}'))
            fig = apply_layout(fig, height=380)
            fig.update_traces(textposition='outside', textfont_size=9)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('<p class="fonte-caption">Custo per capita mensal estimado por UF. Fatores geográficos: VCMH/IESS e DATASUS/SIH.</p>', unsafe_allow_html=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Tabela de Produtos com Score de Risco
        section_header("Ranking de Produtos por Custo Per Capita", "Maior risco primeiro")
        
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
                ROUND(sinistralidade_estimada * 100, 1) as "Sinist. Estimada (%)",
                ROUND(fator_etario_medio, 2) as "Fator Etário",
                municipios as "Municípios",
                ROUND(despesa_estimada / 1e6, 2) as "Despesa (R$ M)"
            FROM score_risco_produto_agg {where_score}
            ORDER BY custo_per_capita_medio DESC
            LIMIT 100
        """).df()
        
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        
        # Download
        csv_score = df_ranking.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar ranking (.csv)", csv_score, "score_risco_produtos.csv", "text/csv")
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Distribuição do Score
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            section_header("Distribuição de Custo Per Capita")
            df_hist = con.execute(f"""
                SELECT custo_per_capita_medio as custo_pc
                FROM score_risco_produto_agg {where_score}
                WHERE custo_per_capita_medio > 0
            """).df()
            
            fig = px.histogram(df_hist, x='custo_pc', nbins=40,
                              labels={'custo_pc': 'Custo Per Capita (R$/mês)', 'count': 'Produtos'},
                              color_discrete_sequence=[PRIMARY])
            fig = apply_layout(fig, height=320)
            fig.add_vline(x=df_hist['custo_pc'].median(), line_dash="dash", line_color=GOLD_MUTED,
                         annotation_text=f"Mediana: R$ {df_hist['custo_pc'].median():.0f}")
            st.plotly_chart(fig, use_container_width=True)
        
        with col_d2:
            section_header("Fator Etário por Segmentação")
            df_fator = con.execute(f"""
                SELECT segmentacao, AVG(fator_etario_medio) as fator_medio, SUM(vidas_total) as vidas
                FROM score_risco_produto_agg {where_score}
                GROUP BY segmentacao
                ORDER BY fator_medio DESC
            """).df()
            
            fig = px.bar(df_fator, x='segmentacao', y='fator_medio',
                        labels={'segmentacao': '', 'fator_medio': 'Fator Etário Médio'},
                        color_discrete_sequence=[PRIMARY_MUTED],
                        text=df_fator['fator_medio'].apply(lambda x: f'{x:.2f}'))
            fig = apply_layout(fig, height=320)
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{SURFACE}; border-left:4px solid {PRIMARY}; padding:1rem 1.2rem; border-radius:8px; font-size:0.85rem; color:#374151;">
            <strong style="color:{PRIMARY};">Metodologia do Score de Risco</strong><br>
            O rateio distribui a despesa assistencial total (DIOPS) entre produtos proporcionalmente ao score de risco calculado:
            <code style="background:#E5E7EB; padding:2px 6px; border-radius:3px;">Score = Vidas x Fator_Etário x Fator_Geográfico x Fator_Segmentação x Fator_Contratação</code><br>
            <span style="font-size:0.75rem; color:{GRAY_500};">Fontes: RN 63/2003 (curva etária), VCMH/IESS (geográfico), DIOPS 4T/2025 (financeiro), SIB Mar/2026 (beneficiários).</span>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao carregar Score de Risco: {e}")
    
    page_footer()



# =========================================================
# PÁGINA 6: SÉRIE TEMPORAL
# =========================================================
elif pagina == "Série Temporal":
    st.markdown('<p class="page-header">Série Temporal</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Evolução da sinistralidade 2020-2025 — 24 trimestres DIOPS</p>', unsafe_allow_html=True)
    
    try:
        con_st = duckdb.connect(DB_PATH, read_only=True)
        
        # Carregar dados históricos
        df_hist = con_st.execute("""
            SELECT registro_ans, trimestre, receita, despesa, sinistralidade
            FROM sinistralidade_historica
            ORDER BY registro_ans, trimestre
        """).df()
        
        # Mapa de nomes
        nomes_ops = {
            '310239': 'Pessoal Saúde',
            '355097': 'Santa Helena',
            '359017': 'Hapvida NDI',
            '417491': 'Portomed',
            '421197': 'Santa Casa Mauá',
            '422371': 'SF Sistemas'
        }
        df_hist['operadora'] = df_hist['registro_ans'].map(nomes_ops)
        
        # Converter trimestre para ordem cronológica
        def trimestre_to_order(t):
            q = int(t[0])
            y = int(t[2:])
            return y * 4 + q
        
        df_hist['ordem'] = df_hist['trimestre'].apply(trimestre_to_order)
        df_hist = df_hist.sort_values(['registro_ans', 'ordem'])
        
        # Calcular sinistralidade trimestral (delta)
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
                    'registro_ans': reg,
                    'operadora': nomes_ops.get(reg, reg),
                    'trimestre': row['trimestre'],
                    'ordem': row['ordem'],
                    'receita_tri': rec_tri,
                    'despesa_tri': desp_tri,
                    'sinistralidade_tri': sinist_tri
                })
        
        df_tri = pd.DataFrame(records)
        df_tri = df_tri[df_tri['sinistralidade_tri'].notna()]
        df_tri = df_tri[(df_tri['sinistralidade_tri'] > 0) & (df_tri['sinistralidade_tri'] < 2.0)]
        
        # KPIs
        n_ops = df_tri['registro_ans'].nunique()
        n_tri = df_tri['trimestre'].nunique()
        sinist_atual = df_tri[df_tri['trimestre'] == '4T2025']['sinistralidade_tri'].mean()
        sinist_2020 = df_tri[df_tri['trimestre'] == '4T2020']['sinistralidade_tri'].mean()
        variacao = ((sinist_atual / sinist_2020) - 1) * 100 if sinist_2020 and sinist_2020 > 0 else 0
        
        render_kpis([
            ("Operadoras", str(n_ops), ICON_USERS),
            ("Trimestres", str(n_tri), ICON_CHART),
            ("Sinistralidade Média Atual", f"{sinist_atual*100:.1f}%" if sinist_atual else "N/A", ICON_CHART,
             "Alerta > 80%" if sinist_atual and sinist_atual > 0.8 else "Dentro do esperado",
             "negative" if sinist_atual and sinist_atual > 0.8 else "positive"),
            ("Variação 2020-2025", f"{variacao:+.0f}%", ICON_MONEY,
             "Piora" if variacao > 0 else "Melhora",
             "negative" if variacao > 0 else "positive"),
        ])
        
        st.markdown('<p class="fonte-caption">Base: Demonstrações Contábeis DIOPS/ANS. Sinistralidade = Despesa Assistencial (conta 411x) / Receita Total (conta 3). Valores trimestrais (não acumulados).</p>', unsafe_allow_html=True)
        st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
        
        # Filtro de operadora
        ops_disponiveis = sorted(df_tri['operadora'].unique())
        ops_selecionadas = st.multiselect("Operadoras", ops_disponiveis, default=ops_disponiveis, key="st_ops")
        df_filtered = df_tri[df_tri['operadora'].isin(ops_selecionadas)]
        
        # Gráfico 1: Evolução da Sinistralidade
        section_header("Evolução da Sinistralidade Trimestral", "Despesa assistencial / Receita por trimestre isolado")
        
        fig_line = px.line(
            df_filtered.sort_values('ordem'),
            x='trimestre', y='sinistralidade_tri',
            color='operadora',
            markers=True,
            color_discrete_sequence=[PRIMARY, GOLD_MUTED, '#5B8C5A', '#E07A5F', '#3D405B', '#81B29A']
        )
        fig_line.update_yaxes(tickformat='.0%', title=None)
        fig_line.update_xaxes(title=None, tickangle=-45)
        fig_line.add_hline(y=0.80, line_dash="dash", line_color="#EF4444", annotation_text="Alerta 80%")
        fig_line.add_hline(y=0.70, line_dash="dot", line_color="#F59E0B", annotation_text="Referência 70%")
        apply_layout(fig_line, height=400, show_legend=True)
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Gráfico 2: Receita vs Despesa
        col1, col2 = st.columns(2)
        
        with col1:
            section_header("Receita Trimestral", "Evolução por operadora (R$ milhões)")
            df_rec = df_filtered.copy()
            df_rec['receita_M'] = df_rec['receita_tri'] / 1e6
            fig_rec = px.bar(
                df_rec.sort_values('ordem'),
                x='trimestre', y='receita_M',
                color='operadora',
                color_discrete_sequence=[PRIMARY, GOLD_MUTED, '#5B8C5A', '#E07A5F', '#3D405B', '#81B29A']
            )
            fig_rec.update_yaxes(title=None)
            fig_rec.update_xaxes(title=None, tickangle=-45)
            apply_layout(fig_rec, height=300, show_legend=True)
            st.plotly_chart(fig_rec, use_container_width=True)
        
        with col2:
            section_header("Despesa Assistencial Trimestral", "Evolução por operadora (R$ milhões)")
            df_desp = df_filtered.copy()
            df_desp['despesa_M'] = df_desp['despesa_tri'] / 1e6
            fig_desp = px.bar(
                df_desp.sort_values('ordem'),
                x='trimestre', y='despesa_M',
                color='operadora',
                color_discrete_sequence=[PRIMARY, GOLD_MUTED, '#5B8C5A', '#E07A5F', '#3D405B', '#81B29A']
            )
            fig_desp.update_yaxes(title=None)
            fig_desp.update_xaxes(title=None, tickangle=-45)
            apply_layout(fig_desp, height=300, show_legend=True)
            st.plotly_chart(fig_desp, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Gráfico 3: Comparação Anual
        section_header("Sinistralidade Anual (Acumulada)", "Valores do 4T de cada ano")
        
        df_anual = df_hist[df_hist['trimestre'].str.startswith('4T')].copy()
        df_anual['ano'] = df_anual['trimestre'].str[2:]
        df_anual['sinist_pct'] = df_anual['sinistralidade'] * 100
        
        fig_anual = px.bar(
            df_anual,
            x='ano', y='sinist_pct',
            color='operadora',
            barmode='group',
            color_discrete_sequence=[PRIMARY, GOLD_MUTED, '#5B8C5A', '#E07A5F', '#3D405B', '#81B29A']
        )
        fig_anual.update_yaxes(title=None, ticksuffix='%')
        fig_anual.update_xaxes(title=None)
        fig_anual.add_hline(y=80, line_dash="dash", line_color="#EF4444", annotation_text="Alerta 80%")
        apply_layout(fig_anual, height=350, show_legend=True)
        st.plotly_chart(fig_anual, use_container_width=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        
        # Tabela de tendências
        section_header("Indicadores de Tendência", "CAGR de receita e variação de sinistralidade")
        
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
                    'Receita Inicial (R$M)': f"{rec_ini/1e6:.0f}",
                    'Receita Atual (R$M)': f"{rec_fin/1e6:.0f}",
                    'CAGR Receita': f"{cagr_rec:.1f}%",
                    'Sinist. Inicial': f"{sin_ini:.1f}%",
                    'Sinist. Atual': f"{sin_fin:.1f}%",
                    'Delta': f"{delta_sin:+.1f} pp",
                    'Tendência': 'Piora' if delta_sin > 3 else ('Melhora' if delta_sin < -3 else 'Estável')
                })
        
        df_tend = pd.DataFrame(tendencias)
        st.dataframe(df_tend, use_container_width=True, hide_index=True)
        
        st.markdown('<p class="fonte-caption">CAGR calculado sobre receita acumulada anual (4T). Delta Sinistralidade = diferença em pontos percentuais entre 4T2025 e primeiro 4T disponível. Fonte: DIOPS/ANS.</p>', unsafe_allow_html=True)
        
        # Download
        csv_data = df_tri.to_csv(index=False)
        st.download_button("Download Série Temporal (CSV)", csv_data, "serie_temporal_sinistralidade.csv", "text/csv")
        
        con_st.close()
    except Exception as e:
        st.error(f"Erro ao carregar Série Temporal: {e}")
    
    page_footer()



# =========================================================
# PÁGINA 7: METODOLOGIA
# =========================================================

elif pagina == "Benchmark IESS":
    st.markdown('<p class="page-header">Benchmark de Mercado</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Comparação com indicadores IESS, ANS e UNIDAS 2024</p>', unsafe_allow_html=True)
    
    try:
        con_b = duckdb.connect(DB_PATH, read_only=True)
        
        # KPIs de Benchmark
        benchmark_data = con_b.execute("""
            SELECT 
                nome_operadora,
                tipo_operadora,
                ROUND(sinistralidade_operadora, 1) AS sinist_real,
                ROUND(benchmark_sinistralidade, 1) AS benchmark,
                ROUND(delta_vs_benchmark, 1) AS delta,
                classificacao_benchmark,
                SUM(total_vidas) AS vidas,
                ROUND(AVG(custo_percapita_mensal), 0) AS custo_pc
            FROM resultado_benchmark
            WHERE nome_operadora IS NOT NULL
            GROUP BY nome_operadora, tipo_operadora, sinistralidade_operadora, 
                     benchmark_sinistralidade, delta_vs_benchmark, classificacao_benchmark
            ORDER BY delta_vs_benchmark
        """).fetchdf()
        
        # Mercado referência
        sinist_mercado = 82.2
        
        n_eficientes = len(benchmark_data[benchmark_data['delta'] < -5])
        n_pressao = len(benchmark_data[benchmark_data['delta'] > 5])
        custo_medio = benchmark_data['custo_pc'].mean()
        
        kpis_bench = [
            {"icon": ICON_CHART, "label": "Sinistralidade Mercado", "value": f"{sinist_mercado}%", "delta": "4T/2024 ANS"},
            {"icon": ICON_MONEY, "label": "Custo Per Capita Médio", "value": f"R$ {custo_medio:,.0f}/mês"},
            {"icon": ICON_CHECK, "label": "Abaixo do Benchmark", "value": f"{n_eficientes} operadoras", "delta": "Eficientes", "positive": True},
            {"icon": ICON_ALERT, "label": "Acima do Benchmark", "value": f"{n_pressao} operadoras", "delta": "Pressão", "positive": False},
        ]
        render_kpis(kpis_bench)
        
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        
        # Gráfico: Operadoras vs Benchmark
        section_header("Sinistralidade Real vs Benchmark de Mercado", "Comparação com referência por tipo de operadora")
        
        import plotly.graph_objects as go
        
        fig_bench = go.Figure()
        
        # Barras de sinistralidade real
        fig_bench.add_trace(go.Bar(
            x=benchmark_data['nome_operadora'],
            y=benchmark_data['sinist_real'],
            name='Sinistralidade Real',
            marker_color=PRIMARY,
            text=benchmark_data['sinist_real'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ))
        
        # Barras de benchmark
        fig_bench.add_trace(go.Bar(
            x=benchmark_data['nome_operadora'],
            y=benchmark_data['benchmark'],
            name='Benchmark (Tipo)',
            marker_color=GOLD,
            text=benchmark_data['benchmark'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ))
        
        # Linha de mercado
        fig_bench.add_hline(y=sinist_mercado, line_dash="dash", line_color="#E53E3E",
                           annotation_text=f"Mercado Total: {sinist_mercado}%")
        
        fig_bench.update_layout(
            barmode='group',
            yaxis_title="Sinistralidade (%)",
            yaxis_range=[0, 100],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            **apply_layout()
        )
        st.plotly_chart(fig_bench, use_container_width=True)
        
        st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)
        
        # Tabela de classificação
        section_header("Classificação vs Benchmark", "Delta em pontos percentuais em relação à referência do tipo")
        
        col_bench1, col_bench2 = st.columns([3, 2])
        
        with col_bench1:
            display_df = benchmark_data[['nome_operadora', 'tipo_operadora', 'sinist_real', 'benchmark', 'delta', 'classificacao_benchmark', 'vidas']].copy()
            display_df.columns = ['Operadora', 'Tipo', 'Sinistralidade', 'Benchmark', 'Delta (pp)', 'Classificação', 'Vidas']
            display_df['Sinistralidade'] = display_df['Sinistralidade'].apply(lambda x: f'{x:.1f}%')
            display_df['Benchmark'] = display_df['Benchmark'].apply(lambda x: f'{x:.1f}%')
            display_df['Delta (pp)'] = display_df['Delta (pp)'].apply(lambda x: f'{x:+.1f}')
            display_df['Vidas'] = display_df['Vidas'].apply(lambda x: f'{x:,.0f}')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        with col_bench2:
            # Pie chart de classificação
            class_counts = benchmark_data['classificacao_benchmark'].value_counts()
            fig_class = go.Figure(data=[go.Pie(
                labels=class_counts.index,
                values=class_counts.values,
                hole=0.4,
                marker_colors=[PRIMARY, GOLD, '#E53E3E'][:len(class_counts)]
            )])
            fig_class.update_layout(
                title="Distribuição por Classificação",
                **apply_layout()
            )
            st.plotly_chart(fig_class, use_container_width=True)
        
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        
        # VCMH Histórica
        section_header("VCMH/IESS — Inflação Médica Histórica", "Variação de Custos Médico-Hospitalares (fonte: IESS)")
        
        vcmh_data = con_b.execute("""
            SELECT categoria AS ano, valor AS vcmh 
            FROM benchmark_mercado 
            WHERE indicador = 'vcmh_anual'
            ORDER BY categoria
        """).fetchdf()
        
        if not vcmh_data.empty:
            fig_vcmh = go.Figure()
            fig_vcmh.add_trace(go.Scatter(
                x=vcmh_data['ano'],
                y=vcmh_data['vcmh'],
                mode='lines+markers+text',
                text=vcmh_data['vcmh'].apply(lambda x: f'{x:.1f}%'),
                textposition='top center',
                line=dict(color=PRIMARY, width=3),
                marker=dict(size=10, color=GOLD)
            ))
            fig_vcmh.add_hline(y=0, line_dash="dot", line_color="#999")
            fig_vcmh.update_layout(
                yaxis_title="VCMH (%)",
                xaxis_title="Ano",
                **apply_layout()
            )
            st.plotly_chart(fig_vcmh, use_container_width=True)
        
        st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)
        
        # Composição da Despesa Assistencial
        section_header("Composição da Despesa Assistencial", "Peso de cada item na despesa total (fonte: IESS Set/2023)")
        
        comp_data = con_b.execute("""
            SELECT categoria, valor 
            FROM benchmark_mercado 
            WHERE indicador = 'composicao_despesa'
            ORDER BY valor DESC
        """).fetchdf()
        
        if not comp_data.empty:
            fig_comp = go.Figure(data=[go.Pie(
                labels=comp_data['categoria'].str.capitalize(),
                values=comp_data['valor'],
                hole=0.4,
                marker_colors=[PRIMARY, '#4A6FA5', GOLD, '#C9A227', SURFACE]
            )])
            fig_comp.update_layout(
                title="Composição da Despesa (IESS Set/2023)",
                **apply_layout()
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        
        # Top Produtos mais caros vs benchmark
        section_header("Top 20 Produtos por Custo Per Capita", "Produtos com maior custo estimado mensal por beneficiário")
        
        top_prods = con_b.execute("""
            SELECT 
                nome_operadora AS "Operadora",
                uf AS "UF",
                cd_plano AS "Produto",
                tipo_contratacao AS "Contratação",
                total_vidas AS "Vidas",
                ROUND(custo_percapita_mensal, 2) AS "Custo/Mês (R$)",
                ROUND(fator_etario_medio, 2) AS "Fator Etário",
                ROUND(fator_geografico_medio, 2) AS "Fator Geográfico"
            FROM resultado_benchmark
            WHERE custo_percapita_mensal > 0 AND total_vidas >= 50
            ORDER BY custo_percapita_mensal DESC
            LIMIT 20
        """).fetchdf()
        
        if not top_prods.empty:
            top_prods['Custo/Mês (R$)'] = top_prods['Custo/Mês (R$)'].apply(lambda x: f'R$ {x:,.2f}')
            top_prods['Vidas'] = top_prods['Vidas'].apply(lambda x: f'{x:,.0f}')
            st.dataframe(top_prods, use_container_width=True, hide_index=True)
            
            csv_bench = top_prods.to_csv(index=False).encode('utf-8')
            st.download_button("Download Top Produtos (CSV)", csv_bench, "top_produtos_custo.csv", "text/csv")
        
        # Fontes
        st.markdown(f"""
        <div style="margin-top:2rem; padding:1rem; background:{SURFACE}; border-radius:4px;">
            <strong style="color:{PRIMARY};">Fontes de Benchmark</strong><br>
            <span style="font-size:0.85rem; color:#666;">
            • VCMH/IESS — Variação de Custos Médico-Hospitalares (Edição Abril/2026, data-base Set/2023)<br>
            • Panorama ANS — Saúde Suplementar, 8ª Edição (Mar/2025)<br>
            • Pesquisa Nacional UNIDAS 2023 — Custo assistencial per capita por região<br>
            • ANS Dados Econômico-Financeiros 2024 — Sinistralidade 4T/2024: 82.2%<br>
            • Fatores geográficos calibrados com despesa per capita regional (IESS + ANS)
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        con_b.close()
        
    except Exception as e:
        st.error(f"Erro ao carregar Benchmark: {e}")
        import traceback
        st.code(traceback.format_exc())


elif pagina == "Metodologia":
    st.markdown('<p class="page-header">Metodologia</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Modelo de cálculo, fontes de dados e limitações conhecidas</p>', unsafe_allow_html=True)
    
    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
    
    st.markdown(f"""
<div style="background:{SURFACE}; border-radius:12px; padding:1.5rem; margin-bottom:1.5rem; border:1px solid rgba(44,61,91,0.1);">
    <h3 style="font-family:Playfair Display,serif; color:{PRIMARY}; margin:0 0 0.5rem 0; font-size:1.2rem;">Objetivo</h3>
    <p style="font-family:Roboto,sans-serif; color:#374151; font-size:0.9rem; margin:0; line-height:1.6;">
        Estimar a sinistralidade por produto a partir de dados públicos da ANS, distribuindo a despesa 
        assistencial total da operadora (DIOPS) entre seus produtos cadastrados, proporcionalmente a 
        fatores de risco conhecidos.
    </p>
</div>
""", unsafe_allow_html=True)
    
    st.markdown(f"""
<div style="background:{WHITE}; border:1px solid #E5E7EB; border-radius:12px; padding:1.5rem; margin-bottom:1.5rem;">
    <h3 style="font-family:Playfair Display,serif; color:{PRIMARY}; margin:0 0 0.8rem 0; font-size:1.1rem;">Modelo de Cálculo</h3>
    <div style="background:#F9FAFB; border-radius:8px; padding:1rem; font-family:monospace; font-size:0.85rem; color:{PRIMARY}; margin-bottom:0.8rem;">
        Sinistralidade_Estimada(produto) = Sinistralidade_Total(operadora) x Peso_Relativo(produto)
    </div>
    <div style="background:#F9FAFB; border-radius:8px; padding:1rem; font-family:monospace; font-size:0.85rem; color:{PRIMARY};">
        Peso_Relativo = F_Segmentação x F_Contratação x F_Geográfico x F_Etário x F_Moderador
    </div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
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
    
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
    
    section_header("Classificação de Qualidade")
    st.markdown("""
| Qualidade | Margem de Erro | Critério |
|---|---|---|
| Alta | ±8% | 3+ fatores conhecidos e dados de beneficiários disponíveis |
| Média | ±15% | 2+ fatores conhecidos |
| Baixa | ±25% | Menos de 2 fatores disponíveis |
""")
    
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
    
    section_header("Limitações Conhecidas")
    st.markdown(f"""
<div style="background:{SURFACE}; border-radius:8px; padding:1rem; font-size:0.85rem; line-height:1.8;">
    <strong>1. Viés de Mix de Carteira</strong> — Produtos deficitários podem ser subsidiados por rentáveis dentro da mesma operadora<br>
    <strong>2. Ausência de NTRP</strong> — Sem acesso às premissas atuariais reais transmitidas à ANS<br>
    <strong>3. Defasagem Temporal</strong> — DIOPS trimestral vs SIB mensal podem ter defasagens de até 3 meses<br>
    <strong>4. Dados Agregados</strong> — O DIOPS não discrimina despesa por produto, apenas por operadora<br>
    <strong>5. Fatores Fixos</strong> — Os pesos de segmentação e contratação são baseados em literatura, não calibrados por operadora
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
    
    section_header("Fontes de Dados")
    st.markdown("""
| Fonte | Período | Frequência |
|---|---|---|
| DIOPS (Demonstrações Contábeis) | 4T/2025 | Trimestral |
| SIB Individualizado (Beneficiários) | Mar/2026 | Mensal |
| Cadastro de Produtos ANS | Mai/2026 | Contínua |
| Cadastro de Operadoras (CADOP) | Mai/2026 | Contínua |
""")
    
    st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
    
    section_header("Roadmap de Evolução")
    st.markdown(f"""
| Sprint | Entrega | Status |
|---|---|---|
| 1 | Sinistralidade por operadora (DIOPS + SIB consolidado) | Concluído |
| 2 | Motor de proxy por produto (fatores de ponderação) | Concluído |
| 3 | Prova de conceito de granularidade (SIB individualizado) | Concluído |
| 4 | Ingestão completa do SIB individualizado — 696k registros | Concluído |
| 5 | Score de risco por produto e município (alocação atuarial) | Concluído |
| 6 | Série temporal (DIOPS 2020-2025) e tendências | Planejado |
| 7 | Modelo preditivo XGBoost | Futuro |
| 8 | API REST e interface de consulta | Futuro |
""")
    
    page_footer()
