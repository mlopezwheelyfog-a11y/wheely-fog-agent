# -*- coding: utf-8 -*-
"""
WheelyFog AI - Central Command (Streamlit) v3 - GSC CSV
============================================================================
LECTURA GRATIS DE TRAFICO REAL via CSV de Google Search Console.
No usa API, no cuesta dinero, no requiere credenciales. El usuario sube los
CSV que exporta de GSC y la app los lee en memoria (nada se guarda en disco
ni en el repo).

QUE SUBIR (botones en la barra lateral):
  1) Consultas.csv  -> GSC > Rendimiento > pestana Consultas > Exportar > CSV
     Columnas:  Consulta principal | Clics | Impresiones | CTR | Posicion
                (ingles: Top queries | Clicks | Impressions | CTR | Position)
  2) Paginas.csv    -> GSC > Rendimiento > pestana Paginas > Exportar > CSV
     Columnas:  Paginas principales | Clics | Impresiones | CTR | Posicion
  3) (Opcional) CSV de Indexacion: GSC > Indexacion > Paginas > un motivo > Export
     -> lista de URLs de esa categoria (404, noindex, etc.)

Nota: el export CSV de Rendimiento baja un ZIP; dentro estan Consultas.csv y
Paginas.csv. Sube cada uno en su boton.

LO QUE GSC SI DA:  clics, impresiones, CTR, posicion, query, pagina (REAL).
LO QUE NO DA:      valor de conversion (pernocta+seguro+kit), ROAS, gasto Ads.
                   Eso es GA4 + Google Ads API. Reglas de "Valor Real vs Lead"
                   quedan en pausa y la app lo indica.

Ejecutar:   streamlit run app.py
Requisitos: streamlit, pandas, numpy, plotly
============================================================================
"""

import io
import re
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="WheelyFog AI", page_icon="🚐", layout="wide")

GANCHOS = ["Seguro Básico Incluido 0€", "Entrega 24/7 los 365 días",
           "Pet-friendly (supl. 35€)", "Flexibilidad por toda la UE"]

