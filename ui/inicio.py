"""Inicio: panel con lo urgente, tus indicadores y el pulso de tu mercado."""
import altair as alt
import pandas as pd
import streamlit as st

from core import mercado
from core.seguimiento import proximos_plazos
from ui import estado as E
from ui.tema import (AZUL, CIAN, ETIQUETA_RECO, TONOS, VERDE, chip, encabezado, entero, esc, fecha_corta, hoy_texto,
                     html_md, icono, kpis, mini_estados, mostrar, pill_reco, progreso, seccion, soles, vacio)

ss = st.session_state


def _agenda(plazos):
    filas = []
    for p in plazos[:6]:
        dia, mes = fecha_corta(p["fecha"])
        tono = "rojo" if p["dias"] <= 3 else ("ambar" if p["dias"] <= 7 else "azul")
        cuando = "hoy" if p["dias"] == 0 else f"en {p['dias']} días"
        filas.append(f'<div class="lg-row"><div style="display:flex;gap:12px;align-items:center;min-width:0">'
                     f'<div class="lg-date"><b>{dia}</b><small>{mes}</small></div><div style="min-width:0">'
                     f'<div style="font-weight:700;color:#0B1B3F">{esc(p["que"])}</div><div style="color:#7A879C;'
                     f'font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                     f'{esc(str(p["proceso"])[:70].capitalize())}</div></div></div>'
                     f'{chip(cuando, tono, "reloj")}</div>')
    html_md("".join(filas))


def _primeros_pasos(perfil, filas, segs, docs):
    pasos = [("Entrar a LiciGuard", True),
             ("Completar Mi empresa", bool(perfil and perfil.get("experiencia_soles"))),
             ("Revisar tus primeras bases", bool(filas)),
             ("Guardar fechas de un proceso", any(s.get("fecha_ofertas") or s.get("fecha_observaciones") for s in segs)),
             ("Registrar tus documentos", bool(docs))]
    hechos = sum(ok for _, ok in pasos)
    seccion("Primeros pasos", f"{hechos} de {len(pasos)} completados", "check", "verde")
    html_md(progreso(hechos / len(pasos) * 100, VERDE))
    html_md("".join(
        f'<div class="lg-row"><span style="display:flex;gap:10px;align-items:center;font-weight:600;'
        f'color:{"#0B1B3F" if not ok else "#7A879C"}">{icono("check", VERDE if ok else "#CBD6EA", 19)}'
        f'{"<s>" if ok else ""}{t}{"</s>" if ok else ""}</span></div>' for t, ok in pasos))
    return hechos == len(pasos)


def _decisiones(filas):
    seccion("Tus decisiones", "Recomendación de cada licitación revisada", "diana", "violeta")
    conteo = pd.Series([f.get("recomendacion") for f in filas]).value_counts()
    datos = pd.DataFrame({"Recomendación": [ETIQUETA_RECO.get(k, ("Otro",))[0] for k in conteo.index],
                          "Licitaciones": conteo.values})
    dominio = [v[0] for v in ETIQUETA_RECO.values()]
    colores = [TONOS[v[1]][0] for v in ETIQUETA_RECO.values()]
    donut = alt.Chart(datos).mark_arc(innerRadius=70, outerRadius=105, cornerRadius=4, padAngle=0.02).encode(
        theta="Licitaciones:Q",
        color=alt.Color("Recomendación:N", scale=alt.Scale(domain=dominio, range=colores), title=None),
        tooltip=["Recomendación", "Licitaciones"])
    centro = alt.Chart(pd.DataFrame({"t": [str(len(filas))]})).mark_text(
        fontSize=30, fontWeight=800, color="#0B1B3F", dy=-6).encode(text="t:N")
    sub = alt.Chart(pd.DataFrame({"t": ["revisadas"]})).mark_text(fontSize=12, color="#7A879C", dy=16).encode(text="t:N")
    mostrar(donut + centro + sub, 250)


