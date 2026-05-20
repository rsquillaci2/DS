"""
Motor de Sinistralidade ANS
Plataforma de Inteligência Analítica — Tallent Two Financial Holding
v3.0 — Refatoração para Escala (Sprint 8.1)
"""
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import numpy as np
import streamlit.components.v1 as components

# =========================================================
# CONFIGURAÇÃO
# =========================================================
APP_VERSION = "v3.0"
DB_PATH = "/home/ubuntu/mvp_sinistralidade/data/ans_analytics.duckdb"
LOGO_PATH = "/home/ubuntu/mvp_sinistralidade/logo_t2_sidebar.png"
OPERADORAS_CSV = "/home/ubuntu/mvp_sinistralidade/operadoras_ativas.csv"
TOP_N = 10  # Quantidade padrão para rankings

st.set_page_config(
    page_title="Motor de Sinistralidade — Tallent Two",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PALETA — EXECUTIVO FINANCEIRO
# =========================================================
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
    
    /* === HEADER === */
    .exec-header {{
        margin-bottom: 1.5rem;
    }}
    .exec-header .product-name {{
        font-family: 'Inter', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.02em;
    }}
    .exec-header .product-subtitle {{
        font-size: 0.85rem;
        color: {TEXT_SECONDARY};
        margin: 0 0 0.8rem 0;
        font-weight: 400;
    }}
    .data-badge {{
        display: inline-block;
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 0.3rem 0.7rem;
        font-size: 0.7rem;
        color: {TEXT_MUTED};
        font-weight: 500;
        letter-spacing: 0.02em;
    }}
    
    /* === SECTION TITLES === */
    .section-title {{
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: {TEXT_PRIMARY};
        margin: 1.5rem 0 0.3rem 0;
        letter-spacing: -0.01em;
    }}
    .section-subtitle {{
        font-size: 0.75rem;
        color: {TEXT_MUTED};
        margin: 0 0 1rem 0;
        font-weight: 400;
    }}
    
    /* === TABLES === */
    .stDataFrame {{
        font-size: 0.82rem;
    }}
    
    /* === FOOTER === */
    .t2-footer {{
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
    
    /* === TEXT INPUT SEARCH === */
    .stTextInput label {{
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {TEXT_MUTED} !important;
        font-weight: 500 !important;
    }}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def render_kpis(kpis_list):
    """Renderiza KPIs como blocos de decisão executivos."""
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
    """Layout de gráfico executivo."""
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


def format_reais(value):
    """Formata valores monetários de forma legível."""
    if value is None or pd.isna(value):
        return "N/A"
    if abs(value) >= 1e9:
        return f"R$ {value/1e9:.1f} bi"
    elif abs(value) >= 1e6:
        return f"R$ {value/1e6:.0f} M"
    elif abs(value) >= 1e3:
        return f"R$ {value/1e3:.0f} k"
    return f"R$ {value:.0f}"


# =========================================================
# DATA LAYER — RESOLUÇÃO DINÂMICA DE NOMES
# =========================================================
@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data
def load_operadoras_cadastro():
    """Carrega cadastro completo de operadoras para resolução de nomes."""
    con = get_connection()
    df = con.execute(f"""
        SELECT 
            REGISTRO_OPERADORA as registro_ans,
            COALESCE(NULLIF(Nome_Fantasia, ''), Razao_Social) as nome,
            Razao_Social as razao_social,
            Modalidade as modalidade
        FROM read_csv_auto('{OPERADORAS_CSV}', delim=';', header=true)
    """).df()
    return df


@st.cache_data
def get_nome_operadora(registro_ans):
    """Resolve nome de exibição de uma operadora pelo registro ANS."""
    cadastro = load_operadoras_cadastro()
    match = cadastro[cadastro['registro_ans'] == str(registro_ans)]
    if not match.empty:
        return match.iloc[0]['nome']
    return str(registro_ans)


@st.cache_data
def load_operadoras_data():
    """Carrega dados financeiros de todas as operadoras com resolução dinâmica de nomes."""
    con = get_connection()
    df = con.execute(f"""
        SELECT 
            CAST(s.registro_ans AS VARCHAR) as registro_ans,
            COALESCE(NULLIF(o.Nome_Fantasia, ''), o.Razao_Social, CAST(s.registro_ans AS VARCHAR)) as nome_operadora,
            o.Modalidade as modalidade,
            s.receita_contraprestacoes as receita,
            s.despesa_assistencial as despesa,
            s.sinistralidade_total as sinistralidade
        FROM sinistralidade_operadora s
        LEFT JOIN read_csv_auto('{OPERADORAS_CSV}', delim=';', header=true) o
        ON CAST(s.registro_ans AS VARCHAR) = o.REGISTRO_OPERADORA
        WHERE s.sinistralidade_total IS NOT NULL
        ORDER BY s.receita_contraprestacoes DESC
    """).df()
    return df


@st.cache_data
def load_beneficiarios():
    con = get_connection()
    return con.execute("""
        SELECT registro_ans, tipo_contratacao, cobertura, mes_competencia, total_beneficiarios
        FROM sib_operadoras
        ORDER BY mes_competencia
    """).df()


@st.cache_data
def load_score_risco():
    con = get_connection()
    return con.execute("SELECT * FROM score_risco_produto_agg").df()


# =========================================================
# SIDEBAR — NAVEGAÇÃO
# =========================================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=180)
    
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:1.05rem; font-weight:700; color:{TEXT_PRIMARY}; margin:0; line-height:1.3;">Motor de Sinistralidade</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.75rem; color:{TEXT_MUTED}; margin:0.2rem 0 1.2rem 0;">Inteligência analítica para saúde suplementar</p>', unsafe_allow_html=True)
    
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:0 0 1rem 0;">', unsafe_allow_html=True)
    
    pagina = st.radio(
        "Navegação",
        ["Resumo Executivo", "Operadoras", "Produtos e Proxy", "Tendência e Benchmark", "Predição (ML)", "Metodologia"],
        label_visibility="collapsed"
    )
    
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:1.2rem 0 0.8rem 0;">', unsafe_allow_html=True)
    
    # Fontes dinâmicas
    df_ops_sidebar = load_operadoras_data()
    n_ops = len(df_ops_sidebar)
    st.markdown(f'<p style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; color:{TEXT_MUTED}; margin-bottom:0.4rem; font-weight:500;">Fontes de Dados</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0.15rem 0;">DIOPS 4T/2025</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0.15rem 0;">SIB Individualizado Mar/2026</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{TEXT_SECONDARY}; margin:0.15rem 0;">Cadastro de Produtos ANS</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.72rem; color:{PRIMARY}; margin:0.5rem 0 0 0; font-weight:600;">{n_ops} operadoras · 696.183 registros granulares</p>', unsafe_allow_html=True)
    
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:1rem 0 0.5rem 0;">', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.62rem; color:{TEXT_MUTED}; letter-spacing:0.04em;">{APP_VERSION} — Tallent Two Financial Holding</p>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 1: RESUMO EXECUTIVO
# =========================================================
if pagina == "Resumo Executivo":
    df_ops = load_operadoras_data()
    n_operadoras = len(df_ops)
    receita_total = df_ops['receita'].sum()
    sinist_ponderada = df_ops['despesa'].sum() / df_ops['receita'].sum() if df_ops['receita'].sum() > 0 else 0
    
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Motor de Sinistralidade ANS</p>
        <p class="product-subtitle">Análise comparativa de sinistralidade e precificação por produto via dados abertos</p>
        <span class="data-badge">Competência: DIOPS 4T/2025 · SIB Mar/2026 · {n_operadoras} operadoras</span>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs dinâmicos
    sinist_status = "negative" if sinist_ponderada > 0.80 else ("warning" if sinist_ponderada > 0.75 else "positive")
    sinist_ctx = "Acima de 80%" if sinist_ponderada > 0.80 else ("Zona de atenção" if sinist_ponderada > 0.75 else "Saudável")
    
    render_kpis([
        ("Operadoras Analisadas", str(n_operadoras), "Amostra selecionada"),
        ("Receita Total", format_reais(receita_total), "Contraprestações 4T/2025"),
        ("Sinistralidade Ponderada", f"{sinist_ponderada*100:.1f}%", sinist_ctx, sinist_status),
        ("Vidas na Base", "1,734,056", "Último mês disponível"),
    ])
    
    # --- TOP 10 SINISTRALIDADE (Maiores) ---
    col1, col2 = st.columns(2)
    
    with col1:
        section_header("Top 10 — Maior Sinistralidade", "Operadoras com maior pressão assistencial")
        df_top_sinist = df_ops.nlargest(TOP_N, 'sinistralidade').copy()
        df_top_sinist['sinist_pct'] = df_top_sinist['sinistralidade'] * 100
        
        fig = px.bar(df_top_sinist, x='sinist_pct', y='nome_operadora', orientation='h',
                    color_discrete_sequence=[ERROR],
                    labels={'sinist_pct': 'Sinistralidade (%)', 'nome_operadora': ''},
                    text=df_top_sinist['sinist_pct'].apply(lambda x: f'{x:.1f}%'))
        fig.add_vline(x=80, line_dash="dash", line_color=TEXT_MUTED, annotation_text="Ref. 80%", annotation_font_size=9)
        fig = apply_layout(fig, height=320)
        fig.update_traces(textposition='outside', textfont_size=10)
        fig.update_yaxes(categoryorder='total ascending')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        section_header("Top 10 — Menor Sinistralidade", "Operadoras mais eficientes")
        df_bot_sinist = df_ops.nsmallest(TOP_N, 'sinistralidade').copy()
        df_bot_sinist['sinist_pct'] = df_bot_sinist['sinistralidade'] * 100
        
        fig = px.bar(df_bot_sinist, x='sinist_pct', y='nome_operadora', orientation='h',
                    color_discrete_sequence=[SUCCESS],
                    labels={'sinist_pct': 'Sinistralidade (%)', 'nome_operadora': ''},
                    text=df_bot_sinist['sinist_pct'].apply(lambda x: f'{x:.1f}%'))
        fig.add_vline(x=80, line_dash="dash", line_color=TEXT_MUTED, annotation_text="Ref. 80%", annotation_font_size=9)
        fig = apply_layout(fig, height=320)
        fig.update_traces(textposition='outside', textfont_size=10)
        fig.update_yaxes(categoryorder='total descending')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # --- DISTRIBUIÇÃO DE SINISTRALIDADE ---
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    section_header("Distribuição de Sinistralidade", f"Histograma — {n_operadoras} operadoras na base")
    
    df_ops['sinist_pct'] = df_ops['sinistralidade'] * 100
    fig_hist = px.histogram(df_ops, x='sinist_pct', nbins=20,
                           color_discrete_sequence=[PRIMARY],
                           labels={'sinist_pct': 'Sinistralidade (%)', 'count': 'Operadoras'})
    fig_hist.add_vline(x=80, line_dash="dash", line_color=ERROR, annotation_text="Alerta 80%", annotation_font_size=10)
    fig_hist.add_vline(x=sinist_ponderada*100, line_dash="dot", line_color=GOLD, 
                      annotation_text=f"Média ponderada: {sinist_ponderada*100:.1f}%", annotation_font_size=10)
    fig_hist = apply_layout(fig_hist, height=280)
    st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
    
    # --- TOP 10 RECEITA ---
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    section_header("Top 10 — Maior Receita", "Operadoras por volume de contraprestações")
    
    df_top_rec = df_ops.nlargest(TOP_N, 'receita').copy()
    df_top_rec['receita_bi'] = df_top_rec['receita'] / 1e9
    df_top_rec['despesa_bi'] = df_top_rec['despesa'] / 1e9
    
    fig_rec = go.Figure()
    fig_rec.add_trace(go.Bar(
        x=df_top_rec['nome_operadora'], y=df_top_rec['receita_bi'],
        name='Receita', marker_color=PRIMARY,
        text=df_top_rec['receita'].apply(format_reais), textposition='outside'
    ))
    fig_rec.add_trace(go.Bar(
        x=df_top_rec['nome_operadora'], y=df_top_rec['despesa_bi'],
        name='Despesa', marker_color=GOLD_MUTED,
        text=df_top_rec['despesa'].apply(format_reais), textposition='outside'
    ))
    fig_rec.update_layout(barmode='group', yaxis_title="R$ bilhões")
    fig_rec = apply_layout(fig_rec, height=350, show_legend=True)
    st.plotly_chart(fig_rec, use_container_width=True, config={'displayModeBar': False})
    
    # --- TABELA COMPLETA (paginada) ---
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    with st.expander(f"Tabela Completa — {n_operadoras} operadoras", expanded=False):
        df_display = df_ops[['nome_operadora', 'modalidade', 'receita', 'despesa', 'sinistralidade']].copy()
        df_display.columns = ['Operadora', 'Modalidade', 'Receita (R$)', 'Despesa (R$)', 'Sinistralidade']
        df_display['Receita (R$)'] = df_display['Receita (R$)'].apply(format_reais)
        df_display['Despesa (R$)'] = df_display['Despesa (R$)'].apply(format_reais)
        df_display['Sinistralidade'] = df_display['Sinistralidade'].apply(lambda x: f"{x*100:.1f}%")
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
        
        csv_data = df_ops.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar dados (.csv)", csv_data, "sinistralidade_operadoras.csv", "text/csv")
    
    # Insight
    acima_80 = len(df_ops[df_ops['sinistralidade'] > 0.80])
    pct_acima = acima_80 / n_operadoras * 100 if n_operadoras > 0 else 0
    st.markdown(f"""
    <div class="insight-box">
        <strong>Leitura analítica:</strong> {acima_80} de {n_operadoras} operadoras ({pct_acima:.0f}%) apresentam sinistralidade acima de 80%.
        A sinistralidade ponderada do grupo ({sinist_ponderada*100:.1f}%) {"está acima" if sinist_ponderada > 0.80 else "está dentro"} da referência setorial de 80%.
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # --- FILTROS HIERÁRQUICOS ---
    col_f1, col_f2 = st.columns([1, 2])
    
    with col_f1:
        modalidades = ["Todas"] + sorted(df_ops['modalidade'].dropna().unique().tolist())
        sel_modalidade = st.selectbox("Filtrar por Modalidade:", modalidades, key="op_mod_filter")
    
    # Filtrar operadoras pela modalidade selecionada
    if sel_modalidade != "Todas":
        df_ops_filtered = df_ops[df_ops['modalidade'] == sel_modalidade]
    else:
        df_ops_filtered = df_ops
    
    with col_f2:
        # Selectbox com busca (Streamlit nativo suporta digitação para filtrar)
        opcoes_ops = sorted(df_ops_filtered['nome_operadora'].tolist())
        selected_nome = st.selectbox(
            f"Operadora ({len(opcoes_ops)} disponíveis — digite para buscar):",
            opcoes_ops,
            key="op_select"
        )
    
    # Dados da operadora selecionada
    op_data = df_ops[df_ops['nome_operadora'] == selected_nome].iloc[0]
    selected_reg = op_data['registro_ans']
    
    st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
    
    # KPIs
    sinist_val = op_data['sinistralidade'] * 100
    sinist_status = "negative" if sinist_val > 80 else ("warning" if sinist_val > 75 else "positive")
    sinist_ctx = "Acima de 80%" if sinist_val > 80 else ("Zona de atenção" if sinist_val > 75 else "Saudável")
    
    render_kpis([
        ("Receita (4T/2025)", format_reais(op_data['receita']), "Contraprestações"),
        ("Despesa Assistencial", format_reais(op_data['despesa']), "Eventos e sinistros"),
        ("Sinistralidade", f"{sinist_val:.1f}%", sinist_ctx, sinist_status),
    ])
    
    # --- POSIÇÃO NO MERCADO ---
    section_header("Posição no Mercado", "Onde esta operadora se situa em relação às demais")
    
    rank_sinist = (df_ops['sinistralidade'] <= op_data['sinistralidade']).sum()
    percentil = rank_sinist / len(df_ops) * 100
    
    st.markdown(f"""
    <div class="insight-box">
        <strong>{selected_nome}</strong> está no <strong>percentil {percentil:.0f}</strong> de sinistralidade 
        (posição {rank_sinist} de {len(df_ops)} operadoras). 
        {"Isso significa que está entre as operadoras com MAIOR pressão assistencial." if percentil > 75 else 
         "Isso significa que está em posição intermediária no mercado." if percentil > 40 else
         "Isso significa que está entre as operadoras MAIS EFICIENTES do mercado."}
    </div>
    """, unsafe_allow_html=True)
    
    # --- CARTEIRA DE BENEFICIÁRIOS ---
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
        section_header("Evolução de Beneficiários", "Cobertura médico-hospitalar")
        df_med = df_benef_op[df_benef_op['cobertura'].str.contains('dico', case=False, na=False)]
        df_evol = df_med.groupby('mes_competencia')['total_beneficiarios'].sum().reset_index()
        df_evol = df_evol.sort_values('mes_competencia')
        
        if not df_evol.empty:
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
    
    # --- GRANULARIDADE (Sprint 4) ---
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    section_header("Granularidade — Produto, Município e Faixa Etária", "SIB Individualizado — 28 UFs — Competência Mar/2026")
    
    try:
        con = get_connection()
        
        # Verificar se há dados granulares para esta operadora
        has_data = con.execute(f"SELECT COUNT(*) FROM sib_granular WHERE registro_ans = ?", [selected_reg]).fetchone()[0]
        
        if has_data > 0:
            col_f1, col_f2, col_f3 = st.columns(3)
            
            ufs_list = con.execute("SELECT DISTINCT uf FROM sib_granular WHERE registro_ans = ? ORDER BY uf", [selected_reg]).df()['uf'].tolist()
            with col_f1:
                sel_uf = st.selectbox("UF:", ["Todas"] + ufs_list, key="op_uf")
            
            segs = con.execute("SELECT DISTINCT segmentacao FROM sib_granular WHERE registro_ans = ? AND segmentacao IS NOT NULL ORDER BY segmentacao", [selected_reg]).df()['segmentacao'].tolist()
            with col_f2:
                sel_seg = st.selectbox("Segmentação:", ["Todas"] + segs, key="op_seg")
            
            contrats = con.execute("SELECT DISTINCT tipo_contratacao FROM sib_granular WHERE registro_ans = ? ORDER BY tipo_contratacao", [selected_reg]).df()['tipo_contratacao'].tolist()
            with col_f3:
                sel_contr = st.selectbox("Contratação:", ["Todas"] + contrats, key="op_contr")
            
            # Construir query com parâmetros
            params = [selected_reg]
            where_clauses = ["registro_ans = ?"]
            if sel_uf != "Todas":
                where_clauses.append("uf = ?")
                params.append(sel_uf)
            if sel_seg != "Todas":
                where_clauses.append("segmentacao = ?")
                params.append(sel_seg)
            if sel_contr != "Todas":
                where_clauses.append("tipo_contratacao = ?")
                params.append(sel_contr)
            where_sql = "WHERE " + " AND ".join(where_clauses)
            
            stats = con.execute(f"""
                SELECT SUM(qt_beneficiario_ativo) as vidas, COUNT(DISTINCT cd_plano) as produtos,
                       COUNT(DISTINCT municipio) as municipios
                FROM sib_granular {where_sql}
            """, params).fetchone()
            
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
                    """, params).df()
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
                        AND faixa_etaria_reajuste IS NOT NULL
                        GROUP BY faixa_etaria_reajuste ORDER BY faixa
                    """, params).df()
                    fig = px.bar(df_idade, x='faixa', y='vidas', color_discrete_sequence=[PRIMARY_MUTED],
                                labels={'faixa': '', 'vidas': 'Beneficiários'})
                    fig = apply_layout(fig, height=300)
                    fig.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Sem dados granulares disponíveis para esta operadora com os filtros selecionados.")
        else:
            st.info(f"Dados granulares do SIB não disponíveis para {selected_nome}.")
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
    
    try:
        con = get_connection()
        
        # --- FILTROS ---
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
        
        # Construir filtro com parâmetros
        where_parts = []
        params = []
        if op_sel != "Todas":
            where_parts.append("razao_social = ?")
            params.append(op_sel)
        if seg_sel != "Todas":
            where_parts.append("segmentacao = ?")
            params.append(seg_sel)
        if contr_sel != "Todas":
            where_parts.append("tipo_contratacao = ?")
            params.append(contr_sel)
        where_score = "WHERE " + " AND ".join(where_parts) if where_parts else ""
        
        st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
        
        # KPIs
        kpi_data = con.execute(f"""
            SELECT COUNT(DISTINCT cd_plano) as produtos, SUM(vidas_total) as vidas,
                   SUM(despesa_estimada) as despesa, AVG(sinistralidade_estimada) as sinist,
                   AVG(custo_per_capita_medio) as custo_pc
            FROM score_risco_produto_agg {where_score}
        """, params).fetchone()
        
        vidas_fmt = f"{kpi_data[1]/1e6:.2f}M" if kpi_data[1] and kpi_data[1] > 1e6 else f"{kpi_data[1]/1e3:.0f}k" if kpi_data[1] else "0"
        desp_fmt = format_reais(kpi_data[2]) if kpi_data[2] else "N/A"
        
        render_kpis([
            ("Produtos", f"{kpi_data[0]:,}" if kpi_data[0] else "0", "Com score calculado"),
            ("Vidas", vidas_fmt, "Beneficiários ativos"),
            ("Despesa Estimada", desp_fmt, "Alocação proporcional"),
            ("Custo Per Capita", f"R$ {kpi_data[4]:,.0f}/mês" if kpi_data[4] else "N/A", "Média ponderada"),
        ])
        
        # --- SCATTER PLOT: Vidas vs Custo Per Capita ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            section_header("Dispersão: Vidas vs. Custo Per Capita", "Cada ponto = 1 produto (Top 200 por vidas)")
            df_scatter = con.execute(f"""
                SELECT 
                    razao_social as operadora,
                    cd_plano,
                    vidas_total as vidas,
                    custo_per_capita_medio as custo_pc,
                    segmentacao,
                    sinistralidade_estimada as sinist
                FROM score_risco_produto_agg {where_score}
                WHERE vidas_total > 0
                ORDER BY vidas_total DESC
                LIMIT 200
            """, params).df()
            
            if not df_scatter.empty:
                fig = px.scatter(df_scatter, x='vidas', y='custo_pc',
                               color='segmentacao', size='vidas',
                               hover_data=['operadora', 'cd_plano'],
                               color_discrete_sequence=CHART_COLORS,
                               labels={'vidas': 'Vidas', 'custo_pc': 'Custo PC (R$/mês)', 'segmentacao': 'Segmentação'})
                fig = apply_layout(fig, height=350, show_legend=True)
                fig.update_layout(legend=dict(font=dict(size=9)))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col_g2:
            section_header("Custo Per Capita por UF", "Top 15 UFs por custo médio")
            df_uf = con.execute("""
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
        
        # --- RANKING DE PRODUTOS (paginado) ---
        section_header("Ranking de Produtos por Custo Per Capita", "Ordenado por maior custo estimado mensal por beneficiário")
        
        # Controle de paginação
        page_size = 25
        total_products = con.execute(f"SELECT COUNT(*) FROM score_risco_produto_agg {where_score}", params).fetchone()[0]
        total_pages = max(1, (total_products + page_size - 1) // page_size)
        
        col_pg1, col_pg2 = st.columns([3, 1])
        with col_pg2:
            current_page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, key="prod_page")
        with col_pg1:
            st.markdown(f'<p class="caption">Mostrando {page_size} de {total_products:,} produtos (página {current_page}/{total_pages})</p>', unsafe_allow_html=True)
        
        offset = (current_page - 1) * page_size
        
        df_ranking = con.execute(f"""
            SELECT 
                razao_social as "Operadora",
                cd_plano as "Produto",
                segmentacao as "Segmentação",
                tipo_contratacao as "Contratação",
                vidas_total as "Vidas",
                ROUND(custo_per_capita_medio, 0) as "Custo PC (R$/mês)",
                ROUND(sinistralidade_estimada * 100, 1) as "Sinist. (%)",
                ROUND(fator_etario_medio, 2) as "Fator Etário"
            FROM score_risco_produto_agg {where_score}
            ORDER BY custo_per_capita_medio DESC
            LIMIT {page_size} OFFSET {offset}
        """, params).df()
        
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        
        # Export completo
        csv_all = con.execute(f"""
            SELECT razao_social, cd_plano, segmentacao, tipo_contratacao, vidas_total,
                   ROUND(custo_per_capita_medio, 0) as custo_pc, 
                   ROUND(sinistralidade_estimada * 100, 1) as sinistralidade_pct
            FROM score_risco_produto_agg {where_score}
            ORDER BY custo_per_capita_medio DESC
        """, params).df().to_csv(index=False).encode('utf-8')
        st.download_button("Exportar ranking completo (.csv)", csv_all, "score_risco_produtos.csv", "text/csv")
        
        # Metodologia
        with st.expander("Como o score de risco é calculado"):
            st.markdown("""
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
        con_st = get_connection()
        
        df_hist = con_st.execute("""
            SELECT registro_ans, trimestre, receita, despesa, sinistralidade
            FROM sinistralidade_historica
            ORDER BY registro_ans, trimestre
        """).df()
        
        # Resolução dinâmica de nomes
        cadastro = load_operadoras_cadastro()
        nome_map = dict(zip(cadastro['registro_ans'], cadastro['nome']))
        df_hist['operadora'] = df_hist['registro_ans'].map(nome_map).fillna(df_hist['registro_ans'])
        
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
                    'registro_ans': reg, 'operadora': nome_map.get(reg, reg),
                    'trimestre': row['trimestre'], 'ordem': row['ordem'],
                    'receita_tri': rec_tri, 'despesa_tri': desp_tri, 'sinistralidade_tri': sinist_tri
                })
        
        df_tri = pd.DataFrame(records)
        df_tri = df_tri[df_tri['sinistralidade_tri'].notna()]
        df_tri = df_tri[(df_tri['sinistralidade_tri'] > 0) & (df_tri['sinistralidade_tri'] < 2.0)]
        
        # KPIs de tendência
        n_ops_hist = df_tri['registro_ans'].nunique()
        n_trimestres = df_tri['trimestre'].nunique()
        sinist_atual = df_tri[df_tri['trimestre'] == '4T2025']['sinistralidade_tri'].mean()
        sinist_2020 = df_tri[df_tri['trimestre'] == '4T2020']['sinistralidade_tri'].mean()
        variacao = ((sinist_atual / sinist_2020) - 1) * 100 if sinist_2020 and sinist_2020 > 0 else 0
        
        render_kpis([
            ("Operadoras", str(n_ops_hist), "Com série histórica"),
            ("Trimestres", str(n_trimestres), "Período 2020-2025"),
            ("Sinistralidade Atual", f"{sinist_atual*100:.1f}%" if sinist_atual else "N/A", 
             "Acima de 80%" if sinist_atual and sinist_atual > 0.8 else "Dentro do esperado",
             "negative" if sinist_atual and sinist_atual > 0.8 else "positive"),
            ("Variação 5 anos", f"{variacao:+.0f}%", 
             "Piora" if variacao > 0 else "Melhora",
             "negative" if variacao > 0 else "positive"),
        ])
        
        st.markdown(f'<p class="caption">Sinistralidade = Despesa Assistencial / Receita. Valores trimestrais isolados (não acumulados).</p>', unsafe_allow_html=True)
        
        # Filtro de operadoras — INICIA VAZIO (máx 5 sugeridas)
        ops_disponiveis = sorted(df_tri['operadora'].unique())
        
        # Sugerir as 5 maiores por receita como default
        df_ops_main = load_operadoras_data()
        top5_regs = df_ops_main.nlargest(5, 'receita')['registro_ans'].tolist()
        default_ops = [nome_map.get(r, r) for r in top5_regs if nome_map.get(r, r) in ops_disponiveis]
        if not default_ops:
            default_ops = ops_disponiveis[:5]
        
        ops_selecionadas = st.multiselect(
            f"Selecione operadoras para comparar (máx. recomendado: 5 de {len(ops_disponiveis)} disponíveis):",
            ops_disponiveis, 
            default=default_ops,
            key="st_ops"
        )
        
        if ops_selecionadas:
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
        else:
            st.info("Selecione ao menos uma operadora para visualizar a evolução temporal.")
        
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        
        # Tabela de tendências (ranking paginado)
        section_header("Ranking de Tendências", "CAGR de receita e variação de sinistralidade no período")
        
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
                    'Operadora': nome_map.get(reg, reg),
                    'Receita Atual (R$M)': f"{rec_fin/1e6:.0f}",
                    'CAGR Receita': f"{cagr_rec:.1f}%",
                    'Sinist. Atual': f"{sin_fin:.1f}%",
                    'Delta': f"{delta_sin:+.1f} pp",
                    'Tendência': 'Piora' if delta_sin > 3 else ('Melhora' if delta_sin < -3 else 'Estável')
                })
        
        df_tend = pd.DataFrame(tendencias)
        st.dataframe(df_tend, use_container_width=True, hide_index=True, height=250)
        
    except Exception as e:
        st.warning(f"Série temporal indisponível: {e}")
    
    # --- BENCHMARK IESS ---
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    section_header("Benchmark de Mercado", "Comparação com indicadores IESS, ANS e UNIDAS 2024")
    
    try:
        con_b = get_connection()
        
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
        
        if not benchmark_data.empty:
            sinist_mercado = 82.2
            
            # Mostrar Top 10 mais eficientes e Top 10 sob pressão
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                section_header("Mais Eficientes (vs. Benchmark)")
                df_eficientes = benchmark_data.nsmallest(TOP_N, 'delta')
                fig_eff = px.bar(df_eficientes, x='nome_operadora', y='delta',
                                color_discrete_sequence=[SUCCESS],
                                labels={'nome_operadora': '', 'delta': 'Delta vs Benchmark (pp)'},
                                text=df_eficientes['delta'].apply(lambda x: f'{x:+.1f}pp'))
                fig_eff = apply_layout(fig_eff, height=300)
                fig_eff.update_traces(textposition='outside', textfont_size=9)
                fig_eff.update_xaxes(tickangle=-45)
                st.plotly_chart(fig_eff, use_container_width=True, config={'displayModeBar': False})
            
            with col_b2:
                section_header("Sob Maior Pressão (vs. Benchmark)")
                df_pressao = benchmark_data.nlargest(TOP_N, 'delta')
                fig_press = px.bar(df_pressao, x='nome_operadora', y='delta',
                                  color_discrete_sequence=[ERROR],
                                  labels={'nome_operadora': '', 'delta': 'Delta vs Benchmark (pp)'},
                                  text=df_pressao['delta'].apply(lambda x: f'{x:+.1f}pp'))
                fig_press = apply_layout(fig_press, height=300)
                fig_press.update_traces(textposition='outside', textfont_size=9)
                fig_press.update_xaxes(tickangle=-45)
                st.plotly_chart(fig_press, use_container_width=True, config={'displayModeBar': False})
            
            # Tabela completa
            with st.expander(f"Tabela de Classificação Completa ({len(benchmark_data)} operadoras)"):
                display_df = benchmark_data[['nome_operadora', 'tipo_operadora', 'sinist_real', 'benchmark', 'delta', 'classificacao_benchmark']].copy()
                display_df.columns = ['Operadora', 'Tipo', 'Sinistralidade', 'Benchmark', 'Delta (pp)', 'Classificação']
                display_df['Sinistralidade'] = display_df['Sinistralidade'].apply(lambda x: f'{x:.1f}%')
                display_df['Benchmark'] = display_df['Benchmark'].apply(lambda x: f'{x:.1f}%')
                display_df['Delta (pp)'] = display_df['Delta (pp)'].apply(lambda x: f'{x:+.1f}')
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=350)
    
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
# PÁGINA 5: PREDIÇÃO (ML)
# =========================================================
elif pagina == "Predição (ML)":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Predição de Sinistralidade (ML)</p>
        <p class="product-subtitle">Modelo XGBoost treinado com dados DIOPS + SIB — Sprint 8</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        con = get_connection()
        
        # Verificar se tabela de predições existe
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        
        if 'predicoes_xgboost' in tables:
            df_pred = con.execute("""
                SELECT * FROM predicoes_xgboost
            """).df()
            
            # Resolução dinâmica de nomes
            cadastro = load_operadoras_cadastro()
            nome_map = dict(zip(cadastro['registro_ans'].astype(str), cadastro['nome']))
            
            if 'registro_ans' in df_pred.columns:
                df_pred['operadora'] = df_pred['registro_ans'].astype(str).map(nome_map).fillna(df_pred['registro_ans'].astype(str))
            
            # KPIs do modelo
            render_kpis([
                ("Modelo", "XGBoost v1", "Gradient Boosting"),
                ("R² (Test)", "0.901", "Modelo 1 — Operadora", "positive"),
                ("Accuracy", "99.4%", "Classificação binária", "positive"),
                ("Features", "5", "Variáveis preditoras"),
            ])
            
            st.markdown('<hr class="divider-subtle">', unsafe_allow_html=True)
            
            # --- TOP MOVERS: Quem mais muda ---
            section_header("Top Movers — Maiores Variações Previstas", "Operadoras com maior diferença entre sinistralidade real e predita")
            
            if 'sinistralidade_real' in df_pred.columns and 'sinistralidade_predita' in df_pred.columns:
                df_pred['delta_pred'] = (df_pred['sinistralidade_predita'] - df_pred['sinistralidade_real']) * 100
                
                col_p1, col_p2 = st.columns(2)
                
                with col_p1:
                    section_header("Tendência de Piora")
                    df_piora = df_pred.nlargest(min(TOP_N, len(df_pred)), 'delta_pred')
                    if not df_piora.empty:
                        fig = px.bar(df_piora, x='operadora', y='delta_pred',
                                    color_discrete_sequence=[ERROR],
                                    labels={'operadora': '', 'delta_pred': 'Δ Sinistralidade (pp)'},
                                    text=df_piora['delta_pred'].apply(lambda x: f'+{x:.1f}pp'))
                        fig = apply_layout(fig, height=280)
                        fig.update_traces(textposition='outside', textfont_size=10)
                        fig.update_xaxes(tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                with col_p2:
                    section_header("Tendência de Melhora")
                    df_melhora = df_pred.nsmallest(min(TOP_N, len(df_pred)), 'delta_pred')
                    if not df_melhora.empty:
                        fig = px.bar(df_melhora, x='operadora', y='delta_pred',
                                    color_discrete_sequence=[SUCCESS],
                                    labels={'operadora': '', 'delta_pred': 'Δ Sinistralidade (pp)'},
                                    text=df_melhora['delta_pred'].apply(lambda x: f'{x:.1f}pp'))
                        fig = apply_layout(fig, height=280)
                        fig.update_traces(textposition='outside', textfont_size=10)
                        fig.update_xaxes(tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                # Insight agregado
                n_piora = len(df_pred[df_pred['delta_pred'] > 1])
                n_melhora = len(df_pred[df_pred['delta_pred'] < -1])
                n_estavel = len(df_pred) - n_piora - n_melhora
                
                st.markdown(f"""
                <div class="insight-box">
                    <strong>Resumo preditivo:</strong> De {len(df_pred)} operadoras analisadas, 
                    <strong>{n_piora}</strong> apresentam tendência de piora (Δ > +1pp), 
                    <strong>{n_melhora}</strong> de melhora (Δ < -1pp) e 
                    <strong>{n_estavel}</strong> permanecem estáveis.
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<hr class="divider">', unsafe_allow_html=True)
            
            # --- FEATURE IMPORTANCE ---
            section_header("Importância das Features (SHAP)", "Contribuição de cada variável para a predição")
            
            col_fi1, col_fi2 = st.columns(2)
            
            if 'feature_importance_m1' in tables:
                with col_fi1:
                    section_header("Modelo 1 — Sinistralidade Operadora")
                    df_fi1 = con.execute("SELECT feature, importance FROM feature_importance_m1 ORDER BY importance DESC LIMIT 10").df()
                    if not df_fi1.empty:
                        fig = px.bar(df_fi1, x='importance', y='feature', orientation='h',
                                    color_discrete_sequence=[PRIMARY],
                                    labels={'importance': 'SHAP Importance', 'feature': ''},
                                    text=df_fi1['importance'].apply(lambda x: f'{x:.4f}'))
                        fig = apply_layout(fig, height=280)
                        fig.update_traces(textposition='outside', textfont_size=10)
                        fig.update_yaxes(categoryorder='total ascending')
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            if 'feature_importance_m2' in tables:
                with col_fi2:
                    section_header("Modelo 2 — Score de Risco Produto")
                    df_fi2 = con.execute("SELECT feature, importance FROM feature_importance_m2 ORDER BY importance DESC LIMIT 10").df()
                    if not df_fi2.empty:
                        fig = px.bar(df_fi2, x='importance', y='feature', orientation='h',
                                    color_discrete_sequence=[GOLD],
                                    labels={'importance': 'SHAP Importance', 'feature': ''},
                                    text=df_fi2['importance'].apply(lambda x: f'{x:.4f}'))
                        fig = apply_layout(fig, height=280)
                        fig.update_traces(textposition='outside', textfont_size=10)
                        fig.update_yaxes(categoryorder='total ascending')
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown('<hr class="divider">', unsafe_allow_html=True)
            
            # Tabela de predições completa
            with st.expander(f"Tabela de Predições ({len(df_pred)} operadoras)"):
                display_cols = ['operadora']
                if 'sinistralidade_real' in df_pred.columns:
                    display_cols.append('sinistralidade_real')
                if 'sinistralidade_predita' in df_pred.columns:
                    display_cols.append('sinistralidade_predita')
                if 'delta_pred' in df_pred.columns:
                    display_cols.append('delta_pred')
                
                df_show = df_pred[display_cols].copy()
                df_show.columns = ['Operadora', 'Real (%)', 'Predita (%)', 'Delta (pp)'] if len(display_cols) == 4 else display_cols
                if 'Real (%)' in df_show.columns:
                    df_show['Real (%)'] = df_show['Real (%)'].apply(lambda x: f'{x*100:.1f}%' if x < 1 else f'{x:.1f}%')
                if 'Predita (%)' in df_show.columns:
                    df_show['Predita (%)'] = df_show['Predita (%)'].apply(lambda x: f'{x*100:.1f}%' if x < 1 else f'{x:.1f}%')
                if 'Delta (pp)' in df_show.columns:
                    df_show['Delta (pp)'] = df_show['Delta (pp)'].apply(lambda x: f'{x:+.1f}')
                st.dataframe(df_show, use_container_width=True, hide_index=True, height=300)
            
            # Governança
            with st.expander("Governança e Limitações"):
                st.markdown("""
                **Modelo:** XGBoost Regressor (Modelo 1) + XGBoost Classifier (Modelo 2)  
                **Dados de treino:** DIOPS 2020-2025 (132 registros) + SIB Mar/2026 (696k registros)  
                **Validação:** Hold-out 20% + Cross-validation 5-fold  
                **Limitações:**
                - Base de treino limitada a operadoras com dados completos no SIB
                - Modelo não captura choques exógenos (pandemia, mudanças regulatórias)
                - Predição de 1 trimestre à frente; horizonte maior requer recalibração
                """)
        else:
            st.info("Tabela de predições não encontrada. Execute o Sprint 8 (sprint8_xgboost.py) para gerar as predições.")
    
    except Exception as e:
        st.error(f"Erro na página de Predição: {e}")
    
    page_footer()



# =========================================================
# PÁGINA 6: METODOLOGIA
# =========================================================
elif pagina == "Metodologia":
    st.markdown(f"""
    <div class="exec-header">
        <p class="product-name">Metodologia e Fontes</p>
        <p class="product-subtitle">Transparência metodológica — Motor de Sinistralidade ANS</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### Fontes de Dados
    
    | Fonte | Competência | Registros | Uso |
    |-------|-------------|-----------|-----|
    | DIOPS — ANS | 4T/2025 | 6 operadoras | Receita, despesa, sinistralidade |
    | SIB Individualizado — ANS | Mar/2026 | 696.183 | Vidas por produto, faixa, UF |
    | Cadastro de Produtos — ANS | Abr/2026 | 1.793 | Segmentação, cobertura |
    | VCMH/IESS | Set/2023 | — | Fatores geográficos |
    | RN 63/2003 — ANS | — | 10 faixas | Curva etária regulatória |
    
    ### Modelo de Alocação (Score de Risco)
    
    O modelo distribui a despesa assistencial total (DIOPS) entre produtos individuais usando um score composto:
    
    ```
    Score_Produto = Vidas × Fator_Etário × Fator_Geográfico × Fator_Segmentação × Fator_Contratação
    Despesa_Produto = (Score_Produto / Σ Scores_Operadora) × Despesa_Total_Operadora
    Sinistralidade_Produto = Despesa_Produto / Receita_Estimada_Produto
    ```
    
    ### Modelo Preditivo (Sprint 8)
    
    - **Modelo 1:** XGBoost Regressor — prediz sinistralidade da operadora no próximo trimestre
    - **Modelo 2:** XGBoost Regressor — prediz score de risco por produto
    - **Features:** sinistralidade_historica, fator_etario, fator_geografico, cagr_receita, vidas_total
    - **Métricas:** R² = 0.901 (M1), R² = 0.994 (M2)
    
    ### Roadmap de Sprints
    """)
    
    st.markdown("""
    | Sprint | Escopo | Status |
    |--------|--------|--------|
    | 1 | ETL DIOPS + Sinistralidade base | ✅ Concluído |
    | 2 | ETL SIB + Carteira de beneficiários | ✅ Concluído |
    | 3 | Cadastro de Produtos + Cruzamento | ✅ Concluído |
    | 4 | Granularidade por produto/município/faixa | ✅ Concluído |
    | 5 | Score de Risco + Proxy de Sinistralidade | ✅ Concluído |
    | 6 | Série Temporal DIOPS 2020-2025 | ✅ Concluído |
    | 7 | Benchmark IESS/ANS/UNIDAS | ✅ Concluído |
    | 8 | Predição ML (XGBoost) | ✅ Concluído |
    | 8.1 | Refatoração UX/UI para Escala | ✅ Concluído |
    | 8.5 | Expansão para mercado completo (~700 ops) | 🔜 Próximo |
    | 9 | API REST (FastAPI) | 📋 Planejado |
    | 10 | Pipeline de Atualização Automática | 📋 Planejado |
    | 11 | Interface Web Dedicada (React) | 📋 Planejado |
    """)
    
    st.markdown("""
    ### Limitações e Disclaimers
    
    - Dados DIOPS são auto-declarados pelas operadoras e sujeitos a revisão pela ANS
    - O modelo de alocação (proxy) estima sinistralidade por produto; não substitui dados reais de sinistros
    - Fatores geográficos baseados em VCMH/IESS podem não refletir variações locais recentes
    - Predições ML são indicativas e não devem ser usadas isoladamente para decisões de precificação
    """)
    
    page_footer()