COLORS = {"seo": "#34a853", "sem": "#ea4335", "cross": "#fbbc05", "global": "#4285f4"}
VERT_COLORS = {
    "ALQUILER": "#1a73e8", "VENTA": "#9334e6",
    "CAMPERIZACION": "#e37400", "MARCA": "#137333", "INFORMACIONAL": "#5f6368",
}

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background:#fff; border:1px solid #e0e0e0; border-radius:12px; padding:16px; }
    .metric-card { background:#fff; border-radius:12px; padding:18px; border:1px solid #e0e0e0; box-shadow:0 1px 3px rgba(0,0,0,0.05); }
    .metric-title { font-size:.75rem; font-weight:700; text-transform:uppercase; color:#5f6368; letter-spacing:.5px; }
    .metric-value { font-size:2rem; font-weight:800; color:#202124; margin:6px 0; }
    .rec-card { background:#fff; border:1px solid #e0e0e0; border-radius:12px; padding:18px; margin-bottom:14px; }
    .tag { display:inline-block; padding:2px 8px; border-radius:5px; font-size:.72rem; font-weight:600; margin-right:6px; }
    .tag-alta { background:#fce8e6; color:#c5221f; }
    .tag-media { background:#fef7e0; color:#b06000; }
    .tag-info { background:#e8f0fe; color:#1a73e8; }
    .tag-canal { background:#f1f3f4; color:#5f6368; }
    .tag-vert { color:#fff; }
</style>
""", unsafe_allow_html=True)


def render_metric(title, value, color_type="global", delta=None, delta_type="up"):
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
# 1. PARSER DE CSV DE GOOGLE SEARCH CONSOLE (ES/EN)
# ==========================================
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


def parse_gsc_csv(uploaded_file, kind):
    """kind='query'|'page'. Devuelve (df|None, mensaje).
    df columnas: termino, Clics, Impresiones, CTR, Posicion."""
    try:
        raw = uploaded_file.getvalue()
        df = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=enc)
                break
            except Exception:
                df = None
        if df is None or df.empty:
            return None, "El CSV está vacío o no se pudo leer."
    except Exception as e:
        return None, f"No se pudo abrir el archivo: {e}"

    cols_lower = {c.lower().strip(): c for c in df.columns}
    dim_key = "query" if kind == "query" else "page"
    dim_col = _find_col(cols_lower, COLMAP[dim_key])
    if dim_col is None:
        return None, (f"No encuentro la columna de {'consulta' if kind=='query' else 'página'}. "
                      f"Columnas detectadas: {list(df.columns)}. "
                      f"¿Es el CSV de {'Consultas' if kind=='query' else 'Páginas'} de GSC?")

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
    return out, f"OK: {len(out)} filas leídas."


# ==========================================
# 2. CLASIFICADOR DE VERTICALES
# ==========================================
FLOTA = ["santorini", "kioto", "bibury", "formentera", "nueva york", "arizona",
         "kenia", "gamla stan", "la cabaña", "la cabana", "compact sky",
         "red compact", "blue compact", "grey compact", "white compact",
         "vancubic", "sa talaia"]
TERMS_VENTA = ["comprar", "compra", "venta", "vender", "en venta", "precio camper",
               "cuanto cuesta", "financiacion", "financiación", "km0", "km 0"]
TERMS_TOXICOS_VENTA = ["segunda mano", "barato", "barata", "baratas", "baratos",
                       "particular", "ocasion", "ocasión", "de segunda"]
TERMS_CAMPERIZACION = ["camperizar", "camperizacion", "camperización", "homologar",
                       "homologacion", "homologación", "mueble camper", "kit camper",
                       "aislamiento furgoneta", "transformar furgoneta"]
TERMS_ALQUILER = ["alquiler", "alquilar", "rent", "renting", "fin de semana",
                  "escapada", "ruta", "vacaciones", "viaje", "por dias", "por días",
                  "3 noches", "noches"]


def clasifica_vertical(kw: str) -> str:
    k = str(kw).lower()
    if "wheely" in k or "wheelyfog" in k:
        return "MARCA"
    if any(m in k for m in FLOTA):
        return "MARCA"
    if any(t in k for t in TERMS_CAMPERIZACION):
        return "CAMPERIZACION"
    if any(t in k for t in TERMS_VENTA) or any(t in k for t in TERMS_TOXICOS_VENTA):
        return "VENTA"
    if any(t in k for t in TERMS_ALQUILER):
        return "ALQUILER"
    return "INFORMACIONAL"


def es_toxico_para_venta(kw: str) -> bool:
    k = str(kw).lower()
    return any(t in k for t in TERMS_TOXICOS_VENTA)


# ==========================================
# 3. MOTOR DE RECOMENDACIONES sobre GSC (queries)
# ==========================================
def build_recommendations(df_q):
    recs, rid = [], 0

    def add(sev, canal, freq, kw, vertical, titulo, detalle, accion, impacto):
        nonlocal rid
        rid += 1
        recs.append(dict(id=rid, sev=sev, canal=canal, freq=freq, kw=kw, vertical=vertical,
                         titulo=titulo, detalle=detalle, accion=accion, impacto=impacto))

    if df_q is None or df_q.empty:
        add("alta", "Sistema", "diaria", "-", "INFORMACIONAL",
            "Sube el CSV de Consultas de GSC para activar las recomendaciones",
            "Sin datos reales de Search Console no hay nada que auditar.",
            "Barra lateral → botón 'Consultas.csv'.",
            "Recomendaciones basadas en posiciones y clics reales")
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
            f'"{r["termino"]}" — {int(r["Impresiones"]):,} impresiones, {int(r["Clics"])} clics, '
            f'posición {r["Posicion"]:.0f}. Busca segunda mano/precio bajo: no cualifica para flota nueva.',
            "Negativizar en FRASE en campañas de VENTA. No perseguirlo en orgánico.",
            "Evitas leads de venta no cualificados")

    venta_ok = df[(df["Vertical"] == "VENTA") & ~df["termino"].apply(es_toxico_para_venta)]
    for _, r in venta_ok[(venta_ok["Posicion"] > 10) & (venta_ok["Impresiones"] >= 100)].sort_values("Impresiones", ascending=False).head(5).iterrows():
        add("media", "SEO", "semanal", r["termino"], "VENTA",
            "Oportunidad SEO en vertical VENTA",
            f'"{r["termino"]}" — {int(r["Impresiones"]):,} impresiones pero posición {r["Posicion"]:.0f}: '
            "apareces pero casi nadie te ve.",
            "Crear/optimizar landing de venta de flota para esta keyword.",
            "Pipeline de leads de venta de alto ticket sin puja")

    alq = df[df["Vertical"] == "ALQUILER"]
    strike = alq[(alq["Posicion"] >= 4) & (alq["Posicion"] <= 15) & (alq["Impresiones"] >= 50)]
    for _, r in strike.sort_values("Impresiones", ascending=False).head(8).iterrows():
        ctr_txt = f"{r['CTR']*100:.1f}%" if pd.notna(r["CTR"]) else "n/d"
        add("media", "SEO", "semanal", r["termino"], "ALQUILER",
            "Striking distance: a un empujón del Top 3",
            f'"{r["termino"]}" — posición {r["Posicion"]:.0f}, {int(r["Impresiones"]):,} impresiones, CTR {ctr_txt}. '
            "Subir 2-5 posiciones dispara los clics sin coste.",
            f"Refuerzo on-page + enlazado interno. Ganchos: {GANCHOS[0]}, {GANCHOS[1]}.",
            "Tráfico transaccional incremental gratis")

    top_bajo_ctr = df[(df["Posicion"] <= 5) & (df["Impresiones"] >= 200) & (df["CTR"] < 0.02)]
    for _, r in top_bajo_ctr.sort_values("Impresiones", ascending=False).head(5).iterrows():
        add("media", "SEO", "semanal", r["termino"], clasifica_vertical(r["termino"]),
            "Estás en Top 5 pero casi nadie hace clic (revisar title/meta)",
            f'"{r["termino"]}" — posición {r["Posicion"]:.0f}, {int(r["Impresiones"]):,} impresiones, '
            f'CTR {r["CTR"]*100:.1f}%.',
            f"Reescribir title y meta description con gancho: {GANCHOS[0]} / {GANCHOS[2]}.",
            "Más clics con el mismo ranking")

    add("info", "Sistema", "semanal", "-", "INFORMACIONAL",
        "Valor de conversión real: requiere GA4 + Google Ads (no está en GSC)",
        "GSC da clics/impresiones/posición reales, pero NO el valor de pasarela "
        "(pernocta + seguro + kit) ni el ROAS. Reglas de fuga por valor en pausa.",
        "Conectar GA4 más adelante para activar 'Valor Real vs Lead'.",
        "Desbloquea la auditoría de dinero, no solo de tráfico")

    orden = {"alta": 0, "media": 1, "info": 2}
    return sorted(recs, key=lambda x: orden[x["sev"]])


# ==========================================
# 4. ESTADO DE SESION
# ==========================================
if "df_queries" not in st.session_state:
    st.session_state.df_queries = None
if "df_pages" not in st.session_state:
    st.session_state.df_pages = None
if "rec_estado" not in st.session_state:
    st.session_state.rec_estado = {}


# ==========================================
# 5. BARRA LATERAL: CARGA DE CSV
# ==========================================
with st.sidebar:
    st.markdown("## 🚐 WheelyFog AI")
    st.markdown("Lectura de tráfico real de Search Console (gratis, sin API).")
    st.divider()

    hemisferio = st.radio(
        "Módulos:",
        ("🤖 Recomendaciones del Agente",
         "📝 SEO Real (Search Console)",
         "🩺 Salud de Indexación"),
    )
    st.divider()

    st.markdown("### 📤 Sube tus CSV de GSC")
    up_q = st.file_uploader("1) Consultas.csv (keywords)", type=["csv"], key="up_q")
    up_p = st.file_uploader("2) Páginas.csv (URLs)", type=["csv"], key="up_p")

    if up_q is not None:
        dfq, msg_q = parse_gsc_csv(up_q, "query")
        st.session_state.df_queries = dfq
        (st.success if dfq is not None else st.error)(msg_q)
    if up_p is not None:
        dfp, msg_p = parse_gsc_csv(up_p, "page")
        st.session_state.df_pages = dfp
        (st.success if dfp is not None else st.error)(msg_p)

    st.divider()
    st.caption("Los CSV se leen en memoria. No se guardan en disco ni en el repo.")
    st.warning("🟡 GA4 / Google Ads: sin conectar (sin valor de conversión ni ROAS)")

df_q = st.session_state.df_queries
df_p = st.session_state.df_pages


# ==========================================
# 6. MODULO: RECOMENDACIONES
# ==========================================
if hemisferio == "🤖 Recomendaciones del Agente":
    st.title("🤖 Recomendaciones del Agente")
    st.markdown("Clasificadas por **vertical** (ALQUILER / VENTA / CAMPERIZACIÓN / MARCA), sobre datos reales de Search Console. Cada acción requiere tu aprobación.")

    recs = build_recommendations(df_q)
    activas = [r for r in recs if r["id"] not in st.session_state.rec_estado]
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric("Recomendaciones activas", str(len(activas)), "cross")
    with c2: render_metric("Prioridad alta", str(len([r for r in activas if r["sev"] == "alta"])), "sem")
    with c3: render_metric("Vertical ALQUILER", str(len([r for r in activas if r["vertical"] == "ALQUILER"])), "global")
    with c4: render_metric("Vertical VENTA", str(len([r for r in activas if r["vertical"] == "VENTA"])), "seo")

    st.divider()
    for r in recs:
        estado = st.session_state.rec_estado.get(r["id"])
        tag_class = {"alta": "tag-alta", "media": "tag-media", "info": "tag-info"}[r["sev"]]
        tag_label = {"alta": "Prioridad alta", "media": "Prioridad media", "info": "Informativo"}[r["sev"]]
        vcolor = VERT_COLORS.get(r["vertical"], "#5f6368")
        opacity = "opacity:0.55;" if estado else ""
        st.markdown(f"""
        <div class="rec-card" style="{opacity}">
            <div style="margin-bottom:8px;">
                <span class="tag tag-vert" style="background:{vcolor};">{r['vertical']}</span>
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
            st.success("✓ En cola de aprobación (aplicar manualmente).")
        elif estado == "descartada":
            cd1, cd2 = st.columns([3, 1])
            cd1.caption("Descartada.")
            if cd2.button("Deshacer", key=f"undo_{r['id']}"):
                st.session_state.rec_estado.pop(r["id"], None); st.rerun()
        else:
            b1, b2, _ = st.columns([2, 1, 4])
            if b1.button("✓ Aplicar (a cola)", key=f"apply_{r['id']}"):
                st.session_state.rec_estado[r["id"]] = "aplicada"; st.rerun()
            if b2.button("Descartar", key=f"dismiss_{r['id']}"):
                st.session_state.rec_estado[r["id"]] = "descartada"; st.rerun()


# ==========================================
# 7. MODULO: SEO REAL (SEARCH CONSOLE)
# ==========================================
elif hemisferio == "📝 SEO Real (Search Console)":
    st.title("📝 Tráfico Orgánico Real (Search Console)")
    if df_q is None and df_p is None:
        st.info("⬅️ Sube el CSV de **Consultas** y/o **Páginas** en la barra lateral para ver tus datos reales.")
        st.markdown("**Cómo exportarlos:** GSC → Rendimiento → Resultados de búsqueda → **Exportar** → **CSV** (baja un ZIP con `Consultas.csv` y `Páginas.csv`).")
    else:
        base = (df_q if df_q is not None else df_p).copy()
        base["Vertical"] = base["termino"].apply(clasifica_vertical)

        clics = int(base["Clics"].sum())
        impr = int(base["Impresiones"].sum())
        ctr_glob = (clics / impr) if impr else 0
        con_pos = base.dropna(subset=["Posicion"])
        pos_pond = ((con_pos["Posicion"] * con_pos["Impresiones"]).sum() /
                    max(con_pos["Impresiones"].sum(), 1)) if not con_pos.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric("Clics reales (periodo)", f"{clics:,}", "seo")
        with c2: render_metric("Impresiones", f"{impr:,}", "seo")
        with c3: render_metric("CTR medio", f"{ctr_glob*100:.1f}%", "seo")
        with c4: render_metric("Posición media (pond.)", f"{pos_pond:.1f}", "seo")

        st.divider()
        st.subheader("📊 Tráfico por Vertical")
        dv = base.groupby("Vertical").agg({"Clics": "sum", "Impresiones": "sum",
                                           "termino": "count"}).reset_index()
        dv.columns = ["Vertical", "Clics", "Impresiones", "Nº términos"]
        fig = px.bar(dv, x="Vertical", y="Clics", color="Vertical",
                     color_discrete_map=VERT_COLORS, text="Nº términos",
                     title="¿De qué vertical vienen los clics reales?")
        st.plotly_chart(fig, use_container_width=True)

        if df_q is not None:
            st.subheader("🔍 Consultas (keywords reales)")
            q = st.text_input("Filtrar consultas:")
            dfq_v = df_q.copy(); dfq_v["Vertical"] = dfq_v["termino"].apply(clasifica_vertical)
            if q:
                dfq_v = dfq_v[dfq_v["termino"].str.contains(q, case=False, na=False)]
            dfq_v = dfq_v.rename(columns={"termino": "Consulta"})
            st.dataframe(dfq_v.sort_values("Clics", ascending=False),
                         use_container_width=True, hide_index=True)

        if df_p is not None:
            st.subheader("🔗 Páginas (URLs reales)")
            dfp_v = df_p.rename(columns={"termino": "Página"})
            st.dataframe(dfp_v.sort_values("Clics", ascending=False),
                         use_container_width=True, hide_index=True)


# ==========================================
# 8. MODULO: SALUD DE INDEXACION
# ==========================================
else:
    st.title("🩺 Salud de Indexación")
    st.markdown("Sube el CSV de un motivo de **GSC → Indexación → Páginas** (ej. los 404, los noindex) para listar las URLs afectadas y ver qué vertical golpean.")
    st.error("Diagnóstico previo: 248 'Not found (404)' en estado *Failed* y 279 'Page with redirect' son la causa probable de la caída de páginas indexadas (~530 → 245). Prioridad: recuperar los 404 válidos con redirección 301.")

    up_idx = st.file_uploader("CSV de indexación (URLs de un motivo)", type=["csv"], key="up_idx")
    if up_idx is not None:
        try:
            raw = up_idx.getvalue()
            df_idx = None
            for enc in ("utf-8-sig", "utf-8", "latin-1"):
                try:
                    df_idx = pd.read_csv(io.BytesIO(raw), encoding=enc); break
                except Exception:
                    df_idx = None
            if df_idx is None or df_idx.empty:
                st.error("No se pudo leer el CSV.")
            else:
                url_col = None
                for c in df_idx.columns:
                    if "url" in c.lower() or "página" in c.lower() or "pagina" in c.lower():
                        url_col = c; break
                st.success(f"{len(df_idx)} URLs en el archivo.")
                if url_col:
                    df_idx["Vertical afectada"] = df_idx[url_col].apply(
                        lambda u: clasifica_vertical(str(u).replace("-", " ").replace("/", " ")))
                    st.markdown("**¿Qué vertical está afectada por estas URLs rotas/excluidas?**")
                    st.bar_chart(df_idx["Vertical afectada"].value_counts())
                st.dataframe(df_idx, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error: {e}")
