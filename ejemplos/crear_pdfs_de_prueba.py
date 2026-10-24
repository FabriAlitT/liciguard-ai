"""Ocho bases FICTICIAS (dos por rubro) para probar LiciGuard (una por cada recomendación).

Uso:  python ejemplos/crear_pdfs_de_prueba.py        (crea los PDF en la carpeta ejemplos/)
Perfil sugerido en Mi empresa: rubro "Uniformes y textiles", experiencia 320 000, producción 3 000 al mes,
6 máquinas, 8 personas, MYPE, RNP vigente.
  1_uniformes_observar.pdf      -> Observar primero (marca, experiencia 2x, 5 días, ISO 14001, muestras 24 h)
  2_limpieza_postular.pdf       -> Postular (condiciones razonables, retención MYPE)
  3_mobiliario_no_cumples.pdf   -> No te conviene (piden S/ 2,45 M de experiencia: salida consorcio)
  4_uniformes_postular.pdf      -> Postular (Confecciones Andinas)
  5_limpieza_observar.pdf       -> Observar primero (marca exigida, entrega en 3 días)
  6_mobiliario_postular.pdf     -> Postular (Muebles Huancayo)
  7_utiles_sin_rnp.pdf          -> No te conviene hoy: falta el RNP (Distribuidora Escolar)
  8_utiles_observar.pdf         -> Observar primero (marca exigida y experiencia del doble)
"""
import sys

import pymupdf as fitz

AVISO = "EJEMPLO FICTICIO PARA PROBAR LICIGUARD - NO ES UN DOCUMENTO OFICIAL"


def portada(entidad, numero, objeto):
    return (f"{entidad}\nBASES INTEGRADAS\nLICITACIÓN PÚBLICA N° {numero}\n{objeto}\n\n"
            "Procedimiento de selección regido por la Ley N° 32069, Ley General de Contrataciones Públicas, "
            "y su Reglamento aprobado por D.S. N° 009-2025-EF.")


