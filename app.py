# -*- coding: utf-8 -*-
"""
WheelyFog AI - Central Command (Streamlit)
============================================================================
Version corregida del prototipo + modulo de recomendaciones del agente.

FIXES aplicados respecto al original:
  - [BUG botones anidados] Generacion de articulo y aprobacion controladas con
    st.session_state (NO un boton dentro de otro -> ya funciona en cada rerun).
  - [Metodologia] La "Posicion Media" del SEO ahora es PONDERADA por trafico,
    no una media aritmetica (que mezclaba keywords de volumenes distintos).
  - [Incoherencia marca] El motor de recomendaciones NUNCA propone pausar la
    puja de marca "wheely fog" siendo Top 1 organico: la protege.
  - [Honestidad de estado] Los badges de API ya no dicen "Sincronizada"
    decorativo: reflejan que Google Ads / GSC / GA4 estan SIN conectar.

ANADIDO (lo pedido como experto en posicionamiento):
  - Modulo "Recomendaciones del Agente": sugerencias diarias/semanales con
    deteccion automatica de CHOQUE DE INTENCION (compra vs alquiler), fugas de
    presupuesto, canibalizacion y oportunidades SEO. Cada accion se Aplica
    (cola de aprobacion - humano en el bucle) o se Descarta.

Ejecutar:  streamlit run app.py
Requisitos: streamlit, pandas, numpy, plotly
============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
import re
import zipfile

# ==========================================
# 1. CONFIGURACION GLOBAL Y ESTILOS
# ==========================================
st.set_page_config(page_title="WheelyFog AI", page_icon="🚐", layout="wide")

COLORS = {"seo": "#34a853", "sem": "#ea4335", "cross": "#fbbc05", "global": "#4285f4"}

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background:#fff; border:1px solid #e0e0e0; border-radius:12px; padding:16px; }
    .metric-card { background:#fff; border-radius:12px; padding:18px; border:1px solid #e0e0e0; box-shadow:0 1px 3px rgba(0,0,0,0.05); }
    .metric-title { font-size:.75rem; font-weight:700; text-transform:uppercase; color:#5f6368; letter-spacing:.5px; }
    .metric-value { font-size:2rem; font-weight:800; color:#202124; margin:6px 0; }
    .blog-container { background:#f8f9fa; padding:24px; border-radius:8px; border-left:4px solid #34a853; margin-top:12px; line-height:1.6; }
    .img-suggestion { background:#e8f0fe; color:#1a73e8; padding:14px; border-radius:6px; font-family:monospace; margin:16px 0; border:1px dashed #1a73e8; font-size:.85rem; }
    .rec-card { background:#fff; border:1px solid #e0e0e0; border-radius:12px; padding:18px; margin-bottom:14px; }
    .tag { display:inline-block; padding:2px 8px; border-radius:5px; font-size:.72rem; font-weight:600; margin-right:6px; }
    .tag-alta { background:#fce8e6; color:#c5221f; }
    .tag-media { background:#fef7e0; color:#b06000; }
    .tag-info { background:#e8f0fe; color:#1a73e8; }
    .tag-canal { background:#f1f3f4; color:#5f6368; }
</style>
""", unsafe_allow_html=True)


