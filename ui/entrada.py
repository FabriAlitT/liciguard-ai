"""Portada y entrada sin contraseña."""
import secrets
import time

import streamlit as st

from core.fechas import ahora_lima
from core.privacidad import AVISO
from core.usuarios import LimiteIntentos, generar_codigo, normalizar_codigo
from ui import estado as E
from ui import google
from ui.tema import TONOS, anillo, chip, esc, html_md, icono, logo

ss = st.session_state


@st.cache_resource
def limites() -> tuple[LimiteIntentos, LimiteIntentos]:
    """Uno solo para todo el servidor: así recargar la página no reinicia el contador.

    - Por sesión: 5 fallos bloquean (frena a una persona probando códigos).
    - Por IP: 25 fallos. Más permisivo porque varias personas pueden compartir la misma IP (una oficina, una
      cabina o el proxy del servidor); así un intruso no deja bloqueados a todos los demás.
    """
    return LimiteIntentos(max_fallas=5), LimiteIntentos(max_fallas=25)


def _llaves():
    """Quién intenta: su sesión y su IP (si Streamlit la conoce)."""
    ss.setdefault("id_sesion", secrets.token_hex(8))
    try:
        ip = st.context.ip_address
    except Exception:
        ip = None
    return f"sesion:{ss.id_sesion}", (f"ip:{ip}" if ip else None)


PASOS = [("subir", "Sube las bases", "El PDF de la licitación"),
         ("rayo", "Mira la recomendación", "Postular, observar o pasar"),
         ("mano", "Actúa", "Observación en Word y fechas")]


def _vista_previa():
    fg_r, _ = TONOS["rojo"]
    mini = "".join(
        f'<div style="background:{TONOS[t][1]};border-radius:12px;padding:10px 12px">'
        f'<div style="font-size:12px;font-weight:700;color:{TONOS[t][0]}">{q}</div>'
        f'<div style="font-size:17px;font-weight:800;color:#0B1B3F">{v}</div></div>'
        for q, v, t in [("¿Es justa?", "5 alertas", "violeta"), ("¿Puedo?", "4 de 5", "azul"),
                        ("¿Me conviene?", "14,2 %", "ambar"), ("¿Puedo ganar?", "8 previos", "cian")])
    html_md(f"""<div style="background:#FFFFFF;border:1px solid #E2E8F2;border-radius:22px;padding:18px;
      box-shadow:0 24px 60px rgba(30,58,138,.14)">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-size:12px;font-weight:700;color:#2563EB;letter-spacing:.06em">FICHA DE DECISIÓN</div>
        <div style="font-weight:800;color:#0B1B3F">Uniformes institucionales · S/ 812 mil</div></div>
        {chip("Ejemplo", "azul")}</div>
      <div style="display:flex;gap:16px;align-items:center;margin-top:14px">
        {anillo(38, fg_r, "38", "apertura")}
        <div style="flex:1;background:linear-gradient(120deg,#C2410C,#F59E0B);border-radius:14px;padding:14px 16px;color:#fff">
          <div style="font-size:12px;font-weight:700;opacity:.9">RECOMENDACIÓN</div>
          <div style="font-size:18px;font-weight:800;line-height:1.25">Vale la pena, pero primero pide que corrijan las bases</div></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px">{mini}</div>
    </div>""")


_FALLO = object()


def _buscar(R, codigo):
    """Busca el código; si la base de datos falla, avisa en pantalla y devuelve _FALLO (la app no se cae)."""
    try:
        return R.buscar_usuario(codigo)
    except Exception as e:
        E.error_base_de_datos(e)
        return _FALLO


def _demo_invitado():
    E.entrar_como(None, invitado=True)          # muestra las cartas de empresas de ejemplo


def _hero():
    a, b = st.columns([3, 2])
    with a:
        logo()
    with b:
        html_md(f'<div style="display:flex;justify-content:flex-end;margin-top:6px">{chip("Demo FuturX 2026", "azul", "rayo")}</div>')
    st.write("")
    izq, der = st.columns([1.15, 1], gap="large")
    with izq:
        html_md("""<div style="padding-top:28px">
          <div style="font-size:13px;font-weight:800;color:#7C3AED;letter-spacing:.06em">PARA MYPE QUE VENDEN AL ESTADO</div>
          <div style="font-size:52px;font-weight:800;line-height:1.05;letter-spacing:-0.03em;color:#0B1B3F;margin:12px 0 14px">
          ¿Me presento a esta <span style="background:linear-gradient(90deg,#2563EB,#06B6D4);-webkit-background-clip:text;
          background-clip:text;color:transparent">licitación?</span></div>
          <div style="font-size:19px;color:#51607A;line-height:1.5;max-width:520px">Sube las bases y en 1 minuto sabes
          si te conviene postular.</div></div>""")
        st.write("")
        with st.container(key="portada_cta"):
            c1, _ = st.columns([1.1, 1])
            c1.button("Ver la demo", key="demo_portada", type="primary", width="stretch", on_click=_demo_invitado,
                      icon=":material/play_arrow:", help="Con una empresa de ejemplo. No necesitas registrarte.")
            c1.caption("Sin registrarte · nada se guarda")
    with der:
        st.write("")
        _vista_previa()