CASOS = {
    # 1) Observar primero: marca, experiencia 2x, plazo corto, ISO sin relación, muestras en 24 h
    "1_uniformes_observar.pdf": [
        portada("EJERCITO PERUANO", "04-2026-MDE/CS", "ADQUISICIÓN DE UNIFORMES INSTITUCIONALES PARA EL PERSONAL ADMINISTRATIVO"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: Ejercito Peruano.\n1.2 Objeto de la convocatoria: la "
        "adquisición de uniformes institucionales para el personal administrativo. 1.3 El valor estimado asciende a "
        "S/ 812,400.00 (ochocientos doce mil cuatrocientos con 00/100 soles), incluidos los impuestos de ley. "
        "La cantidad total requerida es de 2 400 prendas.\n"
        "1.4 Sistema de contratación: suma alzada.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de cinco (5) días calendario "
        "contados desde el día siguiente de suscrito el contrato. La entrega se realizará en el almacén central.\n"
        "3.3 Las muestras se presentarán dentro de las veinticuatro (24) horas siguientes a la convocatoria.",
        "CAPÍTULO III. REQUERIMIENTO\n3.1 Especificaciones técnicas. La tela para los uniformes deberá ser de marca "
        "TexAndes, modelo Premium 300, sin excepción. El postor deberá consignar la marca y modelo del bien ofertado "
        "en su oferta.\n3.2 Tallas: según cuadro de distribución del Anexo 1.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 1 600 000,00 por la venta de bienes iguales o similares. El postor debe contar "
        "con inscripción vigente en el Registro Nacional de Proveedores. El postor deberá contar con "
        "certificación ISO 14001 vigente a su nombre.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 22/10/2026. Formulación de consultas y observaciones: "
        "del 23/10/2026 al 30/10/2026. Presentación de ofertas: 16/11/2026. Otorgamiento de la buena pro: 23/11/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. "
        "5.2 Penalidades. En caso de retraso se aplica una penalidad por mora hasta un máximo del 10% del "
        "monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los treinta (30) días calendario "
        "siguientes a la conformidad.",
    ],
    # 2) Postular: condiciones razonables y experiencia proporcional
    "2_limpieza_postular.pdf": [
        portada("MUNICIPALIDAD DISTRITAL DE SAN ISIDRO", "12-2026-MDSI/CS", "ADQUISICIÓN DE PRODUCTOS DE LIMPIEZA PARA LAS SEDES MUNICIPALES"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: Municipalidad Distrital de San Isidro.\n1.2 Objeto de la "
        "convocatoria: la adquisición de productos de limpieza para las sedes municipales. 1.3 El valor estimado "
        "asciende a S/ 186,500.00 (ciento ochenta y seis mil quinientos con 00/100 soles). La cantidad total "
        "requerida es de 2 500 unidades.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de treinta (30) días calendario "
        "contados desde el día siguiente de suscrito el contrato, en tres entregas parciales.\n"
        "3.1 Especificaciones técnicas. Los productos deberán cumplir la norma técnica peruana aplicable. "
        "Se aceptan marcas equivalentes que cumplan las características técnicas.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 180 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 26/10/2026. Formulación de consultas y observaciones: "
        "del 27/10/2026 al 03/11/2026. Presentación de ofertas: 20/11/2026. Otorgamiento de la buena pro: 27/11/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. Las MYPE "
        "pueden optar por la retención del 10% del monto del contrato. 5.2 Penalidades. Penalidad por mora hasta un "
        "máximo del 10% del monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los quince (15) "
        "días calendario siguientes a la conformidad.",
    ],
    # 3) No te conviene hoy: contrato grande, piden más experiencia de la que tienes (salida: consorcio)
    "3_mobiliario_no_cumples.pdf": [
        portada("MINISTERIO DE EDUCACION", "07-2026-MINEDU/UE", "ADQUISICIÓN DE MOBILIARIO ESCOLAR PARA INSTITUCIONES EDUCATIVAS"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: Ministerio de Educacion.\n1.2 Objeto de la convocatoria: "
        "la adquisición de mobiliario escolar para instituciones educativas. 1.3 El valor estimado asciende a "
        "S/ 2,450,000.00 (dos millones cuatrocientos cincuenta mil con 00/100 soles). La cantidad total requerida "
        "es de 4 800 carpetas.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de sesenta (60) días calendario "
        "contados desde el día siguiente de suscrito el contrato.\n3.1 Especificaciones técnicas según fichas del Anexo 2.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 2 450 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores. Se permite la participación en consorcio.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 27/10/2026. Formulación de consultas y observaciones: "
        "del 28/10/2026 al 04/11/2026. Presentación de ofertas: 24/11/2026. Otorgamiento de la buena pro: 01/12/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. "
        "5.2 Penalidades. Penalidad por mora hasta un máximo del 10% del monto del contrato. 5.3 Forma de pago. "
        "El pago se realizará dentro de los treinta (30) días calendario siguientes a la conformidad.",
    ],

    # 4) Uniformes · Postular: monto razonable, plazo holgado, acepta marcas equivalentes
    "4_uniformes_postular.pdf": [
        portada("GOBIERNO REGIONAL DEL CUSCO", "09-2026-GRC/CS", "ADQUISICIÓN DE UNIFORMES PARA EL PERSONAL DE SALUD"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: Gobierno Regional del Cusco.\n1.2 Objeto de la convocatoria: "
        "la adquisición de uniformes para el personal de salud. 1.3 El valor estimado asciende a S/ 284,000.00 "
        "(doscientos ochenta y cuatro mil con 00/100 soles). La cantidad total requerida es de 1 200 prendas.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de cuarenta y cinco (45) días "
        "calendario contados desde el día siguiente de suscrito el contrato.\n3.1 Especificaciones técnicas. Tela "
        "drill de algodón 65/35 o equivalente. Se aceptan marcas equivalentes que cumplan las características técnicas.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 250 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 28/10/2026. Formulación de consultas y observaciones: "
        "del 29/10/2026 al 05/11/2026. Presentación de ofertas: 25/11/2026. Otorgamiento de la buena pro: 02/12/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. Las MYPE "
        "pueden optar por la retención del 10% del monto del contrato. 5.2 Penalidades. Penalidad por mora hasta un "
        "máximo del 10% del monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los quince (15) "
        "días calendario siguientes a la conformidad.",
    ],
    # 5) Limpieza · Observar primero: marca exigida y entrega en 3 días
    "5_limpieza_observar.pdf": [
        portada("HOSPITAL REGIONAL HONORIO DELGADO", "15-2026-HRHD/CS", "ADQUISICIÓN DE DESINFECTANTES Y PRODUCTOS DE LIMPIEZA HOSPITALARIA"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: Hospital Regional Honorio Delgado.\n1.2 Objeto de la "
        "convocatoria: la adquisición de desinfectantes y productos de limpieza hospitalaria. 1.3 El valor estimado "
        "asciende a S/ 238,000.00 (doscientos treinta y ocho mil con 00/100 soles). La cantidad total requerida es "
        "de 3 000 unidades.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de tres (3) días calendario "
        "contados desde el día siguiente de suscrito el contrato.\n3.1 Especificaciones técnicas. El desinfectante "
        "deberá ser de marca CloroMax, modelo Hospitalario 5L, sin excepción.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 220 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 27/10/2026. Formulación de consultas y observaciones: "
        "del 28/10/2026 al 04/11/2026. Presentación de ofertas: 19/11/2026. Otorgamiento de la buena pro: 26/11/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. Las MYPE "
        "pueden optar por la retención del 10% del monto del contrato. 5.2 Penalidades. Penalidad por mora hasta un "
        "máximo del 10% del monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los treinta (30) "
        "días calendario siguientes a la conformidad.",
    ],
    # 6) Mobiliario · Postular: contrato a su medida
    "6_mobiliario_postular.pdf": [
        portada("UGEL HUANCAYO", "03-2026-UGELH/CS", "ADQUISICIÓN DE CARPETAS UNIPERSONALES PARA INSTITUCIONES EDUCATIVAS"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: UGEL Huancayo.\n1.2 Objeto de la convocatoria: la "
        "adquisición de carpetas unipersonales para instituciones educativas. 1.3 El valor estimado asciende a "
        "S/ 420,000.00 (cuatrocientos veinte mil con 00/100 soles). La cantidad total requerida es de 1 200 carpetas.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de sesenta (60) días calendario "
        "contados desde el día siguiente de suscrito el contrato.\n3.1 Especificaciones técnicas según fichas del "
        "Anexo 2. Se aceptan productos equivalentes que cumplan las características técnicas.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 400 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores. Se permite la participación en consorcio.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 29/10/2026. Formulación de consultas y observaciones: "
        "del 30/10/2026 al 06/11/2026. Presentación de ofertas: 26/11/2026. Otorgamiento de la buena pro: 03/12/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. Las MYPE "
        "pueden optar por la retención del 10% del monto del contrato. 5.2 Penalidades. Penalidad por mora hasta un "
        "máximo del 10% del monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los veinte (20) "
        "días calendario siguientes a la conformidad.",
    ],
    # 7) Útiles de oficina · Postular: compra pequeña, ideal para empezar
    "7_utiles_postular.pdf": [
        portada("MUNICIPALIDAD DISTRITAL DE SURQUILLO", "21-2026-MDS/CS", "ADQUISICIÓN DE ÚTILES DE OFICINA PARA LAS ÁREAS ADMINISTRATIVAS"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: Municipalidad Distrital de Surquillo.\n1.2 Objeto de la "
        "convocatoria: la adquisición de útiles de oficina para las áreas administrativas. 1.3 El valor estimado "
        "asciende a S/ 42,000.00 (cuarenta y dos mil con 00/100 soles). La cantidad total requerida es de 800 unidades.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de veinte (20) días calendario "
        "contados desde el día siguiente de suscrito el contrato.\n3.1 Especificaciones técnicas según el cuadro del "
        "Anexo 1. Se aceptan marcas equivalentes.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 40 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 26/10/2026. Formulación de consultas y observaciones: "
        "del 27/10/2026 al 02/11/2026. Presentación de ofertas: 16/11/2026. Otorgamiento de la buena pro: 20/11/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. Las MYPE "
        "pueden optar por la retención del 10% del monto del contrato. 5.2 Penalidades. Penalidad por mora hasta un "
        "máximo del 10% del monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los diez (10) "
        "días calendario siguientes a la conformidad.",
    ],
    # 8) Útiles de oficina · Observar primero: marca de papel y certificación sin relación
    "8_utiles_observar.pdf": [
        portada("SUNAT", "11-2026-SUNAT/CS", "ADQUISICIÓN DE PAPEL BOND Y ÚTILES DE ESCRITORIO"),
        "CAPÍTULO I. GENERALIDADES\n1.1 Entidad contratante: SUNAT.\n1.2 Objeto de la convocatoria: la adquisición "
        "de papel bond y útiles de escritorio. 1.3 El valor estimado asciende a S/ 48,000.00 (cuarenta y ocho mil "
        "con 00/100 soles). La cantidad total requerida es de 1 500 unidades.",
        "CAPÍTULO II. DEL PROCEDIMIENTO\n2.6 Plazo de entrega. El plazo de entrega es de cinco (5) días calendario "
        "contados desde el día siguiente de suscrito el contrato.\n3.1 Especificaciones técnicas. El papel bond "
        "deberá ser de marca PaperOne, modelo A4 80 g, sin excepción.",
        "4.2 Requisitos de calificación. Experiencia del postor: el postor debe acreditar un monto facturado "
        "acumulado no menor a S/ 40 000,00 por la venta de bienes iguales o similares. El postor debe contar con "
        "inscripción vigente en el Registro Nacional de Proveedores. El postor deberá contar con certificación "
        "ISO 14001 vigente a su nombre.",
        "CRONOGRAMA DEL PROCEDIMIENTO. Convocatoria: 27/10/2026. Formulación de consultas y observaciones: "
        "del 28/10/2026 al 03/11/2026. Presentación de ofertas: 17/11/2026. Otorgamiento de la buena pro: 23/11/2026.\n"
        "5.1 Garantías. La garantía de fiel cumplimiento equivale al 10% del monto del contrato original. Las MYPE "
        "pueden optar por la retención del 10% del monto del contrato. 5.2 Penalidades. Penalidad por mora hasta un "
        "máximo del 10% del monto del contrato. 5.3 Forma de pago. El pago se realizará dentro de los treinta (30) "
        "días calendario siguientes a la conformidad.",
    ],
}


def crear(paginas) -> bytes:
    doc = fitz.open()
    for i, texto in enumerate(paginas, 1):
        p = doc.new_page()
        p.draw_rect(fitz.Rect(40, 22, 572, 44), color=(0.85, 0.2, 0.2), fill=(1, 0.93, 0.93))
        p.insert_text((50, 37), AVISO, fontsize=9, color=(0.7, 0.1, 0.1))
        p.insert_textbox(fitz.Rect(60, 70, 540, 780), texto, fontsize=11)
        p.insert_text((290, 815), f"- {i} -", fontsize=9, color=(0.4, 0.4, 0.4))
    data = doc.tobytes()
    doc.close()
    return data


if __name__ == "__main__":
    from pathlib import Path
    salida = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent)
    for nombre, paginas in CASOS.items():
        with open(f"{salida}/{nombre}", "wb") as f:
            f.write(crear(paginas))
        print("ok", nombre)
