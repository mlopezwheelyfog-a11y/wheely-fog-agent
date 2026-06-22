import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN CORE DEL DASHBOARD
# ==========================================
st.set_page_config(
    page_title="Wheely Fog | Advanced SEM AI",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Avanzados para emular un entorno Google / Material Design
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1a73e8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-title { color: #5f6368; font-size: 0.9rem; font-weight: 500; }
    .metric-value { color: #202124; font-size: 1.8rem; font-weight: 700; margin: 5px 0; }
    .metric-delta.positive { color: #1e8e3e; font-size: 0.9rem; font-weight: 500;}
    .metric-delta.negative { color: #d93025; font-size: 0.9rem; font-weight: 500;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE DATOS SIMULADOS (LÓGICA WHEELY FOG)
# ==========================================
@st.cache_data
def load_historical_data():
    """Genera el dataset principal de términos de búsqueda con métricas SEM avanzadas."""
    np.random.seed(42)
    fechas = [datetime.today() - timedelta(days=i) for i in range(30)]
    
    terminos = [
        "alquiler camper valencia", "alquiler furgoneta camper", "comprar camper segunda mano",
        "camperizacion furgonetas valencia", "wheely fog", "alquiler autocaravana barata",
        "camper santorini", "furgoneta gran volumen nueva york", "willy fog alquiler",
        "alquiler camper perros permitidos", "precio camperizacion l2h2", "alquiler camper kilometraje ilimitado",
        "furgoneta camper particulares", "alquiler camper rafelbunyol", "diseño vinilos camper"
    ]
    
    verticales = ["Alquiler", "Alquiler", "Venta de Flota", "Camperización", "Marca", "Alquiler", 
                  "Alquiler", "Alquiler", "Marca", "Alquiler", "Camperización", "Alquiler", 
                  "Alquiler", "Alquiler", "Camperización"]
    
    intenciones = ["Transaccional", "Transaccional", "Fuga P2P/Compra", "Transaccional", "Navegacional", "Fuga Precio",
                   "Transaccional", "Transaccional", "Navegacional", "Transaccional", "Informativa", "Transaccional",
                   "Fuga P2P/Compra", "Transaccional", "Informativa"]
                   
    data = []
    for _ in range(500):
        idx = np.random.randint(0, len(terminos))
        impresiones = np.random.randint(10, 500)
        ctr = np.random.uniform(0.01, 0.25)
        clics = int(impresiones * ctr)
        cpc = np.random.uniform(0.20, 2.50)
        coste = clics * cpc
        
        # Lógica de conversión basada en la vertical y la intención
        cr = 0.0
        if intenciones[idx] == "Transaccional" or intenciones[idx] == "Navegacional":
            cr = np.random.uniform(0.02, 0.15)
        conversiones = int(clics * cr)
        
        # ROAS dinámico simulando pernoctas, seguro y extras (Mínimo base 100km)
        valor_conv = 0
        if conversiones > 0 and verticales[idx] == "Alquiler":
            noches = np.random.randint(3, 10)
            precio_noche = np.random.uniform(70, 150)
            seguro = np.random.choice([0, 22, 39]) # Básico, Estándar, Extra
            kit = np.random.choice([0, 49])
            mascota = np.random.choice([0, 35])
            valor_conv = conversiones * ((noches * precio_noche) + (seguro * noches) + kit + mascota)
            
        data.append({
            "Fecha": np.random.choice(fechas),
            "Término de Búsqueda": terminos[idx],
            "Vertical": verticales[idx],
            "Intención": intenciones[idx],
            "Impresiones": impresiones,
            "Clics": clics,
            "Coste (€)": round(coste, 2),
            "Conversiones": conversiones,
            "Valor Conversión (€)": round(valor_conv, 2),
            "Search Impr. Share": np.random.uniform(0.1, 0.9),
            "Quality Score": np.random.randint(3, 11)
        })
        
    df = pd.DataFrame(data)
    df["CTR (%)"] = (df["Clics"] / df["Impresiones"]) * 100
    df["CPA (€)"] = np.where(df["Conversiones"] > 0, df["Coste (€)"] / df["Conversiones"], df["Coste (€)"])
    df["ROAS"] = np.where(df["Coste (€)"] > 0, df["Valor Conversión (€)"] / df["Coste (€)"], 0)
    return df

@st.cache_data
def load_fleet_data():
    """Genera datos de ocupación y rendimiento por modelo de la flota."""
    modelos = [
        {"Modelo": "Santorini", "Segmento": "Mini Van", "Ocupación": 85},
        {"Modelo": "Kioto", "Segmento": "Mini Van", "Ocupación": 92},
        {"Modelo": "Nueva York", "Segmento": "Gran Volumen Premium", "Ocupación": 45},
        {"Modelo": "Formentera", "Segmento": "Gran Volumen Premium", "Ocupación": 60},
        {"Modelo": "La Cabaña", "Segmento": "Mini Van", "Ocupación": 78}
    ]
    return pd.DataFrame(modelos)

df_raw = load_historical_data()
df_flota = load_fleet_data()

# ==========================================
# 3. BARRA LATERAL (CONTROL GLOBAL & FILTROS)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1200px-Google_%22G%22_logo.svg.png", width=40)
    st.title("Filtros Globales")
    st.markdown("Aplica filtros multidimensionales. Todas las gráficas reaccionarán en tiempo real.")
    
    # Buscador de texto libre
    search_query = st.text_input("🔍 Buscar por Palabra Clave", placeholder="Ej. camperizacion, rafelbunyol...")
    
    # Filtros categóricos
    vertical_filter = st.multiselect("🎯 Vertical de Negocio", options=df_raw["Vertical"].unique(), default=df_raw["Vertical"].unique())
    intent_filter = st.multiselect("🧠 Intención de Búsqueda", options=df_raw["Intención"].unique(), default=df_raw["Intención"].unique())
    
    # Filtro de Rendimiento
    min_roas = st.slider("💰 ROAS Mínimo Deseado", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
    
    st.divider()
    st.markdown("**Status del Agente:**")
    st.success("🟢 Online - Leyendo API Ads")
    st.info("🧠 Memoria Histórica: Activa")

# ==========================================
# 4. APLICACIÓN DE FILTROS AL DATASET
# ==========================================
df_filtered = df_raw.copy()

if search_query:
    df_filtered = df_filtered[df_filtered["Término de Búsqueda"].str.contains(search_query, case=False, na=False)]

if vertical_filter:
    df_filtered = df_filtered[df_filtered["Vertical"].isin(vertical_filter)]

if intent_filter:
    df_filtered = df_filtered[df_filtered["Intención"].isin(intent_filter)]

df_filtered = df_filtered[df_filtered["ROAS"] >= min_roas]

# ==========================================
# 5. CÁLCULO DE KPIs DINÁMICOS
# ==========================================
total_cost = df_filtered["Coste (€)"].sum()
total_conv_value = df_filtered["Valor Conversión (€)"].sum()
total_clicks = df_filtered["Clics"].sum()
total_impressions = df_filtered["Impresiones"].sum()

global_roas = total_conv_value / total_cost if total_cost > 0 else 0
global_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
global_cpa = total_cost / df_filtered["Conversiones"].sum() if df_filtered["Conversiones"].sum() > 0 else total_cost

# Identificación de Fugas (Coste en intenciones no deseadas)
fugas_mask = df_filtered["Intención"].isin(["Fuga P2P/Compra", "Fuga Precio"])
coste_fugas = df_filtered[fugas_mask]["Coste (€)"].sum()

# ==========================================
# 6. ESTRUCTURA DE PESTAÑAS (TABS)
# ==========================================
st.title("🚀 Centro de Mando SEM Avanzado")
st.markdown("Arquitectura de control automatizado de tráfico. Decisiones basadas en ROAS dinámico de pasarela.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard Operativo", 
    "🕵️‍♂️ Inspector de Términos (Deep Dive)", 
    "🚐 Optimización de Flota", 
    "🧠 Cerebro & Aprobaciones",
    "🔬 Analítica Avanzada SEM"
])

# ------------------------------------------
# TAB 1: DASHBOARD OPERATIVO
# ------------------------------------------
with tab1:
    # Fila de KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Inversión Filtrada (€)</div>
            <div class="metric-value">{total_cost:,.2f} €</div>
            <div class="metric-delta positive">Fugas detectadas: {coste_fugas:,.2f} €</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Valor de Conversión Real</div>
            <div class="metric-value">{total_conv_value:,.2f} €</div>
            <div class="metric-title">Incluye Seguros y Kits</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">ROAS Global</div>
            <div class="metric-value">{global_roas:.2f}x</div>
            <div class="metric-delta positive">Objetivo de rentabilidad</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CPA Promedio</div>
            <div class="metric-value">{global_cpa:,.2f} €</div>
            <div class="metric-title">Coste por Reserva/Lead</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # Gráficos Principales
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        # Tendencia temporal de Coste vs Valor
        df_trend = df_filtered.groupby(df_filtered["Fecha"].dt.date).agg({
            "Coste (€)": "sum", "Valor Conversión (€)": "sum"
        }).reset_index()
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_trend["Fecha"], y=df_trend["Valor Conversión (€)"], 
                                       mode='lines+markers', name='Valor Generado (€)', line=dict(color='#1e8e3e', width=3)))
        fig_trend.add_trace(go.Bar(x=df_trend["Fecha"], y=df_trend["Coste (€)"], 
                                   name='Coste Ads (€)', marker_color='#d93025', opacity=0.6))
        fig_trend.update_layout(title="Evolución de Rendimiento (Coste vs Ingresos)",
                                plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_g2:
        # Gráfico Sunburst para desglosar Vertical -> Intención
        fig_sunburst = px.sunburst(
            df_filtered, path=['Vertical', 'Intención'], values='Coste (€)',
            title="Distribución de la Inversión (Gasto)",
            color='Intención',
            color_discrete_map={
                "Transaccional": "#2e7b32", "Navegacional": "#1565c0", 
                "Informativa": "#ffb300", "Fuga P2P/Compra": "#d32f2f", "Fuga Precio": "#c62828"
            }
        )
        fig_sunburst.update_traces(textinfo="label+percent parent")
        st.plotly_chart(fig_sunburst, use_container_width=True)

# ------------------------------------------
# TAB 2: INSPECTOR DE TÉRMINOS (DEEP DIVE)
# ------------------------------------------
with tab2:
    st.subheader("Auditoría de Términos de Búsqueda a Nivel Keyword")
    st.markdown("Utiliza el buscador lateral para aislar términos específicos. El agente evalúa cada fila.")
    
    # Matriz de Dispersión: Coste vs ROAS
    fig_scatter = px.scatter(
        df_filtered, x="Coste (€)", y="ROAS", size="Clics", color="Intención", hover_name="Término de Búsqueda",
        title="Matriz de Eficiencia: Detección de Fugas (Abajo a la derecha = Tóxico)",
        log_x=True, size_max=40,
        color_discrete_map={
                "Transaccional": "#2e7b32", "Navegacional": "#1565c0", 
                "Informativa": "#ffb300", "Fuga P2P/Compra": "#d32f2f", "Fuga Precio": "#c62828"
            }
    )
    fig_scatter.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Break-even ROAS")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Tabla dinámica de datos
    df_agrupado = df_filtered.groupby(["Término de Búsqueda", "Vertical", "Intención"]).agg({
        "Impresiones": "sum", "Clics": "sum", "Coste (€)": "sum", "Conversiones": "sum", "Valor Conversión (€)": "sum"
    }).reset_index()
    
    df_agrupado["CTR (%)"] = (df_agrupado["Clics"] / df_agrupado["Impresiones"] * 100).round(2)
    df_agrupado["ROAS"] = (df_agrupado["Valor Conversión (€)"] / df_agrupado["Coste (€)"]).round(2)
    
    st.dataframe(
        df_agrupado.sort_values(by="Coste (€)", ascending=False),
        column_config={
            "Coste (€)": st.column_config.NumberColumn(format="%.2f €"),
            "Valor Conversión (€)": st.column_config.NumberColumn(format="%.2f €"),
            "ROAS": st.column_config.NumberColumn(format="%.2fx")
        },
        use_container_width=True,
        height=400
    )

# ------------------------------------------
# TAB 3: OPTIMIZACIÓN DE FLOTA Y ROAS
# ------------------------------------------
with tab3:
    st.subheader("Integración de Lógica de Negocio y Estacionalidad")
    st.markdown("El agente IA conecta el stock de la flota con las pujas de Google Ads. Las pujas se reducen automáticamente si el modelo está cerca del 100% de ocupación para evitar malgastar presupuesto.")
    
    col_f1, col_f2 = st.columns([1, 1])
    
    with col_f1:
        st.markdown("**Estado de Ocupación por Modelo (Integración CRM)**")
        fig_bar_fleet = px.bar(
            df_flota, x="Modelo", y="Ocupación", color="Segmento",
            text="Ocupación", title="Saturación de Flota (%)",
            color_discrete_map={"Mini Van": "#0277bd", "Gran Volumen Premium": "#f57c00"}
        )
        fig_bar_fleet.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_bar_fleet.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Límite de Reducción de Puja")
        fig_bar_fleet.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig_bar_fleet, use_container_width=True)

    with col_f2:
        st.markdown("**Acciones Dinámicas de Puja Propuestas**")
        acciones_flota = []
        for index, row in df_flota.iterrows():
            if row["Ocupación"] > 80:
                accion = "Reducir Modificador de Puja (-50%)"
                motivo = "Alta ocupación. Preservar presupuesto."
                estado = "⚠️ Alerta"
            elif row["Ocupación"] < 50:
                accion = "Aumentar Puja (+20%)"
                motivo = "Baja ocupación. Empujar visibilidad."
                estado = "🟢 Impulso"
            else:
                accion = "Mantener Puja"
                motivo = "Ocupación estable."
                estado = "⚪ Estable"
                
            acciones_flota.append({"Modelo": row["Modelo"], "Acción IA": accion, "Motivo": motivo, "Status": estado})
            
        st.dataframe(pd.DataFrame(acciones_flota), use_container_width=True)

# ------------------------------------------
# TAB 4: CEREBRO & APROBACIONES (MEMORIA)
# ------------------------------------------
with tab4:
    st.subheader("Cola de Ejecución (Modo Sombra)")
    st.markdown("Revisiones estructurales propuestas por el Agente basadas en la auditoría algorítmica en tiempo real.")
    
    # Generar propuestas dinámicas basadas en los filtros actuales
    propuestas = []
    if coste_fugas > 0:
        terminos_toxicos = df_filtered[df_filtered["Intención"].str.contains("Fuga")]["Término de Búsqueda"].unique()
        for t in terminos_toxicos[:5]: # Mostrar top 5 toxicos
            propuestas.append({
                "Nivel": "Cuenta",
                "Acción Técnica": f'Añadir a lista de Negativas (Frase): "{t.split()[-1]}"',
                "Trigger Analítico": f"Intención incompatible detectada en {t}.",
                "Impacto Financiero": f"Protección activa de ROAS",
                "Aprobación": False
            })
            
    df_propuestas = pd.DataFrame(propuestas)
    
    if not df_propuestas.empty:
        df_editable = st.data_editor(
            df_propuestas,
            column_config={
                "Aprobación": st.column_config.CheckboxColumn("¿Aprobar Ejecución?", default=False)
            },
            disabled=["Nivel", "Acción Técnica", "Trigger Analítico", "Impacto Financiero"],
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("Volcar Cambios Aprobados a Google Ads API"):
            aprobados = df_editable[df_editable["Aprobación"] == True]
            if len(aprobados) > 0:
                st.success(f"Ejecutando {len(aprobados)} cambios mediante API... (Simulado)")
            else:
                st.warning("Selecciona al menos una acción para ejecutar.")
    else:
        st.info("No hay acciones estructurales pendientes bajo los filtros actuales. La cuenta está optimizada.")

    st.divider()
    st.subheader("Historial Inmutable de Cambios (Google Sheets Link)")
    st.markdown("Registro permanente de acciones de optimización para trazabilidad de equipo.")
    historial = pd.DataFrame({
        "Fecha": ["Hace 2 horas", "Hace 1 día", "Hace 1 día"],
        "Actor": ["Agente IA", "Agente IA", "Humano"],
        "Cambio": ["Ajuste Target ROAS a 350%", "Negativizar [barato]", "Pausa Anuncio A/B Test"],
        "Campaña": ["LOCAL_Alquiler", "GLOBAL_Cuenta", "Venta_Flota"]
    })
    st.dataframe(historial, use_container_width=True)

# ------------------------------------------
# TAB 5: ANALÍTICA AVANZADA SEM
# ------------------------------------------
with tab5:
    st.subheader("Evaluación Algorítmica de Calidad (Google Ads Internals)")
    st.markdown("Desglose del **Quality Score (Nivel de Calidad)** de la cuenta. Aumentar estos ratios reduce directamente el CPC que Wheely Fog paga en las subastas de Google.")
    
    col_qs1, col_qs2 = st.columns(2)
    
    with col_qs1:
        st.markdown("**Diagnóstico de Componentes QS**")
        componentes = pd.DataFrame({
            "Componente": ["CTR Esperado", "Relevancia del Anuncio", "Exp. Landing Page (Velocidad/Contenido)"],
            "Puntuación (1-10)": [6.5, 8.0, 4.5],
            "Estado": ["Promedio", "Por encima de la media", "Por debajo de la media"]
        })
        
        fig_qs = px.bar(
            componentes, x="Puntuación (1-10)", y="Componente", orientation='h',
            color="Estado", color_discrete_map={"Promedio": "#fbc02d", "Por encima de la media": "#388e3c", "Por debajo de la media": "#d32f2f"}
        )
        fig_qs.update_layout(xaxis_range=[0, 10])
        st.plotly_chart(fig_qs, use_container_width=True)
        
    with col_qs2:
        st.markdown("**Análisis de Visibilidad (Impression Share)**")
        # Simulación de pérdida de impresiones
        is_data = pd.DataFrame({
            "Métrica": ["Impr. Share Obtenido", "Perdido por Presupuesto", "Perdido por Ranking (Puja/Calidad)"],
            "Porcentaje": [65, 15, 20]
        })
        fig_is = px.pie(
            is_data, values="Porcentaje", names="Métrica", hole=0.6,
            color="Métrica", color_discrete_map={"Impr. Share Obtenido": "#1a73e8", "Perdido por Presupuesto": "#f57c00", "Perdido por Ranking (Puja/Calidad)": "#d32f2f"}
        )
        fig_is.update_traces(textinfo='percent+label', textposition='inside')
        st.plotly_chart(fig_is, use_container_width=True)
        
    st.info("💡 **Recomendación de la IA para Landing Pages:** El componente de Experiencia de Landing Page está reduciendo tu Quality Score general, encareciendo el CPC. Se recomienda optimizar el tiempo de carga de las páginas de los modelos Gran Volumen Premium y asegurar que los ganchos de 'Pet Friendly 35€' y 'Seguro Básico 0€' sean legibles en el primer pantallazo móvil (Above the fold).")
