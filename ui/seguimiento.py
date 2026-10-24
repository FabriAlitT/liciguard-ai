"""Seguimiento: embudo de tus procesos, agenda de plazos y aprendizaje del resultado."""
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from core.seguimiento import COLOR_ETAPA, ETAPAS, aprendizaje, checklist, dias_hasta, proximos_plazos
from ui import estado as E
from ui.tema import (TONOS, VERDE, barra_etapas, chip, encabezado, entero, esc, fecha_corta, html_md, kpis, mostrar,
                     pill_reco, progreso, seccion, soles, vacio)

ss = st.session_state
TONO_ETAPA = {"Revisada": "azul", "Observada": "ambar", "Ofertada": "violeta", "Ganada": "verde", "Perdida": "rojo",
              "Descartada": "gris"}


def _f(v):
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def _avance_checklist(s):
    res = next((f.get("resultado") for f in E.analisis() if f["sha256"] == s["sha256"]), None)
    items = checklist(res) if res else []
    marcados = s.get("checklist") or {}
    return (sum(bool(marcados.get(k)) for k, _ in items), len(items)) if items else (0, 0)


def _embudo(segs):
    conteo = pd.Series([s.get("etapa", "Revisada") for s in segs]).value_counts()
    datos = pd.DataFrame({"Etapa": ETAPAS, "Procesos": [int(conteo.get(e, 0)) for e in ETAPAS]})
    mostrar(alt.Chart(datos).mark_bar(cornerRadiusEnd=6).encode(
        y=alt.Y("Etapa:N", sort=ETAPAS, title=None), x=alt.X("Procesos:Q", title=None, axis=alt.Axis(tickMinStep=1)),
        color=alt.Color("Etapa:N", scale=alt.Scale(domain=ETAPAS, range=[COLOR_ETAPA[e] for e in ETAPAS]), legend=None),
        tooltip=["Etapa", "Procesos"]), 230)


def _agenda(plazos):
    if not plazos:
        vacio("calendario", "Sin plazos en los próximos 30 días", "Guarda las fechas en la pestaña Actuar de cada ficha.")
        return
    filas = []
    for p in plazos[:6]:
        dia, mes = fecha_corta(p["fecha"])
        tono = "rojo" if p["dias"] <= 3 else ("ambar" if p["dias"] <= 7 else "azul")
        cuando = "hoy" if p["dias"] == 0 else f"en {p['dias']} días"
        filas.append(f'<div class="lg-row"><div style="display:flex;gap:12px;align-items:center;min-width:0">'
                     f'<div class="lg-date"><b>{dia}</b><small>{mes}</small></div><div style="min-width:0">'
                     f'<div style="font-weight:700;color:#0B1B3F">{esc(p["que"])}</div><div style="color:#7A879C;'
                     f'font-size:13px">{esc(str(p["proceso"])[:55].capitalize())}</div></div></div>'
                     f'{chip(cuando, tono, "reloj")}</div>')
    html_md("".join(filas))


def acciones(activos) -> list[tuple[str, str, str]]:
    """Qué hacer ahora en cada proceso activo: (texto, detalle, tono)."""
    salida = []
    for s in activos:
        nombre = str(s.get("nombre") or "")[:48].capitalize()
        etapa = s.get("etapa", "Revisada")
        n_obs, n_of = dias_hasta(s.get("fecha_observaciones")), dias_hasta(s.get("fecha_ofertas"))
        if etapa == "Revisada" and s.get("recomendacion") == "observar" and n_obs is not None and n_obs >= 0:
            salida.append((f"Presenta tus observaciones en {n_obs} días", nombre, "rojo" if n_obs <= 3 else "ambar"))
        hechos, total = _avance_checklist(s)
        if total and hechos < total and etapa in ("Revisada", "Observada"):
            salida.append((f"Prepara {total - hechos} documentos pendientes", nombre, "violeta"))
        if not s.get("mi_oferta") and etapa in ("Revisada", "Observada"):
            salida.append(("Define tu precio en «¿Me conviene?»", nombre, "azul"))
        if etapa == "Ofertada" and n_of is not None and n_of < 0:
            salida.append(("Registra el resultado cuando se publique la buena pro", nombre, "cian"))
        if not s.get("fecha_ofertas"):
            salida.append(("Guarda la fecha de presentación de ofertas", nombre, "gris"))
    return salida


