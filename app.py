import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN CORE Y ESTILOS AVANZADOS
# ==========================================
st.set_page_config(
    page_title="Wheely Fog | AI Central Command", 
    page_icon="🧠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Inyección de CSS corporativo y limpio
st.markdown("""
    <style>
    /* Tarjetas de métricas personalizadas */
    .metric-card { 
        background-color: #ffffff; 
        border-radius: 10px; 
        padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .metric-title { 
        color: #5f6368; 
        font-size: 0.85rem; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 0.5px; 
    }
    .metric-value { 
        color: #202124; 
        font-size: 2.2rem; 
        font-weight: 800; 
        margin: 10px 0 5px 0; 
    }
    
    /* Indicadores de borde por departamento */
    .seo-card { border-left: 6px solid #34a853; }
    .sem-card { border-left: 6px solid #ea4335; }
    .cross-card { border-left: 6px solid #fbbc05; }
    .global-card { border-left: 6px solid #4285f4; }
    
    /* Badges de estado */
    .badge-status { 
        padding: 5px 10px; 
        border-radius: 6px; 
        font-size: 0.8rem; 
        font-weight: 600; 
        display: inline-block; 
    }
    .status-up { background-color: #e6f4ea; color: #1e8e3e; }
    .status-down { background-color: #fce8e6; color: #d93025; }
    </style>
""", unsafe_allow_html=True)

# Función auxiliar para renderizar métricas HTML fácilmente y ahorrar código repetitivo
def render_metric(title, value, card_type="global", delta=None, delta_type="up"):
    delta_html = ""
    if delta:
        color_class = "status-up" if delta_type == "up" else "status-down"
        icon = "↑" if delta_type == "up" else "↓"
        delta_html = f'<div class="badge-status {color_class}">{icon} {delta}</div>'
        
    html = f"""
    <div class="metric-card {card_type}-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 2. GENERADORES DE DATOS SINTÉTICOS MASIVOS
# ==========================================

@st.cache_data
def load_sem_large_dataset():
    """Genera un histórico granular de 1000 subastas de Google Ads."""
    np.random.seed(42)
    fechas = [datetime.today() - timedelta(days=i) for i in range(90)]
    
    campañas = ["LOCAL_Rafelbunyol", "GLOBAL_Flota_España", "BRAND_WheelyFog", "RETARGETING_Comunidad"]
    terminos = [
        "alquiler camper valencia", "alquiler furgoneta camper", 
        "comprar camper segunda mano", "camperizacion valencia", 
        "wheely fog", "camper santorini alquiler", "rutas camper valencia",
        "camper barata valencia", "alquiler autocaravana rafelbunyol",
        "viajar en camper 2 personas", "furgoneta camperizada alquiler"
    ]
    
    data = []
    # Generamos 1000 registros para dar peso analítico
    for _ in range(1000):
        camp = np.random.choice(campañas)
        term = np.random.choice(terminos)
        fecha = np.random.choice(fechas)
        
        # Lógica para que las campañas de marca sean más baratas y conviertan más
        if camp == "BRAND_WheelyFog":
            impresiones = np.random.randint(100, 800)
            ctr = np.random.uniform(0.15, 0.35)
            cpc = np.random.uniform(0.10, 0.30)
            cvr = np.random.uniform(0.05, 0.15)
        else:
            impresiones = np.random.randint(50, 500)
            ctr = np.random.uniform(0.02, 0.12)
            cpc = np.random.uniform(0.50, 2.10)
            cvr = np.random.uniform(0.00, 0.04)
            
        clics = int(impresiones * ctr)
        coste = clics * cpc
        conversiones = int(clics * cvr)
        
        # Ticket medio entre 150€ y 600€
        valor = conversiones * np.random.uniform(150, 600) if conversiones > 0 else 0
        
        data.append({
            "Fecha": fecha,
            "Campaña": camp,
            "Término": term, 
            "Impresiones": impresiones, 
            "Clics": clics, 
            "Coste (€)": coste, 
            "Conversiones": conversiones, 
            "Valor (€)": valor
        })
    
    df = pd.DataFrame(data)
    # Ordenar cronológicamente
    df = df.sort_values(by="Fecha", ascending=False).reset_index(drop=True)
    return df

@st.cache_data
def load_seo_large_dataset():
    """Genera la base de conocimiento de URLs y rendimiento orgánico."""
    data = [
        {"URL": "/rutas/costa-blanca-camper", "Palabra Clave Principal": "ruta costa blanca camper", "Tráfico Mensual": 4500, "Posición Media": 1.4, "Volumen Keyword": 12000, "Dificultad (KD)": 24, "Tasa Conversión": 0.018},
        {"URL": "/guias/normativa-pernocta-comunidad-valenciana", "Palabra Clave Principal": "pernocta comunidad valenciana", "Tráfico Mensual": 3800, "Posición Media": 1.2, "Volumen Keyword": 8500, "Dificultad (KD)": 15, "Tasa Conversión": 0.006},
        {"URL": "/modelos/diferencias-minivan-gran-volumen", "Palabra Clave Principal": "minivan vs gran volumen", "Tráfico Mensual": 2900, "Posición Media": 2.8, "Volumen Keyword": 4100, "Dificultad (KD)": 35, "Tasa Conversión": 0.029},
        {"URL": "/consejos/viajar-con-perro-autocaravana", "Palabra Clave Principal": "viajar con perro camper", "Tráfico Mensual": 2100, "Posición Media": 3.2, "Volumen Keyword": 5600, "Dificultad (KD)": 42, "Tasa Conversión": 0.034},
        {"URL": "/eventos/festivales-musica-espana-camper", "Palabra Clave Principal": "festivales en camper", "Tráfico Mensual": 1950, "Posición Media": 4.1, "Volumen Keyword": 9000, "Dificultad (KD)": 55, "Tasa Conversión": 0.042},
        {"URL": "/rutas/escapadas-fin-de-semana-rafelbunyol", "Palabra Clave Principal": "rutas camper cerca de valencia", "Tráfico Mensual": 1400, "Posición Media": 1.5, "Volumen Keyword": 4200, "Dificultad (KD)": 12, "Tasa Conversión": 0.025},
        {"URL": "/", "Palabra Clave Principal": "wheely fog", "Tráfico Mensual": 5000, "Posición Media": 1.0, "Volumen Keyword": 1500, "Dificultad (KD)": 5, "Tasa Conversión": 0.120},
        {"URL": "/modelos/santorini-parejas", "Palabra Clave Principal": "camper santorini alquiler", "Tráfico Mensual": 1100, "Posición Media": 2.1, "Volumen Keyword": 2100, "Dificultad (KD)": 28, "Tasa Conversión": 0.058},
        {"URL": "/blog/bricolaje-aislamiento-termico", "Palabra Clave Principal": "camperizacion valencia", "Tráfico Mensual": 850, "Posición Media": 14.5, "Volumen Keyword": 3300, "Dificultad (KD)": 65, "Tasa Conversión": 0.001},
        {"URL": "/contacto", "Palabra Clave Principal": "telefono wheely fog", "Tráfico Mensual": 300, "Posición Media": 1.1, "Volumen Keyword": 400, "Dificultad (KD)": 2, "Tasa Conversión": 0.080}
    ]
    return pd.DataFrame(data)

@st.cache_data
def load_content_proposals():
    """Generador autónomo de artículos diarios."""
    return pd.DataFrame([
        {
            "Título Propuesto": "Ruta de los Festivales 2026: Cómo preparar tu Camper para la temporada musical",
            "Keyword Objetivo": "festivales en camper 2026",
            "Vol. Búsqueda (Mes)": 8500,
            "KD": 24,
            "Intención": "Informativa / Concienciación",
            "Estrategia": "Aprovechar la inminente temporada de verano. Ideal para activar promociones cruzadas o sorteos."
        },
        {
            "Título Propuesto": "Escapadas de fin de semana desde Rafelbunyol: 5 destinos a menos de 100km",
            "Keyword Objetivo": "rutas camper cerca de valencia",
            "Vol. Búsqueda (Mes)": 4200,
            "KD": 15,
            "Intención": "Transaccional Local",
            "Estrategia": "Filtra al cliente ideal. Remarcar los 100km/noche asegura rentabilidad mecánica."
        },
        {
            "Título Propuesto": "Dónde alquilar campers baratas en Valencia sin sorpresas en el seguro",
            "Keyword Objetivo": "alquiler camper valencia barata",
            "Vol. Búsqueda (Mes)": 5600,
            "KD": 42,
            "Intención": "Transaccional / Precio",
            "Estrategia": "Atacar la transparencia frente a competidores o plataformas P2P."
        }
    ])

@st.cache_data
def load_cross_channel_matrix():
    """Matriz unificada para evaluar intersección de canales SEO y SEM."""
    return pd.DataFrame([
        {"Keyword": "alquiler camper valencia", "SEO Posición": 2.4, "SEO Tráfico": 3100, "SEM Gasto (€)": 1450.20, "SEM ROAS": 4.8, "Estado": "🔥 Rendimiento Líder", "Acción": "Mantener Inversión"},
        {"Keyword": "camper santorini alquiler", "SEO Posición": 2.1, "SEO Tráfico": 1100, "SEM Gasto (€)": 810.50, "SEM ROAS": 6.5, "Estado": "🔥 Rendimiento Líder", "Acción": "Escalar Presupuesto"},
        {"Keyword": "rutas camper cerca de valencia", "SEO Posición": 1.5, "SEO Tráfico": 1400, "SEM Gasto (€)": 285.10, "SEM ROAS": 1.2, "Estado": "🌱 Optimizar SEO", "Acción": "Reducir Puja SEM"},
        {"Keyword": "comprar camper segunda mano", "SEO Posición": 48.0, "SEO Tráfico": 5, "SEM Gasto (€)": 910.40, "SEM ROAS": 0.0, "Estado": "💸 Fuga Absoluta", "Acción": "Negativizar Exacta"},
        {"Keyword": "camperizacion valencia", "SEO Posición": 14.5, "SEO Tráfico": 80, "SEM Gasto (€)": 495.00, "SEM ROAS": 0.4, "Estado": "💸 Fuga Absoluta", "Acción": "Negativizar Frase"},
        {"Keyword": "wheely fog", "SEO Posición": 1.0, "SEO Tráfico": 5000, "SEM Gasto (€)": 145.00, "SEM ROAS": 14.2, "Estado": "🔥 Rendimiento Líder", "Acción": "Proteger Marca"},
        {"Keyword": "camper barata valencia", "SEO Posición": 9.2, "SEO Tráfico": 110, "SEM Gasto (€)": 1280.60, "SEM ROAS": 3.1, "Estado": "🌱 Optimizar SEO", "Acción": "Crear Landing SEO"}
    ])

# Cargar todos los dataframes a memoria
df_sem_raw = load_sem_large_dataset()
df_seo = load_seo_large_dataset()
df_proposals = load_content_proposals()
df_cross = load_cross_channel_matrix()

# ==========================================
# 3. BARRA LATERAL Y FILTROS GLOBALES
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1200px-Google_%22G%22_logo.svg.png", width=50)
    st.title("WheelyFog AI")
    st.markdown("Gestión integrada de canales digitales.")
    
    st.divider()
    
    # Navegación principal del Dashboard
    hemisferio = st.radio(
        "Módulos del Sistema:",
        (
            "🛰️ SEM (Performance & Subastas)", 
            "📝 SEO (Content Factory Orgánico)",
            "🔑 Auditoría Cruzada (SEO vs SEM)"
        )
    )
    
    st.divider()
    
    # Filtro global de fechas para el SEM
    st.markdown("### 📅 Filtro Temporal (SEM)")
    dias_filtro = st.slider("Rango de análisis (Días previos):", min_value=7, max_value=90, value=30, step=1)
    fecha_limite = datetime.today() - timedelta(days=dias_filtro)
    
    # Aplicar el filtro al DataFrame principal de SEM
    df_sem = df_sem_raw[pd.to_datetime(df_sem_raw['Fecha']) >= fecha_limite]
    
    st.divider()
    st.success("🟢 API Google Ads: Sincronizada")
    st.success("🟢 Search Console: Actualizada")

# ==========================================
# 4. MÓDULO SEM: PERFORMANCE Y BUSCADOR
# ==========================================
if hemisferio == "🛰️ SEM (Performance & Subastas)":
    st.title("🛰️ Director de Performance (SEM Ads)")
    st.markdown(f"Auditoría del capital inyectado en subastas. Datos filtrados para los últimos **{dias_filtro} días**.")
    
    # -- CÁLCULO DE KPIS SEM --
    total_gasto = df_sem['Coste (€)'].sum()
    total_retorno = df_sem['Valor (€)'].sum()
    total_conversiones = df_sem['Conversiones'].sum()
    
    roas_global = total_retorno / total_gasto if total_gasto > 0 else 0
    cpa_global = total_gasto / total_conversiones if total_conversiones > 0 else 0
    
    # Renderizado de Tarjetas (Usando la función auxiliar)
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1: render_metric("Gasto Total", f"{total_gasto:,.2f} €", "sem")
    with col_s2: render_metric("Retorno Generado", f"{total_retorno:,.2f} €", "sem", "+14.2%", "up")
    with col_s3: render_metric("ROAS de Cuenta", f"{roas_global:.2f}x", "sem")
    with col_s4: render_metric("CPA Promedio", f"{cpa_global:.2f} €", "sem", "-2.10 €", "up")

    st.divider()

    # -- BUSCADOR AVANZADO SEM --
    st.subheader("🔍 Motor de Búsqueda de Términos (Auditoría SEM)")
    st.markdown("Filtra el dataset completo para aislar términos específicos y auditar su rentabilidad real.")
    
    term_search = st.text_input("Introduce un término (Ej: valencia, segunda mano, santorini):")
    
    if term_search:
        df_filtered = df_sem[df_sem['Término'].str.contains(term_search, case=False, na=False)]
        if not df_filtered.empty:
            f_gasto = df_filtered['Coste (€)'].sum()
            f_retorno = df_filtered['Valor (€)'].sum()
            f_roas = f_retorno / f_gasto if f_gasto > 0 else 0
            
            # Sub-Métricas del término buscado
            st.info(f"Resultados aislados para: **'{term_search}'**")
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Gasto Acumulado", f"{f_gasto:,.2f} €")
            sc2.metric("Conversiones Logradas", df_filtered['Conversiones'].sum())
            sc3.metric("ROAS Específico", f"{f_roas:.2f}x")
            
            # Mostrar tabla detallada de ese término
            st.dataframe(df_filtered.sort_values(by="Fecha", ascending=False).head(50), use_container_width=True, hide_index=True)
        else:
            st.warning(f"No hay registros de subasta para '{term_search}' en los últimos {dias_filtro} días.")
    
    st.divider()
    
    # -- VISUALIZACIONES SEM AVANZADAS --
    tab_graf1, tab_graf2 = st.tabs(["📈 Tendencia Inversión vs Retorno", "🍩 Distribución por Campaña"])
    
    with tab_graf1:
        # Agrupar por fecha para ver tendencia
        df_trend = df_sem.groupby('Fecha').agg({'Coste (€)': 'sum', 'Valor (€)': 'sum'}).reset_index()
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=df_trend['Fecha'], y=df_trend['Coste (€)'], name='Inversión (€)', marker_color='#ea4335'))
        fig_trend.add_trace(go.Scatter(x=df_trend['Fecha'], y=df_trend['Valor (€)'], mode='lines+markers', name='Retorno (€)', line=dict(color='#1a73e8', width=3)))
        fig_trend.update_layout(barmode='group', hovermode="x unified", title="Evolución Diaria del Margen")
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with tab_graf2:
        # Agrupar por campaña para el gráfico de torta
        df_camp = df_sem.groupby('Campaña').agg({'Coste (€)': 'sum'}).reset_index()
        fig_pie = px.pie(df_camp, values='Coste (€)', names='Campaña', title='Distribución del Presupuesto por Campaña', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# 5. MÓDULO SEO: CONTENT ENGINE Y BUSCADOR
# ==========================================
elif hemisferio == "📝 SEO (Content Factory Orgánico)":
    st.title("📝 Director de Contenidos Autónomo (SEO)")
    st.markdown("Análisis de posicionamiento SERP, extracción de volumen y Fábrica de Contenidos automatizada.")
    
    # -- CÁLCULO DE KPIS SEO --
    total_trafico = df_seo['Tráfico Mensual'].sum()
    pos_media = df_seo['Posición Media'].mean()
    top3_count = len(df_seo[df_seo['Posición Media'] <= 3])
    
    col_o1, col_o2, col_o3 = st.columns(3)
    with col_o1: render_metric("Visitas Orgánicas/Mes", f"{total_trafico:,}", "seo", "+8.4%", "up")
    with col_o2: render_metric("Posición Media Global", f"{pos_media:.1f}", "seo", "-0.4", "up") # Menos es mejor en posición
    with col_o3: render_metric("Keywords en Top 3", f"{top3_count}", "seo")

    st.divider()

    # -- BUSCADOR AVANZADO SEO --
    st.subheader("🔍 Buscador de Volumen Orgánico y URLs")
    st.markdown("Rastrea URLs indexadas o audita el volumen de palabras clave en tu nicho.")
    
    seo_search = st.text_input("Introduce palabra clave (Ej: ruta, camper, pernocta):")
    
    if seo_search:
        df_filtered_seo = df_seo[df_seo['Palabra Clave Principal'].str.contains(seo_search, case=False, na=False) | df_seo['URL'].str.contains(seo_search, case=False, na=False)]
        if not df_filtered_seo.empty:
            max_vol = df_filtered_seo['Volumen Keyword'].max()
            trafico_capturado = df_filtered_seo['Tráfico Mensual'].sum()
            
            st.info(f"Análisis Orgánico para coincidencias con: **'{seo_search}'**")
            so1, so2 = st.columns(2)
            so1.metric("Volumen de Búsqueda Potencial", f"{max_vol:,} búsquedas/mes")
            so2.metric("Tráfico Real Capturado", f"{trafico_capturado:,} visitas/mes")
            
            # Formatear la tabla para que sea legible
            df_show = df_filtered_seo.copy()
            df_show['Tasa Conversión'] = (df_show['Tasa Conversión'] * 100).round(2).astype(str) + "%"
            st.dataframe(df_show.sort_values(by="Tráfico Mensual", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.warning(f"Ninguna URL o Keyword coincide con '{seo_search}'. ¡Oportunidad para crear nuevo contenido!")
            
    st.divider()

    # -- TABS DE FÁBRICA Y RENDIMIENTO --
    tab_factory, tab_seo_chart = st.tabs(["🏭 Fábrica de Contenidos IA", "📈 Dificultad vs Volumen"])
    
    with tab_factory:
        st.subheader("Borradores Propuestos por la IA")
        st.markdown("Basado en el historial de éxito, el agente ha redactado estos enfoques para publicación.")
        
        for index, row in df_proposals.iterrows():
            with st.expander(f"📌 {row['Título Propuesto']}"):
                colA, colB, colC = st.columns(3)
                colA.metric("Volumen Búsqueda", f"{row['Vol. Búsqueda (Mes)']:,}")
                
                # Asignación de color según dificultad SEO
                kd = row['KD']
                color_kd = "🟢 Fácil" if kd < 30 else "🟡 Media" if kd < 60 else "🔴 Difícil"
                colB.metric("Dificultad (KD)", f"{kd}/100 ({color_kd})")
                
                colC.metric("Intención Principal", row['Intención'])
                
                st.markdown(f"**Ángulo Estratégico de Negocio:** {row['Estrategia']}")
                if st.button("Aprobar y Mandar a CMS", key=f"pub_{index}"):
                    st.success("Draft enviado correctamente a la cola de publicación.")
                    
    with tab_seo_chart:
        st.subheader("Mapa de Competitividad SEO")
        st.markdown("Visualización de todo tu inventario de URLs. Buscamos burbujas grandes (mucho tráfico) situadas a la izquierda (baja dificultad).")
        fig_seo = px.scatter(
            df_seo, 
            x="Dificultad (KD)", 
            y="Tráfico Mensual", 
            size="Volumen Keyword", 
            color="Posición Media",
            hover_name="Palabra Clave Principal",
            color_continuous_scale="Viridis",
            title="Relación Tráfico vs Dificultad Orgánica"
        )
        st.plotly_chart(fig_seo, use_container_width=True)

# ==========================================
# 6. MÓDULO AUDITORÍA CRUZADA (SEO vs SEM)
# ==========================================
elif hemisferio == "🔑 Auditoría Cruzada (SEO vs SEM)":
    st.title("🔑 Matriz de Auditoría Cross-Channel")
    st.markdown("Módulo estratégico avanzado. Identifica canibalización de tráfico, fugas de presupuesto y determina la rentabilidad neta de cada palabra clave.")
    
    # Dictamen Ejecutivo
    st.markdown("### 🤖 Veredicto Algorítmico Integral")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    lideres = len(df_cross[df_cross['Estado'] == '🔥 Rendimiento Líder'])
    fugas = len(df_cross[df_cross['Estado'] == '💸 Fuga Absoluta'])
    ops = len(df_cross[df_cross['Estado'] == '🌱 Optimizar SEO'])
    
    with col_c1: render_metric("Keywords Eficientes", lideres, "cross")
    with col_c2: render_metric("Fugas Críticas", fugas, "cross", "Requiere Acción", "down")
    with col_c3: render_metric("Oportunidades SEO", ops, "cross")

    st.error("""
    **🚨 Alertas de Negocio (Fuga de Caja):** Las búsquedas transaccionales de venta (ej: `comprar camper segunda mano`) están consumiendo más de **1.400€ mensuales** en SEM sin generar retorno (ROAS 0.0x). 
    Al no dedicarnos a la venta, todo ese tráfico es basura rebotada. Se exige negativizar los términos de venta en concordancia amplia y de frase inmediatamente.
    """)

    st.divider()

    # -- TABLA COMPLETA CON BUSCADOR --
    st.subheader("📊 Matriz Estratégica de Efectividad")
    
    cross_search = st.text_input("Filtrar matriz combinada por palabra clave:", placeholder="Ej: alquiler, comprar, santorini...")
    
    if cross_search:
        df_show_cross = df_cross[df_cross['Keyword'].str.contains(cross_search, case=False, na=False)]
    else:
        df_show_cross = df_cross
        
    # Formatear columnas financieras para que se vean bien
    df_styled = df_show_cross.style.format({
        "SEM Gasto (€)": "{:.2f} €",
        "SEM ROAS": "{:.1f}x",
        "SEO Posición": "{:.1f}"
    })
    st.dataframe(df_styled, use_container_width=True, hide_index=True)

    # -- GRÁFICO DE CANIBALIZACIÓN AVANZADO --
    st.subheader("📈 Cuadrante de Toma de Decisiones (Posición vs ROAS)")
    st.markdown("Analiza gráficamente el inventario. **Eje X (Posición SEO) invertido**: La izquierda es el Top 1 de Google.")
    
    fig_cross = px.scatter(
        df_cross, 
        x="SEO Posición", 
        y="SEM ROAS", 
        size="SEM Gasto (€)", 
        color="Estado",
        text="Keyword",
        hover_data=["Acción", "SEO Tráfico"],
        color_discrete_map={
            "🔥 Rendimiento Líder": "#34a853",
            "🌱 Optimizar SEO": "#fbbc05",
            "💸 Fuga Absoluta": "#ea4335"
        }
    )
    # Mejoras visuales del gráfico
    fig_cross.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_cross.update_xaxes(autorange="reverse", title_text="Posición en Google (Orgánico)") 
    fig_cross.update_yaxes(title_text="ROAS SEM (Retorno por Euro Invertido)")
    fig_cross.update_layout(margin=dict(l=40, r=40, t=30, b=40), height=600)
    
    st.plotly_chart(fig_cross, use_container_width=True)

    # -- BOTONES DE ACCIÓN RÁPIDA --
    st.subheader("⚡ Ejecución de Acciones")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("🛡️ Negativizar Fugas SEM (API Ads)"):
            st.success("Términos destructivos añadidos a la lista de palabras clave negativas de la cuenta.")
    with col_b2:
        if st.button("📉 Pausar SEM Canibalizado"):
            st.info("Pausados anuncios para la keyword 'wheely fog' (Top 1 Orgánico consolidado).")
    with col_b3:
        if st.button("🚀 Enviar Ops a Cola de Contenidos"):
            st.success("Términos marcados como 'Optimizar SEO' añadidos al calendario editorial.")
