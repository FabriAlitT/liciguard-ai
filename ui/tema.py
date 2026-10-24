"""Sistema visual corporativo de LiciGuard: colores, íconos y componentes reutilizables."""
import html
import re
from datetime import date

import altair as alt
import streamlit as st

from core.ayuda import AYUDA_INDICADORES, AYUDA_MENU, GLOSARIO
from core.fechas import hoy_lima

# ------------------------------------------------------------------------------------------
# Paleta: azul tecnológico + cian, con violeta, verde y ámbar como acentos. Fondo claro.
# ------------------------------------------------------------------------------------------
AZUL, AZUL_OSC, CIAN, VIOLETA, VERDE, AMBAR, ROJO, GRIS = (
    "#2563EB", "#1E3A8A", "#06B6D4", "#7C3AED", "#10B981", "#F59E0B", "#EF4444", "#64748B")
TINTA, TEXTO2, BORDE, FONDO = "#0B1B3F", "#51607A", "#E2E8F2", "#F4F7FC"

TONOS = {  # color fuerte, fondo suave
    "azul": ("#2563EB", "#EAF1FF"), "cian": ("#0891B2", "#E2F7FB"), "violeta": ("#7C3AED", "#F2ECFF"),
    "verde": ("#059669", "#E3F8EF"), "ambar": ("#D97706", "#FFF4DD"), "rojo": ("#DC2626", "#FDECEC"),
    "gris": ("#475569", "#EEF2F7"),
}

ICONOS = {
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>'
           '<path d="M8 13h8M8 17h5"/>',
    "alerta": '<path d="m21.7 18-8-14a2 2 0 0 0-3.5 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3"/>'
              '<path d="M12 9v4"/><path d="M12 17h.01"/>',
    "dinero": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>'
              '<path d="M6 12h.01M18 12h.01"/>',
    "trofeo": '<path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0z"/>'
              '<path d="M17 5h3v2a3 3 0 0 1-3 3"/><path d="M7 5H4v2a3 3 0 0 0 3 3"/>',
    "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "edificio": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1"/>'
                '<path d="M10 21v-3h4v3"/>',
    "tendencia": '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    "personas": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
                '<path d="M22 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "diana": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "calendario": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    "balanza": '<path d="M12 3v18"/><path d="M6 21h12"/><path d="M4 7h16"/><path d="m7 7-3 7a3 3 0 0 0 6 0z"/>'
               '<path d="m17 7-3 7a3 3 0 0 0 6 0z"/>',
    "lista": '<path d="M10 6h11M10 12h11M10 18h11"/><path d="m3 6 1.5 1.5L7 5M3 12l1.5 1.5L7 11M3 18l1.5 1.5L7 17"/>',
    "porcentaje": '<path d="M19 5 5 19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "carpeta": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "libro": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/>'
             '<path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    "base": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/>'
            '<path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "ia": '<path d="M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7-4.7-1.8 4.7-1.8z"/>'
          '<path d="M19 15l.8 2.2 2.2.8-2.2.8L19 21l-.8-2.2-2.2-.8 2.2-.8z"/>',
    "llave": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="m10.7 12.3 9.3-9.3M16 7l3 3M14 9l2 2"/>',
    "escudo": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "correo": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "lupa": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "rayo": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "subir": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
    "mano": '<path d="M7 11V6a2 2 0 0 1 4 0v5M11 10V4a2 2 0 0 1 4 0v6M15 10V6a2 2 0 0 1 4 0v7a8 8 0 0 1-8 8h-1'
            'a7 7 0 0 1-6-3.4L2 14a2 2 0 0 1 3.4-2L7 14"/>',
}


