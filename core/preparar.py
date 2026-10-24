"""Funciones del notebook de preparación de datos (se pueden probar con pytest).

A) Normativa en PDF  -> data/normativa/articulos.json   (para el buscador de normas)
B) Datos abiertos    -> data/ocds/historial.csv         (para "¿Puedo ganar?")
"""
import csv
import gzip
import json
import re
from pathlib import Path

from core.extraccion import sin_tildes

# ----------------------------------------------------------------------------------------
# A) Normativa
# ----------------------------------------------------------------------------------------
PATRON_ARTICULO = re.compile(r"(?:^|\n)\s*(Art[íi]culo\s+\d+[A-Za-z\-]*)\s*[.\-–:]\s*", re.I)


def texto_pdf(ruta: Path) -> str:
    import pymupdf
    with pymupdf.open(ruta) as doc:
        return "\n".join(p.get_text("text") for p in doc)


def dividir_articulos(texto: str, fuente: str, url: str | None = None, maximo: int = 1800) -> list[dict]:
    """Corta el texto por 'Artículo N.'; si un artículo es muy largo, lo parte en trozos."""
    partes = PATRON_ARTICULO.split(texto)
    articulos = []
    if len(partes) < 3:  # documento sin artículos (bases estándar, opiniones): cortar por bloques
        bloques = [b.strip() for b in re.split(r"\n\s*\n", texto) if len(b.strip()) > 80]
        for i, b in enumerate(bloques, 1):
            articulos.append({"fuente": fuente, "articulo": f"Sección {i}", "titulo": b.split("\n")[0][:120],
                              "texto": re.sub(r"\s+", " ", b)[:maximo], "url": url})
        return articulos
    for i in range(1, len(partes) - 1, 2):
        nombre = re.sub(r"\s+", " ", partes[i]).strip().title().replace("Articulo", "Artículo")
        cuerpo = re.sub(r"\s+", " ", partes[i + 1]).strip()
        titulo = cuerpo.split(".")[0][:120]
        for j in range(0, max(len(cuerpo), 1), maximo):
            articulos.append({"fuente": fuente, "articulo": nombre + (f" (parte {j // maximo + 1})" if j else ""),
                              "titulo": titulo, "texto": cuerpo[j:j + maximo], "url": url})
    return articulos


def preparar_normativa(carpeta: Path, fuentes: dict, salida: Path) -> list[dict]:
    """`fuentes`: {'nombre_archivo.pdf': {'fuente': 'Ley N.° 32069', 'url': '...'}}"""
    todos = []
    for pdf in sorted(carpeta.glob("*.pdf")):
        info = fuentes.get(pdf.name, {"fuente": pdf.stem, "url": None})
        todos += dividir_articulos(texto_pdf(pdf), info["fuente"], info.get("url"))
    salida.write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")
    return todos


# ----------------------------------------------------------------------------------------
# B) Datos abiertos (OCDS, archivos .jsonl.gz del Open Contracting Data Registry)
# ----------------------------------------------------------------------------------------
COLUMNAS = ["ocid", "fecha", "entidad", "titulo", "valor_estimado", "n_postores", "ganador",
            "monto_adjudicado", "url"]


def _releases(linea: dict):
    """Acepta compiled releases, records o paquetes de releases."""
    if "compiledRelease" in linea:
        yield linea["compiledRelease"]
    elif "releases" in linea and isinstance(linea["releases"], list):
        yield from linea["releases"]
    elif "records" in linea:
        for rec in linea["records"]:
            if "compiledRelease" in rec:
                yield rec["compiledRelease"]
    else:
        yield linea


def fila_historial(rel: dict) -> dict:
    tender = rel.get("tender") or {}
    awards = rel.get("awards") or []
    activos = [a for a in awards if (a.get("status") or "active") in ("active", "")] or awards
    ganadores = [s.get("name") for a in activos for s in (a.get("suppliers") or []) if s.get("name")]
    monto = sum(((a.get("value") or {}).get("amount") or 0) for a in activos) or None
    n_post = tender.get("numberOfTenderers")
    if n_post is None and tender.get("tenderers") is not None:
        n_post = len(tender["tenderers"])
    if n_post is None:
        n_post = sum("tenderer" in (p.get("roles") or []) for p in rel.get("parties") or []) or None
    docs = tender.get("documents") or []
    return {
        "ocid": rel.get("ocid"),
        "fecha": ((tender.get("tenderPeriod") or {}).get("startDate") or rel.get("date") or "")[:10],
        "entidad": (rel.get("buyer") or {}).get("name"),
        "titulo": " ".join(x for x in [tender.get("title"), tender.get("description")] if x)[:300],
        "valor_estimado": (tender.get("value") or {}).get("amount"),
        "n_postores": n_post,
        "ganador": " / ".join(dict.fromkeys(ganadores)) or None,
        "monto_adjudicado": monto,
        "url": docs[0].get("url") if docs else None,
    }


def _coincide(texto: str, palabras: list[str]) -> bool:
    t = sin_tildes((texto or "").lower())
    return any(p in t for p in palabras)


def preparar_historial(archivos: list[Path], palabras: list[str], salida: Path,
                       entidades: list[str] | None = None, limite_lineas: int | None = None,
                       cada: int = 200_000) -> int:
    """Lee los .jsonl.gz línea por línea (sin cargarlos enteros en memoria) y guarda solo lo útil."""
    palabras = [sin_tildes(p.lower()) for p in palabras]
    entidades = [sin_tildes(e.lower()) for e in (entidades or [])]
    guardadas = 0
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for archivo in archivos:
            abrir = gzip.open if str(archivo).endswith(".gz") else open
            with abrir(archivo, "rt", encoding="utf-8") as entrada:
                for n, linea in enumerate(entrada, 1):
                    if limite_lineas and n > limite_lineas:
                        break
                    if cada and n % cada == 0:
                        print(f"  {archivo.name}: {n:,} líneas leídas · {guardadas:,} guardadas")
                    try:
                        obj = json.loads(linea)
                    except json.JSONDecodeError:
                        continue
                    for rel in _releases(obj):
                        fila = fila_historial(rel)
                        if not fila["ganador"] or not _coincide(fila["titulo"], palabras):
                            continue
                        if entidades and not _coincide(fila["entidad"], entidades):
                            continue
                        w.writerow(fila)
                        guardadas += 1
    return guardadas
