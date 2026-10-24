"""Las 4 preguntas de la ficha de decisión y la recomendación final.

Todo aquí es determinista (reglas + datos). La IA solo se usa después para explicar en simple
y para el asistente, así se gastan pocos tokens y el resultado es repetible.
"""
import math

from core.config import CERTIFICACIONES_POCO_COMUNES, SUPUESTOS, UMBRALES
from core.extraccion import cita_en_pagina, cronograma, datos_generales, extraer_requisitos, maximo, primero
from core.historial_ocds import procesos_parecidos, resumen

ESTADOS = {"bien": "Bien", "ojo": "Ojo", "cuidado": "Cuidado", "sin_datos": "Sin datos"}


def _hallazgo(pregunta, severidad, titulo, simple, req, consulta_norma, normativa, textos):
    normas = normativa.buscar(consulta_norma, k=2) if normativa else []
    return {
        "pregunta": pregunta, "severidad": severidad, "titulo": titulo, "simple": simple,
        "pagina": req["pagina"], "cita": req["cita"],
        "cita_verificada": cita_en_pagina(req["cita"], textos.get(req["pagina"], "")),
        "normas": [{"fuente": n.get("fuente"), "articulo": n.get("articulo"), "texto": n["texto"][:600],
                    "url": n.get("url")} for n in normas],
    }


def _fmt(n):
    return f"S/ {n:,.0f}".replace(",", " ") if n is not None else "—"


# ----------------------------------------------------------------------------------------
# 1. ¿Es justa?
# ----------------------------------------------------------------------------------------
def evaluar_justa(datos, reqs, normativa, textos) -> dict:
    h = []
    for r in [x for x in reqs if x["categoria"] == "marca"]:
        h.append(_hallazgo("justa", "fuerte" if r.get("tajante") else "media",
                           f"Piden una marca específica ({r['valor']})",
                           "Solo podrías postular con esa marca, aunque tengas una igual o mejor.",
                           r, "requerimiento marca equivalente especificaciones técnicas", normativa, textos))

    exp, ve = maximo(reqs, "experiencia"), datos.get("valor_estimado")
    if exp and ve:
        ratio = exp["valor"] / ve
        if ratio > UMBRALES["experiencia_media"]:
            sev = "fuerte" if ratio > UMBRALES["experiencia_fuerte"] else "media"
            h.append(_hallazgo("justa", sev, f"Piden {ratio:.1f} veces el valor del contrato en experiencia",
                               f"Te piden haber vendido {_fmt(exp['valor'])} para un contrato de {_fmt(ve)}.",
                               exp, "experiencia del postor monto facturado acumulado requisitos calificación",
                               normativa, textos))

    plazo = min((x for x in reqs if x["categoria"] == "plazo_entrega" and x.get("valor")),
                key=lambda x: x["valor"], default=None)
    if plazo and plazo["valor"] <= UMBRALES["plazo_entrega_corto"]:
        sev = "fuerte" if plazo["valor"] <= UMBRALES["plazo_entrega_muy_corto"] else "media"
        h.append(_hallazgo("justa", sev, f"Entrega en solo {plazo['valor']} días",
                           "Un plazo tan corto favorece a quien ya tiene los bienes listos.",
                           plazo, "plazo de entrega libre concurrencia competencia", normativa, textos))

    for r in [x for x in reqs if x["categoria"] == "certificacion"]:
        numero = r["valor"].split()[-1]
        if numero in CERTIFICACIONES_POCO_COMUNES and r.get("tipo") == "requisito":
            h.append(_hallazgo("justa", "media", f"Piden {r['valor']} ({CERTIFICACIONES_POCO_COMUNES[numero]})",
                               "Verifica si este certificado tiene relación real con lo que se compra.",
                               r, "requisitos de calificación relación objeto contratación certificación",
                               normativa, textos))

    mu = min((x for x in reqs if x["categoria"] == "muestras"), key=lambda x: x["valor"], default=None)
    if mu and mu["valor"] <= UMBRALES["muestras_horas_corto"]:
        h.append(_hallazgo("justa", "leve", f"Muestras en {mu['valor']} horas",
                           "Tendrías muy poco tiempo para preparar y llevar tus muestras.",
                           mu, "muestras plazo presentación", normativa, textos))

    fuertes = sum(x["severidad"] == "fuerte" for x in h)
    estado = "cuidado" if fuertes else ("ojo" if h else "bien")
    textos_estado = {
        "cuidado": "Podría estar hecha a la medida de otro proveedor",
        "ojo": "Hay condiciones que conviene revisar",
        "bien": "No encontramos condiciones restrictivas con nuestras reglas",
    }
    return {"estado": estado, "resumen": textos_estado[estado], "hallazgos": h}


