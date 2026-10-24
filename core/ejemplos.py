"""Ejemplos para probar LiciGuard en 1 clic: empresas modelo y bases (ficticias y reales del SEACE).

- EMPRESAS: perfiles listos (uno por rubro) con sus documentos; las fechas se calculan desde hoy para que
  siempre se vean vigentes, por vencer o vencidos.
- bases_disponibles(): junta
    1. las 3 bases FICTICIAS de ejemplos/ (siempre están: sirven para la demo y los jurados),
    2. las bases REALES que pongas en ejemplos/reales/ (se suben a GitHub; las ve la app publicada),
    3. las bases reales que bajaste con bajar_bases_reales.py en data/bases/ (solo en tu computadora).
"""
from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path

from core.fechas import hoy_lima

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_EJEMPLOS = RAIZ / "ejemplos"
CARPETA_REALES = CARPETA_EJEMPLOS / "reales"
CARPETA_DESCARGAS = RAIZ / "data" / "bases"
MAX_MB_GALERIA = 50


# ------------------------------------------------------------------------------------------
# Empresas de ejemplo (ficticias)
# ------------------------------------------------------------------------------------------
EMPRESAS = [
    {"id": "andinas", "tono": "violeta", "ico": "personas", "ciudad": "Cusco",
     "lema": "Confección de uniformes · taller con 6 máquinas",
     "perfil": {"razon_social": "Confecciones Andinas SAC", "rubro": "Uniformes y textiles", "region": "Cusco",
                "experiencia_soles": 320000, "produccion_mensual": 3000, "maquinas": 6, "personal": 8,
                "certificaciones": ["ISO 9001"], "es_mype": True, "rnp_vigente": True},
     "documentos": [("Constancia RNP de bienes", "Constancia RNP", 210), ("Constancia MYPE (REMYPE)", "Constancia MYPE", 400),
                    ("Contrato Gobierno Regional Cusco 2025", "Contrato de experiencia", None),
                    ("Certificado ISO 9001", "Certificado ISO", 18)]},
    {"id": "limpieza", "tono": "cian", "ico": "check", "ciudad": "Arequipa",
     "lema": "Productos de limpieza · distribuidora regional",
     "perfil": {"razon_social": "Limpieza Total del Sur EIRL", "rubro": "Limpieza", "region": "Arequipa",
                "experiencia_soles": 260000, "produccion_mensual": 4000, "maquinas": 2, "personal": 6,
                "certificaciones": [], "es_mype": True, "rnp_vigente": True},
     "documentos": [("Constancia RNP de bienes", "Constancia RNP", 150), ("Constancia MYPE (REMYPE)", "Constancia MYPE", 300),
                    ("Contrato Municipalidad de Cayma 2025", "Contrato de experiencia", None)]},
    {"id": "muebles", "tono": "ambar", "ico": "edificio", "ciudad": "Huancayo",
     "lema": "Mobiliario escolar y de oficina · carpintería",
     "perfil": {"razon_social": "Muebles Huancayo SAC", "rubro": "Mobiliario", "region": "Junín",
                "experiencia_soles": 600000, "produccion_mensual": 900, "maquinas": 10, "personal": 14,
                "certificaciones": ["ISO 9001"], "es_mype": True, "rnp_vigente": True},
     "documentos": [("Constancia RNP de bienes", "Constancia RNP", 90),
                    ("Carta fianza Ugel Huancayo", "Carta fianza", -5)]},
    {"id": "utiles", "tono": "verde", "ico": "libro", "ciudad": "Lima",
     "lema": "Útiles de oficina · distribuidora que recién empieza",
     "perfil": {"razon_social": "Distribuidora Escolar Lima SAC", "rubro": "Útiles de oficina", "region": "Lima",
                "experiencia_soles": 45000, "produccion_mensual": 2000, "maquinas": 0, "personal": 3,
                "certificaciones": [], "es_mype": True, "rnp_vigente": True},
     "documentos": [("Constancia RNP de bienes", "Constancia RNP", 25),
                    ("Constancia MYPE (REMYPE)", "Constancia MYPE", 250)]},
]


def empresa(id_empresa: str) -> dict | None:
    return next((e for e in EMPRESAS if e["id"] == id_empresa), None)


