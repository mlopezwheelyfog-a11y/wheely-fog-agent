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
        {"Keyword": "comprar camper segunda mano", "SEO Posición": 48.0, "SEO Tráfico": 5, "SEM Gasto (€)": 910.40, "SEM ROAS": 0.0, "Estado": "💸 Fuga Absoluta", "Acción": "Negativizar Exacta"},
        {"Keyword": "camperizacion valencia", "SEO Posición": 14.5, "SEO Tráfico": 80, "SEM Gasto (€)": 495.00, "SEM ROAS": 0.4, "Estado": "💸 Fuga Absoluta", "Acción": "Negativizar Frase"},
        {"Keyword": "wheely fog", "SEO Posición": 1.0, "SEO Tráfico": 5000, "SEM Gasto (€)": 145.00, "SEM ROAS": 14.2, "Estado": "🔥 Rendimiento Líder", "Acción": "Proteger Marca"},
        {"Keyword": "camper barata valencia", "SEO Posición": 9.2, "SEO Tráfico": 110, "SEM Gasto (€)": 1280.60, "SEM ROAS": 3.1, "Estado": "🌱 Optimizar SEO", "Acción": "Crear Landing SEO"},
    ])


def generate_ai_blog(keyword, title):
    """Motor IA de redaccion. Sesga hacia el ALQUILER y excluye a propietarios."""
    if "eurodisney" in keyword.lower():
        return """
        <h3>¿Te imaginas conocer el parque temático más famoso de Europa con tu casa sobre ruedas?</h3>
        <p>En <strong>Wheely Fog</strong>, tu empresa de alquiler de furgonetas camper en Valencia, hemos diseñado un itinerario para que disfrutes de un viaje a Eurodisney lleno de magia. Tanto en familia como en pareja o con amigos, ofrecemos furgonetas camper de hasta 5 personas.</p>
        <div class="img-suggestion">📸 <b>Prompt IA / Director de Arte:</b><br>"Fotografía hiperrealista. Una familia feliz saliendo de una furgoneta camper moderna y reluciente; de fondo desenfocado se intuye el castillo de Eurodisney. Luz de atardecer golden hour."<br><i>Alt text sugerido: Alquilar furgoneta camper en Valencia para ir a Eurodisney familiar.</i></div>
        <h4>La mejor época y el factor "Tranquilidad"</h4>
        <p>Recomendamos fechas entre primavera y verano. Pero hay un factor crucial: <strong>el vehículo</strong>. El trayecto España-París supera los 1.300 km solo de ida. Muchos descartan la idea por miedo a someter su vehículo propio o antiguo a semejante desgaste. Aquí entra la inteligencia: <strong>alquilar una camper de última generación con Wheely Fog</strong> garantiza cero kilómetros en tu coche, motores revisados de bajo consumo y seguro a todo riesgo europeo.</p>
        <h4>Dormir en furgoneta camper en Eurodisney</h4>
        <ul>
            <li><strong>El parking del parque:</strong> zona para vaciar aguas, suministro eléctrico y baños.</li>
            <li><strong>Camping Le Parc de Paris:</strong> a 20 min, con supermercado, lavandería y minigolf.</li>
        </ul>
        <div class="img-suggestion">📸 <b>Sugerencia de Fotografía Propia:</b><br>"Sube una foto real del interior del modelo 'Santorini' (5 plazas). Muestra la cama montada, bien iluminada, demostrando que es más cómodo que un hotel estándar."<br><i>Alt text sugerido: Interior cama furgoneta camper alquiler Wheely Fog Paris.</i></div>
        <p>Reserva tus entradas con antelación y calcula peajes. El parque se visita bien en 3 días. Entra en nuestra web, selecciona fechas y reserva hoy tu camper en Wheely Fog.</p>
        """
    return f"""
    <h3>Descubre {title}</h3>
    <p>En <strong>Wheely Fog</strong> sabemos que las mejores aventuras a veces están a la vuelta de la esquina. No necesitas planificar expediciones de miles de kilómetros ni desgastar tu vehículo.</p>
    <p>Nuestra filosofía es clara: transparencia y rentabilidad. Por eso el alquiler base incluye <strong>100 km por noche</strong>, la distancia matemáticamente perfecta para recoger tu vehículo en Rafelbunyol y plantarte en paraísos naturales sin pagar extra de kilometraje.</p>
    <div class="img-suggestion">📸 <b>Prompt IA / Director de Arte:</b><br>"Furgoneta camper aparcada frente a la Albufera de Valencia al atardecer, dos sillas de camping desplegadas y dos tazas de café en una mesa plegable."<br><i>Alt text sugerido: Escapada camper barata desde Rafelbunyol Valencia.</i></div>
    <p>Deja el mantenimiento, los seguros y los dolores de cabeza de tener un vehículo en propiedad para nosotros. <i>(El artículo continuaría detallando las 5 rutas locales).</i></p>
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


def parse_gsc_upload(uploaded_file):
    """
    Punto de entrada unico. Acepta ZIP / CSV / XLSX de GSC.
    Devuelve dict con lo que haya podido extraer:
      { 'queries': df|None, 'pages': df|None,
        'index_urls': df|None, 'index_issue': str|None, 'msg': str }
    """
    res = {"queries": None, "pages": None, "index_urls": None,
           "index_issue": None, "msg": ""}
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
# Wheely Fog opera ALQUILER y VENTA como negocios PARALELOS e independientes.
# El clasificador NO usa listas planas (causaban mezcla): puntúa señales de
# intención y gana la señal transaccional DOMINANTE. Regla de oro: el verbo de
# acción manda. "alquiler ... barata" es ALQUILER (el usuario quiere alquilar
# barato), no VENTA, aunque contenga "barata".
FLOTA = ["santorini", "kioto", "bibury", "formentera", "nueva york", "arizona",
         "kenia", "gamla stan", "la cabaña", "la cabana", "compact sky",
         "red compact", "blue compact", "grey compact", "white compact",
         "vancubic", "sa talaia"]

# Señales de ACCIÓN (verbo de intención) — pesan más que los adjetivos
SIG_ALQUILER = ["alquiler", "alquilar", "alquilo", "alquila", "rent", "renting",
                "de alquiler", "en alquiler"]
SIG_VENTA = ["comprar", "compra", "venta", "vender", "en venta", "adquirir",
             "concesionario", "financiacion", "financiación", "financiar",
             "km0", "km 0", "a la venta"]
# Señales de CONTEXTO (refuerzan, no deciden solas)
CTX_ALQUILER = ["fin de semana", "finde", "escapada", "escapadas", "ruta", "rutas",
                "vacaciones", "viaje", "viajar", "noches", "por dias", "por días",
                "una semana", "puente", "pernocta", "dormir"]
CTX_VENTA = ["precio camper", "precio furgoneta", "cuanto cuesta comprar",
             "camper nueva", "furgoneta nueva", "camper a estrenar",
             "camper en venta", "furgoneta en venta"]
TERMS_TOXICOS_VENTA = ["segunda mano", "particular", "ocasion", "ocasión",
                       "de segunda", "reacondicionad"]
TERMS_CAMPERIZACION = ["camperizar", "camperizacion", "camperización", "homologar",
                       "homologacion", "homologación", "mueble camper", "kit camper",
                       "aislamiento furgoneta", "transformar furgoneta", "camperizada diy"]


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


def es_toxico_para_venta(kw):
    """Tóxico SOLO si es intención de VENTA con señal de segunda mano/particular.
    'alquiler barato' NO es tóxico (es alquiler legítimo)."""
    k = str(kw).lower()
    if clasifica_vertical(kw) != "VENTA":
        return False
    return any(t in k for t in TERMS_TOXICOS_VENTA)


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

    tox = df[(df["Vertical"] == "VENTA") & df["termino"].apply(es_toxico_para_venta)]
    for _, r in tox.sort_values("Impresiones", ascending=False).head(8).iterrows():
        add("alta", "SEM", "diaria", r["termino"], "VENTA",
            "Término tóxico para VENTA de flota premium",
            f'"{r["termino"]}" — {int(r["Impresiones"]):,} impr., {int(r["Clics"])} clics, pos {r["Posicion"]:.0f}. '
            "Busca segunda mano/precio bajo: no cualifica para flota nueva.",
            "Negativizar en FRASE en campañas de VENTA.",
            "Evitas leads de venta no cualificados")

    # VENTA legítima = vertical de negocio activa (Wheely Fog vende flota, no solo alquila)
    venta_ok = df[(df["Vertical"] == "VENTA") & ~df["termino"].apply(es_toxico_para_venta)]
    if not venta_ok.empty:
        add("info", "SEO+SEM", "semanal", "vertical venta", "VENTA",
            "Vertical VENTA activa: captar leads de compra de flota",
            f"{len(venta_ok)} términos de compra reales ({int(venta_ok['Impresiones'].sum()):,} impr., "
            f"{int(venta_ok['Clics'].sum()):,} clics). Ticket alto y ciclo de decisión largo: "
            "el lead cualificado vale más que un clic de alquiler.",
            "Mantener campañas de VENTA separadas de ALQUILER (presupuesto y anuncios propios). "
            "KPI = lead cualificado de compra, no reserva.",
            "Monetiza la demanda de compra que ya te encuentra")
    # Oportunidad SEO por término de venta con demanda pero mala posición
    for _, r in venta_ok[(venta_ok["Posicion"] > 8) & (venta_ok["Impresiones"] >= 80)].sort_values("Impresiones", ascending=False).head(6).iterrows():
        add("media", "SEO", "semanal", r["termino"], "VENTA",
            "Oportunidad SEO en VENTA (demanda de compra sin posición)",
            f'"{r["termino"]}" — {int(r["Impresiones"]):,} impr. pero pos {r["Posicion"]:.0f}: '
            "apareces pero casi nadie te ve. La compra madura con contenido.",
            "Crear/optimizar landing de venta de flota para esta keyword (ficha, precio orientativo, "
            "financiación, CTA de contacto). No mezclar con páginas de alquiler.",
            "Pipeline de leads de compra de alto ticket sin depender de puja")

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

    add("info", "Sistema", "semanal", "-", "INFORMACIONAL",
        "Valor de conversión real: requiere GA4 + Google Ads",
        "GSC da clics/impresiones/posición reales, pero NO el valor de pasarela (pernocta+seguro+kit) ni ROAS.",
        "Conectar GA4 para activar 'Valor Real vs Lead'.",
        "Desbloquea la auditoría de dinero, no solo de tráfico")

    orden = {"alta": 0, "media": 1, "info": 2}
    return sorted(recs, key=lambda x: orden[x["sev"]])


# ==========================================
# 3. MOTOR DE RECOMENDACIONES (NUEVO)
#    Reglas de negocio de un gestor SEO/SEM. Mas adelante esta capa la consume
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

        # R1 - CHOQUE DE INTENCION: keyword de compra consumiendo presupuesto de alquiler
        if intent == "compra" and gasto > 0:
            rid += 1
            recs.append(dict(id=rid, sev="alta", canal="SEM", freq="diaria", kw=kw,
                titulo="Choque de intención: negativizar término de COMPRA",
                detalle=f'"{kw}" es intención de compra/venta, pero el negocio es alquiler. Quema {gasto:,.2f} €/mes con ROAS {roas:.1f}x. Ese tráfico rebota.',
                accion=f'Añadir "{kw}" como negativa en concordancia de frase y exacta en todas las campañas de alquiler.',
                impacto=f"Ahorro estimado: {gasto:,.2f} €/mes"))
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

    st.markdown("### 📤 Datos reales de Search Console")
    st.caption("Sube el **ZIP** de GSC (Rendimiento o Indexación), o CSV/XLSX sueltos.")
    up_files = st.file_uploader("Arrastra tus archivos de GSC",
                                type=["zip", "csv", "xlsx", "xls"],
                                accept_multiple_files=True, key="gsc_up")
    if up_files:
        for uf in up_files:
            r = parse_gsc_upload(uf)
            if r["queries"] is not None:
                st.session_state.gsc_queries = r["queries"]
            if r["pages"] is not None:
                st.session_state.gsc_pages = r["pages"]
            if r["index_urls"] is not None:
                issue = r["index_issue"] or uf.name
                st.session_state.gsc_index = [x for x in st.session_state.gsc_index
                                              if x[0] != issue]
                st.session_state.gsc_index.append((issue, r["index_urls"]))
            st.success(f"{uf.name}: {r['msg']}")

    st.divider()
    st.markdown("### 📅 Filtro Temporal (SEM)")
    dias_filtro = st.slider("Rango de análisis (días previos):", 7, 90, 30, 1)
    fecha_limite = datetime.today() - timedelta(days=dias_filtro)
    df_sem = df_sem_raw[pd.to_datetime(df_sem_raw["Fecha"]) >= fecha_limite]

    st.divider()
    st.warning("🟡 API Google Ads: sin conectar")
    if st.session_state.gsc_queries is not None or st.session_state.gsc_pages is not None:
        st.success("🟢 Search Console: datos cargados (CSV/ZIP)")
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
        tab_perf, tab_kw, tab_pag, tab_idx = st.tabs(
            ["📈 Resumen", "🔍 Consultas", "🔗 Páginas", "🩺 Salud de Indexación"])

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

        # --- Consultas ---
        with tab_kw:
            if dfq is not None:
                q = st.text_input("Filtrar consultas:")
                d = dfq.copy()
                d["Vertical"] = d["termino"].apply(clasifica_vertical)
                if q:
                    d = d[d["termino"].str.contains(q, case=False, na=False)]
                d = d.rename(columns={"termino": "Consulta"})
                st.dataframe(d.sort_values("Clics", ascending=False),
                             use_container_width=True, hide_index=True)
            else:
                st.info("No has subido el archivo de Consultas (Queries).")

        # --- Páginas ---
        with tab_pag:
            if dfp is not None:
                d = dfp.rename(columns={"termino": "Página"})
                st.dataframe(d.sort_values("Clics", ascending=False),
                             use_container_width=True, hide_index=True)
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
    st.markdown(f"Auditoría del capital inyectado en subastas. Datos de los últimos **{dias_filtro} días**.")

    total_gasto = df_sem["Coste (€)"].sum()
    total_retorno = df_sem["Valor (€)"].sum()
    total_conv = df_sem["Conversiones"].sum()
    roas_global = total_retorno / total_gasto if total_gasto > 0 else 0
    cpa_global = total_gasto / total_conv if total_conv > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric("Gasto Total", f"{total_gasto:,.2f} €", "sem")
    with c2: render_metric("Retorno Generado", f"{total_retorno:,.2f} €", "sem", "+14.2%", "up")
    with c3: render_metric("ROAS de Cuenta", f"{roas_global:.2f}x", "sem")
    with c4: render_metric("CPA Promedio", f"{cpa_global:.2f} €", "sem", "-2.10 €", "up")

    st.divider()
    st.subheader("🔍 Motor de Búsqueda de Términos (Auditoría SEM)")
    term_search = st.text_input("Introduce un término (Ej: valencia, segunda mano, santorini):")
    if term_search:
        df_f = df_sem[df_sem["Término"].str.contains(term_search, case=False, na=False)]
        if not df_f.empty:
            fg = df_f["Coste (€)"].sum(); fv = df_f["Valor (€)"].sum()
            fr = fv / fg if fg > 0 else 0
            st.info(f"Resultados aislados para: **'{term_search}'**")
            s1, s2, s3 = st.columns(3)
            s1.metric("Gasto Acumulado", f"{fg:,.2f} €")
            s2.metric("Conversiones", int(df_f["Conversiones"].sum()))
            s3.metric("ROAS Específico", f"{fr:.2f}x")
            st.dataframe(df_f.sort_values("Fecha", ascending=False).head(50), use_container_width=True, hide_index=True)
        else:
            st.warning(f"No hay registros para '{term_search}' en los últimos {dias_filtro} días.")

    st.divider()
    t1, t2 = st.tabs(["📈 Tendencia Inversión vs Retorno", "🍩 Distribución por Campaña"])
    with t1:
        df_trend = df_sem.groupby("Fecha").agg({"Coste (€)": "sum", "Valor (€)": "sum"}).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_trend["Fecha"], y=df_trend["Coste (€)"], name="Inversión (€)", marker_color=COLORS["sem"]))
        fig.add_trace(go.Scatter(x=df_trend["Fecha"], y=df_trend["Valor (€)"], mode="lines+markers", name="Retorno (€)", line=dict(color=COLORS["global"], width=3)))
        fig.update_layout(barmode="group", hovermode="x unified", title="Evolución Diaria del Margen")
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        df_camp = df_sem.groupby("Campaña").agg({"Coste (€)": "sum"}).reset_index()
        fig2 = px.pie(df_camp, values="Coste (€)", names="Campaña", title="Distribución del Presupuesto por Campaña", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)


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
    st.subheader("🏭 Fábrica de Contenidos IA")
    for i, prop in df_proposals.iterrows():
        with st.container(border=True):
            st.markdown(f"#### 📌 {prop['Título Propuesto']}")
            kd = prop["KD"]
            kd_label = "🟢 Fácil" if kd < 30 else ("🟡 Media" if kd < 60 else "🔴 Difícil")
            m1, m2, m3 = st.columns(3)
            m1.metric("Volumen", f"{prop['Vol. Búsqueda (Mes)']:,}")
            m2.metric("Dificultad", f"{kd}/100", kd_label)
            m3.metric("Intención", prop["Intención"])
            st.info(f"💡 **Justificación de ventas:** {prop['Justificacion_Ventas']}")

            # FIX botones anidados: generacion via session_state (no boton dentro de boton)
            if not st.session_state.articulos.get(i):
                if st.button("🧠 Generar Artículo y Prompts Visuales", key=f"gen_{i}"):
                    with st.spinner("La IA está redactando y sesgando el contenido..."):
                        st.session_state.articulos[i] = generate_ai_blog(prop["Keyword Objetivo"], prop["Título Propuesto"])
                    st.rerun()
            else:
                st.markdown(f'<div class="blog-container">{st.session_state.articulos[i]}</div>', unsafe_allow_html=True)
                bc1, bc2 = st.columns([2, 1])
                if not st.session_state.aprobados.get(i):
                    if bc1.button("📤 Aprobar y Enviar a Web", key=f"appr_{i}"):
                        st.session_state.aprobados[i] = True
                        st.rerun()
                else:
                    bc1.success("✓ Draft enviado a la cola de publicación.")
                if bc2.button("Descartar", key=f"disc_{i}"):
                    st.session_state.articulos[i] = None
                    st.session_state.aprobados[i] = False
                    st.rerun()

    st.divider()
    st.subheader("📈 Mapa de Competitividad SEO")
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
    fuga = int(df_cross["Estado"].str.contains("Fuga").sum())
    optim = int(df_cross["Estado"].str.contains("Optimizar").sum())
    c1, c2, c3 = st.columns(3)
    with c1: render_metric("Keywords Eficientes", str(lider), "cross")
    with c2: render_metric("Fugas Críticas", str(fuga), "cross", "Requiere Acción", "down")
    with c3: render_metric("Oportunidades SEO", str(optim), "cross")

    st.error("🚨 **Fuga de caja:** términos de compra ('comprar camper segunda mano') consumen +1.400 €/mes en SEM con ROAS 0.0x. Al no dedicarte a la venta, ese tráfico rebota. Negativizar términos de compra en concordancia amplia y de frase.")

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
                       color_discrete_map={"🔥 Rendimiento Líder": COLORS["seo"], "🌱 Optimizar SEO": COLORS["cross"], "💸 Fuga Absoluta": COLORS["sem"]})
    fig_q.update_xaxes(autorange="reversed", title="Posición en Google (← mejor)")
    fig_q.update_yaxes(title="ROAS SEM")
    st.plotly_chart(fig_q, use_container_width=True)

    st.info("Las acciones rápidas viven en el módulo **🤖 Recomendaciones del Agente**, donde cada cambio se aprueba antes de tocar Google Ads (humano en el bucle).")
