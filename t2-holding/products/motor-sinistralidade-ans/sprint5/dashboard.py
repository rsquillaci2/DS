"""
Motor de Sinistralidade ANS
Dashboard Analítico — Tallent Two Financial Holding
v0.4
"""
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import base64
import os

# =========================================================
# CONFIGURAÇÃO
# =========================================================
APP_VERSION = "v0.5"
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
SURFACE = "#FFF3DE"
GOLD = "#FFD700"
GRAY = "#BEBEBE"
WHITE = "#FFFFFF"
BLACK = "#000000"
SUCCESS = "#16A34A"
WARNING = "#CA8A04"
ERROR = "#DC2626"
LIGHT_BG = "#F9FAFB"

CHART_COLORS = ["#2C3D5B", "#3D5278", "#5A7099", "#7D92B3", "#C9A227", "#9CA3AF"]
PIE_COLORS = ["#2C3D5B", "#5A7099", "#7D92B3", "#A8B8D0", "#C9A227"]

# Custom CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;700;800&family=Roboto:wght@300;400;500;700&display=swap');
    
    .main-header {{
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: {PRIMARY};
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }}
    .sub-header {{
        font-family: 'Roboto', sans-serif;
        font-size: 0.95rem;
        color: #6B7280;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }}
    .stMetric > div {{
        background-color: {LIGHT_BG};
        padding: 0.9rem 1rem;
        border-radius: 2px;
        border-bottom: 2px solid {PRIMARY};
    }}
    .stMetric label {{
        font-family: 'Roboto', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #6B7280 !important;
    }}
    .stMetric [data-testid="stMetricValue"] {{
        font-family: 'Roboto', sans-serif !important;
        font-weight: 700 !important;
        color: {PRIMARY} !important;
    }}
    div[data-testid="stSidebar"] {{
        background-color: {PRIMARY};
    }}
    div[data-testid="stSidebar"] .stMarkdown {{
        color: {WHITE};
    }}
    div[data-testid="stSidebar"] label {{
        color: {SURFACE} !important;
    }}
    div[data-testid="stSidebar"] .stRadio label {{
        color: {SURFACE} !important;
    }}
    div[data-testid="stSidebar"] .stRadio label span {{
        font-size: 0.88rem !important;
    }}
    h1, h2, h3 {{
        font-family: 'Playfair Display', serif;
        color: {PRIMARY};
    }}
    h3 {{
        font-size: 1.15rem !important;
        margin-top: 1rem !important;
    }}
    .stDataFrame thead tr th {{
        background-color: {PRIMARY} !important;
        color: {WHITE} !important;
        font-size: 0.8rem !important;
    }}
    .block-container {{
        font-family: 'Roboto', sans-serif;
        padding-top: 2rem;
    }}
    .t2-footer {{
        text-align: center;
        color: #9CA3AF;
        font-size: 0.75rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #E5E7EB;
        margin-top: 3rem;
        font-family: 'Roboto', sans-serif;
    }}
    .fonte-caption {{
        font-size: 0.72rem;
        color: #9CA3AF;
        margin-top: 0.3rem;
    }}
    .section-divider {{
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 1.5rem 0;
    }}
</style>
""", unsafe_allow_html=True)


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
    
    st.markdown("")
    st.markdown("#### Motor de Sinistralidade")
    st.markdown('<span style="font-size:0.82rem; color:#A8B8D0;">Precificação baseada em dados abertos ANS</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navegação
    pagina = st.radio(
        "Navegação",
        ["Visão Geral", "Análise por Operadora", "Proxy por Produto", "Granularidade", "Score de Risco", "Metodologia"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Fontes de dados
    st.markdown('<span style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em; color:#A8B8D0;">Fontes de Dados</span>', unsafe_allow_html=True)
    st.markdown('<span style="font-size:0.82rem;">DIOPS 4T/2025</span>', unsafe_allow_html=True)
    st.markdown('<span style="font-size:0.82rem;">SIB Individualizado Mar/2026</span>', unsafe_allow_html=True)
    st.markdown('<span style="font-size:0.82rem;">Cadastro de Produtos ANS</span>', unsafe_allow_html=True)
    st.markdown('<span style="font-size:0.82rem; color:#C9A227;">696.183 registros granulares</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f'<span style="font-size:0.72rem; color:#7D92B3;">{APP_VERSION} — Tallent Two</span>', unsafe_allow_html=True)


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
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F3F4F6")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F3F4F6")
    return fig


# =========================================================
# PÁGINA 1: VISÃO GERAL
# =========================================================
if pagina == "Visão Geral":
    st.markdown('<p class="main-header">Sinistralidade Comparativa</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Operadoras selecionadas — Demonstrações Contábeis DIOPS 4T/2025</p>', unsafe_allow_html=True)
    
    df_ops = load_operadoras_data()
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Operadoras", len(df_ops))
    with col2:
        receita_total = df_ops['receita'].sum()
        st.metric("Receita Total", f"R$ {receita_total/1e9:.2f} bi")
    with col3:
        sinist_media = df_ops['despesa'].sum() / df_ops['receita'].sum()
        st.metric("Sinistralidade Ponderada", f"{sinist_media*100:.1f}%")
    with col4:
        df_benef = load_beneficiarios()
        total_vidas = df_benef[df_benef['mes_competencia'] == df_benef['mes_competencia'].max()]['total_beneficiarios'].sum()
        st.metric("Vidas (Último Mês)", f"{total_vidas:,.0f}")
    
    st.markdown('<p class="fonte-caption">Base: 6 operadoras selecionadas. Fonte: DIOPS/ANS e SIB/ANS.</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Gráficos
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.markdown("### Sinistralidade por Operadora")
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
        st.markdown('<p class="fonte-caption">Linha pontilhada: limiar de alerta setorial.</p>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown("### Receita vs Despesa Assistencial")
        df_comp = df_chart[['nome_display', 'receita', 'despesa']].copy()
        df_comp['receita_bi'] = df_comp['receita'] / 1e9
        df_comp['despesa_bi'] = df_comp['despesa'] / 1e9
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Receita', y=df_comp['nome_display'], x=df_comp['receita_bi'],
                              orientation='h', marker_color=PRIMARY))
        fig2.add_trace(go.Bar(name='Despesa', y=df_comp['nome_display'], x=df_comp['despesa_bi'],
                              orientation='h', marker_color="#DC2626"))
        fig2 = apply_layout(fig2, height=320, show_legend=True)
        fig2.update_layout(barmode='group', xaxis_title="R$ bilhões")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela
    st.markdown("---")
    st.markdown("### Resumo Financeiro")
    df_display = df_ops[['registro_ans', 'nome_operadora', 'modalidade', 'receita', 'despesa', 'sinistralidade']].copy()
    df_display.columns = ['Registro ANS', 'Operadora', 'Modalidade', 'Receita', 'Despesa Assistencial', 'Sinistralidade']
    df_display['Receita'] = df_display['Receita'].apply(lambda x: f"R$ {x/1e6:,.1f} M")
    df_display['Despesa Assistencial'] = df_display['Despesa Assistencial'].apply(lambda x: f"R$ {x/1e6:,.1f} M")
    df_display['Sinistralidade'] = df_display['Sinistralidade'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.markdown(f'<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 2: ANÁLISE POR OPERADORA
# =========================================================
elif pagina == "Análise por Operadora":
    st.markdown('<p class="main-header">Análise Individual</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Detalhamento financeiro e de carteira por operadora</p>', unsafe_allow_html=True)
    
    df_ops = load_operadoras_data()
    df_benef = load_beneficiarios()
    
    opcoes = df_ops['nome_operadora'].fillna(df_ops['registro_ans']).tolist()
    registros = df_ops['registro_ans'].tolist()
    
    selected_nome = st.selectbox("Operadora:", opcoes)
    idx = opcoes.index(selected_nome)
    selected_reg = registros[idx]
    
    op_data = df_ops[df_ops['registro_ans'] == selected_reg].iloc[0]
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Receita (4T/2025)", f"R$ {op_data['receita']/1e6:,.1f} M")
    with col2:
        st.metric("Despesa Assistencial", f"R$ {op_data['despesa']/1e6:,.1f} M")
    with col3:
        sinist_val = op_data['sinistralidade'] * 100
        delta_label = "Acima de 80%" if sinist_val > 80 else "Dentro do esperado"
        st.metric("Sinistralidade", f"{sinist_val:.1f}%", delta=delta_label)
    
    st.markdown("---")
    
    df_benef_op = df_benef[df_benef['registro_ans'] == selected_reg]
    
    if not df_benef_op.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### Tipo de Contratação")
            df_contrat = df_benef_op.groupby('tipo_contratacao')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_contrat, values='total_beneficiarios', names='tipo_contratacao',
                        color_discrete_sequence=PIE_COLORS, hole=0.4)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.markdown("### Cobertura Assistencial")
            df_cob = df_benef_op.groupby('cobertura')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_cob, values='total_beneficiarios', names='cobertura',
                        color_discrete_sequence=PIE_COLORS, hole=0.4)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # Evolução temporal
        st.markdown("### Evolução de Beneficiários")
        df_med = df_benef_op[df_benef_op['cobertura'].str.contains('dico', case=False, na=False)]
        df_evol = df_med.groupby('mes_competencia')['total_beneficiarios'].sum().reset_index()
        df_evol = df_evol.sort_values('mes_competencia')
        
        mediana = df_evol['total_beneficiarios'].median()
        df_evol = df_evol[df_evol['total_beneficiarios'] >= mediana * 0.5]
        df_evol['mes_date'] = pd.to_datetime(df_evol['mes_competencia'].astype(str) + '01', format='%Y%m%d')
        df_evol = df_evol.sort_values('mes_date')
        
        fig = px.line(df_evol, x='mes_date', y='total_beneficiarios',
                     labels={'mes_date': '', 'total_beneficiarios': 'Beneficiários'},
                     color_discrete_sequence=[PRIMARY])
        fig = apply_layout(fig, height=220)
        fig.update_layout(xaxis=dict(dtick="M6", tickformat="%b/%Y"))
        fig.update_traces(mode='lines+markers', marker=dict(size=3), line=dict(width=2))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<p class="fonte-caption">Cobertura médico-hospitalar. Meses com dados parciais removidos automaticamente.</p>', unsafe_allow_html=True)
    else:
        st.info("Dados de beneficiários não disponíveis para esta operadora no dataset consolidado.")
    
    st.markdown(f'<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 3: PROXY POR PRODUTO
# =========================================================
elif pagina == "Proxy por Produto":
    st.markdown('<p class="main-header">Sinistralidade Proxy por Produto</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Estimativa baseada em fatores de ponderação atuarial (segmentação, contratação, abrangência, moderador)</p>', unsafe_allow_html=True)
    
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
        
        st.markdown("---")
        
        # KPIs — USAM df_filtered (corrigido)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Produtos Filtrados", f"{len(df_filtered):,}")
        with col2:
            st.metric("Sinistralidade Proxy Média", f"{df_filtered['sinistralidade_proxy'].mean()*100:.1f}%")
        with col3:
            st.metric("Proxy Mínimo", f"{df_filtered['sinistralidade_proxy'].min()*100:.1f}%")
        with col4:
            st.metric("Proxy Máximo", f"{df_filtered['sinistralidade_proxy'].max()*100:.1f}%")
        
        st.markdown('<p class="fonte-caption">KPIs calculados sobre o conjunto filtrado acima.</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Gráficos
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown("### Distribuição da Sinistralidade Proxy")
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
            st.markdown("### Por Tipo de Contratação")
            df_box = df_filtered.copy()
            df_box['sinistralidade_pct'] = df_box['sinistralidade_proxy'] * 100
            fig = px.box(df_box, x='tipo_contratacao', y='sinistralidade_pct',
                        color='tipo_contratacao',
                        labels={'sinistralidade_pct': 'Sinistralidade (%)', 'tipo_contratacao': ''},
                        color_discrete_sequence=CHART_COLORS)
            fig = apply_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabela
        st.markdown("---")
        st.markdown("### Detalhamento por Produto")
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
    
    st.markdown(f'<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 4: GRANULARIDADE (SPRINT 4)
# =========================================================
elif pagina == "Granularidade":
    st.markdown('<p class="main-header">Granularidade por Produto, Município e Faixa Etária</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">SIB Individualizado — 28 UFs — Competência Mar/2026</p>', unsafe_allow_html=True)
    
    try:
        con = get_connection()
        
        # Filtros PRIMEIRO (para que KPIs respondam)
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
        
        st.markdown("---")
        
        # KPIs — RESPONDEM AOS FILTROS (corrigido)
        stats = con.execute(f"""
            SELECT 
                SUM(qt_beneficiario_ativo) as vidas,
                COUNT(DISTINCT cd_plano) as produtos,
                COUNT(DISTINCT municipio) as municipios,
                COUNT(DISTINCT registro_ans) as operadoras,
                COUNT(DISTINCT uf) as ufs
            FROM sib_granular {where_sql}
        """).fetchone()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Vidas Ativas", f"{stats[0]:,.0f}")
        col2.metric("Produtos", f"{stats[1]:,.0f}")
        col3.metric("Municípios", f"{stats[2]:,.0f}")
        col4.metric("Operadoras", f"{stats[3]:,.0f}")
        col5.metric("UFs", f"{stats[4]:,.0f}")
        
        st.markdown('<p class="fonte-caption">Métricas calculadas sobre o filtro selecionado acima.</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Gráficos
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown("### Top 15 Municípios por Vidas")
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
            st.markdown("### Distribuição por Faixa Etária")
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
                        color_discrete_sequence=["#5A7099"])
            fig = apply_layout(fig, height=380)
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Heatmap
        st.markdown("### Concentração por UF e Segmentação")
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
                           color_continuous_scale=[[0, "#F9FAFB"], [0.3, "#A8B8D0"], [0.7, "#5A7099"], [1, PRIMARY]],
                           aspect="auto")
            fig = apply_layout(fig, height=450)
            fig.update_layout(coloraxis_showscale=True)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Tabela por Produto
        st.markdown("### Detalhamento por Produto")
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
        
        st.markdown("---")
        
        # Composição
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            st.markdown("### Titular vs Dependente")
            df_vinc = con.execute(f"""
                SELECT tipo_vinculo, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY tipo_vinculo
            """).df()
            fig = px.pie(df_vinc, values='vidas', names='tipo_vinculo',
                        color_discrete_sequence=PIE_COLORS, hole=0.4)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_v2:
            st.markdown("### Tipo de Contratação")
            df_cont = con.execute(f"""
                SELECT tipo_contratacao, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY tipo_contratacao
            """).df()
            fig = px.pie(df_cont, values='vidas', names='tipo_contratacao',
                        color_discrete_sequence=CHART_COLORS, hole=0.4)
            fig = apply_layout(fig, height=280, show_legend=True)
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar dados granulares: {e}")
    
    st.markdown(f'<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 5: SCORE DE RISCO (Sprint 5)
# =========================================================
elif pagina == "Score de Risco":
    st.markdown('<p class="main-header">Score de Risco Atuarial</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sinistralidade estimada por Produto × Município × Faixa Etária (Rateio Financeiro)</p>', unsafe_allow_html=True)
    
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
        
        st.markdown("---")
        
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
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{int(kpi_data["produtos"].iloc[0]):,}</div><div class="kpi-label">Produtos</div></div>', unsafe_allow_html=True)
        with c2:
            vidas_v = kpi_data['vidas'].iloc[0]
            vidas_fmt = f"{vidas_v/1e6:.2f}M" if vidas_v > 1e6 else f"{vidas_v/1e3:.0f}k"
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{vidas_fmt}</div><div class="kpi-label">Vidas</div></div>', unsafe_allow_html=True)
        with c3:
            desp_v = kpi_data['despesa'].iloc[0]
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">R$ {desp_v/1e9:.2f}B</div><div class="kpi-label">Despesa Estimada</div></div>', unsafe_allow_html=True)
        with c4:
            sinist_v = kpi_data['sinist_media'].iloc[0] * 100
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{sinist_v:.1f}%</div><div class="kpi-label">Sinistralidade Média</div></div>', unsafe_allow_html=True)
        with c5:
            custo_v = kpi_data['custo_pc'].iloc[0]
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">R$ {custo_v:.0f}</div><div class="kpi-label">Custo Per Capita/Mês</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Gráfico 1: Custo Per Capita por Operadora
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("### Custo Per Capita por Operadora")
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
                        color='sinist', color_continuous_scale=[[0, '#16A34A'], [0.5, '#C9A227'], [1, '#DC2626']],
                        labels={'operadora': '', 'custo_pc': 'R$/mês', 'sinist': 'Sinistralidade'},
                        text=df_op_custo['custo_pc'].apply(lambda x: f'R$ {x:.0f}'))
            fig = apply_layout(fig, height=380)
            fig.update_traces(textposition='outside')
            fig.update_layout(coloraxis_colorbar=dict(title="Sinist.", tickformat=".0%"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
            st.markdown("### Sinistralidade por Tipo de Contratação")
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
                        color='sinist', color_continuous_scale=[[0, '#16A34A'], [0.5, '#C9A227'], [1, '#DC2626']],
                        labels={'tipo_contratacao': '', 'custo_pc': 'R$/mês', 'sinist': 'Sinistralidade'},
                        text=df_contr['custo_pc'].apply(lambda x: f'R$ {x:.0f}'))
            fig = apply_layout(fig, height=380)
            fig.update_traces(textposition='outside')
            fig.update_layout(coloraxis_colorbar=dict(title="Sinist.", tickformat=".0%"))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Gráfico 2: Mapa de Custo por UF
        st.markdown("### Custo Per Capita por UF")
        
        # Filtro de operadora para UF
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
                        color_continuous_scale=[[0, '#5A7099'], [0.5, '#C9A227'], [1, '#DC2626']],
                        labels={'uf': 'UF', 'custo_per_capita': 'R$/mês'},
                        hover_data=['vidas', 'produtos', 'municipios'],
                        text=df_uf['custo_per_capita'].apply(lambda x: f'R${x:.0f}'))
            fig = apply_layout(fig, height=380)
            fig.update_traces(textposition='outside', textfont_size=9)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Custo per capita mensal estimado por UF. Fatores geográficos baseados em VCMH/IESS e DATASUS/SIH.")
        
        st.markdown("---")
        
        # Tabela de Produtos com Score de Risco
        st.markdown("### Ranking de Produtos por Custo Per Capita")
        st.markdown("Produtos ordenados pelo custo per capita estimado (maior risco primeiro).")
        
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
                ROUND(fator_etario_medio, 2) as "Fator Etário Médio",
                municipios as "Municípios",
                ROUND(despesa_estimada / 1e6, 2) as "Despesa Est. (R$ M)"
            FROM score_risco_produto_agg {where_score}
            ORDER BY custo_per_capita_medio DESC
            LIMIT 100
        """).df()
        
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        
        # Download
        csv_score = df_ranking.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar ranking (.csv)", csv_score, "score_risco_produtos.csv", "text/csv")
        
        st.markdown("---")
        
        # Distribuição do Score
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("### Distribuição de Custo Per Capita")
            df_hist = con.execute(f"""
                SELECT custo_per_capita_medio as custo_pc
                FROM score_risco_produto_agg {where_score}
                WHERE custo_per_capita_medio > 0
            """).df()
            
            fig = px.histogram(df_hist, x='custo_pc', nbins=40,
                              labels={'custo_pc': 'Custo Per Capita (R$/mês)', 'count': 'Produtos'},
                              color_discrete_sequence=[PRIMARY])
            fig = apply_layout(fig, height=320)
            fig.add_vline(x=df_hist['custo_pc'].median(), line_dash="dash", line_color="#C9A227",
                         annotation_text=f"Mediana: R$ {df_hist['custo_pc'].median():.0f}")
            st.plotly_chart(fig, use_container_width=True)
        
        with col_d2:
            st.markdown("### Fator Etário Médio por Segmentação")
            df_fator = con.execute(f"""
                SELECT segmentacao, AVG(fator_etario_medio) as fator_medio, SUM(vidas_total) as vidas
                FROM score_risco_produto_agg {where_score}
                GROUP BY segmentacao
                ORDER BY fator_medio DESC
            """).df()
            
            fig = px.bar(df_fator, x='segmentacao', y='fator_medio',
                        labels={'segmentacao': '', 'fator_medio': 'Fator Etário Médio'},
                        color_discrete_sequence=["#5A7099"],
                        text=df_fator['fator_medio'].apply(lambda x: f'{x:.2f}'))
            fig = apply_layout(fig, height=320)
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("""
        **Metodologia do Score de Risco:**
        O rateio distribui a despesa assistencial total (DIOPS) entre produtos proporcionalmente ao score de risco calculado:
        `Score = Vidas × Fator_Etário × Fator_Geográfico × Fator_Segmentação × Fator_Contratação`.
        Fontes: RN 63/2003 (curva etária), VCMH/IESS (geográfico), DIOPS 4T/2025 (financeiro), SIB Mar/2026 (beneficiários).
        """)
    
    except Exception as e:
        st.error(f"Erro ao carregar Score de Risco: {e}")
    
    st.markdown(f'<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 6: METODOLOGIA
# =========================================================
elif pagina == "Metodologia":
    st.markdown('<p class="main-header">Metodologia</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Modelo de cálculo, fontes de dados e limitações conhecidas</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
### Objetivo

Estimar a sinistralidade por produto a partir de dados públicos da ANS, distribuindo a despesa 
assistencial total da operadora (DIOPS) entre seus produtos cadastrados, proporcionalmente a 
fatores de risco conhecidos.

### Modelo de Cálculo

O Motor aplica a seguinte fórmula para cada produto:

```
Sinistralidade_Proxy(produto) = Sinistralidade_Total(operadora) × Peso_Relativo(produto)
```

O peso relativo é composto por quatro fatores multiplicativos:

```
Peso_Relativo = F_Segmentação × F_Contratação × F_Abrangência × F_Moderador
```
""")
    
    st.markdown("---")
    st.markdown("### Fatores de Ponderação")
    
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
        
        st.markdown("**Mecanismo de Regulação (Coparticipação)**")
        st.markdown("""
| Moderador | Fator |
|---|---|
| Coparticipação e Franquia | 0.82 |
| Franquia | 0.85 |
| Coparticipação | 0.88 |
| Ausente | 1.05 |
""")
    
    st.markdown("---")
    st.markdown("""
### Classificação de Qualidade

Cada estimativa recebe uma classificação baseada na disponibilidade de informação:

| Qualidade | Margem de Erro | Critério |
|---|---|---|
| Alta | ±8% | 3+ fatores conhecidos e dados de beneficiários disponíveis |
| Média | ±15% | 2+ fatores conhecidos |
| Baixa | ±25% | Menos de 2 fatores disponíveis |

### Limitações

1. **Viés de Mix de Carteira** — Produtos deficitários podem ser subsidiados por rentáveis dentro da mesma operadora
2. **Ausência de NTRP** — Sem acesso às premissas atuariais reais transmitidas à ANS
3. **Defasagem Temporal** — DIOPS trimestral vs SIB mensal podem ter defasagens de até 3 meses
4. **Dados Agregados** — O DIOPS não segrega despesa por produto; a alocação é estimada

### Fontes de Dados

| Fonte | Período | Frequência |
|---|---|---|
| DIOPS (Demonstrações Contábeis) | 4T/2025 | Trimestral |
| SIB Individualizado (Beneficiários) | Mar/2026 | Mensal |
| Cadastro de Produtos ANS | Mai/2026 | Contínua |
| Cadastro de Operadoras (CADOP) | Mai/2026 | Contínua |
""")
    
    st.markdown("---")
    st.markdown("""
### Roadmap de Evolução

| Sprint | Entrega | Status |
|---|---|---|
| 1 | Sinistralidade por operadora (DIOPS + SIB consolidado) | Concluído |
| 2 | Motor de proxy por produto (fatores de ponderação) | Concluído |
| 3 | Prova de conceito de granularidade (SIB individualizado) | Concluído |
| 4 | Ingestão completa do SIB individualizado — 696k registros | Concluído |
| 5 | Score de risco por produto e município (alocação atuarial) | Concluído |
| 6 | Série temporal (DIOPS 2020–2025) e tendências | Planejado |
| 7 | Modelo preditivo XGBoost | Futuro |
| 8 | API REST e interface de consulta | Futuro |
""")
    
    st.markdown(f'<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS {APP_VERSION}</div>', unsafe_allow_html=True)
