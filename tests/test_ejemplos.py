"""Catálogo de ejemplos: cada base ficticia da el resultado esperado con su empresa modelo."""
from core import ejemplos as X
from core.pdf_parser import extraer_paginas
from core.preguntas import analizar
from core.seguimiento import perfil_efectivo


def test_cada_base_ficticia_con_su_empresa_da_lo_esperado():
    demos = [b for b in X.bases_disponibles() if b["origen"] == "demo"]
    assert len(demos) == 8
    assert {b['rubro'] for b in demos} == {e['perfil']['rubro'] for e in X.EMPRESAS}
    for b in demos:
        emp = X.empresa(b["empresa"])
        perfil = perfil_efectivo(emp["perfil"], X.documentos_de(emp))
        r = analizar(extraer_paginas(b["ruta"].read_bytes()), perfil)
        assert r["recomendacion"]["codigo"] == b["esperado"], b["archivo"]


def test_bases_reales_con_catalogo(tmp_path, monkeypatch):
    from tests.bases_ejemplo import crear_pdf
    (tmp_path / "proceso_1.pdf").write_bytes(crear_pdf())
    (tmp_path / "catalogo.csv").write_text("archivo,entidad,titulo,valor_estimado,fecha,url\n"
                                           "proceso_1.pdf,Municipalidad X,Compra de uniformes,150000,2025-03-01,"
                                           "https://prod1.seace.gob.pe/x\n", encoding="utf-8")
    monkeypatch.setattr(X, "CARPETA_REALES", tmp_path)
    monkeypatch.setattr(X, "CARPETA_DESCARGAS", tmp_path / "no_existe")
    reales = [b for b in X.bases_disponibles() if b["origen"] == "real"]
    assert len(reales) == 1 and reales[0]["entidad"] == "Municipalidad X" and reales[0]["valor"] == 150000
    assert X.base(reales[0]["id"])["titulo"] == "Compra de uniformes"


def test_documentos_con_fechas_desde_hoy():
    docs = X.documentos_de(X.empresa("muebles"))
    assert {d["tipo"] for d in docs} == {"Constancia RNP", "Carta fianza"}
    assert all(len(X.bases_de_rubro(e["perfil"]["rubro"])) == 2 for e in X.EMPRESAS)        # 2 por rubro
    assert all(d["vence_el"] for d in docs)
