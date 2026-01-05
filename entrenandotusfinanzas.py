import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Entrenando tus finanzas", layout="wide", initial_sidebar_state="expanded")

# --- BLOQUE CSS BLINDADO (CERO GRIS) ---
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .main {
        background-color: #000000 !important;
    }
    h1, h2, h3, p, label, span, div, .stMarkdown {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] button svg { display: none !important; }
    [data-testid="stSidebar"] [role="button"]::before {
        content: "←"; color: #FFFFFF !important; font-size: 26px; margin-right: 15px; font-weight: bold;
    }
    [data-testid="stSidebar"] [role="button"]::after {
        content: "→"; color: #FFFFFF !important; font-size: 26px; margin-left: 15px; font-weight: bold;
    }
    input, .stSelectbox div, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    span[data-baseweb="tag"] {
        background-color: #00D4FF !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    div.stDownloadButton > button {
        background-color: #00D4FF !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border: none !important;
        width: 100% !important;
    }
    [data-testid="stMetricValue"] { color: #00D4FF !important; }
    [data-testid="stMetricDelta"] > div { color: #00FF00 !important; }
    /* Tabla sin grises */
    .stDataFrame div { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- BARRA LATERAL ---
st.sidebar.image("ETF.jfif", use_container_width=True)
st.sidebar.markdown("<h2 style='color: white;'>📊 Configuración</h2>", unsafe_allow_html=True)

moneda = st.sidebar.radio("Moneda de Visualización", ["USD (Dólares)", "ARS (Pesos)"])
tipo_cambio = 1.0
if moneda == "ARS (Pesos)":
    tipo_cambio = st.sidebar.number_input("Tipo de cambio USD/ARS", value=1200, step=10)

tickers_sugeridos = ['AAPL', 'MSFT', 'TSLA', 'MELI', 'GGAL.BA', 'BTC-USD', 'ETH-USD', 'ZC=F', 'S=F']
assets = st.sidebar.multiselect("Activos a comparar", tickers_sugeridos, default=['BTC-USD', 'MELI'])
start_date = st.sidebar.date_input("Fecha de inicio", value=pd.to_datetime("2024-01-01"))
monto_inicial_usd = st.sidebar.number_input("Monto Inicial (USD)", value=1000, step=100)
mostrar_spy = st.sidebar.toggle("Comparar vs S&P 500 (SPY)", value=True)

# --- CUERPO PRINCIPAL ---
st.title("📊 Entrenando tus finanzas")
st.subheader("Inteligencia de Mercado para la Comunidad")
st.markdown("---")

if assets:
    download_list = assets.copy()
    if mostrar_spy: download_list.append('SPY')

    with st.spinner('Actualizando datos...'):
        data = yf.download(download_list, start=start_date)['Close'].ffill().dropna()

    if not data.empty:
        simbolo = "$" if moneda == "ARS (Pesos)" else "USD"
        
        # --- RESUMEN Y MÉTRICAS ---
        resumen = []
        for asset in assets:
            p_ini, p_fin = data[asset].iloc[0], data[asset].iloc[-1]
            rend = ((p_fin / p_ini) - 1) * 100
            val_f = (p_fin / p_ini) * monto_inicial_usd * tipo_cambio
            resumen.append({"ticket": asset, "rendimiento": rend, "valor": val_f})

        resumen = sorted(resumen, key=lambda x: x['rendimiento'], reverse=True)
        
        st.subheader(f"💰 Capital Actual: {simbolo} {monto_inicial_usd * tipo_cambio:,.2f}")
        c1, c2 = st.columns(2)
        c1.success(f"🚀 **Top Ganador:** {resumen[0]['ticket']} (+{resumen[0]['rendimiento']:.2f}%)")
        c2.error(f"📉 **Bajo Desempeño:** {resumen[-1]['ticket']} ({resumen[-1]['rendimiento']:.2f}%)")
        
        cols = st.columns(len(assets))
        for i, res in enumerate(resumen):
            cols[i].metric(label=res['ticket'], value=f"{simbolo} {res['valor']:,.2f}", delta=f"{res['rendimiento']:.2f}%")

        # --- GRÁFICO DE CRECIMIENTO ---
        st.markdown("---")
        df_norm = (data / data.iloc[0]) * 100
        fig = px.line(df_norm, title="Crecimiento Comparativo (%)", color_discrete_sequence=['#00D4FF', '#FF8700', '#00FF41', '#FF007A'])
        if 'SPY' in df_norm.columns:
            fig.update_traces(line=dict(width=5, dash='dot', color='#FFD700'), selector=dict(name='SPY'))
        fig.update_layout(template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black')
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN: RIESGO VS RETORNO (¡AQUÍ ESTÁ!) ---
        st.markdown("---")
        st.subheader("⚠️ Análisis de Riesgo y Retorno")
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            # Cálculo estadístico
            returns = np.log(data[assets] / data[assets].shift(1)).dropna()
            df_stats = pd.DataFrame({
                'Activo': assets,
                'Retorno Anual (%)': returns.mean() * 252 * 100,
                'Riesgo (Volatilidad %)': returns.std() * np.sqrt(252) * 100
            })
            st.dataframe(df_stats.style.format({'Retorno Anual (%)': '{:.2f}', 'Riesgo (Volatilidad %)': '{:.2f}'}), use_container_width=True)
            
        with col_b:
            fig_risk = px.scatter(df_stats, x='Riesgo (Volatilidad %)', y='Retorno Anual (%)', text='Activo', color='Activo', size='Riesgo (Volatilidad %)', title="Matriz de Eficiencia")
            fig_risk.update_layout(template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black')
            st.plotly_chart(fig_risk, use_container_width=True)

        # --- CONSEJO Y DESCARGA ---
        st.markdown("---")
        consejos = ["💡 Diversificá para bajar el riesgo.", "💡 El interés compuesto es la octava maravilla.", "💡 Invertí solo lo que no necesites hoy."]
        st.info(np.random.choice(consejos))

        csv = data.to_csv().encode('utf-8')
        st.sidebar.markdown("---")
        st.sidebar.download_button("📥 Descargar Reporte CSV", data=csv, file_name='reporte_etf.csv')

else:
    st.info("👈 Configura tus activos en el Panel de Control.")