def render_metric(title, value, color_type="global", delta=None, delta_type="up"):
    """Tarjeta de KPI personalizada con borde de color por canal."""
    border = COLORS.get(color_type, COLORS["global"])
    delta_html = ""
    if delta:
        bg = "#e6f4ea" if delta_type == "up" else "#fce8e6"
        fg = "#137333" if delta_type == "up" else "#c5221f"
        arrow = "↑" if delta_type == "up" else "↓"
        delta_html = f'<span style="background:{bg};color:{fg};padding:3px 8px;border-radius:6px;font-size:.75rem;font-weight:600;">{arrow} {delta}</span>'
    st.markdown(f"""
    <div class="metric-card" style="border-left:6px solid {border};">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 2. GENERADORES DE DATOS SINTETICOS
#    (Reemplazar por Google Ads API / GSC / GA4 cuando se conecten)
# ==========================================
@st.cache_data
def load_sem_large_dataset():
    """Dataset SEM sintetico (1000 filas). np.random fijo para reproducibilidad."""
    np.random.seed(42)
    today = datetime.today()
    fechas = [today - timedelta(days=i) for i in range(90)]
    campañas = ["LOCAL_Rafelbunyol", "GLOBAL_Flota_España", "BRAND_WheelyFog", "RETARGETING_Comunidad"]
    terminos = [
        "alquiler camper valencia", "alquiler furgoneta camper", "comprar camper segunda mano",
        "camperizacion valencia", "wheely fog", "camper santorini alquiler", "rutas camper valencia",
        "camper barata valencia", "alquiler autocaravana rafelbunyol", "viajar en camper 2 personas",
        "furgoneta camperizada alquiler",
    ]
    rows = []
    for _ in range(1000):
        camp = np.random.choice(campañas)
        term = np.random.choice(terminos)
        fecha = fechas[np.random.randint(0, 90)]
        if camp == "BRAND_WheelyFog":
            impresiones = np.random.randint(100, 800)
            ctr = np.random.uniform(0.15, 0.35)
            cpc = np.random.uniform(0.10, 0.30)
            cvr = np.random.uniform(0.05, 0.15)
        else:
            impresiones = np.random.randint(50, 500)
            ctr = np.random.uniform(0.02, 0.12)
            cpc = np.random.uniform(0.50, 2.10)
            cvr = np.random.uniform(0.0, 0.04)
        clics = int(impresiones * ctr)
        coste = round(clics * cpc, 2)
        conversiones = int(clics * cvr)
        valor = round(conversiones * np.random.uniform(150, 600), 2) if conversiones > 0 else 0.0
        rows.append({
            "Fecha": fecha.strftime("%Y-%m-%d"), "Campaña": camp, "Término": term,
            "Impresiones": impresiones, "Clics": clics, "Coste (€)": coste,
            "Conversiones": conversiones, "Valor (€)": valor,
        })
    return pd.DataFrame(rows)


@st.cache_data
def load_seo_large_dataset():
    """Datos SEO (Search Console simulado)."""
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
        {"URL": "/contacto", "Palabra Clave Principal": "telefono wheely fog", "Tráfico Mensual": 300, "Posición Media": 1.1, "Volumen Keyword": 400, "Dificultad (KD)": 2, "Tasa Conversión": 0.080},
    ]
    return pd.DataFrame(data)


@st.cache_data
def load_content_proposals():
    """Generador autonomo de ideas con justificacion analitica pre-redaccion."""
    return pd.DataFrame([
        {
            "Título Propuesto": "Guía Definitiva: Viaje a Eurodisney en Furgoneta Camper",
            "Keyword Objetivo": "eurodisney furgoneta camper", "Vol. Búsqueda (Mes)": 8500, "KD": 24,
            "Intención": "Transaccional / Alquiler Familiar",
            "Estrategia": "Aprovechar la inminente temporada de verano. Ideal para promociones cruzadas o sorteos.",
            "Justificacion_Ventas": "Ataca un viaje de +1.300km. Los duenos de campers antiguas temen averias en trayectos largos internacionales. El texto se sesga hacia la 'tranquilidad' de alquilar vehiculos nuevos con seguro a todo riesgo, filtrando curiosos y atrayendo reservas familiares de alto ticket (7-10 dias).",
        },
        {
            "Título Propuesto": "Escapadas de fin de semana desde Rafelbunyol: 5 destinos a menos de 100km",
            "Keyword Objetivo": "rutas camper cerca de valencia", "Vol. Búsqueda (Mes)": 4200, "KD": 15,
            "Intención": "Transaccional Local",
            "Estrategia": "Filtra al cliente ideal. Remarcar los 100km/noche asegura rentabilidad mecanica.",
            "Justificacion_Ventas": "Atrae trafico Bottom-of-Funnel (gente lista para salir este finde). El foco en rutas cortas excluye a nomadas con furgo propia y maximiza la tarifa base (100km/dia), reduciendo la depreciacion del motor.",
        },
        {
            "Título Propuesto": "Dónde alquilar campers baratas en Valencia sin sorpresas en el seguro",
            "Keyword Objetivo": "alquiler camper valencia barata", "Vol. Búsqueda (Mes)": 5600, "KD": 42,
            "Intención": "Transaccional / Precio",
            "Estrategia": "Atacar la transparencia frente a competidores o plataformas P2P.",
            "Justificacion_Ventas": "Resuelve la friccion pre-compra: el miedo a franquicias ocultas. Un articulo transparente roba clientes a Yescapa o competidores locales y convierte trafico en alquileres cerrados.",
        },
    ])


@st.cache_data
def load_cross_channel_matrix():
    """Matriz unificada para evaluar la interseccion de canales SEO y SEM."""
    return pd.DataFrame([
        {"Keyword": "alquiler camper valencia", "SEO Posición": 2.4, "SEO Tráfico": 3100, "SEM Gasto (€)": 1450.20, "SEM ROAS": 4.8, "Estado": "🔥 Rendimiento Líder", "Acción": "Mantener Inversión"},
        {"Keyword": "camper santorini alquiler", "SEO Posición": 2.1, "SEO Tráfico": 1100, "SEM Gasto (€)": 810.50, "SEM ROAS": 6.5, "Estado": "🔥 Rendimiento Líder", "Acción": "Escalar Presupuesto"},
        {"Keyword": "rutas camper cerca de valencia", "SEO Posición": 1.5, "SEO Tráfico": 1400, "SEM Gasto (€)": 285.10, "SEM ROAS": 1.2, "Estado": "🌱 Optimizar SEO", "Acción": "Reducir Puja SEM"},
        {"Keyword": "comprar camper segunda mano", "SEO Posición": 48.0, "SEO Tráfico": 5, "SEM Gasto (€)": 910.40, "SEM ROAS": 0.0, "Estado": "🛒 Vertical Venta", "Acción": "Campaña de venta propia (/venta)"},
        {"Keyword": "camperizacion valencia", "SEO Posición": 14.5, "SEO Tráfico": 80, "SEM Gasto (€)": 495.00, "SEM ROAS": 0.4, "Estado": "🔧 Pre-lanzamiento", "Acción": "Captar lista de espera, puja mínima"},
        {"Keyword": "wheely fog", "SEO Posición": 1.0, "SEO Tráfico": 5000, "SEM Gasto (€)": 145.00, "SEM ROAS": 14.2, "Estado": "🔥 Rendimiento Líder", "Acción": "Proteger Marca"},
        {"Keyword": "camper barata valencia", "SEO Posición": 9.2, "SEO Tráfico": 110, "SEM Gasto (€)": 1280.60, "SEM ROAS": 3.1, "Estado": "🌱 Optimizar SEO", "Acción": "Crear Landing SEO"},
    ])


# Ficha REAL de Wheely Fog (verificada en wheelyfog.com) para el Content Factory.
# El contenido generado debe ceñirse SOLO a estos datos para no inventar.
WF_FACTS = {
    "empresa": "Wheely Fog (Gesibris SL)",
    "base": "Rafelbunyol, Valencia (Carrer del Mar 9). A 5 min a pie del metro Línea 3.",
    "core": "alquiler de furgonetas camper premium desde Valencia",
    "verticales": "alquiler, venta de campers ex-flota con historial, y camperización (próximamente)",
    "entrega": "entrega y devolución de llaves 24/7, los 365 días del año",
    "km_base": "100 km/noche incluidos (ampliable a ilimitado con el seguro Extra o pack de +15€/día)",
    "seguro": "seguro básico incluido a 0€, con dos niveles opcionales (Estándar 22€/noche, Extra 39€/noche)",
    "minimos": "mínimo 3 noches (4 en temporada alta, 7 en agosto)",
    "pet": "pet-friendly con suplemento único de 35€ por limpieza",
    "ue": "viajes permitidos por toda la Unión Europea sin recargos",
    "kit": "Kit Completo opcional (49€): ropa de cama, toallas, menaje de cocina y set de limpieza",
    "pago": "pago fraccionado opcional (30% para reservar, 70% al recoger)",
    "venta": "campers de la propia flota, con historial de mantenimiento completo, con opción de "
             "'pruébala alquilando antes de comprar y te descontamos el importe del alquiler'",
    "flota_ejemplos": "Santorini, Formentera, Nueva York, Bibury (gran volumen) y Compact Sky, "
                      "Grey/Blue/Red Compact (mini van)",
}


def generate_ai_blog(keyword, title):
    """Motor IA de redaccion. Se ciñe a los datos REALES de WF_FACTS. Detecta la
    vertical de la keyword y adapta el enfoque (alquiler vs venta)."""
    vert = clasifica_vertical(keyword) if "clasifica_vertical" in globals() else "ALQUILER"
    if "eurodisney" in keyword.lower():
        return """
        <h3>¿Te imaginas conocer el parque temático más famoso de Europa con tu casa sobre ruedas?</h3>
        <p>En <strong>Wheely Fog</strong>, tu empresa de alquiler de furgonetas camper en Valencia, hemos diseñado un itinerario para que disfrutes de un viaje a Eurodisney lleno de magia. Tanto en familia como en pareja o con amigos, ofrecemos furgonetas camper de hasta 5 personas.</p>
        <div class="img-suggestion">📸 <b>Prompt IA / Director de Arte:</b><br>"Fotografía hiperrealista. Una familia feliz saliendo de una furgoneta camper moderna y reluciente; de fondo desenfocado se intuye el castillo de Eurodisney. Luz de atardecer golden hour."<br><i>Alt text sugerido: Alquilar furgoneta camper en Valencia para ir a Eurodisney familiar.</i></div>
        <h4>La mejor época y el factor "Tranquilidad"</h4>
        <p>Recomendamos fechas entre primavera y verano. Pero hay un factor crucial: <strong>el vehículo</strong>. El trayecto España-París supera los 1.300 km solo de ida. Muchos descartan la idea por miedo a someter su vehículo propio o antiguo a semejante desgaste. Aquí entra la inteligencia: <strong>alquilar una camper con Wheely Fog</strong> mantiene tu coche a cero kilómetros, e incluye seguro básico a 0€ (ampliable al nivel Extra con kilometraje ilimitado) y asistencia en carretera 24h por toda la Unión Europea.</p>
        <h4>Dormir en furgoneta camper en Eurodisney</h4>
        <ul>
            <li><strong>El parking del parque:</strong> zona para vaciar aguas, suministro eléctrico y baños.</li>
            <li><strong>Camping Le Parc de Paris:</strong> a 20 min, con supermercado, lavandería y minigolf.</li>
        </ul>
        <div class="img-suggestion">📸 <b>Sugerencia de Fotografía Propia:</b><br>"Sube una foto real del interior del modelo 'Santorini' (5 plazas). Muestra la cama montada, bien iluminada, demostrando que es más cómodo que un hotel estándar."<br><i>Alt text sugerido: Interior cama furgoneta camper alquiler Wheely Fog Paris.</i></div>
        <p>Reserva tus entradas con antelación y calcula peajes. El parque se visita bien en 3 días. Entra en nuestra web, selecciona fechas y reserva hoy tu camper en Wheely Fog.</p>
        """
    if vert == "VENTA":
        return f"""
    <h3>{title}</h3>
    <p>En <strong>{WF_FACTS['empresa']}</strong> no solo alquilamos campers: también las vendemos.
    Y con una ventaja poco habitual — son <strong>vehículos de nuestra propia flota</strong>, {WF_FACTS['venta']}.</p>
    <p>Sabes exactamente lo que compras: cada camper tiene su historial de mantenimiento completo,
    y puedes conocerla a fondo antes de decidir. Modelos como {WF_FACTS['flota_ejemplos']} pasan por
    nuestro taller antes de ponerse a la venta.</p>
    <div class="img-suggestion">📸 <b>Prompt IA / Director de Arte:</b><br>"Furgoneta camper Wheely Fog
    limpia y preparada en exposición, con etiqueta de kilómetros e historial visible. Luz natural, aspecto
    fiable y premium."<br><i>Alt text sugerido: Comprar camper de ocasión con historial en Valencia — Wheely Fog.</i></div>
    <h4>Por qué comprar una ex-flota con historial</h4>
    <p>Frente a un particular anónimo, aquí sabes cómo se ha cuidado el vehículo. Base en {WF_FACTS['base']}
    Además, ofrecemos la opción de <strong>probarla alquilando antes de comprar</strong>: si te decides,
    te descontamos el alquiler del precio final.</p>
    <p><i>(El artículo continuaría con las fichas de los modelos disponibles: año, kilómetros, equipamiento y precio.)</i></p>
    """
    # Alquiler / informacional
    return f"""
    <h3>{title}</h3>
    <p>En <strong>{WF_FACTS['empresa']}</strong> te lo ponemos fácil: {WF_FACTS['core']}, con
    {WF_FACTS['entrega']} para máxima flexibilidad.</p>
    <p>Nuestra filosofía es la transparencia: <strong>{WF_FACTS['seguro']}</strong>, {WF_FACTS['km_base']},
    y {WF_FACTS['pet']}. Todo lo básico va de serie, sin sorpresas.</p>
    <div class="img-suggestion">📸 <b>Prompt IA / Director de Arte:</b><br>"Furgoneta camper aparcada
    frente a la Albufera de Valencia al atardecer, dos sillas de camping y dos cafés en una mesa plegable."
    <br><i>Alt text sugerido: Alquiler de camper desde Rafelbunyol, Valencia — Wheely Fog.</i></div>
    <h4>Lo que incluye tu alquiler</h4>
    <ul>
        <li>{WF_FACTS['km_base']}.</li>
        <li>{WF_FACTS['seguro']}.</li>
        <li>Opcional: {WF_FACTS['kit']}.</li>
        <li>{WF_FACTS['ue']}. {WF_FACTS['minimos']}.</li>
    </ul>
    <p>Recoge tu camper en {WF_FACTS['base']} Reserva 100% online y {WF_FACTS['pago']}.
    <i>(El artículo continuaría detallando las rutas locales recomendadas.)</i></p>
    """


# ==========================================
# 2.b LECTOR DE ARCHIVOS REALES DE GOOGLE SEARCH CONSOLE
#     Acepta ZIP (export nativo de GSC), CSV y XLSX. GRATIS, sin API.
#     - Del export de Rendimiento (ZIP) saca Queries.csv y Pages.csv.
#     - Del export de Cobertura/Indexacion (ZIP) saca Table.csv (URLs) +
#       Metadata.csv (el motivo: 404, noindex, redirect...).
#     Los archivos se leen en memoria; nada se guarda en disco ni en el repo.
# ==========================================
GANCHOS = ["Seguro Básico Incluido 0€", "Entrega 24/7 los 365 días",
           "Pet-friendly (supl. 35€)", "Flexibilidad por toda la UE"]

COLMAP = {
    "query":       ["consulta principal", "consultas principales", "consulta", "consultas",
                    "top queries", "query", "queries"],
    "page":        ["páginas principales", "paginas principales", "página", "pagina",
                    "top pages", "page", "pages", "url"],
    "clicks":      ["clics", "clicks", "clics totales"],
    "impressions": ["impresiones", "impressions", "impresiones totales"],
    "ctr":         ["ctr", "ctr medio", "ctr promedio", "average ctr"],
    "position":    ["posición", "posicion", "posición media", "posicion media",
                    "position", "average position"],
}


def _find_col(cols_lower, keys):
    for k in keys:
        if k in cols_lower:
            return cols_lower[k]
    for k in keys:
        for c in cols_lower:
            if k in c:
                return cols_lower[c]
    return None


def _to_pct(series):
    def conv(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip().replace("%", "").replace(",", ".")
        try:
            f = float(s)
        except ValueError:
            return np.nan
        return f / 100 if f > 1 else f
    return series.apply(conv)


def _to_num(series):
    def conv(v):
        if pd.isna(v):
            return np.nan
        s = re.sub(r"[^0-9.\-]", "", str(v).strip().replace(",", "."))
        try:
            return float(s)
        except ValueError:
            return np.nan
    return series.apply(conv)


def _read_any(raw_bytes, filename):
    """Lee bytes de un CSV o XLSX -> DataFrame (o None)."""
    name = filename.lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw_bytes))
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
            except Exception:
                continue
    except Exception:
        return None
    return None


def _pick_from_zip(zf, wanted_substrings):
    """Devuelve (df, nombre) del primer archivo del ZIP cuyo nombre contenga
    alguno de los substrings buscados (case-insensitive)."""
    for info in zf.namelist():
        base = info.split("/")[-1].lower()
        if not base or base.startswith("."):
            continue
        if any(w in base for w in wanted_substrings):
            df = _read_any(zf.read(info), base)
            if df is not None and not df.empty:
                return df, base
    return None, None


def _normalize_perf(df, kind):
    """df crudo de GSC -> columnas: termino, Clics, Impresiones, CTR, Posicion."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    dim_key = "query" if kind == "query" else "page"
    dim_col = _find_col(cols_lower, COLMAP[dim_key])
    if dim_col is None:
        return None
    out = pd.DataFrame()
    out["termino"] = df[dim_col].astype(str)
    for target, key in [("Clics", "clicks"), ("Impresiones", "impressions"),
                        ("CTR", "ctr"), ("Posicion", "position")]:
        col = _find_col(cols_lower, COLMAP[key])
        if col is None:
            out[target] = np.nan
        elif target == "CTR":
            out[target] = _to_pct(df[col])
        else:
            out[target] = _to_num(df[col])
    out["Clics"] = out["Clics"].fillna(0).astype(int)
    out["Impresiones"] = out["Impresiones"].fillna(0).astype(int)
    return out


def _normalize_timeseries(df):
    """Chart.csv/Dates.csv de GSC -> DataFrame con Fecha (datetime), Mes (period),
    Clics, Impresiones, CTR, Posicion. Soporta 'Date Range' con rango o fecha suelta."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    date_col = None
    for key in ["date range", "fecha", "date", "week", "semana", "día", "dia", "day"]:
        if key in cols_lower:
            date_col = cols_lower[key]
            break
    if date_col is None:
        date_col = df.columns[0]

    def parse_date(v):
        s = str(v).strip()
        # "2025-07-07 - 2025-07-12" -> tomamos la fecha inicial del periodo
        if " - " in s:
            s = s.split(" - ")[0].strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return pd.to_datetime(s, format=fmt)
            except Exception:
                continue
        try:
            return pd.to_datetime(s)
        except Exception:
            return pd.NaT

    out = pd.DataFrame()
    out["Fecha"] = df[date_col].apply(parse_date)
    out = out.dropna(subset=["Fecha"])
    if out.empty:
        return None
    for target, key in [("Clics", "clicks"), ("Impresiones", "impressions"),
                        ("CTR", "ctr"), ("Posicion", "position")]:
        col = _find_col(cols_lower, COLMAP[key])
        if col is None:
            out[target] = np.nan
        elif target == "CTR":
            out[target] = _to_pct(df[col].reindex(out.index) if len(df) == len(out) else df[col]).values[:len(out)]
        else:
            vals = _to_num(df[col])
            out[target] = vals.values[:len(out)]
    out["Clics"] = pd.to_numeric(out["Clics"], errors="coerce").fillna(0).astype(int)
    out["Impresiones"] = pd.to_numeric(out["Impresiones"], errors="coerce").fillna(0).astype(int)
    out["Mes"] = out["Fecha"].dt.to_period("M").astype(str)
    return out.sort_values("Fecha").reset_index(drop=True)


MESES_ES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
            "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


def _parse_fecha_es(s):
    """'11 may 2026, 9:21:48' -> Timestamp. Soporta formatos de Google Ads en ES."""
    s = str(s).strip()
    m = re.match(r"(\d{1,2})\s+(\w{3})\w*\s+(\d{4})", s)
    if m:
        d, mes, y = m.groups()
        try:
            return pd.Timestamp(int(y), MESES_ES.get(mes[:3].lower(), 1), int(d))
        except Exception:
            return pd.NaT
    try:
        return pd.to_datetime(s, dayfirst=True)
    except Exception:
        return pd.NaT


def parse_ads_change_history(raw_bytes, filename):
    """Lee el 'Informe de historial de cambios' de Google Ads (CSV/XLSX).
    Devuelve DataFrame con Fecha, Usuario, Campaña, Grupo, Cambios | None."""
    name = filename.lower()
    df = None
    try:
        if name.endswith((".xlsx", ".xls")):
            # La cabecera real suele estar 2 filas más abajo
            for sk in (0, 1, 2, 3):
                tmp = pd.read_excel(io.BytesIO(raw_bytes), skiprows=sk)
                if any("fecha" in str(c).lower() for c in tmp.columns):
                    df = tmp
                    break
        else:
            for enc in ("utf-8-sig", "utf-8", "latin-1"):
                for sk in (0, 1, 2, 3):
                    try:
                        tmp = pd.read_csv(io.BytesIO(raw_bytes), encoding=enc,
                                          skiprows=sk, engine="python")
                        if any("fecha" in str(c).lower() for c in tmp.columns):
                            df = tmp
                            break
                    except Exception:
                        continue
                if df is not None:
                    break
    except Exception:
        return None
    if df is None or df.empty:
        return None

    cols = {c.lower().strip(): c for c in df.columns}
    fcol = next((cols[c] for c in cols if "fecha" in c), None)
    if fcol is None:
        return None
    out = pd.DataFrame()
    out["Fecha"] = df[fcol].apply(_parse_fecha_es)
    out["Usuario"] = df[cols.get("usuario", fcol)] if "usuario" in cols else ""
    ccol = next((cols[c] for c in cols if "campa" in c), None)
    out["Campaña"] = df[ccol] if ccol else ""
    gcol = next((cols[c] for c in cols if "grupo" in c), None)
    out["Grupo"] = df[gcol] if gcol else ""
    chcol = next((cols[c] for c in cols if "cambio" in c), None)
    out["Cambios"] = df[chcol] if chcol else ""
    out = out.dropna(subset=["Fecha"])
    if out.empty:
        return None
    out["Mes"] = out["Fecha"].dt.to_period("M").astype(str)
    return out.sort_values("Fecha").reset_index(drop=True)


def parse_gsc_upload(uploaded_file):
    """
    Punto de entrada unico. Acepta ZIP / CSV / XLSX de GSC.
    Devuelve dict: queries, pages, index_urls, index_issue, timeseries, msg.
    """
    res = {"queries": None, "pages": None, "index_urls": None,
           "index_issue": None, "timeseries": None, "msg": ""}
    if uploaded_file is None:
        return res
    raw = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    msgs = []

    # --- ZIP (export nativo de GSC) ---
    if name.endswith(".zip"):
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except Exception as e:
            res["msg"] = f"ZIP ilegible: {e}"
            return res

        dq, _ = _pick_from_zip(zf, ["quer", "consult"])
        if dq is not None:
            res["queries"] = _normalize_perf(dq, "query")
            if res["queries"] is not None:
                msgs.append(f"Consultas: {len(res['queries'])} filas")

        dp, _ = _pick_from_zip(zf, ["page", "pagin", "página"])
        if dp is not None:
            res["pages"] = _normalize_perf(dp, "page")
            if res["pages"] is not None:
                msgs.append(f"Páginas: {len(res['pages'])} filas")

        # Serie temporal (Chart.csv / Dates.csv): clics/impresiones/CTR/pos por fecha
        dts, _ = _pick_from_zip(zf, ["chart", "date", "fecha", "week", "semana"])
        if dts is not None:
            ts = _normalize_timeseries(dts)
            if ts is not None and not ts.empty:
                res["timeseries"] = ts
                msgs.append(f"Serie temporal: {len(ts)} periodos")

        # Cobertura / indexacion: Table.csv (URLs) + Metadata.csv (motivo)
        dt, _ = _pick_from_zip(zf, ["table"])
        if dt is not None:
            url_col = next((c for c in dt.columns
                            if "url" in c.lower() or "pagin" in c.lower()
                            or "página" in c.lower()), dt.columns[0])
            res["index_urls"] = dt.rename(columns={url_col: "URL"})
            msgs.append(f"Indexación: {len(dt)} URLs")
            dm, _ = _pick_from_zip(zf, ["metadata"])
            if dm is not None:
                try:
                    txt = " ".join(dm.astype(str).values.ravel())
                    m = re.search(r"(404|noindex|redirect|forbidden|canonical|4xx|crawl)", txt, re.I)
                    if m:
                        res["index_issue"] = m.group(0)
                except Exception:
                    pass
        res["msg"] = " · ".join(msgs) if msgs else "El ZIP no contenía Queries/Pages/Table reconocibles."
        return res

    # --- CSV o XLSX suelto ---
    df = _read_any(raw, name)
    if df is None or df.empty:
        res["msg"] = "No se pudo leer el archivo."
        return res
    cols_lower = {c.lower().strip(): c for c in df.columns}
    if any(k in cols_lower for k in ["date range", "fecha", "date", "week", "semana"]) and \
       _find_col(cols_lower, COLMAP["clicks"]) is not None and \
       _find_col(cols_lower, COLMAP["query"]) is None and \
       _find_col(cols_lower, COLMAP["page"]) is None:
        ts = _normalize_timeseries(df)
        if ts is not None:
            res["timeseries"] = ts
            res["msg"] = f"Serie temporal: {len(ts)} periodos"
            return res
    if _find_col(cols_lower, COLMAP["query"]) is not None:
        res["queries"] = _normalize_perf(df, "query")
        res["msg"] = f"Consultas: {len(res['queries'])} filas"
    elif _find_col(cols_lower, COLMAP["page"]) is not None:
        res["pages"] = _normalize_perf(df, "page")
        res["msg"] = f"Páginas: {len(res['pages'])} filas"
    elif any("url" in c.lower() for c in df.columns):
        url_col = next(c for c in df.columns if "url" in c.lower())
        res["index_urls"] = df.rename(columns={url_col: "URL"})
        res["msg"] = f"Indexación: {len(df)} URLs"
    else:
        res["msg"] = f"No reconozco las columnas: {list(df.columns)}"
    return res


# --- Clasificador de VERTICALES de negocio (ALQUILER/VENTA/CAMPERIZACION/MARCA) ---
# Modelo REAL de wheelyfog.com (verificado en la web):
#   ALQUILER (/campers): core. Desde 3 noches, desde Valencia.
#   VENTA (/venta): campers EX-FLOTA con historial completo y kilometraje real
#       (ocasión/seminuevo premium, NO concesionario nuevo). Precios 35k-80k.
#       Gancho propio: "historial completo + puedes alquilarla antes de comprar
#       y te descontamos el alquiler". => "segunda mano", "km", "ocasión",
#       "seminueva" son tráfico VÁLIDO y cualificado de venta, NO tóxico.
#   CAMPERIZACION (/camperizacion): PRÓXIMAMENTE. Aún no activa; solo lista de
#       espera. Se captan leads, no se compite a full por ahora.
# El clasificador puntúa señales de intención; el verbo de acción manda.
FLOTA = ["santorini", "kioto", "bibury", "formentera", "nueva york", "arizona",
         "kenia", "gamla stan", "la cabaña", "la cabana", "compact sky",
         "red compact", "blue compact", "grey compact", "white compact",
         "vancubic", "sa talaia", "tromso", "tromsø"]

# Señales de ACCIÓN (verbo de intención) — pesan más que los adjetivos
SIG_ALQUILER = ["alquiler", "alquilar", "alquilo", "alquila", "rent", "renting",
                "de alquiler", "en alquiler"]
SIG_VENTA = ["comprar", "compra", "venta", "vender", "en venta", "adquirir",
             "a la venta", "me interesa comprar",
             # ocasión/seminuevo: en Wheely Fog SON venta legítima (ex-flota)
             "segunda mano", "seminueva", "seminuevo", "ocasion", "ocasión",
             "de ocasion", "km0", "km 0", "kilometraje", "con historial"]
# Señales de CONTEXTO (refuerzan, no deciden solas)
CTX_ALQUILER = ["fin de semana", "finde", "escapada", "escapadas", "ruta", "rutas",
                "vacaciones", "viaje", "viajar", "noches", "por dias", "por días",
                "una semana", "puente", "pernocta", "dormir"]
CTX_VENTA = ["precio camper", "precio furgoneta", "cuanto cuesta una camper",
             "camper en venta", "furgoneta en venta", "camper de ocasion",
             "financiacion", "financiación", "financiar", "iva incluido"]
# Camperización (aún "Próximamente" en la web)
TERMS_CAMPERIZACION = ["camperizar", "camperizacion", "camperización", "homologar",
                       "homologacion", "homologación", "mueble camper", "kit camper",
                       "aislamiento furgoneta", "transformar furgoneta", "camperizar mi"]
# Realmente contraproducente para una marca premium: SOLO "barato/a" en intención
# de compra (erosiona posicionamiento; su flota de venta es premium con historial).
TERMS_EROSION_PREMIUM = ["barato", "barata", "baratas", "baratos", "chollo",
                         "tirado de precio", "regalada"]


def _score_intent(k):
    """Puntúa señales de cada vertical. Acción=3, contexto=1. Devuelve dict."""
    s = {"ALQUILER": 0, "VENTA": 0}
    for t in SIG_ALQUILER:
        if t in k:
            s["ALQUILER"] += 3
    for t in SIG_VENTA:
        if t in k:
            s["VENTA"] += 3
    for t in CTX_ALQUILER:
        if t in k:
            s["ALQUILER"] += 1
    for t in CTX_VENTA:
        if t in k:
            s["VENTA"] += 1
    return s


def clasifica_vertical(kw):
    """Devuelve la vertical dominante. Prioridad: MARCA > CAMPERIZACION > (VENTA vs
    ALQUILER por puntuación de intención) > INFORMACIONAL."""
    k = str(kw).lower()
    if "wheely" in k:
        return "MARCA"
    if any(m in k for m in FLOTA):
        return "MARCA"
    if any(t in k for t in TERMS_CAMPERIZACION):
        return "CAMPERIZACION"
    s = _score_intent(k)
    # Si hay señal de alquiler, ALQUILER gana los empates (el verbo de acción manda)
    if s["ALQUILER"] > 0 and s["ALQUILER"] >= s["VENTA"]:
        return "ALQUILER"
    if s["VENTA"] > s["ALQUILER"]:
        return "VENTA"
    return "INFORMACIONAL"


def erosiona_premium(kw):
    """True si es intención de compra con 'barato/chollo': choca con el
    posicionamiento premium de la flota de venta (con historial, 35k-80k).
    NO aplica a alquiler: 'alquiler barato' es una búsqueda legítima."""
    k = str(kw).lower()
    if clasifica_vertical(kw) != "VENTA":
        return False
    return any(t in k for t in TERMS_EROSION_PREMIUM)


# Compatibilidad con el resto del código (antes se llamaba es_toxico_para_venta)
def es_toxico_para_venta(kw):
    return erosiona_premium(kw)


VERT_COLORS = {"ALQUILER": "#1a73e8", "VENTA": "#9334e6", "CAMPERIZACION": "#e37400",
               "MARCA": "#137333", "INFORMACIONAL": "#5f6368"}


def build_gsc_recommendations(df_q):
    """Recomendaciones sobre datos REALES de GSC, clasificadas por vertical."""
    recs, rid = [], 0

    def add(sev, canal, freq, kw, vert, titulo, detalle, accion, impacto):
        nonlocal rid
        rid += 1
        recs.append(dict(id=f"g{rid}", sev=sev, canal=canal, freq=freq, kw=kw,
                         vertical=vert, titulo=titulo, detalle=detalle,
                         accion=accion, impacto=impacto))

    if df_q is None or df_q.empty:
        return recs
    df = df_q.copy()
    df["Vertical"] = df["termino"].apply(clasifica_vertical)

    marca = df[df["Vertical"] == "MARCA"]
    if not marca.empty:
        add("info", "SEO+SEM", "semanal", "wheely fog / flota", "MARCA",
            "Proteger marca y nombres de flota (NUNCA negativizar)",
            f"{len(marca)} términos de marca/flota generan {int(marca['Clics'].sum()):,} clics reales.",
            "Mantener campaña de marca en Ads y vigilar SERP de Santorini, Kioto, Formentera, etc.",
            "Blindas el tráfico de mayor conversión")

    # ---- VENTA: campers EX-FLOTA con historial (ocasión premium) ----
    # "barato/chollo" en compra erosiona el posicionamiento premium: se avisa,
    # NO se negativiza a ciegas (podría ser demanda real mal encajada).
    eros = df[(df["Vertical"] == "VENTA") & df["termino"].apply(erosiona_premium)]
    for _, r in eros.sort_values("Impresiones", ascending=False).head(5).iterrows():
        add("media", "SEO+SEM", "semanal", r["termino"], "VENTA",
            "Búsqueda de 'barato' choca con tu venta premium (con historial)",
            f'"{r["termino"]}" — {int(r["Impresiones"]):,} impr., pos {r["Posicion"]:.0f}. '
            "Tu flota de venta es ocasión premium con historial (35k-80k€), no saldo.",
            "En SEM, matizar con negativa 'gratis/saldo' pero NO 'ocasión/km'. En orgánico, "
            "reencuadrar el copy hacia 'relación calidad-historial-precio', no hacia 'lo más barato'.",
            "Filtras cazagangas sin perder demanda real de compra")

    # VENTA legítima (ocasión, km, seminueva, comprar...) = vertical activa y cualificada
    venta_ok = df[(df["Vertical"] == "VENTA") & ~df["termino"].apply(erosiona_premium)]
    if not venta_ok.empty:
        add("info", "SEO+SEM", "semanal", "vertical venta", "VENTA",
            "Vertical VENTA activa: campers ex-flota con historial",
            f"{len(venta_ok)} términos de compra reales ({int(venta_ok['Impresiones'].sum()):,} impr., "
            f"{int(venta_ok['Clics'].sum()):,} clics). Vendes tu propia flota con historial completo y "
            "opción de 'pruébala alquilando antes de comprar y te descontamos el alquiler'.",
            "Campañas de VENTA separadas de ALQUILER. Copy con los ganchos REALES: historial de "
            "mantenimiento, prueba-antes-de-comprar, IVA incluido. KPI = lead de compra, no reserva.",
            "Monetiza la rotación de flota con el argumento diferencial que ya tienes")
    # Oportunidad SEO de venta (ocasión/km con demanda pero mala posición)
    for _, r in venta_ok[(venta_ok["Posicion"] > 8) & (venta_ok["Impresiones"] >= 60)].sort_values("Impresiones", ascending=False).head(5).iterrows():
        add("media", "SEO", "semanal", r["termino"], "VENTA",
            "Oportunidad SEO en VENTA (demanda de ocasión sin posición)",
            f'"{r["termino"]}" — {int(r["Impresiones"]):,} impr. pero pos {r["Posicion"]:.0f}. '
            "Compra de camper de ocasión: ciclo largo, el contenido con historial madura el lead.",
            "Optimizar /venta y fichas por vehículo (marca, año, km, historial, 'pruébala antes de "
            "comprar'). Enlazar desde el blog. No mezclar con /campers de alquiler.",
            "Pipeline de leads de compra sin depender de puja")

    # ---- ALQUILER: quick-wins tipo agente Google ----
    # CTR medio esperado por posición (curva estándar aproximada). Sirve para
    # estimar la GANANCIA de clics de subir una keyword, y priorizar por impacto.
    def ctr_esperado(pos):
        tabla = {1: .28, 2: .16, 3: .11, 4: .08, 5: .06, 6: .05,
                 7: .04, 8: .032, 9: .028, 10: .025}
        p = int(round(pos)) if pd.notna(pos) else 20
        if p <= 10:
            return tabla.get(p, .025)
        return max(.02 - (p - 10) * 0.0015, 0.003)

    def ganancia_clics(r, objetivo=3):
        """Clics extra estimados si sube a la posición objetivo (top 3)."""
        if pd.isna(r["Posicion"]) or r["Impresiones"] <= 0:
            return 0
        actual = r["CTR"] if pd.notna(r["CTR"]) and r["CTR"] > 0 else ctr_esperado(r["Posicion"])
        meta = ctr_esperado(objetivo)
        return max(int(r["Impresiones"] * (meta - actual)), 0)

    alq = df[df["Vertical"] == "ALQUILER"].copy()
    # Ventana quick-win: pos 4-10 (página 1 baja) — mínimo esfuerzo, máximo salto de CTR
    quick = alq[(alq["Posicion"] >= 4) & (alq["Posicion"] <= 10) & (alq["Impresiones"] >= 50)].copy()
    if not quick.empty:
        quick["ganancia"] = quick.apply(ganancia_clics, axis=1)
        quick = quick.sort_values("ganancia", ascending=False)
        for _, r in quick.head(8).iterrows():
            g = int(r["ganancia"])
            sev = "alta" if g >= 30 else "media"
            ctr_txt = f"{r['CTR']*100:.1f}%" if pd.notna(r["CTR"]) else "n/d"
            add(sev, "SEO", "semanal", r["termino"], "ALQUILER",
                f"Quick-win ALQUILER: +{g} clics/mes estimados subiendo al Top 3",
                f'"{r["termino"]}" — pos {r["Posicion"]:.0f}, {int(r["Impresiones"]):,} impr., CTR {ctr_txt}. '
                "Ya estás en página 1: subir 1-3 puestos es el mayor retorno por esfuerzo.",
                f"Un solo ajuste on-page: meter la keyword exacta en H1+title, 2-3 enlaces internos "
                f"desde páginas de alquiler potentes, y añadir gancho ({GANCHOS[0]}). Sin crear contenido nuevo.",
                f"~{g} clics/mes de alquiler sin coste de puja")

    # ALQUILER: pos 11-20 (inicio página 2) — segundo lote, algo más de trabajo
    pag2 = alq[(alq["Posicion"] > 10) & (alq["Posicion"] <= 20) & (alq["Impresiones"] >= 150)].copy()
    if not pag2.empty:
        pag2["ganancia"] = pag2.apply(lambda r: ganancia_clics(r, objetivo=8), axis=1)
        for _, r in pag2.sort_values("ganancia", ascending=False).head(4).iterrows():
            add("media", "SEO", "semanal", r["termino"], "ALQUILER",
                "ALQUILER en página 2: empujar a página 1",
                f'"{r["termino"]}" — pos {r["Posicion"]:.0f}, {int(r["Impresiones"]):,} impr. '
                "Alta demanda pero fuera de página 1: no recibe casi clics.",
                "Reforzar la página existente (contenido + enlazado interno). Un solo empujón la mete en página 1.",
                "Desbloquea demanda de alquiler hoy invisible")

    # ---- CTR bajo en Top 5 (cualquier vertical): arreglo de title/meta ----
    top_bajo = df[(df["Posicion"] <= 5) & (df["Impresiones"] >= 200) & (df["CTR"] < 0.02)].copy()
    for _, r in top_bajo.sort_values("Impresiones", ascending=False).head(5).iterrows():
        v = clasifica_vertical(r["termino"])
        add("alta", "SEO", "semanal", r["termino"], v,
            "Top 5 pero casi nadie hace clic (arreglo de 1 línea: title/meta)",
            f'"{r["termino"]}" — pos {r["Posicion"]:.0f}, {int(r["Impresiones"]):,} impr., CTR {r["CTR"]*100:.1f}%. '
            "Ya rankeas arriba; el problema es que el resultado no invita a clicar.",
            f"Reescribir SOLO el title y la meta description con un gancho ({GANCHOS[0]} / {GANCHOS[2]}). "
            "Cero cambios de contenido, efecto inmediato.",
            "Más clics con el mismo ranking, esfuerzo mínimo")

    # ---- CAMPERIZACION: aún "Próximamente" (lista de espera, no full competición) ----
    campz = df[df["Vertical"] == "CAMPERIZACION"]
    if not campz.empty:
        add("info", "SEO", "semanal", "vertical camperizacion", "CAMPERIZACION",
            "Camperización en pre-lanzamiento: capta lista de espera, no gastes en puja",
            f"{len(campz)} términos de camperización ({int(campz['Impresiones'].sum()):,} impr.). "
            "El servicio está 'Próximamente': aún no conviene competir a full en SEM.",
            "Mantener la landing /camperizacion captando leads (WhatsApp/email de lista de espera) y "
            "trabajar SEO informativo para llegar posicionado al lanzamiento. Puja SEM mínima o nula por ahora.",
            "Llegas al lanzamiento con demanda y posición ya calentadas")

    add("info", "Sistema", "semanal", "-", "INFORMACIONAL",
        "Valor de conversión real: requiere GA4 + Google Ads",
        "GSC da clics/impresiones/posición reales, pero NO el valor de pasarela (pernocta+seguro+kit) ni ROAS.",
        "Conectar GA4 para activar 'Valor Real vs Lead'.",
        "Desbloquea la auditoría de dinero, no solo de tráfico")

    orden = {"alta": 0, "media": 1, "info": 2}
    return sorted(recs, key=lambda x: orden[x["sev"]])


# ==========================================
# 2.d ANALISIS TEMPORAL + CONCLUSIONES EXPERTAS
#     Comparativa entre periodos y diagnostico de por que sube/baja el trafico,
#     con conocimiento del sector (alquiler+venta de campers) y de SEO.
# ==========================================
# Estacionalidad real del alquiler de camper en España (demanda de búsqueda).
ESTACIONALIDAD = {
    1: "baja (post-navidad)", 2: "baja, arranque de planificación de verano",
    3: "subida (Semana Santa se empieza a buscar)", 4: "alta (Semana Santa y puentes)",
    5: "alta (pre-verano, pico de reservas de julio/agosto)",
    6: "muy alta (planificación de verano en pleno apogeo)",
    7: "alta pero ya en ejecución (mucha búsqueda de última hora)",
    8: "media-alta (agosto, reservas de última hora y septiembre)",
    9: "media (escapadas de otoño, puente de octubre)",
    10: "media (puente de octubre/todos los santos)",
    11: "baja (valle estacional)", 12: "baja-media (repunte por regalos de Navidad, packs regalo)",
}


def resumen_periodo(ts, periodo):
    """Agrega la serie temporal a un mes concreto (str 'YYYY-MM')."""
    d = ts[ts["Mes"] == periodo]
    if d.empty:
        return None
    clics = int(d["Clics"].sum())
    impr = int(d["Impresiones"].sum())
    ctr = (clics / impr) if impr else 0
    cp = d.dropna(subset=["Posicion"])
    pos = ((cp["Posicion"] * cp["Impresiones"]).sum() / max(cp["Impresiones"].sum(), 1)) if not cp.empty else np.nan
    return {"clics": clics, "impr": impr, "ctr": ctr, "pos": pos, "n": len(d)}


def comparar_periodos(ts, mes_a, mes_b):
    """Compara dos meses y genera conclusiones EXPERTAS de por qué cambió el tráfico."""
    a = resumen_periodo(ts, mes_a)
    b = resumen_periodo(ts, mes_b)
    if a is None or b is None:
        return None, []
    # Aviso de mes incompleto: si un periodo tiene muchos menos registros que el otro
    aviso_parcial = None
    if a["n"] and b["n"] and (min(a["n"], b["n"]) / max(a["n"], b["n"]) < 0.5):
        menor = mes_b if b["n"] < a["n"] else mes_a
        aviso_parcial = ("⚠️", "Comparativa con un mes incompleto",
            f"{menor} tiene bastantes menos registros que el otro mes (probablemente está a medias). "
            "Los porcentajes pueden exagerar la caída/subida. Compara meses completos para leer bien la tendencia.")
    def pct(x, y):
        return ((y - x) / x * 100) if x else 0
    delta = {
        "clics": pct(a["clics"], b["clics"]),
        "impr": pct(a["impr"], b["impr"]),
        "ctr": pct(a["ctr"], b["ctr"]),
        "pos": (b["pos"] - a["pos"]) if (pd.notna(a["pos"]) and pd.notna(b["pos"])) else np.nan,
    }
    concl = []
    if aviso_parcial:
        concl.append(aviso_parcial)
    try:
        m_b = int(mes_b.split("-")[1])
    except Exception:
        m_b = None

    # 1) Diagnóstico de clics + causa raíz (impresiones vs CTR vs posición)
    if delta["clics"] <= -10:
        causa = "impresiones" if delta["impr"] <= -8 else ("posición" if (pd.notna(delta["pos"]) and delta["pos"] > 0.5) else "CTR")
        if causa == "impresiones":
            concl.append(("🔻", "Caída de clics por menos impresiones (demanda o indexación)",
                f"Los clics bajan {delta['clics']:.0f}% y las impresiones {delta['impr']:.0f}%. "
                "Google te muestra menos: o bajó la demanda estacional, o perdiste páginas indexadas "
                "(revisa el módulo Salud de Indexación: los 404 recientes encajan con esto)."))
        elif causa == "posición":
            concl.append(("🔻", "Caída de clics por pérdida de posiciones",
                f"Clics {delta['clics']:.0f}% y la posición media empeora {delta['pos']:.1f} puestos. "
                "Competencia o pérdida de relevancia: refuerza contenido y enlazado de las URLs clave."))
        else:
            concl.append(("🔻", "Caída de clics con impresiones estables = problema de CTR",
                f"Sigues apareciendo (impresiones {delta['impr']:+.0f}%) pero te clican menos "
                f"(CTR {delta['ctr']:+.0f}%). Suele ser title/meta poco atractivos o nuevos competidores "
                "con mejor snippet. Reescribe titles con ganchos."))
    elif delta["clics"] >= 10:
        motor = "más impresiones" if delta["impr"] >= 8 else ("mejor posición" if (pd.notna(delta["pos"]) and delta["pos"] < -0.5) else "mejor CTR")
        concl.append(("🔺", f"Subida de clics impulsada por {motor}",
            f"Clics {delta['clics']:+.0f}% (impresiones {delta['impr']:+.0f}%, CTR {delta['ctr']:+.0f}%, "
            f"posición {delta['pos']:+.1f}). Identifica qué páginas/keywords lo motivan y dóblalas."))
    else:
        concl.append(("➡️", "Tráfico estable entre ambos periodos",
            f"Variación de clics {delta['clics']:+.0f}%. Sin movimientos bruscos."))

    # 2) Lectura estacional del sector camper
    if m_b:
        concl.append(("📅", "Contexto estacional del sector (alquiler camper)",
            f"{mes_b}: demanda típicamente {ESTACIONALIDAD.get(m_b, 'variable')}. "
            "Compara la variación real con esta expectativa: si caes en temporada alta, es un problema tuyo; "
            "si caes en valle estacional, es mercado."))

    # 3) Palanca experta según posición media
    if pd.notna(b["pos"]):
        if b["pos"] > 10:
            concl.append(("🛠️", "Posición media fuera de página 1",
                f"Posición media {b['pos']:.1f}: gran parte de tus impresiones no reciben clic. "
                "El mayor retorno está en subir a Top 10 las keywords de más impresiones (ver quick-wins)."))
        elif b["pos"] <= 5:
            concl.append(("✅", "Posición media fuerte",
                f"Posición media {b['pos']:.1f}: estás arriba. El margen ahora está en CTR "
                "(titles/meta) y en captar keywords nuevas, no en subir posiciones."))
    return {"a": a, "b": b, "delta": delta, "mes_a": mes_a, "mes_b": mes_b}, concl


def tabla_rendimiento(df, top=100):
    """Prepara la tabla estilo GSC (Consulta/Página, Clics, Impresiones, CTR, Posición, Vertical)."""
    if df is None or df.empty:
        return None
    d = df.copy()
    d["Vertical"] = d["termino"].apply(clasifica_vertical)
    d["CTR %"] = (d["CTR"] * 100).round(1)
    d = d.rename(columns={"termino": "Término"})
    cols = ["Término", "Vertical", "Clics", "Impresiones", "CTR %", "Posicion"]
    d = d[cols].rename(columns={"Posicion": "Posición"})
    return d.sort_values("Clics", ascending=False).head(top)


# --- Estrategia de contenido: pensamiento crítico sobre datos REALES + sector ---
# Temas con tráfico probado en el mundo camper (patrones de intención que funcionan
# en el sector: rutas locales, normativa/pernocta, comparativas, guías prácticas).
TEMAS_SECTOR_CAMPER = [
    ("rutas y escapadas locales", "Rutas en camper cerca de Valencia (fin de semana)",
     "Las guías de rutas por comunidad captan tráfico transaccional local y estacional. "
     "Refuerza el km/noche y la cercanía a la base de Rafelbunyol."),
    ("normativa y pernocta", "Dónde pernoctar legalmente en camper en la Comunidad Valenciana",
     "La duda legal de aparcar/pernoctar es de altísima demanda informacional y fideliza. "
     "Poca competencia bien resuelta = posiciones rápidas."),
    ("comparativa de vehículos", "Mini van vs gran volumen: qué camper elegir según tu viaje",
     "Comparativas que ayudan a decidir capturan usuarios a mitad de embudo y enlazan a fichas."),
    ("primerizos / cómo funciona", "Primera vez en camper: guía completa para no perderte nada",
     "Contenido para primerizos amplía el mercado (gente que nunca ha alquilado) y reduce fricción."),
    ("mascotas", "Viajar en camper con perro: consejos y equipamiento",
     "El nicho pet-friendly es un diferencial real de Wheely Fog (supl. 35€). Poca competencia."),
    ("venta / ocasión", "Comprar una camper de ocasión con historial: qué mirar",
     "Contenido de venta que educa sobre el valor del historial de mantenimiento; madura leads de compra."),
]


def content_strategy_desde_datos(df_q, top_n=6):
    """Genera propuestas de contenido con pensamiento crítico:
    1) Oportunidades REALES de los datos GSC (muchas impresiones, mala posición).
    2) Temas con tráfico probado en el sector camper.
    Cada propuesta lleva su porqué analítico."""
    props = []
    if df_q is not None and not df_q.empty:
        d = df_q.copy()
        d["Vertical"] = d["termino"].apply(clasifica_vertical)
        # Oportunidad = aparece mucho (impresiones) pero mal posicionada (>8) y no es marca
        op = d[(d["Posicion"] > 8) & (d["Impresiones"] >= 200) & (d["Vertical"] != "MARCA")]
        op = op.sort_values("Impresiones", ascending=False).head(top_n)
        for _, r in op.iterrows():
            props.append({
                "titulo": f"Contenido para: “{r['termino']}”",
                "keyword": r["termino"],
                "vertical": r["Vertical"],
                "origen": "DATO REAL (GSC)",
                "metrica": f"{int(r['Impresiones']):,} impresiones/periodo · posición {r['Posicion']:.0f} · CTR {r['CTR']*100:.1f}%",
                "porque": (f"Ya apareces {int(r['Impresiones']):,} veces por esta búsqueda pero en posición "
                           f"{r['Posicion']:.0f}: hay demanda comprobada que no capturas. Un artículo enfocado "
                           "aquí ataca tráfico que Google ya te asocia. Máxima prioridad por dato real."),
            })
    # Completar con temas de sector probados si faltan propuestas
    for tema, titulo, porque in TEMAS_SECTOR_CAMPER:
        if len(props) >= top_n + 3:
            break
        props.append({
            "titulo": titulo, "keyword": tema,
            "vertical": clasifica_vertical(titulo),
            "origen": "PATRÓN DE SECTOR",
            "metrica": "Tema con demanda probada en el nicho camper",
            "porque": porque,
        })
    return props


def sugerencia_foto(keyword, vertical):
    """Sugiere qué FOTO buscar manualmente (banco libre) + alt text SEO."""
    k = str(keyword).lower()
    if vertical == "VENTA":
        desc = ("Foto real de la camper en venta: exterior limpio + detalle de interior cuidado. "
                "Evita fondos genéricos; transmite 'fiable y con historial'.")
        alt = f"Comprar camper de ocasión con historial en Valencia — {keyword}"
    elif "perro" in k or "mascota" in k:
        desc = "Foto de un perro asomado o dentro de una camper, ambiente relajado y natural."
        alt = f"Viajar en camper con perro — {keyword}"
    elif "ruta" in k or "escapada" in k or "pernocta" in k:
        desc = ("Camper aparcada en un paraje natural de la Comunidad Valenciana (Albufera, costa, "
                "montaña), sillas de camping y luz de atardecer.")
        alt = f"Escapada en camper desde Valencia — {keyword}"
    else:
        desc = ("Interior acogedor de camper con cama montada y buena luz, o pareja disfrutando junto "
                "al vehículo. Aspecto premium y real, no de catálogo.")
        alt = f"Alquiler de camper en Valencia — {keyword}"
    return desc, alt
#    un LLM (Claude tool-use) que razona sobre datos reales.
# ==========================================
INTENT_COMPRA = ["comprar", "compra", "segunda mano", "venta", "vender", "ocasion", "km0", "km 0"]
INTENT_ALQUILER = ["alquiler", "alquilar", "rent", "fin de semana", "ruta", "escapada"]


def detecta_intencion(kw):
    k = kw.lower()
    if any(t in k for t in INTENT_COMPRA):
        return "compra"
    if any(t in k for t in INTENT_ALQUILER):
        return "alquiler"
    return "informacional"


def build_recommendations(df_cross, df_seo):
    """Genera la lista priorizada de recomendaciones diarias/semanales."""
    recs = []
    rid = 0
    for _, r in df_cross.iterrows():
        kw = r["Keyword"]
        intent = detecta_intencion(kw)
        es_marca = "wheely fog" in kw.lower()
        gasto = r["SEM Gasto (€)"]
        roas = r["SEM ROAS"]
        pos = r["SEO Posición"]

        # R1 - VERTICAL VENTA: NO es fuga (Wheely Fog también vende campers ex-flota).
        # Solo es problema si el término erosiona el premium ('barato/chollo') o si el
        # tráfico de compra está cayendo en campañas de ALQUILER (mezcla de verticales).
        if intent == "compra" and gasto > 0:
            rid += 1
            # ¿término que erosiona posicionamiento premium de la venta?
            erosiona = ("erosiona_premium" in globals() and erosiona_premium(kw))
            if erosiona:
                recs.append(dict(id=rid, sev="media", canal="SEM", freq="semanal", kw=kw,
                    titulo="Término de compra 'low-cost' que choca con tu venta premium",
                    detalle=f'"{kw}" busca precio bajo, pero tu flota de venta es ocasión premium con '
                            f'historial (35k-80k€). Gasta {gasto:,.2f} €/mes con ROAS {roas:.1f}x.',
                    accion="Refinar el copy hacia 'calidad-historial-precio' y filtrar negativas de saldo "
                           "('gratis', 'regalada'). NO negativizar 'ocasión/segunda mano/km' (son tu producto).",
                    impacto="Mejoras la calidad del lead de venta sin perder demanda real"))
            else:
                recs.append(dict(id=rid, sev="media", canal="Cross", freq="semanal", kw=kw,
                    titulo="Tráfico de VENTA: separar de las campañas de alquiler",
                    detalle=f'"{kw}" es intención de compra legítima (vendemos campers ex-flota con historial). '
                            f'Gasta {gasto:,.2f} €/mes con ROAS {roas:.1f}x. No es fuga: es otra vertical.',
                    accion=f'Asegurar que "{kw}" vive en una campaña de VENTA propia (no en alquiler) con su '
                           'landing /venta y su KPI de lead de compra. Si está en una campaña de alquiler, moverlo.',
                    impacto="Atribuyes bien el gasto y mides la venta por su propio embudo"))
            continue

        # R2 - FUGA: gasto alto y ROAS bajo (sin ser marca)
        if not es_marca and roas < 1 and gasto > 300:
            rid += 1
            recs.append(dict(id=rid, sev="alta", canal="SEM", freq="diaria", kw=kw,
                titulo="Fuga de presupuesto (ROAS < 1)",
                detalle=f'"{kw}" gasta {gasto:,.2f} € y devuelve ROAS {roas:.1f}x. Pierde dinero en cada clic.',
                accion="Pausar el grupo de anuncios o bajar puja agresivamente y revisar landing/coincidencia.",
                impacto=f"Recuperas margen sobre {gasto:,.2f} €/mes"))
            continue

        # R3 - CANIBALIZACION: Top SEO solido + ROAS SEM flojo -> bajar puja (NO si es marca)
        if not es_marca and pos <= 3 and roas < 2 and gasto > 100:
            rid += 1
            recs.append(dict(id=rid, sev="media", canal="Cross", freq="semanal", kw=kw,
                titulo="Canibalización: ya eres Top 3 orgánico",
                detalle=f'"{kw}" está en posición {pos:.1f} orgánica con ROAS SEM {roas:.1f}x. Pagas clics que ganarías gratis.',
                accion="Reducir puja SEM un 40-60% y reinvertir en términos sin posición orgánica.",
                impacto="Recortas gasto redundante manteniendo el clic orgánico"))
            continue

        # R4 - PROTECCION DE MARCA (corrige la incoherencia del original)
        if es_marca:
            rid += 1
            recs.append(dict(id=rid, sev="info", canal="SEM", freq="semanal", kw=kw,
                titulo="Proteger marca (NO pausar)",
                detalle=f'"{kw}" tiene ROAS {roas:.1f}x y defenderla cuesta poco. Competidores y plataformas P2P (Yescapa, etc.) pujan tu marca.',
                accion="Mantener campaña de marca activa. Defenderla es barato y evita robo de tráfico de marca.",
                impacto="Blindas el tráfico de mayor conversión de la cuenta"))
            continue

        # R5 - OPORTUNIDAD SEO: paga SEM pero sin posicion organica decente
        if pos > 8 and roas >= 1:
            rid += 1
            recs.append(dict(id=rid, sev="media", canal="SEO", freq="semanal", kw=kw,
                titulo="Crear/optimizar contenido orgánico",
                detalle=f'"{kw}" depende 100% de SEM (posición {pos:.1f}). Sin contenido, el coste nunca baja.',
                accion="Crear landing optimizada para esta keyword y meterla en el calendario editorial.",
                impacto="Reduce dependencia de puja a medio plazo"))

    # R6 - SEO: URLs con buena posicion pero conversion bajisima (intencion mal alineada)
    for _, s in df_seo.iterrows():
        if s["Posición Media"] <= 5 and s["Tasa Conversión"] < 0.005 and s["Tráfico Mensual"] > 500:
            rid += 1
            recs.append(dict(id=rid, sev="media", canal="SEO", freq="semanal", kw=s["Palabra Clave Principal"],
                titulo="Tráfico que no convierte (revisar intención de la URL)",
                detalle=f'{s["URL"]} posiciona top ({s["Posición Media"]:.1f}) y trae {int(s["Tráfico Mensual"]):,} visitas/mes, pero convierte al {s["Tasa Conversión"]*100:.2f}%. Atrae informacional, no comprador.',
                accion="Añadir CTA de reserva y bloques de oferta a la URL para capturar intención transaccional.",
                impacto=f'Monetiza {int(s["Tráfico Mensual"]):,} visitas/mes ya existentes'))

    orden = {"alta": 0, "media": 1, "info": 2}
    return sorted(recs, key=lambda x: orden[x["sev"]])


# Cargar dataframes a memoria
df_sem_raw = load_sem_large_dataset()
df_seo = load_seo_large_dataset()
df_proposals = load_content_proposals()
df_cross = load_cross_channel_matrix()

# Estado de sesion (fix botones anidados + cola de acciones)
if "articulos" not in st.session_state:
    st.session_state.articulos = {}
if "aprobados" not in st.session_state:
    st.session_state.aprobados = {}
if "rec_estado" not in st.session_state:
    st.session_state.rec_estado = {}
if "gsc_queries" not in st.session_state:
    st.session_state.gsc_queries = None
if "gsc_pages" not in st.session_state:
    st.session_state.gsc_pages = None
if "gsc_index" not in st.session_state:
    st.session_state.gsc_index = []  # lista de (issue, df_urls)
if "gsc_ts" not in st.session_state:
    st.session_state.gsc_ts = None  # serie temporal (Chart.csv)
if "ads_changes" not in st.session_state:
    st.session_state.ads_changes = None  # historial de cambios de Google Ads
if "file_registry" not in st.session_state:
    st.session_state.file_registry = []  # [(nombre, seccion, detalle, ts)]
if "articulos_log" not in st.session_state:
    st.session_state.articulos_log = []  # cronología de artículos generados

# ==========================================
# 4. BARRA LATERAL Y FILTROS GLOBALES
# ==========================================
with st.sidebar:
    st.markdown("## 🚐 WheelyFog AI")
    st.markdown("Gestión integrada de canales digitales.")
    st.divider()

    hemisferio = st.radio(
        "Módulos del Sistema:",
        (
            "🤖 Recomendaciones del Agente",
            "📡 SEO Real (Search Console)",
            "🛰️ SEM (Performance & Subastas)",
            "📝 SEO (Content Factory Orgánico)",
            "🔑 Auditoría Cruzada (SEO vs SEM)",
        ),
    )
    st.divider()

    st.markdown("### 📤 Sube tus archivos (auto-detecta SEO/SEM)")
    st.caption("**SEO**: ZIP de GSC (Rendimiento/Indexación) o CSV/XLSX. "
               "**SEM**: 'Informe de historial de cambios' de Google Ads (CSV/XLSX).")
    up_files = st.file_uploader("Arrastra aquí cualquier archivo",
                                type=["zip", "csv", "xlsx", "xls"],
                                accept_multiple_files=True, key="gsc_up")
    if up_files:
        for uf in up_files:
            seccion, detalle = None, ""
            # 1) ¿Es historial de cambios de Google Ads? (SEM)
            es_ads = ("cambio" in uf.name.lower() or "historial" in uf.name.lower()
                      or "change" in uf.name.lower())
            ads_df = None
            if es_ads or uf.name.lower().endswith((".csv", ".xlsx", ".xls")):
                try:
                    ads_df = parse_ads_change_history(uf.getvalue(), uf.name)
                except Exception:
                    ads_df = None
            if ads_df is not None and len(ads_df) > 0:
                st.session_state.ads_changes = ads_df
                seccion, detalle = "SEM", f"{len(ads_df)} cambios de Ads"
                st.success(f"🛰️ SEM · {uf.name}: {detalle}")
            else:
                # 2) Si no, tratar como GSC (SEO)
                r = parse_gsc_upload(uf)
                got = False
                if r["queries"] is not None:
                    st.session_state.gsc_queries = r["queries"]; got = True
                if r["pages"] is not None:
                    st.session_state.gsc_pages = r["pages"]; got = True
                if r["index_urls"] is not None:
                    issue = r["index_issue"] or uf.name
                    st.session_state.gsc_index = [x for x in st.session_state.gsc_index if x[0] != issue]
                    st.session_state.gsc_index.append((issue, r["index_urls"])); got = True
                if r.get("timeseries") is not None:
                    st.session_state.gsc_ts = r["timeseries"]; got = True
                if got:
                    seccion, detalle = "SEO", r["msg"]
                    st.success(f"📡 SEO · {uf.name}: {r['msg']}")
                else:
                    st.warning(f"❓ {uf.name}: {r['msg']}")
            if seccion:
                st.session_state.file_registry = [
                    x for x in st.session_state.file_registry if x[0] != uf.name]
                st.session_state.file_registry.append(
                    (uf.name, seccion, detalle, datetime.today().strftime("%Y-%m-%d %H:%M")))

    # Registro de archivos en memoria (para no perder de vista qué hay cargado)
    if st.session_state.file_registry:
        st.markdown("##### 🗂️ Archivos en memoria")
        for nombre, seccion, detalle, ts in st.session_state.file_registry:
            icono = "🛰️" if seccion == "SEM" else "📡"
            st.caption(f"{icono} **{seccion}** · {nombre[:28]} · {detalle}")

    st.divider()
    st.markdown("### 📅 Filtro Temporal (SEM demo)")
    dias_filtro = st.slider("Rango de análisis (días previos):", 7, 90, 30, 1)
    fecha_limite = datetime.today() - timedelta(days=dias_filtro)
    df_sem = df_sem_raw[pd.to_datetime(df_sem_raw["Fecha"]) >= fecha_limite]

    st.divider()
    if st.session_state.ads_changes is not None:
        st.success(f"🟢 Google Ads (historial): {len(st.session_state.ads_changes)} cambios")
    else:
        st.warning("🟡 Google Ads: sube el historial de cambios")
    if st.session_state.gsc_queries is not None or st.session_state.gsc_pages is not None:
        st.success("🟢 Search Console: datos cargados")
    else:
        st.warning("🟡 Search Console: sin datos (sube el ZIP)")
    st.warning("🟡 GA4: sin conectar")


# ==========================================
# 5. MODULO: RECOMENDACIONES DEL AGENTE (NUEVO)
# ==========================================
if hemisferio == "🤖 Recomendaciones del Agente":
    st.title("🤖 Recomendaciones del Agente")
    st.markdown("Sugerencias **diarias y semanales** sobre lo que no está funcionando: choque de intención compra/alquiler, fugas de presupuesto, canibalización y oportunidades SEO. Cada acción requiere tu aprobación.")

    # Si hay datos REALES de GSC cargados, esas recomendaciones van primero
    recomendaciones = build_gsc_recommendations(st.session_state.gsc_queries)
    if st.session_state.gsc_queries is None:
        st.info("💡 Sube el ZIP de Search Console en la barra lateral para obtener recomendaciones sobre datos REALES. Mientras tanto, se muestran las de demostración.")
    recomendaciones += build_recommendations(df_cross, df_seo)
    activas = [r for r in recomendaciones if r["id"] not in st.session_state.rec_estado]

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric("Recomendaciones activas", str(len(activas)), "cross")
    with c2: render_metric("Prioridad alta", str(len([r for r in activas if r["sev"] == "alta"])), "sem", "Acción hoy", "down")
    with c3: render_metric("Frecuencia diaria", str(len([r for r in recomendaciones if r["freq"] == "diaria"])), "cross")
    with c4: render_metric("Frecuencia semanal", str(len([r for r in recomendaciones if r["freq"] == "semanal"])), "seo")

    st.divider()

    for r in recomendaciones:
        estado = st.session_state.rec_estado.get(r["id"])
        tag_class = {"alta": "tag-alta", "media": "tag-media", "info": "tag-info"}[r["sev"]]
        tag_label = {"alta": "Prioridad alta", "media": "Prioridad media", "info": "Informativo"}[r["sev"]]
        opacity = "opacity:0.55;" if estado else ""
        st.markdown(f"""
        <div class="rec-card" style="{opacity}">
            <div style="margin-bottom:8px;">
                <span class="tag {tag_class}">{tag_label}</span>
                <span class="tag tag-canal">{r['canal']}</span>
                <span class="tag tag-canal">↻ {r['freq']}</span>
                <code style="color:#5f6368;font-size:.78rem;">{r['kw']}</code>
            </div>
            <div style="font-weight:700;font-size:1.05rem;">{r['titulo']}</div>
            <div style="font-size:.9rem;color:#3c4043;margin-top:4px;">{r['detalle']}</div>
            <div style="font-size:.9rem;margin-top:6px;"><b>Acción sugerida:</b> {r['accion']}</div>
            <div style="font-size:.9rem;color:#137333;font-weight:600;margin-top:2px;">{r['impacto']}</div>
        </div>
        """, unsafe_allow_html=True)

        if estado == "aplicada":
            st.success("✓ Añadida a la cola de ejecución (pendiente de push a Google Ads).")
        elif estado == "descartada":
            cdesh1, cdesh2 = st.columns([3, 1])
            cdesh1.caption("Descartada.")
            if cdesh2.button("Deshacer", key=f"undo_{r['id']}"):
                st.session_state.rec_estado.pop(r["id"], None)
                st.rerun()
        else:
            b1, b2, _ = st.columns([2, 1, 4])
            if b1.button("✓ Aplicar (a cola de aprobación)", key=f"apply_{r['id']}"):
                st.session_state.rec_estado[r["id"]] = "aplicada"
                st.rerun()
            if b2.button("Descartar", key=f"dismiss_{r['id']}"):
                st.session_state.rec_estado[r["id"]] = "descartada"
                st.rerun()


# ==========================================
# 6. MODULO SEM: PERFORMANCE Y BUSCADOR
# ==========================================
elif hemisferio == "📡 SEO Real (Search Console)":
    st.title("📡 SEO Real (Search Console)")
    st.markdown("Datos **reales** de tu web leídos de los archivos de Google Search Console. Gratis, sin API.")

    dfq = st.session_state.gsc_queries
    dfp = st.session_state.gsc_pages
    idx = st.session_state.gsc_index

    if dfq is None and dfp is None and not idx:
        st.info("⬅️ Sube en la barra lateral el **ZIP** que exportas de GSC "
                "(Rendimiento → Exportar, o Indexación → un motivo → Exportar). "
                "También valen CSV o XLSX sueltos.")
    else:
        tab_perf, tab_evo, tab_kw, tab_pag, tab_idx = st.tabs(
            ["📈 Resumen", "📆 Evolución y Comparativa", "🔍 Consultas", "🔗 Páginas", "🩺 Salud de Indexación"])

        # --- Resumen ---
        with tab_perf:
            base = dfq if dfq is not None else dfp
            if base is not None:
                base = base.copy()
                base["Vertical"] = base["termino"].apply(clasifica_vertical)
                clics = int(base["Clics"].sum())
                impr = int(base["Impresiones"].sum())
                ctr_g = (clics / impr) if impr else 0
                cp = base.dropna(subset=["Posicion"])
                pos_p = ((cp["Posicion"] * cp["Impresiones"]).sum() /
                         max(cp["Impresiones"].sum(), 1)) if not cp.empty else 0
                c1, c2, c3, c4 = st.columns(4)
                with c1: render_metric("Clics reales", f"{clics:,}", "seo")
                with c2: render_metric("Impresiones", f"{impr:,}", "seo")
                with c3: render_metric("CTR medio", f"{ctr_g*100:.1f}%", "seo")
                with c4: render_metric("Posición media (pond.)", f"{pos_p:.1f}", "seo")
                st.divider()
                st.subheader("📊 Tráfico real por Vertical de negocio")
                dv = base.groupby("Vertical").agg(
                    Clics=("Clics", "sum"), Impresiones=("Impresiones", "sum"),
                    Terminos=("termino", "count")).reset_index()
                fig = px.bar(dv, x="Vertical", y="Clics", color="Vertical",
                             color_discrete_map=VERT_COLORS, text="Terminos",
                             title="¿De qué vertical vienen los clics reales?")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sube el archivo de Consultas o Páginas para ver el resumen.")

        # --- Evolución y Comparativa temporal ---
        with tab_evo:
            ts = st.session_state.gsc_ts
            if ts is None or ts.empty:
                st.info("Para el filtro temporal y las comparativas necesito la **serie temporal**. "
                        "Viene dentro del ZIP de Rendimiento de GSC (archivo Chart.csv). "
                        "Vuelve a subir ese ZIP completo y aparecerá aquí automáticamente.")
            else:
                st.markdown("Evolución real por periodos y **comparativa entre dos meses** con "
                            "diagnóstico experto de por qué sube o baja el tráfico.")
                # Métrica a graficar + filtro de meses
                meses = sorted(ts["Mes"].unique())
                fc1, fc2 = st.columns([1, 2])
                metrica = fc1.selectbox("Métrica:", ["Clics", "Impresiones", "CTR", "Posicion"])
                rango = fc2.select_slider("Rango de meses:", options=meses,
                                          value=(meses[0], meses[-1]))
                tsf = ts[(ts["Mes"] >= rango[0]) & (ts["Mes"] <= rango[1])]
                # Serie agregada por mes
                agg = tsf.groupby("Mes").agg(
                    Clics=("Clics", "sum"), Impresiones=("Impresiones", "sum"),
                    CTR=("CTR", "mean"), Posicion=("Posicion", "mean")).reset_index()
                fig = px.line(agg, x="Mes", y=metrica, markers=True,
                              title=f"Evolución de {metrica} por mes")
                if metrica == "Posicion":
                    fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)

                st.divider()
                st.subheader("🆚 Comparar dos meses")
                cc1, cc2 = st.columns(2)
                mes_a = cc1.selectbox("Mes base (antes):", meses, index=max(0, len(meses) - 2))
                mes_b = cc2.selectbox("Mes a comparar (después):", meses, index=len(meses) - 1)
                comp, conclusiones = comparar_periodos(ts, mes_a, mes_b)
                if comp:
                    a, b, delta = comp["a"], comp["b"], comp["delta"]
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Clics", f"{b['clics']:,}", f"{delta['clics']:+.0f}%")
                    m2.metric("Impresiones", f"{b['impr']:,}", f"{delta['impr']:+.0f}%")
                    m3.metric("CTR", f"{b['ctr']*100:.1f}%", f"{delta['ctr']:+.0f}%")
                    pos_txt = f"{delta['pos']:+.1f}" if pd.notna(delta['pos']) else "n/d"
                    m4.metric("Posición media", f"{b['pos']:.1f}" if pd.notna(b['pos']) else "n/d",
                              pos_txt, delta_color="inverse")
                    st.markdown(f"##### 🧠 Conclusiones del agente ({mes_a} → {mes_b})")
                    for icono, titulo, detalle in conclusiones:
                        st.markdown(f"**{icono} {titulo}**  \n{detalle}")
                else:
                    st.warning("No hay datos suficientes en alguno de los dos meses elegidos.")

        # --- Consultas (tabla estilo GSC) ---
        with tab_kw:
            if dfq is not None:
                q = st.text_input("Filtrar consultas:")
                tabla = tabla_rendimiento(dfq, top=1000)
                if q:
                    tabla = tabla[tabla["Término"].str.contains(q, case=False, na=False)]
                st.caption(f"{len(tabla)} consultas reales · clics, impresiones, CTR y posición.")
                st.dataframe(tabla, use_container_width=True, hide_index=True)
            else:
                st.info("No has subido el archivo de Consultas (Queries).")

        # --- Páginas (tabla estilo GSC) ---
        with tab_pag:
            if dfp is not None:
                tabla_p = tabla_rendimiento(dfp, top=1000).rename(columns={"Término": "Página"})
                qp = st.text_input("Filtrar páginas:")
                if qp:
                    tabla_p = tabla_p[tabla_p["Página"].str.contains(qp, case=False, na=False)]
                st.caption(f"{len(tabla_p)} páginas reales.")
                st.dataframe(tabla_p, use_container_width=True, hide_index=True)
            else:
                st.info("No has subido el archivo de Páginas (Pages).")

        # --- Salud de Indexación ---
        with tab_idx:
            if not idx:
                st.info("Sube el ZIP de **Indexación → un motivo → Exportar** "
                        "(404, noindex, redirect...) para listar las URLs afectadas.")
            else:
                st.caption("URLs excluidas/rotas por motivo, con la vertical afectada.")
                for issue, dfu in idx:
                    st.markdown(f"**{issue}** — {len(dfu)} URLs")
                    du = dfu.copy()
                    if "URL" in du.columns:
                        du["Vertical afectada"] = du["URL"].apply(
                            lambda u: clasifica_vertical(str(u).replace("-", " ").replace("/", " ")))
                        st.bar_chart(du["Vertical afectada"].value_counts())
                    st.dataframe(du, use_container_width=True, hide_index=True)
                    st.divider()


elif hemisferio == "🛰️ SEM (Performance & Subastas)":
    st.title("🛰️ Director de Performance (SEM Ads)")

    # --- HONESTIDAD DE DATOS: S/N de lo que realmente tenemos conectado ---
    tiene_ads = False          # Google Ads API: no conectada
    tiene_valor = False        # Valor de conversión (pasarela): requiere GA4/Ads
    st.markdown("### 📡 ¿Tenemos estos datos? (estado real de las fuentes)")
    d1, d2, d3, d4 = st.columns(4)
    def sn(col, titulo, disponible, nota):
        with col:
            estado = "✅ Sí" if disponible else "❌ No"
            color = "seo" if disponible else "sem"
            render_metric(titulo, estado, color)
            st.caption(nota)
    sn(d1, "Gasto publicitario", tiene_ads, "Fuente: Google Ads API (sin conectar)")
    sn(d2, "Retorno / Valor conv.", tiene_valor, "Fuente: GA4 + pasarela (sin conectar)")
    sn(d3, "ROAS real", tiene_ads and tiene_valor, "Necesita gasto + valor")
    sn(d4, "CPA real", tiene_ads and tiene_valor, "Necesita gasto + conversiones")

    if not (tiene_ads and tiene_valor):
        st.error("⚠️ **No hay datos reales de SEM todavía.** Antes mostrábamos cifras de retorno/ROAS "
                 "que eran de demostración (falsas). Para no engañar, ahora se marcan como ❌ No. "
                 "Para activarlas hay que conectar: **Google Ads API** (gasto, impresiones, clics de pago) "
                 "y **GA4 + valor de pasarela** (pernocta + seguro + kit) para el retorno.")
        st.info("💡 Lo que **sí** es real y puedes explotar hoy está en **📡 SEO Real (Search Console)**: "
                "clics, impresiones, CTR y posición orgánicos.")

    with st.expander("Ver todavía la maqueta de demostración (datos NO reales)"):
        total_gasto = df_sem["Coste (€)"].sum()
        total_retorno = df_sem["Valor (€)"].sum()
        total_conv = df_sem["Conversiones"].sum()
        roas_global = total_retorno / total_gasto if total_gasto > 0 else 0
        cpa_global = total_gasto / total_conv if total_conv > 0 else 0
        st.caption("⚠️ Cifras sintéticas para probar la interfaz. No son de wheelyfog.com.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gasto (demo)", f"{total_gasto:,.2f} €")
        c2.metric("Retorno (demo)", f"{total_retorno:,.2f} €")
        c3.metric("ROAS (demo)", f"{roas_global:.2f}x")
        c4.metric("CPA (demo)", f"{cpa_global:.2f} €")
        df_trend = df_sem.groupby("Fecha").agg({"Coste (€)": "sum", "Valor (€)": "sum"}).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_trend["Fecha"], y=df_trend["Coste (€)"], name="Inversión (€)", marker_color=COLORS["sem"]))
        fig.add_trace(go.Scatter(x=df_trend["Fecha"], y=df_trend["Valor (€)"], mode="lines+markers", name="Retorno (€)", line=dict(color=COLORS["global"], width=3)))
        fig.update_layout(barmode="group", hovermode="x unified", title="Evolución (demo, no real)")
        st.plotly_chart(fig, use_container_width=True)

    # --- TABLA REAL: términos orgánicos que sí funcionan (de GSC) ---
    st.divider()
    st.subheader("🔍 Términos con buen rendimiento (datos REALES de Search Console)")
    dfq_sem = st.session_state.gsc_queries
    if dfq_sem is None:
        st.info("Sube el ZIP de Search Console (barra lateral) para ver aquí tus términos reales, "
                "identificar los que mejor convierten en orgánico y decidir cuáles reforzar con SEM cuando lo conectes.")
    else:
        tabla = tabla_rendimiento(dfq_sem, top=200)
        f1, f2 = st.columns([2, 1])
        q_txt = f1.text_input("Filtrar término (ej: valencia, alquiler, ocasión):", key="sem_qf")
        v_sel = f2.multiselect("Vertical:", list(VERT_COLORS.keys()),
                               default=list(VERT_COLORS.keys()), key="sem_vf")
        tv = tabla[tabla["Vertical"].isin(v_sel)]
        if q_txt:
            tv = tv[tv["Término"].str.contains(q_txt, case=False, na=False)]
        st.caption(f"{len(tv)} términos · ordenados por clics reales. "
                   "Los de alto CTR y buena posición son candidatos a proteger/escalar en SEM.")
        st.dataframe(tv, use_container_width=True, hide_index=True)

    # --- HISTORIAL DE CAMBIOS DE GOOGLE ADS: frecuencia de trabajo ---
    st.divider()
    st.subheader("🗓️ Frecuencia de trabajo en la cuenta (historial de cambios)")
    ch = st.session_state.ads_changes
    if ch is None:
        st.info("Sube el **'Informe de historial de cambios'** de Google Ads (barra lateral) para "
                "medir con qué frecuencia se ha trabajado la cuenta: cuántos cambios, quién los hizo y cuándo. "
                "Ideal para auditar la actividad de la agencia.")
    else:
        fmin, fmax = ch["Fecha"].min().date(), ch["Fecha"].max().date()
        st.caption(f"Historial disponible: {fmin} → {fmax} · {len(ch)} cambios totales.")

        modo = st.radio("Modo:", ["Un rango", "Comparar dos rangos"], horizontal=True)

        def resumen_rango(df, ini, fin):
            d = df[(df["Fecha"].dt.date >= ini) & (df["Fecha"].dt.date <= fin)]
            dias = max((fin - ini).days + 1, 1)
            semanas = max(dias / 7, 0.14)
            n = len(d)
            dias_activos = d["Fecha"].dt.date.nunique()
            return {"n": n, "dias": dias, "por_semana": n / semanas,
                    "dias_activos": dias_activos, "cobertura": dias_activos / dias,
                    "por_usuario": d["Usuario"].value_counts().to_dict(),
                    "por_campana": d["Campaña"].value_counts().to_dict(), "df": d}

        def pinta_resumen(r, etiqueta=""):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Cambios {etiqueta}", r["n"])
            c2.metric("Media/semana", f"{r['por_semana']:.1f}")
            c3.metric("Días con actividad", r["dias_activos"])
            c4.metric("Cobertura", f"{r['cobertura']*100:.0f}%",
                      help="% de días del rango en los que se tocó algo")

        if modo == "Un rango":
            col1, col2 = st.columns(2)
            ini = col1.date_input("Desde:", value=fmin, min_value=fmin, max_value=fmax, key="ads_i1")
            fin = col2.date_input("Hasta:", value=fmax, min_value=fmin, max_value=fmax, key="ads_f1")
            if ini <= fin:
                r = resumen_rango(ch, ini, fin)
                pinta_resumen(r)
                # Diagnóstico experto de la cadencia
                if r["por_semana"] < 1:
                    st.warning("⚠️ Cadencia **baja**: menos de 1 cambio/semana. Una cuenta de Ads activa "
                               "suele requerir revisión semanal (negativas, pujas, creatividades). Posible cuenta "
                               "desatendida o en piloto automático.")
                elif r["por_semana"] > 8:
                    st.info("Cadencia **alta**: mucha actividad. Verifica que no sea 'ruido' (cambios pequeños "
                            "repetidos) sin impacto real en rendimiento.")
                else:
                    st.success("Cadencia **saludable** de optimización continua.")

                g1, g2 = st.columns(2)
                with g1:
                    st.markdown("**Cambios por mes**")
                    serie = r["df"].groupby("Mes").size()
                    st.bar_chart(serie)
                with g2:
                    st.markdown("**Quién trabajó la cuenta**")
                    st.bar_chart(pd.Series(r["por_usuario"]))
                with st.expander("Ver detalle de cambios"):
                    st.dataframe(r["df"][["Fecha", "Usuario", "Campaña", "Cambios"]]
                                 .sort_values("Fecha", ascending=False),
                                 use_container_width=True, hide_index=True)
            else:
                st.error("La fecha 'Desde' debe ser anterior a 'Hasta'.")
        else:
            st.markdown("**Rango A**")
            a1, a2 = st.columns(2)
            ia = a1.date_input("A · Desde:", value=fmin, min_value=fmin, max_value=fmax, key="ads_ia")
            fa = a2.date_input("A · Hasta:", value=fmin + timedelta(days=90), min_value=fmin, max_value=fmax, key="ads_fa")
            st.markdown("**Rango B**")
            b1, b2 = st.columns(2)
            ib = b1.date_input("B · Desde:", value=fmax - timedelta(days=90), min_value=fmin, max_value=fmax, key="ads_ib")
            fb = b2.date_input("B · Hasta:", value=fmax, min_value=fmin, max_value=fmax, key="ads_fb")
            if ia <= fa and ib <= fb:
                ra, rb = resumen_rango(ch, ia, fa), resumen_rango(ch, ib, fb)
                cA, cB = st.columns(2)
                with cA:
                    st.markdown(f"##### 🅰️ {ia} → {fa}")
                    pinta_resumen(ra, "A")
                with cB:
                    st.markdown(f"##### 🅱️ {ib} → {fb}")
                    pinta_resumen(rb, "B")
                # Conclusión comparativa
                if ra["por_semana"] > 0:
                    var = (rb["por_semana"] - ra["por_semana"]) / ra["por_semana"] * 100
                    if var <= -30:
                        st.warning(f"🔻 La actividad **cayó {abs(var):.0f}%** por semana de A a B. "
                                   "La cuenta se está trabajando menos que antes.")
                    elif var >= 30:
                        st.info(f"🔺 La actividad **subió {var:.0f}%** por semana de A a B.")
                    else:
                        st.success(f"➡️ Actividad estable entre rangos ({var:+.0f}%/semana).")
            else:
                st.error("Revisa las fechas: cada 'Desde' debe ser anterior a su 'Hasta'.")


# ==========================================
# 7. MODULO SEO: CONTENT FACTORY
# ==========================================
elif hemisferio == "📝 SEO (Content Factory Orgánico)":
    st.title("📝 Director de Contenidos Autónomo (SEO)")
    st.markdown("Análisis SERP, volumen y fábrica de contenidos automatizada.")

    trafico_total = df_seo["Tráfico Mensual"].sum()
    # FIX: posicion media PONDERADA por trafico (no media aritmetica)
    pos_ponderada = (df_seo["Posición Media"] * df_seo["Tráfico Mensual"]).sum() / trafico_total
    top3 = int((df_seo["Posición Media"] <= 3).sum())

    c1, c2, c3 = st.columns(3)
    with c1: render_metric("Visitas Orgánicas/Mes", f"{trafico_total:,}", "seo", "+8.4%", "up")
    with c2: render_metric("Posición Media (ponderada)", f"{pos_ponderada:.1f}", "seo", "-0.4", "up")
    with c3: render_metric("Keywords en Top 3", str(top3), "seo")

    st.divider()
    st.subheader("🔍 Buscador de Volumen Orgánico y URLs")
    seo_search = st.text_input("Ej: ruta, camper, pernocta...")
    if seo_search:
        mask = df_seo["Palabra Clave Principal"].str.contains(seo_search, case=False, na=False) | df_seo["URL"].str.contains(seo_search, case=False, na=False)
        df_sf = df_seo[mask]
        if not df_sf.empty:
            st.dataframe(df_sf.sort_values("Tráfico Mensual", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.warning("Sin coincidencias. ¡Oportunidad para crear contenido nuevo!")

    st.divider()
    st.subheader("🏭 Fábrica de Contenidos (estrategia sobre datos reales)")
    dfq_cf = st.session_state.gsc_queries
    if dfq_cf is not None:
        st.success("✅ Usando tus datos reales de Search Console para priorizar por demanda comprobada.")
    else:
        st.info("💡 Sube el ZIP de GSC para que las propuestas se basen en tus impresiones/posiciones reales. "
                "Mientras, se muestran temas con demanda probada en el sector camper.")

    propuestas = content_strategy_desde_datos(dfq_cf, top_n=6)
    for i, prop in enumerate(propuestas):
        with st.container(border=True):
            badge = "🟢 DATO REAL" if prop["origen"] == "DATO REAL (GSC)" else "🔵 PATRÓN SECTOR"
            vcolor = VERT_COLORS.get(prop["vertical"], "#5f6368")
            st.markdown(f"#### 📌 {prop['titulo']}")
            st.markdown(f"<span class='tag' style='background:{vcolor};color:#fff;'>{prop['vertical']}</span> "
                        f"<span class='tag tag-info'>{badge}</span> "
                        f"<code style='font-size:.78rem'>{prop['keyword']}</code>", unsafe_allow_html=True)
            st.caption(f"📊 {prop['metrica']}")
            st.info(f"🧠 **Por qué este contenido:** {prop['porque']}")

            akey = f"cf_art_{i}"
            if not st.session_state.get(akey):
                if st.button("🧠 Generar artículo", key=f"gen_{i}"):
                    with st.spinner("Redactando con los datos reales de Wheely Fog..."):
                        html = generate_ai_blog(prop["keyword"], prop["titulo"])
                        st.session_state[akey] = html
                        # Cronología de artículos
                        st.session_state.articulos_log = [
                            x for x in st.session_state.articulos_log if x["titulo"] != prop["titulo"]]
                        st.session_state.articulos_log.append({
                            "titulo": prop["titulo"], "keyword": prop["keyword"],
                            "vertical": prop["vertical"], "origen": prop["origen"],
                            "fecha": datetime.today().strftime("%Y-%m-%d %H:%M"),
                            "html": html})
                    st.rerun()
            else:
                st.markdown(f'<div class="blog-container">{st.session_state[akey]}</div>',
                            unsafe_allow_html=True)
                # Sugerencia de FOTO a buscar manualmente
                desc, alt = sugerencia_foto(prop["keyword"], prop["vertical"])
                st.markdown(f"""<div class="img-suggestion">📸 <b>Qué foto buscar (banco libre, sin copyright):</b><br>
                {desc}<br><i>Alt text SEO sugerido: {alt}</i></div>""", unsafe_allow_html=True)
                if st.button("Descartar", key=f"disc_{i}"):
                    st.session_state[akey] = None
                    st.rerun()

    # --- CRONOLOGÍA de artículos generados ---
    st.divider()
    st.subheader("🕒 Cronología de artículos")
    if not st.session_state.articulos_log:
        st.caption("Aún no has generado artículos. Los que crees quedarán aquí ordenados por fecha "
                   "(dentro de esta sesión).")
    else:
        log = sorted(st.session_state.articulos_log, key=lambda x: x["fecha"], reverse=True)
        st.caption(f"{len(log)} artículos generados en esta sesión (más reciente arriba).")
        for a in log:
            vcolor = VERT_COLORS.get(a["vertical"], "#5f6368")
            with st.expander(f"📄 {a['fecha']} · {a['titulo']} [{a['vertical']}]"):
                st.markdown(f"<span class='tag' style='background:{vcolor};color:#fff;'>{a['vertical']}</span> "
                            f"<code>{a['keyword']}</code> · origen: {a['origen']}", unsafe_allow_html=True)
                st.markdown(f'<div class="blog-container">{a["html"]}</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("📈 Mapa de Competitividad SEO (demo)")
    fig_seo = px.scatter(df_seo, x="Dificultad (KD)", y="Tráfico Mensual", size="Volumen Keyword",
                         color="Tasa Conversión", hover_name="Palabra Clave Principal",
                         color_continuous_scale="Greens", size_max=50,
                         title="Burbujas grandes a la izquierda (baja dificultad) = oportunidades")
    st.plotly_chart(fig_seo, use_container_width=True)


# ==========================================
# 8. MODULO: AUDITORIA CRUZADA
# ==========================================
elif hemisferio == "🔑 Auditoría Cruzada (SEO vs SEM)":
    st.title("🔑 Matriz de Auditoría Cross-Channel")
    st.markdown("Identifica canibalización, fugas de presupuesto y rentabilidad neta por keyword.")

    lider = int(df_cross["Estado"].str.contains("Líder").sum())
    venta = int(df_cross["Estado"].str.contains("Venta").sum())
    optim = int(df_cross["Estado"].str.contains("Optimizar").sum())
    c1, c2, c3 = st.columns(3)
    with c1: render_metric("Keywords Eficientes", str(lider), "cross")
    with c2: render_metric("Términos de Venta", str(venta), "cross", "Embudo propio", "up")
    with c3: render_metric("Oportunidades SEO", str(optim), "cross")

    st.info("🔀 **Wheely Fog opera dos verticales paralelas: ALQUILER y VENTA de campers ex-flota.** "
            "El tráfico de compra ('comprar camper', 'ocasión', 'segunda mano', 'km') NO es una fuga: es la "
            "vertical de venta, que trabaja en su propio embudo. Lo que sí hay que vigilar es (1) que la venta "
            "tenga campañas y landing propias (/venta), separadas del alquiler, y (2) los términos 'low-cost' "
            "('barato', 'chollo'), que chocan con el posicionamiento premium de la flota de venta.")

    st.divider()
    st.subheader("📊 Matriz Estratégica")
    cross_search = st.text_input("Filtrar: alquiler, comprar, santorini...")
    df_cf = df_cross[df_cross["Keyword"].str.contains(cross_search, case=False, na=False)] if cross_search else df_cross
    st.dataframe(df_cf, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📈 Cuadrante: Posición SEO vs ROAS")
    st.caption("Eje X invertido: la izquierda es el Top 1 de Google.")
    fig_q = px.scatter(df_cross, x="SEO Posición", y="SEM ROAS", size="SEM Gasto (€)",
                       color="Estado", hover_name="Keyword", size_max=55,
                       color_discrete_map={"🔥 Rendimiento Líder": COLORS["seo"], "🌱 Optimizar SEO": COLORS["cross"],
                                           "🛒 Vertical Venta": VERT_COLORS["VENTA"], "🔧 Pre-lanzamiento": VERT_COLORS["CAMPERIZACION"]})
    fig_q.update_xaxes(autorange="reversed", title="Posición en Google (← mejor)")
    fig_q.update_yaxes(title="ROAS SEM")
    st.plotly_chart(fig_q, use_container_width=True)

    st.info("Las acciones rápidas viven en el módulo **🤖 Recomendaciones del Agente**, donde cada cambio se aprueba antes de tocar Google Ads (humano en el bucle).")
