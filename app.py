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

# NUEVA SECCIÓN: Intencionalidad y Top Búsquedas
st.subheader("🔍 Análisis Estratégico: Intención y Top 5 Búsquedas")
col_intent, col_top = st.columns([1, 1.2])

with col_intent:
    # Gráfico de anillo para la intención de búsqueda
    datos_intencion = pd.DataFrame({
        "Intención": ["Transaccional (Alta Intención)", "Informativa / Curiosidad", "Fuga (P2P/Barato)", "Navegacional (Marca)"],
        "Volumen": [45, 25, 20, 10]
    })
    fig_intent = px.pie(
        datos_intencion, 
        values="Volumen", 
        names="Intención", 
        title="Distribución de Intencionalidad del Tráfico",
        hole=0.5,
        color="Intención",
        color_discrete_map={
            "Transaccional (Alta Intención)": "#2e7b32", 
            "Navegacional (Marca)": "#1565c0", 
            "Informativa / Curiosidad": "#ffb300", 
            "Fuga (P2P/Barato)": "#d32f2f"
        }
    )
    st.plotly_chart(fig_intent, use_container_width=True)

with col_top:
    st.markdown("**🏆 Top 5 Términos de Búsqueda (Últimos 7 días)**")
    datos_top = pd.DataFrame({
        "Término de Búsqueda": [
            "alquiler camper valencia", 
            "comprar camper santorini", 
            "wheely fog", 
            "alquiler furgoneta camper particulares", 
            "rutas camper comunidad valenciana"
        ],
        "Intención Asignada": ["Transaccional", "Transaccional", "Marca", "Fuga", "Informativa"],
        "Impresiones": [340, 185, 120, 95, 80],
        "Clics": [45, 22, 38, 15, 5]
    })
    
    # Calculamos el CTR automáticamente para la tabla
    datos_top["CTR (%)"] = ((datos_top["Clics"] / datos_top["Impresiones"]) * 100).round(1).astype(str) + "%"
    
    st.dataframe(datos_top, use_container_width=True)

st.divider()

# SECCIÓN 3: Log de Decisiones Propuestas
st.subheader("🤖 Acciones Propuestas (Requieren Aprobación)")
datos_propuestas = {
    "Campaña": ["LOCAL", "Venta Flota", "LOCAL"],
    "ACCIÓN EXACTA": [
        "Añadir a Negativas (Frase): \"particulares\"", 
        "Añadir a Negativas (Frase): \"alquiler\"", 
        "Alerta: Revisar ROAS de anuncio"
    ],
    "Elemento Original": ["alquiler furgoneta camper particulares", "alquiler furgoneta barata", "Modelo Santorini"],
    "Motivo Analítico": [
        "Intención P2P en campaña profesional.", 
        "Intención de alquiler en campaña de venta.", 
        "0 reservas (evaluado sobre base 100km/noche) tras 75€ gastados."
    ],
    "Estado": ["Pendiente", "Pendiente", "Requiere Revisión"]
}
st.dataframe(pd.DataFrame(datos_propuestas), use_container_width=True)

if st.button("Aprobar modificaciones técnicas de hoy"):
    st.success("Acciones enviadas a la API de Google Ads.")

st.divider()

# SECCIÓN 4: Histórico
st.subheader("✅ Historial de Cambios Ejecutados (Últimos 7 días)")
datos_historial = {
    "Fecha Ejecución": ["18/06/2026", "20/06/2026"],
    "Campaña Afectada": ["LOCAL", "LOCAL"],
    "Modificación Realizada": [
        "Eliminación de Negativa: [furgoneta camper valencia]", 
        "Ajuste de Puja: Límite de CPA"
    ],
    "Motivo Estratégico": [
        "Bloqueaba demanda en zona de influencia (Rafelbunyol).", 
        "Prevención de volatilidad. Crecimiento del cap limitado al +20%."
    ]
}
st.dataframe(pd.DataFrame(datos_historial), use_container_width=True)
