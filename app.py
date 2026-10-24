"""LiciGuard AI — ¿Me presento a esta licitación?

Módulos:
  Portada y entrada sin contraseña · Inicio (panel) · Ejemplos (demo en 1 clic) · Revisar bases (Ficha de decisión, Pruebas en el PDF,
  Actuar, Pregúntale a tus bases) · Oportunidades · Seguimiento · Mi empresa

Ejecutar:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="LiciGuard · Inteligencia para licitar", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="auto")

from ui import ejemplos, empresa, entrada, inicio, oportunidades, privacidad, revisar, seguimiento  # noqa: E402
from ui import estado as E  # noqa: E402
from ui import google  # noqa: E402
from ui import guia  # noqa: E402
from ui import seleccion  # noqa: E402
from ui import asistente  # noqa: E402
from core.ia import en_pausa, reactivar_todos  # noqa: E402
from ui import tema  # noqa: E402
from ui.tema import AMBAR, GRIS, VERDE, aplicar, css_menu, esc, html_md, logo  # noqa: E402

aplicar()
E.iniciar()
ss = st.session_state

PAGINAS = {
    "Inicio": inicio.pantalla,
    "Ejemplos": ejemplos.pantalla,
    "Revisar bases": revisar.pantalla,
    "Oportunidades": oportunidades.pantalla,
    "Seguimiento": seguimiento.pantalla,
    "Mi empresa": empresa.pantalla,
    "Privacidad": privacidad.pantalla,
}
ICONOS = {"Inicio": ":material/space_dashboard:", "Ejemplos": ":material/science:", "Revisar bases": ":material/fact_check:",
          "Oportunidades": ":material/travel_explore:", "Seguimiento": ":material/timeline:",
          "Mi empresa": ":material/apartment:", "Privacidad": ":material/shield_person:"}


def _estado(ok, texto, aviso=False):
    color = VERDE if ok else (AMBAR if aviso else GRIS)
    return f'<div class="lg-status"><span class="lg-dot" style="background:{color}"></span>{esc(texto)}</div>'


def _nombre_ia(nombre):
    resta = en_pausa(nombre)
    return f"{nombre} (en pausa {max(1, round(resta / 60))} min)" if resta else nombre


def _empresa_activa():
    p = E.perfil() or {}
    html_md(f'<div class="lg-activa"><div class="k">EMPRESA ACTIVA</div><div class="t">'
            f'{esc(p.get("razon_social") or "Sin nombre")}</div><div class="s">{esc(p.get("rubro") or "Sin rubro")}'
            f'{" · " + esc(p.get("region")) if p.get("region") else ""}</div></div>')
    st.button("Cambiar de empresa", key="cambiar_empresa", on_click=_cambiar, width="stretch",
              icon=":material/swap_horiz:", help="Vuelve a las cartas para elegir otra empresa (o agregar una).")


def _cambiar():
    E.cambiar_de_empresa()
    ss.elegir_empresa = True


def barra_lateral():
    with st.sidebar:
        logo()
        st.write("")
        if ss.usuario:
            nombre = ss.usuario["nombre"]
            iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "LG"
            html_md(f'<div class="lg-user"><div class="av">{esc(iniciales)}</div><div style="min-width:0">'
                    f'<div style="font-weight:700;color:#0B1B3F;font-size:14px">{esc(nombre)}</div>'
                    f'<div style="font-size:12px;color:#7A879C;overflow-wrap:anywhere">'
                    f'{"Google · " + esc(ss.get("correo_google", "")) if ss.get("via_google") else "Código: " + esc(ss.usuario["codigo"])}'
                    f'</div></div></div>')
        else:
            html_md('<div class="lg-user"><div class="av">IN</div><div><div style="font-weight:700;color:#0B1B3F;'
                    'font-size:14px">Invitado</div><div style="font-size:12px;color:#7A879C">Sin historial</div></div></div>')
        _empresa_activa()
        st.write("")
        st.caption("MENÚ")
        st.radio("Menú", list(PAGINAS), key="pagina", label_visibility="collapsed",
                 format_func=lambda p: f"{ICONOS[p]} {p}")
        html_md(css_menu(list(PAGINAS)))
        st.caption("AYUDA")
        st.button("Recorrido guiado (1 min)", key="tono_violeta_tour_menu", on_click=guia.tour_desde_menu,
                  width="stretch", icon=":material/tour:",
                  help="Te mostramos paso a paso cómo leer una ficha de decisión.")
        guia.glosario()
        if ss.get("guias_cerradas"):
            st.button("Volver a mostrar las guías", key="guias_de_nuevo", on_click=guia.mostrar_guias_de_nuevo,
                      width="stretch", icon=":material/help:")
        st.divider()
        with st.expander("Estado del sistema", icon=":material/settings:"):
            R, n, d = E.repo(), E.normativa(), E.mercado_df()
            provs = ss.router.proveedores
            html_md(
                _estado(R.modo == "supabase", "Base de datos: " + ("Supabase" if R.modo == "supabase" else "modo local"),
                        aviso=True)
                + _estado(n.disponible, f"Normativa: {len(n.articulos)} artículos" if n.disponible else "Normativa: sin cargar")
                + _estado(bool(len(d)), f"Datos abiertos: {len(d):,} procesos".replace(",", " ") if len(d)
                          else "Datos abiertos: sin cargar")
                + _estado(bool(provs), ("IA: " + " → ".join(_nombre_ia(p["nombre"]) for p in provs)) if provs
                          else "IA: modo sin IA (reglas)"))
            if any(en_pausa(p["nombre"]) for p in provs):
                st.button("Reactivar IA en pausa", key="reactivar_ia", on_click=reactivar_todos, width="stretch",
                          icon=":material/restart_alt:",
                          help="Un proveedor que falla varias veces se salta unos minutos. Esto lo vuelve a probar ya.")
            from core.config import avisos_configuracion
            for aviso in avisos_configuracion():
                st.warning(aviso)
            if not provs:
                st.caption("No encontramos claves de IA. Revisa que el archivo se llame exactamente "
                           "`.streamlit/secrets.toml` (no `.example` ni `.txt`) y reinicia la app.")
            elif st.button("Probar ahora", width="stretch", key="probar_ia"):
                with st.spinner("Probando cada proveedor…"):
                    ss.diag_ia = ss.router.diagnosticar()
            for r in ss.get("diag_ia") or []:
                (st.success if r["ok"] else st.error)(f"**{r['proveedor']}** ({r['modelo']}): {r['mensaje']}")
                if r.get("tecnico"):
                    st.caption(f"Detalle técnico: {r['tecnico']}")
            if provs:
                st.toggle(f"Simular caída de {provs[0]['nombre']}", key="simular",
                          help="Para la demo: muestra cómo responde el respaldo automático.")
                ss.router.simular_caida = {provs[0]["nombre"]} if ss.get("simular") else set()
        st.divider()
        if st.button("Cerrar sesión", icon=":material/logout:", width="stretch"):
            google.salir()          # si entró con Google, también cierra su sesión de Google en la app
            st.rerun()


def app_principal():
    barra_lateral()
    ss.aviso_lectura = None
    if ss.get("aviso_ejemplo"):
        st.toast(ss.pop("aviso_ejemplo"), icon=":material/check_circle:")
    aviso = st.empty()   # se llena al final si alguna lectura de la base falló en esta pantalla
    pagina = ss.pagina
    tema.DESPUES_DEL_ENCABEZADO[:] = [lambda: guia.franja(pagina)]
    PAGINAS[pagina]()
    tema.DESPUES_DEL_ENCABEZADO.clear()
    guia.siguiente(pagina)
    asistente.flotante()
    if ss.aviso_lectura:
        with aviso.container():
            st.warning("No pudimos leer tus datos de la base de datos (revisa tu internet o Supabase). Algunas "
                       "secciones pueden verse vacías; vuelve a intentarlo en un rato.", icon=":material/cloud_off:")
            st.caption(f"Detalle técnico: {ss.aviso_lectura}")


if google.conectado() and not ss.usuario and not google.sincronizar():
    st.stop()               # primera vez con Google: se muestra la bienvenida (aceptar el aviso de privacidad)
if ss.usuario or ss.invitado:
    if not ss.empresa_id and not ss.get("elegir_empresa"):
        lista = E.empresas()
        if len(lista) == 1:                      # una sola empresa: entra directo, como siempre
            E.elegir_empresa(lista[0]["id"])
    if not ss.empresa_id or not E.empresa_activa():
        ss.empresa_id = None
        seleccion.pantalla()                     # cartas: tus empresas o las de ejemplo (demo)
    else:
        app_principal()
else:
    if ss.pop("cuenta_borrada", False):
        st.success("Listo: borramos tu cuenta y todos tus datos.", icon=":material/check_circle:")
    entrada.pantalla()
