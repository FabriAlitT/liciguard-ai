"""Textos de ayuda: glosario, explicaciones al pasar el cursor, guía de cada página y recorrido guiado.

Todo en un solo lugar para corregir la redacción sin tocar las pantallas.
"""

# Palabras difíciles: se subrayan con puntos en la app y muestran su significado al pasar el cursor.
GLOSARIO = {
    "RNP": "Registro Nacional de Proveedores. Inscripción obligatoria (y vigente) para venderle al Estado peruano.",
    "MYPE": "Micro y pequeña empresa. Tiene beneficios, como la retención del 10 % en lugar de la carta fianza.",
    "garantía de fiel cumplimiento": "Dinero que asegura que cumplirás el contrato (normalmente 10 %). Se da con "
                                     "carta fianza o, si eres MYPE, con retención.",
    "carta fianza": "Documento de un banco que respalda tu garantía. Cobra una comisión anual.",
    "retención": "En lugar de carta fianza, la entidad te descuenta el 10 % de los pagos y te lo devuelve al final. "
                 "Beneficio para MYPE.",
    "valor estimado": "Lo que la entidad calcula que costará la compra. Es el techo de referencia de las ofertas.",
    "buena pro": "La adjudicación: el momento en que se anuncia quién ganó la licitación.",
    "observaciones": "Pedidos formales a la entidad para que corrija las bases si algo restringe la competencia. "
                     "Tienen un plazo en el cronograma.",
    "penalidad": "Multa por entregar tarde; suele llegar hasta el 10 % del contrato.",
    "consorcio": "Alianza temporal con otras empresas para sumar experiencia y capacidad y postular juntas.",
    "conformidad": "Cuando la entidad acepta lo que entregaste. Desde ahí corren los días para pagarte.",
    "suma alzada": "Precio total fijo por todo el contrato, sin pagos por unidad.",
    "bases integradas": "Versión final de las bases, con las consultas y observaciones ya incorporadas.",
    "IGV": "Impuesto General a las Ventas (18 %). Va incluido en tu oferta, pero se lo pagas a SUNAT.",
    "OECE": "Organismo Especializado para las Contrataciones Públicas Eficientes (antes OSCE). Publica los datos "
            "abiertos que usamos.",
    "SEACE": "Sistema Electrónico de Contrataciones del Estado: donde se publican las licitaciones y sus bases.",
    "índice de apertura": "De 0 a 100: qué tan abiertas a la competencia parecen las bases. Baja con cada alerta.",
}

# Explicación de cada indicador (se muestra al pasar el cursor por la tarjeta)
AYUDA_INDICADORES = {
    "Licitaciones revisadas": "Cuántas bases analizaste con LiciGuard.",
    "Valor analizado": "Suma de los valores estimados de todas las bases que revisaste.",
    "Alertas detectadas": "Condiciones que podrían restringir la competencia y que puedes observar.",
    "Procesos activos": "Licitaciones que sigues y que todavía no terminan.",
    "Tasa de éxito": "De las licitaciones que ya tienen resultado, cuántas ganaste.",
    "Procesos 2025–2026": "Licitaciones adjudicadas en tu rubro desde 2025, según datos abiertos del Estado.",
    "Monto adjudicado": "Cuánto dinero se adjudicó en tu rubro desde 2025.",
    "Valor típico": "El valor del proceso «del medio» en tu rubro (mediana).",
    "Tu alcance hoy": "Porcentaje de procesos de tu rubro que podrías respaldar con tu experiencia actual.",
    "Valor estimado": "Lo que la entidad calcula que costará. Lo leímos del PDF (mira la página indicada).",
    "Plazo de entrega": "Días que tienes para entregar desde que firmas el contrato.",
    "Experiencia pedida": "Monto que debes haber facturado antes en ventas parecidas para poder postular.",
    "Garantía": "Porcentaje del contrato que debes garantizar (carta fianza o retención MYPE).",
    "Pago": "Días que tarda la entidad en pagarte después de aceptar tu entrega.",
    "Requisitos que cumples": "Comparamos lo que piden las bases con tu perfil de Mi empresa.",
    "Ganarías": "Tu ganancia después de costos, IGV, garantía y costo del dinero.",
    "Capital que necesitas": "Dinero que debes poner antes de que te paguen.",
    "Costo de financiarte": "Intereses o costo de usar tu dinero mientras esperas el pago.",
    "IGV incluido": "Parte de tu oferta que no es tuya: va a SUNAT.",
    "Multa máxima": "Lo máximo que te podrían descontar si te atrasas.",
    "Perfil completo": "Cuántos datos clave de tu empresa ya llenaste. Con más datos, mejores respuestas.",
    "Experiencia acreditable": "Lo que ya facturaste en ventas parecidas y puedes demostrar con contratos.",
    "Alcance de mercado": "Porcentaje de procesos de tu rubro que podrías respaldar con tu experiencia.",
    "Documentos registrados": "Documentos de tu expediente con su fecha de vencimiento.",
    "Por vencer o vencidos": "Documentos que vencen en 30 días o ya vencieron: renuévalos a tiempo.",
}

