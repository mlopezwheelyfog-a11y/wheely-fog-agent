import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Wheely Fog AI Command Center", layout="wide")

# Cabecera
st.title("🚐 Wheely Fog | AI Command Center (Shadow Mode)")
st.markdown("Dashboard operativo del Agente Autónomo. **Modo Sombra Activo**: No se aplican cambios en Google Ads sin validación.")

st.divider()

# KPIs Simulados (Fase 1)
st.subheader("📊 Métricas de Control Diario")
col1, col2, col3 = st.columns(3)
col1.metric("Gasto Ads (Últimas 24h)", "34.50 €", "-1.20 €")
col2.metric("Propuestas Pendientes", "3", "+3")
col3.metric("Estado del Agente", "Activo / Leyendo API", "OK")

st.divider()

# Log de Decisiones (Simulado para la estructura visual)
st.subheader("🤖 Log de Decisiones Propuestas")

# Datos de prueba basados en tus reglas de negocio
datos_prueba = {
    "Fecha": ["19/06/2026", "19/06/2026", "19/06/2026"],
    "Vertical": ["Alquiler", "Venta de Flota", "Alquiler"],
    "Tipo de Acción": ["Negativizar (Frase)", "Negativizar (Frase)", "Alerta Tracking"],
    "Elemento": ["comprar furgoneta segunda mano", "alquiler furgoneta barata", "Campaña LOCAL"],
    "Motivo": ["Búsqueda de compra en campaña de alquiler. Fuga de capital.", "Término tóxico para venta de flota premium.", "Detectadas 0 conversiones con valor dinámico > 0€."],
    "Estado": ["Pendiente", "Pendiente", "Requiere Revisión"]
}

df = pd.DataFrame(datos_prueba)

# Mostrar la tabla interactiva
st.dataframe(df, use_container_width=True)

st.divider()

# Botones de Acción (Visuales por ahora)
st.subheader("⚡ Acciones de Control")
colA, colB = st.columns(2)
with colA:
    if st.button("Aprobar todas las negativizaciones de hoy"):
        st.success("Acciones aprobadas (Simulación). En vivo, esto enviaría la orden a la API de Google Ads.")
with colB:
    if st.button("Forzar recálculo de ROAS"):
        st.info("Recalculando basándose en el valor de reservas pasarela...")
