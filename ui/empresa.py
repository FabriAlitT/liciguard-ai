"""Mi empresa: perfil, posición en el mercado, "Para crecer" y documentos con vencimiento."""
import altair as alt
import streamlit as st

from core import mercado
from core.seguimiento import dias_hasta, rnp_segun_documentos
from ui import estado as E
from ui.tema import (AZUL, CIAN, VERDE, anillo, chip, encabezado, entero, esc, html_md, icono, kpis, mostrar,
                     progreso, seccion, soles, vacio)

ss = st.session_state
CERTIFICACIONES = ["ISO 9001", "ISO 14001", "ISO 45001", "ISO 37001", "ISO 27001"]
TIPOS_DOC = ["Constancia RNP", "Constancia MYPE", "Contrato de experiencia", "Certificado ISO", "Carta fianza", "Otro"]
EXPEDIENTE = ["Constancia RNP", "Constancia MYPE", "Contrato de experiencia", "Certificado ISO", "Carta fianza"]
OPCIONES_RNP = ["Sí, vigente", "No o venció", "No lo he registrado"]
CAMPOS = ["razon_social", "rubro", "region", "experiencia_soles", "produccion_mensual", "maquinas", "personal",
          "certificaciones"]


def completitud(p) -> float:
    if not p:
        return 0.0
    hechos = sum(bool(p.get(c)) for c in CAMPOS) + (p.get("rnp_vigente") is not None)
    return hechos / (len(CAMPOS) + 1) * 100


def estado_doc(d):
    n = dias_hasta(d.get("vence_el"))
    if n is None:
        return "Sin fecha", "gris", n
    if n < 0:
        return f"Venció hace {-n} días", "rojo", n
    if n <= 30:
        return f"Vence en {n} días", "ambar", n
    return f"Vigente hasta {d['vence_el']}", "verde", n


def formulario_perfil(rubros):
    p = E.perfil() or {}
    with st.form("perfil", border=False):
        c1, c2 = st.columns(2)
        razon = c1.text_input("Razón social", p.get("razon_social") or "")
        opciones = rubros + ["Otro"] if rubros else ["Otro"]
        principal = ss.get("rubro_principal")
        actual = p.get("rubro") if p.get("rubro") in opciones else (principal if principal in opciones else opciones[0])
        rubro = c2.selectbox("Rubro principal", opciones, index=opciones.index(actual))
        region = c1.text_input("Región", p.get("region") or "")
        exp = c2.number_input("Experiencia acreditable en tu rubro (S/)", min_value=0.0,
                              value=float(p.get("experiencia_soles") or 0), step=10000.0,
                              help="Suma de tus contratos con conformidad en bienes iguales o similares.")
        d1, d2, d3 = st.columns(3)
        prod = d1.number_input("Producción mensual (unid.)", min_value=0, value=int(p.get("produccion_mensual") or 0),
                               help="Con esto calculamos si llegas a la cantidad que piden en el plazo de entrega.")
        maq = d2.number_input("Máquinas o equipos", min_value=0, value=int(p.get("maquinas") or 0))
        per = d3.number_input("Personas en tu equipo", min_value=0, value=int(p.get("personal") or 0))
        certs = st.multiselect("Certificaciones vigentes", CERTIFICACIONES, placeholder="Elige tus certificaciones",
                               default=[c for c in (p.get("certificaciones") or []) if c in CERTIFICACIONES])
        m1, m2 = st.columns(2)
        mype = m1.checkbox("Soy MYPE (acreditada)", value=p.get("es_mype", True))
        rnp_actual = {True: "Sí, vigente", False: "No o venció"}.get(p.get("rnp_vigente"), "No lo he registrado")
        rnp = m2.radio("¿Tu inscripción en el RNP está vigente?", OPCIONES_RNP, horizontal=True,
                       index=OPCIONES_RNP.index(rnp_actual),
                       help="Si registras tu «Constancia RNP» con fecha en Tus documentos, usamos esa fecha.")
        segun_docs = rnp_segun_documentos(E.documentos())
        if segun_docs is not None:
            m2.caption(("Según tu Constancia RNP en Tus documentos: **vigente**." if segun_docs else
                        "Según tu Constancia RNP en Tus documentos: **vencida**.") + " Esa fecha es la que usamos.")
        if st.form_submit_button("Guardar perfil", type="primary", icon=":material/save:"):
            ok = E.guardar_perfil({"razon_social": razon, "rubro": rubro, "region": region, "es_mype": mype,
                              "experiencia_soles": exp, "produccion_mensual": prod, "maquinas": maq,
                              "personal": per, "certificaciones": certs,
                              "rnp_vigente": {"Sí, vigente": True, "No o venció": False}.get(rnp)})
            if ok:
                st.success("Perfil guardado. Tus fichas y oportunidades ya usan estos datos.")
                st.rerun()
    return E.perfil() or {}


