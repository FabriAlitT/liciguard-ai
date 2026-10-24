"""Ayuda para recorrer la app: guía de cada página, siguiente paso, glosario y recorrido guiado de la ficha."""
import json

import streamlit as st
import streamlit.components.v1 as components

from core.ayuda import GLOSARIO, GUIAS, TOUR_FICHA
from ui import estado as E
from ui.tema import esc, html_md, icono

ss = st.session_state


# ------------------------------------------------------------------------------------------
# Guía de la página («¿Para qué sirve esta página?»), se cierra con la X
# ------------------------------------------------------------------------------------------
def _cerrar(pagina):
    ss.setdefault("guias_cerradas", set()).add(pagina)


def mostrar_guias_de_nuevo():
    ss.guias_cerradas = set()


def franja(pagina: str):
    """Una sola línea: qué se hace en esta página. Se cierra con la X."""
    if pagina not in GUIAS or pagina in ss.get("guias_cerradas", set()):
        return
    if pagina == "Revisar bases" and ss.get("sha_actual") in ss.get("pdfs", {}):
        return                                   # con la ficha abierta ya se entiende; menos ruido
    titulo, frase, _ = GUIAS[pagina]
    clave = pagina.lower().replace(" ", "_")
    with st.container(key=f"guia_{clave}"):
        a, b = st.columns([14, 1], vertical_alignment="center")
        a.markdown(f'<div class="lg-guia"><div class="ic">{icono("ia", "#FFFFFF", 16)}</div><div style="flex:1;min-width:0">'
                   f'<span class="t">{esc(titulo)}</span><span class="s"> · {esc(frase)}</span></div></div>',
                   unsafe_allow_html=True)
        b.button("", key=f"guia_x_{clave}", icon=":material/close:", on_click=_cerrar, args=(pagina,),
                 help="Ocultar")


# ------------------------------------------------------------------------------------------
# Siguiente paso sugerido (al final de cada página)
# ------------------------------------------------------------------------------------------
def _sugerencia(pagina):
    perfil, filas = E.perfil(), E.analisis()
    ficha_abierta = ss.get("sha_actual") in ss.get("pdfs", {})
    if pagina == "Inicio":
        if not perfil:
            return "Completa tu perfil para saber si cumples los requisitos.", "Mi empresa", ":material/apartment:"
        if not filas:
            return "Revisa tus primeras bases (o prueba con un ejemplo).", "Revisar bases", ":material/fact_check:"
        return "Busca nuevas licitaciones de tu rubro.", "Oportunidades", ":material/travel_explore:"
    if pagina == "Ejemplos":
        return "¿Tienes el PDF de una licitación real? Súbelo y revísalo.", "Revisar bases", ":material/upload_file:"
    if pagina == "Revisar bases":
        if ficha_abierta:
            return "Guarda las fechas de esta licitación para que no se te pasen.", "Seguimiento", ":material/timeline:"
        return None                       # la página ya ofrece ejemplos: no repetirlo abajo
    if pagina == "Oportunidades":
        return "Encontraste una buena? Baja sus bases del SEACE y revísalas.", "Revisar bases", ":material/fact_check:"
    if pagina == "Seguimiento":
        return "Mantén tus documentos al día para postular sin sustos.", "Mi empresa", ":material/apartment:"
    if pagina == "Mi empresa":
        return "Con tu perfil listo, revisa unas bases.", "Revisar bases", ":material/fact_check:"
    if pagina == "Privacidad":
        return "Vuelve a tu panel.", "Inicio", ":material/space_dashboard:"
    return None


def siguiente(pagina: str):
    s = _sugerencia(pagina)
    if not s:
        return
    texto, destino, ico = s
    with st.container(key="siguiente_paso"):
        a, b = st.columns([3, 1.2], vertical_alignment="center")
        a.markdown(f'<div style="font-size:12px;font-weight:800;color:#059669;letter-spacing:.06em">SIGUIENTE PASO</div>'
                   f'<div style="font-weight:700;color:#0B1B3F">{esc(texto)}</div>', unsafe_allow_html=True)
        b.button(f"Ir a {destino}", key=f"tono_verde_sig_{destino.replace(' ', '_')}", type="primary",
                 width="stretch", icon=ico, on_click=E.ir_a, args=(destino,))


# ------------------------------------------------------------------------------------------
# Glosario (barra lateral)
# ------------------------------------------------------------------------------------------
def glosario():
    with st.popover("Glosario: ¿qué significa…?", icon=":material/menu_book:", width="stretch"):
        st.markdown("**Palabras que verás en las bases**")
        for termino, definicion in GLOSARIO.items():
            st.markdown(f"**{termino[0].upper() + termino[1:]}** · {definicion}")


# ------------------------------------------------------------------------------------------
# Recorrido guiado de la ficha
# ------------------------------------------------------------------------------------------
def iniciar_tour():
    ss.tour_paso = 0


def _mover(delta):
    ss.tour_paso = (ss.get("tour_paso") or 0) + delta


def terminar_tour():
    ss.tour_paso = None
    ss.tour_visto = True


def tour_desde_menu():
    """Botón del menú: si hay una ficha abierta, la recorre; si no, abre unas bases de ejemplo de tu rubro."""
    from ui.ejemplos import demo_de_empresa_activa
    if ss.get("sha_actual") in ss.get("pdfs", {}):
        iniciar_tour()
        E.ir_a("Revisar bases")
    else:
        demo_de_empresa_activa()


def tour():
    """Se llama después de dibujar la ficha. Resalta una parte y muestra la burbuja con Siguiente / Saltar."""
    paso = ss.get("tour_paso")
    if paso is None:
        return
    paso = max(0, min(paso, len(TOUR_FICHA) - 1))
    selector, titulo, texto = TOUR_FICHA[paso]
    html_md(f"<style>{selector} {{ position: relative; z-index: 100000; border-radius: 16px; "
            f"box-shadow: 0 0 0 4px #A78BFA, 0 0 0 9999px rgba(11,27,63,.55) !important; "
            f"background: #FFFFFF; transition: box-shadow .25s ease; }}</style>")
    with st.container(key="tour_burbuja"):
        puntos = "".join(f'<i class="{"on" if i <= paso else ""}"></i>' for i in range(len(TOUR_FICHA)))
        st.markdown(f'<div class="k">RECORRIDO GUIADO · {paso + 1} DE {len(TOUR_FICHA)}</div>'
                    f'<div class="t">{esc(titulo)}</div><div class="s">{esc(texto)}</div>'
                    f'<div class="dots">{puntos}</div>', unsafe_allow_html=True)
        a, b, c = st.columns([1, 1, 1.3])
        a.button("Saltar", key="tour_saltar", on_click=terminar_tour, width="stretch")
        b.button("Atrás", key="tour_atras", on_click=_mover, args=(-1,), width="stretch", disabled=paso == 0)
        if paso < len(TOUR_FICHA) - 1:
            c.button("Siguiente", key="tono_violeta_tour_sig", type="primary", on_click=_mover, args=(1,),
                     width="stretch", icon=":material/arrow_forward:")
        else:
            c.button("¡Listo!", key="tono_verde_tour_fin", type="primary", on_click=terminar_tour, width="stretch",
                     icon=":material/check:")
        components.html(f"<script>/* paso {paso} */ setTimeout(function(){{const e=window.parent.document."
                        f"querySelector({json.dumps(selector)}); if(e) e.scrollIntoView({{behavior:'smooth',"
                        f"block:'center'}});}}, 350);</script>", height=0)
