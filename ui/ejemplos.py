"""Ejemplos: bases de licitación del rubro de tu empresa activa, para probar LiciGuard en 1 clic."""
import streamlit as st

from core import ejemplos as X
from ui import estado as E
from ui.tema import TONOS, chip, encabezado, esc, html_md, icono, seccion, soles, vacio

ss = st.session_state
ORIGEN = {"demo": ("Ejemplo ficticio", "violeta", "rayo"), "real": ("Real · SEACE", "cian", "base"),
          "descargada": ("Real · bajada por ti", "verde", "subir")}
ESPERADO = {"postular": ("Postular", "verde"), "observar": ("Observar primero", "ambar"),
            "no_postular": ("No te conviene", "rojo")}


# ------------------------------------------------------------------------------------------
# Acciones (también desde Inicio, Revisar bases, el selector de empresas y el menú)
# ------------------------------------------------------------------------------------------
def abrir_base(id_base: str):
    """Abre unas bases de ejemplo con el perfil de la empresa activa."""
    if not X.base(id_base):
        return
    ss.ejemplo_pendiente = id_base
    E.ir_a("Revisar bases", sha_actual=None, abierto=None)


def base_demo(rubro: str | None, razon_social: str | None = None) -> dict | None:
    """La base que mejor enseña para esta empresa: la de su demo; si no, la primera de su rubro."""
    emp = X.empresa_por_razon(razon_social)
    if emp and X.DEMO_DE_EMPRESA.get(emp["id"]):
        return X.base(f"demo:{X.DEMO_DE_EMPRESA[emp['id']]}")
    bases = X.bases_de_rubro(rubro) if rubro else []
    return bases[0] if bases else None


def demo_de_empresa_activa():
    """Abre la base de ejemplo del rubro de la empresa activa y arranca el recorrido guiado."""
    p = E.perfil() or {}
    b = base_demo(p.get("rubro"), p.get("razon_social"))
    if not b:
        ss.aviso_ejemplo = "Aún no hay bases de ejemplo de tu rubro. Sube un PDF en «Revisar bases»."
        E.ir_a("Revisar bases")
        return
    abrir_base(b["id"])
    ss.tour_paso = 0


# ------------------------------------------------------------------------------------------
# Tarjeta de una base
# ------------------------------------------------------------------------------------------
def _tarjeta_base(b):
    origen, tono_o, ico_o = ORIGEN[b["origen"]]
    fg, bg = TONOS[tono_o]
    esperado = ""
    if b.get("esperado"):
        t, tono = ESPERADO[b["esperado"]]
        esperado = f'<div class="s" style="margin-top:8px">Resultado con la empresa modelo: {chip(t, tono)}</div>'
    datos = " · ".join(x for x in [b.get("entidad"), soles(b["valor"]) if b.get("valor") else "",
                                   b.get("fecha")] if x)
    html_md(f'<div class="lg-ej t-{tono_o}" style="--c:{fg};--b:{bg}"><div class="hd"><div class="ic">'
            f'{icono("doc", "#FFFFFF", 20)}</div><div style="min-width:0"><div class="k">{icono(ico_o, fg, 13, 2.4)} '
            f'{esc(origen)}</div><div class="t">{esc(b["titulo"][:1].upper() + b["titulo"][1:])}</div></div></div>'
            f'<div class="s">{esc(datos) or esc(b["archivo"])}</div>'
            f'<div class="s" style="margin-top:6px;color:#334155">{esc(b["que_ver"])}</div>{esperado}</div>')
    clave = b["id"].replace(":", "_").replace(".", "_")
    st.button("Revisar estas bases", key=f"tono_{tono_o}_base_{clave}", type="primary", width="stretch",
              on_click=abrir_base, args=(b["id"],), icon=":material/play_circle:")
    if b.get("url"):
        st.link_button("Ver en el SEACE", b["url"], width="stretch", icon=":material/open_in_new:")


# ------------------------------------------------------------------------------------------
# Página
# ------------------------------------------------------------------------------------------
def pantalla():
    p = E.perfil() or {}
    rubro, nombre = p.get("rubro"), p.get("razon_social") or "tu empresa"
    encabezado("Ejemplos", f"Bases de ejemplo · {rubro or 'todos los rubros'}",
               f"Licitaciones del rubro de {nombre} para probar LiciGuard sin tener un PDF a mano.")
    with st.container(key="ej_hero"):
        a, b = st.columns([2.3, 1], vertical_alignment="center")
        a.markdown(f'<div class="k">RECORRIDO GUIADO · 1 MINUTO</div><div class="t">Mira LiciGuard con '
                   f'{esc(nombre)}</div><div class="s">Abrimos unas bases de {esc(rubro or "tu rubro")} y te '
                   f'explicamos la ficha paso a paso: la recomendación, las 4 preguntas y las pruebas.</div>',
                   unsafe_allow_html=True)
        b.button("Empezar el recorrido", key="demo_hero", type="primary", width="stretch",
                 on_click=demo_de_empresa_activa, icon=":material/play_arrow:")
    st.write("")
    bases = X.bases_de_rubro(rubro) if rubro else X.bases_disponibles()
    reales = [b for b in bases if b["origen"] != "demo"]
    seccion(f"Bases de {rubro or 'todos los rubros'}", f"{len(bases) - len(reales)} ficticias guiadas y "
            f"{len(reales)} reales · se revisan con el perfil de {nombre}", "doc", "azul")
    if not bases:
        vacio("doc", "Aún no hay bases de ejemplo de este rubro",
              "Sube el PDF de una licitación en «Revisar bases» o cambia de empresa en el menú.")
    for i in range(0, len(bases), 3):
        cols = st.columns(3)
        for col, b in zip(cols, bases[i:i + 3]):
            with col.container(border=True):
                _tarjeta_base(b)
    st.write("")
    with st.expander("Para el equipo: cómo sumar bases reales a esta galería", icon=":material/add_circle:"):
        st.markdown(
            "1. En tu computadora ejecuta `python bajar_bases_reales.py --utiles 10 --rubro Mobiliario`.\n"
            "2. Las bases útiles quedan en `data/bases/` y **ya aparecen aquí** en su rubro (solo en tu computadora).\n"
            "3. Para que las vean los jurados en la app publicada: `python bajar_bases_reales.py --a-galeria 4` "
            "las copia a `ejemplos/reales/`; súbelas a GitHub.\n\n"
            "Son documentos públicos del SEACE. Nunca pongas aquí documentos confidenciales.")
