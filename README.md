# LiciGuard AI — ¿Me presento a esta licitación?

Copiloto para MYPE peruanas que venden al Estado. Sube las bases y LiciGuard responde **4 preguntas con pruebas**,
te ayuda a **actuar** y te acompaña hasta el resultado.

## Módulos

| Módulo | Qué hace |
|---|---|
| **Portada y entrada** | Entrar con un código sin contraseña, crear uno, o probar como invitado (no se guarda nada). |
| **Varias empresas (cartas)** | Al entrar eliges con qué empresa trabajar (o agregas una). Todo se filtra por su rubro y se guarda aparte: revisiones, plazos, documentos, mercado y oportunidades. «Cambiar de empresa» en el menú. La demo empieza eligiendo una de 4 empresas de ejemplo. |
| **Asistente flotante** | Botón «Pregúntale a LiciGuard» siempre a mano: responde con el contexto de tu empresa y de la pantalla. Guardrails: se niega a temas ajenos, a cambiar sus reglas y a dar datos de otros; sin IA responde con reglas. |
| **Ejemplos (demo en 1 clic)** | 4 **empresas modelo** (llenan Mi empresa con sus documentos) y una **galería de bases** para revisar sin tener un PDF: 3 ficticias guiadas (Postular · Observar primero · No te conviene) + las reales que pongas en `ejemplos/reales/`. También hay botón «Ver la demo ahora» en la portada (sin registrarse). |
| **Ayuda para recorrer la app** | Recorrido guiado de la ficha (5 pasos), descripciones al pasar el cursor (menú e indicadores), glosario de términos (RNP, MYPE, garantía…), guía «¿Para qué sirve?» en cada página y «Siguiente paso» al final. |
| **Inicio (panel)** | 5 indicadores, agenda de plazos, primeros pasos / tus decisiones y el pulso de tu mercado con gráficos. |
| **Revisar bases → Ficha de decisión** | Recomendación, **índice de apertura (0–100)**, 6 datos clave de las bases y las 4 preguntas con su indicador: **¿Es justa? · ¿Puedo? · ¿Me conviene? · ¿Puedo ganar?** |
| **Revisar bases → Pruebas en el PDF** | La página exacta con la cita **resaltada**, explicación simple y el artículo de la normativa relacionado. |
| **Revisar bases → Actuar** | Borrador de observación (Word), fechas leídas del cronograma y checklist para tu oferta. |
| **Revisar bases → Pregúntale a tus bases** | Asistente que responde solo con tus bases y la normativa (dice "no sé" si no hay fuente). |
| **Oportunidades** | Con los datos abiertos del OECE: dónde se compra tu rubro, procesos a tu medida y **socios para consorcio**. |
| **Seguimiento** | Etapa de cada licitación, plazos que vencen y "aprende para la próxima" si perdiste. |
| **Mi empresa** | Perfil (con capacidad de producción y RNP), documentos con vencimiento, **"Para crecer"** y **Tus datos y privacidad** (descargar / borrar cuenta). |

**Diseño para no gastar tokens:** todo el análisis se hace con reglas (gratis, rápido y repetible). La IA solo explica
en simple y responde preguntas, con respaldo automático **Groq → Cloudflare → Gemini → sin IA** (con reintentos, pausa de proveedores caídos y caché).

---

## Puesta en marcha (ya tienes los datos listos)

Este proyecto ya incluye tus datos reales:
- `data/normativa/articulos.json` — 967 artículos (Ley 32069, Reglamento y su modificación)
- `data/ocds/historial.csv` — 8 175 procesos adjudicados (uniformes, mobiliario, limpieza, útiles de oficina)