def documentos_de(emp: dict) -> list[dict]:
    """Documentos de la empresa con fechas relativas a hoy (None = sin fecha de vencimiento)."""
    hoy = hoy_lima()
    return [{"nombre": n, "tipo": t, "vence_el": (hoy + timedelta(days=d)).isoformat() if d is not None else None}
            for n, t, d in emp["documentos"]]


# ------------------------------------------------------------------------------------------
# Bases de ejemplo («numeros»: oferta y costos de ejemplo para que «¿Me conviene?» ya tenga cifras)
# ------------------------------------------------------------------------------------------
FICTICIAS = {
    "1_uniformes_observar.pdf": {
        "titulo": "Uniformes institucionales", "entidad": "Ejército Peruano (ficticio)", "valor": 812400,
        "rubro": "Uniformes y textiles", "esperado": "observar", "empresa": "andinas",
        "numeros": {"oferta": 780000.0, "tela": 330000.0, "mano": 150000.0, "otros": 35000.0},
        "que_ver": "Marca exigida, experiencia del doble, entrega en 5 días y muestras en 24 h."},
    "2_limpieza_postular.pdf": {
        "titulo": "Productos de limpieza", "entidad": "Municipalidad de San Isidro (ficticio)", "valor": 186500,
        "rubro": "Limpieza", "esperado": "postular", "empresa": "limpieza",
        "numeros": {"oferta": 179000.0, "tela": 92000.0, "mano": 15000.0, "otros": 6000.0},
        "que_ver": "Bases razonables: acepta marcas equivalentes y retención para MYPE."},
    "3_mobiliario_no_cumples.pdf": {
        "titulo": "Mobiliario escolar", "entidad": "Ministerio de Educación (ficticio)", "valor": 2450000,
        "rubro": "Mobiliario", "esperado": "no_postular", "empresa": "muebles",
        "numeros": {"oferta": 2350000.0, "tela": 1500000.0, "mano": 400000.0, "otros": 120000.0},
        "que_ver": "Piden S/ 2,45 M de experiencia: te mostramos la salida en consorcio."},
    "4_uniformes_postular.pdf": {
        "titulo": "Uniformes para personal de salud", "entidad": "Gobierno Regional del Cusco (ficticio)",
        "valor": 284000, "rubro": "Uniformes y textiles", "esperado": "postular", "empresa": "andinas",
        "numeros": {"oferta": 272000.0, "tela": 120000.0, "mano": 55000.0, "otros": 12000.0},
        "que_ver": "Bases a tu medida: plazo de 45 días, marcas equivalentes y retención MYPE."},
    "5_limpieza_observar.pdf": {
        "titulo": "Desinfectantes hospitalarios", "entidad": "Hospital Regional Honorio Delgado (ficticio)",
        "valor": 238000, "rubro": "Limpieza", "esperado": "observar", "empresa": "limpieza",
        "numeros": {"oferta": 229000.0, "tela": 120000.0, "mano": 18000.0, "otros": 9000.0},
        "que_ver": "Exigen la marca CloroMax y entrega en solo 3 días: conviene observar."},
    "6_mobiliario_postular.pdf": {
        "titulo": "Carpetas unipersonales", "entidad": "UGEL Huancayo (ficticio)", "valor": 420000,
        "rubro": "Mobiliario", "esperado": "postular", "empresa": "muebles",
        "numeros": {"oferta": 405000.0, "tela": 190000.0, "mano": 70000.0, "otros": 15000.0},
        "que_ver": "Contrato a tu medida: 1 200 carpetas en 60 días y experiencia proporcional."},
    "7_utiles_postular.pdf": {
        "titulo": "Útiles de oficina", "entidad": "Municipalidad de Surquillo (ficticio)", "valor": 42000,
        "rubro": "Útiles de oficina", "esperado": "postular", "empresa": "utiles",
        "numeros": {"oferta": 40500.0, "tela": 24000.0, "mano": 1500.0, "otros": 1200.0},
        "que_ver": "Compra pequeña, ideal para empezar a venderle al Estado."},
    "8_utiles_observar.pdf": {
        "titulo": "Papel bond y útiles de escritorio", "entidad": "SUNAT (ficticio)", "valor": 48000,
        "rubro": "Útiles de oficina", "esperado": "observar", "empresa": "utiles",
        "numeros": {"oferta": 46500.0, "tela": 28000.0, "mano": 1500.0, "otros": 1500.0},
        "que_ver": "Exigen papel marca PaperOne, entrega en 5 días e ISO 14001 sin relación."},
}

