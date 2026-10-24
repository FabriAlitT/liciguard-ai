"""Pruebas del motor de las 4 preguntas (harness básico). Ejecutar: python -m pytest -q"""
import gzip
import json

from core.borrador import a_word, crear_borrador
from core.buscador import BM25, Normativa, buscar_en_paginas
from core.extraccion import cita_en_pagina, parse_monto
from core.ia import RouterIA, limpiar_salida, resumen_sin_ia
from core.pdf_parser import extraer_paginas
from core.preguntas import analizar
from core.preparar import dividir_articulos, preparar_historial
from tests.bases_ejemplo import crear_pdf

PERFIL = {"experiencia_soles": 320000, "certificaciones": []}
COSTOS = {"tela": 410000, "mano": 210000, "otros": 45000}


def _res(**kw):
    return analizar(extraer_paginas(crear_pdf()), PERFIL, **kw)


def test_montos_en_formatos_peruanos():
    assert parse_monto("1 600 000,00") == 1600000
    assert parse_monto("1,600,000.00") == 1600000
    assert parse_monto("1'600,000.00") == 1600000
    assert parse_monto("812400") == 812400
    assert parse_monto("812,40") == 812.40


def test_datos_generales():
    d = _res()["datos"]
    assert d["valor_estimado"] == 812400
    assert "uniformes" in d["objeto"].lower()
    assert d["nomenclatura"].startswith("04-2026")


def test_es_justa_detecta_senales_con_cita_verificada():
    j = _res()["justa"]
    titulos = " ".join(h["titulo"] for h in j["hallazgos"])
    assert j["estado"] == "cuidado"
    assert "TexAndes" in titulos and "experiencia" in titulos and "5 días" in titulos and "ISO 14001" in titulos
    assert all(h["cita_verificada"] for h in j["hallazgos"])


def test_marca_y_modelo_ofertado_no_es_senal():
    # "consignar la marca y modelo del bien ofertado" no debe contarse como exigencia de marca
    marcas = [r for r in _res()["requisitos"] if r["categoria"] == "marca"]
    assert len(marcas) == 1 and marcas[0]["valor"] == "TexAndes"


def test_puedo_y_salidas():
    p = _res()["puedo"]
    exp = next(i for i in p["items"] if i["requisito"] == "Experiencia")
    assert exp["estado"] == "no_cumple" and any("consorcio" in s for s in exp["salidas"])


COSTOS_IGV = {"tela": 330000, "mano": 170000, "otros": 40000}


def test_me_conviene_sin_igv_ni_financiamiento_es_el_calculo_simple():
    c = _res(oferta=780000, costos=COSTOS, supuestos={"aplica_igv": False, "tasa_mensual": 0})["conviene"]
    assert c["estado"] == "bien" and 100000 < c["ganancia"] < 115000 and c["igv"] == 0
    assert any(o["titulo"].startswith("Te pagan") and o["pagina"] == 6 for o in c["ocultos"])


def test_me_conviene_descuenta_igv_y_costo_financiero():
    c = _res(oferta=780000, costos=COSTOS_IGV)["conviene"]
    assert round(c["igv"]) == round(780000 - 780000 / 1.18)
    # financiamiento: 540 000 x 2 % mensual x (5 días de entrega + 30 de pago) / 30
    assert round(c["costo_financiero"]) == round(540000 * 0.02 * 35 / 30)
    assert c["estado"] == "bien" and 100000 < c["ganancia"] < 112000
    # los mismos costos de antes, al descontar el IGV, en realidad dan pérdida
    assert _res(oferta=780000, costos=COSTOS)["conviene"]["estado"] == "cuidado"


def test_no_conviene_si_pierde():
    r = _res(oferta=600000, costos=COSTOS)
    assert r["conviene"]["estado"] == "cuidado" and r["recomendacion"]["codigo"] == "no_postular"


def test_recomendacion_observar():
    assert _res(oferta=780000, costos=COSTOS_IGV)["recomendacion"]["codigo"] == "observar"


def test_puedo_ganar_con_historial():
    hist = [{"entidad": "MUNICIPALIDAD DISTRITAL DE EJEMPLO", "titulo": "Adquisición de uniformes institucionales",
             "ganador": "TEXTILES DEL NORTE SAC", "n_postores": "1", "valor_estimado": "800000",
             "monto_adjudicado": "790000", "fecha": f"202{i}-01-01"} for i in range(4)]
    g = _res(historial=hist)["ganar"]
    assert g["estado"] == "cuidado" and g["veces_ganador"] == 4


