"""Conseguir bases REALES para probar LiciGuard (lo usa notebooks/04_bajar_bases_reales.ipynb).

Cada proceso de data/ocds/historial.csv trae en la columna `url` el primer documento publicado en el SEACE
(normalmente las bases o las bases integradas). Aquí se elige una muestra variada de procesos, se descargan
esos documentos con calma (sin saturar el SEACE) y se revisa cuáles sirven: PDF con texto que parezcan bases.

Solo se usa la biblioteca estándar (urllib) para no sumar dependencias.
"""
import io
import re
import time
import urllib.request
import zipfile

TAMANO_MAXIMO = 50 * 1024 * 1024        # lo que la app acepta (ver core/pdf_parser.py y .streamlit/config.toml)
TAMANO_DESCARGA = 80 * 1024 * 1024      # un ZIP puede pesar más que el PDF que trae dentro
AGENTE = "Mozilla/5.0 (LiciGuard; pruebas académicas con datos abiertos)"
PARECE_BASES = re.compile(r"\bbases\b|requerimiento|t[ée]rminos de referencia|especificaciones t[ée]cnicas", re.I)


class ArchivoMuyGrande(Exception):
    pass


def elegir_procesos(df, rubro=None, desde="2024", cuantos=30, max_por_entidad=2, semilla=7):
    """Muestra variada: procesos recientes del rubro, como máximo `max_por_entidad` por entidad."""
    d = df[df["url"].fillna("").str.startswith("http")]
    if rubro:
        d = d[d["rubro"] == rubro]
    if desde:
        d = d[d["fecha"].fillna("").str[:4] >= str(desde)]
    d = d.sample(frac=1, random_state=semilla)                      # mezcla para no tomar siempre los mismos
    d = d.groupby("entidad", group_keys=False).head(max_por_entidad)
    return d.head(cuantos).reset_index(drop=True)


def tipo_de_archivo(data: bytes) -> str:
    """Reconoce el archivo por sus primeros bytes (el nombre o la extensión pueden mentir)."""
    cabeza = data[:8]
    if cabeza.startswith(b"%PDF"):
        return "pdf"
    if cabeza.startswith(b"PK"):
        return "zip"
    if cabeza.startswith(b"Rar!"):
        return "rar"
    if cabeza.startswith(b"\xd0\xcf\x11\xe0"):
        return "doc"
    if data[:200].lstrip().lower().startswith((b"<!doctype", b"<html")):
        return "html"
    return "otro"


def pdfs_de_zip(data: bytes, nivel: int = 0) -> list[tuple[str, bytes]]:
    """Saca los PDF que vienen dentro de un ZIP, también de un ZIP dentro de otro (muchas entidades publican así)."""
    salida = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            nombre = info.filename.lower()
            if nombre.endswith(".pdf") and 0 < info.file_size <= TAMANO_MAXIMO:
                salida.append((info.filename.rsplit("/", 1)[-1], z.read(info)))
            elif nombre.endswith(".zip") and nivel < 2 and info.file_size <= TAMANO_DESCARGA:
                try:
                    salida += pdfs_de_zip(z.read(info), nivel + 1)
                except zipfile.BadZipFile:
                    pass
    # primero los que dicen "bases" en el nombre
    return sorted(salida, key=lambda x: "base" not in x[0].lower())


def contenido_zip(data: bytes) -> str:
    """Qué trae un ZIP sin PDF (para explicar por qué no sirvió): p. ej. '2 .rar, 1 .docx'."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            ext = [n.rsplit(".", 1)[-1].lower() for n in z.namelist() if "." in n.rsplit("/", 1)[-1]]
    except zipfile.BadZipFile:
        return "ZIP dañado"
    cuenta = {e: ext.count(e) for e in dict.fromkeys(ext)}
    return ", ".join(f"{n} .{e}" for e, n in cuenta.items()) or "ZIP vacío"


def es_docx(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return "word/document.xml" in z.namelist()
    except zipfile.BadZipFile:
        return False


def revisar_pdf(data: bytes) -> dict:
    """¿Sirve para probar? Cuenta páginas con texto y busca palabras típicas de unas bases."""
    import pymupdf
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            textos = [p.get_text("text") for p in doc]
    except Exception as e:  # PDF dañado o con contraseña
        return {"paginas": 0, "con_texto": 0.0, "parece_bases": False, "motivo": f"no se pudo abrir ({e})"}
    con_texto = sum(len(t.strip()) >= 40 for t in textos) / len(textos) if textos else 0.0
    parece = bool(PARECE_BASES.search(" ".join(textos[:4])))
    motivo = ("escaneado (sin texto): necesitaría OCR" if con_texto < 0.5 else
              "no parece unas bases" if not parece else "sirve")
    return {"paginas": len(textos), "con_texto": round(con_texto, 2), "parece_bases": parece, "motivo": motivo}


def descargar(url: str, intentos: int = 2, pausa: float = 2.0, timeout: int = 60) -> bytes:
    """Descarga con un User-Agent identificable, reintentos y pausa (para no saturar el SEACE)."""
    ultimo = None
    for i in range(intentos + 1):
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(pedido, timeout=timeout) as r:
                data = r.read(TAMANO_DESCARGA + 1)
            if len(data) > TAMANO_DESCARGA:
                raise ArchivoMuyGrande(f"el archivo supera {TAMANO_DESCARGA // 2**20} MB")
            return data
        except ArchivoMuyGrande:
            raise                               # no tiene sentido reintentar
        except Exception as e:
            ultimo = e
            time.sleep(pausa * (i + 1))
    raise ultimo


def procesar_descarga(data: bytes) -> tuple[str, list[tuple[str, bytes]]]:
    """Devuelve (tipo, [(nombre, pdf_bytes), ...]) listo para guardar."""
    tipo = tipo_de_archivo(data)
    if tipo == "pdf":
        return tipo, [("bases.pdf", data)]
    if tipo == "zip":
        if es_docx(data):
            return "docx", []
        try:
            return tipo, pdfs_de_zip(data)
        except zipfile.BadZipFile:
            return "zip dañado", []
    return tipo, []
