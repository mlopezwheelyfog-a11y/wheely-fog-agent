import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Wheely Fog AI Command Center", layout="wide", initial_sidebar_state="collapsed")

# Cabecera
st.title("🚐 Wheely Fog | AI Command Center")
st.markdown("**Modo Sombra Activo**: Lectura de datos simulada. Las acciones requieren aprobación manual.")
st.divider()

# Creación de Pestañas (Tabs)
tab1, tab2, tab3 = st.tabs(["🛠️ Operaciones y Aprobaciones", "📊 Auditoría Ejecutiva (Presentaciones)", "🧠 Memoria y Contexto Histórico"])

with tab1:
    st.header("Sala de Máquinas: Control Diario")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gasto Ads (Últimas 24h)", "34.50 €", "-1.20 €")
    col2.metric("Propuestas Pendientes", "3", "+3")
    col3.metric("Estado del Agente", "Esperando Aprobaciones", "OK")
    
    st.subheader("🔍 Intención y Top 5 Búsquedas (Demanda en Rafelbunyol y Global)")
    col_intent, col_top = st.columns([1, 1.2])

    with col_intent:
        datos_intencion = pd.DataFrame({
            "Intención": ["Transaccional (Alta Intención)", "Informativa / Curiosidad", "Fuga (P2P/Barato)", "Navegacional (Marca)"],
            "Volumen": [45, 25, 20, 10]
        })
        fig_intent = px.pie(
            datos_intencion, values="Volumen", names="Intención", hole=0.5,
            color="Intención",
            color_discrete_map={
                "Transaccional (Alta Intención)": "#2e7b32", "Navegacional (Marca)": "#1565c0", 
                "Informativa / Curiosidad": "#ffb300", "Fuga (P2P/Barato)": "#d32f2f"
            }
        )
        st.plotly_chart(fig_intent, use_container_width=True)

    with col_top:
        datos_top = pd.DataFrame({
            "Término de Búsqueda": ["alquiler camper valencia", "comprar camper santorini", "wheely fog", "alquiler particulares", "rutas camper levante"],
            "Intención": ["Transaccional", "Transaccional", "Marca", "Fuga", "Informativa"],
            "Impresiones": [340, 185, 120, 95, 80],
            "Clics": [45, 22, 38, 15, 5]
        })
        datos_top["CTR (%)"] = ((datos_top["Clics"] / datos_top["Impresiones"]) * 100).round(1).astype(str) + "%"
        st.dataframe(datos_top, use_container_width=True)

    st.subheader("🤖 Acciones Propuestas (Requieren Aprobación)")
    datos_propuestas = {
        "Campaña": ["LOCAL", "LOCAL", "Venta Flota"],
        "ACCIÓN EXACTA": ["Negativizar (Frase): \"particulares\"", "Alerta: Revisar ROAS", "Negativizar (Frase): \"alquiler\""],
        "Motivo Analítico": ["Intención P2P en campaña profesional.", "0 reservas (base 100km/noche) tras 75€ gastados.", "Intención de alquiler en campaña de venta."],
        "Impacto Estimado": ["Ahorro: 15€/semana", "Requiere decisión humana", "Ahorro: 22€/semana"]
    }
    st.dataframe(pd.DataFrame(datos_propuestas), use_container_width=True)
    if st.button("Aprobar modificaciones técnicas", key="btn_aprobar"):
        st.success("Acciones registradas. Listas para volcar vía API.")

with tab2:
    st.header("Auditoría de Rendimiento (Vista Stakeholders)")
    st.markdown("Impacto financiero directo de las decisiones del Agente IA.")
    
    colA, colB, colC = st.columns(3)
    colA.metric("Presupuesto Salvado (Fugas Frenadas)", "142.50 €", "+12.4% vs mes anterior")
    colB.metric("CPA Real Promedio", "18.30 €", "-4.20 €")
    colC.metric("Cuota de Impresiones Perdida (Presupuesto)", "15%", "-5%")

    st.subheader("📈 Eficiencia del Gasto Semanal")
    fechas = [(datetime.today() - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    datos_roi = pd.DataFrame({
        "Día": fechas * 2,
        "Métrica": ["Gasto Bruto (€)"]*7 + ["Valor Retornado (Reserva + Seguro)"]*7,
        "Valor": [25, 30, 22, 40, 45, 50, 48, 120, 150, 0, 200, 250, 300, 280]
    })
    
    fig_roi = px.line(
        datos_roi, x="Día", y="Valor", color="Métrica", markers=True,
        color_discrete_map={"Gasto Bruto (€)": "#d32f2f", "Valor Retornado (Reserva + Seguro)": "#2e7b32"}
    )
    st.plotly_chart(fig_roi, use_container_width=True)

with tab3:
    st.header("Cerebro del Agente: Registro de Auditoría")
    st.markdown("Memoria inmutable de todas las acciones ejecutadas. (Próxima integración: Google Sheets).")
    
    st.subheader("✅ Historial de Modificaciones")
    datos_historial = {
        "Fecha Ejecución": ["18/06/2026", "20/06/2026", "21/06/2026"],
        "Autor": ["Agencia (Histórico)", "Agente IA", "Agente IA"],
        "Campaña Afectada": ["LOCAL", "LOCAL", "BRAND"],
        "Modificación Realizada": [
            "Negativizar Exacta: [furgoneta camper]", 
            "Eliminar Negativa: [furgoneta camper]",
            "Ajuste de Puja: Límite de CPA a 20€"
        ],
        "Motivo Estratégico": [
            "Desconocido / Reactivo", 
            "Estaba bloqueando demanda core en zona de influencia.",
            "Prevención de volatilidad algorítmica."
        ]
    }
    st.dataframe(pd.DataFrame(datos_historial), use_container_width=True)