def icono(nombre, color="currentColor", tam=20, grosor=2):
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round">{ICONOS[nombre]}</svg>')


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stMarkdown, p, label, li, input, textarea, button, h1, h2, h3, h4 { font-family: 'Plus Jakarta Sans', sans-serif; }
h1, h2, h3, h4 { color: #0B1B3F !important; letter-spacing: -0.02em; font-weight: 800 !important; }
h3 { font-size: 1.15rem !important; }
.stApp { background: #F4F7FC; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }

/* Barra lateral corporativa */
section[data-testid="stSidebar"] { border-right: 1px solid #E2E8F2; }
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 1.2rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; width: 100%; display: flex; flex-direction: column; }
section[data-testid="stSidebar"] [data-testid="stRadio"], section[data-testid="stSidebar"] [data-testid="stRadio"] > div { width: 100%; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { width: 100%; box-sizing: border-box; display: flex; padding: 10px 12px; border-radius: 10px; margin: 0; cursor: pointer; }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label p { font-weight: 600; color: #51607A; font-size: 15px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #F4F7FC; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) { background: #EAF1FF; box-shadow: inset 3px 0 0 #2563EB; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p { color: #1D4ED8; }

/* Selectores horizontales (dentro de las páginas) como segmentos */
.main div[role="radiogroup"][aria-orientation="horizontal"], [data-testid="stMain"] div[role="radiogroup"][aria-orientation="horizontal"] {
  gap: 4px; flex-wrap: wrap; background: #FFFFFF; border: 1px solid #E2E8F2; border-radius: 12px; padding: 4px; width: fit-content; }
[data-testid="stMain"] div[role="radiogroup"][aria-orientation="horizontal"] label { border-radius: 9px; padding: 7px 14px; margin: 0 !important; cursor: pointer; }
[data-testid="stMain"] div[role="radiogroup"][aria-orientation="horizontal"] label > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
[data-testid="stMain"] div[role="radiogroup"][aria-orientation="horizontal"] label p { font-weight: 600; color: #51607A; font-size: 14px; }
[data-testid="stMain"] div[role="radiogroup"][aria-orientation="horizontal"] label:has(input:checked) { background: #2563EB; }
[data-testid="stMain"] div[role="radiogroup"][aria-orientation="horizontal"] label:has(input:checked) p { color: #FFFFFF; }

/* Tarjetas, métricas y pestañas */
div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stVerticalBlock"][class*="st-key-"] { }
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) { }
div[data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF; border: 1px solid #E2E8F2 !important; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(11,27,63,.04), 0 6px 18px rgba(11,27,63,.04); }
div[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E2E8F2; border-radius: 14px; padding: 14px 16px; }
div[data-testid="stMetricValue"] { color: #0B1B3F; font-weight: 800; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #E2E8F2; }
.stTabs [data-baseweb="tab"] { padding: 10px 16px; font-weight: 600; color: #51607A; }
.stTabs [aria-selected="true"] { color: #2563EB !important; }
.stTabs [data-baseweb="tab-highlight"] { background: #2563EB; height: 3px; border-radius: 3px; }
.stButton button, .stDownloadButton button, .stFormSubmitButton button { border-radius: 10px; min-height: 42px; font-weight: 700; }
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB, #1D4ED8); border: 0; box-shadow: 0 6px 16px rgba(37,99,235,.25); }
[data-testid="stFileUploaderDropzone"] { background: #F8FAFF; border: 2px dashed #B9CCF5; border-radius: 14px; padding: 26px; }
[data-testid="stExpander"] details { border-radius: 12px; border-color: #E2E8F2; background: #FFFFFF; }
[data-testid="stDataFrame"] { border: 1px solid #E2E8F2; border-radius: 12px; overflow: hidden; }

/* Componentes propios */
.lg-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin: 0 0 18px; flex-wrap: wrap; }
.lg-head .crumb { font-size: 13px; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: .08em; }
.lg-head .tt { font-size: 30px; font-weight: 800; color: #0B1B3F; letter-spacing: -0.02em; line-height: 1.15; margin-top: 4px; }
.lg-head .st { font-size: 15px; color: #51607A; margin-top: 4px; max-width: 760px; }
.lg-head .der { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.lg-chip { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 4px 11px; font-size: 12.5px; font-weight: 700; white-space: nowrap; }
.lg-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 4px 0 18px; }
.lg-kpi { background: #FFFFFF; border: 1px solid #E2E8F2; border-radius: 16px; padding: 16px 18px; display: flex; gap: 14px; align-items: flex-start;
  box-shadow: 0 1px 2px rgba(11,27,63,.04); }
.lg-kpi { flex-direction: column; gap: 10px; }
.lg-kpi .top { display: flex; align-items: center; gap: 10px; }
.lg-kpi .ic { width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex: none; }
.lg-kpi .lb { font-size: 13px; font-weight: 600; color: #51607A; }
.lg-kpi .vl { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 24px; font-weight: 800; color: #0B1B3F; letter-spacing: -0.02em; line-height: 1.2; margin-top: 2px; }
.lg-kpi .nt { font-size: 12.5px; color: #7A879C; margin-top: 2px; }
.lg-sec { display: flex; align-items: center; gap: 10px; margin: 6px 0 10px; }
.lg-sec .ic { width: 32px; height: 32px; border-radius: 9px; display: flex; align-items: center; justify-content: center; }
.lg-sec .tt { font-size: 17px; font-weight: 800; color: #0B1B3F; }
.lg-sec .st { font-size: 13px; color: #7A879C; }
.lg-band { position: relative; overflow: hidden; border-radius: 20px; padding: 26px 30px; color: #FFFFFF;
  background: linear-gradient(120deg, #1D4ED8 0%, #2563EB 45%, #06B6D4 100%); margin-bottom: 18px; }
.lg-band::after { content: ""; position: absolute; inset: 0; background-image: radial-gradient(rgba(255,255,255,.22) 1px, transparent 1px);
  background-size: 18px 18px; mask-image: linear-gradient(90deg, transparent 35%, #000 100%); -webkit-mask-image: linear-gradient(90deg, transparent 35%, #000 100%); }
.lg-band .k { font-size: 13px; font-weight: 700; opacity: .85; text-transform: uppercase; letter-spacing: .08em; }
.lg-band .t { font-size: 28px; font-weight: 800; letter-spacing: -0.02em; margin-top: 4px; line-height: 1.2; position: relative; z-index: 1; }
.lg-band .s { font-size: 15px; opacity: .92; margin-top: 6px; max-width: 780px; position: relative; z-index: 1; }
.lg-qcard { background: #FFFFFF; border: 1px solid #E2E8F2; border-radius: 16px; padding: 16px 18px; height: 100%;
  position: relative; overflow: hidden; }
.lg-qcard::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--kc, #2563EB); }
.lg-qcard .top { display: flex; justify-content: space-between; align-items: center; }
.lg-qcard .ic { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.lg-qcard .q { font-size: 17px; font-weight: 800; color: #0B1B3F; margin-top: 12px; }
.lg-qcard .big { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin-top: 4px; }
.lg-qcard .r { font-size: 13.5px; color: #51607A; margin-top: 4px; line-height: 1.45; }
.lg-ring { width: 118px; height: 118px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex: none; }
.lg-ring > div { width: 88px; height: 88px; border-radius: 50%; background: #FFFFFF; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.lg-ring b { font-size: 26px; font-weight: 800; color: #0B1B3F; line-height: 1; }
.lg-ring small { font-size: 11px; color: #7A879C; font-weight: 600; }
.lg-prog { height: 8px; border-radius: 999px; background: #EEF2F7; overflow: hidden; }
.lg-prog > div { height: 100%; border-radius: 999px; }
.lg-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #EEF2F7; font-size: 14px; }
.lg-row:last-child { border-bottom: 0; }
.lg-date { width: 50px; flex: none; text-align: center; border-radius: 10px; background: #EAF1FF; color: #1D4ED8; padding: 5px 0; line-height: 1.1; }
.lg-date b { font-size: 18px; display: block; } .lg-date small { font-size: 11px; font-weight: 700; text-transform: uppercase; }
.lg-empty { text-align: center; padding: 28px 18px; border: 1.5px dashed #CBD6EA; border-radius: 16px; background: #FAFCFF; }
.lg-empty .ic { width: 52px; height: 52px; margin: 0 auto 10px; border-radius: 14px; background: #EAF1FF; display: flex; align-items: center; justify-content: center; }
.lg-empty .t { font-weight: 800; color: #0B1B3F; font-size: 16px; } .lg-empty .s { color: #51607A; font-size: 14px; margin-top: 4px; }
.lg-cita { background: #FFFBEB; border-left: 4px solid #F59E0B; border-radius: 10px; padding: 12px 16px; font-family: Georgia, serif; line-height: 1.6; }
.lg-aviso { background: #FFF7E6; color: #8A4B00; border: 1px solid #FCE2B0; border-radius: 12px; padding: 10px 14px; font-weight: 600; font-size: 14px; }
.lg-ok { background: #E8F8F1; color: #047857; border: 1px solid #BDEBD7; border-radius: 12px; padding: 10px 14px; font-weight: 600; font-size: 14px; }
.lg-info { background: #EEF4FF; color: #1E40AF; border: 1px solid #CFDDFB; border-radius: 12px; padding: 10px 14px; font-weight: 600; font-size: 14px; }
.lg-codigo { font-size: 26px; font-weight: 800; color: #1D4ED8; letter-spacing: .01em; }
.lg-bar { display: flex; height: 40px; border-radius: 10px; overflow: hidden; gap: 2px; margin: 8px 0; }
.lg-bar div { display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #0B1B3F; }
.lg-steps { display: flex; gap: 6px; margin-top: 8px; } .lg-steps span { flex: 1; height: 8px; border-radius: 999px; }
.lg-mini { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 6px; margin-top: 10px; }
.lg-mini span { border-radius: 10px; padding: 7px 4px; text-align: center; font-size: 11.5px; font-weight: 700; line-height: 1.3; }
.lg-feat { background: #FFFFFF; border: 1px solid #E2E8F2; border-radius: 16px; padding: 18px; height: 100%; }
.lg-feat .ic { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }
.lg-feat .t { font-weight: 800; color: #0B1B3F; font-size: 16px; } .lg-feat .s { color: #51607A; font-size: 14px; margin-top: 4px; line-height: 1.5; }
.lg-user { display: flex; gap: 10px; align-items: center; background: #F4F7FC; border: 1px solid #E2E8F2; border-radius: 12px; padding: 10px; }
.lg-user .av { width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg,#2563EB,#06B6D4); color: #fff;
  font-weight: 800; display: flex; align-items: center; justify-content: center; flex: none; }
.lg-status { font-size: 13px; color: #51607A; display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.lg-dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.lg-logo { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 20px; color: #0B1B3F; letter-spacing: -0.02em; }
.lg-logo .m { width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg,#2563EB,#06B6D4); display: inline-flex;
  align-items: center; justify-content: center; box-shadow: 0 6px 14px rgba(37,99,235,.3); }
.lg-logo small { display: block; font-size: 11px; font-weight: 600; color: #7A879C; letter-spacing: .02em; margin-top: -2px; }

/* ===================== COLOR EN TODA LA APP ===================== */
/* Botones: secundarios en azul suave, primarios con degradado y relieve */
.stButton button, .stDownloadButton button, .stFormSubmitButton button, .stLinkButton > a,
[data-testid="stPopover"] button { transition: transform .12s ease, box-shadow .12s ease, background .12s ease; }
.stButton button[kind="secondary"], .stFormSubmitButton button[kind="secondary"], [data-testid="stPopover"] button {
  background: #EEF4FF; color: #1D4ED8; border: 1px solid #CFDDFB; }
.stButton button[kind="secondary"]:hover, .stFormSubmitButton button[kind="secondary"]:hover, [data-testid="stPopover"] button:hover {
  background: #DCE8FF; border-color: #93B4F8; color: #1E40AF; transform: translateY(-1px); }
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {
  background: linear-gradient(135deg, #3B82F6, #2563EB); transform: translateY(-1px); box-shadow: 0 10px 22px rgba(37,99,235,.32); }
[class*="st-key-tono_verde_uso_"] .stButton button:disabled { background: #E3F8EF !important; color: #047857 !important; border-color: #BDEBD7 !important; opacity: 1; }
.stDownloadButton button[kind="secondary"] { background: #E3F8EF; color: #047857; border: 1px solid #BDEBD7; }
.stDownloadButton button[kind="secondary"]:hover { background: #CDF2E1; color: #065F46; border-color: #86DDB8; transform: translateY(-1px); }
.stLinkButton > a { background: #F2ECFF; color: #6D28D9 !important; border: 1px solid #DDD0FB; border-radius: 10px; font-weight: 700; min-height: 42px; }
.stLinkButton > a:hover { background: #E7DCFF; border-color: #C4B0F8; transform: translateY(-1px); }
.stButton button p, .stDownloadButton button p, .stFormSubmitButton button p, .stLinkButton > a p { font-weight: 700; }

/* Colores por clave del botón: key="tono_<color>_..." */
.stElementContainer[class*="st-key-tono_violeta_"] .stButton button { background: #F2ECFF; color: #6D28D9; border: 1px solid #DDD0FB; }
.stElementContainer[class*="st-key-tono_violeta_"] .stButton button[kind="primary"] { background: linear-gradient(135deg, #7C3AED, #6D28D9); color: #fff; border: 0; box-shadow: 0 6px 16px rgba(124,58,237,.28); }
.stElementContainer[class*="st-key-tono_cian_"] .stButton button { background: #E2F7FB; color: #0E7490; border: 1px solid #B5E8F2; }
.stElementContainer[class*="st-key-tono_cian_"] .stButton button[kind="primary"] { background: linear-gradient(135deg, #06B6D4, #0891B2); color: #fff; border: 0; box-shadow: 0 6px 16px rgba(8,145,178,.28); }
.stElementContainer[class*="st-key-tono_verde_"] .stButton button { background: #E3F8EF; color: #047857; border: 1px solid #BDEBD7; }
.stElementContainer[class*="st-key-tono_verde_"] .stButton button[kind="primary"] { background: linear-gradient(135deg, #10B981, #059669); color: #fff; border: 0; box-shadow: 0 6px 16px rgba(5,150,105,.28); }
.stElementContainer[class*="st-key-tono_ambar_"] .stButton button { background: #FFF4DD; color: #B45309; border: 1px solid #FCE2B0; }
.stElementContainer[class*="st-key-tono_ambar_"] .stButton button[kind="primary"] { background: linear-gradient(135deg, #F59E0B, #D97706); color: #fff; border: 0; box-shadow: 0 6px 16px rgba(217,119,6,.28); }
.stElementContainer[class*="st-key-tono_rojo_"] .stButton button { background: #FDECEC; color: #B91C1C; border: 1px solid #F8C9C9; }
.stElementContainer[class*="st-key-tono_rojo_"] .stButton button[kind="primary"] { background: linear-gradient(135deg, #EF4444, #DC2626); color: #fff; border: 0; box-shadow: 0 6px 16px rgba(220,38,38,.28); }
.stElementContainer[class*="st-key-tono_azul_"] .stButton button[kind="primary"] { background: linear-gradient(135deg, #2563EB, #1D4ED8); }
.stElementContainer[class*="st-key-tono_"] .stButton button:hover { filter: brightness(.97) saturate(1.1); transform: translateY(-1px); }
/* Botones de borrar y quitar en rojo */
.stElementContainer[class*="st-key-del_"] .stButton button, .st-key-borrar_cuenta .stButton button, .st-key-borrar_invitado .stButton button { background: #FDECEC; color: #B91C1C; border: 1px solid #F8C9C9; }
.stElementContainer[class*="st-key-del_"] .stButton button:hover, .st-key-borrar_cuenta .stButton button:hover, .st-key-borrar_invitado .stButton button:hover { background: #FBD5D5; color: #991B1B; }
/* Google: botón blanco con borde de color, como el de Google */
.st-key-btn_google .stButton button { background: linear-gradient(135deg, #2563EB, #06B6D4); border: 0; }

/* Menú lateral: cada página con su color */
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #FFFFFF 0%, #F5F8FF 100%); }
section[data-testid="stSidebar"] div[role="radiogroup"] label span[role="img"] {
  width: 30px; height: 30px; border-radius: 9px; display: inline-flex; align-items: center; justify-content: center;
  margin-right: 8px; font-size: 18px; vertical-align: middle; color: var(--mc); background: var(--mb); }
section[data-testid="stSidebar"] div[role="radiogroup"] label p { display: flex; align-items: center; }
section[data-testid="stSidebar"] div[role="radiogroup"] { align-items: stretch; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div { width: 100%; }
section[data-testid="stSidebar"] .stElementContainer:has([data-testid="stRadio"]), section[data-testid="stSidebar"] [data-testid="stRadio"], section[data-testid="stSidebar"] [data-testid="stRadioGroup"] { width: 100% !important; }
section[data-testid="stSidebar"] [data-testid="stRadioOption"] { width: 100% !important; padding: 7px 10px !important; }
.stButton button, .stDownloadButton button, .stFormSubmitButton button, .stLinkButton > a,
.stButton button p, .stDownloadButton button p, .stFormSubmitButton button p { font-family: 'Plus Jakarta Sans', sans-serif !important; }
/* Cargador de PDF en español */
[data-testid="stFileUploaderDropzoneInstructions"] span { font-size: 0 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span::after { content: "Arrastra aquí el PDF de las bases · hasta 50 MB"; font-size: 14px; color: #51607A; font-weight: 600; }
[data-testid="stFileUploaderDropzone"] button p { font-size: 0 !important; }
[data-testid="stFileUploaderDropzone"] button p::after { content: "Elegir PDF"; font-size: 15px; font-weight: 700; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(1) label { --mc: #2563EB; --mb: #EAF1FF; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(2) label { --mc: #7C3AED; --mb: #F2ECFF; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(3) label { --mc: #0891B2; --mb: #E2F7FB; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(4) label { --mc: #059669; --mb: #E3F8EF; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(5) label { --mc: #D97706; --mb: #FFF4DD; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(6) label { --mc: #DB2777; --mb: #FDEAF3; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child(7) label { --mc: #475569; --mb: #EEF2F7; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(120deg, var(--mc), color-mix(in srgb, var(--mc) 70%, #06B6D4)); box-shadow: 0 8px 18px color-mix(in srgb, var(--mc) 30%, transparent); }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p { color: #FFFFFF; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span[role="img"] { background: rgba(255,255,255,.22); color: #FFFFFF; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover:not(:has(input:checked)) { background: var(--mb); }
section[data-testid="stSidebar"] .lg-user { background: linear-gradient(120deg, #EAF1FF, #F2ECFF); border-color: #DCE4F7; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { font-weight: 700; letter-spacing: .06em; color: #7A879C; }

/* Encabezados, pestañas, expanders y entradas con color */
.lg-head .crumb { display: inline-block; background: linear-gradient(90deg, #EAF1FF, #F2ECFF); color: #4338CA;
  padding: 4px 12px; border-radius: 999px; font-size: 12px; }
.lg-head .tt { background: linear-gradient(90deg, #0B1B3F 0%, #1E3A8A 60%, #2563EB 100%); -webkit-background-clip: text;
  background-clip: text; color: transparent; }
.stTabs [role="tablist"] { gap: 6px; background: #FFFFFF; border: 1px solid #E2E8F2; border-radius: 14px; padding: 5px;
  width: fit-content; max-width: 100%; flex-wrap: wrap; }
.stTabs [data-testid="stTab"] { border-radius: 10px; padding: 8px 16px; cursor: pointer; }
.stTabs [data-testid="stTab"] p { font-weight: 700; color: #51607A; }
.stTabs [data-testid="stTab"][aria-selected="true"] { background: linear-gradient(120deg, #2563EB, #06B6D4); box-shadow: 0 6px 14px rgba(37,99,235,.25); }
.stTabs [data-testid="stTab"][aria-selected="true"] p, .stTabs [data-testid="stTab"][aria-selected="true"] span[role="img"] { color: #FFFFFF !important; }
.stTabs [data-testid="stTab"]:hover:not([aria-selected="true"]) { background: #EEF4FF; }
.stTabs [data-testid="stTab"]:hover:not([aria-selected="true"]) p { color: #1D4ED8; }
[data-testid="stExpander"] details summary { background: linear-gradient(90deg, #F5F8FF, #FFFFFF); border-radius: 12px; }
[data-testid="stExpander"] details summary span[role="img"], [data-testid="stExpander"] details summary [data-testid="stIconMaterial"] { color: #7C3AED; }
[data-testid="stExpander"] details summary:hover p { color: #2563EB; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, textarea:focus { border-color: #2563EB !important; box-shadow: 0 0 0 3px rgba(37,99,235,.15); }
[data-baseweb="tag"] { background: #EAF1FF !important; } [data-baseweb="tag"] span { color: #1D4ED8 !important; }
[data-testid="stFileUploaderDropzone"] { background: linear-gradient(135deg, #F5F8FF, #F2ECFF); border-color: #A5B8F3; }
[data-testid="stFileUploaderDropzone"] button { background: linear-gradient(135deg, #2563EB, #7C3AED); color: #fff; border: 0; }

/* Ficha: índice + 6 datos + 4 preguntas en UNA rejilla de 4 columnas (mismos bordes y mismo espacio) */
.lg-ficha { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 0 0 14px; align-items: stretch; }
.lg-ficha > * { min-width: 0; height: 100%; box-sizing: border-box; margin: 0; }
.lg-ficha .lg-indice { grid-row: span 2; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; text-align: center; }
.lg-ficha .lg-indice .k { font-size: 12px; font-weight: 700; color: #7A879C; letter-spacing: .06em; }
.lg-ficha .lg-indice .lg-ring { width: 132px; height: 132px; } .lg-ficha .lg-indice .lg-ring > div { width: 100px; height: 100px; }
.lg-ficha .lg-indice .lg-ring b { font-size: 32px; }
@media (max-width: 1000px) { .lg-ficha { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { .lg-ficha { grid-template-columns: minmax(0, 1fr); } .lg-ficha .lg-indice { grid-row: auto; } }

/* ¿Puedo?: requisito | piden | tienes | estado, con anchos fijos */
.lg-req { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 1.2fr) 150px; gap: 16px; align-items: start; }
.lg-req .ch { display: flex; justify-content: flex-end; padding-top: 2px; }
@media (max-width: 800px) { .lg-req { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } .lg-req .ch { justify-content: flex-start; } }

/* Indicadores (KPI) con barra de color arriba */
.lg-kpi { position: relative; overflow: hidden; border-top: 0; }
.lg-kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--kc, #2563EB); }
.lg-kpi { background: linear-gradient(180deg, var(--kb, #F5F8FF) 0%, #FFFFFF 55%); }

/* Bandas de demo (portada y Ejemplos) */
.st-key-ej_hero, .st-key-portada_demo { background: linear-gradient(120deg, #6D28D9 0%, #2563EB 55%, #06B6D4 100%);
  border-radius: 20px; padding: 22px 26px; box-shadow: 0 18px 40px rgba(76,29,149,.22); }
.st-key-ej_hero .k, .st-key-portada_demo .k { color: #E0E7FF; font-size: 12.5px; font-weight: 800; letter-spacing: .08em; }
.st-key-ej_hero .t, .st-key-portada_demo .t { color: #FFFFFF; font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin-top: 2px; }
.st-key-ej_hero .s, .st-key-portada_demo .s { color: #E8EEFF; font-size: 15px; margin-top: 4px; max-width: 760px; }
.st-key-ej_hero .stButton button[kind="primary"], .st-key-portada_demo .stButton button[kind="primary"] { background: #FFFFFF; color: #4C1D95;
  min-height: 52px; font-size: 16px; box-shadow: 0 10px 24px rgba(15,23,42,.25); }
.st-key-ej_hero button[kind="primary"] p, .st-key-portada_demo button[kind="primary"] p { color: #4C1D95; font-size: 16px; }
.st-key-ej_hero .stButton button[kind="primary"]:hover, .st-key-portada_demo .stButton button[kind="primary"]:hover { background: #F5F3FF; }
.st-key-rev_ejemplos { }
.st-key-emp_ejemplo_caja { background: linear-gradient(120deg, #F5F3FF, #EEF4FF); border: 1px dashed #C4B0F8; border-radius: 14px; padding: 10px 14px 14px; margin-bottom: 8px; }

/* Tarjetas de ejemplos */
.lg-ej .hd { display: flex; gap: 12px; align-items: center; margin: -2px 0 10px; }
.lg-ej .ic { width: 42px; height: 42px; border-radius: 12px; flex: none; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--c), color-mix(in srgb, var(--c) 65%, #06B6D4)); box-shadow: 0 8px 16px color-mix(in srgb, var(--c) 30%, transparent); }
.lg-ej .k { font-size: 11.5px; font-weight: 800; color: var(--c); letter-spacing: .06em; text-transform: uppercase; display: flex; gap: 4px; align-items: center; }
.lg-ej .t { font-weight: 800; color: #0B1B3F; font-size: 16px; line-height: 1.25; }
.lg-ej .s { color: #51607A; font-size: 13.5px; line-height: 1.45; }
.lg-ej .ch { display: flex; gap: 6px; flex-wrap: wrap; }
/* Cartas de empresa: mismo alto de título y descripción (2 líneas) para que chips y botones queden en la misma línea */
.lg-ej .t { min-height: 2.5em; display: flex; align-items: center; }
.lg-ej .s { min-height: 2.9em; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
/* Y la carta entera ocupa todo el alto de su columna, con el botón pegado abajo */
.st-key-cartas_iguales [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height: 100%; }
.st-key-cartas_iguales [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] { flex: 1 1 auto; display: flex; flex-direction: column; }
.st-key-cartas_iguales [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] { flex: 1 1 auto; }
.st-key-cartas_iguales [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child { margin-top: auto; }
/* Barra de acciones de la ficha: el aviso mide lo mismo que los botones */
.lg-info.lg-barra { min-height: 42px; padding: 0 14px; display: flex; align-items: center; box-sizing: border-box; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] > div[data-testid="stMarkdown"] .lg-ej.t-violeta) { background: linear-gradient(#7C3AED, #7C3AED) top / 100% 4px no-repeat, #FFFFFF !important; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] > div[data-testid="stMarkdown"] .lg-ej.t-cian) { background: linear-gradient(#06B6D4, #06B6D4) top / 100% 4px no-repeat, #FFFFFF !important; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] > div[data-testid="stMarkdown"] .lg-ej.t-ambar) { background: linear-gradient(#F59E0B, #F59E0B) top / 100% 4px no-repeat, #FFFFFF !important; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] > div[data-testid="stMarkdown"] .lg-ej.t-verde) { background: linear-gradient(#10B981, #10B981) top / 100% 4px no-repeat, #FFFFFF !important; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] > div[data-testid="stMarkdown"] .lg-ej.t-azul) { background: linear-gradient(#2563EB, #2563EB) top / 100% 4px no-repeat, #FFFFFF !important; }

/* ===================== AYUDAS AL PASAR EL CURSOR ===================== */
[data-tip] { position: relative; }
[data-tip]:hover::after { content: attr(data-tip); position: absolute; left: 0; top: calc(100% + 8px); z-index: 99999;
  width: max-content; max-width: 280px; white-space: normal; text-align: left; background: #0B1B3F; color: #FFFFFF;
  padding: 9px 12px; border-radius: 10px; font-size: 12.5px; font-weight: 500; line-height: 1.45; letter-spacing: 0;
  text-transform: none; box-shadow: 0 12px 28px rgba(11,27,63,.28); pointer-events: none; }
[data-tip]:hover::before { content: ""; position: absolute; left: 14px; top: calc(100% + 2px); z-index: 99999;
  border: 6px solid transparent; border-bottom-color: #0B1B3F; pointer-events: none; }
.lg-kpi { overflow: visible; cursor: help; }
.lg-kpi::before { border-radius: 16px 16px 0 0; }
.lg-kpi .lb .q { display: inline-flex; width: 15px; height: 15px; border-radius: 50%; background: #E2E8F2; color: #51607A;
  font-size: 10px; font-weight: 800; align-items: center; justify-content: center; margin-left: 5px; vertical-align: 1px; }
.lg-kpi:hover { box-shadow: 0 10px 24px rgba(11,27,63,.10); transform: translateY(-1px); transition: all .15s ease; z-index: 60; }
.lg-kpi { position: relative; }
.lg-kpi[data-tip]:hover::after { left: 12px; top: calc(100% + 6px); }
.lg-kpi[data-tip]:hover::before { left: 26px; top: calc(100% - 6px); }
.lg-term:hover { position: relative; z-index: 60; }
.lg-band .lg-term { border-bottom-color: rgba(255,255,255,.85); }
.lg-term { border-bottom: 1.5px dotted #7C3AED; cursor: help; color: inherit; }
.lg-term:hover { background: #F2ECFF; border-radius: 4px; }
/* Menú: descripción al pasar el cursor */
section[data-testid="stSidebar"] div[role="radiogroup"] > div { position: relative; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div:hover::after { position: absolute; left: 12px; right: 12px;
  top: calc(100% - 2px); z-index: 9999; background: #0B1B3F; color: #fff; font-size: 12.5px; line-height: 1.4; font-weight: 500;
  padding: 8px 11px; border-radius: 10px; box-shadow: 0 12px 26px rgba(11,27,63,.28); pointer-events: none; }

/* Empresa activa (menú lateral) */
.lg-activa { margin-top: 10px; border-radius: 12px; padding: 10px 12px; color: #FFFFFF;
  background: linear-gradient(120deg, #4C1D95, #2563EB 60%, #0891B2); box-shadow: 0 8px 18px rgba(76,29,149,.22); }
.lg-activa .k { font-size: 10.5px; font-weight: 800; letter-spacing: .08em; opacity: .85; }
.lg-activa .t { font-size: 15px; font-weight: 800; line-height: 1.25; margin-top: 2px; }
.lg-activa .s { font-size: 12.5px; opacity: .9; }

/* ===================== GUÍA DE CADA PÁGINA ===================== */
[class*="st-key-guia_"] { background: linear-gradient(120deg, #F5F3FF 0%, #EEF4FF 100%); border: 1px solid #DDD0FB;
  border-radius: 14px; padding: 6px 12px; margin-bottom: 6px; }
.lg-guia { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.lg-guia .ic { width: 28px; height: 28px; border-radius: 8px; background: linear-gradient(135deg, #7C3AED, #2563EB);
  display: flex; align-items: center; justify-content: center; flex: none; }
.lg-guia .t { font-weight: 800; color: #4C1D95; font-size: 14px; } .lg-guia .s { color: #51607A; font-size: 14px; }
.lg-guia .pasos { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.lg-guia .pasos span { background: #FFFFFF; border: 1px solid #DDD0FB; color: #5B21B6; border-radius: 999px; padding: 3px 10px;
  font-size: 12px; font-weight: 700; }
.lg-guia .pasos b { background: #7C3AED; color: #fff; border-radius: 50%; display: inline-flex; width: 17px; height: 17px;
  align-items: center; justify-content: center; font-size: 10.5px; margin-right: 5px; }
.st-key-siguiente_paso { background: #FFFFFF; border: 1px solid #E2E8F2; border-left: 5px solid #10B981; border-radius: 14px;
  padding: 12px 16px; margin-top: 18px; }

/* ===================== ASISTENTE FLOTANTE ===================== */
.block-container { padding-bottom: 6rem !important; }
.st-key-asistente_boton { position: fixed !important; right: 28px; bottom: 24px; z-index: 99990; width: auto !important; }
.st-key-asistente_boton .stButton button { background: linear-gradient(135deg, #7C3AED, #2563EB); color: #FFFFFF;
  border: 0; border-radius: 999px; min-height: 52px; padding: 0 22px; box-shadow: 0 14px 30px rgba(76,29,149,.35); }
.st-key-asistente_boton .stButton button p { color: #FFFFFF; font-size: 15px; }
.st-key-asistente_boton .stButton button:hover { transform: translateY(-2px); filter: brightness(1.05); }
[class*="st-key-asistente_panel"] { position: fixed !important; right: 28px; bottom: 88px; z-index: 99991; width: 420px !important;
  max-width: calc(100vw - 32px); max-height: calc(100vh - 120px); overflow-y: auto; background: #FFFFFF;
  border-radius: 20px; padding: 18px 18px 8px; box-shadow: 0 28px 70px rgba(11,27,63,.32);
  background: linear-gradient(90deg, #7C3AED, #2563EB) top / 100% 5px no-repeat, #FFFFFF; }
/* Expandido: casi toda la pantalla, para leer explicaciones largas con calma */
.st-key-asistente_panel_xl { width: min(920px, calc(100vw - 56px)) !important; }
.st-key-asistente_panel_xl [data-testid="stChatMessage"] p, .st-key-asistente_panel_xl [data-testid="stChatMessage"] li { font-size: 15px !important; line-height: 1.6 !important; }
.lg-chat-ctx { display: flex; gap: 8px; align-items: center; background: #F5F3FF; border: 1px solid #E4DBFD; color: #5B21B6;
  border-radius: 10px; padding: 7px 10px; font-size: 12.5px; font-weight: 600; margin: 2px 0 4px; }
.lg-chat-ctx span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
[class*="st-key-asistente_panel"] [data-testid="stChatMessage"] ul { margin: 4px 0 6px; padding-left: 18px; }
[class*="st-key-asistente_panel"] [class*="st-key-asis_idea_"] button { justify-content: flex-start; text-align: left; min-height: 38px; }
[class*="st-key-asistente_panel"] [class*="st-key-asis_idea_"] button p { font-weight: 600; font-size: 13.5px; }
.lg-chat-hd { display: flex; gap: 10px; align-items: center; }
.lg-chat-hd .ic { width: 36px; height: 36px; border-radius: 11px; background: linear-gradient(135deg, #7C3AED, #2563EB);
  display: flex; align-items: center; justify-content: center; flex: none; }
.lg-chat-hd .t { font-weight: 800; color: #0B1B3F; font-size: 15px; } .lg-chat-hd .s { color: #7A879C; font-size: 12.5px; }
.st-key-asistente_mensajes { background: #F7F9FD; border-radius: 14px; }
[class*="st-key-asistente_panel"] [data-testid="stChatMessage"] p, [class*="st-key-asistente_panel"] [data-testid="stChatMessage"] li { font-size: 14px; line-height: 1.5; }
[class*="st-key-asistente_panel"] [data-testid="stChatMessage"] { padding: 8px 10px; }
[class*="st-key-asis_idea_"] .stButton button { background: #F5F3FF; color: #5B21B6; border: 1px solid #DDD0FB;
  justify-content: flex-start; min-height: 36px; font-size: 13.5px; }
@media (max-width: 640px) { [class*="st-key-asistente_panel"] { right: 16px; left: 16px; width: auto !important; bottom: 84px; }
  .st-key-asistente_boton { right: 16px; bottom: 16px; } }

/* ===================== RECORRIDO GUIADO ===================== */
.st-key-tour_burbuja { position: fixed !important; right: 28px; bottom: 28px; width: 390px !important; max-width: calc(100vw - 32px);
  z-index: 100001; background: #FFFFFF; border-radius: 18px; padding: 18px 18px 12px; border-top: 6px solid #7C3AED;
  box-shadow: 0 24px 60px rgba(11,27,63,.35); }
.st-key-tour_burbuja .k { font-size: 12px; font-weight: 800; color: #7C3AED; letter-spacing: .06em; }
.st-key-tour_burbuja .t { font-size: 18px; font-weight: 800; color: #0B1B3F; margin-top: 2px; }
.st-key-tour_burbuja .s { font-size: 14px; color: #334155; line-height: 1.5; margin-top: 4px; }
.st-key-tour_burbuja .dots { display: flex; gap: 5px; margin-top: 10px; }
.st-key-tour_burbuja .dots i { height: 6px; flex: 1; border-radius: 999px; background: #E9E3FB; }
.st-key-tour_burbuja .dots i.on { background: linear-gradient(90deg, #7C3AED, #2563EB); }
.st-key-tour_burbuja iframe { display: none; }
@media (max-width: 640px) { .st-key-tour_burbuja { right: 16px; left: 16px; bottom: 16px; width: auto !important; } }
</style>
"""

# Las 4 preguntas: clave, número, título, ícono, tono
PREGUNTAS = [
    ("justa", "1", "¿Es justa?", "balanza", "violeta"),
    ("puedo", "2", "¿Puedo?", "lista", "azul"),
    ("conviene", "3", "¿Me conviene?", "dinero", "ambar"),
    ("ganar", "4", "¿Puedo ganar?", "trofeo", "cian"),
]
ESTADOS = {"bien": "Bien", "ojo": "Ojo", "cuidado": "Cuidado", "sin_datos": "Sin datos"}
TONO_ESTADO = {"bien": "verde", "ojo": "ambar", "cuidado": "rojo", "sin_datos": "gris"}
COLOR_ESTADO = {k: TONOS[v] for k, v in TONO_ESTADO.items()}
ETIQUETA_RECO = {"postular": ("Postular", "verde"), "observar": ("Observar primero", "ambar"),
                 "no_postular": ("No te conviene", "rojo")}
GRADIENTE_RECO = {"postular": "linear-gradient(120deg,#047857,#10B981)",
                  "observar": "linear-gradient(120deg,#C2410C,#F59E0B)",
                  "no_postular": "linear-gradient(120deg,#B91C1C,#F43F5E)"}
ICONO_RECO = {"postular": "check", "observar": "alerta", "no_postular": "alerta"}
SEVERIDAD = {"fuerte": "Fuerte", "media": "Media", "leve": "Leve", "info": "Info"}
TONO_SEVERIDAD = {"fuerte": "rojo", "media": "ambar", "leve": "verde", "info": "gris"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"]
MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre",
               "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(t):
    return html.escape(str(t if t is not None else ""))


def html_md(contenido: str):
    st.markdown(contenido, unsafe_allow_html=True)


def soles(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    if n != n:  # NaN
        return "—"
    if abs(n) >= 1_000_000:
        return f"S/ {n / 1_000_000:,.1f} M".replace(",", "X").replace(".", ",").replace("X", " ")
    if abs(n) >= 10_000:
        return f"S/ {n / 1_000:,.0f} mil".replace(",", " ")
    return f"S/ {n:,.0f}".replace(",", " ")


def soles_exacto(n):
    try:
        return f"S/ {float(n):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return "—"


def entero(n):
    try:
        return f"{int(n):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "—"


def hoy_texto():
    h = hoy_lima()
    return f"{DIAS[h.weekday()].capitalize()} {h.day} de {MESES_LARGO[h.month - 1]} de {h.year}"


def fecha_corta(iso):
    try:
        f = date.fromisoformat(str(iso)[:10])
        return f.day, MESES[f.month - 1]
    except ValueError:
        return "—", ""


# ------------------------------------------------------------------------------------------
# Componentes
# ------------------------------------------------------------------------------------------
_TERMINOS = sorted(GLOSARIO, key=len, reverse=True)
_PATRON_TERMINOS = re.compile(r"(?<![\wÁÉÍÓÚáéíóúñÑ])(" + "|".join(re.escape(t) for t in _TERMINOS)
                              + r")(?![\wÁÉÍÓÚáéíóúñÑ])", re.IGNORECASE)
_DEF = {t.lower(): d for t, d in GLOSARIO.items()}


def con_glosario(texto) -> str:
    """Escapa el texto y subraya (una vez cada uno) los términos del glosario con su significado al pasar el cursor."""
    usados = set()

    def poner(m):
        clave = m.group(0).lower()
        if clave in usados:
            return m.group(0)
        usados.add(clave)
        return f'<span class="lg-term" data-tip="{html.escape(_DEF[clave], quote=True)}">{m.group(0)}</span>'
    return _PATRON_TERMINOS.sub(poner, esc(texto))


def css_menu(paginas) -> str:
    """Descripción de cada página del menú al pasar el cursor (en el orden del menú)."""
    reglas = [f'section[data-testid="stSidebar"] div[role="radiogroup"] > div:nth-child({i}):hover::after '
              f'{{ content: "{AYUDA_MENU[p]}"; }}' for i, p in enumerate(paginas, 1) if p in AYUDA_MENU]
    return "<style>" + "\n".join(reglas) + "</style>"


def chip(texto, tono="gris", ico=None):
    fg, bg = TONOS[tono]
    i = icono(ico, fg, 14, 2.4) if ico else ""
    return f'<span class="lg-chip" style="color:{fg};background:{bg}">{i}{esc(texto)}</span>'


def pill_reco(codigo):
    t, tono = ETIQUETA_RECO.get(codigo, ("Sin revisar", "gris"))
    return chip(t, tono)


def logo():
    html_md(f'<div class="lg-logo"><span class="m">{icono("escudo", "#FFFFFF", 19, 2.4)}</span>'
            f'<div>LiciGuard<small>Inteligencia para licitar</small></div></div>')


DESPUES_DEL_ENCABEZADO = []   # app.py registra aquí la guía de la página


def encabezado(migas, titulo, subtitulo="", derecha=""):
    html_md(f'<div class="lg-head"><div><div class="crumb">{esc(migas)}</div><div class="tt">{esc(titulo)}</div>'
            f'{f"<div class=st>{esc(subtitulo)}</div>" if subtitulo else ""}</div>'
            f'<div class="der">{derecha}</div></div>')
    while DESPUES_DEL_ENCABEZADO:
        DESPUES_DEL_ENCABEZADO.pop()()


def seccion(titulo, subtitulo="", ico="tendencia", tono="azul"):
    fg, bg = TONOS[tono]
    html_md(f'<div class="lg-sec"><div class="ic" style="background:{bg}">{icono(ico, fg, 17)}</div>'
            f'<div><div class="tt">{esc(titulo)}</div>{f"<div class=st>{esc(subtitulo)}</div>" if subtitulo else ""}'
            f'</div></div>')


def kpi_html(etiqueta, valor, nota, ico, tono) -> str:
    fg, bg = TONOS[tono]
    ayuda = AYUDA_INDICADORES.get(etiqueta)
    tip = f' data-tip="{esc(ayuda)}"' if ayuda else ""
    etiqueta_html = f'{esc(etiqueta)}<span class="q">?</span>' if ayuda else esc(etiqueta)
    return (f'<div class="lg-kpi"{tip} style="--kc:{fg};--kb:{bg}"><div class="top"><div class="ic" style="background:{bg}">'
            f'{icono(ico, fg, 18)}</div><div class="lb">{etiqueta_html}</div></div><div style="min-width:0;width:100%">'
            f'<div class="vl" title="{esc(valor)}">{esc(valor)}</div>'
            f'{f"<div class=nt>{esc(nota)}</div>" if nota else ""}</div></div>')


def kpis(items, columnas=None):
    """items: lista de (etiqueta, valor, nota, icono, tono)."""
    estilo = f' style="grid-template-columns:repeat({columnas},minmax(0,1fr))"' if columnas else ""
    html_md(f'<div class="lg-kpis"{estilo}>{"".join(kpi_html(*i) for i in items)}</div>')


def anillo(pct, color=AZUL, texto=None, sub=""):
    pct = max(0, min(100, float(pct or 0)))
    return (f'<div class="lg-ring" style="background:conic-gradient({color} {pct * 3.6:.0f}deg,#EEF2F7 0)">'
            f'<div><b>{esc(texto if texto is not None else f"{pct:.0f}%")}</b><small>{esc(sub)}</small></div></div>')


def progreso(pct, color=AZUL):
    pct = max(0, min(100, float(pct or 0)))
    return f'<div class="lg-prog"><div style="width:{pct:.1f}%;background:{color}"></div></div>'


def vacio(ico, titulo, texto):
    html_md(f'<div class="lg-empty"><div class="ic">{icono(ico, AZUL, 26)}</div><div class="t">{esc(titulo)}</div>'
            f'<div class="s">{con_glosario(texto)}</div></div>')


def banda(kicker, titulo, texto, fondo=None, ico=None):
    estilo = f' style="background:{fondo}"' if fondo else ""
    i = (f'<div style="position:absolute;right:26px;top:22px;opacity:.9;z-index:1">{icono(ico, "#FFFFFF", 40, 1.8)}</div>'
         if ico else "")
    html_md(f'<div class="lg-band"{estilo}>{i}<div class="k">{esc(kicker)}</div><div class="t">{esc(titulo)}</div>'
            f'<div class="s">{esc(texto)}</div></div>')


def banner(rec):
    banda("Nuestra recomendación", rec["titulo"], rec["detalle"], GRADIENTE_RECO.get(rec["codigo"]),
          ICONO_RECO.get(rec["codigo"]))


def indicador_pregunta(res, clave):
    """Número grande de cada pregunta (lo que se ve primero en la tarjeta)."""
    r = res.get(clave) or {}
    if clave == "justa":
        n = len(r.get("hallazgos", []))
        return (f"{n} alerta{'s' if n != 1 else ''}" if n else "Sin alertas")
    if clave == "puedo":
        return f"{r['cumple']} de {r['total']}" if r.get("total") else "—"
    if clave == "conviene":
        return f"{r['margen']:.1f} %".replace(".", ",") if r.get("margen") is not None else "—"
    if clave == "ganar":
        return f"{r.get('n', 0)} previos" if r.get("n") else "—"
    return "—"


def tarjeta_pregunta_html(res, clave, num, titulo, ico, tono) -> str:
    est = res[clave]["estado"]
    fg, bg = TONOS[tono]
    efg, _ = COLOR_ESTADO[est]
    return (f'<div class="lg-qcard" style="--kc:{fg}"><div class="top">'
            f'<div class="ic" style="background:{bg}">{icono(ico, fg, 19)}</div>{chip(ESTADOS[est], TONO_ESTADO[est])}</div>'
            f'<div class="q">{num} · {titulo}</div><div class="big" style="color:{efg}">{esc(indicador_pregunta(res, clave))}</div>'
            f'<div class="r">{con_glosario(res[clave]["resumen"])}</div></div>')


def tarjeta_pregunta(res, clave, num, titulo, ico, tono):
    html_md(tarjeta_pregunta_html(res, clave, num, titulo, ico, tono))


def mini_estados(resultado) -> str:
    if not resultado:
        return ""
    partes = []
    for clave, _, titulo, _, _ in PREGUNTAS:
        est = (resultado.get(clave) or {}).get("estado", "sin_datos")
        fg, bg = COLOR_ESTADO[est]
        partes.append(f'<span style="background:{bg};color:{fg}">{titulo.strip("¿?")}<br>{ESTADOS[est]}</span>')
    return f'<div class="lg-mini">{"".join(partes)}</div>'


def barra_etapas(etapa, colores, etapas_linea=("Revisada", "Observada", "Ofertada", "Resultado")):
    orden = {"Revisada": 0, "Observada": 1, "Ofertada": 2, "Ganada": 3, "Perdida": 3, "Descartada": 3}
    n = orden.get(etapa, 0)
    color = colores.get(etapa, AZUL)
    partes = "".join(f'<span style="background:{color if i <= n else "#E6EBF3"}"></span>' for i in range(4))
    nombres = "".join(f'<small style="flex:1;color:{TEXTO2};font-weight:600;font-size:12px">{e}</small>'
                      for e in etapas_linea)
    return f'<div class="lg-steps">{partes}</div><div style="display:flex;gap:6px;margin-top:4px">{nombres}</div>'


def indice_apertura(res) -> int:
    """0–100: qué tan abiertas a la competencia parecen las bases (criterio LiciGuard, no legal)."""
    pesos = {"fuerte": 25, "media": 12, "leve": 5}
    return max(0, 100 - sum(pesos.get(h["severidad"], 0) for h in res["justa"]["hallazgos"]))


def grafico(chart, alto=240):
    """Estilo común para los gráficos Altair."""
    return (chart.properties(height=alto)
            .configure(font="Plus Jakarta Sans, Segoe UI, Helvetica, Arial, sans-serif")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=TEXTO2, titleColor=TEXTO2, gridColor="#EEF2F7", domainColor=BORDE,
                            tickColor=BORDE, labelFontSize=12, labelLimit=230, titleFontSize=12, titleFontWeight=600)
            .configure_legend(labelColor=TEXTO2, titleColor=TEXTO2, orient="bottom"))


def mostrar(chart, alto=240):
    st.altair_chart(grafico(chart, alto), width="stretch")


__all__ = ["alt"]
