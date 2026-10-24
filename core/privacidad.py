"""Aviso de privacidad (Ley N.° 29733, Ley de Protección de Datos Personales del Perú).

Un solo texto para toda la app: la página «Privacidad», el aviso de la portada y el de Mi empresa.
Antes de usar LiciGuard con clientes reales, revísalo con un abogado.
Las afirmaciones de este texto describen lo que el código hace de verdad (verificado en tests/test_app.py).
"""

RESPONSABLE = "NullVector"
CONTACTO = "grupohackathon8@gmail.com"
VERSION = "Versión de demostración · Hackathon FuturX 2026"

# (ícono Material, título, texto en Markdown)
SECCIONES = [
    (":material/folder_open:", "¿Qué datos guardamos?", """
- **Cuenta:** tu nombre y la fecha en que aceptaste este aviso. Si entras con **Google**, usamos tu nombre y tu
  correo solo para reconocerte: en la base guardamos tu nombre y un código interno derivado de tu correo
  (no tu correo). Si entras con un **código**, guardamos ese código.
- **Perfil de tu empresa:** razón social, rubro, región, experiencia, capacidad (producción, máquinas, personal),
  certificaciones, condición MYPE y si tu RNP está vigente.
- **Licitaciones:** el resultado de cada análisis (datos de las bases, citas textuales y páginas), tu seguimiento
  y tus notas.
- **Documentos:** solo el **nombre, tipo y fecha de vencimiento** que escribes. No subimos tus documentos.
- **No guardamos el PDF de las bases:** se lee en la memoria de tu sesión y se descarta al cerrarla;
  solo se guarda el resultado del análisis.
"""),
    (":material/target:", "¿Para qué los usamos?", """
- Mostrarte tu ficha de decisión, tu historial, tus plazos y oportunidades de tu rubro.
- Comparar los requisitos de las bases con el perfil de tu empresa.

**No vendemos ni compartimos tus datos** con fines comerciales o publicitarios.
"""),
    (":material/auto_awesome:", "Inteligencia artificial", """
Solo cuando **tú** pides «Explícamelo simple» o haces una pregunta, enviamos un resumen del análisis o fragmentos
de las bases a un proveedor de IA: **Groq**, **Cloudflare Workers AI** o **Google Gemini** (en ese orden de
respaldo). Nunca enviamos tu correo, tu código de acceso ni los datos de tu perfil.

Groq y Cloudflare indican que no usan estos datos para entrenar; el plan gratuito de Gemini puede usarlos para
mejorar sus servicios. **No subas documentos confidenciales.** Todo el análisis principal funciona **sin IA**.
"""),
    (":material/cloud:", "¿Dónde se guardan y cómo se protegen?", """
En una base de datos en la nube (**Supabase**), a la que solo accede el servidor de LiciGuard; desde el navegador
no se puede leer. Se entra con tu cuenta de **Google** o con un código (sin contraseña, por ser una demostración)
con límite de intentos.

En **modo invitado no se guarda nada**: todo vive en tu sesión y desaparece al cerrarla.
Ningún sistema es 100 % seguro: si notas algo extraño, escríbenos.
"""),
    (":material/gavel:", "Tus derechos", """
Puedes ejercer tus derechos de **acceso, rectificación, cancelación y oposición** (ARCO):

- **Acceso:** descarga todo lo que guardamos en *Mi empresa → Tus datos y privacidad* (archivo JSON).
- **Rectificación:** corrige tu perfil, tus licitaciones y tus documentos en la app cuando quieras.
- **Cancelación:** el botón **Borrar mi cuenta** elimina para siempre tu cuenta y todos tus datos.
- **Oposición** u otras consultas: escríbenos al correo de contacto.
"""),
    (":material/event_available:", "¿Cuánto tiempo los conservamos?", """
Mientras tengas tu cuenta. Al **borrarla**, se eliminan de inmediato tu perfil, tus licitaciones, tu seguimiento
y tus documentos (borrado en cascada en la base de datos).
"""),
]

NOTA = ("LiciGuard es una herramienta de apoyo: sus alertas deben contrastarse con las bases oficiales. "
        "No es asesoría legal ni garantiza la adjudicación.")

# Versión en texto corrido (para los avisos emergentes de la portada y de Mi empresa)
AVISO = (f"**Responsable:** {RESPONSABLE} · **Contacto:** {CONTACTO}\n\n"
         + "\n\n".join(f"**{titulo}**\n{texto.strip()}" for _, titulo, texto in SECCIONES)
         + f"\n\n*{NOTA} {VERSION}.*")
