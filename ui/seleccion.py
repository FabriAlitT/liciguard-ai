"""Elegir con qué empresa trabajar: tus empresas, agregar una nueva o probar con una empresa de ejemplo.

- Invitado (demo): ve las 4 empresas de ejemplo en cartas; al elegir una, todo se filtra por su rubro y se abre
  la ficha de sus bases con el recorrido guiado.
- Con cuenta: ve sus empresas (p. ej. un consultor con varios clientes); cada una con su historial aparte.
"""
import streamlit as st

from core import ejemplos as X
from core.db import CAMPOS_EMPRESA
from ui import estado as E
from ui.tema import TONOS, chip, esc, html_md, icono, logo, soles

ss = st.session_state
RUBROS = ["Uniformes y textiles", "Limpieza", "Mobiliario", "Útiles de oficina", "Otro"]
TONO_RUBRO = {"Uniformes y textiles": "violeta", "Limpieza": "cian", "Mobiliario": "ambar",
              "Útiles de oficina": "verde"}
ICONO_RUBRO = {"Uniformes y textiles": "personas", "Limpieza": "check", "Mobiliario": "edificio",
               "Útiles de oficina": "libro"}


# ------------------------------------------------------------------------------------------
# Acciones
# ------------------------------------------------------------------------------------------
def entrar_a(empresa_id):
    E.elegir_empresa(empresa_id)
    ss.elegir_empresa = False
    ss.pagina = "Inicio"


def usar_ejemplo(id_ejemplo: str):
    """Crea (o reutiliza) la empresa de ejemplo, la activa y abre la demo guiada de su rubro."""
    emp = X.empresa(id_ejemplo)
    existente = next((e for e in E.empresas() if e.get("razon_social") == emp["perfil"]["razon_social"]), None)
    eid = existente["id"] if existente else E.crear_empresa(dict(emp["perfil"]))
    if not eid:
        return
    E.elegir_empresa(eid)
    ss.elegir_empresa = False
    ya = {d.get("nombre") for d in E.documentos()}
    for d in X.documentos_de(emp):
        if d["nombre"] not in ya:
            E.agregar_documento(d["nombre"], d["tipo"], d["vence_el"])
    from ui.ejemplos import demo_de_empresa_activa
    demo_de_empresa_activa()


def _crear_propia():
    nombre = (ss.get("nueva_razon") or "").strip()
    if len(nombre) < 3:
        ss.aviso_nueva = "Escribe el nombre de tu empresa (al menos 3 letras)."
        return
    datos = {k: None for k in CAMPOS_EMPRESA} | {"razon_social": nombre, "rubro": ss.get("nueva_rubro"),
                                                 "es_mype": True, "certificaciones": []}
    eid = E.crear_empresa(datos)
    if eid:
        entrar_a(eid)
        ss.pagina = "Mi empresa"               # a completar sus datos
        ss.aviso_ejemplo = f"Creamos «{nombre}». Completa sus datos para que las fichas sean exactas."


# ------------------------------------------------------------------------------------------
# Cartas
# ------------------------------------------------------------------------------------------
def _carta(nombre, rubro, linea, chips_html, tono, ico):
    fg, bg = TONOS[tono]
    html_md(f'<div class="lg-ej t-{tono}" style="--c:{fg};--b:{bg}"><div class="hd"><div class="ic">'
            f'{icono(ico, "#FFFFFF", 20)}</div><div style="min-width:0"><div class="k">{esc(rubro or "Sin rubro")}</div>'
            f'<div class="t">{esc(nombre)}</div></div></div><div class="s">{esc(linea)}</div>'
            f'<div class="ch" style="margin-top:8px">{chips_html}</div></div>')


def _chips(p):
    return "".join([
        chip(f"Exp. {soles(p.get('experiencia_soles'))}", "gris", "trofeo") if p.get("experiencia_soles") else "",
        chip("MYPE", "verde") if p.get("es_mype") else "",
        chip("RNP vigente", "azul", "check") if p.get("rnp_vigente") else ""])


