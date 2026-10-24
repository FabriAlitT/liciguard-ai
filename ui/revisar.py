"""Revisar bases: Ficha de decisión, Pruebas en el PDF, Actuar y Preguntar."""
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from core.borrador import a_word, crear_borrador
from core.buscador import buscar_en_paginas
from core.config import SUPUESTOS
from core.extraccion import primero
from core.ia import como_documento, contexto_de_resultado, resumen_sin_ia
from core.pdf_parser import PDFInvalido, extraer_paginas, huella, imagen_pagina_resaltada, paginas_sin_texto
from core.preguntas import analisis_fijo, completar_analisis
from core.seguimiento import checklist, nuevo, perfil_efectivo
from ui import estado as E
from ui import guia
from ui.tema import (AMBAR, AZUL, CIAN, PREGUNTAS, SEVERIDAD, TONO_SEVERIDAD, TONOS, VERDE, anillo, banner,
                     chip, con_glosario, encabezado, entero, esc, html_md, icono, indice_apertura, kpis, mostrar, pill_reco,
                     progreso, seccion, soles, soles_exacto, tarjeta_pregunta_html, vacio, kpi_html)

ss = st.session_state

QUE_REVISAMOS = [
    ("Marca específica", "balanza"), ("Experiencia desproporcionada", "trofeo"), ("Plazo de entrega corto", "reloj"),
    ("Certificaciones ISO", "escudo"), ("Muestras con poco tiempo", "lista"), ("Garantía de fiel cumplimiento", "dinero"),
    ("Retención para MYPE", "edificio"), ("Penalidades por atraso", "alerta"), ("Días de pago", "calendario"),
    ("Adelantos", "porcentaje"), ("Registro RNP", "doc"), ("Cronograma del proceso", "calendario"),
]




# ----------------------------------------------------------------------------------------
# Cálculo
# ----------------------------------------------------------------------------------------
def calcular(sha):
    """Recalcula la ficha con el perfil y los números actuales (rápido: solo reglas, sin IA)."""
    info = ss.pdfs[sha]
    e = ss.entradas.get(sha, {})
    for campo, clave in (("oferta", "of"), ("tela", "ma"), ("mano", "mo"), ("otros", "ot")):
        if f"{clave}_{sha}" in ss:
            e[campo] = ss[f"{clave}_{sha}"]
    supuestos = {k: ss[f"{c}_{sha}"] for k, c in (("comision_fianza_anual", "cf"), ("meses_contrato", "mc"),
                                                  ("aplica_igv", "igv"), ("tasa_mensual", "tm"))
                 if f"{c}_{sha}" in ss}
    costos = {k: e.get(k) for k in ("tela", "mano", "otros")} if e else None
    if "fijo" not in info:  # lo pesado (regex + normativa + OCDS) se calcula una sola vez por PDF
        info["fijo"] = analisis_fijo(info["paginas"], E.normativa(), E.historial())
    perfil = perfil_efectivo(E.perfil(), E.documentos())
    return completar_analisis(info["fijo"], perfil, oferta=e.get("oferta") or None, costos=costos,
                              supuestos=supuestos)


MAX_PDFS_EN_SESION = 4


def _limitar_pdfs(conservar):
    """Guarda en memoria solo los últimos PDFs (cada uno puede pesar hasta 50 MB)."""
    while len(ss.pdfs) > MAX_PDFS_EN_SESION:
        viejo = next(k for k in ss.pdfs if k not in (conservar, ss.sha_actual))
        ss.pdfs.pop(viejo)


def imagen_resaltada(sha, pdf_data, pagina, cita):
    """PNG de la página con la cita resaltada, guardada para no volver a dibujarla en cada clic."""
    cache = ss.pdfs[sha].setdefault("imagenes", {}) if sha in ss.pdfs else {}
    clave = (pagina, cita)
    if clave not in cache:
        cache[clave] = imagen_pagina_resaltada(pdf_data, pagina, cita)
    return cache[clave]


def fila_de(res, nombre, sha, paginas):
    d = res["datos"]
    return {"nombre_archivo": nombre, "sha256": sha, "paginas": len(paginas),
            "paginas_sin_texto": len(paginas_sin_texto(paginas)), "entidad": d.get("entidad"),
            "objeto": d.get("objeto"), "nomenclatura": d.get("nomenclatura"),
            "valor_estimado": d.get("valor_estimado"), "estado": "listo",
            "recomendacion": res["recomendacion"]["codigo"], "resultado": res}


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------------------------
# Pestaña 1 · Ficha de decisión
# ----------------------------------------------------------------------------------------
def detalle_justa(res):
    j = res["justa"]
    if not j["hallazgos"]:
        html_md('<div class="lg-ok">No encontramos condiciones restrictivas con nuestras reglas. '
                'Igual revisa las bases con calma.</div>')
        return
    conteo = pd.Series([h["severidad"] for h in j["hallazgos"]]).value_counts()
    html_md('<div style="display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 12px">'
            + "".join(chip(f"{conteo.get(s, 0)} {SEVERIDAD[s].lower()}{'s' if conteo.get(s, 0) != 1 else ''}",
                           TONO_SEVERIDAD[s]) for s in ("fuerte", "media", "leve"))
            + '<span style="color:#51607A;font-size:14px;align-self:center">· Míralas en <b>Pruebas en el PDF</b></span></div>')
    filas = []
    for h in j["hallazgos"]:
        fg, _ = TONOS[TONO_SEVERIDAD[h["severidad"]]]
        filas.append(f'<div style="display:flex;gap:14px;align-items:flex-start;padding:14px 16px;border:1px solid #E2E8F2;'
                     f'border-left:4px solid {fg};border-radius:12px;background:#FFFFFF;margin-bottom:8px">'
                     f'<div style="flex:1"><div style="font-weight:800;color:#0B1B3F">{esc(h["titulo"])}</div>'
                     f'<div style="color:#51607A;font-size:14px;margin-top:2px">{con_glosario(h["simple"])}</div></div>'
                     f'<div style="text-align:right;display:flex;flex-direction:column;gap:6px;align-items:flex-end">'
                     f'{chip(SEVERIDAD[h["severidad"]], TONO_SEVERIDAD[h["severidad"]])}'
                     f'<span style="font-size:12px;color:#7A879C;font-weight:600">pág. {h["pagina"]}</span></div></div>')
    html_md("".join(filas))


