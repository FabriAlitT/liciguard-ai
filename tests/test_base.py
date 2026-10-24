import pymupdf as fitz

from core.db import RepoMemoria
from core.pdf_parser import extraer_paginas, huella, imagen_pagina_resaltada, paginas_sin_texto
from core.usuarios import base_desde_nombre, generar_codigo, normalizar_codigo


def _pdf_de_prueba() -> bytes:
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((72, 72), "La tela debera ser de marca TexAndes, sin excepcion.")
    doc.new_page()  # página vacía (como si fuera escaneada)
    data = doc.tobytes()
    doc.close()
    return data


def test_normalizar_codigo():
    assert normalizar_codigo("  Rosa-Quispe-4821 ") == "rosa-quispe-4821"
    assert normalizar_codigo("José Ñuñez") == "jose-nunez"


def test_base_desde_nombre():
    assert base_desde_nombre("María Rosa Quispe") == "maria-rosa"
    assert base_desde_nombre("!!!") == "usuario"


def test_codigo_unico_evita_repetidos():
    repo = RepoMemoria()
    c1 = generar_codigo("Rosa Quispe", repo.existe_codigo)
    repo.crear_usuario(c1, "Rosa Quispe")
    c2 = generar_codigo("Rosa Quispe", repo.existe_codigo)
    sufijo = c1.split("-")[-1]
    assert c1 != c2 and c1.startswith("rosa-quispe-") and len(sufijo) == 6
    assert normalizar_codigo(c1) == c1  # el código generado pasa el filtro de la base (^[a-z0-9-]{3,40}$)


def test_historial_por_usuario_y_por_empresa():
    repo = RepoMemoria()
    ea = repo.crear_empresa("a", {"razon_social": "A1"})["id"]
    ea2 = repo.crear_empresa("a", {"razon_social": "A2"})["id"]
    eb = repo.crear_empresa("b", {"razon_social": "B1"})["id"]
    repo.guardar_analisis("a", ea, {"nombre_archivo": "x.pdf", "sha256": "1"})
    repo.guardar_analisis("a", ea2, {"nombre_archivo": "x.pdf", "sha256": "1"})   # mismo PDF, otra empresa
    repo.guardar_analisis("b", eb, {"nombre_archivo": "y.pdf", "sha256": "2"})
    assert [f["nombre_archivo"] for f in repo.listar_analisis("a", ea)] == ["x.pdf"]
    assert len(repo.listar_analisis("a", ea2)) == 1 and repo.listar_analisis("a", eb) == []
    assert [e["razon_social"] for e in repo.listar_empresas("a")] == ["A1", "A2"]
    assert repo.obtener_empresa("b", ea) is None                                 # no ve empresas ajenas
    repo.agregar_documento("a", ea2, "RNP", "Constancia RNP", None)
    repo.guardar_seguimiento("a", ea2, {"sha256": "1", "etapa": "Revisada"})
    repo.borrar_empresa("a", ea2)                                                # borra lo suyo en cascada
    assert repo.listar_documentos("a", ea2) == [] and repo.listar_seguimiento("a", ea2) == []
    assert len(repo.listar_analisis("a", ea)) == 1


def test_pdf_paginas_y_resaltado():
    data = _pdf_de_prueba()
    paginas = extraer_paginas(data)
    assert len(paginas) == 2 and "TexAndes" in paginas[0]["texto"]
    assert paginas_sin_texto(paginas) == [2]
    assert len(huella(data)) == 64
    png = imagen_pagina_resaltada(data, 1, "marca TexAndes")
    assert png[:4] == b"\x89PNG"
