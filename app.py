import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN CORE Y ESTILOS
# ==========================================
st.set_page_config(page_title="Wheely Fog | Google AI Agent", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .metric-card { background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid #1a73e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .metric-title { color: #5f6368; font-size: 0.9rem; font-weight: 500; }
    .metric-value { color: #202124; font-size: 1.8rem; font-weight: 700; margin: 5px 0; }
    .seo-card { border-left: 5px solid #34a853; }
    .sem-card { border-left: 5px solid #ea4335; }
    .badge-verde { background-color: #e6f4ea; color: #1e8e3e; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;}
    .badge-rojo { background-color: #fce8e6; color: #d93025; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTORES DE DATOS (SEM & SEO)
# ==========================================
@st.cache_data
def load_sem_data():
    """Genera dataset avanzado para SEM."""
    np.random.seed(42)
    fechas = [datetime.today() - timedelta(days=i) for i in range(30)]
    terminos = ["alquiler camper valencia", "alquiler furgoneta camper", "comprar camper segunda mano", "camperizacion valencia", "wheely fog", "camper santorini alquiler"]
    data = []
    for _ in range(300):
        idx = np.random.randint(0, len(terminos))
        impresiones = np.random.randint(50, 500)
        clics = int(impresiones * np.random.uniform(0.05, 0.20))
        coste = clics * np.random.uniform(0.50, 1.50)
        conversiones = int(clics * np.random.uniform(0.01, 0.1))
        valor = conversiones * np.random.uniform(150, 450) if conversiones > 0 else 0
        data.append({"Fecha": np.random.choice(fechas), "Término": terminos[idx], "Impresiones": impresiones, "Clics": clics, "Coste (€)": coste, "Conversiones": conversiones, "Valor (€)": valor})
    return pd.DataFrame(data)

@st.cache_data
def load_seo_historical_blogs():
    """Simula la ingesta de los 50 blogs históricos de mayor rendimiento."""
    blogs = [
        {"URL": "/rutas/costa-blanca-camper", "Tráfico (All Time)": 14500, "Palabra Clave Principal": "ruta costa blanca camper", "Posición Media": 2.4, "Tasa Conversión a Reserva": "1.2%"},
        {"URL": "/guias/normativa-pernocta-comunidad-valenciana", "Tráfico (All Time)": 12200, "Palabra Clave Principal": "pernocta comunidad valenciana", "Posición Media": 1.8, "Tasa Conversión a Reserva": "0.5%"},
        {"URL": "/modelos/diferencias-minivan-gran-volumen", "Tráfico (All Time)": 8900, "Palabra Clave Principal": "minivan vs gran volumen", "Posición Media": 3.1, "Tasa Conversión a Reserva": "2.8%"},
        {"URL": "/consejos/viajar-con-perro-autocaravana", "Tráfico (All Time)": 7400, "Palabra Clave Principal": "viajar con perro camper", "Posición Media": 4.5, "Tasa Conversión a Reserva": "3.1% (Alta Pet Friendly)"},
        {"URL": "/eventos/festivales-musica-espana-camper", "Tráfico (All Time)": 6800, "Palabra Clave Principal": "ir de festival en camper", "Posición Media": 5.2, "Tasa Conversión a Reserva": "4.5% (Pico Estacional)"}
    ]
    return pd.DataFrame(blogs)

@st.cache_data
def load_daily_content_proposals():
    """Generador autónomo de 5 artículos diarios basados en cruce de datos SEO."""
    propuestas = [
        {
            "Título Propuesto": "Ruta de los Festivales 2026: Cómo preparar tu Camper para la temporada musical",
            "Keyword Objetivo": "festivales en camper 2026",
            "Vol. Búsqueda (Mes)": "8,500",
            "Keyword Difficulty (1-100)": 24,
            "Intención": "Informativa / Concienciación de Marca",
            "Ángulo Estratégico": "Aprovechar la inminente temporada de festivales de verano para posicionar la marca. Ideal para activar promociones cruzadas o sorteos de ruleta."
        },
        {
            "Título Propuesto": "Escapadas de fin de semana desde Rafelbunyol: 5 destinos a menos de 100km",
            "Keyword Objetivo": "rutas camper cerca de valencia",
            "Vol. Búsqueda (Mes)": "4,200",
            "Keyword Difficulty (1-100)": 15,
            "Intención": "Transaccional (Decisión Base)",
            "Ángulo Estratégico": "Ataca directamente nuestra regla de oro: el cliente que busca el kilometraje base (100km/noche) para escapadas rápidas de fin de semana sin coste extra."
        },
        {
            "Título Propuesto": "Análisis: Por qué el modelo Santorini es el Rey de las escapadas en pareja",
            "Keyword Objetivo": "alquilar furgoneta camper pequeña valencia",
            "Vol. Búsqueda (Mes)": "2,100",
            "Keyword Difficulty (1-100)": 38,
            "Intención": "Transaccional (Fondo de Embudo)",
            "Ángulo Estratégico": "Tráfico de muy alta conversión. Focalizado en usuarios que ya saben el segmento que quieren (Mini Van) y están comparando precios."
        },
        {
            "Título Propuesto": "Guía de climatización: Sobrevivir al verano en camper (Importancia del aislamiento)",
            "Keyword Objetivo": "aire acondicionado camper",
            "Vol. Búsqueda (Mes)": "12,000",
            "Keyword Difficulty (1-100)": 65,
            "Intención": "Informativa / Bricolaje",
            "Ángulo Estratégico": "Alto volumen, pero intención diluida. Traerá tráfico de gente que busca camperizar por su cuenta, no alquilar."
        },
        {
            "Título Propuesto": "Dónde alquilar campers baratas en Valencia sin sorpresas en el seguro",
            "Keyword Objetivo": "alquiler camper valencia barata",
            "Vol. Búsqueda (Mes)": "5,600",
            "Keyword Difficulty (1-100)": 42,
            "Intención": "Transaccional (Buscador de Precio)",
            "Ángulo Estratégico": "Ataca el dolor del usuario (precios ocultos). Permite destacar nuestra política transparente frente a competidores o plataformas P2P."
        }
    ]
    return pd.DataFrame(propuestas)

df_sem = load_sem_data()
df_hist_seo = load_seo_historical_blogs()
df_proposals = load_daily_content_proposals()

# ==========================================
# 3. NAVEGACIÓN LATERAL (HEMISFERIOS DEL AGENTE)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1200px-Google_%22G%22_logo.svg.png", width=40)
    st.title("Wheely Fog AI")
    st.markdown("Selecciona el hemisferio estratégico que deseas operar.")
    
    hemisferio = st.radio(
        "Módulos Activos:",
        ("🛰️ SEM (Google Ads Performance)", "📝 SEO (Content Factory & Orgánico)"),
        index=1 # Empezamos en SEO por defecto para mostrarte la novedad
    )
    
    st.divider()
    st.markdown("**Status de Integración:**")
    st.success("🟢 API Google Ads: Conectada")
    st.success("🟢 API Search Console: Conectada")
    st.success("🟢 Memoria Vectorial: Activa")

# ==========================================
# 4. HEMISFERIO 1: SEO & CONTENT ENGINE
# ==========================================
if hemisferio == "📝 SEO (Content Factory & Orgánico)":
    st.title("📝 Director de Contenidos Autónomo (SEO)")
    st.markdown("El agente monitoriza la web, ingiere el histórico de éxito y redacta propuestas diarias orientadas a dominar las SERPs (Páginas de Resultados de Google) para atraer reservas orgánicas.")
    
    tab_seo1, tab_seo2, tab_seo3 = st.tabs(["🧠 Generación Diaria (Fábrica)", "📈 Analítica Orgánica", "📚 Ingesta Histórica (Top 50)"])
    
    # ------------------------------------------
    # TAB: FÁBRICA DE CONTENIDOS (EL NÚCLEO)
    # ------------------------------------------
    with tab_seo1:
        st.header("Propuestas de Publicación para Hoy")
        st.markdown(f"*Fecha de evaluación: {datetime.today().strftime('%d de %B de %Y')}*")
        
        # EL DICTAMEN DE LA IA (PENSAMIENTO CRÍTICO)
        st.markdown("### 🏆 Veredicto Estratégico del Agente IA")
        st.info("""
        **Decisión algorítmica: Se recomienda publicar la Opción 2 ("Escapadas desde Rafelbunyol: 5 destinos a menos de 100km").**
        
        **Razonamiento SEO y de Negocio (Pensamiento Crítico):**
        1. **Ratio Esfuerzo/Recompensa (KD vs Vol):** Tiene una Dificultad de Palabra Clave (KD) bajísima (15/100). Podemos posicionar este artículo en el Top 3 de Google en menos de 3 semanas sin necesidad de linkbuilding agresivo.
        2. **Intención Transaccional Localizada:** Quien busca "rutas cerca de valencia" está planificando un viaje a corto plazo. No está curioseando.
        3. **Alineación con el Modelo de Rentabilidad:** Destacar el radio de "100km" refuerza psicológicamente la rentabilidad del kilometraje base de la empresa. Atrae a un cliente que consume pocas noches, pero no gasta el motor de la furgoneta. Menos mantenimiento = Mayor LTV (Life Time Value) del vehículo.
        4. **Descarte de rivales:** La "Guía de climatización" (Opción 4) trae mucho tráfico, pero atrae a "manitas" que camperizan, no a clientes de alquiler. Ensucia el embudo de retargeting en Ads. La "Ruta de Festivales" (Opción 1) es excelente para *Brand Awareness*, pero requiere un presupuesto de promoción y redes sociales asociado para capitalizarla; recomiendo guardarla para la campaña de primavera.
        """)
        
        st.divider()
        st.subheader("Borradores Generados (Top 5)")
        
        for index, row in df_proposals.iterrows():
            with st.expander(f"Opción {index + 1}: {row['Título Propuesto']}"):
                colA, colB, colC = st.columns(3)
                colA.metric("Volumen Búsqueda", row['Vol. Búsqueda (Mes)'])
                # Lógica visual para la dificultad
                kd = row['Keyword Difficulty (1-100)']
                color_kd = "🟢 Fácil" if kd < 30 else "🟡 Media" if kd < 60 else "🔴 Difícil"
                colB.metric("Dificultad (KD)", f"{kd}/100 ({color_kd})")
                colC.metric("Intención Principal", row['Intención'])
                
                st.markdown(f"**Ángulo Estratégico (Por qué escribir esto):** {row['Ángulo Estratégico']}")
                
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button(f"Aprobar y Enviar a Web", key=f"pub_{index}"):
                        st.success(f"Artículo '{row['Título Propuesto']}' enviado al CMS (Draft) para revisión final.")
    
    # ------------------------------------------
    # TAB: ANALÍTICA ORGÁNICA
    # ------------------------------------------
    with tab_seo2:
        st.header("Rendimiento Orgánico General (Search Console)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Clics Orgánicos (30d)", "14,520", "+12.4%")
        col2.metric("Impresiones en Google", "185,400", "+5.2%")
        col3.metric("Posición Media Global", "14.2", "+1.1")
        
        # Gráfico simulado de tráfico orgánico
        fechas_seo = pd.date_range(end=datetime.today(), periods=30)
        trafico_seo = np.random.normal(loc=500, scale=50, size=30) + np.arange(30) * 2 # Tendencia al alza
        df_trafico_seo = pd.DataFrame({"Fecha": fechas_seo, "Clics Orgánicos": trafico_seo})
        
        fig_seo = px.line(df_trafico_seo, x="Fecha", y="Clics Orgánicos", title="Evolución de Tráfico SEO (Crecimiento de Autoridad)")
        fig_seo.update_traces(line_color="#34a853")
        st.plotly_chart(fig_seo, use_container_width=True)

    # ------------------------------------------
    # TAB: INGESTA HISTÓRICA
    # ------------------------------------------
    with tab_seo3:
        st.header("Memoria Base: Los 50 Pilares de Tráfico")
        st.markdown("El Agente utiliza los datos de estas URLs históricas para comprender qué temáticas resuenan mejor con la audiencia y generan la mayor **Tasa de Conversión a Reserva**, no solo clics vacíos.")
        st.dataframe(df_hist_seo, use_container_width=True)
        
        st.info("💡 **Insights Extraídos del Histórico:** Los artículos con la palabra 'Ruta' generan mucho tráfico en la parte superior del embudo, pero los artículos que mencionan restricciones (pernocta, normativa, viajar con perro) tienen una tasa de conversión a reserva de pasarela 3 veces superior porque resuelven fricciones previas a la compra.")

# ==========================================
# 5. HEMISFERIO 2: SEM & PERFORMANCE
# ==========================================
elif hemisferio == "🛰️ SEM (Google Ads Performance)":
    st.title("🛰️ Director de Performance (SEM Ads)")
    st.markdown("Control de inyección de capital en subastas de Google Ads. Optimización implacable por ROAS y protección de fugas hacia concordancia exacta ineficiente.")
    
    col_sem1, col_sem2, col_sem3 = st.columns(3)
    
    coste_total = df_sem['Coste (€)'].sum()
    valor_total = df_sem['Valor (€)'].sum()
    roas = valor_total / coste_total if coste_total > 0 else 0
    
    with col_sem1:
        st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">Inversión (Últimos 30d)</div><div class="metric-value">{coste_total:,.2f} €</div></div>""", unsafe_allow_html=True)
    with col_sem2:
        st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">Valor Retornado (Reservas)</div><div class="metric-value">{valor_total:,.2f} €</div></div>""", unsafe_allow_html=True)
    with col_sem3:
        st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">ROAS Consolidado</div><div class="metric-value">{roas:.2f}x</div></div>""", unsafe_allow_html=True)

    st.subheader("Alertas de Destrucción de Presupuesto (Acción Requerida)")
    
    alertas_sem = pd.DataFrame({
        "Campaña": ["LOCAL_Rafelbunyol", "GLOBAL_Flota", "BRAND_Wheely"],
        "Anomalía Detectada": ["Tráfico cruzado: Búsqueda de 'compra/venta'", "Pico de CPC (+45%) en 'Santorini'", "Canibalización SEO vs SEM"],
        "Solución Propuesta IA": ["Negativizar en FRASE el clúster [venta, segunda mano, comprar]", "Reducir CPA Max un 15% temporalmente", "Pausar anuncio. Ya estamos Top 1 Orgánico."],
        "Impacto (€)": ["Salva 45€/sem", "Salva 20€/sem", "Salva 80€/sem"]
    })
    
    st.data_editor(alertas_sem, use_container_width=True, hide_index=True)
    
    if st.button("Aplicar Escudos Financieros SEM"):
        st.success("Reglas de negativización y ajustes de puja inyectados vía API en Google Ads.")

    st.subheader("Evolución de Gasto vs Retorno")
    df_tendencia_sem = df_sem.groupby('Fecha').agg({'Coste (€)': 'sum', 'Valor (€)': 'sum'}).reset_index()
    fig_sem = go.Figure()
    fig_sem.add_trace(go.Bar(x=df_tendencia_sem['Fecha'], y=df_tendencia_sem['Coste (€)'], name='Inversión (€)', marker_color='#ea4335'))
    fig_sem.add_trace(go.Scatter(x=df_tendencia_sem['Fecha'], y=df_tendencia_sem['Valor (€)'], mode='lines+markers', name='Retorno (€)', line=dict(color='#1a73e8', width=3)))
    fig_sem.update_layout(barmode='group')
    st.plotly_chart(fig_sem, use_container_width=True)
import streamlit as st
import pandas as pd
import random

# --- HERRAMIENTAS (SIMULADOR DE API) ---
# Aquí es donde conectaremos Search Console y Google Ads
def tool_get_search_volume(brand_term="Wheely Fog"):
    # En el futuro, esto hará un request real a Google Search Console API
    # Simulación de datos actuales
    searches = random.randint(1200, 1500) 
    trend = "+12%"
    return {"busquedas": searches, "tendencia": trend}

def tool_get_campaign_performance():
    # Simulación de datos de Ads
    return {"roas": 3.8, "cpa": 12.50}

# --- LÓGICA DEL AGENTE ESTRATEGA ---
def get_ai_strategic_advice(query, data_brand, data_performance):
    """Aquí ocurre el pensamiento crítico. El agente cruza datos y decide."""
    
    # Lógica de Pensamiento Crítico
    if "wheely fog" in query.lower() or "marca" in query.lower():
        if int(data_brand['busquedas']) > 1000:
            return f"He detectado {data_brand['busquedas']} búsquedas de marca ({data_brand['tendencia']}). El crecimiento es sano y orgánico. Dado que el ROAS es de {data_performance['roas']}x, mi recomendación estratégica es **aumentar el presupuesto de marca un 10%**. Estamos en un punto dulce: la marca está traccionando sola y el tráfico de pago está siendo rentable."
        else:
            return "El volumen de búsqueda de marca está estancado. Antes de invertir más, sugiero revisar si estamos perdiendo impresiones por ranking."
    
    return "No tengo suficientes datos específicos para esa consulta. Por favor, especifica si quieres analizar Marca o Rendimiento de Campañas."

# --- INTERFAZ DEL CHAT ---
st.title("🛰️ Centro de Mando: Agente Operativo")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input de usuario
if prompt := st.chat_input("Pregunta al agente (ej: ¿Cómo va la marca? ¿Invertimos más?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando APIs de Google..."):
            # 1. El agente "ejecuta" las herramientas para obtener datos reales
            brand_data = tool_get_search_volume()
            ads_data = tool_get_campaign_performance()
            
            # 2. El agente procesa los datos con pensamiento crítico
            response = get_ai_strategic_advice(prompt, brand_data, ads_data)
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
