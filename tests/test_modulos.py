"""Pruebas de los módulos Oportunidades, Seguimiento y cronograma."""
from datetime import date, timedelta

import pandas as pd

from core import mercado
from core.extraccion import cronograma
from core.historial_ocds import clave_proveedor, resumen
from core.pdf_parser import extraer_paginas
from core.seguimiento import aprendizaje, checklist, nuevo, proximos_plazos
from core.preguntas import analizar
from tests.bases_ejemplo import crear_pdf

HIST = pd.DataFrame([
    {"rubro": "Uniformes y textiles", "ocid": f"o{i}", "fecha": f"202{i % 6}-05-01", "entidad": "EJERCITO PERUANO",
     "titulo": "Adquisición de uniformes", "valor_estimado": str(100000 * (i + 1)), "n_postores": str(i + 1),
     "ganador": "TEXTIL A S.A.C." if i % 2 else "Textil A SAC", "monto_adjudicado": str(95000 * (i + 1))}
    for i in range(6)])


def test_cronograma_lee_fechas_por_etapa():
    c = cronograma(extraer_paginas(crear_pdf()))
    assert c["observaciones"]["fecha"] == "2026-10-26"
    assert c["ofertas"]["fecha"] == "2026-11-09"
    assert c["buena_pro"]["fecha"] == "2026-11-16"


def test_ganadores_con_nombres_distintos_se_unen():
    assert clave_proveedor("Industria Estrella Azul E.I.R.L.") == clave_proveedor("INDUSTRIA ESTRELLA AZUL EIRL")
    r = resumen(HIST.to_dict("records"))
    assert r["veces_ganador"] == 6 and r["distintos_ganadores"] == 1


def test_mercado():
    d = mercado.preparar(HIST)
    assert mercado.rubros(d) == ["Uniformes y textiles"]
    assert mercado.resumen(d)["n"] == 6
    assert len(mercado.a_tu_medida(d, 250000)) == 2
    b = mercado.brechas(d, 250000)
    assert list(b["Procesos accesibles (%)"]) == sorted(b["Procesos accesibles (%)"])
    assert mercado.socios(d, 0).iloc[0]["Ganados"] == 6


def test_seguimiento():
    res = analizar(extraer_paginas(crear_pdf()))
    s = nuevo("abc", res, "bases.pdf")
    assert s["fecha_ofertas"] == "2026-11-09" and s["etapa"] == "Revisada"
    claves = [k for k, _ in checklist(res)]
    assert {"rnp", "exp", "iso", "muestras", "garantia"} <= set(claves)
    s["fecha_observaciones"] = (date.today() + timedelta(days=3)).isoformat()
    assert proximos_plazos([s])[0]["dias"] == 3
    assert round(aprendizaje({"mi_oferta": 103, "oferta_ganadora": 100, "valor_estimado": 110})["pct"]) == 3