# La base que abre la demo de cada empresa (la que más enseña: tiene alertas que observar)
DEMO_DE_EMPRESA = {"andinas": "1_uniformes_observar.pdf", "limpieza": "5_limpieza_observar.pdf",
                   "muebles": "3_mobiliario_no_cumples.pdf", "utiles": "8_utiles_observar.pdf"}


def bases_de_rubro(rubro: str | None) -> list[dict]:
    """Bases (ficticias y reales) de un rubro; la de la demo primero."""
    demos = set(DEMO_DE_EMPRESA.values())
    todas = [b for b in bases_disponibles() if not rubro or b.get("rubro") == rubro]
    return sorted(todas, key=lambda b: (b["archivo"] not in demos, b["origen"] != "demo", b["archivo"]))


def empresa_por_razon(razon_social: str | None) -> dict | None:
    return next((e for e in EMPRESAS if e["perfil"]["razon_social"] == razon_social), None)


def _catalogo_csv(carpeta: Path) -> dict[str, dict]:
    """Datos de cada PDF real (entidad, título, valor, enlace) si hay un catalogo.csv o descargas.csv."""
    datos = {}
    for nombre in ("catalogo.csv", "descargas.csv"):
        ruta = carpeta / nombre
        if not ruta.exists():
            continue
        try:
            with open(ruta, encoding="utf-8") as f:
                for fila in csv.DictReader(f):
                    archivo = Path(fila.get("archivo") or "").name
                    if archivo:
                        datos.setdefault(archivo, fila)
        except (OSError, csv.Error, UnicodeDecodeError):
            pass
    return datos


_RUBRO_POR_URL: dict[str, str] | None = None


def _rubro_de_url(url: str) -> str:
    """Para descargas antiguas sin columna rubro: lo busca en data/ocds/historial.csv por su enlace."""
    global _RUBRO_POR_URL
    if not url:
        return ""
    if _RUBRO_POR_URL is None:
        _RUBRO_POR_URL = {}
        ruta = RAIZ / "data" / "ocds" / "historial.csv"
        try:
            with open(ruta, encoding="utf-8") as f:
                for fila in csv.DictReader(f):
                    if fila.get("url"):
                        _RUBRO_POR_URL[fila["url"]] = fila.get("rubro") or ""
        except (OSError, csv.Error, UnicodeDecodeError):
            pass
    return _RUBRO_POR_URL.get(url, "")


def _num(x):
    try:
        return float(str(x).replace(",", "")) if str(x).strip() else None
    except ValueError:
        return None


def _real(ruta: Path, meta: dict, origen: str) -> dict:
    titulo = (meta.get("titulo") or ruta.stem.replace("_", " ")).strip()
    return {"id": f"{origen}:{ruta.name}", "ruta": ruta, "archivo": ruta.name, "origen": origen,
            "titulo": titulo[:90], "entidad": (meta.get("entidad") or "").strip(),
            "valor": _num(meta.get("valor_estimado")), "fecha": (meta.get("fecha") or "")[:10],
            "url": meta.get("url") or "",
            "rubro": (meta.get("rubro") or "").strip() or _rubro_de_url(meta.get("url") or ""), "esperado": None,
            "empresa": None, "que_ver": "Bases reales publicadas en el SEACE.",
            "mb": ruta.stat().st_size / 1e6}


def bases_disponibles() -> list[dict]:
    salida = []
    for nombre, meta in FICTICIAS.items():
        ruta = CARPETA_EJEMPLOS / nombre
        if ruta.exists():
            salida.append({"id": f"demo:{nombre}", "ruta": ruta, "archivo": nombre, "origen": "demo", "fecha": "",
                           "url": "", "mb": ruta.stat().st_size / 1e6, **meta})
    vistos = set()
    for carpeta, origen in ((CARPETA_REALES, "real"), (CARPETA_DESCARGAS, "descargada")):
        if not carpeta.is_dir():
            continue
        catalogo = _catalogo_csv(carpeta)
        for ruta in sorted(carpeta.glob("*.pdf")):
            if ruta.name in vistos or ruta.stat().st_size > MAX_MB_GALERIA * 1e6:
                continue
            vistos.add(ruta.name)
            salida.append(_real(ruta, catalogo.get(ruta.name, {}), origen))
    return salida


def base(id_base: str) -> dict | None:
    return next((b for b in bases_disponibles() if b["id"] == id_base), None)
