"""Genera la mini web pública (GitHub Pages) que Google pide para publicar «Entrar con Google».

Crea docs/sitio/index.html (página principal) y docs/sitio/privacidad.html (política de privacidad)
con el MISMO texto de la app (core/privacidad.py). Uso:  python docs/sitio/generar_sitio.py [URL_DE_LA_APP]
"""
import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from core.privacidad import CONTACTO, NOTA, RESPONSABLE, SECCIONES, VERSION  # noqa: E402

URL_APP = sys.argv[1] if len(sys.argv) > 1 else "https://TU-APP.streamlit.app"
SALIDA = Path(__file__).resolve().parent

CSS = """
:root{--azul:#2563EB;--tinta:#0B1B3F;--gris:#51607A;--borde:#E2E8F2}
*{box-sizing:border-box} body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:var(--tinta);background:#F4F7FC;line-height:1.6}
.band{background:linear-gradient(120deg,#1D4ED8,#2563EB 45%,#06B6D4);color:#fff;padding:48px 20px}
.wrap{max-width:900px;margin:0 auto;padding:0 20px} .band .wrap{padding:0}
.k{font-size:13px;font-weight:700;letter-spacing:.08em;opacity:.9} h1{font-size:34px;line-height:1.15;margin:8px 0 10px}
.band p{font-size:17px;opacity:.95;margin:0;max-width:640px}
main{padding:32px 20px 48px} .card{background:#fff;border:1px solid var(--borde);border-radius:16px;padding:22px 24px;margin:0 0 16px}
h2{font-size:19px;margin:0 0 8px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:0 0 16px}
.grid .card{margin:0} .btn{display:inline-block;background:#fff;color:var(--azul);font-weight:800;padding:12px 22px;border-radius:12px;text-decoration:none;margin-top:20px}
.btn2{display:inline-block;color:#fff;font-weight:700;margin:20px 0 0 14px} a{color:var(--azul)} small,.muted{color:var(--gris)}
.aviso{background:#FFF7E6;border:1px solid #FCE2B0;color:#8A4B00;border-radius:12px;padding:14px 18px}
footer{color:var(--gris);font-size:13px;text-align:center;padding:0 20px 32px}
"""


def md(texto):
    t = html.escape(texto.strip())
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)
    salida, en_lista, parrafo = [], False, []

    def cerrar_parrafo():
        if parrafo:
            salida.append("<p>" + " ".join(parrafo) + "</p>")
            parrafo.clear()

    for linea in t.split("\n"):
        if linea.startswith("- "):
            cerrar_parrafo()
            if not en_lista:
                salida.append("<ul>")
                en_lista = True
            salida.append(f"<li>{linea[2:]}</li>")
        elif linea.startswith("  ") and en_lista:
            salida[-1] = salida[-1][:-5] + " " + linea.strip() + "</li>"
        else:
            if en_lista:
                salida.append("</ul>")
                en_lista = False
            if linea.strip():
                parrafo.append(linea.strip())
            else:
                cerrar_parrafo()
    cerrar_parrafo()
    if en_lista:
        salida.append("</ul>")
    return "\n".join(salida)


def pagina(titulo, banda, cuerpo):
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{titulo}</title>'
            f'<style>{CSS}</style></head><body>{banda}<main class="wrap">{cuerpo}</main>'
            f'<footer>© {RESPONSABLE} · LiciGuard AI · {VERSION} · <a href="mailto:{CONTACTO}">{CONTACTO}</a></footer>'
            f'</body></html>')


INDEX = pagina("LiciGuard · ¿Me presento a esta licitación?", f"""
<header class="band"><div class="wrap"><div class="k">LICIGUARD AI · HACKATHON FUTURX 2026</div>
<h1>¿Me presento a esta licitación?</h1>
<p>LiciGuard ayuda a las micro y pequeñas empresas del Perú a decidir con datos: sube las bases de una licitación pública
y en menos de un minuto responde 4 preguntas, con pruebas en el PDF.</p>
<a class="btn" href="{URL_APP}">Abrir LiciGuard</a><a class="btn2" href="privacidad.html">Política de privacidad</a></div></header>""", """
<div class="grid">
<div class="card"><h2>¿Es justa?</h2><p class="muted">Detecta condiciones que podrían favorecer a un solo proveedor y muestra la página exacta.</p></div>
<div class="card"><h2>¿Puedo?</h2><p class="muted">Compara cada requisito con tu empresa y propone salidas si te falta algo.</p></div>
<div class="card"><h2>¿Me conviene?</h2><p class="muted">Calcula tu ganancia real con IGV, garantías, multas y días de pago.</p></div>
<div class="card"><h2>¿Puedo ganar?</h2><p class="muted">Muestra quién ganó antes, a qué precio y con cuánta competencia (datos abiertos del OECE).</p></div>
</div>
<div class="card"><h2>Cómo se usa</h2><p>Entra con tu cuenta de Google o como invitado, sube las bases en PDF y revisa la ficha de decisión.
También puedes preparar tu observación a las bases y seguir los plazos de cada proceso.</p></div>
<p class="aviso">LiciGuard es una herramienta de apoyo: sus alertas deben contrastarse con las bases oficiales. No es asesoría legal.</p>""")

SECCIONES_HTML = "".join(f'<section class="card"><h2>{i:02d} · {html.escape(t)}</h2>{md(x)}</section>'
                         for i, (_, t, x) in enumerate(SECCIONES, 1))
PRIVACIDAD = pagina("Política de privacidad · LiciGuard", """
<header class="band"><div class="wrap"><div class="k">LICIGUARD · LEY N.° 29733</div><h1>Política de privacidad</h1>
<p>Qué datos usamos, para qué y cómo puedes controlarlos.</p><a class="btn" href="index.html">Volver al inicio</a></div></header>""",
f"""<div class="grid"><div class="card"><small>RESPONSABLE</small><h2>{RESPONSABLE}</h2></div>
<div class="card"><small>CONTACTO</small><h2><a href="mailto:{CONTACTO}">{CONTACTO}</a></h2></div></div>
{SECCIONES_HTML}<p class="aviso"><b>Importante.</b> {html.escape(NOTA)}</p>""")

if __name__ == "__main__":
    (SALIDA / "index.html").write_text(INDEX, encoding="utf-8")
    (SALIDA / "privacidad.html").write_text(PRIVACIDAD, encoding="utf-8")
    print("Listo:", SALIDA / "index.html", "y", SALIDA / "privacidad.html")
