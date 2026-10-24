"""«Entrar con Google» (st.login de Streamlit, OpenID Connect).

- Se activa solo si .streamlit/secrets.toml tiene la sección [auth] con [auth.google] (ver README, paso «Google»).
- No hace falta cambiar la base de datos: cada cuenta de Google se guarda como un usuario con un código interno
  "g-" + 16 caracteres derivados del correo (la persona nunca lo ve ni lo tiene que escribir).
- La primera vez, la persona acepta el aviso de privacidad antes de crear su cuenta.
"""
import hashlib

import streamlit as st

from core.fechas import ahora_lima
from core.privacidad import AVISO
from ui import estado as E
from ui.tema import esc, html_md, logo

ss = st.session_state


def configurado() -> bool:
    try:
        auth = st.secrets.get("auth", {})
        g = auth.get("google", {})
        return bool(auth.get("redirect_uri") and auth.get("cookie_secret") and g.get("client_id")
                    and g.get("client_secret"))
    except Exception:
        return False


def conectado() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def codigo_de(correo: str) -> str:
    """Código interno estable para una cuenta de Google (cumple el formato de la tabla usuarios)."""
    return "g-" + hashlib.sha256(correo.strip().lower().encode()).hexdigest()[:16]


def correo() -> str:
    return str(st.user.get("email") or "").strip().lower() if conectado() else ""


def nombre() -> str:
    return str(st.user.get("name") or "") if conectado() else ""


def entrar():
    st.login("google")


def salir():
    for k in ("usuario", "abierto", "sha_actual", "empresa_id", "tour_paso"):
        ss[k] = None
    ss.invitado, ss.elegir_empresa = False, False
    from core.db import RepoMemoria
    ss.repo_invitado = RepoMemoria()
    ss.via_google = False
    if conectado():
        st.logout()


def sincronizar() -> bool:
    """Si la persona volvió de Google, la busca o le pide aceptar el aviso. True = puede seguir a la app."""
    if not conectado() or ss.usuario:
        return bool(ss.usuario)
    mail = correo()
    if not mail:
        st.error("Google no nos compartió tu correo. Vuelve a intentarlo con otra cuenta.")
        st.button("Usar otra cuenta", on_click=salir)
        return False
    try:
        u = E.repo().buscar_usuario(codigo_de(mail))
    except Exception as e:
        logo()
        E.error_base_de_datos(e)
        st.button("Volver a la portada", on_click=salir)
        return False
    if u:
        E.entrar_como(u)
        ss.via_google, ss.correo_google = True, mail
        return True
    bienvenida(mail)
    return False


def bienvenida(mail):
    """Primera vez con Google: aceptar el aviso de privacidad y crear la cuenta."""
    quien = nombre() or mail.split("@")[0]
    logo()
    _, centro, _ = st.columns([1, 2, 1])
    with centro.container(border=True):
        html_md(f'<div style="font-size:24px;font-weight:800;color:#0B1B3F;margin-bottom:4px">Hola, {esc(quien)}</div>'
                f'<div style="color:#51607A">Entraste con <b>{esc(mail)}</b>. Antes de empezar, lee y acepta el aviso '
                f'de privacidad: así podremos guardar tu historial.</div>')
        with st.expander("Aviso de privacidad", icon=":material/shield_person:"):
            st.markdown(AVISO)
        acepto = st.checkbox("Leí y acepto el aviso de privacidad", key="g_acepto")
        a, b = st.columns(2)
        if a.button("Continuar", type="primary", width="stretch", disabled=not acepto, icon=":material/arrow_forward:"):
            try:
                u = E.repo().crear_usuario(codigo_de(mail), quien, acepto_privacidad_en=ahora_lima().isoformat())
            except Exception as e:
                E.error_base_de_datos(e)
                return
            E.entrar_como(u)
            ss.via_google, ss.correo_google = True, mail
            st.rerun()
        b.button("Usar otra cuenta", width="stretch", on_click=salir, icon=":material/logout:")