def _tarjeta(s):
    sha = s["sha256"]
    etapa = s.get("etapa", "Revisada")
    hechos, total = _avance_checklist(s)
    prox = min((d for d in (dias_hasta(s.get(c)) for c in ("fecha_observaciones", "fecha_ofertas", "fecha_buena_pro"))
                if d is not None and d >= 0), default=None)
    with st.container(border=True):
        html_md(f'<div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">'
                f'<div><div style="font-weight:800;color:#0B1B3F;font-size:16px">{esc(str(s.get("nombre") or "")[:90].capitalize())}</div>'
                f'<div style="color:#7A879C;font-size:13px">{esc(s.get("entidad") or "")}</div></div>'
                f'<div style="display:flex;gap:6px">{chip(etapa, TONO_ETAPA.get(etapa, "gris"))}'
                f'{pill_reco(s.get("recomendacion"))}</div></div>')
        html_md(f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0 6px">'
                f'<div><div style="font-size:12px;color:#7A879C;font-weight:600">Valor estimado</div>'
                f'<div style="font-weight:800;color:#0B1B3F">{soles(s.get("valor_estimado"))}</div></div>'
                f'<div><div style="font-size:12px;color:#7A879C;font-weight:600">Mi oferta</div>'
                f'<div style="font-weight:800;color:#0B1B3F">{soles(s.get("mi_oferta"))}</div></div>'
                f'<div><div style="font-size:12px;color:#7A879C;font-weight:600">Próximo plazo</div>'
                f'<div style="font-weight:800;color:{"#DC2626" if prox is not None and prox <= 3 else "#0B1B3F"}">'
                f'{"en " + str(prox) + " días" if prox is not None else "—"}</div></div>'
                f'<div><div style="font-size:12px;color:#7A879C;font-weight:600">Preparación de la oferta</div>'
                f'<div style="font-weight:800;color:#0B1B3F">{f"{hechos} de {total}" if total else "—"}</div>'
                f'{progreso(hechos / total * 100 if total else 0, VERDE)}</div></div>')
        html_md(barra_etapas(etapa, COLOR_ETAPA))
        with st.expander("Actualizar etapa, fechas y resultado", icon=":material/edit:"):
            c1, c2, c3 = st.columns(3)
            nueva = c1.selectbox("Etapa", ETAPAS, index=ETAPAS.index(etapa), key=f"et_{sha}")
            fo = c2.date_input("Último día para observar", _f(s.get("fecha_observaciones")), key=f"sfo_{sha}",
                               format="DD/MM/YYYY")
            fp = c3.date_input("Presentar oferta", _f(s.get("fecha_ofertas")), key=f"sfp_{sha}", format="DD/MM/YYYY")
            d1, d2, d3 = st.columns(3)
            mi = d1.number_input("Mi oferta (S/)", min_value=0.0, value=float(s.get("mi_oferta") or 0),
                                 step=1000.0, key=f"mi_{sha}")
            gan = d2.number_input("Oferta ganadora (S/)", min_value=0.0, value=float(s.get("oferta_ganadora") or 0),
                                  step=1000.0, key=f"og_{sha}")
            quien = d3.text_input("¿Quién ganó?", s.get("ganador") or "", key=f"qg_{sha}")
            notas = st.text_area("Notas", s.get("notas") or "", key=f"no_{sha}", height=80)
            e1, e2 = st.columns(2)
            if e1.button("Guardar", type="primary", key=f"gu_{sha}", width="stretch", icon=":material/save:"):
                s.update(etapa=nueva, fecha_observaciones=fo.isoformat() if fo else None,
                         fecha_ofertas=fp.isoformat() if fp else None, mi_oferta=mi or None,
                         oferta_ganadora=gan or None, ganador=quien or None, notas=notas)
                E.guardar_seguimiento(s)
                st.rerun()
            e2.button("Abrir ficha", key=f"ab_{sha}", width="stretch", on_click=E.ir_a, icon=":material/open_in_new:",
                      args=("Revisar bases",), kwargs={"sha_actual": sha, "abierto": sha})


