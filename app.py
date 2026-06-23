"use client";

/**
 * WheelyFog AI — Central Command (Next.js / App Router)
 * ----------------------------------------------------------------------------
 * Conversión del prototipo Streamlit a Next.js + React + Recharts.
 *
 * INSTALACIÓN (Next.js 14/15 App Router):
 *   1) Coloca este archivo en  app/page.jsx
 *   2) npm install recharts
 *   3) Necesitas Tailwind configurado (npx create-next-app --tailwind).
 *
 * FIXES aplicados respecto al original:
 *   - [BUG botones anidados] La generación de artículo y la aprobación ya NO
 *     dependen de un botón dentro de otro: se controlan con estado (useState).
 *   - [Metodología] La "Posición Media Global" ahora es PONDERADA por tráfico,
 *     no una media aritmética (que mezclaba keywords de volúmenes distintos).
 *   - [Incoherencia marca] El motor de recomendaciones NUNCA propone pausar la
 *     puja de marca ("wheely fog") siendo Top 1 orgánico: la protege.
 *   - Datos deterministas (RNG sembrado) -> sin desajustes de hidratación SSR.
 *
 * AÑADIDO (lo que pediste como experto en posicionamiento):
 *   - Módulo "🤖 Recomendaciones del Agente": sugerencias diarias/semanales con
 *     detección automática de CHOQUE DE INTENCIÓN (compra vs alquiler),
 *     fugas de presupuesto, canibalización y oportunidades SEO. Cada tarjeta
 *     se puede Aplicar o Descartar (cola de acción con humano en el bucle).
 * ----------------------------------------------------------------------------
 */

import { useMemo, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, ComposedChart,
  PieChart, Pie, Cell, ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, Legend,
} from "recharts";

/* ===========================================================================
   PALETA Y HELPERS
   =========================================================================== */
