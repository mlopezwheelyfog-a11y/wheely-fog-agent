import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

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
col2.metric("Propuestas Pendientes", "4", "+4")
col3.metric("Estado del Agente", "Activo / Leyendo API", "OK")
st.divider()

# SECCIÓN 1: Analítica Visual y Tráfico Semanal
st.subheader("📈 Tráfico Semanal e Impacto Financiero")

# Datos simulados para tráfico de los últimos 7 días
fechas = [(datetime.today() - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
datos_trafico = pd.DataFrame({
    "Día": fechas * 2,
    "Métrica": ["Impresiones (Demanda)"]*7 + ["Clics (Tráfico Real)"]*7,
    "Volumen": [1200, 1350, 1100, 1400, 1600, 1800, 1750, 45, 52, 40, 58, 70, 85, 80]
})

datos_graficos = pd.DataFrame({
    "Vertical": ["Alquiler", "Alquiler", "Venta de Flota", "Venta de Flota"],
    "Estado del Gasto": ["Eficiente (ROAS+)", "Fuga (Término Basura)", "Eficiente (Lead Venta)", "Fuga (Término Basura)"],
    "Inversión (€)": [210, 85, 150, 45]
})

colA, colB = st.columns(2)

with colA:
    # Gráfico de líneas para tráfico semanal
    fig_line = px.line(
        datos_trafico, 
        x="Día", 
        y="Volumen", 
        color="Métrica",
        title="Evolución de Búsquedas vs Clics (Últimos 7 días)",
        markers=True,
        color_discrete_map={"Impresiones (Demanda)": "#78909c", "Clics (Tráfico Real)": "#0277bd"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

with colB:
    # Gráfico circular interactivo (Solo Fugas)
    fugas_df = datos_graficos[datos_graficos["Estado del Gasto"] == "Fuga (Término Basura)"]
    fig_pie = px.pie(
        fugas_df, 
        values="Inversión (€)", 
        names="Vertical", 
        title="Origen de Fugas de Capital (€ Perdidos)",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# SECCIÓN 2: Log de Decisiones Propuestas (Concretas)
st.subheader("🤖 Acciones Propuestas (Requieren Aprobación)")
st.markdown("Detalle exacto de la modificación que se enviará a la API de Google Ads.")

datos_propuestas = {
    "Fecha Detección": ["22/06/2026", "22/06/2026", "22/06/2026", "22/06/2026"],
    "Campaña": ["LOCAL", "Venta Flota", "LOCAL", "BRAND"],
    "ACCIÓN EXACTA": [
        "Añadir a Negativas (Frase): \"segunda mano\"", 
        "Añadir a Negativas (Frase): \"alquiler\"", 
        "Alerta: Revisar ROAS de anuncio",
        "Añadir a Negativas (Exacta): \"willy fog dibujos\""
    ],
    "Elemento Original": ["alquiler camper segunda mano", "alquiler furgoneta barata", "Modelo Santorini", "willy fog dibujos"],
    "Motivo Analítico": [
        "Intención de compra en campaña de alquiler.", 
        "Intención de alquiler en campaña de venta.", 
        "0 reservas confirmadas (evaluado sobre base 100km/noche) tras 75€ gastados.",
        "Tráfico irrelevante consumiendo presupuesto de marca."
    ],
    "Estado": ["Pendiente", "Pendiente", "Requiere Revisión", "Pendiente"]
}

df_propuestas = pd.DataFrame(datos_propuestas)
st.dataframe(df_propuestas, use_container_width=True)

colX, colY = st.columns(2)
with colX:
    if st.button("Aprobar modificaciones técnicas de hoy"):
        st.success("Acciones enviadas a la API de Google Ads.")

st.divider()

# SECCIÓN 3: Histórico de Modificaciones Realizadas
st.subheader("✅ Historial de Cambios Ejecutados (Últimos 7 días)")
st.markdown("Registro de acciones ya implementadas en la cuenta y su justificación estratégica.")

datos_historial = {
    "Fecha Ejecución": ["18/06/2026", "19/06/2026", "20/06/2026"],
    "Campaña Afectada": ["LOCAL", "LOCAL", "LOCAL"],
    "Modificación Realizada": [
        "Eliminación de Negativa: [furgoneta camper valencia]", 
        "Añadir a Negativas (Frase): \"particulares\"", 
        "Ajuste de Puja: Límite de CPA"
    ],
    "Motivo Estratégico": [
        "Estaba bloqueando demanda core en zona de influencia (Rafelbunyol).", 
        "Fuga recurrente detectada. Intención P2P incompatible con flota profesional.", 
        "Prevención de volatilidad. Crecimiento del cap limitado al +20% diario."
    ]
}

df_historial = pd.DataFrame(datos_historial)
st.dataframe(df_historial, use_container_width=True)
