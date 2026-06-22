import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN CORE Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Wheely Fog | AI Command Center", 
    page_icon="🧠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .metric-card { background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 5px solid #1a73e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .metric-title { color: #5f6368; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { color: #202124; font-size: 2rem; font-weight: 800; margin: 5px 0; }
    .seo-card { border-left: 5px solid #34a853; }
    .sem-card { border-left: 5px solid #ea4335; }
    .audit-card { border-left: 5px solid #fbbc05; background-color: #fffde7; }
    .badge-verde { background-color: #e6f4ea; color: #1e8e3e; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;}
    .badge-rojo { background-color: #fce8e6; color: #d93025; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTORES DE DATOS Y SIMULADORES API
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
    """Generador autónomo de artículos diarios basados en cruce de datos SEO."""
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
            "Ángulo Estratégico": "Ataca directamente el dolor del usuario. Remarcar el kilometraje base (100km/noche) para escapadas rápidas de fin de semana filtra clientes de alta rentabilidad."
        },
        {
            "Título Propuesto": "Análisis: Por qué el modelo Santorini es el Rey de las escapadas en pareja",
            "Keyword Objetivo": "alquilar furgoneta camper pequeña valencia",
            "Vol. Búsqueda (Mes)": "2,100",
            "Keyword Difficulty (1-100)": 38,
            "Intención": "Transaccional (Fondo de Embudo)",
            "Ángulo Estratégico": "Tráfico de muy alta conversión. Focalizado en usuarios que ya saben el segmento que quieren (Mini Van) y están comparando precios."
        }
    ]
    return pd.DataFrame(propuestas)

@st.cache_data
def load_audit_data():
    """Genera datos de auditoría profunda para Google Ads."""
    return pd.DataFrame({
        "Campaña": ["LOCAL_Rafelbunyol", "GLOBAL_Flota", "BRAND_Wheely", "RETARGETING_Comunidad", "PMAX_Verano"],
        "Estado": ["🔴 Fuga de Capital", "🟡 Revisión Sugerida", "🟢 Óptimo", "🟢 Óptimo", "🔴 Saturación de Frecuencia"],
        "Gasto Ineficiente": ["124.50 €", "45.20 €", "0.00 €", "0.00 €", "89.00 €"],
        "Diagnóstico IA": [
            "El término 'comprar camper' está consumiendo el 15% del presupuesto. Añadir a palabras clave negativas.",
            "Canibalización SEO. Estamos pagando CPC de 0.45€ en 'alquiler camper valencia' cuando ya somos Top 1 orgánico.",
            "Protección de marca funcionando al 100%. CPA por debajo de 5€.",
            "Audiencia altamente receptiva. Reactivación de clientes previos funcionando excelente.",
            "Los usuarios ven el anuncio más de 8 veces sin hacer clic (Fatiga publicitaria)."
        ]
    })

df_sem = load_sem_data()
df_hist_seo = load_seo_historical_blogs()
df_proposals = load_daily_content_proposals()
df_audit = load_audit_data()

# ==========================================
# 3. NAVEGACIÓN LATERAL (HEMISFERIOS DEL AGENTE)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1200px-Google_%22G%22_logo.svg.png", width=40)
    st.title("Wheely Fog AI")
    st.markdown("Selecciona el hemisferio estratégico que deseas operar.")
    
    hemisferio = st.radio(
        "Módulos Activos:",
        ("🛰️ SEM (Performance & Auditoría)", "📝 SEO (Content Factory & Orgánico)"),
        index=0 
    )
    
    st.divider()
    st.markdown("**Status de Integración:**")
    st.success("🟢 API Google Ads: Conectada")
    st.success("🟢 API Search Console: Conectada")
    st.success("🟢 Memoria Vectorial: Activa")

# ==========================================
# 4. HEMISFERIO 1: SEM & PERFORMANCE ESTRATÉGICO
# ==========================================
if hemisferio == "🛰️ SEM (Performance & Auditoría)":
    st.title("🛰️ Sistema Central de Performance (SEM)")
    st.markdown("Auditoría en tiempo real de Google Ads y GA4. Optimización implacable por ROAS, análisis de fugas de presupuesto y reactivación de audiencias.")
    
    # --- PESTAÑAS DEL MÓDULO SEM ---
    tab_sem1, tab_sem2, tab_sem3 = st.tabs(["📊 Dashboard General", "🕵️ Auditoría y Fugas (Escudos)", "🎯 Análisis de Audiencia (Retargeting)"])

    # ------------------------------------------
    # TAB SEM 1: DASHBOARD GENERAL
    # ------------------------------------------
    with tab_sem1:
        st.header("Rendimiento Consolidado (Últimos 30 Días)")
        col_sem1, col_sem2, col_sem3, col_sem4 = st.columns(4)
        
        coste_total = df_sem['Coste (€)'].sum()
        valor_total = df_sem['Valor (€)'].sum()
        conversiones_tot = df_sem['Conversiones'].sum()
        roas = valor_total / coste_total if coste_total > 0 else 0
        cpa = coste_total / conversiones_tot if conversiones_tot > 0 else 0
        
        with col_sem1:
            st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">Gasto Google Ads</div><div class="metric-value">{coste_total:,.2f} €</div></div>""", unsafe_allow_html=True)
        with col_sem2:
            st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">Valor Generado</div><div class="metric-value">{valor_total:,.2f} €</div></div>""", unsafe_allow_html=True)
        with col_sem3:
            st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">ROAS Total</div><div class="metric-value">{roas:.2f}x</div></div>""", unsafe_allow_html=True)
        with col_sem4:
            st.markdown(f"""<div class="metric-card sem-card"><div class="metric-title">CPA Promedio</div><div class="metric-value">{cpa:.2f} €</div></div>""", unsafe_allow_html=True)

        st.subheader("Evolución de Gasto vs Retorno")
        df_tendencia_sem = df_sem.groupby('Fecha').agg({'Coste (€)': 'sum', 'Valor (€)': 'sum'}).reset_index()
        fig_sem = go.Figure()
        fig_sem.add_trace(go.Bar(x=df_tendencia_sem['Fecha'], y=df_tendencia_sem['Coste (€)'], name='Inversión (€)', marker_color='#ea4335'))
        fig_sem.add_trace(go.Scatter(x=df_tendencia_sem['Fecha'], y=df_tendencia_sem['Valor (€)'], mode='lines+markers', name='Retorno (€)', line=dict(color='#1a73e8', width=3)))
        fig_sem.update_layout(barmode='group', hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_sem, use_container_width=True)

    # ------------------------------------------
    # TAB SEM 2: AUDITORÍA Y ESCUDOS FINANCIEROS
    # ------------------------------------------
    with tab_sem2:
        st.header("Auditoría Activa de Campañas")
        st.markdown("El Agente cruza los términos de búsqueda reales con las concordancias de Google Ads para detectar gastos ineficientes y canibalización de SEO.")
        
        # Panel de Dictamen IA
        st.markdown("### 🤖 Veredicto de Optimización")
        st.error("""
        **⚠️ Alerta Crítica Detectada en 'LOCAL_Rafelbunyol':**
        Estás perdiendo presupuesto en el clúster semántico de *compra/venta*. Usuarios buscando "comprar furgoneta" están haciendo clic en los anuncios de alquiler.
        
        **Acción Recomendada:** Inyectar una lista de palabras clave negativas en concordancia exacta y de frase: `[comprar, venta, segunda mano, concesionario]`. Esto salvará aproximadamente **124.50€** al mes que podrán reinvertirse en las campañas de Retargeting.
        """)
        
        st.divider()
        st.subheader("Panel de Control de Fugas")
        
        # Modificación de la tabla para que sea visualmente rica
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if st.button("🛡️ Aplicar Escudos vía API", type="primary"):
                st.success("Términos negativizados y CPC ajustados en tu cuenta de Google Ads con éxito.")

        st.subheader("Análisis de Términos (Top 5 Coste vs Conversión)")
        # Agrupar términos para ver cuáles gastan y no convierten
        df_terms = df_sem.groupby('Término').agg({'Coste (€)': 'sum', 'Conversiones': 'sum', 'Clics': 'sum'}).reset_index()
        df_terms['CPA'] = df_terms['Coste (€)'] / df_terms['Conversiones'].replace(0, 1)
        df_terms = df_terms.sort_values(by='Coste (€)', ascending=False).head(5)
        
        fig_terms = px.scatter(df_terms, x="Coste (€)", y="Conversiones", size="Clics", color="Término", text="Término", title="Mapa de Eficiencia de Keywords")
        fig_terms.update_traces(textposition='top center')
        st.plotly_chart(fig_terms, use_container_width=True)

    # ------------------------------------------
    # TAB SEM 3: ANÁLISIS DE AUDIENCIA / RETARGETING
    # ------------------------------------------
    with tab_sem3:
        st.header("Impacto en la Comunidad Activa (Retargeting)")
        st.markdown("Análisis exclusivo de campañas enviadas y mostradas a la **comunidad de usuarios que ya ha reservado** con nosotros previamente.")
        
        col_ret1, col_ret2 = st.columns(2)
        with col_ret1:
            st.markdown("""
            <div class="metric-card audit-card">
                <div class="metric-title">Tasa de Reactivación (LTV)</div>
                <div class="metric-value">24.5%</div>
                <div style="color: #5f6368; font-size: 0.8rem;">Usuarios antiguos que han vuelto a reservar.</div>
            </div>
            """, unsafe_allow_html=True)
        with col_ret2:
            st.markdown("""
            <div class="metric-card audit-card">
                <div class="metric-title">CPA Comunidad vs Leads Nuevos</div>
                <div class="metric-value">3.20 € vs 18.50 €</div>
                <div style="color: #5f6368; font-size: 0.8rem;">Diferencial de coste de adquisición.</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("""
        **💡 Insight Estratégico (Datos GA4):**
        Las campañas de retargeting disparadas a la base de datos de reservas previas tienen un ROAS **4 veces superior** al tráfico frío. 
        Recomiendo reactivar campañas con cupones similares al código histórico *WINTER20* (ofreciendo kilometraje ilimitado como gancho) dirigido exclusivamente a la lista de "Reservas 2025" para llenar el calendario de los meses de temporada baja.
        """)
        
        # Gráfica de Embudos comparativos
        st.subheader("Embudo de Conversión: Comunidad vs Tráfico Frío")
        funnel_data = dict(
            Pasos=['Impresión Ad', 'Clic a Web', 'Inicio de Reserva', 'Pago (Reserva Confirmada)'],
            Comunidad=[5000, 1200, 300, 150],
            Nuevos=[15000, 800, 50, 12]
        )
        fig_funnel = go.Figure()
        fig_funnel.add_trace(go.Funnel(name='Comunidad (Retargeting)', y=funnel_data['Pasos'], x=funnel_data['Comunidad'], textinfo="value+percent initial"))
        fig_funnel.add_trace(go.Funnel(name='Tráfico Nuevo (Cold)', y=funnel_data['Pasos'], x=funnel_data['Nuevos'], textinfo="value+percent initial"))
        st.plotly_chart(fig_funnel, use_container_width=True)

# ==========================================
# 5. HEMISFERIO 2: SEO & CONTENT ENGINE
# ==========================================
elif hemisferio == "📝 SEO (Content Factory & Orgánico)":
    st.title("📝 Director de Contenidos Autónomo (SEO)")
    st.markdown("El agente ingiere el histórico de éxito y redacta propuestas diarias orientadas a dominar las SERPs para atraer reservas orgánicas.")
    
    tab_seo1, tab_seo2, tab_seo3 = st.tabs(["🧠 Generación Diaria (Fábrica)", "📈 Analítica Orgánica", "📚 Ingesta Histórica (Top 50)"])
    
    # --- TAB SEO 1: FÁBRICA ---
    with tab_seo1:
        st.header("Propuestas de Publicación para Hoy")
        st.markdown(f"*Fecha de evaluación: {datetime.today().strftime('%d de %B de %Y')}*")
        
        st.markdown("### 🏆 Veredicto Estratégico del Agente IA")
        st.info("""
        **Decisión algorítmica: Se recomienda publicar la Opción 2 ("Escapadas desde Rafelbunyol: 5 destinos a menos de 100km").**
        
        **Razonamiento SEO y de Negocio (Pensamiento Crítico):**
        1. **Ratio Esfuerzo/Recompensa (KD vs Vol):** Tiene una Dificultad de Palabra Clave (KD) bajísima (15/100). Podemos posicionar este artículo en el Top 3 de Google en menos de 3 semanas.
        2. **Intención Transaccional Localizada:** Quien busca "rutas cerca de valencia" está planificando un viaje a corto plazo.
        3. **Alineación con el Modelo de Rentabilidad:** Destacar el radio de "100km" refuerza psicológicamente la rentabilidad del kilometraje base de la empresa.
        4. **Descarte de rivales:** La "Guía de climatización" trae mucho tráfico de usuarios "manitas" que camperizan, no de clientes de alquiler. Ensucia el tráfico de nuestra web.
        """)
        
        st.divider()
        st.subheader("Borradores Generados (Top 3)")
        
        for index, row in df_proposals.iterrows():
            with st.expander(f"Opción {index + 1}: {row['Título Propuesto']}"):
                colA, colB, colC = st.columns(3)
                colA.metric("Volumen Búsqueda", row['Vol. Búsqueda (Mes)'])
                kd = row['Keyword Difficulty (1-100)']
                color_kd = "🟢 Fácil" if kd < 30 else "🟡 Media" if kd < 60 else "🔴 Difícil"
                colB.metric("Dificultad (KD)", f"{kd}/100 ({color_kd})")
                colC.metric("Intención Principal", row['Intención'])
                
                st.markdown(f"**Ángulo Estratégico:** {row['Ángulo Estratégico']}")
                
                if st.button(f"Aprobar y Enviar a Web", key=f"pub_{index}"):
                    st.success(f"Artículo '{row['Título Propuesto']}' enviado al CMS (Draft) para revisión final.")
    
    # --- TAB SEO 2: ANALÍTICA ORGÁNICA ---
    with tab_seo2:
        st.header("Rendimiento Orgánico General (Search Console)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Clics Orgánicos (30d)", "14,520", "+12.4%")
        col2.metric("Impresiones en Google", "185,400", "+5.2%")
        col3.metric("Posición Media Global", "14.2", "+1.1")
        
        fechas_seo = pd.date_range(end=datetime.today(), periods=30)
        trafico_seo = np.random.normal(loc=500, scale=50, size=30) + np.arange(30) * 2
        df_trafico_seo = pd.DataFrame({"Fecha": fechas_seo, "Clics Orgánicos": trafico_seo})
        
        fig_seo = px.line(df_trafico_seo, x="Fecha", y="Clics Orgánicos", title="Evolución de Tráfico SEO (Crecimiento de Autoridad)")
        fig_seo.update_traces(line_color="#34a853", fill='tozeroy', fillcolor='rgba(52, 168, 83, 0.1)')
        st.plotly_chart(fig_seo, use_container_width=True)

    # --- TAB SEO 3: HISTÓRICO ---
    with tab_seo3:
        st.header("Memoria Base: Los 50 Pilares de Tráfico")
        st.markdown("El Agente utiliza los datos de estas URLs históricas para comprender qué temáticas resuenan mejor con la audiencia y generan la mayor **Tasa de Conversión a Reserva**.")
        st.dataframe(df_hist_seo, use_container_width=True)
        st.info("💡 **Insights Extraídos del Histórico:** Los artículos con la palabra 'Ruta' generan mucho tráfico en la parte superior del embudo, pero los artículos que mencionan restricciones (pernocta, normativa, viajar con perro) tienen una tasa de conversión a reserva 3 veces superior porque resuelven fricciones previas a la compra.")