const C = { seo: "#34a853", sem: "#ea4335", cross: "#fbbc05", global: "#4285f4" };
const eur = (n) => `${n.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const num = (n) => n.toLocaleString("es-ES");

// RNG determinista (mulberry32) para reproducir np.random.seed(42)
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ===========================================================================
   1. GENERADORES DE DATOS SINTÉTICOS (portados del Python)
   ⚠️ Reemplazar por Google Ads API / Search Console cuando estén conectados.
   =========================================================================== */
function buildSemDataset() {
  const rng = mulberry32(42);
  const ri = (a, b) => Math.floor(rng() * (b - a + 1)) + a;
  const rf = (a, b) => rng() * (b - a) + a;
  const pick = (arr) => arr[Math.floor(rng() * arr.length)];

  const today = new Date();
  const fechas = Array.from({ length: 90 }, (_, i) => {
    const d = new Date(today); d.setDate(d.getDate() - i);
    return d.toISOString().slice(0, 10);
  });
  const campañas = ["LOCAL_Rafelbunyol", "GLOBAL_Flota_España", "BRAND_WheelyFog", "RETARGETING_Comunidad"];
  const terminos = [
    "alquiler camper valencia", "alquiler furgoneta camper", "comprar camper segunda mano",
    "camperizacion valencia", "wheely fog", "camper santorini alquiler", "rutas camper valencia",
    "camper barata valencia", "alquiler autocaravana rafelbunyol", "viajar en camper 2 personas",
    "furgoneta camperizada alquiler",
  ];

  const data = [];
  for (let i = 0; i < 1000; i++) {
    const camp = pick(campañas);
    const term = pick(terminos);
    const fecha = pick(fechas);
    let impresiones, ctr, cpc, cvr;
    if (camp === "BRAND_WheelyFog") {
      impresiones = ri(100, 800); ctr = rf(0.15, 0.35); cpc = rf(0.10, 0.30); cvr = rf(0.05, 0.15);
    } else {
      impresiones = ri(50, 500); ctr = rf(0.02, 0.12); cpc = rf(0.50, 2.10); cvr = rf(0.0, 0.04);
    }
    const clics = Math.round(impresiones * ctr);
    const coste = clics * cpc;
    const conversiones = Math.round(clics * cvr);
    const valor = conversiones > 0 ? conversiones * rf(150, 600) : 0;
    data.push({ Fecha: fecha, Campaña: camp, Término: term, Impresiones: impresiones, Clics: clics, Coste: coste, Conversiones: conversiones, Valor: valor });
  }
  return data.sort((a, b) => (a.Fecha < b.Fecha ? 1 : -1));
}

const SEO_DATA = [
  { URL: "/rutas/costa-blanca-camper", kw: "ruta costa blanca camper", trafico: 4500, pos: 1.4, vol: 12000, kd: 24, cvr: 0.018 },
  { URL: "/guias/normativa-pernocta-comunidad-valenciana", kw: "pernocta comunidad valenciana", trafico: 3800, pos: 1.2, vol: 8500, kd: 15, cvr: 0.006 },
  { URL: "/modelos/diferencias-minivan-gran-volumen", kw: "minivan vs gran volumen", trafico: 2900, pos: 2.8, vol: 4100, kd: 35, cvr: 0.029 },
  { URL: "/consejos/viajar-con-perro-autocaravana", kw: "viajar con perro camper", trafico: 2100, pos: 3.2, vol: 5600, kd: 42, cvr: 0.034 },
  { URL: "/eventos/festivales-musica-espana-camper", kw: "festivales en camper", trafico: 1950, pos: 4.1, vol: 9000, kd: 55, cvr: 0.042 },
  { URL: "/rutas/escapadas-fin-de-semana-rafelbunyol", kw: "rutas camper cerca de valencia", trafico: 1400, pos: 1.5, vol: 4200, kd: 12, cvr: 0.025 },
  { URL: "/", kw: "wheely fog", trafico: 5000, pos: 1.0, vol: 1500, kd: 5, cvr: 0.120 },
  { URL: "/modelos/santorini-parejas", kw: "camper santorini alquiler", trafico: 1100, pos: 2.1, vol: 2100, kd: 28, cvr: 0.058 },
  { URL: "/blog/bricolaje-aislamiento-termico", kw: "camperizacion valencia", trafico: 850, pos: 14.5, vol: 3300, kd: 65, cvr: 0.001 },
  { URL: "/contacto", kw: "telefono wheely fog", trafico: 300, pos: 1.1, vol: 400, kd: 2, cvr: 0.080 },
];

const PROPOSALS = [
  { titulo: "Guía Definitiva: Viaje a Eurodisney en Furgoneta Camper", kw: "eurodisney furgoneta camper", vol: 8500, kd: 24, intencion: "Transaccional / Alquiler Familiar", justificacion: "Este artículo ataca un viaje de +1.300km. Los dueños de campers antiguas temen averías en trayectos largos internacionales. El texto se sesga hacia la 'tranquilidad' de alquilar vehículos nuevos con seguro a todo riesgo, filtrando curiosos y atrayendo reservas familiares de alto ticket (7-10 días)." },
  { titulo: "Escapadas de fin de semana desde Rafelbunyol: 5 destinos a menos de 100km", kw: "rutas camper cerca de valencia", vol: 4200, kd: 15, intencion: "Transaccional Local", justificacion: "Tráfico Bottom-of-Funnel (gente lista para salir este finde). El foco en rutas cortas excluye a nómadas con furgo propia y maximiza la tarifa base (100km/día), reduciendo depreciación del motor." },
  { titulo: "Dónde alquilar campers baratas en Valencia sin sorpresas en el seguro", kw: "alquiler camper valencia barata", vol: 5600, kd: 42, intencion: "Transaccional / Precio", justificacion: "Resuelve la fricción pre-compra: el miedo a franquicias ocultas. Un artículo transparente roba clientes a plataformas P2P y convierte tráfico en alquileres cerrados." },
];

const CROSS = [
  { kw: "alquiler camper valencia", pos: 2.4, trafico: 3100, gasto: 1450.20, roas: 4.8, estado: "🔥 Rendimiento Líder", accion: "Mantener Inversión" },
  { kw: "camper santorini alquiler", pos: 2.1, trafico: 1100, gasto: 810.50, roas: 6.5, estado: "🔥 Rendimiento Líder", accion: "Escalar Presupuesto" },
  { kw: "rutas camper cerca de valencia", pos: 1.5, trafico: 1400, gasto: 285.10, roas: 1.2, estado: "🌱 Optimizar SEO", accion: "Reducir Puja SEM" },
  { kw: "comprar camper segunda mano", pos: 48.0, trafico: 5, gasto: 910.40, roas: 0.0, estado: "💸 Fuga Absoluta", accion: "Negativizar Exacta" },
  { kw: "camperizacion valencia", pos: 14.5, trafico: 80, gasto: 495.00, roas: 0.4, estado: "💸 Fuga Absoluta", accion: "Negativizar Frase" },
  { kw: "wheely fog", pos: 1.0, trafico: 5000, gasto: 145.00, roas: 14.2, estado: "🔥 Rendimiento Líder", accion: "Proteger Marca" },
  { kw: "camper barata valencia", pos: 9.2, trafico: 110, gasto: 1280.60, roas: 3.1, estado: "🌱 Optimizar SEO", accion: "Crear Landing SEO" },
];

/* ===========================================================================
   2. MOTOR DE RECOMENDACIONES (NUEVO)
   Reglas de negocio de un gestor SEO/SEM. Más adelante esta capa la consume
   un LLM (Claude tool-use) que razona sobre datos reales; aquí van las reglas.
   =========================================================================== */
// Léxico de intención. El negocio es ALQUILER; lo de compra/venta es ruido.
const INTENT_COMPRA = ["comprar", "compra", "segunda mano", "venta", "vender", "ocasion", "ocasión", "km0", "km 0"];
const INTENT_ALQUILER = ["alquiler", "alquilar", "rent", "fin de semana", "ruta", "escapada"];

function detectaIntencion(kw) {
  const k = kw.toLowerCase();
  if (INTENT_COMPRA.some((t) => k.includes(t))) return "compra";
  if (INTENT_ALQUILER.some((t) => k.includes(t))) return "alquiler";
  return "informacional";
}

function buildRecommendations(cross, seo) {
  const recs = [];
  let id = 0;

  cross.forEach((r) => {
    const intent = detectaIntencion(r.kw);
    const esMarca = r.kw.toLowerCase().includes("wheely fog");

    // R1 — CHOQUE DE INTENCIÓN: keyword de compra consumiendo presupuesto de alquiler
    if (intent === "compra" && r.gasto > 0) {
      recs.push({
        id: ++id, sev: "alta", canal: "SEM", freq: "diaria", kw: r.kw,
        titulo: "Choque de intención: negativizar término de COMPRA",
        detalle: `"${r.kw}" es intención de compra/venta, pero el negocio es alquiler. Está quemando ${eur(r.gasto)}/mes con ROAS ${r.roas.toFixed(1)}x. Todo ese tráfico rebota.`,
        accion: `Añadir "${r.kw}" como negativa en concordancia de frase y exacta en todas las campañas de alquiler.`,
        impacto: `Ahorro estimado: ${eur(r.gasto)}/mes`,
      });
      return;
    }

    // R2 — FUGA: gasto alto y ROAS bajo (sin ser marca)
    if (!esMarca && r.roas < 1 && r.gasto > 300) {
      recs.push({
        id: ++id, sev: "alta", canal: "SEM", freq: "diaria", kw: r.kw,
        titulo: "Fuga de presupuesto (ROAS < 1)",
        detalle: `"${r.kw}" gasta ${eur(r.gasto)} y devuelve ROAS ${r.roas.toFixed(1)}x. Pierde dinero en cada clic.`,
        accion: "Pausar el grupo de anuncios o bajar puja agresivamente y revisar la landing/coincidencia.",
        impacto: `Recuperas margen sobre ${eur(r.gasto)}/mes`,
      });
      return;
    }

    // R3 — CANIBALIZACIÓN: Top SEO sólido + ROAS SEM flojo -> bajar puja (NO si es marca)
    if (!esMarca && r.pos <= 3 && r.roas < 2 && r.gasto > 100) {
      recs.push({
        id: ++id, sev: "media", canal: "Cross", freq: "semanal", kw: r.kw,
        titulo: "Canibalización: ya eres Top 3 orgánico",
        detalle: `"${r.kw}" está en posición ${r.pos.toFixed(1)} orgánica con ROAS SEM ${r.roas.toFixed(1)}x. Estás pagando clics que ganarías gratis.`,
        accion: "Reducir puja SEM un 40-60% y reinvertir en términos sin posición orgánica.",
        impacto: "Recortas gasto redundante manteniendo el clic orgánico",
      });
      return;
    }

    // R4 — PROTECCIÓN DE MARCA (corrige la incoherencia del original)
    if (esMarca) {
      recs.push({
        id: ++id, sev: "info", canal: "SEM", freq: "semanal", kw: r.kw,
        titulo: "Proteger marca (NO pausar)",
        detalle: `"${r.kw}" tiene ROAS ${r.roas.toFixed(1)}x y defenderla cuesta poco. Competidores y plataformas P2P (Yescapa, etc.) pujan tu marca.`,
        accion: "Mantener campaña de marca activa. Defenderla es barato y evita que te roben tráfico de marca.",
        impacto: "Blindas el tráfico de mayor conversión de la cuenta",
      });
      return;
    }

    // R5 — OPORTUNIDAD SEO: paga SEM pero sin posición orgánica decente
    if (r.pos > 8 && r.roas >= 1) {
      recs.push({
        id: ++id, sev: "media", canal: "SEO", freq: "semanal", kw: r.kw,
        titulo: "Crear/optimizar contenido orgánico",
        detalle: `"${r.kw}" depende 100% de SEM (posición ${r.pos.toFixed(1)}). Sin contenido, el coste nunca baja.`,
        accion: "Crear landing optimizada para esta keyword y meterla en el calendario editorial.",
        impacto: "Reduce dependencia de puja a medio plazo",
      });
    }
  });

  // R6 — SEO: URLs con buena posición pero conversión bajísima (intención mal alineada)
  seo.forEach((s) => {
    if (s.pos <= 5 && s.cvr < 0.005 && s.trafico > 500) {
      recs.push({
        id: ++id, sev: "media", canal: "SEO", freq: "semanal", kw: s.kw,
        titulo: "Tráfico que no convierte (revisar intención de la URL)",
        detalle: `${s.URL} posiciona top (${s.pos.toFixed(1)}) y trae ${num(s.trafico)} visitas/mes, pero convierte al ${(s.cvr * 100).toFixed(2)}%. Atrae informacional, no comprador.`,
        accion: "Añadir CTA de reserva y bloques de oferta a la URL para capturar la intención transaccional.",
        impacto: `Monetiza ${num(s.trafico)} visitas/mes ya existentes`,
      });
    }
  });

  const orden = { alta: 0, media: 1, info: 2 };
  return recs.sort((a, b) => orden[a.sev] - orden[b.sev]);
}

/* ===========================================================================
   3. MOTOR DE REDACCIÓN IA (portado; sesga hacia alquiler, excluye propietarios)
   =========================================================================== */
function generateAiBlog(keyword, titulo) {
  if (keyword.toLowerCase().includes("eurodisney")) {
    return `
      <h3>¿Te imaginas conocer el parque temático más famoso de Europa con tu casa sobre ruedas?</h3>
      <p>En <strong>Wheely Fog</strong>, tu empresa de alquiler de furgonetas camper en Valencia, hemos diseñado un itinerario para que disfrutes de un viaje a Eurodisney lleno de magia. Tanto en familia como en pareja o con amigos, ofrecemos furgonetas camper de hasta 5 personas.</p>
      <div class="img-suggestion">📸 <b>Prompt IA / Director de Arte:</b><br>"Fotografía hiperrealista. Familia feliz saliendo de una furgoneta camper moderna; de fondo desenfocado se intuye el castillo de Eurodisney. Golden hour."<br><i>Alt: Alquilar furgoneta camper en Valencia para ir a Eurodisney familiar.</i></div>
      <h4>La mejor época y el factor "Tranquilidad"</h4>
      <p>Recomendamos primavera-verano. El trayecto España-París supera los 1.300 km solo de ida. Muchos descartan la idea por miedo a desgastar su vehículo propio o antiguo. <strong>Alquilar una camper de última generación con Wheely Fog</strong> garantiza cero kilómetros en tu coche, motores revisados y seguro a todo riesgo europeo.</p>
      <h4>Dormir en Eurodisney</h4>
      <ul><li><strong>Parking del parque:</strong> zona para vaciar aguas, electricidad y baños.</li><li><strong>Camping Le Parc de Paris:</strong> a 20 min, supermercado y lavandería.</li></ul>
      <p>Selecciona fechas en nuestra web y reserva hoy tu camper.</p>`;
  }
  return `
    <h3>Descubre ${titulo}</h3>
    <p>En <strong>Wheely Fog</strong> sabemos que las mejores aventuras están a la vuelta de la esquina. No necesitas expediciones de miles de kilómetros ni desgastar tu vehículo.</p>
    <p>Nuestra filosofía: transparencia y rentabilidad. El alquiler base incluye <strong>100 km por noche</strong>, la distancia perfecta para salir de Rafelbunyol a paraísos naturales sin pagar extra de kilometraje.</p>
    <div class="img-suggestion">📸 <b>Prompt IA:</b><br>"Furgoneta camper frente a la Albufera de Valencia al atardecer, dos sillas de camping y dos cafés en una mesa plegable."<br><i>Alt: Escapada camper barata desde Rafelbunyol Valencia.</i></div>
    <p>Deja el mantenimiento y los seguros para nosotros. <i>(El artículo continuaría con las 5 rutas locales).</i></p>`;
}

/* ===========================================================================
   COMPONENTES UI
   =========================================================================== */
function Metric({ title, value, type = "global", delta, deltaType = "up" }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 transition-transform hover:-translate-y-0.5 hover:shadow-md"
         style={{ borderLeft: `6px solid ${C[type]}` }}>
      <div className="text-xs font-bold uppercase tracking-wide text-gray-500">{title}</div>
      <div className="text-3xl font-extrabold text-gray-900 my-2">{value}</div>
      {delta && (
        <span className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold ${deltaType === "up" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {deltaType === "up" ? "↑" : "↓"} {delta}
        </span>
      )}
    </div>
  );
}

function sevBadge(sev) {
  const map = { alta: "bg-red-100 text-red-700", media: "bg-yellow-100 text-yellow-800", info: "bg-blue-100 text-blue-700" };
  const lbl = { alta: "Prioridad alta", media: "Prioridad media", info: "Informativo" };
  return <span className={`px-2 py-0.5 rounded text-xs font-semibold ${map[sev]}`}>{lbl[sev]}</span>;
}

/* ===========================================================================
   PÁGINA PRINCIPAL
   =========================================================================== */
export default function Page() {
  const [modulo, setModulo] = useState("recom");
  const [dias, setDias] = useState(30);
  const [semSearch, setSemSearch] = useState("");
  const [seoSearch, setSeoSearch] = useState("");
  const [crossSearch, setCrossSearch] = useState("");
  const [articulos, setArticulos] = useState({});       // index -> html (fix botón anidado)
  const [aprobados, setAprobados] = useState({});        // index -> bool
  const [recState, setRecState] = useState({});          // id -> "aplicada" | "descartada"

  const semRaw = useMemo(buildSemDataset, []);
  const recomendaciones = useMemo(() => buildRecommendations(CROSS, SEO_DATA), []);

  // Filtro temporal SEM
  const semData = useMemo(() => {
    const limite = new Date(); limite.setDate(limite.getDate() - dias);
    const lim = limite.toISOString().slice(0, 10);
    return semRaw.filter((r) => r.Fecha >= lim);
  }, [semRaw, dias]);

  /* ---- KPIs SEM ---- */
  const semKpi = useMemo(() => {
    const gasto = semData.reduce((a, r) => a + r.Coste, 0);
    const retorno = semData.reduce((a, r) => a + r.Valor, 0);
    const conv = semData.reduce((a, r) => a + r.Conversiones, 0);
    return { gasto, retorno, conv, roas: gasto > 0 ? retorno / gasto : 0, cpa: conv > 0 ? gasto / conv : 0 };
  }, [semData]);

  /* ---- KPIs SEO (FIX: posición ponderada por tráfico) ---- */
  const seoKpi = useMemo(() => {
    const trafico = SEO_DATA.reduce((a, r) => a + r.trafico, 0);
    const posPonderada = SEO_DATA.reduce((a, r) => a + r.pos * r.trafico, 0) / trafico;
    const top3 = SEO_DATA.filter((r) => r.pos <= 3).length;
    return { trafico, posPonderada, top3 };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 flex flex-col md:flex-row">
      <style>{`
        .blog-container{background:#f8f9fa;padding:24px;border-radius:8px;border-left:4px solid ${C.seo};margin-top:12px;line-height:1.6}
        .blog-container h3,.blog-container h4{font-weight:700;margin:14px 0 6px}
        .blog-container ul{list-style:disc;padding-left:20px;margin:8px 0}
        .img-suggestion{background:#e8f0fe;color:#1a73e8;padding:14px;border-radius:6px;font-family:monospace;margin:16px 0;border:1px dashed #1a73e8;font-size:.85rem}
      `}</style>

      {/* SIDEBAR */}
      <aside className="md:w-72 w-full bg-white border-r border-gray-200 p-5 md:min-h-screen">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center text-white font-black" style={{ background: C.global }}>W</div>
          <h1 className="text-xl font-extrabold">WheelyFog AI</h1>
        </div>
        <p className="text-sm text-gray-500 mb-5">Gestión integrada de canales digitales.</p>

        <nav className="space-y-1.5">
          {[
            ["recom", "🤖 Recomendaciones del Agente"],
            ["sem", "🛰️ SEM (Performance & Subastas)"],
            ["seo", "📝 SEO (Content Factory Orgánico)"],
            ["cross", "🔑 Auditoría Cruzada (SEO vs SEM)"],
          ].map(([k, label]) => (
            <button key={k} onClick={() => setModulo(k)}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition ${modulo === k ? "text-white" : "hover:bg-gray-100 text-gray-700"}`}
              style={modulo === k ? { background: C.global } : {}}>
              {label}
            </button>
          ))}
        </nav>

        {modulo === "sem" && (
          <div className="mt-6">
            <div className="text-sm font-semibold mb-2">📅 Filtro Temporal (SEM)</div>
            <input type="range" min={7} max={90} value={dias} onChange={(e) => setDias(+e.target.value)} className="w-full" />
            <div className="text-xs text-gray-500 mt-1">Últimos {dias} días</div>
          </div>
        )}

        <div className="mt-6 space-y-2 text-sm">
          <div className="px-3 py-2 rounded-lg bg-amber-50 text-amber-800 border border-amber-200">🟡 API Google Ads: sin conectar</div>
          <div className="px-3 py-2 rounded-lg bg-amber-50 text-amber-800 border border-amber-200">🟡 Search Console: sin conectar</div>
          <div className="px-3 py-2 rounded-lg bg-amber-50 text-amber-800 border border-amber-200">🟡 GA4: sin conectar</div>
        </div>
      </aside>

      {/* CONTENIDO */}
      <main className="flex-1 p-6 md:p-8 max-w-[1200px]">

        {/* ============ MÓDULO RECOMENDACIONES (NUEVO) ============ */}
        {modulo === "recom" && (
          <section>
            <h2 className="text-2xl font-extrabold mb-1">🤖 Recomendaciones del Agente</h2>
            <p className="text-gray-600 mb-5">Sugerencias <strong>diarias y semanales</strong> sobre lo que no está funcionando: choque de intención compra/alquiler, fugas de presupuesto, canibalización y oportunidades SEO. Cada acción requiere tu aprobación.</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <Metric type="cross" title="Recomendaciones activas" value={recomendaciones.filter((r) => !recState[r.id]).length} />
              <Metric type="sem" title="Prioridad alta" value={recomendaciones.filter((r) => r.sev === "alta" && !recState[r.id]).length} delta="Acción hoy" deltaType="down" />
              <Metric type="cross" title="Frecuencia diaria" value={recomendaciones.filter((r) => r.freq === "diaria").length} />
              <Metric type="seo" title="Frecuencia semanal" value={recomendaciones.filter((r) => r.freq === "semanal").length} />
            </div>

            <div className="space-y-4">
              {recomendaciones.map((r) => {
                const estado = recState[r.id];
                return (
                  <div key={r.id} className={`bg-white rounded-xl border p-5 shadow-sm ${estado === "aplicada" ? "border-green-300 opacity-70" : estado === "descartada" ? "border-gray-200 opacity-50" : "border-gray-200"}`}>
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      {sevBadge(r.sev)}
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">{r.canal}</span>
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-600">↻ {r.freq}</span>
                      <code className="text-xs text-gray-500">{r.kw}</code>
                    </div>
                    <h3 className="font-bold text-lg">{r.titulo}</h3>
                    <p className="text-sm text-gray-700 mt-1">{r.detalle}</p>
                    <div className="mt-2 text-sm"><span className="font-semibold">Acción sugerida:</span> {r.accion}</div>
                    <div className="text-sm text-green-700 font-semibold mt-1">{r.impacto}</div>

                    <div className="flex gap-2 mt-3">
                      {!estado && (
                        <>
                          <button onClick={() => setRecState((s) => ({ ...s, [r.id]: "aplicada" }))}
                            className="px-3 py-1.5 rounded-lg text-white text-sm font-semibold" style={{ background: C.seo }}>
                            ✓ Aplicar (a cola de aprobación)
                          </button>
                          <button onClick={() => setRecState((s) => ({ ...s, [r.id]: "descartada" }))}
                            className="px-3 py-1.5 rounded-lg text-sm font-semibold border border-gray-300 text-gray-600">
                            Descartar
                          </button>
                        </>
                      )}
                      {estado === "aplicada" && <span className="text-sm text-green-700 font-semibold">✓ Añadida a la cola de ejecución (pendiente de push a Google Ads).</span>}
                      {estado === "descartada" && <span className="text-sm text-gray-500">Descartada. <button onClick={() => setRecState((s) => ({ ...s, [r.id]: undefined }))} className="underline">Deshacer</button></span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ============ MÓDULO SEM ============ */}
        {modulo === "sem" && (
          <section>
            <h2 className="text-2xl font-extrabold mb-1">🛰️ Director de Performance (SEM Ads)</h2>
            <p className="text-gray-600 mb-5">Auditoría del capital inyectado en subastas. Datos de los últimos <strong>{dias} días</strong>.</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <Metric type="sem" title="Gasto Total" value={eur(semKpi.gasto)} />
              <Metric type="sem" title="Retorno Generado" value={eur(semKpi.retorno)} delta="+14.2%" />
              <Metric type="sem" title="ROAS de Cuenta" value={`${semKpi.roas.toFixed(2)}x`} />
              <Metric type="sem" title="CPA Promedio" value={eur(semKpi.cpa)} delta="-2.10 €" />
            </div>

            <h3 className="font-bold text-lg mb-2">🔍 Motor de Búsqueda de Términos</h3>
            <input value={semSearch} onChange={(e) => setSemSearch(e.target.value)} placeholder="Ej: valencia, segunda mano, santorini..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4" />
            {semSearch && (() => {
              const f = semData.filter((r) => r.Término.toLowerCase().includes(semSearch.toLowerCase()));
              if (!f.length) return <div className="p-3 bg-amber-50 text-amber-800 rounded-lg mb-4">Sin registros para "{semSearch}" en los últimos {dias} días.</div>;
              const g = f.reduce((a, r) => a + r.Coste, 0), v = f.reduce((a, r) => a + r.Valor, 0), c = f.reduce((a, r) => a + r.Conversiones, 0);
              return (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div><div className="text-xs text-gray-500">Gasto Acumulado</div><div className="font-bold">{eur(g)}</div></div>
                    <div><div className="text-xs text-gray-500">Conversiones</div><div className="font-bold">{c}</div></div>
                    <div><div className="text-xs text-gray-500">ROAS Específico</div><div className="font-bold">{g > 0 ? (v / g).toFixed(2) : "0.00"}x</div></div>
                  </div>
                </div>
              );
            })()}

            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h4 className="font-semibold mb-2">📈 Inversión vs Retorno</h4>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={Object.values(semData.reduce((acc, r) => {
                    acc[r.Fecha] = acc[r.Fecha] || { Fecha: r.Fecha, Coste: 0, Valor: 0 };
                    acc[r.Fecha].Coste += r.Coste; acc[r.Fecha].Valor += r.Valor; return acc;
                  }, {})).sort((a, b) => (a.Fecha < b.Fecha ? -1 : 1))}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="Fecha" hide /><YAxis /><Tooltip /><Legend />
                    <Bar dataKey="Coste" name="Inversión (€)" fill={C.sem} />
                    <Line dataKey="Valor" name="Retorno (€)" stroke={C.global} strokeWidth={3} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h4 className="font-semibold mb-2">🍩 Distribución por Campaña</h4>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={Object.values(semData.reduce((acc, r) => {
                      acc[r.Campaña] = acc[r.Campaña] || { name: r.Campaña, value: 0 };
                      acc[r.Campaña].value += r.Coste; return acc;
                    }, {}))} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90}>
                      {[C.sem, C.global, C.seo, C.cross].map((col, i) => <Cell key={i} fill={col} />)}
                    </Pie>
                    <Tooltip formatter={(v) => eur(v)} /><Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        )}

        {/* ============ MÓDULO SEO ============ */}
        {modulo === "seo" && (
          <section>
            <h2 className="text-2xl font-extrabold mb-1">📝 Director de Contenidos Autónomo (SEO)</h2>
            <p className="text-gray-600 mb-5">Análisis SERP, volumen y fábrica de contenidos automatizada.</p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
              <Metric type="seo" title="Visitas Orgánicas/Mes" value={num(seoKpi.trafico)} delta="+8.4%" />
              <Metric type="seo" title="Posición Media (ponderada)" value={seoKpi.posPonderada.toFixed(1)} delta="-0.4" />
              <Metric type="seo" title="Keywords en Top 3" value={seoKpi.top3} />
            </div>

            <h3 className="font-bold text-lg mb-2">🔍 Buscador de Volumen Orgánico y URLs</h3>
            <input value={seoSearch} onChange={(e) => setSeoSearch(e.target.value)} placeholder="Ej: ruta, camper, pernocta..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-3" />
            {seoSearch && (() => {
              const f = SEO_DATA.filter((r) => r.kw.toLowerCase().includes(seoSearch.toLowerCase()) || r.URL.toLowerCase().includes(seoSearch.toLowerCase()));
              if (!f.length) return <div className="p-3 bg-amber-50 text-amber-800 rounded-lg mb-4">Sin coincidencias. ¡Oportunidad para crear contenido nuevo!</div>;
              return (
                <div className="overflow-x-auto mb-4 bg-white rounded-xl border border-gray-200">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-500 text-left"><tr>
                      <th className="p-2">URL</th><th className="p-2">Keyword</th><th className="p-2">Tráfico</th><th className="p-2">Pos.</th><th className="p-2">Vol.</th><th className="p-2">KD</th><th className="p-2">CVR</th>
                    </tr></thead>
                    <tbody>{f.sort((a, b) => b.trafico - a.trafico).map((r, i) => (
                      <tr key={i} className="border-t border-gray-100"><td className="p-2">{r.URL}</td><td className="p-2">{r.kw}</td><td className="p-2">{num(r.trafico)}</td><td className="p-2">{r.pos.toFixed(1)}</td><td className="p-2">{num(r.vol)}</td><td className="p-2">{r.kd}</td><td className="p-2">{(r.cvr * 100).toFixed(2)}%</td></tr>
                    ))}</tbody>
                  </table>
                </div>
              );
            })()}

            <h3 className="font-bold text-lg mb-3 mt-6">🏭 Fábrica de Contenidos IA</h3>
            <div className="space-y-4">
              {PROPOSALS.map((p, i) => {
                const kdColor = p.kd < 30 ? "🟢 Fácil" : p.kd < 60 ? "🟡 Media" : "🔴 Difícil";
                return (
                  <div key={i} className="bg-white rounded-xl border border-gray-200 p-5">
                    <h4 className="font-bold">📌 {p.titulo}</h4>
                    <div className="grid grid-cols-3 gap-3 my-3 text-sm">
                      <div><div className="text-gray-500 text-xs">Volumen</div><div className="font-semibold">{num(p.vol)}</div></div>
                      <div><div className="text-gray-500 text-xs">Dificultad</div><div className="font-semibold">{p.kd}/100 ({kdColor})</div></div>
                      <div><div className="text-gray-500 text-xs">Intención</div><div className="font-semibold">{p.intencion}</div></div>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm mb-3">💡 <strong>Justificación:</strong> {p.justificacion}</div>

                    {/* FIX botones anidados: generación controlada por estado */}
                    {!articulos[i] ? (
                      <button onClick={() => setArticulos((s) => ({ ...s, [i]: generateAiBlog(p.kw, p.titulo) }))}
                        className="px-3 py-1.5 rounded-lg text-white text-sm font-semibold" style={{ background: C.seo }}>
                        🧠 Generar Artículo y Prompts Visuales
                      </button>
                    ) : (
                      <>
                        <div className="blog-container" dangerouslySetInnerHTML={{ __html: articulos[i] }} />
                        <div className="flex gap-2 mt-3">
                          {!aprobados[i] ? (
                            <button onClick={() => setAprobados((s) => ({ ...s, [i]: true }))}
                              className="px-3 py-1.5 rounded-lg text-white text-sm font-semibold" style={{ background: C.global }}>
                              📤 Aprobar y Enviar a Web
                            </button>
                          ) : (
                            <span className="text-sm text-green-700 font-semibold">✓ Draft enviado a la cola de publicación.</span>
                          )}
                          <button onClick={() => { setArticulos((s) => ({ ...s, [i]: undefined })); setAprobados((s) => ({ ...s, [i]: false })); }}
                            className="px-3 py-1.5 rounded-lg text-sm font-semibold border border-gray-300 text-gray-600">Descartar</button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            <h3 className="font-bold text-lg mb-2 mt-8">📈 Mapa de Competitividad SEO</h3>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <ResponsiveContainer width="100%" height={360}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                  <CartesianGrid /><XAxis type="number" dataKey="kd" name="Dificultad" label={{ value: "Dificultad (KD)", position: "bottom" }} />
                  <YAxis type="number" dataKey="trafico" name="Tráfico" /><ZAxis type="number" dataKey="vol" range={[60, 600]} />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(v, n) => [num(v), n]} />
                  <Scatter data={SEO_DATA} fill={C.seo} />
                </ScatterChart>
              </ResponsiveContainer>
              <p className="text-xs text-gray-500 mt-1">Burbujas grandes (mucho volumen) a la izquierda (baja dificultad) = oportunidades.</p>
            </div>
          </section>
        )}

        {/* ============ MÓDULO AUDITORÍA CRUZADA ============ */}
        {modulo === "cross" && (
          <section>
            <h2 className="text-2xl font-extrabold mb-1">🔑 Matriz de Auditoría Cross-Channel</h2>
            <p className="text-gray-600 mb-5">Identifica canibalización, fugas de presupuesto y rentabilidad neta por keyword.</p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-5">
              <Metric type="cross" title="Keywords Eficientes" value={CROSS.filter((r) => r.estado.includes("Líder")).length} />
              <Metric type="cross" title="Fugas Críticas" value={CROSS.filter((r) => r.estado.includes("Fuga")).length} delta="Requiere Acción" deltaType="down" />
              <Metric type="cross" title="Oportunidades SEO" value={CROSS.filter((r) => r.estado.includes("Optimizar")).length} />
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-5 text-sm text-red-800">
              <strong>🚨 Fuga de caja:</strong> términos de compra ("comprar camper segunda mano") consumen +1.400€/mes en SEM con ROAS 0.0x. Al no dedicarte a la venta, ese tráfico rebota. Negativizar términos de compra en concordancia amplia y de frase.
            </div>

            <h3 className="font-bold text-lg mb-2">📊 Matriz Estratégica</h3>
            <input value={crossSearch} onChange={(e) => setCrossSearch(e.target.value)} placeholder="Filtrar: alquiler, comprar, santorini..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-3" />
            <div className="overflow-x-auto bg-white rounded-xl border border-gray-200 mb-6">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-left"><tr>
                  <th className="p-2">Keyword</th><th className="p-2">Pos. SEO</th><th className="p-2">Tráfico</th><th className="p-2">Gasto SEM</th><th className="p-2">ROAS</th><th className="p-2">Estado</th><th className="p-2">Acción</th>
                </tr></thead>
                <tbody>{CROSS.filter((r) => r.kw.toLowerCase().includes(crossSearch.toLowerCase())).map((r, i) => (
                  <tr key={i} className="border-t border-gray-100"><td className="p-2 font-medium">{r.kw}</td><td className="p-2">{r.pos.toFixed(1)}</td><td className="p-2">{num(r.trafico)}</td><td className="p-2">{eur(r.gasto)}</td><td className="p-2">{r.roas.toFixed(1)}x</td><td className="p-2">{r.estado}</td><td className="p-2">{r.accion}</td></tr>
                ))}</tbody>
              </table>
            </div>

            <h3 className="font-bold text-lg mb-2">📈 Cuadrante: Posición SEO vs ROAS</h3>
            <p className="text-sm text-gray-600 mb-2">Eje X invertido: la izquierda es el Top 1 de Google.</p>
            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
              <ResponsiveContainer width="100%" height={420}>
                <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                  <CartesianGrid />
                  <XAxis type="number" dataKey="pos" name="Posición SEO" reversed domain={[0, "dataMax"]} label={{ value: "Posición en Google (← mejor)", position: "bottom" }} />
                  <YAxis type="number" dataKey="roas" name="ROAS" label={{ value: "ROAS SEM", angle: -90, position: "left" }} />
                  <ZAxis type="number" dataKey="gasto" range={[80, 700]} />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(v, n) => [n === "gasto" ? eur(v) : v, n]} />
                  {["🔥 Rendimiento Líder", "🌱 Optimizar SEO", "💸 Fuga Absoluta"].map((est) => (
                    <Scatter key={est} name={est} data={CROSS.filter((r) => r.estado === est)}
                      fill={est.includes("Líder") ? C.seo : est.includes("Optimizar") ? C.cross : C.sem} />
                  ))}
                  <Legend />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            <h3 className="font-bold text-lg mb-2">⚡ Ejecución (a cola de aprobación)</h3>
            <p className="text-sm text-gray-600">Las acciones rápidas viven en el módulo <button onClick={() => setModulo("recom")} className="underline font-semibold">🤖 Recomendaciones</button>, donde cada cambio se aprueba antes de tocar Google Ads (humano en el bucle).</p>
          </section>
        )}
      </main>
    </div>
  );
}