def pantalla():
    R = E.repo()
    _hero()

    st.write("")
    st.write("")
    html_md('<div class="lg-sec"><div><div class="tt" style="font-size:22px">Accede en segundos</div></div></div>')
    if R.modo == "memoria":
        html_md('<div class="lg-info">Modo local: los datos se borran al reiniciar la app.</div>')
        st.write("")
    if google.configurado():
        with st.container(border=True):
            g1, g2 = st.columns([3, 1.2], vertical_alignment="center")
            g1.markdown('<div class="lg-sec" style="margin:0"><div class="ic" style="background:#EAF1FF">'
                        f'{icono("escudo", "#2563EB", 17)}</div><div><div class="tt">Entra con Google</div>'
                        '<div class="st">Tu historial queda guardado con tu Gmail.</div></div></div>',
                        unsafe_allow_html=True)
            g2.button("Entrar con Google", type="primary", width="stretch", on_click=google.entrar,
                      icon=":material/login:", key="btn_google")
        st.write("")
    c1, c2 = st.columns(2)
    with c1.container(border=True):
        html_md(f'<div class="lg-sec"><div class="ic" style="background:#EAF1FF">{icono("llave", "#2563EB", 17)}</div>'
                '<div><div class="tt">Ya tengo mi código</div></div></div>')
        codigo = st.text_input("Tu código", placeholder="ej. rosa-quispe-k7m4qx", key="in_codigo",
                               label_visibility="collapsed")
        if st.button("Entrar", type="primary", width="stretch"):
            (por_sesion, por_ip), (sesion, ip) = limites(), _llaves()
            espera = max(por_sesion.espera(sesion), por_ip.espera(ip))
            u = None
            if espera:
                st.error(f"Demasiados intentos fallidos. Espera {espera} segundos y vuelve a intentarlo.")
            elif normalizar_codigo(codigo) and (u := _buscar(R, normalizar_codigo(codigo))) is _FALLO:
                pass                                   # ya se mostró el error de la base de datos
            elif u:
                por_sesion.acierto(sesion)
                por_ip.acierto(ip)
                E.entrar_como(u)
                st.rerun()
            else:
                por_sesion.fallo(sesion)
                por_ip.fallo(ip)
                time.sleep(0.4)  # frena los intentos automáticos sin molestar a una persona
                st.error("No encontramos ese código. Revisa que esté bien escrito.")
    with c2.container(border=True):
        html_md(f'<div class="lg-sec"><div class="ic" style="background:#E3F8EF">{icono("personas", "#059669", 17)}</div>'
                '<div><div class="tt">Es mi primera vez</div></div></div>')
        nombre = st.text_input("Tu nombre o el de tu empresa", key="in_nombre", label_visibility="collapsed",
                               placeholder="Tu nombre o el de tu empresa")
        a, b = st.columns([3, 2], vertical_alignment="center")
        acepto = a.checkbox("Acepto el aviso de privacidad", key="in_acepto")
        with b.popover("Leer aviso", width="stretch"):
            st.markdown(AVISO)
        if st.button("Crear mi código", width="stretch"):
            if len(nombre.strip()) < 3:
                st.warning("Escribe al menos 3 letras.")
            elif not acepto:
                st.warning("Para guardar tu historial necesitamos que aceptes el aviso de privacidad.")
            else:
                try:
                    codigo_nuevo = generar_codigo(nombre, R.existe_codigo)
                    E.entrar_como(R.crear_usuario(codigo_nuevo, nombre.strip(),
                                                  acepto_privacidad_en=ahora_lima().isoformat()))
                except Exception as e:
                    E.error_base_de_datos(e)
                else:
                    ss.codigo_recien_creado, ss.pagina = codigo_nuevo, "Inicio"
                    st.rerun()

    st.write("")
    st.write("")
    pasos = "".join(
        f'<div style="flex:1;min-width:180px;display:flex;gap:12px;align-items:center">'
        f'<div style="width:34px;height:34px;border-radius:50%;background:#2563EB;color:#fff;font-weight:800;display:flex;'
        f'align-items:center;justify-content:center;flex:none">{i}</div><div><div style="font-weight:800;color:#0B1B3F">'
        f'{esc(t)}</div><div style="color:#51607A;font-size:14px">{esc(s)}</div></div></div>'
        for i, (_, t, s) in enumerate(PASOS, 1))
    html_md(f'<div class="lg-feat" style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">{pasos}</div>')
    st.write("")
    st.caption("Las alertas son para revisar, no conclusiones legales. No subas documentos confidenciales.")
