"""Asistente flotante: siempre a mano (botón abajo a la derecha), con el contexto de tu empresa y tu pantalla."""
import streamlit as st

from core import asistente as A
from ui import estado as E
from ui.tema import esc, html_md, icono

ss = st.session_state
MAX_TURNOS = 12


def _abrir():
    ss.chat_abierto = not ss.get("chat_abierto", False)


def _chat() -> list[dict]:
    return ss.setdefault("chats", {}).setdefault(ss.get("empresa_id") or "-", [])


def _resultado_abierto():
    """La ficha que la persona tiene abierta (o la última que abrió), con SUS números actuales."""
    sha = ss.get("sha_actual")
    if sha and sha in ss.get("pdfs", {}):
        try:
            from ui.revisar import calcular
            return calcular(sha)
        except Exception:
            return None
    if ss.get("abierto"):                       # ficha guardada abierta sin el PDF
        fila = next((f for f in E.analisis() if f.get("sha256") == ss.abierto), None)
        return (fila or {}).get("resultado")
    return None


def _viendo(res) -> str:
    """Qué parte de la ficha está mirando (para que la IA sepa a qué se refiere «esto»)."""
    if not res or ss.get("pagina") != "Revisar bases":
        return ""
    sha = ss.get("sha_actual") or ss.get("abierto")
    detalle = ss.get(f"det_{sha}")
    return f"la Ficha de decisión, sección «{detalle.split(' · ', 1)[-1]}»" if detalle else "la Ficha de decisión"


def responder(pregunta: str) -> tuple[str, str]:
    """(respuesta, quién respondió). Aplica los guardrails antes y después de la IA."""
    empresa = E.perfil()
    ok, negativa = A.revisar_pregunta(pregunta, (empresa or {}).get("razon_social") or "")
    if not ok:
        return negativa, "LiciGuard (fuera de tema)"
    pagina = ss.get("pagina", "Inicio")
    docs, segs, res = E.documentos(), E.seguimientos(), _resultado_abierto()
    if ss.router.disponible:
        normas = E.normativa().buscar(pregunta, k=2) if E.normativa().disponible else []
        extra = "\n".join(f"[Norma: {n['fuente']} · {n['articulo']}] {n['texto'][:900]}" for n in normas)
        historia = _chat()[-7:-1]                # la pregunta actual ya está al final del chat
        if historia:
            extra += "\nConversación reciente:\n" + "\n".join(f"{m['rol']}: {m['texto'][:700]}" for m in historia)
        contexto = A.armar_contexto(pagina, empresa, docs, segs, res, extra, viendo=_viendo(res))
        out = ss.router.completar(pregunta, contexto, tarea="asistente_chat", max_tokens=1200,
                                  sistema=A.SISTEMA_ASISTENTE)
        texto = A.revisar_respuesta(out.get("texto"))
        if texto:
            return texto, f"IA · {out['proveedor']}"
    return A.responder_sin_ia(pregunta, pagina, empresa, docs, res), "LiciGuard (reglas, sin IA)"


def _enviar(pregunta=None):
    pregunta = (pregunta or ss.get("chat_in") or "").strip()
    ss.chat_in = ""
    if not pregunta:
        return
    chat = _chat()
    chat.append({"rol": "usuario", "texto": pregunta})
    texto, quien = responder(pregunta)
    chat.append({"rol": "asistente", "texto": texto, "quien": quien})
    del chat[:-2 * MAX_TURNOS]


def _limpiar():
    _chat().clear()


def _expandir():
    ss.chat_grande = not ss.get("chat_grande", False)


def flotante():
    """Botón flotante + panel del asistente (normal o expandido). No se muestra durante el recorrido guiado."""
    if ss.get("tour_paso") is not None:
        return
    abierto = ss.get("chat_abierto", False)
    with st.container(key="asistente_boton"):
        st.button("Cerrar asistente" if abierto else "Pregúntale a LiciGuard", key="asistente_toggle",
                  on_click=_abrir, icon=":material/close:" if abierto else ":material/forum:")
    if not abierto:
        return
    grande = ss.get("chat_grande", False)
    empresa = (E.perfil() or {}).get("razon_social") or "tu empresa"
    res = _resultado_abierto()
    objeto = ((res or {}).get("datos") or {}).get("objeto")
    with st.container(key="asistente_panel_xl" if grande else "asistente_panel"):
        h, b1, b2 = st.columns([16, 1, 1] if grande else [6, 1, 1], vertical_alignment="center", gap="small")
        h.markdown(f'<div class="lg-chat-hd"><div class="ic">{icono("ia", "#FFFFFF", 18)}</div><div style="min-width:0">'
                   f'<div class="t">Asistente LiciGuard</div><div class="s">{esc(empresa)}</div></div></div>',
                   unsafe_allow_html=True)
        b1.button("", key="asis_expandir", on_click=_expandir, width="stretch",
                  icon=":material/close_fullscreen:" if grande else ":material/open_in_full:",
                  help="Achicar" if grande else "Expandir")
        chat = _chat()
        b2.button("", key="asis_limpiar", on_click=_limpiar, width="stretch", icon=":material/delete_sweep:",
                  disabled=not chat, help="Borrar conversación")
        html_md(f'<div class="lg-chat-ctx">{icono("doc", "#5B21B6", 14)}<span>'
                + (f"Analizando: <b>{esc(objeto[:70].capitalize())}</b>" if objeto
                   else "Sin ficha abierta: abre una licitación para que la analice")
                + '</span></div>')
        with st.container(height=560 if grande else 330, key="asistente_mensajes"):
            if not chat:
                st.caption("Pregúntame sobre lo que estás viendo. Por ejemplo:")
                for i, idea in enumerate(A.sugerencias(ss.get("pagina", "Inicio"), res is not None)):
                    st.button(idea, key=f"asis_idea_{i}", on_click=_enviar, args=(idea,), width="stretch")
            for m in chat:
                with st.chat_message("user" if m["rol"] == "usuario" else "assistant",
                                     avatar=":material/person:" if m["rol"] == "usuario" else ":material/shield:"):
                    st.markdown(m["texto"])
                    if m.get("quien"):
                        st.caption(m["quien"])
        with st.form("asistente_form", clear_on_submit=False, border=False):
            a, b = st.columns([5, 1.3], vertical_alignment="bottom")
            a.text_input("Tu pregunta", key="chat_in", placeholder="Escribe tu pregunta…", label_visibility="collapsed")
            b.form_submit_button("Enviar", type="primary", on_click=_enviar, width="stretch")
        st.caption("Orientación, no asesoría legal. La decisión es tuya.")