# ----------------------------------------------------------------------------------------
# 2. ¿Puedo?
# ----------------------------------------------------------------------------------------
def _item_capacidad(plazo, cantidad, perfil) -> dict:
    """¿Alcanza tu producción para entregar a tiempo? Usa producción mensual, máquinas y personal del perfil."""
    prod = float(perfil.get("produccion_mensual") or 0)
    maq, per = int(perfil.get("maquinas") or 0), int(perfil.get("personal") or 0)
    equipo = ", ".join(x for x in [f"{maq} máquinas" if maq else "", f"{per} personas" if per else ""] if x)
    dias = plazo["valor"] if plazo else None
    ref = cantidad or plazo
    base = {"requisito": "Capacidad para entregar a tiempo", "pagina": ref["pagina"], "cita": ref["cita"]}
    if not cantidad:   # las bases no dicen cuánto: solo se puede mostrar el plazo
        return {**base, "requisito": "Plazo de entrega", "piden": f"{dias} días",
                "tienes": f"Produces {prod:,.0f} al mes".replace(",", " ") if prod else "Tú decides",
                "estado": "verificar", "salidas": ["Confirma si puedes producir y entregar en ese plazo"]}
    unidad = cantidad.get("unidad") or "unidades"
    piden = f"{cantidad['valor']:,} {unidad}".replace(",", " ") + (f" en {dias} días" if dias else "")
    if not prod:
        return {**base, "piden": piden, "tienes": "Sin dato de producción", "estado": "verificar",
                "salidas": ["Registra tu producción mensual en Mi empresa para calcularlo"]}
    meses = (dias or 30) / 30
    capacidad = prod * meses
    ok = capacidad >= cantidad["valor"]
    tienes = f"{capacidad:,.0f} en ese plazo".replace(",", " ") + (f" ({equipo})" if equipo else "")
    falta = None if ok else f"{cantidad['valor'] - capacidad:,.0f} {unidad}".replace(",", " ")
    salidas = [] if ok else ["Subcontratar o ir en consorcio para la parte que te falta",
                             "Observar el plazo de entrega si es muy corto para el volumen"]
    if not ok and maq:
        por_maquina = prod / maq
        extra = math.ceil((cantidad["valor"] - capacidad) / (por_maquina * meses)) if por_maquina else None
        if extra:
            salidas.insert(0, f"Necesitarías unas {extra} máquinas más (o turnos extra) con tu ritmo actual")
    return {**base, "piden": piden, "tienes": tienes, "estado": "cumple" if ok else "no_cumple", "falta": falta,
            "salidas": salidas}