def _eliminar_empresa():
    p = E.perfil() or {}
    if (ss.get("borrar_empresa_confirma") or "").strip().lower() != (p.get("razon_social") or "").strip().lower():
        ss.aviso_borrar_empresa = "El nombre no coincide. No se borró nada."
        return
    E.borrar_empresa(ss.empresa_id)
    ss.elegir_empresa = True
    ss.aviso_ejemplo = f"Borramos «{p.get('razon_social')}» y todo lo suyo."


def tus_empresas():
    """Eliminar la empresa activa (con sus revisiones, seguimiento y documentos)."""
    p = E.perfil() or {}
    seccion("Esta empresa", "Cada empresa guarda sus revisiones, plazos y documentos por separado", "edificio", "violeta")
    a, b = st.columns([1, 1], gap="large")
    with a:
        st.markdown(f"Estás trabajando con **{p.get('razon_social') or 'esta empresa'}**. Para ver otra o agregar una "
                    "nueva, usa **Cambiar de empresa** en el menú.")
    with b:
        confirma = st.text_input("Para eliminarla, escribe su razón social", key="borrar_empresa_confirma",
                                 placeholder=p.get("razon_social") or "")
        st.button("Eliminar esta empresa y sus datos", key="borrar_empresa", on_click=_eliminar_empresa,
                  icon=":material/delete_forever:", disabled=not confirma)
        if ss.get("aviso_borrar_empresa"):
            st.error(ss.pop("aviso_borrar_empresa"))


def posicion(p, f, rubro):
    seccion("Tu posición en el mercado", f"{rubro or 'Todos los rubros'} · procesos desde 2023", "diana", "cian")
    exp = float(p.get("experiencia_soles") or 0)
    if not exp:
        vacio("trofeo", "Registra tu experiencia", "Con ese dato calculamos a qué tamaño de licitaciones llegas hoy.")
        return
    pct = (mercado.percentil(f, exp) or 0) * 100
    a, b = st.columns([1, 2])
    a.markdown(anillo(pct, CIAN, f"{pct:.0f}%", "alcance"), unsafe_allow_html=True)
    b.markdown(f'<div style="padding-top:12px"><div style="font-weight:800;font-size:17px;color:#0B1B3F">'
               f'Podrías respaldar el {pct:.0f} % de los procesos</div><div style="color:#51607A;font-size:14px">'
               f'Con {soles(exp)} de experiencia, si te piden 1 vez el valor del contrato. El valor típico del '
               f'rubro es {soles(f["valor"].median())}.</div></div>', unsafe_allow_html=True)


def para_crecer(p, f, rubro):
    seccion("Para crecer", "Cuánto mercado ganas con más experiencia", "tendencia", "verde")
    exp = float(p.get("experiencia_soles") or 0)
    factor = st.slider("Supuesto: la experiencia que piden = N veces el valor del proceso", 0.5, 2.0, 1.0, 0.25,
                       key="factor_crecer")
    b = mercado.brechas(f, exp, factor)
    if not len(b):
        st.caption("No hay suficientes datos de valor estimado para este rubro.")
        return
    hoy, siguiente = b.iloc[0], b.iloc[1]
    mostrar(alt.Chart(b).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
        x=alt.X("Meta:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Procesos accesibles (%):Q", scale=alt.Scale(domain=[0, 100]), title="% de procesos"),
        color=alt.condition(alt.datum.Meta == "Hoy", alt.value("#BFD3FB"), alt.value(AZUL)),
        tooltip=["Meta", alt.Tooltip("Experiencia (S/):Q", format=",.0f"), "Procesos accesibles (%)"]), 210)
    html_md(f'<div class="lg-ok">Con S/ 200 mil más de experiencia pasarías del <b>{hoy["Procesos accesibles (%)"]:.0f} %'
            f'</b> al <b>{siguiente["Procesos accesibles (%)"]:.0f} %</b> de las licitaciones de {esc(rubro or "tus rubros")}.'
            f'</div>')
    st.caption("Ideas: suma experiencia con compras pequeñas de tu rubro o asóciate en consorcio "
               "(mira «Socios» en Oportunidades).")