def _tus_empresas(lista):
    html_md('<div class="lg-sec"><div><div class="tt" style="font-size:20px">Tus empresas</div><div class="st">'
            'Cada una con sus revisiones, plazos y documentos por separado.</div></div></div>')
    cols = st.columns(3)
    for i, e in enumerate(lista):
        tono = TONO_RUBRO.get(e.get("rubro"), "azul")
        with cols[i % 3].container(border=True):
            _carta(e.get("razon_social") or "Mi empresa", e.get("rubro"), e.get("region") or "Región sin registrar",
                   _chips(e), tono, ICONO_RUBRO.get(e.get("rubro"), "edificio"))
            st.button("Entrar con esta empresa", key=f"tono_{tono}_entrar_{e['id']}", type="primary",
                      width="stretch", on_click=entrar_a, args=(e["id"],), icon=":material/login:")
    with cols[len(lista) % 3].container(border=True):
        _formulario_nueva()


def _formulario_nueva():
    html_md(f'<div class="lg-ej t-azul" style="--c:#2563EB;--b:#EAF1FF"><div class="hd"><div class="ic">'
            f'{icono("edificio", "#FFFFFF", 20)}</div><div><div class="k">Nueva</div>'
            f'<div class="t">Agregar mi empresa</div></div></div></div>')
    st.text_input("Razón social", key="nueva_razon", placeholder="ej. Textiles del Norte SAC")
    st.selectbox("Rubro", RUBROS, key="nueva_rubro")
    st.button("Crear y completar sus datos", key="tono_azul_crear_empresa", type="primary", width="stretch",
              on_click=_crear_propia, icon=":material/add_business:")
    if ss.get("aviso_nueva"):
        st.warning(ss.pop("aviso_nueva"))


def _ejemplos(titulo, sub, texto_boton):
    html_md(f'<div class="lg-sec"><div><div class="tt" style="font-size:20px">{esc(titulo)}</div>'
            f'<div class="st">{esc(sub)}</div></div></div>')
    cols = st.columns(len(X.EMPRESAS))
    for col, emp in zip(cols, X.EMPRESAS):
        p = emp["perfil"]
        n_bases = len([b for b in X.bases_disponibles() if b.get("rubro") == p["rubro"]])
        with col.container(border=True):
            _carta(p["razon_social"], p["rubro"], f"{emp['ciudad']} · {emp['lema']}",
                   _chips(p) + chip(f"{n_bases} bases de ejemplo", emp["tono"], "doc"), emp["tono"], emp["ico"])
            st.button(texto_boton, key=f"tono_{emp['tono']}_demo_{emp['id']}", type="primary", width="stretch",
                      on_click=usar_ejemplo, args=(emp["id"],), icon=":material/play_arrow:")


def pantalla():
    a, b = st.columns([3, 1])
    with a:
        logo()
    if ss.invitado:
        b.button("Volver a la portada", key="sel_salir", width="stretch", icon=":material/arrow_back:",
                 on_click=lambda: ss.update(invitado=False))
    st.write("")
    lista = E.empresas()
    if ss.invitado and not lista:
        html_md('<div class="lg-head"><div><div class="crumb">Demo guiada</div><div class="tt">Elige una empresa para '
                'empezar</div><div class="st">Empresas ficticias. Te guiamos paso a paso.</div></div></div>')
        _ejemplos("Empresas de ejemplo", "", "Probar con esta")
        st.write("")
        with st.expander("Prefiero empezar con mi propia empresa", icon=":material/add_business:"):
            _formulario_nueva()
        return
    quien = (ss.usuario or {}).get("nombre") or "invitado"
    html_md(f'<div class="lg-head"><div><div class="crumb">Hola, {esc(quien)}</div><div class="tt">¿Con qué empresa '
            f'trabajamos hoy?</div><div class="st">Elige una: verás solo sus licitaciones, su mercado y sus documentos.'
            f'</div></div></div>')
    if lista:
        _tus_empresas(lista)
    else:
        with st.container(border=True):
            _formulario_nueva()
    if ss.get("aviso_empresa"):
        st.caption(ss.pop("aviso_empresa"))
    st.write("")
    with st.expander("¿Solo quieres probar? Usa una empresa de ejemplo", icon=":material/science:",
                     expanded=not lista):
        _ejemplos("Empresas de ejemplo", "Se agregan a tu lista; puedes borrarlas cuando quieras desde Mi empresa",
                  "Probar con esta empresa")
