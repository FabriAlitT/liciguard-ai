"""Extracción de datos de las bases con REGLAS (sin IA, sin tokens).

Cada requisito guarda la página y la cita textual tomada del propio PDF,
por eso su evidencia siempre es verificable.
"""
import re
import unicodedata

from core.config import CERTIFICACIONES_POCO_COMUNES

MONTO = r"S/\.?\s?(\d{1,3}(?:[  .,'’]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"


# ----------------------------------------------------------------------------------------
# Utilidades de texto
# ----------------------------------------------------------------------------------------
def plano(texto: str) -> str:
    """Une las líneas del PDF en un texto corrido (para buscar frases)."""
    t = texto.replace("­", "")
    t = re.sub(r"-\n(?=[a-záéíóúñ])", "", t)  # palabras cortadas con guion al final de línea
    return re.sub(r"\s+", " ", t).strip()


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def comparable(texto: str) -> str:
    return re.sub(r"\s+", " ", sin_tildes(texto).lower()).strip()


def parse_monto(texto: str) -> float | None:
    """'1 600 000,00' / '1,600,000.00' / "1'600,000.00" / '812400' -> número."""
    t = re.sub(r"[  '’]", "", texto.strip())
    if not t:
        return None
    if "," in t and "." in t:
        decimal = "," if t.rfind(",") > t.rfind(".") else "."
        miles = "." if decimal == "," else ","
        t = t.replace(miles, "").replace(decimal, ".")
    elif "," in t:
        partes = t.split(",")
        t = t.replace(",", ".") if len(partes) == 2 and len(partes[1]) <= 2 else t.replace(",", "")
    elif "." in t:
        partes = t.split(".")
        if not (len(partes) == 2 and len(partes[1]) <= 2):
            t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def oracion(texto: str, inicio: int, fin: int, maximo: int = 320) -> str:
    """Devuelve la oración que contiene texto[inicio:fin]."""
    izq = texto.rfind(". ", 0, inicio)
    izq = 0 if izq == -1 else izq + 2
    der = texto.find(". ", fin)
    der = len(texto) if der == -1 else der + 1
    frase = texto[izq:der].strip()
    if len(frase) > maximo:  # recorta alrededor de la coincidencia
        centro = (inicio + fin) // 2 - izq
        a = max(0, centro - maximo // 2)
        frase = frase[a:a + maximo].strip()
    return frase


def cita_en_pagina(cita: str, texto_pagina: str) -> bool:
    """Verificador: la cita debe existir tal cual (salvo espacios/tildes) en la página."""
    return bool(cita) and comparable(cita) in comparable(plano(texto_pagina))


def _req(categoria, descripcion, pagina, cita, valor=None, unidad=None, **extra):
    return {"categoria": categoria, "descripcion": descripcion, "pagina": pagina, "cita": cita,
            "valor": valor, "unidad": unidad, **extra}


# ----------------------------------------------------------------------------------------
# Datos generales del procedimiento
# ----------------------------------------------------------------------------------------
PROCEDIMIENTOS = (r"(LICITACI[ÓO]N P[ÚU]BLICA(?: ABREVIADA)?|CONCURSO P[ÚU]BLICO(?: ABREVIADO)?|"
                  r"ADJUDICACI[ÓO]N SIMPLIFICADA|SUBASTA INVERSA ELECTR[ÓO]NICA|COMPARACI[ÓO]N DE PRECIOS)"
                  r"\s*N[°º.oO]*\s*([0-9][\w\-/]*)")
ENTIDADES = (r"((?:MUNICIPALIDAD|GOBIERNO REGIONAL|MINISTERIO|HOSPITAL|UNIVERSIDAD|UNIDAD DE GESTI[ÓO]N|"
             r"SEGURO SOCIAL|DIRECCI[ÓO]N REGIONAL|PROGRAMA|INSTITUTO|SUPERINTENDENCIA|POLIC[ÍI]A|EJ[ÉE]RCITO|"
             r"MARINA|FUERZA A[ÉE]REA|CORTE SUPERIOR|PODER JUDICIAL|EMPRESA)[A-ZÁÉÍÓÚÑ ,.\-]{3,90})")


def datos_generales(paginas: list[dict]) -> dict:
    primeras = " ".join(plano(p["texto"]) for p in paginas[:6])
    todo = [(p["pagina"], plano(p["texto"])) for p in paginas]
    datos = {"procedimiento": None, "nomenclatura": None, "entidad": None, "objeto": None,
             "valor_estimado": None, "valor_estimado_pagina": None, "valor_estimado_cita": None}

    m = re.search(PROCEDIMIENTOS, primeras, re.I)
    if m:
        datos["procedimiento"] = m.group(1).title()
        datos["nomenclatura"] = m.group(2).strip(" .-")
    m = re.search(ENTIDADES, primeras)
    if m:
        datos["entidad"] = re.split(r"\s{2,}| BASES| LICITACI| ADJUDICACI| CONCURSO| SUBASTA| COMPARACI",
                                    m.group(1))[0].strip(" ,.-").title()
    m = re.search(r"(?:objeto de la convocatoria|objeto del procedimiento|objeto de la contrataci[óo]n)"
                  r"\s*[:.\-]?\s*(?:la |el )?(.{10,180}?)(?:\.\s|$)", primeras, re.I)
    if m:
        datos["objeto"] = m.group(1).strip(" :.-")
    else:
        m = re.search(r"((?:ADQUISICI[ÓO]N|CONTRATACI[ÓO]N|SUMINISTRO) DE [A-ZÁÉÍÓÚÑ0-9 ,\-]{5,140})", primeras)
        if m:
            datos["objeto"] = m.group(1).strip(" ,.-").capitalize()

    for num, texto in todo:
        m = re.search(r"valor (?:estimado|referencial)[^.]{0,160}?" + MONTO, texto, re.I)
        if m:
            datos["valor_estimado"] = parse_monto(m.group(1))
            datos["valor_estimado_pagina"] = num
            datos["valor_estimado_cita"] = oracion(texto, m.start(), m.end())
            break
    return datos


# ----------------------------------------------------------------------------------------
# Requisitos y condiciones
# ----------------------------------------------------------------------------------------
NO_ES_EXIGENCIA_DE_MARCA = re.compile(
    r"marca\s+(?:y|o|/)\s+modelo|marca(?:s)?\s+(?:del|de los|de la)\s+(?:bien|producto|equipo)s?\s+ofertad|"
    r"marca\s+de\s+agua|marca\s+registrada|consignar|indicar la marca|precisar la marca|declarar la marca|"
    r"marca\s+ofertada|marcar", re.I)
EQUIVALENTE = re.compile(r"equivalente|similar|superior|o mejor|referencial", re.I)
TAJANTE = re.compile(r"sin excepci[óo]n|exclusivamente|[úu]nicamente|obligatoriamente|indefectiblemente", re.I)

NUM_DIAS = r"(\d{1,3})\s*\)?\s*d[íi]as?\s*(calendario|h[áa]biles)?"
NUM_HORAS = r"(\d{1,3})\s*\)?\s*horas"
CANTIDAD = (r"(\d{1,3}(?:[ .,]\d{3})+|\d+)\s*\)?\s*(unidades|unid\.?|und\.?|prendas|juegos|piezas|kits?|pares|"
            r"carpetas|sillas|mesas|m[óo]dulos|bolsas|cajas|paquetes|litros|galones|uniformes|bienes)\b")


def extraer_requisitos(paginas: list[dict]) -> list[dict]:
    reqs: list[dict] = []
    vistos: set[tuple] = set()

    def agregar(r):
        clave = (r["categoria"], r["pagina"], r["cita"][:80])
        if clave not in vistos:
            vistos.add(clave)
            reqs.append(r)

    for p in paginas:
        num, t = p["pagina"], plano(p["texto"])
        if not t:
            continue

        # Experiencia del postor (monto facturado)
        for m in re.finditer(r"monto facturado acumulado[^.]{0,220}?" + MONTO, t, re.I):
            agregar(_req("experiencia", "Monto de experiencia exigido", num, oracion(t, m.start(), m.end()),
                         parse_monto(m.group(1)), "S/"))

        # Marcas exigidas
        for m in re.finditer(r"\bmarcas?\b", t, re.I):
            frase = oracion(t, m.start(), m.end())
            if NO_ES_EXIGENCIA_DE_MARCA.search(frase) or EQUIVALENTE.search(frase):
                continue
            nombre = re.search(r"\bmarcas?\s*[:\-]?\s*[«\"“]?([A-ZÁÉÍÓÚÑ][\w\-]+(?:\s[A-Z0-9][\w\-]+){0,2})", frase)
            if not nombre or not re.search(r"deber[áa]|debe|ser[áa]|exige|requiere|ser de", frase, re.I):
                continue
            agregar(_req("marca", f"Exige la marca {nombre.group(1)}", num, frase, nombre.group(1),
                         tajante=bool(TAJANTE.search(frase))))

        # Plazo de entrega / ejecución
        for m in re.finditer(r"plazo de (?:entrega|ejecuci[óo]n)[^.]{0,140}?" + NUM_DIAS, t, re.I):
            agregar(_req("plazo_entrega", "Plazo de entrega", num, oracion(t, m.start(), m.end()),
                         int(m.group(1)), "días " + (m.group(2) or "").lower()))

        # Certificaciones ISO
        for m in re.finditer(r"\bISO\s*(\d{4,5})", t):
            frase = oracion(t, m.start(), m.end())
            if re.search(r"puntaje|bonificaci|factor de evaluaci", frase, re.I):
                tipo = "factor de evaluación (da puntos)"
            else:
                tipo = "requisito"
            agregar(_req("certificacion", f"Certificación ISO {m.group(1)}", num, frase, f"ISO {m.group(1)}",
                         tipo=tipo, tema=CERTIFICACIONES_POCO_COMUNES.get(m.group(1))))

        # Muestras
        for m in re.finditer(r"muestras?[^.]{0,180}?(?:" + NUM_HORAS + "|" + NUM_DIAS + ")", t, re.I):
            horas = int(m.group(1)) if m.group(1) else int(m.group(2)) * 24
            agregar(_req("muestras", "Plazo para presentar muestras", num, oracion(t, m.start(), m.end()),
                         horas, "horas"))

        # Garantía de fiel cumplimiento
        for m in re.finditer(r"garant[íi]a de fiel cumplimiento[^.]{0,200}?(\d{1,2}(?:[.,]\d)?)\s*%", t, re.I):
            agregar(_req("garantia", "Garantía de fiel cumplimiento", num, oracion(t, m.start(), m.end()),
                         float(m.group(1).replace(",", ".")), "%"))
        m = re.search(r"retenci[óo]n[^.]{0,120}(?:micro|peque[ñn]a|mype)|(?:micro|peque[ñn]a|mype)[^.]{0,120}retenci[óo]n",
                      t, re.I)
        if m:
            agregar(_req("retencion_mype", "Opción de retención para MYPE en lugar de garantía", num,
                         oracion(t, m.start(), m.end())))

        # Penalidades
        for m in re.finditer(r"penalidad[^.]{0,220}?(\d{1,2}(?:[.,]\d)?)\s*%", t, re.I):
            agregar(_req("penalidad", "Tope de penalidad por mora", num, oracion(t, m.start(), m.end()),
                         float(m.group(1).replace(",", ".")), "%"))

        # Forma y plazo de pago
        for m in re.finditer(r"(?:el pago|pago se realizar[áa]|forma de pago)[^.]{0,200}?" + NUM_DIAS, t, re.I):
            agregar(_req("pago", "Plazo de pago", num, oracion(t, m.start(), m.end()), int(m.group(1)), "días"))
        if re.search(r"\badelanto", t, re.I):
            m = re.search(r"\badelanto[^.]{0,120}", t, re.I)
            agregar(_req("adelanto", "Las bases mencionan adelantos", num, oracion(t, m.start(), m.end())))

        # Cantidad requerida (para comparar con la capacidad de producción)
        for m in re.finditer(r"cantidad(?:\s+total)?(?:\s+requerida)?\s*(?:de|:)?[^.]{0,60}?" + CANTIDAD, t, re.I):
            n = parse_monto(m.group(1))
            if n and n >= 2:
                agregar(_req("cantidad", "Cantidad requerida", num, oracion(t, m.start(), m.end()), int(n),
                             m.group(2).lower()))

        # Inscripción en el RNP
        m = re.search(r"Registro Nacional de Proveedores|\bRNP\b", t)
        if m:
            agregar(_req("rnp", "Inscripción vigente en el RNP", num, oracion(t, m.start(), m.end())))
    return reqs


def primero(reqs: list[dict], categoria: str) -> dict | None:
    return next((r for r in reqs if r["categoria"] == categoria), None)


def maximo(reqs: list[dict], categoria: str) -> dict | None:
    candidatos = [r for r in reqs if r["categoria"] == categoria and r.get("valor") is not None]
    return max(candidatos, key=lambda r: r["valor"]) if candidatos else None


# ----------------------------------------------------------------------------------------
# Cronograma (fechas clave)
# ----------------------------------------------------------------------------------------
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
         "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
FECHA = (r"(\d{1,2})[/\-.](\d{1,2})[/\-.](20\d{2})|(\d{1,2}) de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
         r"septiembre|setiembre|octubre|noviembre|diciembre)(?: del?)? (20\d{2})")
ETAPAS = {
    "observaciones": r"consultas(?:\s*y\s*|\s*,\s*|\s*/\s*)observaciones|formulaci[óo]n de (?:consultas|observaciones)",
    "ofertas": r"presentaci[óo]n de (?:ofertas|propuestas)",
    "buena_pro": r"otorgamiento de la buena pro|buena pro",
}


def _a_fecha(m):
    from datetime import date
    try:
        if m.group(1):
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        return date(int(m.group(6)), MESES[m.group(5).lower()], int(m.group(4))).isoformat()
    except (ValueError, KeyError):
        return None


def cronograma(paginas: list[dict]) -> dict:
    """Busca la fecha (la última del rango) que aparece cerca de cada etapa del cronograma."""
    res = {}
    for p in paginas:
        t = plano(p["texto"])
        for etapa, patron in ETAPAS.items():
            if etapa in res:
                continue
            for m in re.finditer(patron, t, re.I):
                ventana = t[m.end(): m.end() + 160]
                cortes = [x.start() for x in [re.search(r"\.\s+[A-ZÁÉÍÓÚ]", ventana)] if x]
                cortes += [x.start() for otra, pat in ETAPAS.items() if otra != etapa
                           for x in [re.search(pat, ventana, re.I)] if x]
                ventana = ventana[:min(cortes)] if cortes else ventana
                fechas = [f for f in (_a_fecha(x) for x in re.finditer(FECHA, ventana, re.I)) if f]
                if fechas:
                    res[etapa] = {"fecha": fechas[-1], "pagina": p["pagina"],
                                  "cita": oracion(t, m.start(), m.end() + 60)}
                    break
    return res
