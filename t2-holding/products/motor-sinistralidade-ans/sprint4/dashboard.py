"""
Motor de Sinistralidade ANS - MVP
Dashboard Interativo (Streamlit)
Tallent Two Financial Holding
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
DB_PATH = "/home/ubuntu/mvp_sinistralidade/data/ans_analytics.duckdb"
LOGO_PATH = "/home/ubuntu/mvp_sinistralidade/logo_t2.png"

st.set_page_config(
    page_title="Motor de Sinistralidade ANS — Tallent Two",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# BRAND STYLE — TALLENT TWO DS
# =========================================================
# Cores T2
PRIMARY = "#2C3D5B"       # Navy — confiança, governança
SURFACE = "#FFF3DE"       # Bege — sofisticação, acolhimento
GOLD = "#FFD700"          # Dourado — sucesso, prestígio
GRAY = "#BEBEBE"          # Neutralidade
WHITE = "#FFFFFF"
BLACK = "#000000"
SUCCESS = "#16A34A"
WARNING = "#CA8A04"
ERROR = "#DC2626"

# Escala navy para gráficos
CHART_COLORS = ["#2C3D5B", "#3D5278", "#5A7099", "#7D92B3", "#FFD700", "#BEBEBE"]
PIE_COLORS = ["#2C3D5B", "#5A7099", "#7D92B3", "#A8B8D0", "#FFD700"]

# Custom CSS — Tallent Two Brand
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;700;800&family=Roboto:wght@300;400;500;700&display=swap');
    
    .main-header {{
        font-family: 'Playfair Display', serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: {PRIMARY};
        margin-bottom: 0;
    }}
    .sub-header {{
        font-family: 'Roboto', sans-serif;
        font-size: 1.1rem;
        color: #6B7280;
        margin-top: 0;
    }}
    .metric-card {{
        background-color: {SURFACE};
        border-left: 4px solid {PRIMARY};
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    .stMetric > div {{
        background-color: {SURFACE};
        padding: 0.8rem;
        border-radius: 0;
        border-bottom: 2px solid {PRIMARY};
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
    h1, h2, h3 {{
        font-family: 'Playfair Display', serif;
        color: {PRIMARY};
    }}
    .stDataFrame thead tr th {{
        background-color: {PRIMARY} !important;
        color: {WHITE} !important;
    }}
    .block-container {{
        font-family: 'Roboto', sans-serif;
    }}
    .t2-footer {{
        text-align: center;
        color: {GRAY};
        font-size: 0.8rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #E5E7EB;
        margin-top: 3rem;
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data
def load_operadoras_data():
    """Carrega dados consolidados das operadoras."""
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
    """Carrega dados de beneficiários."""
    con = get_connection()
    
    df_benef = con.execute("""
        SELECT 
            registro_ans,
            tipo_contratacao,
            cobertura,
            mes_competencia,
            total_beneficiarios
        FROM sib_operadoras
        ORDER BY mes_competencia
    """).df()
    
    return df_benef


@st.cache_data
def load_produtos_proxy():
    """Carrega resultados do motor de proxy."""
    con = get_connection()
    
    try:
        df = con.execute("SELECT * FROM resultado_proxy").df()
        return df
    except:
        return pd.DataFrame()


@st.cache_data
def load_produtos_detalhe():
    """Carrega detalhes dos produtos."""
    con = get_connection()
    
    try:
        df = con.execute("""
            SELECT 
                registro_ans,
                codigo_produto_ans,
                nome_produto,
                segmentacao,
                tipo_contratacao,
                cobertura,
                abrangencia,
                fator_moderador
            FROM produtos_operadoras
        """).df()
        return df
    except:
        return pd.DataFrame()


# =========================================================
# SIDEBAR — TALLENT TWO BRAND
# =========================================================
with st.sidebar:
    # Logo
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=180)
    
    st.markdown("---")
    st.markdown("### Motor de Sinistralidade")
    st.markdown("**Dados Abertos ANS**")
    st.markdown("---")
    
    # Navegação
    pagina = st.radio(
        "Navegação",
        ["Visão Geral", "Análise por Operadora", "Proxy por Produto", "🌍 Granularidade (Sprint 4)", "Metodologia"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("**Fontes de Dados:**")
    st.markdown("• DIOPS 4T/2025")
    st.markdown("• SIB Individualizado Mar/2026")
    st.markdown("• Produtos ANS")
    st.markdown(f"• **696k registros granulares**")
    st.markdown("---")
    st.markdown("*MVP v0.3 — Tallent Two*")


# =========================================================
# PÁGINA 1: VISÃO GERAL
# =========================================================
if pagina == "Visão Geral":
    st.markdown('<p class="main-header">Motor de Sinistralidade ANS</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Análise de sinistralidade baseada em dados abertos — DIOPS 4T/2025 + SIB Mar/2026</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    df_ops = load_operadoras_data()
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Operadoras Analisadas", len(df_ops))
    with col2:
        receita_total = df_ops['receita'].sum()
        st.metric("Receita Total", f"R$ {receita_total/1e9:.1f}B")
    with col3:
        sinist_media = df_ops['despesa'].sum() / df_ops['receita'].sum()
        st.metric("Sinistralidade Média Pond.", f"{sinist_media*100:.1f}%")
    with col4:
        df_benef = load_beneficiarios()
        total_vidas = df_benef[df_benef['mes_competencia'] == df_benef['mes_competencia'].max()]['total_beneficiarios'].sum()
        st.metric("Total de Vidas (SIB)", f"{total_vidas:,.0f}")
    
    st.markdown("---")
    
    # Gráfico de barras: Sinistralidade por Operadora
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("Sinistralidade por Operadora (DIOPS 4T/2025)")
        
        df_chart = df_ops.copy()
        df_chart['sinistralidade_pct'] = df_chart['sinistralidade'] * 100
        df_chart['nome_display'] = df_chart['nome_operadora'].fillna(df_chart['registro_ans'])
        
        fig = px.bar(
            df_chart.sort_values('sinistralidade_pct', ascending=True),
            x='sinistralidade_pct',
            y='nome_display',
            orientation='h',
            color='sinistralidade_pct',
            color_continuous_scale=[SUCCESS, WARNING, ERROR],
            range_color=[60, 90],
            labels={'sinistralidade_pct': 'Sinistralidade (%)', 'nome_display': ''}
        )
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            coloraxis_showscale=False,
            font=dict(family="Roboto")
        )
        fig.add_vline(x=75, line_dash="dash", line_color=ERROR, 
                      annotation_text="Alerta (75%)", annotation_position="top")
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("Composição Receita vs Despesa")
        
        df_comp = df_chart[['nome_display', 'receita', 'despesa']].copy()
        df_comp['receita_bi'] = df_comp['receita'] / 1e9
        df_comp['despesa_bi'] = df_comp['despesa'] / 1e9
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name='Receita',
            y=df_comp['nome_display'],
            x=df_comp['receita_bi'],
            orientation='h',
            marker_color=PRIMARY
        ))
        fig2.add_trace(go.Bar(
            name='Despesa Assistencial',
            y=df_comp['nome_display'],
            x=df_comp['despesa_bi'],
            orientation='h',
            marker_color=ERROR
        ))
        fig2.update_layout(
            barmode='group',
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="R$ Bilhões",
            font=dict(family="Roboto")
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela resumo
    st.subheader("Tabela Resumo")
    df_display = df_ops[['registro_ans', 'nome_operadora', 'modalidade', 'receita', 'despesa', 'sinistralidade']].copy()
    df_display.columns = ['Registro ANS', 'Operadora', 'Modalidade', 'Receita (R$)', 'Despesa Assist. (R$)', 'Sinistralidade']
    df_display['Receita (R$)'] = df_display['Receita (R$)'].apply(lambda x: f"R$ {x/1e6:,.1f}M")
    df_display['Despesa Assist. (R$)'] = df_display['Despesa Assist. (R$)'].apply(lambda x: f"R$ {x/1e6:,.1f}M")
    df_display['Sinistralidade'] = df_display['Sinistralidade'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS v0.2</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 2: ANÁLISE POR OPERADORA
# =========================================================
elif pagina == "Análise por Operadora":
    st.markdown('<p class="main-header">Análise por Operadora</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    df_ops = load_operadoras_data()
    df_benef = load_beneficiarios()
    
    # Seletor de operadora
    opcoes = df_ops['nome_operadora'].fillna(df_ops['registro_ans']).tolist()
    registros = df_ops['registro_ans'].tolist()
    
    selected_nome = st.selectbox("Selecione a Operadora:", opcoes)
    idx = opcoes.index(selected_nome)
    selected_reg = registros[idx]
    
    # Dados da operadora selecionada
    op_data = df_ops[df_ops['registro_ans'] == selected_reg].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Receita (4T/2025)", f"R$ {op_data['receita']/1e6:,.1f}M")
    with col2:
        st.metric("Despesa Assistencial", f"R$ {op_data['despesa']/1e6:,.1f}M")
    with col3:
        sinist_val = op_data['sinistralidade'] * 100
        st.metric("Sinistralidade", f"{sinist_val:.1f}%", 
                  delta=f"{'Acima de 80%' if sinist_val > 80 else 'Saudável'}")
    
    st.markdown("---")
    
    # Beneficiários
    df_benef_op = df_benef[df_benef['registro_ans'] == selected_reg]
    
    if not df_benef_op.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Distribuição por Tipo de Contratação")
            df_contrat = df_benef_op.groupby('tipo_contratacao')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_contrat, values='total_beneficiarios', names='tipo_contratacao',
                        color_discrete_sequence=PIE_COLORS)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.subheader("Distribuição por Cobertura")
            df_cob = df_benef_op.groupby('cobertura')['total_beneficiarios'].sum().reset_index()
            fig = px.pie(df_cob, values='total_beneficiarios', names='cobertura',
                        color_discrete_sequence=PIE_COLORS)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        # Evolução temporal (apenas Médico-hospitalar, filtrando meses com dados parciais)
        st.subheader("Evolução de Beneficiários (Médico-hospitalar)")
        df_med = df_benef_op[df_benef_op['cobertura'].str.contains('dico', case=False, na=False)]
        df_evol = df_med.groupby('mes_competencia')['total_beneficiarios'].sum().reset_index()
        df_evol = df_evol.sort_values('mes_competencia')
        
        # Filtrar meses anômalos (dados parciais da ANS): remover meses < 50% da mediana
        mediana = df_evol['total_beneficiarios'].median()
        df_evol = df_evol[df_evol['total_beneficiarios'] >= mediana * 0.5]
        
        # Converter YYYYMM (int) para data
        df_evol['mes_date'] = pd.to_datetime(df_evol['mes_competencia'].astype(str) + '01', format='%Y%m%d')
        df_evol = df_evol.sort_values('mes_date')
        fig = px.line(df_evol, x='mes_date', y='total_beneficiarios',
                     labels={'mes_date': 'Mês', 'total_beneficiarios': 'Beneficiários'},
                     color_discrete_sequence=[PRIMARY])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"),
                         xaxis=dict(dtick="M6", tickformat="%b/%Y"))
        fig.update_traces(mode='lines+markers', marker=dict(size=4))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("⚠️ Meses com dados parciais da ANS foram removidos automaticamente (filtro: < 50% da mediana).")
    else:
        st.info("Dados detalhados de beneficiários não disponíveis para esta operadora no dataset consolidado.")
    
    st.markdown('<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS v0.2</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 3: PROXY POR PRODUTO
# =========================================================
elif pagina == "Proxy por Produto":
    st.markdown('<p class="main-header">Proxy de Sinistralidade por Produto</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Estimativa baseada em fatores de ponderação (segmentação, contratação, abrangência, moderador)</p>', unsafe_allow_html=True)
    st.markdown("---")
    
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
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Produtos Filtrados", len(df_filtered))
        with col2:
            st.metric("Sinist. Proxy Média", f"{df_filtered['sinistralidade_proxy'].mean()*100:.1f}%")
        with col3:
            st.metric("Proxy Mínimo", f"{df_filtered['sinistralidade_proxy'].min()*100:.1f}%")
        with col4:
            st.metric("Proxy Máximo", f"{df_filtered['sinistralidade_proxy'].max()*100:.1f}%")
        
        st.markdown("---")
        
        # Distribuição
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.subheader("Distribuição da Sinistralidade Proxy")
            fig = px.histogram(
                df_filtered, 
                x=df_filtered['sinistralidade_proxy'] * 100,
                nbins=30,
                color='segmentacao',
                labels={'x': 'Sinistralidade Proxy (%)', 'count': 'Nº Produtos'},
                color_discrete_sequence=CHART_COLORS
            )
            fig.add_vline(x=75, line_dash="dash", line_color=ERROR, annotation_text="Alerta")
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.subheader("Por Tipo de Contratação")
            df_box = df_filtered.copy()
            df_box['sinistralidade_pct'] = df_box['sinistralidade_proxy'] * 100
            fig = px.box(
                df_box,
                x='tipo_contratacao',
                y='sinistralidade_pct',
                color='tipo_contratacao',
                labels={'sinistralidade_pct': 'Sinist. Proxy (%)', 'tipo_contratacao': ''},
                color_discrete_sequence=CHART_COLORS
            )
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de produtos
        st.subheader("Detalhamento por Produto")
        df_table = df_filtered[['nome_produto', 'segmentacao', 'tipo_contratacao', 
                                'abrangencia', 'fator_moderador', 'peso_calculado',
                                'sinistralidade_proxy', 'qualidade_proxy']].copy()
        df_table['sinistralidade_proxy'] = df_table['sinistralidade_proxy'].apply(lambda x: f"{x*100:.1f}%")
        df_table['peso_calculado'] = df_table['peso_calculado'].apply(lambda x: f"{x:.3f}")
        df_table.columns = ['Produto', 'Segmentação', 'Contratação', 'Abrangência', 
                           'Moderador', 'Peso', 'Sinist. Proxy', 'Qualidade']
        
        st.dataframe(
            df_table.sort_values('Sinist. Proxy', ascending=False).head(50),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown('<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS v0.2</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 4: GRANULARIDADE (SPRINT 4)
# =========================================================
elif pagina == "🌍 Granularidade (Sprint 4)":
    st.markdown('<p class="main-header">Granularidade: Produto × Município × Faixa Etária</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">SIB Individualizado Brasil — 696.183 registros de 28 UFs — Competência Mar/2026</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    try:
        con = get_connection()
        
        # Métricas gerais
        stats = con.execute("""
            SELECT 
                SUM(qt_beneficiario_ativo) as vidas,
                COUNT(DISTINCT cd_plano) as produtos,
                COUNT(DISTINCT municipio) as municipios,
                COUNT(DISTINCT registro_ans) as operadoras,
                COUNT(DISTINCT uf) as ufs
            FROM sib_granular
        """).fetchone()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("👥 Vidas Ativas", f"{stats[0]:,.0f}")
        col2.metric("📦 Produtos", f"{stats[1]:,.0f}")
        col3.metric("🏙️ Municípios", f"{stats[2]:,.0f}")
        col4.metric("🏢 Operadoras", f"{stats[3]:,.0f}")
        col5.metric("🗺️ UFs", f"{stats[4]:,.0f}")
        
        st.markdown("---")
        
        # Filtros
        st.subheader("Filtros")
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
        
        # Visão 1: Top Municípios
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.subheader("🏙️ Top 15 Municípios por Vidas")
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
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), 
                            font=dict(family="Roboto"), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.subheader("📊 Distribuição por Faixa Etária")
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
                        color_discrete_sequence=[GOLD])
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), 
                            font=dict(family="Roboto"), xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Visão 2: Heatmap UF x Segmentação
        st.subheader("🗺️ Mapa de Calor: Vidas por UF × Segmentação")
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
                           color_continuous_scale=[[0, SURFACE], [0.5, GOLD], [1, PRIMARY]],
                           aspect="auto")
            fig.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Visão 3: Tabela detalhada por Produto
        st.subheader("📦 Detalhamento por Produto")
        df_prod = con.execute(f"""
            SELECT 
                cd_plano as "Cód. Plano",
                segmentacao as "Segmentação",
                tipo_contratacao as "Contratação",
                abrangencia as "Abrangência",
                COUNT(DISTINCT municipio) as "Municípios",
                COUNT(DISTINCT uf) as "UFs",
                SUM(qt_beneficiario_ativo) as "Vidas Ativas",
                COUNT(DISTINCT faixa_etaria) as "Faixas Etárias"
            FROM sib_granular {where_sql}
            GROUP BY cd_plano, segmentacao, tipo_contratacao, abrangencia
            ORDER BY "Vidas Ativas" DESC
            LIMIT 50
        """).df()
        
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
        
        # Visão 4: Tipo de Vínculo (Titular vs Dependente)
        st.markdown("---")
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            st.subheader("👤 Titular vs Dependente")
            df_vinc = con.execute(f"""
                SELECT tipo_vinculo, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY tipo_vinculo
            """).df()
            fig = px.pie(df_vinc, values='vidas', names='tipo_vinculo',
                        color_discrete_sequence=PIE_COLORS)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_v2:
            st.subheader("📝 Tipo de Contratação")
            df_cont = con.execute(f"""
                SELECT tipo_contratacao, SUM(qt_beneficiario_ativo) as vidas
                FROM sib_granular {where_sql}
                GROUP BY tipo_contratacao
            """).df()
            fig = px.pie(df_cont, values='vidas', names='tipo_contratacao',
                        color_discrete_sequence=CHART_COLORS)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Roboto"))
            st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ **Sprint 4 Concluído!** Base granular com 696k registros de 28 UFs. Próximo: Sprint 5 (Score de Risco Atuaríal).")
        
    except Exception as e:
        st.error(f"Erro ao carregar dados granulares: {e}")
    
    st.markdown('<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS v0.3</div>', unsafe_allow_html=True)


# =========================================================
# PÁGINA 5: METODOLOGIA
# =========================================================
elif pagina == "Metodologia":
    st.markdown('<p class="main-header">Metodologia do Motor de Cálculo</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    ### Visão Geral
    
    O Motor de Sinistralidade ANS calcula uma **estimativa proxy** da sinistralidade por produto,
    partindo da sinistralidade total da operadora (dado público via DIOPS) e distribuindo-a 
    proporcionalmente entre os produtos usando fatores de ponderação baseados em literatura atuarial.
    
    ### Fórmula Base
    
    ```
    Sinistralidade_Proxy(produto) = Sinistralidade_Total(operadora) × Peso_Relativo(produto)
    ```
    
    Onde:
    ```
    Peso_Relativo = F_Segmentação × F_Contratação × F_Abrangência × F_Moderador
    ```
    
    ### Fatores de Ponderação
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Fator de Segmentação Assistencial**")
        st.markdown("""
        | Segmentação | Fator |
        |---|---|
        | Exclusivamente Odontológico | 0.40 |
        | Ambulatorial | 0.70 |
        | Hospitalar | 0.90 |
        | Ambulatorial + Hospitalar | 1.10 |
        | Referência | 1.15 |
        """)
        
        st.markdown("**Fator de Abrangência**")
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
        st.markdown("**Fator de Tipo de Contratação**")
        st.markdown("""
        | Contratação | Fator |
        |---|---|
        | Coletivo empresarial | 0.85 |
        | Coletivo por adesão | 0.95 |
        | Individual ou Familiar | 1.20 |
        """)
        
        st.markdown("**Fator de Coparticipação**")
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
    ### Qualidade do Proxy
    
    Cada estimativa recebe uma classificação de qualidade:
    
    - **Alta** (±8%): 3+ fatores conhecidos E dados de beneficiários disponíveis
    - **Média** (±15%): 2+ fatores conhecidos
    - **Baixa** (±25%): Menos de 2 fatores disponíveis
    
    ### Limitações Conhecidas
    
    1. **Viés de Mix de Carteira**: Produtos deficitários podem ser subsidiados por rentáveis dentro da mesma operadora
    2. **Ausência de NTRP**: Sem acesso às premissas atuariais reais transmitidas à ANS
    3. **Granularidade do SIB**: O dataset consolidado não detalha beneficiários por produto individual
    4. **Defasagem Temporal**: DIOPS trimestral vs SIB mensal podem ter defasagens de até 3 meses
    
    ### Fontes de Dados
    
    | Fonte | Período | Atualização |
    |---|---|---|
    | DIOPS (Demonstrações Contábeis) | 4T/2025 | Trimestral |
    | SIB (Beneficiários) | Mar/2026 | Mensal |
    | Características de Produtos | Atualizado em 19/05/2026 | Contínua |
    | Cadastro de Operadoras (CADOP) | Atualizado em 19/05/2026 | Contínua |
    """)
    
    st.markdown("---")
    st.markdown("""
    ### Roadmap — Rota 1 (Alocação Atuarial Aprimorada)
    
    | Sprint | Entrega | Status |
    |--------|---------|--------|
    | Sprint 1 | MVP base: sinistralidade por operadora (DIOPS + SIB consolidado) | ✅ Concluído |
    | Sprint 2 | Motor de proxy por produto (fatores de ponderação) | ✅ Concluído |
    | Sprint 3 | PoC de granularidade (SIB individualizado × Cadastro) | ✅ Concluído |
    | Sprint 4 | Ingestão completa do SIB individualizado (Brasil) — 696k registros | ✅ Concluído |
    | Sprint 5 | Score de risco por produto × município (alocação atuarial) | Planejado |
    | Sprint 6 | Série temporal (DIOPS 2020-2025) + tendências | Planejado |
    | Sprint 7 | Modelo preditivo XGBoost (Rota 3) | Futuro |
    | Sprint 8 | API REST + Interface de consulta | Futuro |
    """)
    
    st.markdown('<div class="t2-footer">Tallent Two Financial Holding — Motor de Sinistralidade ANS v0.2</div>', unsafe_allow_html=True)
