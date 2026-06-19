import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Wheely Fog AI Command Center", layout="wide")

# Cabecera
st.title("🚐 Wheely Fog | AI Command Center (Shadow Mode)")
st.markdown("Dashboard operativo del Agente Autónomo. **Modo Sombra Activo**: No se aplican cambios en Google Ads sin validación.")
st.divider()

# KPIs Simulados
st.subheader("📊 Métricas de Control Diario")
col1, col2, col3 = st.columns(3)
col1.metric("Gasto Ads (Últimas 24h)", "34.50 €", "-1.20 €")
col2.metric("Propuestas Pendientes", "3", "+3")
col3.metric("Estado del Agente", "Activo / Leyendo API", "OK")
st.divider()

# NUEVA SECCIÓN: Analítica Visual para el Equipo
st.subheader("📈 Impacto Financiero y Distribución de Presupuesto")

# Datos simulados para las gráficas
datos_graficos = pd.DataFrame({
    "Vertical": ["Alquiler", "Alquiler", "Venta de Flota", "Venta de Flota"],
    "Estado del Gasto": ["Eficiente (ROAS+)", "Fuga (Término Basura)", "Eficiente (Lead Venta)", "Fuga (Término Basura)"],
    "Inversión (€)": [210, 85, 150, 45]
})

colA, colB = st.columns(2)

with colA:
    # Gráfico de barras interactivo
    fig_bar = px.bar(
        datos_graficos, 
        x="Vertical", 
        y="Inversión (€)", 
        color="Estado del Gasto",
        title="Rendimiento de Campañas por Unidad de Negocio",
        barmode="group",
        color_discrete_map={"Eficiente (ROAS+)": "#2e7b32", "Eficiente (Lead Venta)": "#1565c0", "Fuga (Término Basura)": "#d32f2f"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with colB:
    # Gráfico circular interactivo (Solo Fugas)
    fugas_df = datos_graficos[datos_graficos["Estado del Gasto"] == "Fuga (Término Basura)"]
    fig_pie = px.pie(
        fugas_df, 
        values="Inversión (€)", 
        names="Vertical", 
        title="Origen de Fugas de Capital (Dónde perdemos dinero)",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# Log de Decisiones
st.subheader("🤖 Log de Decisiones Propuestas")

datos_prueba = {
    "Fecha": ["19/06/2026", "19/06/2026", "19/06/2026"],
    "Vertical": ["Alquiler", "Venta de Flota", "Alquiler"],
    "Tipo de Acción": ["Negativizar (Frase)", "Negativizar (Frase)", "Alerta Tracking"],
    "Elemento": ["comprar furgoneta segunda mano", "alquiler furgoneta barata", "Campaña LOCAL"],
    "Motivo": ["Búsqueda de compra en campaña de alquiler. Fuga de capital.", "Término tóxico para venta de flota premium.", "Detectadas 0 conversiones con valor dinámico > 0€."],
    "Estado": ["Pendiente", "Pendiente", "Requiere Revisión"]
}

df = pd.DataFrame(datos_prueba)
st.dataframe(df, use_container_width=True)

st.divider()

# Botones de Acción
st.subheader("⚡ Acciones de Control")
colX, colY = st.columns(2)
with colX:
    if st.button("Aprobar todas las negativizaciones de hoy"):
        st.success("Acciones aprobadas (Simulación). En vivo, esto enviaría la orden a la API de Google Ads.")
with colY:
    if st.button("Forzar recálculo de ROAS"):
        st.info("Recalculando basándose en el valor de reservas pasarela...")
