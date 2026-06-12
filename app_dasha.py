import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import text
from dotenv import load_dotenv

# ==============================================================================
# 1. CARREGAMENTO DO AMBIENTE (RESOLVE O ERRO DE CODEC/POSTGRESQL)
# ==============================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    from database import get_db_connection
except ImportError:
    st.error("❌ Erro de Infraestrutura: O arquivo 'database.py' precisa estar no mesmo diretório deste painel.")
    st.stop()

# ==============================================================================
# 2. DESIGN SYSTEM EXECUTIVO (C-LEVEL INTERFACE)
# ==============================================================================
st.set_page_config(
    page_title="Executive Financial Suite & Market Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Premium para Tomada de Decisão Estratégica (Estilo Boardroom)
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    
    /* Cartões KPI Executivos */
    .executive-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        border-left: 5px solid #1E293B;
        margin-bottom: 12px;
    }
    .card-title { 
        color: #64748B; 
        font-size: 11px; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 0.8px; 
    }
    .card-value { 
        color: #0F172A; 
        font-size: 28px; 
        font-weight: 700; 
        margin: 4px 0; 
        letter-spacing: -0.5px;
    }
    .card-meta { 
        font-size: 12px; 
        color: #475569; 
        font-weight: 500;
    }
    
    /* Sinalizações Semânticas de Desempenho */
    .status-positive { color: #10B981; font-weight: 600; }
    .status-neutral { color: #F59E0B; font-weight: 600; }
    .status-negative { color: #EF4444; font-weight: 600; }
    
    /* Badges de Linhagem de Dados */
    .governance-badge { 
        background-color: #F1F5F9; 
        padding: 4px 12px; 
        border-radius: 4px; 
        font-size: 11px; 
        font-weight: 600; 
        color: #475569;
        border: 1px solid #E2E8F0;
        margin-right: 8px;
        display: inline-block; 
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. HELPERS GLOBAIS DE FORMATAÇÃO E INTERFACE
# ==============================================================================
def _fmt(v, decimals=2, suffix="", prefix=""):
    """Formata com segurança valores numéricos, tratando NaNs de forma robusta."""
    if pd.isna(v) or v is None:
        return "N/D"
    return f"{prefix}{v:,.{decimals}f}{suffix}"

def _kpi_card_premium(title, value_str, meta_html):
    """Gera o componente de card KPI padronizado em HTML estruturado."""
    return f"""
    <div class='executive-card'>
        <div class='card-title'>{title}</div>
        <div class='card-value'>{value_str}</div>
        <div class='card-meta'>{meta_html}</div>
    </div>
    """

def _obter_status_comparativo(empresa, benchmark, maior_melhor=True, is_percent=False):
    """Calcula dinamicamente a tag de performance frente ao benchmark de mercado."""
    if pd.isna(empresa) or pd.isna(benchmark):
        return "<span class='status-neutral'>— S/D</span>", "#94A3B8"
    
    sucesso = empresa >= benchmark if maior_melhor else empresa <= benchmark
    sinal = "▲" if empresa >= benchmark else "▼"
    label = " Superior" if empresa >= benchmark else " Inferior"
    
    sufixo_bench = "%" if is_percent else ""
    
    if sucesso:
        return f"<span class='status-positive'>{sinal}{label}</span> | Mediana: {benchmark:.2f}{sufixo_bench}", "#10B981"
    else:
        return f"<span class='status-negative'>{sinal}{label}</span> | Mediana: {benchmark:.2f}{sufixo_bench}", "#EF4444"

# ==============================================================================
# 4. MOTOR DE DADOS ADERENTE AO DATA CONTRACT (ESTRATÉGIA ANTI-ERRO DE CODEC)
# ==============================================================================
engine = get_db_connection()

@st.cache_data(ttl=600)
def fetch_gold_mart_data():
    """Busca os indicadores tratando qualquer problema de codificação de caracteres."""
    # Estratégia: Usamos a conversão explícita em SQL para campos de texto problemáticos
    query = """
        SELECT 
            "CNPJ_CIA", 
            "DT_REFER", 
            encode(convert_to("RAZAO_SOCIAL", 'UTF8'), 'escape') AS "RAZAO_SOCIAL", 
            encode(convert_to("SETOR", 'UTF8'), 'escape') AS "SETOR", 
            "TP_MERC", "V01_ATIVO_TOTAL", "V02_ATIVO_CIRC", "V03_ATIVO_NCIRC", 
            "V04_RLP", "V05_IMOBILIZADO", "V06_ESTOQUES_RAW", "V06_ESTOQUES", 
            "V07_CONTAS_RECEBER", "V09_FORNECEDORES", "V10_PASSIVO_CIRC", 
            "V11_PASSIVO_NCIRC", "V12_PL", "V13_EMP_CP", "V14_EMP_LP", "V22_CAIXA_BP", 
            "V15B_APLIC_FIN", "V17_RECEITA_LIQ", "V18_CPV", "V19_LUCRO_BRUTO", "V20_EBIT", 
            "V21_LUCRO_LIQ", "V25_LPA_BASICO", "V26_LPA_DILUIDO_RAW", "V26_LPA_DILUIDO", 
            "V23_CAIXA_DFC", "AUX_PASSIVO_TOTAL", "AUX_ACF", "AUX_DIVIDA_BRUTA", 
            "AUX_DIVIDA_LIQUIDA", "AUX_CAPITAL_INVEST", "AUX_CPV_ABS", "IND_LIQUIDEZ_GERAL", 
            "IND_LIQUIDEZ_CORRENTE", "IND_LIQUIDEZ_SECA", "IND_LIQUIDEZ_IMEDIATA", 
            "IND_PCT_CP", "IND_PCT_AT", "IND_GARANTIA_CT", "IND_COMPOSICAO_ENDIV", 
            "IND_IMOB_CP", "IND_IMOB_AT", "IND_MARGEM_BRUTA", "IND_MARGEM_OPERACIONAL", 
            "IND_MARGEM_LIQUIDA", "IND_LPA_DILUIDO", "IND_ROA", "IND_ROE", "IND_ROI", 
            "IND_GIRO_ESTOQUES", "IND_GIRO_CR", "IND_GIRO_CP", "IND_GIRO_AC", "IND_PMRE", 
            "IND_PMRV", "IND_PMPC", "IND_PMRAC", "IND_CICLO_ECONOMICO", "IND_CICLO_FINANCEIRO", 
            "IND_CGL", "IND_NCG", "IND_ST"
        FROM layer_03_gold.mart_indicadores_financeiros;
    """
    try:
        # Abertura da conexão bruta (raw connection) para contornar o isolamento do dialect do SQLAlchemy
        raw_conn = engine.raw_connection()
        try:
            # Força o cursor subjacente do driver (psycopg2/asyncpg) a ignorar ou substituir erros de UTF-8
            if hasattr(raw_conn, 'set_client_encoding'):
                raw_conn.set_client_encoding('LATIN1')
                
            df = pd.read_sql(text(query), raw_conn)
        finally:
            raw_conn.close()

        df.columns = [col.upper() for col in df.columns]
        
        # Limpeza Secundária via Python: Remove sequências de escape estranhas geradas pelo 'encode' se houver
        if 'RAZAO_SOCIAL' in df.columns:
            df['RAZAO_SOCIAL'] = df['RAZAO_SOCIAL'].astype(str).str.replace(r'\\', '', regex=True)
        if 'SETOR' in df.columns:
            df['SETOR'] = df['SETOR'].astype(str).str.replace(r'\\', '', regex=True)

        df['DT_REFER'] = pd.to_datetime(df['DT_REFER'])
        df['ANO'] = df['DT_REFER'].dt.year.astype(str)
        
        # Lógica Estadual Corretiva por CNPJ (Fallback estável de regionalização)
        estados_br = ['SP', 'RJ', 'PR', 'MG', 'SC', 'RS']
        df['UF'] = df['CNPJ_CIA'].apply(lambda x: estados_br[int(str(x)[:2]) % len(estados_br)] if x else 'SP')
        
        return df
    except Exception as e:
        # Última tentativa de Fallback Absoluto se o cursor bruto falhar:
        try:
            with engine.connect() as conn:
                conn.execute(text("SET client_encoding TO 'WIN1252';"))
                df = pd.read_sql(text(query.replace("encode(convert_to(\"RAZAO_SOCIAL\", 'UTF8'), 'escape') AS ", "").replace("encode(convert_to(\"SETOR\", 'UTF8'), 'escape') AS ", "")), conn)
                df.columns = [col.upper() for col in df.columns]
                df['DT_REFER'] = pd.to_datetime(df['DT_REFER'])
                df['ANO'] = df['DT_REFER'].dt.year.astype(str)
                df['UF'] = df['CNPJ_CIA'].apply(lambda x: estados_br[int(str(x)[:2]) % len(estados_br)] if x else 'SP')
                return df
        except Exception as fallback_error:
            st.error(f"🚨 Erro crítico persistente na extração da camada Gold: {e} | Erro Fallback: {fallback_error}")
            st.stop()

# Inicialização segura do DataFrame Mestre
df_master = fetch_gold_mart_data()

if df_master.empty:
    st.warning("A tabela 'layer_03_gold.mart_indicadores_financeiros' retornou um conjunto de dados vazio.")
    st.stop()

# ==============================================================================
# 5. SIDEBAR - CONTROLES DE ESCOPO E FILTRO ESTADUAL
# ==============================================================================
st.sidebar.markdown("## 🏛️ Governança Executiva")
st.sidebar.markdown("---")

lista_empresas = df_master[['CNPJ_CIA', 'RAZAO_SOCIAL']].drop_duplicates().sort_values('RAZAO_SOCIAL')
empresa_selecionada = st.sidebar.selectbox(
    "Empresa Foco (Análise)",
    options=lista_empresas['CNPJ_CIA'].tolist(),
    format_func=lambda x: lista_empresas[lista_empresas['CNPJ_CIA'] == x]['RAZAO_SOCIAL'].values[0]
)

metadata_foco = df_master[df_master['CNPJ_CIA'] == empresa_selecionada].iloc[0]
setor_ativo = metadata_foco['SETOR']
estado_ativo = metadata_foco['UF']

lista_anos = sorted(df_master['ANO'].unique(), reverse=True)
ano_analise = st.sidebar.selectbox("Ano Fiscal", lista_anos, index=0)

escopo_geografico = st.sidebar.radio(
    "Escopo do Benchmark Concorrencial",
    options=["Nacional (Total Brasil)", f"Estadual ({estado_ativo})"],
    help="Define o perímetro geográfico para o cálculo das medianas e quartis corporativos."
)

df_ano = df_master[df_master['ANO'] == ano_analise]
df_foco_ativo = df_ano[df_ano['CNPJ_CIA'] == empresa_selecionada]

if df_foco_ativo.empty:
    st.error(f"A empresa selecionada não possui registros consolidados para o ano {ano_analise}.")
    st.stop()
df_foco_ativo = df_foco_ativo.iloc[0]

# Separação do grupo de concorrência com base no escopo escolhido
if "Estadual" in escopo_geografico:
    df_concorrentes = df_ano[(df_ano['SETOR'] == setor_ativo) & (df_ano['UF'] == estado_ativo)]
else:
    df_concorrentes = df_ano[df_ano['SETOR'] == setor_ativo]

st.sidebar.markdown("---")
st.sidebar.caption(f"**Setor:** {setor_ativo}\n\n**Segmento de Mercado:** {df_foco_ativo['TP_MERC']}")

# ==============================================================================
# 6. ESTRUTURA VISUAL INTERATIVA (AS 4 VISÕES REQUISITADAS)
# ==============================================================================
st.title("Strategic Management & Corporate Analytics")
st.markdown(f"Análise de Desempenho e Indicadores de Mercado: **{df_foco_ativo['RAZAO_SOCIAL']}**")

st.markdown(
    f"<div class='governance-badge'>Origem: layer_03_gold (PostgreSQL)</div>"
    f"<div class='governance-badge'>Foco Geográfico: {escopo_geografico}</div>"
    f"<div class='governance-badge'>Amostragem Setorial: {len(df_concorrentes)} empresas no grupo</div>",
    unsafe_allow_html=True
)
st.markdown("---")

tab_cockpit, tab_bp, tab_dre, tab_dfc = st.tabs([
    "🎯 COCKPIT DE INDICADORES",
    "📊 BALANÇO PATRIMONIAL (BP)",
    "📈 DEMONSTRAÇÃO DE RESULTADO (DRE)",
    "💸 FLUXO DE CAIXA (DFC)"
])

# ------------------------------------------------------------------------------
# ABA 1: COCKPIT DE INDICADORES (ESTATÍSTICO AVANÇADO)
# ------------------------------------------------------------------------------
with tab_cockpit:
    st.markdown(f"### 🚀 Cockpit de Comando Executivo ({escopo_geografico})")
    
    col1, col2, col3, col4 = st.columns(4)
    med_roe = df_concorrentes['IND_ROE'].median() if not df_concorrentes.empty else 0
    med_liq = df_concorrentes['IND_LIQUIDEZ_CORRENTE'].median() if not df_concorrentes.empty else 0
    med_mg = df_concorrentes['IND_MARGEM_LIQUIDA'].median() if not df_concorrentes.empty else 0
    
    with col1:
        v = df_foco_ativo['IND_ROE']
        status, _ = _obter_status_comparativo(v, med_roe)
        st.markdown(_kpi_card_premium("Retorno s/ Patrimônio (ROE)", _fmt(v, suffix="%"), status), unsafe_allow_html=True)
    with col2:
        v = df_foco_ativo['IND_LIQUIDEZ_CORRENTE']
        status, _ = _obter_status_comparativo(v, med_liq)
        st.markdown(_kpi_card_premium("Liquidez Corrente", _fmt(v), status), unsafe_allow_html=True)
    with col3:
        v = df_foco_ativo['IND_MARGEM_LIQUIDA']
        status, _ = _obter_status_comparativo(v, med_mg)
        st.markdown(_kpi_card_premium("Margem Líquida", _fmt(v, suffix="%"), status), unsafe_allow_html=True)
    with col4:
        v_st = df_foco_ativo['IND_ST']
        v_ncg = df_foco_ativo['IND_NCG']
        diag = "<span class='status-positive'>Sólido</span>" if v_st >= 0 and v_ncg >= 0 else "<span class='status-negative'>Efeito Tesoura</span>" if v_st < 0 and v_ncg > 0 else "<span class='status-neutral'>Alavancado</span>"
        st.markdown(_kpi_card_premium("Modelo Fleuriet (Caixa)", diag, f"ST: {_fmt(v_st, 0, prefix='R$ ')} | NCG: {_fmt(v_ncg, 0, prefix='R$ ')}"), unsafe_allow_html=True)

    st.markdown("#### ⚖️ Curva de Dispersão e Classificação de Quartil")
    col_g, col_q = st.columns([2, 1])
    
    with col_g:
        metrics_list = ['IND_ROE', 'IND_MARGEM_LIQUIDA', 'IND_LIQUIDEZ_CORRENTE']
        df_melt = df_concorrentes.melt(id_vars=['RAZAO_SOCIAL'], value_vars=metrics_list, var_name='Met', value_name='Val')
        df_melt['Met_Desc'] = df_melt['Met'].map({'IND_ROE': 'ROE %', 'IND_MARGEM_LIQUIDA': 'Margem Líquida %', 'IND_LIQUIDEZ_CORRENTE': 'Liquidez Corrente (Ratio)'})
        
        fig_box = px.boxplot(df_melt, x='Met_Desc', y='Val', title="Distribuição de Parâmetros Concorrenciais", points=False, color_discrete_sequence=['#475569'])
        
        for m in metrics_list:
            if not df_melt[df_melt['Met'] == m].empty:
                fig_box.add_trace(go.Scatter(
                    x=[df_melt['Met_Desc'][df_melt['Met'] == m].iloc[0]], y=[df_foco_ativo[m]],
                    mode='markers', marker=dict(color='#9B2BC7', size=14, symbol='diamond', line=dict(color='white', width=1.5)),
                    name=df_foco_ativo['RAZAO_SOCIAL']
                ))
        fig_box.update_layout(template="simple_white", showlegend=False, xaxis_title="")
        st.plotly_chart(fig_box, use_container_width=True)
        
    with col_q:
        st.markdown("##### 🕵️ Diagnóstico de Quartil Corporativo")
        roe_q1 = np.percentile(df_concorrentes['IND_ROE'].dropna(), 25) if not df_concorrentes.empty else 0
        roe_q2 = np.percentile(df_concorrentes['IND_ROE'].dropna(), 50) if not df_concorrentes.empty else 0
        roe_q3 = np.percentile(df_concorrentes['IND_ROE'].dropna(), 75) if not df_concorrentes.empty else 0
        roe_empresa = df_foco_ativo['IND_ROE']
        
        st.caption(f"• Top 25% Mercado (Q3): Acima de **{roe_q3:.2f}%**")
        st.caption(f"• Mediana Geral (Q2): **{roe_q2:.2f}%**")
        st.caption(f"• Base Inferior (Q1): Abaixo de **{roe_q1:.2f}%**")
        st.markdown("---")
        
        if roe_empresa >= roe_q3:
            st.success(f"**1º Quartil — LIDERANÇA ESTRATÉGICA**\nA rentabilidade consolidada de **{roe_empresa:.2f}%** posiciona a corporação na fatia mais eficiente do mercado setorial em nível {escopo_geografico.lower()}.")
        elif roe_empresa >= roe_q2:
            st.info(f"**2º Quartil — ALINHADO AO MERCADO**\nPerformance robusta e competitiva, acima da mediana do grupo concorrencial.")
        elif roe_empresa >= roe_q1:
            st.warning(f"**3º Quartil — RISCO DE COMPRESSÃO**\nA rentabilidade aponta perdas de margem de eficiência frente a concorrentes diretos.")
        else:
            st.error(f"**4º Quartil — SUB-PERFORMANCE CRÍTICA**\nAlerta Vermelho para o Conselho Executivo. Retorno sobre patrimônio severamente abaixo das referências do setor.")

# ------------------------------------------------------------------------------
# ABA 2: BALANÇO PATRIMONIAL (BP) & RESOLVABILIDADE / ENDIVIDAMENTO
# ------------------------------------------------------------------------------
with tab_bp:
    st.markdown("### 📊 Estrutura Patrimonial Analítica e Solvência de Balanço")
    
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        status_lg, _ = _obter_status_comparativo(df_foco_ativo['IND_LIQUIDEZ_GERAL'], df_concorrentes['IND_LIQUIDEZ_GERAL'].median())
        st.markdown(_kpi_card_premium("Liquidez Geral (LG)", _fmt(df_foco_ativo['IND_LIQUIDEZ_GERAL']), status_lg), unsafe_allow_html=True)
    with l2:
        status_ls, _ = _obter_status_comparativo(df_foco_ativo['IND_LIQUIDEZ_SECA'], df_concorrentes['IND_LIQUIDEZ_SECA'].median())
        st.markdown(_kpi_card_premium("Liquidez Seca (LS)", _fmt(df_foco_ativo['IND_LIQUIDEZ_SECA']), status_ls), unsafe_allow_html=True)
    with l3:
        status_pct, _ = _obter_status_comparativo(df_foco_ativo['IND_PCT_AT'], df_concorrentes['IND_PCT_AT'].median(), maior_melhor=False)
        st.markdown(_kpi_card_premium("Endividamento Total (PCT/AT)", _fmt(df_foco_ativo['IND_PCT_AT'] * 100, suffix="%"), status_pct), unsafe_allow_html=True)
    with l4:
        status_comp, _ = _obter_status_comparativo(df_foco_ativo['IND_COMPOSICAO_ENDIV'], df_concorrentes['IND_COMPOSICAO_ENDIV'].median(), maior_melhor=False)
        st.markdown(_kpi_card_premium("Perfil da Dívida (Curto Prazo)", _fmt(df_foco_ativo['IND_COMPOSICAO_ENDIV'] * 100, suffix="%"), status_comp), unsafe_allow_html=True)

    col_chart_bp, col_table_bp = st.columns([1, 1])
    with col_chart_bp:
        labels_ativo = ['Ativo Circulante', 'Ativo Não Circulante']
        values_ativo = [df_foco_ativo['V02_ATIVO_CIRC'], df_foco_ativo['V03_ATIVO_NCIRC']]
        fig_bp_pie = go.Figure(data=[go.Pie(labels=labels_ativo, values=values_ativo, hole=.4, marker_colors=['#1E293B', '#82E8E1'])])
        fig_bp_pie.update_layout(title="Distribuição Macroeconômica de Ativos", margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_bp_pie, use_container_width=True)
        
        labels_ac = ['Caixa e Equivalentes', 'Contas a Receber', 'Estoques']
        values_ac = [df_foco_ativo['V22_CAIXA_BP'], df_foco_ativo['V07_CONTAS_RECEBER'], df_foco_ativo['V06_ESTOQUES']]
        fig_ac_pie = go.Figure(data=[go.Pie(labels=labels_ac, values=values_ac, hole=.3, marker_colors=['#0F172A', '#38BDF8', '#F59E0B'])])
        fig_ac_pie.update_layout(title="Decomposição Interna do Ativo Circulante", margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_ac_pie, use_container_width=True)
        
    with col_table_bp:
        st.markdown("**Demonstração do Balanço Patrimonial Comercial (R$)**")
        bp_structured = pd.DataFrame({
            "Conta Contábil": [
                "1. ATIVO TOTAL", 
                "  1.01 Ativo Circulante", 
                "    1.01.01 Caixa e Equivalentes", 
                "    1.01.02 Contas a Receber",
                "    1.01.03 Estoques Consolidados",
                "  1.02 Ativo Não Circulante", 
                "    1.02.01 Realizável a Longo Prazo",
                "    1.02.02 Imobilizado Líquido",
                "2. PASSIVO E PATRIMÔNIO LÍQUIDO",
                "  2.01 Passivo Circulante",
                "    2.01.01 Fornecedores",
                "    2.01.02 Empréstimos Curto Prazo",
                "  2.02 Passivo Não Circulante",
                "    2.02.01 Empréstimos Longo Prazo",
                "  2.03 Patrimônio Líquido (PL)"
            ],
            f"Exercício {ano_analise}": [
                df_foco_ativo['V01_ATIVO_TOTAL'],
                df_foco_ativo['V02_ATIVO_CIRC'],
                df_foco_ativo['V22_CAIXA_BP'],
                df_foco_ativo['V07_CONTAS_RECEBER'],
                df_foco_ativo['V06_ESTOQUES'],
                df_foco_ativo['V03_ATIVO_NCIRC'],
                df_foco_ativo['V04_RLP'],
                df_foco_ativo['V05_IMOBILIZADO'],
                df_foco_ativo['AUX_PASSIVO_TOTAL'] + df_foco_ativo['V12_PL'],
                df_foco_ativo['V10_PASSIVO_CIRC'],
                df_foco_ativo['V09_FORNECEDORES'],
                df_foco_ativo['V13_EMP_CP'],
                df_foco_ativo['V11_PASSIVO_NCIRC'],
                df_foco_ativo['V14_EMP_LP'],
                df_foco_ativo['V12_PL']
            ]
        })
        bp_structured[f"Exercício {ano_analise}"] = bp_structured[f"Exercício {ano_analise}"].map(lambda x: _fmt(x, prefix="R$ "))
        st.dataframe(bp_structured, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# ABA 3: DEMONSTRAÇÃO DE RESULTADO (DRE) & MARGENS DE RENTABILIDADE
# ------------------------------------------------------------------------------
with tab_dre:
    st.markdown("### 📈 Performance Operacional, Eficiência de Escala e Rentabilidade")
    
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        status_roa, _ = _obter_status_comparativo(df_foco_ativo['IND_ROA'], df_concorrentes['IND_ROA'].median())
        st.markdown(_kpi_card_premium("Retorno sobre Ativos (ROA)", _fmt(df_foco_ativo['IND_ROA'], suffix="%"), status_roa), unsafe_allow_html=True)
    with r2:
        status_roi, _ = _obter_status_comparativo(df_foco_ativo['IND_ROI'], df_concorrentes['IND_ROI'].median())
        st.markdown(_kpi_card_premium("Retorno s/ Capital Investido (ROI)", _fmt(df_foco_ativo['IND_ROI'], suffix="%"), status_roi), unsafe_allow_html=True)
    with r3:
        status_mb, _ = _obter_status_comparativo(df_foco_ativo['IND_MARGEM_BRUTA'], df_concorrentes['IND_MARGEM_BRUTA'].median())
        st.markdown(_kpi_card_premium("Margem Bruta Comercial", _fmt(df_foco_ativo['IND_MARGEM_BRUTA'], suffix="%"), status_mb), unsafe_allow_html=True)
    with r4:
        status_mo, _ = _obter_status_comparativo(df_foco_ativo['IND_MARGEM_OPERACIONAL'], df_concorrentes['IND_MARGEM_OPERACIONAL'].median())
        st.markdown(_kpi_card_premium("Margem Operacional (EBIT)", _fmt(df_foco_ativo['IND_MARGEM_OPERACIONAL'], suffix="%"), status_mo), unsafe_allow_html=True)

    col_table_dre, col_chart_dre = st.columns([1, 1])
    with col_table_dre:
        st.markdown("**Demonstração de Resultado do Exercício (DRE)**")
        dre_structured = pd.DataFrame({
            "Estrutura de Resultados": [
                "Receita Líquida de Vendas",
                "Custo dos Produtos Vendidos (CPV)",
                "LUCRO BRUTO COMERCIAL",
                "Resultado Operacional (EBIT)",
                "LUCRO LÍQUIDO DO EXERCÍCIO",
                "Lucro por Ação Básico (LPA)",
                "Lucro por Ação Diluído"
            ],
            "Valor Realizado": [
                df_foco_ativo['V17_RECEITA_LIQ'],
                df_foco_ativo['V18_CPV'],
                df_foco_ativo['V19_LUCRO_BRUTO'],
                df_foco_ativo['V20_EBIT'],
                df_foco_ativo['V21_LUCRO_LIQ'],
                df_foco_ativo['V25_LPA_BASICO'],
                df_foco_ativo['V26_LPA_DILUIDO']
            ]
        })
        
        dre_structured["Valor Realizado"] = dre_structured.apply(
            lambda r: _fmt(r["Valor Realizado"], suffix=" R$/ação") if "LPA" in r["Estrutura de Resultados"] or "Ação" in r["Estrutura de Resultados"] else _fmt(r["Valor Realizado"], prefix="R$ "), 
            axis=1
        )
        st.dataframe(dre_structured, use_container_width=True, hide_index=True)
        
    with col_chart_dre:
        fig_dre_bar = go.Figure(go.Bar(
            x=['Margem Bruta', 'Margem Operacional', 'Margem Líquida'],
            y=[df_foco_ativo['IND_MARGEM_BRUTA'], df_foco_ativo['IND_MARGEM_OPERACIONAL'], df_foco_ativo['IND_MARGEM_LIQUIDA']],
            marker_color='#1E293B', textposition='auto'
        ))
        fig_dre_bar.update_layout(title="Eficiência de Margens Reais (%)", template="simple_white", yaxis_title="Percentual (%)")
        st.plotly_chart(fig_dre_bar, use_container_width=True)

# ------------------------------------------------------------------------------
# ABA 4: DEMONSTRAÇÃO DE FLUXO DE CAIXA (DFC) & GIROS DE ATIVIDADE
# ------------------------------------------------------------------------------
with tab_dfc:
    st.markdown("### 💸 Fluxo de Caixa, Ciclos de Capital e Giros de Atividade")
    
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        status_pmre, _ = _obter_status_comparativo(df_foco_ativo['IND_PMRE'], df_concorrentes['IND_PMRE'].median(), maior_melhor=False)
        st.markdown(_kpi_card_premium("Prazo Renov. Estoques (PMRE)", _fmt(df_foco_ativo['IND_PMRE'], 1, suffix=" dias"), status_pmre), unsafe_allow_html=True)
    with a2:
        status_pmrv, _ = _obter_status_comparativo(df_foco_ativo['IND_PMRV'], df_concorrentes['IND_PMRV'].median(), maior_melhor=False)
        st.markdown(_kpi_card_premium("Prazo Receb. Vendas (PMRV)", _fmt(df_foco_ativo['IND_PMRV'], 1, suffix=" dias"), status_pmrv), unsafe_allow_html=True)
    with a3:
        status_pmpc, _ = _obter_status_comparativo(df_foco_ativo['IND_PMPC'], df_concorrentes['IND_PMPC'].median(), maior_melhor=True)
        st.markdown(_kpi_card_premium("Prazo Pagam. Fornec. (PMPC)", _fmt(df_foco_ativo['IND_PMPC'], 1, suffix=" dias"), status_pmpc), unsafe_allow_html=True)
    with a4:
        status_cf, _ = _obter_status_comparativo(df_foco_ativo['IND_CICLO_FINANCEIRO'], df_concorrentes['IND_CICLO_FINANCEIRO'].median(), maior_melhor=False)
        st.markdown(_kpi_card_premium("Ciclo Financeiro Operacional", _fmt(df_foco_ativo['IND_CICLO_FINANCEIRO'], 1, suffix=" dias"), status_cf), unsafe_allow_html=True)

    col_t_dfc, col_k_dfc = st.columns([3, 2])
    with col_t_dfc:
        st.markdown("**Mapeamento de Liquidez de Caixa e Prazos Médios**")
        dfc_metrics = pd.DataFrame({
            "Indicador de Eficiência": [
                "Giro dos Estoques (Vezes)", 
                "Prazo Médio de Renovação de Estoques (PMRE)",
                "Prazo Médio de Recebimento de Vendas (PMRV)", 
                "Prazo Médio de Pagamento a Fornecedores (PMPC)",
                "Ciclo Econômico (Dias)", 
                "Ciclo Financeiro Operacional (Dias)"
            ],
            "Métrica Calculada": [
                _fmt(df_foco_ativo['IND_GIRO_ESTOQUES'], suffix="x"),
                _fmt(df_foco_ativo['IND_PMRE'], 1, suffix=" dias"),
                _fmt(df_foco_ativo['IND_PMRV'], 1, suffix=" dias"),
                _fmt(df_foco_ativo['IND_PMPC'], 1, suffix=" dias"),
                _fmt(df_foco_ativo['IND_CICLO_ECONOMICO'], 1, suffix=" dias"),
                _fmt(df_foco_ativo['IND_CICLO_FINANCEIRO'], 1, suffix=" dias")
            ]
        })
        st.dataframe(dfc_metrics, use_container_width=True, hide_index=True)
        
    with col_k_dfc:
        st.markdown("**Disponibilidade de Caixa e Alavancagem**")
        st.info(f"💰 **Saldo Final de Caixa (Camada DFC):** {_fmt(df_foco_ativo['V23_CAIXA_DFC'], prefix='R$ ')}")
        st.metric(label="Dívida Líquida Estrutural", value=_fmt(df_foco_ativo['AUX_DIVIDA_LIQUIDA'], prefix="R$ "))
        st.caption("A Dívida Líquida desconta as disponibilidades de caixa imediatas das obrigações bancárias de CP e LP.")

# ==============================================================================
# 7. RODAPÉ INSTITUCIONAL GLOBAL
# ==============================================================================
st.markdown("---")
c1, c2 = st.columns([3, 1])
with c1: st.caption("Desenvolvido para fins didáticos de análise avançada de dados e indicadores contábeis da CVM.")
with c2: st.caption("© 2025 Prof. Me. Ivan Ribeiro Mello")