def detalle_puedo(res):
    p = res["puedo"]
    if p["estado"] == "sin_datos" and not p.get("items"):
        html_md(f'<div class="lg-info">{esc(p["resumen"])}</div>')
        st.write("")
        st.button("Completar Mi empresa", on_click=E.ir_a, args=("Mi empresa",), key="ir_emp_puedo",
                  icon=":material/apartment:")
        return
    if p.get("total"):
        aro = anillo(p["cumple"] / p["total"] * 100, VERDE if p["cumple"] == p["total"] else AMBAR,
                     f'{p["cumple"]}/{p["total"]}', "cumples")
        html_md(f'<div style="display:flex;gap:18px;align-items:center;margin:4px 0 6px">{aro}'
                f'<div style="font-weight:800;font-size:18px;color:#0B1B3F">{esc(p["resumen"])}</div></div>')
    estado_chip = {"cumple": ("Cumples", "verde"), "no_cumple": ("No cumples", "rojo"), "verificar": ("Verifica", "ambar")}
    for i in p["items"]:
        t, tono = estado_chip[i["estado"]]
        if i.get("beneficio"):
            t, tono = ("Beneficio disponible", "violeta") if i["estado"] == "cumple" else ("Beneficio", "gris")
        falta = f'<br><span style="color:#DC2626">Falta: {esc(i["falta"])}</span>' if i.get("falta") else ""
        salidas = ("<div style='margin-top:12px;padding-top:10px;border-top:1px solid #EEF2F7;font-size:13.5px;color:#1E40AF'>"
                   "<b>Tus salidas:</b> "
                   + " · ".join(con_glosario(s) for s in i["salidas"]) + "</div>") if i["salidas"] else ""
        html_md(f'<div style="padding:14px 16px;border:1px solid #E2E8F2;border-radius:12px;background:#FFFFFF;margin-top:8px">'
                f'<div class="lg-req">'
                f'<div><div style="font-weight:800;color:#0B1B3F">{con_glosario(i["requisito"])}</div>'
                f'<div style="font-size:12px;color:#7A879C">pág. {i["pagina"]}</div></div>'
                f'<div style="font-size:14px"><span style="color:#7A879C">Piden</span><br><b>{esc(i["piden"])}</b></div>'
                f'<div style="font-size:14px"><span style="color:#7A879C">Tienes</span><br><b>{esc(i["tienes"])}</b>'
                f'{falta}'
                f'</div><div class="ch">{chip(t, tono)}</div></div>{salidas}</div>')


