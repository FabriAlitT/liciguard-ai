"""Oportunidades: inteligencia de mercado con los datos abiertos (procesos adjudicados)."""
import altair as alt
import streamlit as st

from core import mercado
from ui import estado as E
from ui.tema import AZUL, VIOLETA, chip, encabezado, entero, html_md, kpis, mostrar, seccion, soles, vacio

ss = st.session_state


def _graficos(f):
    a, b = st.columns([1.4, 1], gap="medium")
    with a.container(border=True):
        seccion("Evolución anual", "Procesos (barras) y monto adjudicado (línea)", "tendencia", "azul")
        anual = mercado.por_anio(f)
        base = alt.Chart(anual).encode(x=alt.X("Año:N", title=None, axis=alt.Axis(labelAngle=0)))
        barras = base.mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#BFD3FB").encode(
            y=alt.Y("Procesos:Q", title="Procesos"), tooltip=["Año", "Procesos", alt.Tooltip("Monto (S/):Q", format=",.0f")])
        linea = base.mark_line(color=AZUL, strokeWidth=3, point=alt.OverlayMarkDef(color=AZUL, size=60)).encode(
            y=alt.Y("Monto (S/):Q", title="Monto adjudicado (S/)", axis=alt.Axis(format="~s")))
        mostrar(alt.layer(barras, linea).resolve_scale(y="independent"), 260)
    with b.container(border=True):
        seccion("Tamaño de las compras", "Procesos por rango de valor estimado", "porcentaje", "violeta")
        r = mercado.rangos(f)
        mostrar(alt.Chart(r).mark_bar(cornerRadiusEnd=6, color=VIOLETA).encode(
            y=alt.Y("Rango:N", sort=alt.EncodingSortField("orden"), title=None),
            x=alt.X("Procesos:Q", title=None), tooltip=["Rango", "Procesos"]), 260)

    c, d = st.columns(2, gap="medium")
    with c.container(border=True):
        seccion("Principales compradores", "Entidades con más procesos · más oscuro = un mismo proveedor gana más",
                "edificio", "cian")
        top = mercado.top_entidades(f, 8)
        top["Entidad corta"] = top["Entidad"].astype(str).str[:34]
        mostrar(alt.Chart(top).mark_bar(cornerRadiusEnd=6).encode(
            y=alt.Y("Entidad corta:N", sort="-x", title=None), x=alt.X("Procesos:Q", title=None),
            color=alt.Color("Concentración:Q", scale=alt.Scale(range=["#67E8F9", "#0E7490"]), legend=None),
            tooltip=["Entidad", "Procesos", alt.Tooltip("Concentración:Q", format=".0%"),
                     alt.Tooltip("Monto total (S/):Q", format=",.0f")]), 280)
    with d.container(border=True):
        seccion("Quién gana más", "Participación en el monto adjudicado", "trofeo", "ambar")
        g = mercado.top_ganadores(f, 8)
        mostrar(alt.Chart(g).mark_bar(cornerRadiusEnd=6, color="#F59E0B").encode(
            y=alt.Y("Empresa:N", sort="-x", title=None), x=alt.X("Participación:Q", title=None, axis=alt.Axis(format="%")),
            tooltip=["Empresa", "Ganados", alt.Tooltip("Monto:Q", format=",.0f"),
                     alt.Tooltip("Participación:Q", format=".1%")]), 280)


