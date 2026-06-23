import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ==========================================
# 1. CONFIGURACIÓN CORE Y ESTILOS AVANZADOS
# ==========================================
st.set_page_config(
    page_title="Wheely Fog | AI Central Command", 
    page_icon="🧠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Inyección de CSS corporativo
st.markdown("""
    <style>
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
    .metric-title { color: #5f6368; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; }
    .metric-value { color: #202124; font-size: 2.2rem; font-weight: 800; margin: 10px 0 5px 0; }
    
    .seo-card { border-left: 6px solid #34a853; }
    .sem-card { border-left: 6px solid #ea4335; }
    .cross-card { border-left: 6px solid #fbbc05; }
    
    .badge-status { padding: 5px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .status-up { background-color: #e6f4ea; color: #1e8e3e; }
    .status-down { background-color: #fce8e6; color: #d93025; }
    
    .blog-container {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 8px;
        border-left: 4px solid #34a853;
        margin-top: 15px;
    }
    .img-suggestion {
        background-color: #e8f0fe;
        color: #1a73e8;
        padding: 10px 15px;
        border-radius: 6px;
        font-family: monospace;
        margin: 15px 0;
        border: 1px dashed #1a73e8;
    }
    </style>
""", unsafe_allow_html=True)

def render_metric(title, value, card_type="global", delta=None, delta_type="up"):
    delta_html = ""
    if delta:
        color_class = "status-up" if delta_type == "up" else "status-down"
        icon = "↑" if delta_type == "up" else "↓"
        delta_html = f'<div class="badge-status {color_class}">{icon} {delta}</div>'
        
    st.markdown(f"""
    <div class="metric-card {card_type}-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MOTORES DE DATOS SINTÉTICOS 
# ==========================================
@st.cache_data
def load_sem_large_dataset():
    np.random.seed(42)
    fechas = [datetime.today() - timedelta(days=i) for i in range(90)]
    campañas = ["LOCAL_Rafelbunyol", "GLOBAL_Flota_España", "BRAND_WheelyFog", "RETARGETING_Comunidad"]
    terminos = [
        "alquiler camper valencia", "alquiler furgoneta camper", 
        "comprar camper segunda mano", "camperizacion valencia", 
        "wheely fog", "camper santorini alquiler", "rutas camper valencia",
        "camper barata valencia"
    ]
    
    data = []
    for _ in range(1000):
        camp = np.random.choice(campañas)
        term = np.random.choice(terminos)
        fecha = np.random.choice(fechas)
        
        impresiones = np.random.randint(50, 500)
        ctr = np.random.uniform(0.02, 0.12) if camp != "BRAND_WheelyFog" else np.random.uniform(0.15, 0.35)
        cpc = np.random.uniform(0.50, 2.10) if camp != "BRAND_WheelyFog" else np.random.uniform(0.10, 0.30)
        cvr = np.random.uniform(0.00, 0.04) if camp != "BRAND_WheelyFog" else np.random.uniform(0.05, 0.15)
            
        clics = int(impresiones * ctr)
        coste = clics * cpc
        conversiones = int(clics * cvr)
        valor = conversiones * np.random.uniform(150, 600) if conversiones > 0 else 0
        
        data.append({"Fecha": fecha, "Campaña": camp, "Término": term, "Impresiones": impresiones, "Clics": clics, "Coste (€)": coste, "Conversiones": conversiones, "Valor (€)": valor})
    return pd.DataFrame(data).sort_values(by="Fecha", ascending=False).reset_index(drop=True)

@st.cache_data
def load_seo_large_dataset():
    data = [
        {"URL": "/rutas/costa-blanca-camper", "Palabra Clave Principal": "ruta costa blanca camper", "Tráfico Mensual": 4500, "Posición Media": 1.4, "Volumen Keyword": 12000, "Dificultad (KD)": 24},
        {"URL": "/guias/eurodisney-furgoneta-camper", "Palabra Clave Principal": "viaje eurodisney camper", "Tráfico Mensual": 2100, "Posición Media": 3.2, "Volumen Keyword": 8500, "Dificultad (KD)": 42},
        {"URL": "/modelos/diferencias-minivan-gran-volumen", "Palabra Clave Principal": "minivan vs gran volumen", "Tráfico Mensual": 2900, "Posición Media": 2.8, "Volumen Keyword": 4100, "Dificultad (KD)": 35},
        {"URL": "/", "Palabra Clave Principal": "wheely fog", "Tráfico Mensual": 5000, "Posición Media": 1.0, "Volumen Keyword": 1500, "Dificultad (KD)": 5}
    ]
    return pd.DataFrame(data)

@st.cache_data
def load_content_proposals():
    return pd.DataFrame([
        {
            "Título Propuesto": "Guía: Viaje a Eurodisney en Furgoneta Camper desde Valencia",
            "Keyword Objetivo": "eurodisney furgoneta camper",
            "Vol. Búsqueda": 8500,
            "Intención": "Transaccional / Alquiler Familiar",
            "Filtro del Agente IA": "Excluir consejos de mantenimiento propio. Enfocar en la ventaja de alquilar vehículos nuevos (seguridad en un viaje tan largo) y pernoctar en el parking de Disney."
        },
        {
            "Título Propuesto": "Escapadas a menos de 100km desde Rafelbunyol",
            "Keyword Objetivo": "rutas camper cerca de valencia",
            "Vol. Búsqueda": 4200,
            "Intención": "Transaccional Local",
            "Filtro del Agente IA": "Atraer a primerizos. Destacar que el alquiler base incluye 100km/día, haciendo la escapada sumamente barata sin costes ocultos."
        }
    ])

@st.cache_data
def load_cross_channel_matrix():
    return pd.DataFrame([
        {"Keyword": "alquiler camper valencia", "SEO Posición": 2.4, "SEM ROAS": 4.8, "SEM Gasto (€)": 1450.20, "Estado": "🔥 Rendimiento Líder"},
        {"Keyword": "comprar camper segunda mano", "SEO Posición": 48.0, "SEM ROAS": 0.0, "SEM Gasto (€)": 910.40, "Estado": "💸 Fuga Absoluta"}
    ])

df_sem_raw = load_sem_large_dataset()
df_seo = load_seo_large_dataset()
df_proposals = load_content_proposals()
df_cross = load_cross_channel_matrix()

# ==========================================
# 3. MOTOR DE GENERACIÓN DE CONTENIDOS IA (SIMULADO)
# ==========================================
def generate_blog_content(keyword):
    """
    Simula la respuesta del Agente IA al generar el artículo.
    Aplica el filtro para evitar a usuarios que ya tienen camper y prioriza el ALQUILER.
    """
    if "eurodisney" in keyword.lower():
        return """
### ¿Te imaginas conocer el parque temático más famoso de Europa con tu casa sobre ruedas?

En **Wheely Fog**, tu empresa de alquiler de furgonetas camper en Valencia, hemos diseñado un completo itinerario para que disfrutes de un viaje a Eurodisney en furgoneta camper lleno de magia. 

**⚠️ Un consejo antes de arrancar:** Un viaje de más de 1.300 km desde Valencia hasta París pone a prueba cualquier vehículo. Muchos viajeros dudan en someter a su camper antigua a este desgaste por miedo a averías en el extranjero. Por eso, **alquilar una de nuestras furgonetas camper de última generación con seguro a todo riesgo** es la opción más inteligente. Cero kilómetros extra en tu vehículo propio, cero preocupaciones en Francia. Tú solo dedícate a disfrutar.

Tanto si viajas con niños, como si lo haces en pareja o con amigos, te ofrecemos una amplia gama de campers con una capacidad máxima de 5 personas. ¿Preparado para volver a tu infancia? ¡Allá vamos!

<div class="img-suggestion">
📸 <b>Prompt de Imagen sugerido (Para IA o Stock):</b><br>
"Una familia feliz saliendo de una furgoneta camper moderna y reluciente, aparcada. De fondo y ligeramente desenfocado, se intuye el castillo mágico de Eurodisney. Luz de atardecer, estilo fotográfico realista."<br>
<i>Alt text web: Alquilar furgoneta camper en Valencia para ir a Eurodisney familiar.</i>
</div>

#### La mejor época para hacer una escapada a Eurodisney
Si aún no has decidido cuál es la mejor época, te recomendamos entre la primavera y el verano. Durante estos meses el clima es cálido, lo que te permitirá disfrutar de las atracciones. Estas estaciones son temporada alta, así que asegúrate de reservar tus entradas a Disney y **tu vehículo de alquiler en Wheely Fog** con la máxima antelación para no quedarte sin disponibilidad.

#### Dormir en furgoneta camper en Eurodisney
Sin duda, la versatilidad y el ahorro son las claves. Con tu "casa sobre ruedas" de alquiler no tendrás que estar pendiente de horarios de transporte ni de los prohibitivos precios de los hoteles parisinos. 

Tienes varias posibilidades:
1. **El Parking del Parque:** La más práctica. Eurodisney cuenta con una zona especial para autocaravanas con vaciado de aguas, suministro eléctrico y baños.
2. **Camping Club Le Parc de Paris:** A 20 minutos de Eurodisney. Cuenta con supermercado, lavandería y zona de barbacoas.

<div class="img-suggestion">
📸 <b>Sugerencia de Fotografía Real:</b><br>
"Sube aquí una foto real del interior de vuestro modelo Santorini o similar, mostrando la cama montada y cómoda para demostrar el confort frente a una habitación de hotel."<br>
<i>Alt text web: Interior cama furgoneta camper alquiler Wheely Fog.</i>
</div>

#### ¿Cómo llegar desde Valencia?
Si recoges tu vehículo en nuestras instalaciones en **Rafelbunyol**, la ruta Mediterránea es tu mejor aliada. Dirígete hasta La Junquera, sigue por Béziers hasta la autopista A-71 y continúa hasta París. Las furgonetas de Wheely Fog cuentan con motores eficientes para que el consumo de combustible en este trayecto sea el mínimo posible.

#### Vacaciones mágicas con Wheely Fog
No te compliques con revisiones mecánicas antes del viaje. Entra en nuestra web, elige tu modelo, recoge las llaves y pon rumbo a París. Disfruta de unas vacaciones únicas y accede a los mejores servicios de alquiler de campers con nosotros. 
        """
    else:
        return """
### Escapadas de Fin de Semana: Rutas a menos de 100km

En **Wheely Fog** sabemos que a veces menos es más. No necesitas recorrer miles de kilómetros para desconectar. De hecho, el secreto de una escapada rentable y sin estrés está en la proximidad. 

Si no tienes camper propia, **nuestra tarifa base de alquiler incluye 100km al día**. Esto está diseñado matemáticamente para que puedas recoger tu furgoneta en nuestras instalaciones de Rafelbunyol y plantarte en entornos naturales increíbles sin pagar ni un euro de más en kilometraje extra o gastar depósitos enteros de combustible.

<div class="img-suggestion">
📸 <b>Sugerencia de Fotografía Local:</b><br>
"Foto de una de vuestras furgonetas aparcada en un paraje natural valenciano (ej: Albufera o Sierra Calderona) con dos sillas de camping desplegadas."<br>
<i>Alt text web: Escapada camper barata desde Rafelbunyol Valencia.</i>
</div>

Descubre estas 3 rutas rápidas ideales para tu primer alquiler... *(El artículo continuaría desarrollando las rutas locales)*.
        """

# ==========================================
# 4. BARRA LATERAL Y FILTROS
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1200px-Google_%22G%22_logo.svg.png", width=50)
    st.title("WheelyFog AI")
    st.markdown("Gestión integrada de canales digitales.")
    st.divider()
    hemisferio = st.radio("Módulos del Sistema:", ("🛰️ SEM (Performance)", "📝 SEO (Content Factory)", "🔑 Auditoría Cruzada"))
    st.divider()
    dias_filtro = st.slider("Rango de análisis (Días previos):", 7, 90, 30, 1)
    df_sem = df_sem_raw[pd.to_datetime(df_sem_raw['Fecha']) >= (datetime.today() - timedelta(days=dias_filtro))]

# ==========================================
# 5. MÓDULO SEM 
# ==========================================
if hemisferio == "🛰️ SEM (Performance)":
    st.title("🛰️ Director de Performance (SEM)")
    
    total_gasto = df_sem['Coste (€)'].sum()
    total_retorno = df_sem['Valor (€)'].sum()
    roas_global = total_retorno / total_gasto if total_gasto > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1: render_metric("Gasto Total", f"{total_gasto:,.2f} €", "sem")
    with c2: render_metric("Retorno Generado", f"{total_retorno:,.2f} €", "sem", "+14.2%", "up")
    with c3: render_metric("ROAS de Cuenta", f"{roas_global:.2f}x", "sem")

    st.subheader("🔍 Motor de Búsqueda de Términos (Auditoría SEM)")
    term_search = st.text_input("Introduce un término (Ej: valencia, segunda mano):")
    if term_search:
        df_filtered = df_sem[df_sem['Término'].str.contains(term_search, case=False, na=False)]
        if not df_filtered.empty:
            f_gasto = df_filtered['Coste (€)'].sum()
            st.info(f"Resultados para: **'{term_search}'** | Gasto: {f_gasto:,.2f} €")
            st.dataframe(df_filtered.head(10), use_container_width=True, hide_index=True)
        else:
            st.warning("Sin registros en este periodo.")

# ==========================================
# 6. MÓDULO SEO: FABRICA DE CONTENIDOS MEJORADA
# ==========================================
elif hemisferio == "📝 SEO (Content Factory)":
    st.title("📝 Content Factory Autónoma (SEO)")
    st.markdown("Generación de artículos optimizados para **intención de alquiler**, filtrando tráfico basura e incorporando directrices visuales.")

    tab_generador, tab_metricas = st.tabs(["🏭 Generador IA de Artículos", "🔍 Buscador Orgánico"])
    
    with tab_generador:
        st.subheader("Borradores Propuestos y Redacción")
        
        for index, row in df_proposals.iterrows():
            with st.expander(f"📌 {row['Título Propuesto']} (Vol: {row['Vol. Búsqueda']})"):
                st.markdown(f"**Directriz del Agente:** {row['Filtro del Agente IA']}")
                
                # Botón de generación
                if st.button("🧠 Redactar Artículo Completo", key=f"btn_{index}"):
                    with st.spinner("Aplicando filtros de negocio y redactando..."):
                        time.sleep(1.5) # Efecto visual de carga
                        st.markdown('<div class="blog-container">', unsafe_allow_html=True)
                        st.markdown(generate_blog_content(row['Keyword Objetivo']), unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if st.button("📤 Aprobar y Enviar a Web", key=f"aprob_{index}"):
                            st.success("Publicado en el blog como borrador.")
                            
    with tab_metricas:
        st.subheader("🔍 Buscador de Volumen Orgánico y URLs")
        seo_search = st.text_input("Introduce palabra clave (Ej: eurodisney, ruta):")
        if seo_search:
            df_filt_seo = df_seo[df_seo['Palabra Clave Principal'].str.contains(seo_search, case=False, na=False)]
            if not df_filt_seo.empty:
                st.dataframe(df_filt_seo, use_container_width=True, hide_index=True)
            else:
                st.warning("Ninguna URL o Keyword coincide.")

# ==========================================
# 7. MÓDULO AUDITORÍA CRUZADA (CON FIX DE PLOTLY)
# ==========================================
elif hemisferio == "🔑 Auditoría Cruzada":
    st.title("🔑 Matriz de Auditoría Cross-Channel")
    st.markdown("Analiza la canibalización y rentabilidad SEO vs SEM.")
    
    st.dataframe(df_cross, use_container_width=True, hide_index=True)

    st.subheader("📈 Cuadrante de Toma de Decisiones (Posición vs ROAS)")
    st.markdown("El eje X (Posición SEO) está invertido: La izquierda es el Top 1 de Google.")
    
    fig_cross = px.scatter(
        df_cross, x="SEO Posición", y="SEM ROAS", size="SEM Gasto (€)", color="Estado", text="Keyword"
    )
    fig_cross.update_traces(textposition='top center')
    
    # ¡SOLUCIÓN AL ERROR DEL IMAGE_09AAA6.PNG APLICADA AQUÍ! (autorange="reversed")
    fig_cross.update_xaxes(autorange="reversed", title_text="Posición en Google (Orgánico)") 
    fig_cross.update_yaxes(title_text="ROAS SEM (Retorno por Euro Invertido)")
    
    st.plotly_chart(fig_cross, use_container_width=True)