def evaluar_puedo(reqs, perfil: dict | None, justa: dict) -> dict:
    if not perfil:
        return {"estado": "sin_datos", "resumen": "Completa el perfil de tu empresa para saberlo", "items": []}
    items = []
    observables = {h["pagina"] for h in justa["hallazgos"]}

    exp = maximo(reqs, "experiencia")
    if exp:
        tengo = float(perfil.get("experiencia_soles") or 0)
        ok = tengo >= exp["valor"]
        items.append({"requisito": "Experiencia", "piden": _fmt(exp["valor"]), "tienes": _fmt(tengo),
                      "estado": "cumple" if ok else "no_cumple", "pagina": exp["pagina"], "cita": exp["cita"],
                      "falta": None if ok else _fmt(exp["valor"] - tengo),
                      "salidas": [] if ok else (["Observarlo (tiene señal de posible direccionamiento)"]
                                                if exp["pagina"] in observables else []) +
                      ["Postular en consorcio con quien tenga la experiencia"]})

    mis_certs = {c.upper().replace(" ", "") for c in (perfil.get("certificaciones") or [])}
    for r in [x for x in reqs if x["categoria"] == "certificacion" and x.get("tipo") == "requisito"]:
        ok = r["valor"].upper().replace(" ", "") in mis_certs
        items.append({"requisito": r["valor"], "piden": "Vigente", "tienes": "Sí" if ok else "No registrada",
                      "estado": "cumple" if ok else "no_cumple", "pagina": r["pagina"], "cita": r["cita"],
                      "salidas": [] if ok else (["Observarlo si no se relaciona con el objeto"]
                                                if r["pagina"] in observables else []) +
                      ["Socio en consorcio que la tenga"]})

    if primero(reqs, "rnp"):
        r = primero(reqs, "rnp")
        rnp = perfil.get("rnp_vigente")  # True / False / None (no lo registró)
        if rnp is None:
            items.append({"requisito": "RNP vigente", "piden": "Sí", "tienes": "No registrado",
                          "estado": "verificar", "pagina": r["pagina"], "cita": r["cita"],
                          "salidas": ["Marca en «Mi empresa» si tu RNP está vigente o registra tu constancia"]})
        else:
            ok = bool(rnp)
            items.append({"requisito": "RNP vigente", "piden": "Sí", "tienes": "Sí" if ok else "No",
                          "estado": "cumple" if ok else "no_cumple", "pagina": r["pagina"], "cita": r["cita"],
                          "salidas": [] if ok else ["Renovar la inscripción antes de ofertar"]})

    plazo = min((x for x in reqs if x["categoria"] == "plazo_entrega" and x.get("valor")),
                key=lambda x: x["valor"], default=None)
    cantidad = maximo(reqs, "cantidad")
    if plazo or cantidad:
        items.append(_item_capacidad(plazo, cantidad, perfil))

    ret = primero(reqs, "retencion_mype")
    if ret:
        es_mype = perfil.get("es_mype")
        items.append({"requisito": "Beneficio MYPE: retención en vez de carta fianza", "piden": "Ser MYPE acreditada",
                      "tienes": "Sí" if es_mype else "No registrado", "estado": "cumple" if es_mype else "verificar",
                      "pagina": ret["pagina"], "cita": ret["cita"], "beneficio": True,
                      "salidas": [] if es_mype else ["Acredítate en el REMYPE para no tener que pagar una carta fianza"]})
    mu = primero(reqs, "muestras")
    if mu:
        items.append({"requisito": "Muestras", "piden": f"En {mu['valor']} horas", "tienes": "Tú decides",
                      "estado": "verificar", "pagina": mu["pagina"], "cita": mu["cita"],
                      "salidas": ["Confirma si puedes llevarlas a tiempo"]})

    if not items:
        return {"estado": "sin_datos", "resumen": "No encontramos requisitos que podamos comparar", "items": []}
    requisitos = [i for i in items if not i.get("beneficio")]  # los beneficios no cuentan como requisito
    cumple = sum(i["estado"] == "cumple" for i in requisitos)
    no = sum(i["estado"] == "no_cumple" for i in requisitos)
    estado = "bien" if no == 0 else ("ojo" if any(i["salidas"] for i in items if i["estado"] == "no_cumple")
                                     else "cuidado")
    return {"estado": estado, "resumen": f"Cumples {cumple} de {len(requisitos)} requisitos revisados",
            "items": items, "cumple": cumple, "total": len(requisitos)}