def pantalla():
    encabezado("Seguimiento", "¿Cómo van tus procesos?",
               "Tu embudo de licitaciones: etapas, plazos, preparación y resultados.")
    if ss.aviso_tablas:
        html_md('<div class="lg-aviso">Para guardar el seguimiento en Supabase ejecuta '
                '<code>supabase/02_seguimiento_y_documentos.sql</code>.</div>')
    segs = sorted(E.seguimientos(), key=lambda s: str(s.get("actualizado_en", "")), reverse=True)
    activos = [s for s in segs if s.get("etapa") not in ("Ganada", "Perdida", "Descartada")]
    ganadas = [s for s in segs if s.get("etapa") == "Ganada"]
    cerradas = [s for s in segs if s.get("etapa") in ("Ganada", "Perdida")]
    kpis([("Procesos activos", entero(len(activos)), f"de {len(segs)} en total", "reloj", "azul"),
          ("Valor en juego", soles(sum(float(s.get("valor_estimado") or 0) for s in activos)), "procesos activos",
           "dinero", "violeta"),
          ("Ofertado", soles(sum(float(s.get("mi_oferta") or 0) for s in segs)), "suma de tus ofertas", "doc", "cian"),
          ("Ganado", soles(sum(float(s.get("mi_oferta") or 0) for s in ganadas)), f"{len(ganadas)} contratos",
           "trofeo", "verde"),
          ("Tasa de éxito", f"{len(ganadas) / len(cerradas):.0%}" if cerradas else "—",
           "ganadas / cerradas" if cerradas else "aún sin resultados", "diana", "ambar")], columnas=5)
    if not segs:
        vacio("lista", "Aún no tienes procesos",
              "Revisa unas bases y aparecerán aquí con sus fechas leídas del cronograma.")
        st.write("")
        st.button("Revisar bases", type="primary", on_click=E.ir_a, args=("Revisar bases",), icon=":material/upload_file:")
        return

    a, b = st.columns([1, 1.2], gap="medium")
    with a.container(border=True):
        seccion("Embudo por etapa", "Dónde está cada licitación", "tendencia", "azul")
        _embudo(segs)
    with b.container(border=True):
        seccion("Agenda", "Plazos de los próximos 30 días", "calendario", "rojo")
        _agenda(proximos_plazos(segs, dias=30))

    st.write("")
    filtro = st.radio("Mostrar", ["Activos", "Todos", "Cerrados"], horizontal=True, key="seg_filtro",
                      label_visibility="collapsed")
    lista = {"Activos": activos, "Todos": segs,
             "Cerrados": [s for s in segs if s not in activos]}[filtro]
    izq, der = st.columns([1.7, 1], gap="medium")
    with izq:
        seccion("Tus procesos", f"{len(lista)} {'proceso' if len(lista) == 1 else 'procesos'}", "lista", "violeta")
        if not lista:
            vacio("lista", "Nada por aquí", "Cambia el filtro para ver otros procesos.")
        for s in lista:
            _tarjeta(s)
    with der:
        seccion("Próximas acciones", "Lo que conviene hacer ahora", "rayo", "ambar")
        with st.container(border=True):
            pendientes = acciones(activos)
            if not pendientes:
                vacio("check", "Todo al día", "No tienes acciones pendientes en tus procesos activos.")
            html_md("".join(
                f'<div class="lg-row" style="align-items:flex-start"><span style="display:flex;gap:10px">'
                f'<span class="lg-dot" style="background:{TONOS[t][0]};margin-top:7px"></span><span>'
                f'<b style="color:#0B1B3F">{esc(a)}</b><br><small style="color:#7A879C">{esc(n)}</small></span></span></div>'
                for a, n, t in pendientes[:8]))

    perdidas = [s for s in segs if s.get("etapa") == "Perdida" and aprendizaje(s)]
    if perdidas:
        st.write("")
        seccion("Aprende para la próxima", "Compara tu oferta con la ganadora", "libro", "ambar")
        for s in perdidas:
            ap = aprendizaje(s)
            with st.container(border=True):
                txt = (f"Perdiste por <b>{soles(ap['diferencia'])}</b>: tu oferta fue <b>{ap['pct']:.1f} %</b> más alta "
                       f"que la ganadora." if ap["diferencia"] > 0 else "Tu oferta fue más baja que la ganadora: "
                       "revisa si perdiste por requisitos o por la evaluación técnica.")
                html_md(f'<div style="font-weight:800;color:#0B1B3F">{esc(str(s.get("nombre"))[:80].capitalize())}</div>'
                        f'<div style="color:#51607A;margin-bottom:8px">{txt}</div>')
                ve = s.get("valor_estimado") or max(s["mi_oferta"], s["oferta_ganadora"])
                tope = max(ve, s["mi_oferta"], s["oferta_ganadora"])
                for etiqueta, v, color in [("Valor estimado", ve, "#CBD5E1"), ("Tu oferta", s["mi_oferta"], "#EF4444"),
                                           ("Ganadora", s["oferta_ganadora"], "#10B981")]:
                    html_md(f'<div style="display:grid;grid-template-columns:120px 1fr 110px;gap:10px;align-items:center;'
                            f'font-size:14px;font-weight:600;margin:4px 0"><span>{etiqueta}</span>'
                            f'{progreso(v / tope * 100, color)}<span>{soles(v)}</span></div>')