def detalle_conviene(res, sha):
    e = ss.entradas.setdefault(sha, {"oferta": res.get("oferta_sugerida") or 0.0, "tela": 0.0, "mano": 0.0,
                                     "otros": 0.0})
    c1, c2, c3, c4 = st.columns(4)
    c1.number_input("Tu oferta (S/)", min_value=0.0, value=float(e["oferta"]), step=1000.0, key=f"of_{sha}")
    c2.number_input("Materiales (S/)", min_value=0.0, value=float(e["tela"]), step=1000.0, key=f"ma_{sha}")
    c3.number_input("Mano de obra (S/)", min_value=0.0, value=float(e["mano"]), step=1000.0, key=f"mo_{sha}")
    c4.number_input("Transporte y otros (S/)", min_value=0.0, value=float(e["otros"]), step=500.0, key=f"ot_{sha}")
    with st.expander("Ajustes avanzados"):
        st.number_input("Comisión anual de la carta fianza (%)", 0.0, 20.0, SUPUESTOS["comision_fianza_anual"],
                        key=f"cf_{sha}")
        st.number_input("Duración del contrato (meses)", 1, 36, SUPUESTOS["meses_contrato"], key=f"mc_{sha}")
        st.number_input("Costo del dinero (% mensual)", 0.0, 10.0, SUPUESTOS["tasa_mensual"], 0.5, key=f"tm_{sha}",
                        help="Lo que te cuesta financiar los insumos hasta que te paguen (préstamo o capital propio).")
        st.checkbox("Mi oferta incluye IGV (18 %)", value=SUPUESTOS["aplica_igv"], key=f"igv_{sha}",
                    help="Desmárcalo solo si tu empresa está exonerada de IGV.")
    c = res["conviene"]
    if c["estado"] != "sin_datos":
        valores = ss.entradas[sha]
        partes = [("IGV", c.get("igv", 0), "#E2E8F0"), ("Materiales", valores.get("tela", 0), "#C7D7FE"),
                  ("Mano de obra", valores.get("mano", 0), "#A5B4FC"), ("Otros", valores.get("otros", 0), "#94A3B8"),
                  ("Garantía", c["costo_garantia"], "#FCD34D"), ("Financiamiento", c.get("costo_financiero", 0), "#FDBA74")]
        bloques = "".join(f'<div style="flex:{max(v, 1):.0f};background:{col}" title="{n}: {soles(v)}"></div>'
                          for n, v, col in partes if v and v > 0)
        if c["ganancia"] > 0:
            bloques += (f'<div style="flex:{c["ganancia"]:.0f};background:linear-gradient(90deg,#10B981,#059669);'
                        f'color:#fff">{c["margen"]:.0f} %</div>')
        html_md(f'<div class="lg-bar">{bloques}</div>')
        st.caption("Gris claro: IGV (se paga a SUNAT) · Azul y gris: tus costos · Amarillo: garantía · "
                   "Naranja: costo de financiarte · Verde: tu ganancia")
        kpis([("Ganarías", soles(c["ganancia"]), f"margen de {c['margen']:.1f} % sobre tu ingreso sin IGV", "dinero",
               "verde" if c["ganancia"] > 0 else "rojo"),
              ("Capital que necesitas", soles(c["capital_necesario"]),
               f"por unos {c.get('meses_espera', 0):.1f} meses hasta que te paguen", "base", "azul"),
              ("Costo de financiarte", soles(c.get("costo_financiero")), "intereses mientras esperas el pago",
               "porcentaje", "ambar"),
              ("IGV incluido", soles(c.get("igv")), "no es tuyo: va a SUNAT", "doc", "gris"),
              ("Multa máxima", soles(c["multa_max"]), "si te atrasas", "alerta", "rojo")], columnas=5)
        if c.get("ratio_valor"):
            st.caption(f"Tu oferta es el {c['ratio_valor']:.0%} del valor estimado por la entidad."
                       + (" Usamos la retención MYPE en lugar de carta fianza." if c.get("usa_retencion") else ""))
    seccion("Lo que no se ve a simple vista", "Costos y riesgos escondidos en las bases", "lupa", "ambar")
    cols = st.columns(len(c["ocultos"]))
    for col, o in zip(cols, c["ocultos"]):
        col.markdown(f'<div class="lg-feat"><div class="t" style="font-size:15px">{esc(o["titulo"])}</div>'
                     f'<div style="font-size:20px;font-weight:800;color:#0B1B3F;margin-top:6px">{esc(o["detalle"])}</div>'
                     f'<div class="s">{"pág. " + str(o["pagina"]) if o["pagina"] else "Supuesto: las bases no lo indican"}'
                     f'</div></div>', unsafe_allow_html=True)