# ----------------------------------------------------------------------------------------
# 3. ¿Me conviene?
# ----------------------------------------------------------------------------------------
def evaluar_conviene(datos, reqs, oferta: float | None, costos: dict | None, supuestos: dict | None = None,
                     es_mype: bool = False) -> dict:
    """Ganancia real: descuenta IGV, garantía (o retención MYPE) y el costo de financiarte mientras esperas el pago."""
    s = {**SUPUESTOS, **(supuestos or {})}
    g = primero(reqs, "garantia")
    pen = maximo(reqs, "penalidad")
    pago = primero(reqs, "pago")
    plazo = min((x["valor"] for x in reqs if x["categoria"] == "plazo_entrega" and x.get("valor")), default=None)
    ret = primero(reqs, "retencion_mype")
    garantia_pct = g["valor"] if g else s["garantia_pct"]
    penal_pct = pen["valor"] if pen else s["penalidad_max_pct"]
    dias_pago = pago["valor"] if pago else s["dias_pago"]
    dias_entrega = plazo or s["dias_entrega"]
    meses_espera = (dias_entrega + dias_pago) / 30          # desde que compras insumos hasta que te pagan
    usa_retencion = bool(es_mype and ret)
    ocultos = [
        {"titulo": "Garantía de fiel cumplimiento",
         "detalle": (f"{garantia_pct:g} % retenido de tus pagos (beneficio MYPE)" if usa_retencion
                     else f"{garantia_pct:g} % del contrato"),
         "pagina": g["pagina"] if g else None, "cita": g["cita"] if g else None, "supuesto": not g},
        {"titulo": "Multa máxima por atraso", "detalle": f"Hasta {penal_pct:g} % del contrato",
         "pagina": pen["pagina"] if pen else None, "cita": pen["cita"] if pen else None, "supuesto": not pen},
        {"titulo": "Te pagan", "detalle": f"Unos {dias_pago} días después de la conformidad" if pago
         else f"Las bases no lo indican (suponemos {dias_pago} días)", "pagina": pago["pagina"] if pago else None,
         "cita": pago["cita"] if pago else None, "supuesto": not pago},
    ]
    if ret:
        ocultos.append({"titulo": "Opción para MYPE", "detalle": "Retención en lugar de carta fianza"
                        + (" (la estamos usando en el cálculo)" if usa_retencion else ""),
                        "pagina": ret["pagina"], "cita": ret["cita"], "supuesto": False})

    if not oferta or not costos or not any(costos.values()):
        return {"estado": "sin_datos", "resumen": "Ingresa tu oferta y tus costos para calcularlo",
                "ocultos": ocultos}
    directos = sum(v or 0 for v in costos.values())
    tasa = s["tasa_mensual"] / 100
    igv = oferta - oferta / (1 + s["igv_pct"] / 100) if s["aplica_igv"] else 0.0
    ingreso = oferta - igv                                   # lo que realmente queda para ti
    if usa_retencion:   # el dinero retenido "cuesta" lo que te costaría prestártelo durante el contrato
        costo_garantia = oferta * garantia_pct / 100 * tasa * s["meses_contrato"]
    else:               # comisión del banco por la carta fianza
        costo_garantia = oferta * garantia_pct / 100 * s["comision_fianza_anual"] / 100 * s["meses_contrato"] / 12
    costo_financiero = directos * tasa * meses_espera
    ganancia = ingreso - directos - costo_garantia - costo_financiero
    margen = ganancia / ingreso * 100 if ingreso else 0.0
    multa = oferta * penal_pct / 100
    estado = "bien" if margen >= UMBRALES["margen_bueno"] else ("ojo" if margen >= UMBRALES["margen_justo"]
                                                                  else "cuidado")
    resumen_txt = (f"Ganarías unos {_fmt(ganancia)} ({margen:.0f} %)" if ganancia > 0
                   else f"Perderías unos {_fmt(-ganancia)}")
    return {"estado": estado, "resumen": resumen_txt, "oferta": oferta, "costos": costos, "igv": igv,
            "ingreso_neto": ingreso, "costo_garantia": costo_garantia, "usa_retencion": usa_retencion,
            "costo_financiero": costo_financiero, "meses_espera": meses_espera, "ganancia": ganancia,
            "margen": margen, "multa_max": multa, "capital_necesario": directos, "ocultos": ocultos,
            "ratio_valor": oferta / datos["valor_estimado"] if datos.get("valor_estimado") else None}


