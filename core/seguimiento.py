"""Seguimiento de cada licitación: etapa, fechas, checklist y aprendizaje del resultado."""
from datetime import date

from core.fechas import hoy_lima

ETAPAS = ["Revisada", "Observada", "Ofertada", "Ganada", "Perdida", "Descartada"]
COLOR_ETAPA = {"Revisada": "#2C7FD0", "Observada": "#E59A12", "Ofertada": "#6A55D8",
               "Ganada": "#1F9D6B", "Perdida": "#DB4F77", "Descartada": "#98A2B3"}

DOCUMENTOS_BASE = [
    ("rnp", "Constancia RNP vigente"),
    ("dj", "Declaraciones juradas y anexos"),
    ("ficha", "Ficha técnica / especificaciones del bien ofertado"),
    ("precio", "Oferta económica firmada"),
]


def checklist(res: dict) -> list[tuple[str, str]]:
    """Lista de lo que hay que preparar, según lo que piden las bases."""
    cats = {r["categoria"] for r in res.get("requisitos", [])}
    items = list(DOCUMENTOS_BASE)
    if "experiencia" in cats:
        items.append(("exp", "Contratos y conformidades que acrediten tu experiencia"))
    if "certificacion" in cats:
        items.append(("iso", "Certificados ISO solicitados (vigentes)"))
    if "muestras" in cats:
        items.append(("muestras", "Muestras del bien, rotuladas"))
    if "garantia" in cats or "retencion_mype" in cats:
        items.append(("garantia", "Carta fianza o solicitud de retención (MYPE)"))
    return items


def nuevo(sha: str, res: dict, nombre: str) -> dict:
    cron = res.get("cronograma", {})
    d = res.get("datos", {})
    return {
        "sha256": sha, "nombre": (d.get("objeto") or nombre or "Licitación")[:120], "entidad": d.get("entidad"),
        "valor_estimado": d.get("valor_estimado"), "recomendacion": res.get("recomendacion", {}).get("codigo"),
        "etapa": "Revisada",
        "fecha_observaciones": (cron.get("observaciones") or {}).get("fecha"),
        "fecha_ofertas": (cron.get("ofertas") or {}).get("fecha"),
        "fecha_buena_pro": (cron.get("buena_pro") or {}).get("fecha"),
        "mi_oferta": None, "oferta_ganadora": None, "ganador": None, "checklist": {}, "notas": "",
    }


def dias_hasta(fecha_iso) -> int | None:
    if not fecha_iso:
        return None
    try:
        return (date.fromisoformat(str(fecha_iso)[:10]) - hoy_lima()).days
    except ValueError:
        return None


def proximos_plazos(seguimientos: list[dict], dias: int = 10) -> list[dict]:
    """Plazos que vencen pronto en procesos activos (para el Inicio)."""
    nombres = {"fecha_observaciones": "Último día para observar", "fecha_ofertas": "Presentar oferta",
               "fecha_buena_pro": "Resultado (buena pro)"}
    salida = []
    for s in seguimientos:
        if s.get("etapa") in ("Ganada", "Perdida", "Descartada"):
            continue
        for campo, texto in nombres.items():
            n = dias_hasta(s.get(campo))
            if n is not None and 0 <= n <= dias:
                salida.append({"proceso": s.get("nombre"), "que": texto, "fecha": s.get(campo), "dias": n,
                               "sha256": s.get("sha256")})
    return sorted(salida, key=lambda x: x["dias"])


def aprendizaje(seg: dict) -> dict | None:
    """Si perdiste: ¿por cuánto? Compara tu oferta con la ganadora y el valor estimado."""
    mi, gan, ve = seg.get("mi_oferta"), seg.get("oferta_ganadora"), seg.get("valor_estimado")
    if not mi or not gan:
        return None
    dif = mi - gan
    return {"diferencia": dif, "pct": dif / gan * 100,
            "mi_ratio": mi / ve if ve else None, "gan_ratio": gan / ve if ve else None}


def rnp_segun_documentos(documentos: list[dict]) -> bool | None:
    """¿El RNP está vigente según «Mis documentos»?

    True  -> hay una «Constancia RNP» con fecha de vencimiento futura.
    False -> todas las constancias RNP con fecha ya vencieron.
    None  -> no hay constancias RNP con fecha (sin fecha no se puede saber: manda lo marcado en el perfil).
    """
    fechas = [dias_hasta(d.get("vence_el")) for d in documentos or []
              if (d.get("tipo") or "").strip().lower() == "constancia rnp"]
    fechas = [n for n in fechas if n is not None]
    if not fechas:
        return None
    return any(n >= 0 for n in fechas)


def perfil_efectivo(perfil: dict | None, documentos: list[dict]) -> dict | None:
    """Perfil para evaluar «¿Puedo?»: si hay constancia RNP en los documentos, su vigencia manda."""
    if not perfil:
        return perfil
    segun_docs = rnp_segun_documentos(documentos)
    return {**perfil, "rnp_vigente": segun_docs} if segun_docs is not None else perfil