### 1 · Base de datos (Supabase)
Si ya ejecutaste `supabase/01_esquema.sql` y `02_seguimiento_y_documentos.sql`, **solo ejecuta los 2 nuevos**, en orden
(**SQL Editor → New query →** pega el archivo **→ Run**). No borran ni cambian nada de lo anterior:
- `supabase/03_rnp_vigente.sql` — guarda si tu RNP está vigente.
- `supabase/04_privacidad.sql` — guarda cuándo cada persona aceptó el aviso de privacidad.
- `supabase/05_permisos.sql` — da permisos al servidor (arregla «permission denied for table usuarios»).
- `supabase/06_varias_empresas.sql` — una persona puede tener **varias empresas**, cada una con sus datos aparte
  (lo que ya tenías pasa a tu empresa actual; no se pierde nada).

Si no los ejecutas, la app sigue funcionando: guarda el resto y te avisa. Base nueva: `01` y luego `02`, `03`, `04`.

### 2 · Tus claves
Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` (créalo desde VS Code) y completa:
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y las claves de IA que tengas. **Cada nombre una sola vez.**
Sin claves la app funciona igual en modo local y sin IA.

**Cloudflare Workers AI (gratis, no entrena con tus datos)** — necesita 2 datos:
1. Entra a https://dash.cloudflare.com → menú **AI → Workers AI**. Copia tu **Account ID** → `CLOUDFLARE_ACCOUNT_ID`.
2. En esa misma página pulsa **Use REST API → Create a Workers AI API Token** (o *Manage API tokens* con la
   plantilla «Workers AI»). Copia el token → `CLOUDFLARE_API_TOKEN` (solo se muestra una vez).
3. Prueba con `python probar_ia.py`: debe decir **OK Cloudflare**.

### 2b · (Opcional) Entrar con Google — recomendado para el jurado
La app muestra el botón **«Entrar con Google»** solo si configuras esto. Sin configurarlo, todo funciona igual
(código o invitado).
1. https://console.cloud.google.com → crea un proyecto (p. ej. «LiciGuard»).
2. Menú **Google Auth Platform → Branding**: nombre de la app, correo de soporte → *Save*.
3. **Audience**: deja *External*. Mientras pruebas, agrega tu Gmail en *Test users*. Para el jurado pulsa
   **Publish app** (con los permisos básicos de correo y nombre no pide verificación).
4. **Clients → Create client → Web application**. En *Authorized redirect URIs* agrega
   `http://localhost:8501/oauth2callback` y, cuando la publiques, `https://TU-APP.streamlit.app/oauth2callback`.
   *Create* → copia **Client ID** y **Client secret**.
5. Genera un secreto para la cookie: `python -c "import secrets; print(secrets.token_hex(32))"`.
6. Pega esto **al final** de `.streamlit/secrets.toml` (nada debajo de `[auth]`):
```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "EL_TEXTO_DEL_PASO_5"

[auth.google]
client_id = "....apps.googleusercontent.com"
client_secret = "GOCSPX-..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```
7. `python -m pip install -r requirements.txt` (instala Authlib) y abre la app.

### 3 · Instalar y abrir
**Windows**
```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```
**Mac/Linux:** `python3 -m venv venv` y `source venv/bin/activate`. Las pruebas deben decir **56 passed**. Usa siempre `python -m …` (así se usa el Python del `venv`).
`requirements.txt` tiene las versiones probadas (es lo que usa Streamlit Cloud); `requirements-dev.txt` agrega pytest.

> Si ya tienes la carpeta `venv` de antes, basta con activarla y ejecutar `pip install -r requirements.txt`.

### 4 · Guion de la demo (3 minutos)
1. **Portada** → "Es mi primera vez" → acepta el aviso de privacidad → crea tu código.
2. **Mi empresa** → razón social, rubro "Uniformes y textiles", experiencia 320 000, producción 3 000, RNP «Sí, vigente» → *Guardar*.
3. **Revisar bases** → sube `ejemplos/1_uniformes_observar.pdf` → lee la **recomendación** y las 4 tarjetas
   (en «¿Puedo?» verás que no te alcanza la producción para 2 400 prendas en 5 días).
