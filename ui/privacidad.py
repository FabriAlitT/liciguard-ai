"""Centro de privacidad (Ley N.° 29733), con el mismo diseño del resto de la app."""
import streamlit as st

from core.privacidad import CONTACTO, NOTA, RESPONSABLE, SECCIONES, VERSION
from ui import estado as E
from ui.tema import TONOS, banda, encabezado, esc, html_md, icono

ss = st.session_state


def _tarjeta(ico, tono, etiqueta, valor, nota):
    fg, bg = TONOS[tono]
    return (f'<div class="lg-feat" style="display:flex;gap:14px;align-items:center">'
            f'<div class="ic" style="background:{bg};margin:0">{icono(ico, fg, 21)}</div><div style="min-width:0">'
            f'<div style="font-size:12px;font-weight:700;color:#7A879C;letter-spacing:.06em">{esc(etiqueta)}</div>'
            f'<div style="font-size:15px;font-weight:800;color:#0B1B3F;overflow-wrap:anywhere">{esc(valor)}</div>'
            f'<div style="font-size:13px;color:#7A879C">{esc(nota)}</div></div></div>')


def pantalla():
    encabezado("Privacidad", "Centro de privacidad", "Qué datos usamos, para qué y cómo puedes controlarlos.")
    banda("LiciGuard · Ley N.° 29733", "Tu información, bajo tu control",
          "Guardamos solo lo necesario para ayudarte a decidir. Puedes descargar o borrar tus datos cuando quieras.",
          ico="escudo")

    a, b, c = st.columns(3)
    a.markdown(_tarjeta("edificio", "azul", "RESPONSABLE", RESPONSABLE, "Tratamiento de datos"), unsafe_allow_html=True)
    b.markdown(_tarjeta("correo", "violeta", "CONTACTO", CONTACTO, "Consultas sobre privacidad"), unsafe_allow_html=True)
    modo = "Invitado: nada se guarda" if ss.invitado else "Con código: datos en Supabase"
    c.markdown(_tarjeta("llave", "verde", "TU SESIÓN", modo, "Puedes borrarlo todo"), unsafe_allow_html=True)
    st.write("")

    izq, der = st.columns([1.6, 1], gap="large")
    with izq:
        for i, (ico, titulo, texto) in enumerate(SECCIONES, 1):
            with st.expander(f"{i:02d} · {titulo}", icon=ico, expanded=i == 1):
                st.markdown(texto)
    with der:
        with st.container(border=True):
            html_md('<div class="lg-sec"><div><div class="tt">Ejerce tus derechos</div>'
                    '<div class="st">Acceso, rectificación, cancelación y oposición</div></div></div>')
            st.button("Descargar o borrar mis datos", icon=":material/manage_accounts:", width="stretch",
                      type="primary", on_click=E.ir_a, args=("Mi empresa",), key="priv_ir_empresa")
            st.link_button("Escribir al equipo", f"mailto:{CONTACTO}?subject=Privacidad%20LiciGuard",
                           icon=":material/mail:", width="stretch")
            if ss.usuario and ss.usuario.get("acepto_privacidad_en"):
                st.caption(f"Aceptaste este aviso el {str(ss.usuario['acepto_privacidad_en'])[:10]}.")
        st.write("")
        html_md(f'<div class="lg-aviso"><b>Importante.</b> {esc(NOTA)}</div>')
    st.caption(f"© {RESPONSABLE} · LiciGuard AI · {VERSION}")