def pantalla():
    rubro_emp = E.rubro()
    encabezado("Oportunidades", f"Oportunidades en {rubro_emp}" if rubro_emp else "Inteligencia de mercado",
               "Dónde se compra tu rubro, cuánto, con cuánta competencia y quién gana. Fuente: datos abiertos del OECE.",
               chip("Procesos adjudicados", "cian", "base"))
    d = E.mercado_df()
    if not len(d):
        vacio("base", "Aún no cargaste los datos abiertos",
              "Ejecuta el cuaderno 02_historial_ocds y pon historial.csv en data/ocds/.")
        return
    perfil = E.perfil() or {}
    rubros = mercado.rubros(d)
    por_defecto = perfil.get("rubro") if perfil.get("rubro") in rubros else d["rubro"].value_counts().index[0]
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.3, 1.5, 1, 0.8])
        if rubro_emp in rubros:               # se filtra por el rubro de la empresa activa (sin mezclar)
            rubro = rubro_emp
            c1.markdown(f'<div style="font-size:14px;color:#51607A;margin-bottom:6px">Rubro</div>'
                        f'{chip(rubro, "violeta", "diana")}', unsafe_allow_html=True)
        else:
            rubro = c1.selectbox("Rubro", ["Todos"] + rubros, index=(["Todos"] + rubros).index(por_defecto))
        entidad = c2.text_input("Entidad o región", placeholder="ej. Cusco, Ejército, EsSalud")
        monto = c3.number_input("Valor máximo (S/)", min_value=0.0, value=0.0, step=50000.0, help="0 = sin límite")
        desde = c4.selectbox("Desde", ["2021", "2022", "2023", "2024", "2025", "2026"], index=0)
    f = mercado.filtrar(d, rubro, entidad.strip() or None, monto or None, desde)
    r = mercado.resumen(f)
    if not r["n"]:
        vacio("lupa", "Sin resultados", "No hay procesos con esos filtros. Prueba ampliando el rango.")
        return

    a1, a2, var = mercado.variacion_anual(f)
    kpis([("Procesos adjudicados", entero(r["n"]), f"desde {desde}", "doc", "azul"),
          ("Monto total", soles(r["monto_total"]), "adjudicado", "dinero", "verde"),
          ("Valor típico", soles(r["valor_mediano"]), "mediana por proceso", "porcentaje", "violeta"),
          ("Variación anual", f"{var:+.0%}" if var is not None else "—", f"{a2} vs. {a1}" if var is not None else "",
           "tendencia", "verde" if (var or 0) >= 0 else "rojo")], columnas=4)
    kpis([("Entidades compradoras", entero(r["entidades"]), "distintas", "edificio", "cian"),
          ("Ganadores distintos", entero(r["ganadores"]), "proveedores", "personas", "violeta"),
          ("Participantes (mediana)", f"{r['participantes_mediana']:.0f}" if r.get("participantes_mediana") else "—",
           "registrados por proceso", "personas", "azul"),
          ("Con un solo participante", f"{r['pct_un_participante']:.0%}", "baja competencia", "alerta", "ambar")],
         columnas=4)

    _graficos(f)

    st.write("")
    t1, t2, t3 = st.tabs([":material/account_balance: Dónde se compra", ":material/target: A tu medida",
                          ":material/handshake: Socios para consorcio"])
    with t1:
        st.caption("Concentración = parte de los procesos que ganó el mismo proveedor. Alta concentración: "
                   "revisa con más cuidado las bases de esa entidad.")
        st.dataframe(mercado.top_entidades(f, 15), hide_index=True, width="stretch", column_config={
            "Monto total (S/)": st.column_config.NumberColumn(format="S/ %,.0f"),
            "Valor típico (S/)": st.column_config.NumberColumn(format="S/ %,.0f"),
            "Participantes (mediana)": st.column_config.NumberColumn(format="%.0f"),
            "Concentración": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
        })
    with t2:
        exp = float(perfil.get("experiencia_soles") or 0)
        if not exp:
            html_md('<div class="lg-aviso">Pon tu experiencia en <b>Mi empresa</b> para ver procesos a tu medida.</div>')
            st.button("Completar Mi empresa", on_click=E.ir_a, args=("Mi empresa",), icon=":material/apartment:")
        else:
            factor = st.slider("Supuesto: experiencia que piden = N veces el valor del proceso", 0.5, 2.0, 1.0, 0.25)
            medida = mercado.a_tu_medida(f, exp, factor, k=25)
            total_ok = len(mercado.a_tu_medida(f, exp, factor, k=100000))
            kpis([("Procesos a tu medida", entero(total_ok), f"de {entero(r['n'])} con estos filtros", "diana", "verde"),
                  ("Tu experiencia", soles(exp), "registrada en Mi empresa", "trofeo", "azul"),
                  ("Valor máximo que respaldas", soles(exp / factor), "con el supuesto elegido", "dinero", "violeta")],
                 columnas=3)
            st.dataframe(medida, hide_index=True, width="stretch", column_config={
                "Valor (S/)": st.column_config.NumberColumn(format="S/ %,.0f"),
                "Participantes": st.column_config.NumberColumn(format="%.0f")})
        st.caption("Son procesos ya adjudicados: te muestran qué tamaño de compra está a tu alcance y quién compite. "
                   "Las alertas de convocatorias abiertas en tiempo real son la siguiente fase.")
    with t3:
        minimo = st.number_input("Experiencia que te falta (S/)", min_value=0.0,
                                 value=float(ss.get("socios_min") or 0), step=100000.0)
        s = mercado.socios(f, minimo, 20)
        st.caption(f"{len(s)} empresas que ganaron en este rubro y suman esa experiencia o más (sin consorcios):")
        st.dataframe(s, hide_index=True, width="stretch", column_config={
            "Experiencia acumulada (S/)": st.column_config.NumberColumn(format="S/ %,.0f")})
        st.caption("Basado en contratos públicos adjudicados. Tú decides si los contactas.")