def detalle_ganar(res):
    g = res["ganar"]
    if g["estado"] == "sin_datos":
        html_md(f'<div class="lg-info">{esc(g["resumen"])}</div>')
        return
    kpis([("Procesos parecidos", entero(g["n"]), "misma entidad y objeto", "doc", "azul"),
          ("Ganadores distintos", entero(g.get("distintos_ganadores")), "en esos procesos", "personas", "violeta"),
          ("Precio ganador vs. valor", f"{g['ratio_min']:.0%} – {g['ratio_max']:.0%}" if g.get("ratio_min") else "—",
           "rango de descuento", "porcentaje", "cian"),
          ("Participantes", f"{g['promedio_participantes']:.0f}" if g.get("promedio_participantes") else "—",
           "registrados en promedio", "personas", "ambar")])
    filas = []
    for p in g["procesos"]:
        va, ad = _num(p.get("valor_estimado")), _num(p.get("monto_adjudicado"))
        filas.append({"Fecha": str(p.get("fecha", ""))[:10], "Ganó": p.get("ganador"),
                      "Participantes": _num(p.get("n_postores")), "Valor (S/)": va, "Adjudicado (S/)": ad,
                      "Precio/valor": ad / va if va and ad else None, "Proceso": str(p.get("titulo", ""))[:90]})
    tabla = pd.DataFrame(filas)
    con_ratio = tabla.dropna(subset=["Precio/valor"])
    if len(con_ratio):
        a, b = st.columns([1.2, 1], gap="large")
        with a:
            seccion("Precio ganador frente al valor estimado", "Cada punto es un proceso parecido", "tendencia", "cian")
            punto = alt.Chart(con_ratio).mark_circle(size=140, color=CIAN, opacity=.85).encode(
                x=alt.X("Fecha:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")), y=alt.Y("Precio/valor:Q", title="Precio / valor", axis=alt.Axis(format="%"),
                                                        scale=alt.Scale(zero=False)),
                tooltip=["Fecha", "Ganó", alt.Tooltip("Precio/valor:Q", format=".0%"),
                         alt.Tooltip("Adjudicado (S/):Q", format=",.0f")])
            regla = alt.Chart(pd.DataFrame({"y": [1]})).mark_rule(strokeDash=[4, 4], color="#94A3B8").encode(y="y:Q")
            mostrar(punto + regla, 220)
        with b:
            seccion("Quién ganó", "Veces que ganó cada empresa", "trofeo", "violeta")
            quien = tabla["Ganó"].fillna("—").astype(str).str[:30].value_counts().reset_index()
            quien.columns = ["Empresa", "Veces"]
            mostrar(alt.Chart(quien).mark_bar(cornerRadiusEnd=6, color="#7C3AED").encode(
                y=alt.Y("Empresa:N", sort="-x", title=None), x=alt.X("Veces:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                tooltip=["Empresa", "Veces"]), 220)
    st.dataframe(tabla, hide_index=True, width="stretch", column_config={
        "Valor (S/)": st.column_config.NumberColumn(format="S/ %,.0f"),
        "Adjudicado (S/)": st.column_config.NumberColumn(format="S/ %,.0f"),
        "Precio/valor": st.column_config.NumberColumn(format="percent"),
        "Participantes": st.column_config.NumberColumn(format="%.0f")})
    st.caption("Fuente: datos abiertos de contratación del OECE (estándar OCDS). Participantes = registrados, "
               "no necesariamente ofertas presentadas.")


def tab_ficha(res, sha):
    a, b = st.columns([3, 1])
    # Etiquetas fijas: si incluyeran el estado, al cambiar un número la selección se reiniciaría.
    opciones = [f"{n} · {t}" for _, n, t, _, _ in PREGUNTAS]
    with a:
        elegido = st.radio("Ver el detalle de", opciones, horizontal=True, key=f"det_{sha}", label_visibility="collapsed")
    if b.button("Explícamelo simple", key=f"simple_{sha}", icon=":material/auto_awesome:", width="stretch"):
        with st.spinner("Pidiendo la explicación a la IA…"):
            out = ss.router.completar("Explica en 4 frases simples qué conviene hacer y por qué.",
                                      contexto_de_resultado(res), tarea="explicacion", max_tokens=1200)
        ss[f"exp_{sha}"] = (out["texto"] or resumen_sin_ia(res), out["proveedor"] or "reglas (sin IA)")
        ss[f"exp_err_{sha}"] = None if out["texto"] else out
    if ss.get(f"exp_{sha}"):
        texto, prov = ss[f"exp_{sha}"]
        with st.container(border=True):
            seccion("En palabras simples", f"Explicado por: {prov}", "ia", "violeta")
            st.markdown(texto)
            if ss.get(f"exp_err_{sha}"):
                motivos_ia(ss[f"exp_err_{sha}"])
    clave = PREGUNTAS[opciones.index(elegido)][0]
    {"justa": lambda: detalle_justa(res), "puedo": lambda: detalle_puedo(res),
     "conviene": lambda: detalle_conviene(res, sha), "ganar": lambda: detalle_ganar(res)}[clave]()


# ----------------------------------------------------------------------------------------
# Pestaña 2 · Pruebas en el PDF
# ----------------------------------------------------------------------------------------
def tab_pruebas(res, pdf_data, sha):
    h = res["justa"]["hallazgos"]
    if not h:
        vacio("check", "Nada que mostrar", "No encontramos condiciones restrictivas en estas bases.")
        return
    nombres = [f"{i + 1}. {x['titulo'][:38]}" for i, x in enumerate(h)]
    elegido = st.selectbox("Alerta", nombres, key=f"pr_{sha}", label_visibility="collapsed")
    i = nombres.index(elegido)
    x = h[i]
    izq, der = st.columns([3, 2], gap="large")
    with izq.container(border=True):
        if pdf_data is not None:
            st.image(imagen_resaltada(sha, pdf_data, x["pagina"], x["cita"]), width="stretch")
        else:
            html_md(f'<div class="lg-cita">«{esc(x["cita"])}»</div>')
            st.caption("Vuelve a subir el PDF para ver la página resaltada.")
    with der:
        fg, _ = TONOS[TONO_SEVERIDAD[x["severidad"]]]
        html_md(f'<div class="lg-feat" style="border-left:4px solid {fg}"><div style="display:flex;justify-content:'
                f'space-between"><div style="font-size:12px;font-weight:700;color:#7A879C;letter-spacing:.06em">'
                f'PÁG. {x["pagina"]}</div>{chip(SEVERIDAD[x["severidad"]], TONO_SEVERIDAD[x["severidad"]])}</div>'
                f'<div style="font-size:20px;font-weight:800;color:#0B1B3F;margin-top:8px;line-height:1.35">'
                f'{esc(x["simple"])}</div></div>')
        verif = (chip("Cita verificada en el PDF", "verde", "check") if x["cita_verificada"]
                 else chip("Revisa la cita a mano", "ambar", "alerta"))
        html_md(f'<div style="margin-top:10px">{verif}</div>')
        st.write("")
        if x["normas"]:
            with st.expander(f"Qué dice la norma ({len(x['normas'])} artículo{'s' if len(x['normas']) != 1 else ''})",
                             icon=":material/gavel:"):
                for n in x["normas"]:
                    html_md(f'<div style="font-weight:700;color:#1D4ED8;font-size:14px">{esc(n["fuente"])} · '
                            f'{esc(n["articulo"])}</div><div style="color:#334155;font-size:14px;margin-bottom:10px">'
                            f'{esc(n["texto"][:380])}…</div>')
                st.caption("Confirma los artículos antes de citarlos.")
        st.write("")
        clave = (sha, i)
        if clave in ss.descartadas:
            st.button("Volver a incluir en mi observación", key=f"inc_{sha}_{i}", width="stretch",
                      on_click=lambda: ss.descartadas.discard(clave))
        else:
            st.button("No aplica (quitar de la observación)", key=f"des_{sha}_{i}", width="stretch",
                      on_click=lambda: ss.descartadas.add(clave))


# ----------------------------------------------------------------------------------------
# Pestaña 3 · Actuar
# ----------------------------------------------------------------------------------------
def _fecha(valor):
    try:
        return date.fromisoformat(str(valor)[:10]) if valor else None
    except ValueError:
        return None


def tab_actuar(res, sha, nombre):
    seg = E.seguimiento_de(sha) or nuevo(sha, res, nombre)
    h = res["justa"]["hallazgos"]
    izq, der = st.columns([3, 2], gap="large")
    with izq.container(border=True):
        seccion("Tu observación a las bases", "", "doc", "azul")
        if not h:
            st.write("No hay condiciones para observar.")
        else:
            opciones = {f"{x['titulo']} (pág. {x['pagina']})": x for x in h}
            por_defecto = [k for i, (k, x) in enumerate(opciones.items())
                           if x["severidad"] != "leve" and (sha, i) not in ss.descartadas]
            elegidas = st.multiselect("Qué incluir", list(opciones), default=por_defecto, key=f"sel_{sha}",
                                      placeholder="Elige las condiciones a observar")
            perfil = E.perfil() or {}
            empresa = perfil.get("razon_social") or (ss.usuario or {}).get("nombre") or "[Tu empresa]"
            texto = crear_borrador(res, [opciones[k] for k in elegidas], empresa, ciudad=perfil.get("region"))
            texto = st.text_area("Borrador (puedes editarlo)", texto, height=360, key=f"bor_{sha}_{len(elegidas)}")
            c1, c2 = st.columns(2)
            c1.download_button("Descargar Word", a_word(texto), "observacion.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               width="stretch", type="primary", icon=":material/download:")
            c2.download_button("Descargar texto", texto.encode("utf-8"), "observacion.txt", "text/plain",
                               width="stretch", icon=":material/description:")
            st.caption("Completa lo que está [entre corchetes] y preséntalo tú dentro del plazo.")
    with der:
        with st.container(border=True):
            cron = res.get("cronograma", {})
            seccion("Tus fechas", "" if cron else "No encontramos el cronograma",
                    "calendario", "violeta")
            f1 = st.date_input("Último día para observar", _fecha(seg.get("fecha_observaciones")), key=f"fo_{sha}",
                               format="DD/MM/YYYY")
            f2 = st.date_input("Presentar oferta", _fecha(seg.get("fecha_ofertas")), key=f"fp_{sha}", format="DD/MM/YYYY")
            f3 = st.date_input("Resultado (buena pro)", _fecha(seg.get("fecha_buena_pro")), key=f"fb_{sha}",
                               format="DD/MM/YYYY")
        with st.container(border=True):
            marcados = dict(seg.get("checklist") or {})
            items = checklist(res)
            listos = sum(bool(st.session_state.get(f"ck_{sha}_{k}", marcados.get(k))) for k, _ in items)
            seccion("Para tu oferta", f"{listos} de {len(items)} listos", "lista", "verde")
            html_md(progreso(listos / len(items) * 100, VERDE))
            st.write("")
            for k, texto_item in items:
                marcados[k] = st.checkbox(texto_item, value=bool(marcados.get(k)), key=f"ck_{sha}_{k}")
        if st.button("Guardar fechas y checklist", type="primary", width="stretch", key=f"gs_{sha}",
                     icon=":material/save:"):
            seg.update(fecha_observaciones=f1.isoformat() if f1 else None,
                       fecha_ofertas=f2.isoformat() if f2 else None,
                       fecha_buena_pro=f3.isoformat() if f3 else None, checklist=marcados)
            E.guardar_seguimiento(seg)
            st.success("Guardado. Lo verás en Seguimiento y en Inicio.")
        falta = next((i for i in res["puedo"].get("items", []) if i["requisito"] == "Experiencia"
                      and i["estado"] == "no_cumple"), None)
        if falta:
            with st.container(border=True):
                seccion("Otra salida: consorcio", f"Te falta {falta['falta']} de experiencia", "personas", "cian")
                monto = float(str(falta["falta"]).replace("S/", "").replace(" ", "").replace(",", "") or 0) \
                    if "M" not in str(falta["falta"]) and "mil" not in str(falta["falta"]) else 0
                st.button("Buscar socios en Oportunidades", key=f"soc_{sha}", on_click=E.ir_a, width="stretch",
                          args=("Oportunidades",), kwargs={"socios_min": monto}, icon=":material/handshake:")


def motivos_ia(out):
    """Explica por qué no respondió cada proveedor de IA."""
    errores = [i for i in out.get("intentos", []) if i["estado"] in ("error", "saltado")]
    if not errores:
        return
    with st.expander("¿Por qué no respondió la IA?", icon=":material/help:"):
        for i in errores:
            st.markdown(f"**{i['proveedor']}:** {i.get('explicacion') or i['error']}")
            st.caption(f"Detalle técnico: {i['error']}")


# ----------------------------------------------------------------------------------------
# Pestaña 4 · Preguntar
# ----------------------------------------------------------------------------------------
def tab_preguntar(paginas):
    with st.container(border=True):
        seccion("Pregúntale a tus bases", "", "ia", "violeta")
        sugerencias = ["¿Qué documentos necesito para postular?", "¿Cuál es el plazo de pago?",
                       "¿Cuánto es la penalidad por atraso?", "¿Puedo postular en consorcio?"]
        elegida = st.pills("Ideas", sugerencias, key="sug_preg", label_visibility="collapsed")
        a, b = st.columns([5, 1])
        escrita = a.text_input("Tu pregunta", key="preg", label_visibility="collapsed",
                               placeholder="Escribe tu pregunta o elige una idea")
        pulsado = b.button("Preguntar", type="primary", width="stretch")
    pregunta = (escrita or elegida or "").strip()
    if not pulsado or not pregunta:
        return
    trozos = buscar_en_paginas(paginas, pregunta, k=3) if paginas else []
    normas = E.normativa().buscar(pregunta, k=2)
    contexto = "\n\n".join(
        [f"[Bases, pág. {t['pagina']}]\n{como_documento(t['texto'], 2500)}" for t in trozos] +
        [f"[{n['fuente']} · {n['articulo']}]\n{n['texto'][:1500]}" for n in normas])
    if not contexto:
        st.warning("No hay texto de las bases en esta sesión. Vuelve a subir el PDF para preguntar.")
        return
    with st.spinner("Buscando la respuesta en tus bases…"):
        out = ss.router.completar(pregunta, contexto, tarea="asistente", max_tokens=1500)
    with st.container(border=True):
        if out["texto"]:
            st.markdown(out["texto"])
            respaldo = any(i["estado"] in ("error", "saltado") for i in out["intentos"])
            st.caption(f"Respondió {out['proveedor']}" + (" (respaldo automático)" if respaldo else "")
                       + (" · respuesta guardada, no gastó cuota" if out.get("desde_cache") else ""))
        else:
            html_md('<div class="lg-info">La IA no respondió. Estas son las partes que más se relacionan '
                    'con tu pregunta:</div>')
            motivos_ia(out)
    for t in trozos:
        with st.expander(f"Bases · página {t['pagina']}", icon=":material/description:"):
            st.text(t["texto"][:1500])
    for n in normas:
        with st.expander(f"{n['fuente']} · {n['articulo']}", icon=":material/gavel:"):
            st.write(n["texto"][:1500])


# ----------------------------------------------------------------------------------------
# Ficha
# ----------------------------------------------------------------------------------------
def _dato(reqs, categoria, formato):
    r = primero(reqs, categoria)
    return formato(r["valor"]) if r and r.get("valor") is not None else "No indica"


def resumen_ficha(res):
    """Índice de apertura (ocupa 2 filas) + 6 datos clave, en la misma rejilla de 4 columnas que las preguntas."""
    d, reqs = res["datos"], res.get("requisitos", [])
    indice = indice_apertura(res)
    tono = "verde" if indice >= 75 else ("ambar" if indice >= 50 else "rojo")
    nivel = "Abiertas" if indice >= 75 else ("Revisar" if indice >= 50 else "Restrictivas")
    fg, bg = TONOS[tono]
    p = res["puedo"]
    datos = [("Valor estimado", soles_exacto(d.get("valor_estimado")) if d.get("valor_estimado") else "No indica",
              f"pág. {d['valor_estimado_pagina']}" if d.get("valor_estimado_pagina") else "", "dinero", "azul"),
             ("Plazo de entrega", _dato(reqs, "plazo_entrega", lambda v: f"{v:g} días"), "desde la firma", "reloj", "violeta"),
             ("Experiencia pedida", _dato(reqs, "experiencia", soles), "monto acumulado", "trofeo", "cian"),
             ("Garantía", _dato(reqs, "garantia", lambda v: f"{v:g} %"), "fiel cumplimiento", "escudo", "ambar"),
             ("Pago", _dato(reqs, "pago", lambda v: f"{v:g} días"), "después de la conformidad", "calendario", "verde"),
             ("Requisitos que cumples", f"{p['cumple']} de {p['total']}" if p.get("total") else "—",
              "según Mi empresa", "lista", "azul")]
    indice_html = (f'<div class="lg-kpi lg-indice" style="--kc:{fg};--kb:{bg}"><div class="k">ÍNDICE DE APERTURA</div>'
                   f'{anillo(indice, fg, str(indice), "de 100")}{chip(nivel, tono)}</div>')
    html_md(f'<div class="lg-ficha">{indice_html}{"".join(kpi_html(*x) for x in datos)}</div>')


def ficha(res, pdf_data, paginas, sha, nombre):
    d = res["datos"]
    meta = "".join(chip(x, t, i) for x, t, i in [(d.get("entidad"), "azul", "edificio"),
                                                 (d.get("procedimiento"), "gris", "doc"),
                                                 (d.get("nomenclatura"), "gris", None)] if x)
    html_md(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">{meta}</div>'
            f'<div style="font-size:26px;font-weight:800;color:#0B1B3F;letter-spacing:-0.02em;line-height:1.2;'
            f'margin-bottom:14px">{esc((d.get("objeto") or "Licitación").capitalize())}</div>')
    with st.container(key="tour_reco"):
        banner(res["recomendacion"])
    with st.container(key="tour_datos"):
        resumen_ficha(res)
    with st.container(key="tour_preguntas"):
        html_md('<div class="lg-ficha">' + "".join(tarjeta_pregunta_html(res, *x) for x in PREGUNTAS) + '</div>')
    st.write("")
    t1, t2, t3, t4 = st.container(key="tour_pestanas").tabs([
        ":material/assignment: Ficha de decisión", ":material/find_in_page: Pruebas en el PDF",
        ":material/edit_document: Actuar", ":material/forum: Pregúntale a tus bases"])
    with t1:
        tab_ficha(res, sha)
    with t2:
        tab_pruebas(res, pdf_data, sha)
    with t3:
        tab_actuar(res, sha, nombre)
    with t4:
        tab_preguntar(paginas)


# ----------------------------------------------------------------------------------------
# Página
# ----------------------------------------------------------------------------------------
def _procesar(archivo):
    return _procesar_datos(archivo.getvalue(), archivo.name)


def _procesar_datos(data, nombre_archivo):
    sha = huella(data)
    if sha not in ss.pdfs:
        caja = st.empty()            # el avance se ve mientras se procesa y luego desaparece
        try:
            with caja.status("Revisando tus bases…", expanded=True) as estado:
                st.write("Leyendo las páginas…")
                paginas = extraer_paginas(data)
                vacias = paginas_sin_texto(paginas)
                if len(vacias) > len(paginas) * 0.5:
                    st.warning("La mayoría de páginas parecen escaneadas (sin texto): el análisis será incompleto.")
                st.write("Respondiendo: ¿Es justa? · ¿Puedo? · ¿Me conviene? · ¿Puedo ganar?")
                ss.pdfs[sha] = {"data": data, "paginas": paginas, "nombre": nombre_archivo}
                _limitar_pdfs(conservar=sha)
                res = calcular(sha)
                st.write("Verificando cada cita en el PDF…")
                E.guardar_analisis(fila_de(res, nombre_archivo, sha, paginas))
                if not E.seguimiento_de(sha):
                    E.guardar_seguimiento(nuevo(sha, res, nombre_archivo))
                estado.update(label="Listo", state="complete", expanded=False)
            caja.empty()
        except PDFInvalido as e:
            st.error(str(e))
            return False
    nuevo_abierto = ss.sha_actual != sha
    ss.sha_actual, ss.abierto = sha, None
    return nuevo_abierto


def _nueva_revision():
    ss.sha_actual, ss.abierto = None, None
    ss.n_subida = ss.get("n_subida", 0) + 1


def _portada():
    with st.container(border=True):
        seccion("Sube el PDF de las bases", "", "subir", "azul")
        archivo = st.file_uploader("Sube el PDF de las bases", type=["pdf"], key=f"subir_{ss.get('n_subida', 0)}",
                                   label_visibility="collapsed")
        if not E.perfil():
            html_md('<div class="lg-info">Consejo: completa <b>Mi empresa</b> para saber si cumples los requisitos.</div>')
        with st.expander(f"¿Qué revisamos? ({len(QUE_REVISAMOS)} condiciones)", icon=":material/shield:"):
            html_md('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px">' + "".join(
                f'<div style="display:flex;gap:8px;align-items:center;font-size:13px;font-weight:600;color:#334155;'
                f'background:#F8FAFF;border:1px solid #EEF2F7;border-radius:10px;padding:8px 10px">'
                f'{icono(ic, AZUL, 15)}{esc(t)}</div>' for t, ic in QUE_REVISAMOS) + '</div>')
    st.write("")
    _probar_ejemplo()
    filas = E.analisis()
    if filas:
        st.write("")
        with st.container(border=True):
            seccion("Revisiones recientes", "", "reloj", "gris")
            for f in filas[:5]:
                res = f.get("resultado") or {}
                n_al = len(res.get("justa", {}).get("hallazgos", []))
                a, b, c, d = st.columns([4, 1.4, 1.3, 1])
                a.markdown(f'<div style="font-weight:700;color:#0B1B3F;padding-top:8px">'
                           f'{esc((f.get("objeto") or f["nombre_archivo"])[:80].capitalize())}</div>'
                           f'<div style="color:#7A879C;font-size:12.5px">{esc(f.get("entidad") or "")}</div>',
                           unsafe_allow_html=True)
                b.markdown(f'<div style="padding-top:12px;font-weight:700">{soles(f.get("valor_estimado"))}</div>',
                           unsafe_allow_html=True)
                c.markdown(f'<div style="padding-top:10px">{pill_reco(f.get("recomendacion"))}<br>'
                           f'<small style="color:#7A879C">{n_al} alertas</small></div>', unsafe_allow_html=True)
                d.button("Abrir", key=f"rec_{f['sha256']}", width="stretch", on_click=E.ir_a, args=("Revisar bases",),
                         kwargs={"sha_actual": f["sha256"], "abierto": f["sha256"]})
    return archivo


def _probar_ejemplo():
    """Atajo: revisar una base de ejemplo del rubro de tu empresa, sin tener un PDF a mano."""
    from core import ejemplos as X
    from ui.ejemplos import abrir_base
    rubro = E.rubro()
    bases = X.bases_de_rubro(rubro)[:3] if rubro else []
    if not bases:
        return
    with st.container(border=True, key="rev_ejemplos"):
        seccion(f"¿Sin PDF? Prueba un ejemplo de {rubro}", "", "rayo", "violeta")
        cols = st.columns(len(bases) + 1)
        for col, b in zip(cols, bases):
            t, tono = {"postular": ("Postular", "verde"), "observar": ("Observar primero", "ambar"),
                       "no_postular": ("No te conviene", "rojo"), None: ("Real · SEACE", "cian")}[b.get("esperado")]
            col.markdown(f'<div style="font-weight:800;color:#0B1B3F">{esc(b["titulo"][:48])}</div>'
                         f'<div style="font-size:13px;color:#7A879C;margin:2px 0 6px">{soles(b.get("valor"))} · '
                         f'{chip(t, tono)}</div>', unsafe_allow_html=True)
            col.button("Revisar este ejemplo", key=f"tono_{tono}_rev_{b['archivo'][:12]}", width="stretch",
                       on_click=abrir_base, args=(b["id"],), icon=":material/play_circle:")
        with cols[-1]:
            st.markdown(f'<div style="font-weight:800;color:#0B1B3F">Todas las de {esc(rubro)}</div>'
                        f'<div style="font-size:13px;color:#7A879C;margin:2px 0 6px">'
                        f'{len(X.bases_de_rubro(rubro))} disponibles</div>', unsafe_allow_html=True)
            st.button("Ver ejemplos", key="tono_violeta_rev_galeria", width="stretch", on_click=E.ir_a,
                      args=("Ejemplos",), icon=":material/science:")


def _ejemplo_pendiente():
    """Si se eligió una base en Ejemplos, se analiza aquí (con el mismo flujo que un PDF subido)."""
    pendiente = ss.pop("ejemplo_pendiente", None)
    if not pendiente:
        return
    from core import ejemplos as X
    b = X.base(pendiente)
    if not b:
        st.error("No encontramos ese ejemplo. Elige otro en la página Ejemplos.")
        return
    data = b["ruta"].read_bytes()
    if b.get("numeros"):            # cifras de ejemplo para «¿Me conviene?» (la persona puede cambiarlas)
        sha = huella(data)
        ss.entradas[sha] = dict(b["numeros"])
        for clave in ("of", "ma", "mo", "ot"):
            ss.pop(f"{clave}_{sha}", None)
    _procesar_datos(data, b["archivo"])
    ss.ejemplo_activo = {"sha": ss.sha_actual, "titulo": b["titulo"], "origen": b["origen"],
                         "empresa": (E.perfil() or {}).get("razon_social")}


def _aviso_ejemplo(sha):
    ej = ss.get("ejemplo_activo") or {}
    if ej.get("sha") != sha:
        return
    quien = f" · <b>{esc(ej['empresa'])}</b>" if ej.get("empresa") else ""
    tipo = "un ejemplo" if ej["origen"] == "demo" else "bases reales del SEACE"
    a, c, b = st.columns([4, 1.3, 1.2], vertical_alignment="center")
    c.button("Recorrido guiado", key="tono_violeta_tour_ficha", type="primary", width="stretch",
             on_click=guia.iniciar_tour, icon=":material/tour:")
    a.markdown(f'<div class="lg-info" style="background:#F2ECFF;color:#5B21B6;border-color:#DDD0FB">'
               f'Estás viendo {tipo}{quien}.</div>', unsafe_allow_html=True)
    b.button("Otro ejemplo", key="tono_violeta_otro_ej", width="stretch", on_click=E.ir_a, args=("Ejemplos",),
             icon=":material/science:")


def pantalla():
    _ejemplo_pendiente()
    abierto = (ss.sha_actual in ss.pdfs) or bool(ss.abierto)
    if not abierto:
        encabezado("Revisar bases", "Revisemos tus bases")
        archivo = _portada()
        if archivo and _procesar(archivo):
            st.rerun()
        return

    a, b = st.columns([3, 1])
    with a:
        encabezado("Revisar bases", "Ficha de decisión")
    with b:
        st.write("")
        st.button("Revisar otras bases", icon=":material/add:", on_click=_nueva_revision, width="stretch")
    sha = ss.sha_actual
    if sha and sha in ss.pdfs:
        _aviso_ejemplo(sha)
        info = ss.pdfs[sha]
        res = calcular(sha)
        ficha(res, info["data"], info["paginas"], sha, info["nombre"])
        st.write("")
        if st.button("Guardar cambios en mi historial", icon=":material/save:"):
            if E.guardar_analisis(fila_de(res, info["nombre"], sha, info["paginas"])):
                st.success("Guardado.")
        guia.tour()
    elif ss.abierto:
        fila = next((f for f in E.analisis() if f["sha256"] == ss.abierto), None)
        if fila and fila.get("resultado"):
            html_md('<div class="lg-info">Ficha guardada. Para ver el PDF, vuelve a subirlo.</div>')
            st.write("")
            ficha(fila["resultado"], None, None, fila["sha256"], fila["nombre_archivo"])
            guia.tour()
