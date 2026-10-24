"""'¿Puedo ganar?': procesos anteriores parecidos, desde los datos abiertos.

El cuaderno 02_historial_ocds genera data/ocds/historial.csv con estas columnas:
  ocid, fecha, rubro, entidad, titulo, valor_estimado, n_postores, ganador, monto_adjudicado, url

Puede tener cientos de miles de filas (varios rubros y años), por eso se carga con pandas
y primero se filtra por entidad (rápido, vectorizado) y luego por parecido del objeto.
"""
import re
from collections import Counter

from core.config import ARCHIVO_HISTORIAL
from core.extraccion import sin_tildes

GENERICAS = set("""adquisicion contratacion suministro servicio servicios bienes para del de la las los el
y en con por municipalidad distrital provincial gobierno regional ministerio hospital nacional
institucional institucionales unidad ejecutora""".split())


def _norm(texto) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", sin_tildes(str(texto or "").lower()))


def _claves(texto) -> set[str]:
    return {w for w in _norm(texto).split() if len(w) > 3 and w not in GENERICAS}


def cargar_historial(ruta=ARCHIVO_HISTORIAL):
    """Devuelve un DataFrame (vacío si no existe el archivo)."""
    import pandas as pd
    try:
        df = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    except FileNotFoundError:
        return pd.DataFrame()
    if len(df):
        df["_entidad"] = df["entidad"].map(_norm)
    return df


def _como_df(historial):
    import pandas as pd
    if isinstance(historial, pd.DataFrame):
        return historial
    df = pd.DataFrame(list(historial or []))
    if len(df):
        df["_entidad"] = df["entidad"].map(_norm)
    return df


def procesos_parecidos(historial, entidad: str | None, objeto: str | None, limite: int = 8) -> list[dict]:
    """Mismo comprador (palabras del nombre) y objeto parecido (palabras clave)."""
    df = _como_df(historial)
    ent, obj = _claves(entidad), _claves(objeto)
    if not len(df) or not obj or not ent:
        return []
    # 1) Filtro rápido por entidad: al menos la mitad de sus palabras clave
    coincidencias = sum(df["_entidad"].str.contains(rf"\b{re.escape(t)}\b", regex=True) for t in ent)
    candidatos = df[coincidencias >= max(1, len(ent) // 2)]
    # 2) Parecido del objeto
    resultado = []
    for fila in candidatos.to_dict("records"):
        comun = len(obj & _claves(fila.get("titulo")))
        if comun:
            fila.pop("_entidad", None)
            resultado.append({**fila, "_parecido": comun})
    resultado.sort(key=lambda f: (f["_parecido"], f.get("fecha", "")), reverse=True)
    return resultado[:limite]


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


SUFIJOS = [(r"\bsociedad anonima cerrada\b", "sac"), (r"\bs\s*a\s*c\b", "sac"),
           (r"\bempresa individual de responsabilidad limitada\b", "eirl"), (r"\be\s*i\s*r\s*l\b", "eirl"),
           (r"\bsociedad comercial de responsabilidad limitada\b", "srl"), (r"\bs\s*r\s*l\b", "srl"),
           (r"\bsociedad anonima\b", "sa"), (r"\bs\s*a\b", "sa")]


def clave_proveedor(nombre) -> str:
    """'INDUSTRIA ESTRELLA AZUL E.I.R.L.' y 'Industria Estrella Azul EIRL' -> la misma clave."""
    t = re.sub(r"[^a-z0-9 ]", " ", sin_tildes(str(nombre or "").lower()))
    for patron, corto in SUFIJOS:
        t = re.sub(patron, corto, t)
    return re.sub(r"\s+", " ", t).strip()


def resumen(procesos: list[dict]) -> dict:
    """Ojo: en los datos abiertos de Perú 'n_postores' cuenta PARTICIPANTES registrados, no ofertas."""
    if not procesos:
        return {"n": 0}
    nombres, ganadores = {}, Counter()
    for p in procesos:
        if p.get("ganador"):
            k = clave_proveedor(p["ganador"])
            ganadores[k] += 1
            nombres.setdefault(k, p["ganador"])
    postores = [_num(p.get("n_postores")) for p in procesos if _num(p.get("n_postores")) is not None]
    ratios = [_num(p.get("monto_adjudicado")) / _num(p.get("valor_estimado")) for p in procesos
              if _num(p.get("monto_adjudicado")) and _num(p.get("valor_estimado"))]
    top, veces = ganadores.most_common(1)[0] if ganadores else (None, 0)
    top = nombres.get(top, top)
    return {
        "n": len(procesos),
        "ganador_frecuente": top,
        "veces_ganador": veces,
        "share_ganador": veces / len(procesos),
        "promedio_participantes": sum(postores) / len(postores) if postores else None,
        "distintos_ganadores": len(ganadores),
        "ratio_min": min(ratios) if ratios else None,
        "ratio_max": max(ratios) if ratios else None,
    }