def _pulso(perfil):
    d = E.mercado_df()
    if not len(d):
        return
    rubros = mercado.rubros(d)
    rubro = perfil.get("rubro") if perfil.get("rubro") in rubros else d["rubro"].value_counts().index[0]
    f = mercado.filtrar(d, rubro, desde=2021)
    reciente = mercado.filtrar(f, desde=2025)
    r = mercado.resumen(reciente)
    with st.container(border=True):
        seccion(f"Pulso de tu mercado · {rubro}", "Datos abiertos del OECE (procesos adjudicados)", "tendencia", "azul")
        exp = float(perfil.get("experiencia_soles") or 0)
        p = mercado.percentil(mercado.filtrar(d, rubro, desde=2023), exp) if exp else None
        alcance = p * 100 if p is not None else None
        kpis([("Procesos 2025–2026", entero(r.get("n")), "adjudicados en tu rubro", "doc", "azul"),
              ("Monto adjudicado", soles(r.get("monto_total")), "desde 2025", "dinero", "verde"),
              ("Valor típico", soles(r.get("valor_mediano")), "mediana por proceso", "porcentaje", "violeta"),
              ("Tu alcance hoy", f"{alcance:.0f} %" if alcance is not None else "—",
               "de procesos que podrías respaldar" if exp else "completa tu experiencia", "diana", "cian")])
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            anual = mercado.por_anio(f)
            area = alt.Chart(anual).mark_area(
                line={"color": AZUL, "strokeWidth": 2.5}, opacity=1,
                color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                                   stops=[alt.GradientStop(color="#FFFFFF", offset=0),
                                          alt.GradientStop(color="#93B4F8", offset=1)])).encode(
                x=alt.X("Año:N", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("Procesos:Q", title="Procesos"),
                tooltip=["Año", "Procesos", alt.Tooltip("Monto (S/):Q", format=",.0f")])
            puntos = alt.Chart(anual).mark_circle(size=60, color=AZUL).encode(x="Año:N", y="Procesos:Q")
            mostrar(area + puntos, 230)
        with b:
            top = mercado.top_entidades(reciente, 6)
            if len(top):
                top["Entidad corta"] = top["Entidad"].astype(str).str[:28]
                barras = alt.Chart(top).mark_bar(cornerRadiusEnd=6, color=CIAN).encode(
                    y=alt.Y("Entidad corta:N", sort="-x", title=None), x=alt.X("Procesos:Q", title="Procesos desde 2025"),
                    tooltip=["Entidad", "Procesos", alt.Tooltip("Monto total (S/):Q", format=",.0f")])
                mostrar(barras, 230)
        st.button("Ver todas las oportunidades", icon=":material/travel_explore:", on_click=E.ir_a,
                  args=("Oportunidades",), key="ini_opo")


def pantalla():
    perfil = E.perfil() or {}
    quien = (ss.usuario or {}).get("nombre") or "invitado"
    empresa_txt = " · ".join(x for x in [perfil.get("razon_social"), perfil.get("rubro")] if x)
    encabezado("Panel principal", f"Hola, {quien}",
               f"Resumen de {empresa_txt}: licitaciones, plazos y mercado en un solo lugar." if empresa_txt else
               "Tu resumen de licitaciones, plazos y mercado en un solo lugar.",
               chip(hoy_texto(), "gris", "calendario"))
    if ss.get("codigo_recien_creado"):
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(f'<div style="color:#51607A;font-weight:600">Tu código para volver a entrar</div>'
                       f'<div class="lg-codigo">{esc(ss.codigo_recien_creado)}</div>'
                       f'<div style="color:#7A879C;font-size:13px">Guárdalo: no hay contraseña, este código es tu llave.</div>',
                       unsafe_allow_html=True)
            if b.button("Ya lo guardé", icon=":material/check:", width="stretch"):
                ss.codigo_recien_creado = None
                st.rerun()
    if ss.invitado:
        html_md('<div class="lg-aviso">Estás como invitado: nada se guardará al cerrar.</div>')
        st.write("")

    filas, segs, docs = E.analisis(), E.seguimientos(), E.documentos()
    activos = [s for s in segs if s.get("etapa") not in ("Ganada", "Perdida", "Descartada")]
    ganadas = sum(s.get("etapa") == "Ganada" for s in segs)
    cerradas = sum(s.get("etapa") in ("Ganada", "Perdida") for s in segs)
    alertas = sum(len((f.get("resultado") or {}).get("justa", {}).get("hallazgos", [])) for f in filas)
    kpis([("Licitaciones revisadas", entero(len(filas)), "en tu historial", "doc", "azul"),
          ("Valor analizado", soles(sum(float(f.get("valor_estimado") or 0) for f in filas)), "suma de valores estimados",
           "dinero", "verde"),
          ("Alertas detectadas", entero(alertas), "condiciones para observar", "alerta", "ambar"),
          ("Procesos activos", entero(len(activos)), "en seguimiento", "reloj", "violeta"),
          ("Tasa de éxito", f"{ganadas / cerradas:.0%}" if cerradas else "—",
           f"{ganadas} ganadas de {cerradas} cerradas" if cerradas else "aún sin resultados", "trofeo", "cian")], columnas=5)

    izq, der = st.columns([1.35, 1], gap="medium")
    with izq.container(border=True):
        plazos = proximos_plazos(segs, dias=30)
        seccion("Próximos plazos", "Los siguientes 30 días", "calendario", "rojo" if plazos and plazos[0]["dias"] <= 3
                else "azul")
        if plazos:
            _agenda(plazos)
            st.button("Ir a Seguimiento", icon=":material/timeline:", on_click=E.ir_a, args=("Seguimiento",), key="ir_seg")
        else:
            vacio("calendario", "Sin plazos cercanos", "Cuando revises unas bases, leemos su cronograma y te avisamos aquí.")
            st.write("")
            st.button("Revisar unas bases", type="primary", icon=":material/upload_file:", on_click=E.ir_a,
                      args=("Revisar bases",), key="ir_rev")
    with der.container(border=True):
        completo = _primeros_pasos(perfil, filas, segs, docs) if not filas else True
        if filas and completo:
            _decisiones(filas)
        if not filas:
            from ui.ejemplos import demo_de_empresa_activa
            st.write("")
            html_md('<div class="lg-info" style="background:#F2ECFF;color:#5B21B6;border-color:#DDD0FB">'
                    f'¿Primera vez? Te mostramos cómo LiciGuard revisa unas bases de {esc(perfil.get("rubro") or "tu rubro")}, '
                    'paso a paso.</div>')
            st.write("")
            c1, c2 = st.columns(2)
            c1.button("Recorrido guiado", key="tono_violeta_demo_inicio", type="primary", width="stretch",
                      on_click=demo_de_empresa_activa, icon=":material/play_arrow:")
            c2.button("Ver ejemplos", key="ini_ejemplos", width="stretch", on_click=E.ir_a, args=("Ejemplos",),
                      icon=":material/science:")

    _pulso(perfil)

    if filas:
        st.write("")
        seccion("Tus licitaciones revisadas", f"Últimas {min(len(filas), 6)} de {len(filas)}", "doc", "azul")
        cols = st.columns(3)
        for i, f in enumerate(filas[:6]):
            with cols[i % 3].container(border=True):
                html_md(f'<div>{pill_reco(f.get("recomendacion"))}</div>'
                        f'<div style="font-weight:800;color:#0B1B3F;line-height:1.3;margin-top:8px;min-height:42px">'
                        f'{esc((f.get("objeto") or f["nombre_archivo"])[:70].capitalize())}</div>'
                        f'<div style="color:#7A879C;font-size:13px;margin-top:4px">'
                        f'{esc(f.get("entidad") or "")} · {soles(f.get("valor_estimado"))}</div>')
                html_md(mini_estados(f.get("resultado")))
                st.button("Abrir ficha", key=f"ini_{f['sha256']}", width="stretch", on_click=E.ir_a,
                          args=("Revisar bases",), kwargs={"sha_actual": f["sha256"], "abierto": f["sha256"]})
