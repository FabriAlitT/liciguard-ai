"""Genera unas bases FICTICIAS para pruebas automáticas (no usar como datos reales)."""
import pymupdf as fitz

PAGINAS = [
    "MUNICIPALIDAD DISTRITAL DE EJEMPLO\nBASES INTEGRADAS\nLICITACIÓN PÚBLICA N° 04-2026-MDE/CS\n"
    "ADQUISICIÓN DE UNIFORMES INSTITUCIONALES PARA EL PERSONAL",
    "CAPÍTULO I. GENERALIDADES\n1.1 Objeto de la convocatoria: la adquisición de uniformes institucionales "
    "para el personal administrativo. 1.2 El valor estimado asciende a S/ 812,400.00 (ochocientos doce mil "
    "cuatrocientos con 00/100 soles), incluidos los impuestos de ley. 1.3 La cantidad total requerida es de "
    "2 400 prendas.",
    "2.6 Plazo de entrega. El plazo de entrega es de cinco (5) días calendario contados desde el día "
    "siguiente de suscrito el contrato. La entrega se realizará en el almacén central.\n"
    "3.3 Las muestras se presentarán dentro de las veinticuatro (24) horas siguientes a la convocatoria.",
    "3.1 Especificaciones técnicas. La tela para los uniformes deberá ser de marca TexAndes, modelo Premium "
    "300, sin excepción. El postor deberá consignar la marca y modelo del bien ofertado en su oferta.",
    "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
    "acumulado no menor a S/ 1 600 000,00 por la venta de bienes iguales o similares. El postor debe contar "
    "con inscripción vigente en el Registro Nacional de Proveedores. El postor deberá contar con "
    "certificación ISO 14001 vigente a su nombre.",
    "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 20/10/2026. Formulación de consultas y observaciones: "
    "del 21/10/2026 al 26/10/2026. Presentación de ofertas: 09/11/2026. Otorgamiento de la buena pro: 16/11/2026. "
    "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. "
    "5.2 Penalidades. En caso de retraso se aplica una penalidad por mora hasta un máximo del 10% del "
    "monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los treinta (30) días calendario "
    "siguientes a la conformidad.",
]


def crear_pdf(paginas=PAGINAS) -> bytes:
    doc = fitz.open()
    for texto in paginas:
        p = doc.new_page()
        p.insert_textbox(fitz.Rect(60, 60, 540, 780), texto, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data