# Qué hace cada página del menú (al pasar el cursor)
AYUDA_MENU = {
    "Inicio": "Tu resumen: plazos que vencen, tus indicadores y cómo va tu mercado.",
    "Ejemplos": "Bases de ejemplo de tu rubro para probar la app en 1 clic.",
    "Revisar bases": "Sube el PDF de una licitación y recibe tu ficha de decisión.",
    "Oportunidades": "Dónde se compra lo que vendes, procesos a tu medida y socios.",
    "Seguimiento": "La etapa y las fechas de cada licitación que sigues.",
    "Mi empresa": "Tu perfil, tus documentos y cuánto mercado puedes alcanzar.",
    "Privacidad": "Qué datos guardamos y cómo descargarlos o borrarlos.",
}

# Franja «¿Para qué sirve esta página?»: título, frase, pasos
GUIAS = {
    "Inicio": ("Tu panel", "Mira de un vistazo qué vence pronto y cómo vas.",
               ["Revisa los próximos plazos", "Mira tus indicadores", "Sigue el pulso de tu mercado"]),
    "Ejemplos": ("Prueba sin tus documentos", "Bases de tu rubro, listas para probar.",
                 ["Elige unas bases", "Mira la ficha de decisión", "Prueba el recorrido guiado"]),
    "Revisar bases": ("Revisa unas bases", "Sube el PDF y en 1 minuto sabes si te conviene.", ["Sube el PDF (o usa un ejemplo)", "Lee la recomendación",
                                                "Mira las pruebas y actúa"]),
    "Oportunidades": ("Encuentra dónde vender", "Quién compra lo que vendes y con quién asociarte.", ["Dónde se compra", "Procesos a tu medida", "Socios para consorcio"]),
    "Seguimiento": ("No se te pase ninguna fecha", "La etapa y los plazos de cada licitación.",
                    ["Mira la etapa", "Revisa las fechas", "Anota qué aprendiste"]),
    "Mi empresa": ("Tu perfil, una sola vez", "Con estos datos sabemos si cumples los requisitos.",
                   ["Llena tus datos (o carga un ejemplo)", "Agrega tus documentos", "Mira tu alcance de mercado"]),
    "Privacidad": ("Tus datos, bajo tu control", "Qué guardamos y cómo borrarlo.",
                   ["Lee qué guardamos", "Descarga tus datos", "Borra tu cuenta si quieres"]),
}

# Recorrido guiado de la ficha: (selector CSS, título, texto)
TOUR_FICHA = [
    (".st-key-tour_reco", "La respuesta en una frase",
     "¿Te presentas o no? Verde: postula. Ámbar: vale la pena, pero primero pide que corrijan las bases. "
     "Rojo: hoy no te conviene (y te decimos por qué)."),
    (".st-key-tour_datos", "Lo importante de las bases",
     "El índice de apertura (0 a 100) y los datos clave leídos del PDF: valor, plazo, experiencia, garantía y pago. "
     "Pasa el cursor sobre cada tarjeta para ver qué significa."),
    (".st-key-tour_preguntas", "Las 4 preguntas",
     "¿Es justa? ¿Puedo? ¿Me conviene? ¿Puedo ganar? Cada una con su semáforo: Bien, Ojo o Cuidado."),
    (".st-key-tour_pestanas [role='tablist']", "Pruebas y acción",
     "En «Pruebas en el PDF» ves la página exacta resaltada. En «Actuar» descargas la observación en Word y las "
     "fechas. En «Pregúntale a tus bases» le preguntas lo que quieras."),
    ("section[data-testid='stSidebar'] div[role='radiogroup']", "Y después…",
     "Seguimiento guarda las fechas de esta licitación, Mi empresa tu perfil y Ejemplos otras bases de tu rubro. "
     "Arriba puedes «Cambiar de empresa», y abajo a la derecha tienes al asistente para preguntar lo que quieras."),
]