4. **Pruebas en el PDF** → elige una condición → la cita aparece resaltada + el artículo del Reglamento.
5. **Ficha → ¿Me conviene?** → materiales 330 000 y mano de obra 170 000 → la barra separa IGV, costos, financiamiento y ganancia.
6. **Explícamelo simple** → barra lateral → *Simular caída de Groq* → vuelve a pedirlo: responde Cloudflare o Gemini.
7. **Actuar** → descarga el borrador en Word → guarda fechas y checklist.
8. **Oportunidades → Socios para consorcio** y **Seguimiento** con el plazo que vence.

### 5 · Publicar (Streamlit Community Cloud)
1. Sube el proyecto a un repositorio **privado** de GitHub (`secrets.toml` y `venv` no se suben).
2. https://share.streamlit.io → *Create app* → repo y `app.py`.
3. *Advanced settings → Secrets*: pega el contenido de tu `secrets.toml`.

---

## Actualizar los datos (cuadernos para Google Colab)
| Cuaderno | Para qué | Resultado |
|---|---|---|
| `notebooks/01_construir_rag.ipynb` | Descarga y corta la normativa por artículos | `data/normativa/articulos.json` |
| `notebooks/02_historial_ocds.ipynb` | Descarga los datos abiertos, clasifica por rubro (19 rubros) y valida | `data/ocds/historial.csv` |
| `notebooks/03_opcional_medir_aciertos.ipynb` | Mide qué tan bien acierta la extracción (para el pitch) | porcentaje de aciertos |
| `notebooks/04_bajar_bases_reales.ipynb` | **Baja bases reales del SEACE** (enlaces de los datos abiertos), se queda con las que sirven y prueba LiciGuard en todas | PDFs en `data/bases/` + tabla de resultados |

**Bases de prueba ficticias:** `ejemplos/` trae 3 PDF (uno por cada recomendación) y el script que los crea.

## Estructura
```
app.py                     Navegación y barra lateral
ui/                        Pantallas: entrada, inicio, revisar, oportunidades, seguimiento, empresa · tema visual
core/extraccion.py         Reglas que leen las bases (montos, marcas, plazos, ISO, garantías, cronograma)
core/preguntas.py          Las 4 preguntas y la recomendación
core/buscador.py           Búsqueda BM25 en normativa y páginas (RAG local)
core/historial_ocds.py     "¿Puedo ganar?" con datos abiertos (normaliza nombres de proveedores)
core/mercado.py            Oportunidades, socios para consorcio y "Para crecer"
core/seguimiento.py        Etapas, plazos, checklist y aprendizaje
core/ia.py                 Groq → Cloudflare → Gemini → Hugging Face → sin IA, con guardrails y reintentos
core/borrador.py · db.py · usuarios.py · pdf_parser.py · preparar.py · fechas.py (hora de Lima)
core/privacidad.py         Aviso de privacidad (Ley 29733) · core/bases_reales.py (cuaderno 04)
supabase/01 … 04_*.sql     Esquema y migraciones
ejemplos/                  3 bases ficticias para la demo · ejemplos/reales/: bases reales de la galería
tests/                     56 pruebas (motor, mejoras, IA, bases reales y pantallas con AppTest)
```

## Límites (dilo con honestidad en el pitch)
- Las señales son **alertas para revisar**, no conclusiones legales. La decisión es de la persona.
- En los datos abiertos, `n_postores` cuenta **participantes registrados**, no ofertas presentadas.
- Oportunidades usa procesos **ya adjudicados**: orienta sobre tamaño, compradores y competencia. Las alertas de
  convocatorias abiertas en tiempo real son la siguiente fase.
- Los umbrales de alerta (`core/config.py`) son criterios del sistema, no límites de la ley.
- Los PDF escaneados (sin texto) aún no se analizan bien (faltaría OCR).
- Sin contraseña: quien conozca un código ve su historial (los códigos nuevos son largos y hay límite de intentos,
  pero en producción se usaría un enlace al correo).

## Cambios de esta versión
Ver [`CAMBIOS.md`](CAMBIOS.md).

## Revisión técnica
El documento [`docs/REVISION_TECNICA.md`](docs/REVISION_TECNICA.md) detalla arquitectura, estado de la IA, hallazgos por área y backlog priorizado.
