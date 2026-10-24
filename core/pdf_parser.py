"""Lectura de las bases en PDF, página por página (PyMuPDF)."""
import hashlib

import pymupdf as fitz  # PyMuPDF

TAMANO_MAXIMO_MB = 50   # igual que maxUploadSize en .streamlit/config.toml
MINIMO_CARACTERES_POR_PAGINA = 40


class PDFInvalido(Exception):
    pass


def huella(data: bytes) -> str:
    """SHA-256 del archivo: sirve para detectar duplicados."""
    return hashlib.sha256(data).hexdigest()


def extraer_paginas(data: bytes) -> list[dict]:
    """Devuelve [{'pagina': 1, 'texto': '...'}, ...] (páginas numeradas desde 1)."""
    if len(data) > TAMANO_MAXIMO_MB * 1024 * 1024:
        raise PDFInvalido(f"El archivo supera {TAMANO_MAXIMO_MB} MB.")
    if not data.startswith(b"%PDF"):
        raise PDFInvalido("El archivo no parece un PDF.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:  # PDF dañado
        raise PDFInvalido(f"No se pudo abrir el PDF: {e}") from e
    with doc:
        if doc.needs_pass:
            raise PDFInvalido("El PDF tiene contraseña.")
        return [{"pagina": i + 1, "texto": p.get_text("text")} for i, p in enumerate(doc)]


def paginas_sin_texto(paginas: list[dict]) -> list[int]:
    """Páginas que parecen escaneadas (casi sin texto). Necesitarían OCR."""
    return [p["pagina"] for p in paginas if len(p["texto"].strip()) < MINIMO_CARACTERES_POR_PAGINA]


def imagen_pagina_resaltada(data: bytes, pagina: int, cita: str | None = None, dpi: int = 130) -> bytes:
    """PNG de una página; si hay `cita`, la resalta en amarillo (para el visor de pruebas)."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        page = doc[pagina - 1]
        if cita:
            for rect in page.search_for(cita.strip()[:200]):
                page.add_highlight_annot(rect)
        return page.get_pixmap(dpi=dpi).tobytes("png")