def documentos(docs):
    tipos = {d.get("tipo") for d in docs if estado_doc(d)[1] in ("verde", "ambar", "gris")}
    hechos = sum(t in tipos for t in EXPEDIENTE)
    a, b = st.columns([1, 1.6], gap="large")
    with a:
        seccion("Expediente para postular", f"{hechos} de {len(EXPEDIENTE)} documentos clave", "carpeta", "violeta")
        html_md(progreso(hechos / len(EXPEDIENTE) * 100, "#7C3AED"))
        html_md("".join(
            f'<div class="lg-row"><span style="display:flex;gap:10px;align-items:center;font-weight:600;color:#0B1B3F">'
            f'{icono("check", VERDE if t in tipos else "#CBD6EA", 18)}{t}</span>'
            f'{chip("Listo", "verde") if t in tipos else chip("Falta", "gris")}</div>' for t in EXPEDIENTE))
    with b:
        seccion("Tus documentos", "Te avisamos antes de que venzan", "doc", "azul")
        if not docs:
            vacio("carpeta", "Aún no registras documentos", "Agrega tu constancia RNP y otros documentos con su fecha.")
        for d in docs:
            texto, tono, _ = estado_doc(d)
            c1, c2 = st.columns([5, 1.5])
            c1.markdown(f'<div class="lg-row" style="padding:8px 0"><span style="display:flex;gap:10px;align-items:center">'
                        f'{icono("doc", "#2563EB", 18)}<span><b style="color:#0B1B3F">{esc(d["nombre"])}</b><br>'
                        f'<small style="color:#7A879C">{esc(d.get("tipo") or "")}</small></span></span>'
                        f'{chip(texto, tono)}</div>', unsafe_allow_html=True)
            c2.button("Quitar", key=f"del_{d['id']}", on_click=E.borrar_documento, args=(d["id"],),
                      icon=":material/delete:")
        with st.form("nuevo_doc", clear_on_submit=True, border=False):
            c1, c2, c3 = st.columns([2, 1.5, 1.2])
            nombre = c1.text_input("Documento", placeholder="ej. Constancia RNP de bienes")
            tipo = c2.selectbox("Tipo", TIPOS_DOC)
            vence = c3.date_input("Vence el", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Agregar documento", icon=":material/add:") and nombre.strip():
                E.agregar_documento(nombre.strip(), tipo, vence.isoformat() if vence else None)
                st.rerun()


def _json(datos) -> bytes:
    import json
    return json.dumps(datos, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def privacidad():
    seccion("Tus datos y privacidad", "Ley N.° 29733: puedes ver, descargar y borrar todo lo que guardamos",
            "escudo", "gris")
    a, b = st.columns([1, 1], gap="large")
    with a:
        st.button("Ver el centro de privacidad", icon=":material/shield_person:", on_click=E.ir_a,
                  args=("Privacidad",), key="emp_ir_priv")
        if ss.usuario and ss.usuario.get("acepto_privacidad_en"):
            st.caption(f"Aceptaste el aviso el {str(ss.usuario['acepto_privacidad_en'])[:10]}.")
        st.download_button("Descargar mis datos (JSON)", _json(E.exportar_mis_datos()), "mis_datos_liciguard.json",
                           "application/json", icon=":material/download:")
    with b:
        if ss.usuario:
            st.markdown("**Borrar mi cuenta.** Se eliminan para siempre tu perfil, tus licitaciones, tu seguimiento "
                        "y tus documentos. No se puede deshacer.")
            via_google = ss.get("via_google")
            esperado = ss.get("correo_google", "") if via_google else ss.usuario["codigo"]
            confirma = st.text_input("Para confirmar, escribe tu correo de Google" if via_google else
                                     "Para confirmar, escribe tu código", key="borrar_confirma", placeholder=esperado)
            if st.button("Borrar mi cuenta y mis datos", icon=":material/delete_forever:", key="borrar_cuenta"):
                if confirma.strip().lower() != esperado:
                    st.error(("El correo" if via_google else "El código") + " no coincide. No se borró nada.")
                else:
                    try:
                        E.borrar_mi_cuenta()
                        ss.cuenta_borrada = True
                        if via_google:
                            from ui import google
                            google.salir()      # cierra también la sesión de Google en la app
                        st.rerun()
                    except Exception as e:
                        st.error(f"No pudimos borrar la cuenta ahora (revisa tu internet o Supabase): "
                                 f"{type(e).__name__}. No se borró nada; inténtalo de nuevo.")
        else:
            st.markdown("**Modo invitado:** nada se guarda en la base de datos; al cerrar la pestaña se borra todo.")
            if st.button("Borrar ahora lo de esta sesión", icon=":material/delete:", key="borrar_invitado"):
                E.borrar_mi_cuenta()
                ss.cuenta_borrada = True
                st.rerun()


def pantalla():
    encabezado("Mi empresa", (E.perfil() or {}).get("razon_social") or "Perfil de tu empresa",
               "Se llena una vez. Lo usamos en cada ficha para responder “¿Puedo?” y para medir tu mercado.")
    if getattr(E.repo(), "falta_columna_rnp", False):
        html_md('<div class="lg-aviso">Para guardar si tu RNP está vigente ejecuta '
                '<code>supabase/03_rnp_vigente.sql</code> en Supabase (lo demás sí se guardó).</div>')
    if ss.aviso_tablas:
        html_md('<div class="lg-aviso">Para guardar documentos en Supabase ejecuta '
                '<code>supabase/02_seguimiento_y_documentos.sql</code>.</div>')
    d = E.mercado_df()
    rubros = mercado.rubros(d)
    if len(d) and "rubro_principal" not in ss:
        ss.rubro_principal = d["rubro"].value_counts().index[0]  # el rubro con más datos
    p = E.perfil() or {}
    docs = sorted(E.documentos(), key=lambda x: str(x.get("vence_el") or "9999"))
    rubro = p.get("rubro") if p.get("rubro") in rubros else None
    f = mercado.filtrar(d, rubro, desde=2023) if len(d) else d
    exp = float(p.get("experiencia_soles") or 0)
    alcance = (mercado.percentil(f, exp) or 0) * 100 if exp and len(f) else None
    por_vencer = sum(estado_doc(x)[1] in ("ambar", "rojo") for x in docs)
    kpis([("Perfil completo", f"{completitud(p):.0f} %", "de los datos clave", "check", "verde"),
          ("Experiencia acreditable", soles(exp) if exp else "—", "en tu rubro", "trofeo", "azul"),
          ("Alcance de mercado", f"{alcance:.0f} %" if alcance is not None else "—", "procesos que podrías respaldar",
           "diana", "cian"),
          ("Documentos registrados", entero(len(docs)), "en tu expediente", "carpeta", "violeta"),
          ("Por vencer o vencidos", entero(por_vencer), "renuévalos a tiempo", "alerta",
           "rojo" if por_vencer else "gris")], columnas=5)

    izq, der = st.columns([1.15, 1], gap="medium")
    with izq.container(border=True):
        seccion("Datos de tu empresa", "Usados para comparar requisitos", "edificio", "azul")
        html_md(progreso(completitud(p), AZUL))
        st.write("")
        p = formulario_perfil(rubros)
    with der:
        if len(d):
            with st.container(border=True):
                posicion(p, f, rubro)
            with st.container(border=True):
                para_crecer(p, f, rubro)
        else:
            vacio("base", "Carga los datos abiertos", "Ejecuta el cuaderno 02 para ver tu posición en el mercado.")
    st.write("")
    with st.container(border=True):
        documentos(docs)
    st.write("")
    with st.container(border=True):
        tus_empresas()
    st.write("")
    with st.container(border=True):
        privacidad()