# ----------------------------------------------------------------------------------------
# 4. ¿Puedo ganar?
# ----------------------------------------------------------------------------------------
def evaluar_ganar(datos, historial) -> dict:
    if historial is None or len(historial) == 0:
        return {"estado": "sin_datos", "resumen": "Carga los datos abiertos con el notebook", "procesos": []}
    procesos = procesos_parecidos(historial, datos.get("entidad"), datos.get("objeto"))
    res = resumen(procesos)
    if res["n"] == 0:
        return {"estado": "sin_datos", "resumen": "No encontramos procesos parecidos de esta entidad",
                "procesos": [], **res}
    alerta_ganador = res["n"] >= 3 and res["share_ganador"] >= UMBRALES["ganador_repetido"]
    alerta_poca = (res["promedio_participantes"] is not None
                   and res["promedio_participantes"] <= UMBRALES["participantes_pocos"])
    if alerta_ganador:
        txt = f"{res['ganador_frecuente']} ganó {res['veces_ganador']} de {res['n']} procesos parecidos"
    elif alerta_poca:
        txt = "En procesos parecidos casi no hubo competencia"
    else:
        txt = f"Hay competencia: {res['distintos_ganadores']} ganadores distintos en {res['n']} procesos parecidos"
    estado = "cuidado" if alerta_ganador else ("ojo" if alerta_poca else "bien")
    return {"estado": estado, "resumen": txt, "procesos": procesos, **res}


# ----------------------------------------------------------------------------------------
# Recomendación final
# ----------------------------------------------------------------------------------------
def recomendar(justa, puedo, conviene, ganar) -> dict:
    if conviene["estado"] == "cuidado":
        return {"codigo": "no_postular", "titulo": "Con estos números no te conviene",
                "detalle": "Revisa tus costos o tu precio antes de invertir en la propuesta."}
    hay_fuertes = any(h["severidad"] == "fuerte" for h in justa["hallazgos"])
    no_cumple = [i for i in puedo.get("items", []) if i["estado"] == "no_cumple"]
    if hay_fuertes or (justa["hallazgos"] and no_cumple):
        return {"codigo": "observar", "titulo": "Vale la pena, pero primero pide que corrijan las bases",
                "detalle": "Presenta tus observaciones dentro del plazo; si las acogen, podrás competir en mejores condiciones."}
    if no_cumple:
        return {"codigo": "no_postular", "titulo": "Hoy no cumples todos los requisitos",
                "detalle": "Mira las salidas propuestas (por ejemplo, un consorcio) antes de decidir."}
    if ganar["estado"] == "cuidado":
        return {"codigo": "observar", "titulo": "Puedes postular, pero la competencia ha sido muy concentrada",
                "detalle": "Revisa con calma las condiciones y tu precio frente a los ganadores anteriores."}
    return {"codigo": "postular", "titulo": "Adelante: puedes postular",
            "detalle": "No encontramos condiciones restrictivas y cumples lo revisado."}


def analisis_fijo(paginas, normativa=None, historial=None) -> dict:
    """La parte pesada que solo depende del PDF (regex, BM25 de normativa, búsqueda OCDS).

    Se calcula UNA vez por PDF y se guarda; así, al escribir tus costos o cambiar el perfil,
    solo se recalcula lo liviano (ver `completar_analisis`).
    """
    textos = {p["pagina"]: p["texto"] for p in paginas}
    datos = datos_generales(paginas)
    reqs = extraer_requisitos(paginas)
    return {"datos": datos, "cronograma": cronograma(paginas), "requisitos": reqs,
            "justa": evaluar_justa(datos, reqs, normativa, textos),
            "ganar": evaluar_ganar(datos, historial if historial is not None else [])}


def completar_analisis(fijo, perfil=None, oferta=None, costos=None, supuestos=None) -> dict:
    """La parte liviana: depende del perfil y de los números que escribe la persona."""
    datos, reqs, justa, ganar = fijo["datos"], fijo["requisitos"], fijo["justa"], fijo["ganar"]
    puedo = evaluar_puedo(reqs, perfil, justa)
    if oferta is None and datos.get("valor_estimado"):
        oferta = round(datos["valor_estimado"] * 0.96, -2)
    conviene = evaluar_conviene(datos, reqs, oferta, costos, supuestos, es_mype=bool((perfil or {}).get("es_mype")))
    return {**fijo, "puedo": puedo, "conviene": conviene,
            "recomendacion": recomendar(justa, puedo, conviene, ganar), "oferta_sugerida": oferta}


def analizar(paginas, perfil=None, normativa=None, historial=None, oferta=None, costos=None, supuestos=None):
    return completar_analisis(analisis_fijo(paginas, normativa, historial), perfil, oferta, costos, supuestos)
