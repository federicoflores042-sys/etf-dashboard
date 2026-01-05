import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# 1. Configuración de página y Forzar Modo Oscuro
st.set_page_config(page_title="Entrenando tus finanzas", layout="wide", initial_sidebar_state="expanded")

# --- CSS DEFINITIVO PARA VISIBILIDAD ---
st.markdown("""
    <style>
    /* Fondo principal y texto general */
    .stApp { background-color: #0e1117; color: white; }
    
    /* Texto de las métricas (Celeste ETF) */
    [data-testid="stMetricValue"] { font-size: 30px; color: #00d4ff; font-weight: bold; }
    
    /* FORZAR COLOR EN EL SIDEBAR */
    section[data-testid="stSidebar"] { 
        background-color: #111827 !important; 
    }
    
    /* Forzar Blanco en: Etiquetas, Párrafos, Títulos y el texto del Toggle */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    div[data-testid="stWidgetLabel"] p,
    .st-emotion-cache-qsr96s { 
        color: #ffffff !important; 
        font-weight: bold !important;
        font-size: 1.05rem !important;
    }

    /* Estilo para el botón de descarga para que no sea gris */
    .stDownloadButton button {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #00d4ff !important;
    }
    
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL CON LOGO ---
st.sidebar.image("ETF.jfif", use_container_width=True)
st.sidebar.header("🕹️ Panel de Control")

# --- TÍTULO PRINCIPAL ---
st.title("📊 Entrenando tus finanzas")
st.subheader("Inteligencia de Mercado para la Comunidad")
st.markdown("---")

# 2. Selección de Activos en el Panel
tickers_sugeridos = ['AAPL', 'MSFT', 'TSLA', 'MELI', 'GGAL.BA', 'BTC-USD', 'ETH-USD', 'ZC=F', 'S=F']
assets = st.sidebar.multiselect("Activos a comparar", tickers_sugeridos, default=['BTC-USD', 'MELI'])
start_date = st.sidebar.date_input("Fecha de inicio", value=pd.to_datetime("2024-01-01"))
monto_inicial = st.sidebar.number_input("Monto Inicial ($)", value=1000, step=100)
# Este es el texto que ahora se verá blanco brillante
mostrar_spy = st.sidebar.toggle("Comparar vs S&P 500 (SPY)", value=True)

if assets:
    download_list = assets.copy()
    if mostrar_spy:
        download_list.append('SPY')

    with st.spinner('Sincronizando mercados...'):
        raw_data = yf.download(download_list, start=start_date)['Close']
        data = raw_data.ffill().dropna() 

    if not data.empty:
        if len(download_list) == 1:
            data = data.to_frame()
            data.columns = download_list

        # --- SECCIÓN 1: MÉTRICAS ---
        st.subheader(f"💰 Inversión proyectada: ${monto_inicial:,.2f}")
        cols = st.columns(len(assets))
        for i, asset in enumerate(assets):
            p_ini, p_fin = data[asset].iloc[0], data[asset].iloc[-1]
            val_final = (p_fin / p_ini) * monto_inicial
            rend = ((p_fin / p_ini) - 1) * 100
            cols[i].metric(label=asset, value=f"${val_final:,.2f}", delta=f"{rend:.2f}%")

        # --- SECCIÓN 2: GRÁFICO (Benchmark en Amarillo Oro) ---
        st.markdown("---")
        df_norm = (data / data.iloc[0]) * 100
        
        fig = px.line(df_norm, title="Crecimiento Comparativo (%)",
                      color_discrete_sequence=['#00d4ff', '#ff8700', '#00ff41', '#ff007a'])
        
        if 'SPY' in df_norm.columns:
            fig.update_traces(line=dict(width=5, dash='dash', color='#FFD700'), selector=dict(name='SPY'))

        fig.update_layout(template="plotly_dark", hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN 3: RIESGO VS RETORNO ---
        st.markdown("---")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.subheader("⚠️ Riesgo/Retorno")
            returns = np.log(data[assets] / data[assets].shift(1)).dropna()
            df_stats = pd.DataFrame({
                'Activo': assets,
                'Retorno Anual (%)': returns.mean() * 252 * 100,
                'Riesgo (%)': returns.std() * np.sqrt(252) * 100
            })
            st.dataframe(df_stats.style.format({
                'Retorno Anual (%)': '{:.2f}', 
                'Riesgo (%)': '{:.2f}'
            }), use_container_width=True)
            
        with col_b:
            fig_risk = px.scatter(df_stats, x='Riesgo (%)', y='Retorno Anual (%)', text='Activo',
                                  color='Activo', title="Matriz de Eficiencia")
            fig_risk.update_layout(template="plotly_dark")
            fig_risk.update_traces(marker=dict(size=20))
            st.plotly_chart(fig_risk, use_container_width=True)

        # Botón de Descarga
        csv = data.to_csv().encode('utf-8')
        st.sidebar.download_button("📥 Descargar Reporte CSV", data=csv, file_name='reporte_etf.csv')

else:
    st.info("👈 Configura tus activos en el Panel de Control.")