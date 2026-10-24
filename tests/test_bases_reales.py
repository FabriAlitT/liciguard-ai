"""Funciones del cuaderno 04 (bajar bases reales). Sin internet: se prueban con archivos fabricados."""
import io
import zipfile

import pandas as pd

from core.bases_reales import elegir_procesos, procesar_descarga, revisar_pdf, tipo_de_archivo
from tests.bases_ejemplo import crear_pdf


def test_reconoce_tipos_por_contenido():
    assert tipo_de_archivo(crear_pdf()) == "pdf"
    assert tipo_de_archivo(b"Rar!\x1a\x07\x00") == "rar"
    assert tipo_de_archivo(b"  <!DOCTYPE html><html>") == "html"


def test_saca_los_pdf_de_un_zip_y_prioriza_bases():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("anexos.pdf", crear_pdf())
        z.writestr("carpeta/BASES_INTEGRADAS.pdf", crear_pdf())
        z.writestr("leeme.txt", "hola")
    tipo, pdfs = procesar_descarga(buf.getvalue())
    assert tipo == "zip" and [n for n, _ in pdfs] == ["BASES_INTEGRADAS.pdf", "anexos.pdf"]


def test_revisar_pdf_dice_si_sirve():
    r = revisar_pdf(crear_pdf())
    assert r["paginas"] == 6 and r["con_texto"] == 1.0 and r["parece_bases"] and r["motivo"] == "sirve"
    assert "no se pudo abrir" in revisar_pdf(b"%PDF-roto")["motivo"]


def test_muestra_variada_por_entidad():
    df = pd.DataFrame([{"rubro": "Limpieza", "fecha": f"2025-0{i % 9 + 1}-01", "entidad": f"E{i % 3}",
                        "url": f"https://prod1.seace.gob.pe/x?fileCode={i}"} for i in range(30)])
    m = elegir_procesos(df, "Limpieza", "2024", cuantos=10, max_por_entidad=2)
    assert len(m) == 6 and m["entidad"].value_counts().max() == 2


def _zip(**archivos):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for nombre, contenido in archivos.items():
            z.writestr(nombre, contenido)
    return buf.getvalue()


def test_zip_dentro_de_zip_word_y_contenido():
    from core.bases_reales import contenido_zip
    tipo, pdfs = procesar_descarga(_zip(**{"x/BASES.zip": _zip(**{"bases.pdf": crear_pdf()})}))
    assert tipo == "zip" and [n for n, _ in pdfs] == ["bases.pdf"]
    assert procesar_descarga(_zip(**{"word/document.xml": "<w/>"})) == ("docx", [])
    assert contenido_zip(_zip(**{"a.rar": "x", "b.docx": "y", "c.rar": "z"})) == "2 .rar, 1 .docx"


def test_a_galeria_copia_las_mejores_con_catalogo(tmp_path, monkeypatch):
    import bajar_bases_reales as B
    carpeta = tmp_path / "data" / "bases"
    carpeta.mkdir(parents=True)
    filas = []
    for i, reco in enumerate(["observar", "observar", "postular"]):
        (carpeta / f"b{i}.pdf").write_bytes(crear_pdf())
        filas.append({"url": f"u{i}", "archivo": f"b{i}.pdf", "estado": "sirve", "entidad": f"E{i}",
                      "titulo": f"T{i}", "valor_estimado": "1000", "fecha": "2025-01-01", "rubro": "Limpieza"})
    monkeypatch.setattr(B, "RAIZ", tmp_path)
    monkeypatch.setattr(B, "CARPETA", carpeta)
    analisis = pd.DataFrame({"url": ["u0", "u1", "u2"], "recomendacion": ["observar", "observar", "postular"]})
    assert B.a_galeria(pd.DataFrame(filas), analisis, 2) == 2
    cat = pd.read_csv(tmp_path / "ejemplos" / "reales" / "catalogo.csv")
    assert sorted(cat["archivo"]) == ["b0.pdf", "b2.pdf"]          # una de cada recomendación
