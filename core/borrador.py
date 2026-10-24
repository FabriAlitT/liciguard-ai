"""Borrador de observación a las bases (plantilla, sin IA). Siempre requiere revisión humana."""
import io

from core.fechas import hoy_lima

PEDIDOS = {
    "marca": "Solicitamos que se admitan bienes de características técnicas equivalentes, sin restringir el requerimiento a una marca determinada.",
    "experiencia": "Solicitamos que el monto de experiencia exigido se ajuste a lo previsto en las bases estándar aplicables, de modo que guarde proporción con el valor estimado.",
    "plazo": "Solicitamos ampliar el plazo de entrega a uno razonable para la fabricación de los bienes, a fin de no limitar la concurrencia de postores.",
    "certificacion": "Solicitamos retirar esta certificación como requisito de calificación o sustentar su relación con el objeto de la contratación.",
    "muestras": "Solicitamos ampliar el plazo para la presentación de muestras.",
}


def _tipo(h):
    t = h["titulo"].lower()
    for clave in ("marca", "experiencia", "muestras"):
        if clave in t:
            return clave
    if "entrega" in t:
        return "plazo"
    if "iso" in t:
        return "certificacion"
    return None


def crear_borrador(res: dict, hallazgos: list[dict], empresa: str, representante: str = "[Representante legal]",
                   ciudad: str | None = None) -> str:
    d = res["datos"]
    proc = " ".join(x for x in [d.get("procedimiento"), f"N.° {d['nomenclatura']}" if d.get("nomenclatura") else None] if x)
    lineas = [
        f"{(ciudad or '').strip().title() or 'Lima'}, {hoy_lima():%d/%m/%Y}",
        "",
        "Señores del Comité",
        f"{d.get('entidad') or '[Entidad]'}",
        "",
        f"Asunto: Observaciones a las bases de la {proc or '[procedimiento]'}",
        f"Objeto: {d.get('objeto') or '[objeto de la convocatoria]'}",
        "",
        f"{empresa}, en calidad de participante, formula las siguientes observaciones:",
        "",
    ]
    for i, h in enumerate(hallazgos, 1):
        normas = h.get("normas") or []
        base_legal = (f"{normas[0].get('fuente', '')} {normas[0].get('articulo', '')}".strip()
                      if normas else "[artículo por confirmar]")
        lineas += [
            f"Observación N.° {i}: {h['titulo']} (página {h['pagina']} de las bases)",
            f"Texto de las bases: «{h['cita']}»",
            PEDIDOS.get(_tipo(h), "Solicitamos revisar esta condición."),
            f"Base legal referida: {base_legal} [verificar antes de presentar]",
            "",
        ]
    lineas += ["Atentamente,", "", representante, empresa,
               "", "— Borrador generado por LiciGuard. Revísalo y confírmalo antes de presentarlo por el canal oficial."]
    return "\n".join(lineas)


def a_word(texto: str) -> bytes:
    from docx import Document
    doc = Document()
    for linea in texto.split("\n"):
        doc.add_paragraph(linea)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