def test_cita_inventada_no_se_verifica():
    pag = extraer_paginas(crear_pdf())[3]["texto"]
    assert cita_en_pagina("deberá ser de marca TexAndes", pag)
    assert not cita_en_pagina("deberá ser de marca Patito", pag)


def test_borrador_y_word():
    r = _res()
    texto = crear_borrador(r, r["justa"]["hallazgos"][:2], "Mi Empresa SAC")
    assert "TexAndes" in texto and "Mi Empresa SAC" in texto and "página 4" in texto
    assert a_word(texto)[:2] == b"PK"


def test_buscador():
    idx = BM25(["el plazo de pago es de treinta días", "la marca de la tela"])
    assert idx.top("¿cuándo me pagan? plazo de pago")[0][0] == 0
    assert buscar_en_paginas(extraer_paginas(crear_pdf()), "forma de pago después de la conformidad", k=1)[0]["pagina"] == 6


def test_normativa_por_articulos():
    arts = dividir_articulos("LEY\nArtículo 1. Objeto\nRegula.\nArtículo 16. Requerimiento\nNo usar marca.", "Ley")
    n = Normativa(arts)
    assert [a["articulo"] for a in arts] == ["Artículo 1", "Artículo 16"]
    assert n.buscar("marca requerimiento")[0]["articulo"] == "Artículo 16"


def test_historial_ocds(tmp_path):
    ruta = tmp_path / "x.jsonl.gz"
    rel = {"ocid": "o1", "buyer": {"name": "Hospital X"}, "tender": {"title": "Uniformes", "tenderers": [{}, {}]},
           "awards": [{"status": "active", "suppliers": [{"name": "A SAC"}], "value": {"amount": 10}}]}
    with gzip.open(ruta, "wt") as f:
        f.write(json.dumps({"compiledRelease": rel}) + "\n")
        f.write(json.dumps({"tender": {"title": "Laptops"}, "awards": [{"suppliers": [{"name": "B"}]}]}) + "\n")
    salida = tmp_path / "h.csv"
    assert preparar_historial([ruta], ["uniforme"], salida, cada=0) == 1
    assert "A SAC" in salida.read_text()


def test_ia_sin_proveedores_usa_reglas():
    r = RouterIA([])
    assert r.completar("hola")["texto"] is None
    assert "corrijan" in resumen_sin_ia(_res(oferta=780000, costos=COSTOS_IGV))


def test_guardrail_lenguaje():
    assert "corrupción" not in limpiar_salida("Hay corrupción en estas bases").lower()


def _puedo(perfil):
    return {i["requisito"]: i for i in analizar(extraer_paginas(crear_pdf()), perfil)["puedo"]["items"]}


def test_capacidad_usa_produccion_maquinas_y_personal():
    sin_dato = _puedo(PERFIL)["Capacidad para entregar a tiempo"]
    assert sin_dato["estado"] == "verificar" and "2 400 prendas en 5 días" in sin_dato["piden"]
    poca = _puedo({**PERFIL, "produccion_mensual": 3000, "maquinas": 6, "personal": 8})["Capacidad para entregar a tiempo"]
    assert poca["estado"] == "no_cumple" and "máquinas más" in poca["salidas"][0] and "6 máquinas" in poca["tienes"]
    assert _puedo({**PERFIL, "produccion_mensual": 20000})["Capacidad para entregar a tiempo"]["estado"] == "cumple"


def test_beneficio_mype_no_cuenta_como_requisito_y_se_usa_en_conviene():
    pags = extraer_paginas(crear_pdf())
    pags[-1]["texto"] += " Las MYPE pueden optar por la retención del 10% del monto del contrato."
    r = analizar(pags, {**PERFIL, "es_mype": True}, oferta=780000, costos=COSTOS_IGV)
    item = next(i for i in r["puedo"]["items"] if i.get("beneficio"))
    assert item["estado"] == "cumple" and r["puedo"]["total"] == len(r["puedo"]["items"]) - 1
    assert r["conviene"]["usa_retencion"]
