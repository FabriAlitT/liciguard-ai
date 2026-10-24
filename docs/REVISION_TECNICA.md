# LiciGuard AI — Documento de revisión técnica y traspaso

| | |
|---|---|
| **Proyecto** | LiciGuard AI — "¿Me presento a esta licitación?" (Hackathon FuturX 2026, Desafío 1) |
| **Fecha** | 23 de octubre de 2026 |
| **Estado** | Versión 3 (23/10/2026, noche). Funciona de punta a punta; 56 pruebas. Ver «Avance» abajo y `CAMBIOS.md`. |
| **Para** | Programador(a) que revisará, corregirá y continuará el proyecto |
| **Stack** | Python 3.11+ · Streamlit 1.50+ · Supabase (Postgres) · PyMuPDF · pandas/Altair · cliente `openai` hacia Groq / Cloudflare Workers AI / Gemini |

> **Cómo leer este documento:** la sección 1 es obligatoria antes de ejecutar nada (secretos). La sección 5 explica el
> problema de las IA. La sección 6 es la revisión detallada por área, con severidad, archivo y propuesta. La
> sección 7 resume todo en un backlog priorizado.

> ### Avance al 23/10/2026 (noche) — qué ya se resolvió de este documento
> | Backlog | Estado |
> |---|---|
> | #2 3.er proveedor de IA | ✅ **Cloudflare Workers AI** (Groq → Cloudflare → Gemini). HF queda opcional |
> | #3, #7 Reintentos, cortacircuito, timeouts, caché (IA-2/3/4/7) | ✅ |
> | #4 RNP vigente | ✅ (perfil + Constancia RNP con fecha) |
> | #6 Códigos más largos + límite de intentos | ✅ (5 por sesión, 25 por IP) |
> | #10 Hora de Lima | ✅ `core/fechas.py` |
> | #11 Rendimiento (análisis fijo por PDF, caché de imágenes, máx. 4 PDF) | ✅ |
> | #12 Versiones fijas | ✅ (`requirements.txt` + `requirements-dev.txt`); **CI pendiente** |
> | #13 Errores de Supabase al leer y escribir | ✅ |
> | #14 Aviso de privacidad + descargar / borrar cuenta | ✅ (completar responsable y contacto en `core/privacidad.py`) |
> | #17 Producción, máquinas, personal y MYPE en «¿Puedo?» | ✅ |
> | #18 IGV y costo financiero en «¿Me conviene?» | ✅ (adelantos: pendiente) |
> | Pruebas de pantallas (6.9) | ✅ `tests/test_app.py` (AppTest) |
> | #8 Corpus de bases reales | 🟡 Herramienta lista: `notebooks/04_bajar_bases_reales.ipynb`; falta ejecutarla y etiquetar |
> | #1 Rotar claves · #5 ensayo de demo · #9 patrones · #15 OCR · #16 tablas · #19 umbrales · #20 Auth/RLS · #21–#25 | ⏳ Pendiente |
>
> Las secciones siguientes se conservan como estaban (describen el estado anterior y el porqué de cada cambio).

---

## Índice

1. [Confidencialidad: el archivo `secrets.toml` NO viene incluido](#1-confidencialidad-el-archivo-secretstoml-no-viene-incluido)
2. [Qué hace el producto](#2-qué-hace-el-producto)
3. [Cómo ejecutarlo](#3-cómo-ejecutarlo)
4. [Arquitectura y mapa del código](#4-arquitectura-y-mapa-del-código)
5. [Estado de la IA y lo que hay que arreglar](#5-estado-de-la-ia-y-lo-que-hay-que-arreglar)
6. [Revisión detallada por área](#6-revisión-detallada-por-área)
7. [Backlog priorizado](#7-backlog-priorizado)
8. [Plan de pruebas y criterios de aceptación](#8-plan-de-pruebas-y-criterios-de-aceptación)
9. [Límites que deben decirse con honestidad](#9-límites-que-deben-decirse-con-honestidad)
10. [Anexos](#10-anexos)

---

## 1. Confidencialidad: el archivo `secrets.toml` NO viene incluido

**El archivo `.streamlit/secrets.toml` se excluyó a propósito por confidencialidad.** Contiene la clave
`service_role` de Supabase (acceso total a la base de datos, saltándose RLS) y las claves de los proveedores de IA.
No se comparte por chat, correo, zip ni repositorio.

### 1.1 Qué hacer para obtener acceso

1. Pide las credenciales a la responsable del proyecto **por un canal seguro** (gestor de contraseñas compartido,
   por ejemplo Bitwarden/1Password, o en persona). Nunca por WhatsApp/correo en texto plano.
2. Alternativa recomendada para desarrollo: **crea tus propias cuentas y claves** (Supabase free, Google AI Studio,
   Groq) y un proyecto Supabase de desarrollo. Así no se toca la base de la demo.
3. Copia `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` y complétalo:

```toml
# --- Base de datos (Supabase > Project Settings > API Keys) ---
SUPABASE_URL = "https://<tu-proyecto>.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "<clave secreta service_role / secret>"   # NUNCA la anon/publishable

# --- IA (Groq primero: es el más rápido; Gemini de respaldo) ---
GROQ_API_KEY = "gsk_..."        # https://console.groq.com/keys
GEMINI_API_KEY = "AIza..."      # https://aistudio.google.com/apikey
HF_TOKEN = ""                   # vacío: la cuenta actual no tiene créditos (ver sección 5)

ORDEN_IA = "groq,gemini"
GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-3.8-flash"
```

### 1.2 Reglas para no filtrar secretos

- `.streamlit/secrets.toml` ya está en `.gitignore`. **Verifica antes de cada commit**: `git status` no debe listarlo.
- **Cada nombre una sola vez** en el TOML. Si se repite una clave (por ejemplo, dos `GEMINI_MODEL`), el archivo no
  carga (`TOMLDecodeError: Cannot overwrite a value`). Le pasó a la responsable durante la configuración.
- En **Streamlit Community Cloud** los secretos se pegan en *App settings → Secrets*, no en el repo.
- **Recomendación de seguridad:** durante la configuración se pegaron fragmentos de claves (enmascarados) en chats y
  terminales. Por precaución, **rota (regenera) las claves de Groq, Gemini y la `service_role` de Supabase** antes de
  la presentación pública y después de entregar el proyecto.
- Agregar un *pre-commit hook* con un detector de secretos (por ejemplo `gitleaks` o `detect-secrets`) — ver backlog.
- No subir PDFs reales con información confidencial de clientes a la demo (la app lo advierte en la portada).

---

## 2. Qué hace el producto

App para MYPE peruanas que venden al Estado. Se suben las **bases de una licitación (PDF)** y la app responde
**4 preguntas con pruebas** (página + cita textual + artículo de la norma):

| Pregunta | Qué evalúa | Fuente |
|---|---|---|
| **¿Es justa?** | Señales de posible direccionamiento: marca específica, experiencia desproporcionada, plazo muy corto, ISO sin relación con el objeto, muestras con poco tiempo | Reglas sobre el PDF + normativa (BM25) |
| **¿Puedo?** | Requisitos de las bases vs. perfil de la empresa | Reglas + perfil en Supabase |
| **¿Me conviene?** | Margen, costo de la carta fianza, multa máxima, días de pago | Reglas + números del usuario |
| **¿Puedo ganar?** | Procesos parecidos ya adjudicados: quién ganó, a qué precio, cuánta competencia | Datos abiertos OCDS (OECE) |

Además: recomendación (postular / observar primero / no te conviene), **índice de apertura 0–100**, borrador de
observación en Word, cronograma, checklist, asistente "Pregúntale a tus bases" (RAG local), y los módulos
**Inicio (panel)**, **Oportunidades**, **Seguimiento** y **Mi empresa**.

**Principio de diseño:** todo el análisis es **determinista (reglas)**. La IA solo **explica en simple** y responde
preguntas. Si no hay IA, la app sigue funcionando.

---

## 3. Cómo ejecutarlo

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Mac/Linux: source venv/bin/activate)
python -m pip install -r requirements.txt
python -m pytest -q              # esperado: 25 passed
python -m streamlit run app.py
```

- **Usar siempre `python -m ...`** en Windows. Se observó que el comando `streamlit` a secas resolvía al Python global
  (`...\Python313\Lib\site-packages`) y no al `venv`, lo que causó `ModuleNotFoundError: No module named 'pymupdf'`.
- `python probar_ia.py` prueba cada proveedor de IA por separado, sin abrir la app, y lista los modelos disponibles si
  uno da 404. Nunca imprime las claves.
- Supabase: ejecutar en el SQL Editor `supabase/01_esquema.sql` y luego `supabase/02_seguimiento_y_documentos.sql`.
- El error `ConnectionResetError [WinError 10054]` en la terminal de Windows es ruido de `asyncio` al cerrar pestañas;
  no afecta a la app.
- PDFs de prueba (ficticios, marcados como tales): `1_uniformes_observar.pdf`, `2_limpieza_postular.pdf`,
  `3_mobiliario_no_cumples.pdf` (perfil sugerido: rubro "Uniformes y textiles", experiencia S/ 320 000).

---

## 4. Arquitectura y mapa del código

```
           PDF de bases                                   Datos abiertos OCDS (cuaderno 02)
                │                                                   │
        core/pdf_parser.py ── páginas ──┐                  data/ocds/historial.csv
                                        ▼                           │
                              core/extraccion.py  (regex)           │
                       datos · requisitos · cronograma              │
                                        ▼                           ▼
     data/normativa/articulos.json → core/buscador.py (BM25) → core/preguntas.py ← core/historial_ocds.py
       (cuaderno 01)                                         4 preguntas + recomendación
                                                                    │
                       core/ia.py (Groq → Gemini → HF → sin IA)  ◄──┤  solo explicar / asistente
                                                                    ▼
   ui/*.py (Streamlit) ── core/db.py ──► Supabase (o memoria)   core/mercado.py · core/seguimiento.py
```

| Archivo | Responsabilidad | Notas para el revisor |
|---|---|---|
| `app.py` | `set_page_config`, barra lateral, menú, router de páginas, botón "Probar conexión con la IA" | El menú es un `st.radio(key="pagina")`; solo se cambia `ss.pagina` desde callbacks (`E.ir_a`) |
| `ui/tema.py` | Sistema visual: CSS, paleta, íconos SVG, componentes HTML (`kpis`, `encabezado`, `anillo`, `banner`…), estilo Altair | Mucho HTML en f-strings; ver 6.7 |
| `ui/estado.py` | Recursos cacheados (`repo`, `normativa`, `historial`, `mercado_df`), estado de sesión, acceso a datos con/ sin usuario | `_seguro` evita romper si faltan tablas nuevas |
| `ui/entrada.py` | Portada y acceso sin contraseña (código / crear / invitado) | Ver riesgos de seguridad 6.1 |
| `ui/inicio.py` | Panel: KPIs, plazos, decisiones, pulso de mercado | |
| `ui/revisar.py` | Subida del PDF, ficha, 4 pestañas (Ficha, Pruebas, Actuar, Preguntar) | `calcular()` se ejecuta en cada rerun (ver 6.8) |
| `ui/oportunidades.py` | Inteligencia de mercado OCDS: KPIs, 4 gráficos, tablas | |
| `ui/seguimiento.py` | Embudo, agenda, próximas acciones, tarjetas, aprendizaje | |
| `ui/empresa.py` | Perfil, posición en el mercado, "Para crecer", documentos | |
| `core/config.py` | Lectura de secretos, proveedores IA, **umbrales** y supuestos | Umbrales = criterio del sistema, no ley |
| `core/pdf_parser.py` | Leer PDF, huella SHA-256, imagen de página con cita resaltada | Sin OCR |
| `core/extraccion.py` | Regex: montos, marcas, plazos, ISO, muestras, garantía, penalidad, pago, adelanto, RNP, cronograma | Núcleo frágil: ver 6.3 |
| `core/preguntas.py` | Evalúa las 4 preguntas y la recomendación | Ver 6.4 |
| `core/buscador.py` | BM25 propio (sin embeddings) para normativa y páginas | |
| `core/historial_ocds.py` | Procesos parecidos, normalización de proveedores (SAC/EIRL…) | |
| `core/mercado.py` | Agregados para Oportunidades / Mi empresa | |
| `core/seguimiento.py` | Etapas, plazos, checklist, aprendizaje | |
| `core/ia.py` | Router de IA con respaldo, guardrails, diagnóstico, cambio automático de modelo | Ver sección 5 |
| `core/borrador.py` | Plantilla de observación + exportación a Word | |
| `core/db.py` | `RepoMemoria` / `RepoSupabase` (misma interfaz) | |
| `core/usuarios.py` | Generación de códigos sin contraseña | Ver 6.1 |
| `core/preparar.py` | Utilidades de preparación de datos usadas por cuadernos | |
| `notebooks/01_…` | Construye `articulos.json` (Ley 32069, Reglamento, modificación) | Colab |
| `notebooks/02_…` | Descarga OCDS, clasifica 19 rubros, genera `historial.csv` | Colab |
| `notebooks/03_…` | Mide aciertos de la extracción (opcional) | Colab |
| `supabase/01_esquema.sql`, `02_…sql` | Esquema + RLS activado sin políticas | Ver 6.6 |
| `tests/` | 25 pruebas pytest (motor, módulos, base) | Sin pruebas de UI en el repo |

**Datos incluidos:** `articulos.json` (967 artículos, 1,6 MB) y `historial.csv` (8 175 procesos adjudicados, 5,3 MB,
fechas del 26/11/2013 al 03/10/2026; rubros: Uniformes y textiles 5 083, Mobiliario 1 745, Limpieza 1 176, Útiles de
oficina 171). `historial_excluidos_para_revisar.csv` está en `.gitignore`.

---

## 5. Estado de la IA y lo que hay que arreglar

### 5.1 Qué pasó (diagnóstico del 23/10/2026)

| Proveedor | Síntoma | Causa | Estado actual |
|---|---|---|---|
| **Gemini** | `404 … gemini-2.5-flash is no longer available to new users` | Modelo retirado para cuentas nuevas | Cambiado a `gemini-3.8-flash`. Clave válida. **Intermitente: `503 high demand`** (saturación del lado de Google) y un `APITimeoutError` |
| **Groq** | `404 model_not_found` con `llama-3.3-70b-versatile` | Groq retiró Llama del plan gratuito (agosto 2026) | Cambiado a `openai/gpt-oss-120b`. **Funciona (≈0,6 s)**. Al principio respondía vacío (ver 5.2) |
| **Hugging Face** | `402 You have no remaining credits` | Cuenta sin créditos de *Inference Providers* | **No funciona**. `HF_TOKEN` debe quedar vacío hasta decidir (ver 5.3) |

Hubo además errores de configuración del lado del usuario, ya resueltos: claves duplicadas en el TOML y una clave mal
pegada (`401 Invalid API Key`).

### 5.2 Cambios ya aplicados en `core/ia.py` (revisar)

- **Orden por defecto `groq,gemini,hugging face`** (`core/config.py`, `proveedores_ia`).
- **Modelos "que razonan"** (`gpt-oss`, `gemini-3*`, `qwen3`): se envía `reasoning_effort="low"` (`pensar_poco`, `_llamar`).
  Sin esto, con `max_tokens` bajo, el razonamiento consumía todo el presupuesto y `content` llegaba vacío.
  Si el proveedor rechaza el parámetro (400 que menciona *reasoning*), se reintenta sin él.
- `max_tokens` subido a 1200 (explicación) y 1500 (asistente) en `ui/revisar.py`; `timeout` 45 s, `max_retries=1`.
- **Cambio automático de modelo**: si un modelo da 404, `modelo_alternativo()` lista los modelos de la cuenta
  (`client.models.list()`) y elige uno de chat según `PREFERIDOS`; reintenta y lo informa en el diagnóstico.
- **Diagnóstico**: `RouterIA.diagnosticar()` + botón en la barra lateral; `explicar_error()` traduce 401/403, 404,
  402, 429, 5xx y errores de conexión a mensajes en español; `revisar_formato_clave()` detecta claves pegadas en el
  campo equivocado (`AIza…` Gemini, `gsk_…` Groq, `hf_…` HF).
- En la UI, cuando la IA no responde se muestra **"¿Por qué no respondió la IA?"** con el motivo por proveedor.

### 5.3 Tareas pendientes para el revisor (IA)

| # | Prioridad | Tarea | Detalle / criterio de aceptación |
|---|---|---|---|
| IA-1 | **P0** | Decidir el 3.er proveedor | HF no tiene créditos. Opciones: (a) comprar créditos o plan PRO; (b) reemplazar por otro proveedor con API compatible con OpenAI y plan gratuito (evaluar disponibilidad y términos vigentes); (c) dejar solo Groq + Gemini. Actualizar `proveedores_ia()`, `PREFIJOS`, `PREFERIDOS` y `.example`. |
| IA-2 | **P0** | Reintentos con *backoff* para 429/5xx | Hoy, ante `503 high demand`, se pasa al siguiente proveedor sin reintentar. Añadir 1–2 reintentos con espera exponencial y *jitter* solo para 429/500/502/503/504, respetando `Retry-After`. No reintentar 401/402/404. |
| IA-3 | **P1** | *Circuit breaker* por proveedor | Si un proveedor falla N veces seguidas, saltarlo durante X minutos (guardar en `st.cache_resource`). Evita esperar 45 s por un proveedor caído en cada pregunta. |
| IA-4 | **P1** | Timeouts diferenciados | Groq responde en < 2 s: usar timeout corto (10–15 s) para fallar rápido y dejar el largo solo al último proveedor. Hoy todos usan 45 s. |
| IA-5 | **P1** | Fijar modelos y monitorear deprecaciones | Los proveedores retiran modelos sin aviso (pasó con dos de tres). Fijar los modelos en `secrets.toml`, registrar el modelo usado en `llm_llamadas` y revisar mensualmente las páginas de deprecación. El cambio automático (`modelo_alternativo`) es un salvavidas, no la solución: puede elegir un modelo menos adecuado. |
| IA-6 | **P1** | Validar `reasoning_effort` por proveedor/modelo | Confirmar en la documentación vigente qué valores acepta cada modelo (en algunos modelos Qwen los valores difieren). Hoy hay reintento sin el parámetro, pero conviene una tabla explícita. |
| IA-7 | **P2** | Caché de respuestas | Cachear (`st.cache_data`) por hash de (pregunta, contexto, modelo) para no gastar cuota en preguntas repetidas durante la demo. |
| IA-8 | **P2** | *Streaming* | Mostrar la respuesta mientras se genera (`stream=True` + `st.write_stream`) para mejor percepción de velocidad. |
| IA-9 | **P2** | Registro útil en `llm_llamadas` | Hoy no se guarda `analisis_id` ni el texto de la pregunta. Agregar `analisis_id`, `tarea`, `modelo` real usado y tokens de razonamiento si el proveedor los devuelve. Construir un mini tablero de latencia/errores. |
| IA-10 | **P2** | Evaluar calidad del asistente | Crear 20–30 preguntas con respuesta esperada sobre las bases de prueba y medir: respuesta correcta, cita la página correcta, dice "no sé" cuando no hay fuente. (El plan original mencionaba RAGAS; con un set pequeño basta.) |
| IA-11 | **P2** | Guardrails | El texto del PDF va dentro de `<documento>` y hay instrucciones contra acusaciones (`SISTEMA`, `limpiar_salida`). Falta: prueba de *prompt injection* (bases con texto tipo "ignora las instrucciones"), límite de longitud de la pregunta y bloqueo de solicitudes fuera de tema. |

---

## 6. Revisión detallada por área

Severidad: **Alta** (riesgo real o error visible) · **Media** (limita resultados o mantenimiento) · **Baja** (mejora).

### 6.1 Seguridad y privacidad

| Sev. | Hallazgo | Dónde | Propuesta |
|---|---|---|---|
| **Alta** | **El código de acceso es adivinable.** Formato `nombre-apellido-NNNN` con solo 9 000 combinaciones por nombre (`secrets.randbelow(9000)+1000`). Conociendo el nombre de una empresa, se puede probar por fuerza bruta. No hay límite de intentos. | `core/usuarios.py:33-37`, `ui/entrada.py` (botón Entrar) | Para la demo: sufijo aleatorio más largo (6–8 caracteres base32) y límite de intentos por sesión/IP. Para producción: **Supabase Auth** con *magic link* por correo u OTP por SMS/WhatsApp. |
| **Alta** | **Aislamiento entre usuarios solo en el código de la app.** Se usa la clave `service_role` (salta RLS); todas las consultas filtran `usuario_id` a mano. Un error en un filtro expondría datos de otras empresas. | `core/db.py` (`RepoSupabase`), SQL con RLS sin políticas | Migrar a Supabase Auth y **políticas RLS** `usuario_id = auth.uid()`, usando la clave `anon` + JWT del usuario. Mientras tanto, pruebas automáticas que verifiquen que cada método filtra por `usuario_id`. |
| Media | Códigos guardados en texto plano en `usuarios.codigo`. | `supabase/01_esquema.sql` | Guardar hash (por ejemplo SHA-256 con *pepper* en secretos) y comparar por hash. |
| Media | **Protección de datos personales (Ley N.° 29733).** No hay aviso de privacidad, consentimiento, ni opción de exportar o borrar datos. | Portada / Mi empresa | Agregar aviso de privacidad, casilla de aceptación, botón "Borrar mi cuenta y datos" (el `on delete cascade` ya existe) y política de retención. |
| Media | `resultado` (jsonb) guarda citas textuales de las bases. Si un usuario sube documentos internos, quedan en la base. | `analisis.resultado` | Documentar la retención; opción de no guardar citas o caducarlas. |
| Baja | Fuente tipográfica cargada desde Google Fonts (`@import`) → solicitud externa en cada carga. | `ui/tema.py:67`, `.streamlit/config.toml` | Servir la fuente localmente (Streamlit `static` + `[[theme.fontFaces]]`) si se exige no depender de terceros. |
| Baja | Sin detector de secretos en el repo. | — | `pre-commit` con `gitleaks`/`detect-secrets`. |

### 6.2 Inteligencia artificial

Ver la sección 5. Además:

| Sev. | Hallazgo | Dónde | Propuesta |
|---|---|---|---|
| Media | `temperature=0.2` fijo para todos los modelos. Algunos modelos recientes recomiendan otros valores o ignoran el parámetro. | `core/ia.py` (`_crear`) | Parametrizar por proveedor en `config.py`. |
| Media | Contexto del asistente: 3 páginas completas (hasta 2 500 caracteres cada una) + 2 artículos (1 500). Sin control de tokens totales. | `ui/revisar.py` (`tab_preguntar`) | Recortar por fragmentos (párrafos) en lugar de páginas enteras; calcular tokens aproximados. |
| Baja | `resumen_sin_ia` es correcto pero genérico. | `core/ia.py` | Plantillas más ricas por tipo de recomendación. |

### 6.3 Extracción por reglas (`core/extraccion.py`) — el núcleo más frágil

Todo depende de expresiones regulares sobre el texto del PDF. Funciona muy bien con las bases de prueba, pero
**no se ha medido con un corpus amplio de bases reales**.

| Sev. | Hallazgo | Propuesta |
|---|---|---|
| **Alta** | **Sin OCR.** Los PDF escaneados (frecuentes en municipalidades) no tienen texto: la app avisa, pero el análisis sale vacío. | Integrar OCR (por ejemplo, PyMuPDF con Tesseract o un servicio OCR) para páginas detectadas por `paginas_sin_texto()`. |
| **Alta** | **Falta medir precisión con bases reales.** El cuaderno `03_opcional_medir_aciertos.ipynb` existe, pero no hay un set etiquetado. | Reunir 30–50 bases integradas del SEACE (varios rubros y entidades), etiquetar a mano los campos y medir precisión/recall por campo. Usar el resultado en el pitch. |
| Media | **Tablas.** El cronograma y los requisitos suelen venir en tablas; `get_text("text")` puede desordenar celdas. La ventana del cronograma es de 160 caracteres (`extraccion.py:258`). | Probar `page.find_tables()` de PyMuPDF para el cronograma; ampliar y validar la ventana. |
| Media | **Experiencia:** solo se detecta la frase "monto facturado acumulado". Otras redacciones (p. ej. "experiencia del postor … no menor a S/") se pierden. | Ampliar patrones; agregar pruebas con redacciones reales. |
| Media | **Valor estimado:** exige "valor estimado/referencial" + `S/` a ≤160 caracteres. No reconoce montos en letras ni tablas de ítems; el requerimiento real de la Municipalidad de Chiclayo revisado no trae el valor. | Patrones adicionales; sumar ítems; pedir el valor al usuario si no se encuentra. |
| Media | **Entidad:** lista fija de palabras en MAYÚSCULAS (`ENTIDADES`). Falla con nombres en minúsculas o entidades no listadas (p. ej. "Superintendencia…" sí, "Autoridad…" no). | Buscar también "Entidad contratante:" y normalizar contra la lista de entidades del OCDS. |
| Media | **Marca:** heurística con exclusiones (`NO_ES_EXIGENCIA_DE_MARCA`, `EQUIVALENTE`). Posibles falsos positivos (marca mencionada como referencia) y falsos negativos (marca en tabla). | Casos de prueba con frases reales; evaluar un clasificador ligero o IA *solo para confirmar* (con cita verificada). |
| Baja | Montos en letras ("un millón…") no se interpretan. | Parser de números en palabras (opcional). |
| Baja | Fechas solo `dd/mm/aaaa` y "dd de mes de aaaa" con año 20xx. | Añadir "dd.mm.aa" y rangos con "al". |

### 6.4 Lógica de las 4 preguntas (`core/preguntas.py`)

| Sev. | Hallazgo | Dónde | Propuesta |
|---|---|---|---|
| **Alta** | **"RNP vigente" siempre sale como cumplido.** Usa `perfil.get("rnp_vigente", True)`, pero el perfil no tiene ese campo. | `preguntas.py:112`, `ui/empresa.py`, `core/db.py` (`CAMPOS_EMPRESA`) | Agregar la casilla "RNP vigente" (y fecha de vencimiento) al perfil y a la tabla `empresas`; o derivarlo del documento "Constancia RNP" en Mis documentos. |
| Media | Datos del perfil **no usados**: `produccion_mensual`, `maquinas`, `personal`, `es_mype`. | `evaluar_puedo` | Usarlos: capacidad de producción vs. cantidad y plazo de entrega; `es_mype` para la retención en lugar de garantía y para beneficios MYPE. |
| Media | **Umbrales sin sustento documentado** (`UMBRALES` en `config.py:59`): experiencia > 1× media, > 1,5× fuerte; plazo ≤ 10 días, etc. | `core/config.py` | Validarlos con un abogado o especialista en contrataciones y con las bases estándar vigentes; documentar la fuente de cada umbral. |
| Media | **Índice de apertura** = 100 − 25·fuerte − 12·media − 5·leve: pesos arbitrarios. | `ui/tema.py:383` (`indice_apertura`) | Moverlo a `core/` con pruebas; calibrar con el corpus etiquetado. Mantener la leyenda "criterio LiciGuard, no conclusión legal". |
| Media | **¿Me conviene?** No considera IGV, costo financiero de esperar el pago (días de pago × capital), ni adelantos. `meses_contrato` = 3 por defecto. | `preguntas.py:142-170` | Añadir costo financiero (tasa mensual editable), IGV y adelanto. |
| Media | **¿Puedo ganar?** Coincidencia por palabras de entidad (≥ mitad) y del objeto; puede traer procesos poco parecidos o perder sinónimos. `n_postores` = participantes **registrados**, no ofertas. | `historial_ocds.py:50-67` | Mejorar similitud (n-gramas, sinónimos por rubro), mostrar el puntaje de parecido, filtrar por rango de valor y años recientes. |
| Baja | Reglas de `recomendar()` simples y en cascada. | `preguntas.py:208` | Tabla de decisión explícita y probada caso por caso. |

### 6.5 Datos (OCDS, normativa y cuadernos)

| Sev. | Hallazgo | Propuesta |
|---|---|---|
| Media | `historial.csv` es una **foto** (al 03/10/2026). Oportunidades muestra procesos **ya adjudicados**, no convocatorias abiertas. | Actualización programada (mensual) con el cuaderno 02 o un job; mostrar "datos al dd/mm/aaaa" en la UI. Fase 2: convocatorias en tiempo real desde el SEACE. |
| Media | Incluye procesos 2013–2017 con huecos (2018–2020 casi vacíos). La UI filtra desde 2021 por defecto, pero `procesos_parecidos` usa todo. | Filtrar por años recientes en "¿Puedo ganar?" o ponderar por recencia. |
| Media | Normativa: 967 artículos cortados automáticamente; algunos artículos salen partidos ("Artículo 44 (parte 2)") y los títulos se generan del texto. | Revisión manual de los artículos más citados; versionar la normativa con fecha. |
| Baja | Archivos de datos grandes en el repo (5,3 MB + 1,6 MB). | Aceptable para la demo; a futuro, Supabase Storage o Git LFS. |
| Baja | Cuadernos de Colab sin pruebas. | Extraer funciones a `core/preparar.py` (ya existe en parte) y probarlas. |

### 6.6 Base de datos (Supabase)

| Sev. | Hallazgo | Dónde | Propuesta |
|---|---|---|---|
| Media | **Tablas sin uso:** `requisitos` y `hallazgos` se crean pero nunca se escriben (todo va en `analisis.resultado` jsonb). | `01_esquema.sql` | Usarlas (permite consultas y métricas por tipo de hallazgo) o eliminarlas para evitar confusión. |
| Media | `llm_llamadas.analisis_id` nunca se llena. | `core/ia.py`, `core/db.py` | Pasar el `analisis_id` al router. |
| Media | Errores de Supabase en `guardar_analisis`/`guardar_empresa` **no se capturan** (sí en seguimiento/documentos con `_seguro`). Si la BD falla, la app muestra un error técnico. | `ui/estado.py` | Envolver todas las escrituras con manejo de error y mensaje amable. |
| Baja | Sin migraciones versionadas (dos scripts sueltos). | `supabase/` | Usar `supabase/migrations` con la CLI. |
| Baja | Sin `check` en `seguimiento.recomendacion`; sin triggers de `actualizado_en`. | `02_…sql` | Añadir. |

### 6.7 Interfaz (Streamlit)

| Sev. | Hallazgo | Dónde | Propuesta |
|---|---|---|---|
| Media | **Zona horaria:** `date.today()` usa la hora del servidor. En Streamlit Cloud (UTC) los "días que faltan" y la fecha del borrador pueden salir con un día de diferencia por la noche en Lima. | `core/seguimiento.py:49`, `core/borrador.py:30`, `ui/tema.py:251` | Usar `datetime.now(ZoneInfo("America/Lima")).date()` en una función común. |
| Media | Mucho **HTML en f-strings** dentro de `ui/*.py` (difícil de mantener y de testear; riesgo de olvidar `esc()` en algún dato). | `ui/` | Mover a plantillas/componentes; revisar que todo texto de usuario o del PDF pase por `esc()`. |
| Media | El borrador dice siempre **"Lima,"** como ciudad. | `core/borrador.py:30` | Usar la región del perfil. |
| Baja | El cargador de archivos muestra "Upload" y "25MB per file" en inglés (texto propio de Streamlit). | `ui/revisar.py` | Aceptar o cubrir con CSS/texto propio. |
| Baja | Accesibilidad: parte del significado depende del color (verde/ámbar/rojo). | `ui/tema.py` | Ya hay etiquetas de texto en la mayoría; revisar contraste y `aria-label`. |
| Baja | Diseño probado en escritorio (1440 px). No verificado en celular. | — | Probar a 390 px; ajustar columnas. |
| Baja | Guardar en historial tras editar costos es manual ("Guardar cambios en mi historial"). | `ui/revisar.py` | Guardado automático con *debounce*. |

### 6.8 Rendimiento

| Sev. | Hallazgo | Propuesta |
|---|---|---|
| Media | `calcular()` re-ejecuta `analizar()` completo (regex + BM25 de normativa por hallazgo + búsqueda OCDS) **en cada rerun**, por ejemplo al escribir un número. | Cachear por `(sha, hash del perfil, entradas)` con `st.cache_data`, o separar el análisis fijo (por PDF) del cálculo de "¿Me conviene?". |
| Media | `ss.pdfs` guarda los bytes del PDF (hasta 25 MB c/u) en memoria de sesión, sin límite. | Mantener solo los últimos N o guardar en disco temporal / Supabase Storage. |
| Baja | `imagen_pagina_resaltada()` re-renderiza la página en cada rerun. | `st.cache_data` por `(sha, página, cita)`. |
| Baja | El índice BM25 de páginas se reconstruye en cada pregunta. | Cachear por `sha`. |

### 6.9 Calidad de código, pruebas y despliegue

| Sev. | Hallazgo | Propuesta |
|---|---|---|
| Media | **Dependencias sin fijar** (`streamlit>=1.50`, etc.). Una versión nueva puede romper la UI (el CSS depende de `data-testid`). | Fijar versiones exactas (`pip freeze` / `uv lock`) y separar `requirements-dev.txt` (pytest, ipykernel). |
| Media | **Sin pruebas de UI en el repo** (se usaron AppTest y Playwright fuera del repo durante el desarrollo). | Agregar `tests/test_app.py` con `streamlit.testing.v1.AppTest` (recorrido de las 5 páginas como invitado) y un e2e opcional con Playwright. |
| Media | **Sin CI.** | GitHub Actions: `ruff` + `pytest` en cada push. |
| Baja | Sin linter/formatter configurado. | `ruff` con `pyproject.toml`. |
| Baja | Requiere Python ≥ 3.11 (`X | None`, `tomllib` en `probar_ia.py`). | Documentarlo en el README y en `pyproject.toml`. |
| Baja | El CSS depende de selectores internos de Streamlit (`data-testid`, `stSidebar`, `role=radiogroup`). | Revisar visualmente después de cada actualización de Streamlit. |

---

## 7. Backlog priorizado

**P0 = antes de la demo / presentación · P1 = siguiente iteración · P2 = mejora continua**

| # | Prio. | Tarea | Área | Esfuerzo |
|---|---|---|---|---|
| 1 | P0 | Rotar claves (Groq, Gemini, Supabase `service_role`) y confirmar que `secrets.toml` no está en ningún repo/zip | Seguridad | 0,5 h |
| 2 | P0 | Decidir 3.er proveedor de IA (HF sin créditos) y dejar `HF_TOKEN=""` mientras tanto | IA | 1 h |
| 3 | P0 ✅ | Reintentos con backoff para 429/5xx (Gemini 503) | IA | 2 h |
| 4 | P0 ✅ | Corregir "RNP vigente siempre cumple" (campo en perfil + tabla) | Lógica | 1–2 h |
| 5 | P0 | Ensayo de demo con los 3 PDFs ficticios + 2 bases reales del SEACE; probar con hotspot (red corporativa) | QA | 2 h |
| 6 | P1 ✅ | Códigos de acceso más largos + límite de intentos (o Supabase Auth) | Seguridad | 3–6 h |
| 7 | P1 ✅ | Circuit breaker y timeouts diferenciados por proveedor | IA | 2–3 h |
| 8 | P1 | Corpus de 30–50 bases reales etiquetadas + medir precisión (cuaderno 03) | Extracción | 1–2 días |
| 9 | P1 | Ampliar patrones (experiencia, valor estimado, entidad) según el corpus | Extracción | 1 día |
| 10 | P1 ✅ | Zona horaria America/Lima en todas las fechas | UI | 1 h |
| 11 | P1 ✅ | Cachear `calcular()` e imágenes de páginas | Rendimiento | 2–3 h |
| 12 | P1 | Fijar dependencias + CI (ruff + pytest + AppTest) | Calidad | 3 h |
| 13 | P1 ✅ | Manejo de errores de Supabase en todas las escrituras | BD | 1–2 h |
| 14 | P1 | Aviso de privacidad (Ley 29733) + borrar mi cuenta | Privacidad | 3 h |
| 15 | P2 | OCR para PDFs escaneados | Extracción | 1–2 días |
| 16 | P2 | Lectura de tablas (cronograma) con `find_tables()` | Extracción | 1 día |
| 17 | P2 | Usar producción, máquinas, personal y MYPE en "¿Puedo?" | Lógica | 1 día |
| 18 | P2 | Costo financiero + IGV + adelantos en "¿Me conviene?" | Lógica | 0,5 día |
| 19 | P2 | Validar umbrales con especialista y documentar fuentes | Lógica | — |
| 20 | P2 | RLS con `auth.uid()` (Supabase Auth) | Seguridad | 1–2 días |
| 21 | P2 | Usar o eliminar tablas `requisitos`/`hallazgos`; migraciones versionadas | BD | 0,5 día |
| 22 | P2 | Caché + streaming de respuestas IA; evaluación del asistente (20–30 preguntas) | IA | 1 día |
| 23 | P2 | Actualización programada de OCDS y "datos al…" en la UI; convocatorias en tiempo real (fase 2) | Datos | 1 día + |
| 24 | P2 | Alertas de plazos por correo/WhatsApp | Producto | 1–2 días |
| 25 | P2 | Refactor del HTML de la UI a componentes; prueba en móvil | UI | 1–2 días |

---

## 8. Plan de pruebas y criterios de aceptación

### 8.1 Automáticas (existentes)

`python -m pytest -q` → **25 passed** (`tests/test_base.py`, `test_motor.py`, `test_modulos.py`). Cubren montos
peruanos, extracción, las 4 preguntas, cronograma, normalización de proveedores, mercado y seguimiento.

### 8.2 Recorrido manual (5 minutos)

| Paso | Esperado |
|---|---|
| Portada → "Es mi primera vez" → nombre | Se crea el código y se muestra en Inicio |
| Mi empresa → rubro "Uniformes y textiles", experiencia 320 000 → Guardar | KPIs del perfil y "Para crecer" con datos |
| Revisar bases → `1_uniformes_observar.pdf` | **Observar primero**, índice ≈ 21/100, 5 alertas, "1 de 5" requisitos, 8 procesos previos |
| `2_limpieza_postular.pdf` | **Postular**, sin alertas |
| `3_mobiliario_no_cumples.pdf` | **No te conviene**, salida "consorcio" en Actuar |
| Pruebas en el PDF | Página con la cita resaltada + artículo de la norma |
| Explícamelo simple | "Explicado por: Groq" (o motivo visible si falla) |
| Pregúntale a tus bases → "¿Cuánto es la penalidad por atraso?" | Respuesta con página 6 y artículos |
| Barra lateral → Simular caída de Groq → repetir | Responde el siguiente proveedor, o muestra "¿Por qué no respondió la IA?" |
| Seguimiento | Proceso con plazo, embudo, próximas acciones |
| Probar conexión con la IA | Groq OK; Gemini OK o "saturado (temporal)" |

### 8.3 Criterios para considerar resuelto el problema de las IA

- `python probar_ia.py` muestra **OK** en al menos 2 proveedores.
- Con un proveedor caído (simulado), la respuesta llega en **< 10 s** usando el siguiente.
- Ningún error técnico en inglés llega a la pantalla sin su explicación en español.

---

## 9. Límites que deben decirse con honestidad

- Las señales son **alertas para revisar**, no conclusiones legales. La decisión es de la persona.
- Umbrales e índice de apertura son **criterios del sistema**, pendientes de validación con especialistas.
- "Participantes" en datos abiertos = **registrados**, no ofertas presentadas.
- Oportunidades usa procesos **ya adjudicados**; las convocatorias abiertas en tiempo real son la siguiente fase.
- PDFs escaneados no se analizan (falta OCR).
- Acceso sin contraseña = solo para demo.
- Los artículos de la norma se encuentran por búsqueda: **confirmarlos antes de citarlos** en una observación real.

---

## 10. Anexos

### 10.1 Variables de `secrets.toml`

| Variable | Obligatoria | Uso |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | No (sin ellas: modo local en memoria) | Persistencia |
| `GROQ_API_KEY` | Recomendada | IA principal |
| `GEMINI_API_KEY` | Recomendada | IA de respaldo |
| `HF_TOKEN` | No (vacío) | 3.er proveedor, sin créditos hoy |
| `ORDEN_IA` | No | Orden de proveedores (`groq,gemini,hugging face` por defecto) |
| `GROQ_MODEL`, `GEMINI_MODEL`, `HF_MODEL` | No | Fijar modelos (por defecto `openai/gpt-oss-120b`, `gemini-3.8-flash`, `Qwen/Qwen2.5-72B-Instruct`) |

### 10.2 Comandos útiles

```powershell
# Buscar nombres de modelos en el proyecto (incluye secrets.toml, sin mostrar claves)
Get-ChildItem -Recurse -File -Include *.py,*.toml -Exclude *.example |
  Select-String -Pattern "gemini-|gpt-oss|llama|Qwen"

# Ver forma de las claves sin exponerlas (largo, 4 primeras y 2 últimas letras)
python -c "import tomllib; s=tomllib.loads(open('.streamlit/secrets.toml',encoding='utf-8-sig').read()); [print(k, len(v), v[:4], v[-2:]) for k,v in s.items() if 'KEY' in k or 'TOKEN' in k]"

# Probar IA sin abrir la app
python probar_ia.py
```

### 10.3 Errores ya vistos y su solución

| Error | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'pymupdf'` | `streamlit` corría con el Python global | `python -m pip install -r requirements.txt` y `python -m streamlit run app.py` |
| `TOMLDecodeError: Cannot overwrite a value` | Claves repetidas en `secrets.toml` | Dejar cada nombre una sola vez |
| `404 model … no longer available / model_not_found` | Modelo retirado | Actualizar `*_MODEL`; el router intenta otro modelo automáticamente |
| `401 Invalid API Key` / `400 Please pass a valid API key` | Clave mal pegada | Volver a copiar desde la consola del proveedor |
| `402 no remaining credits` (HF) | Sin créditos | `HF_TOKEN = ""` o comprar créditos |
| `503 high demand` (Gemini) | Saturación temporal | Reintentar; el router pasa al siguiente proveedor |
| Respuesta vacía de Groq | Modelo razonador sin espacio de tokens | Ya corregido (`reasoning_effort="low"`, más `max_tokens`) |
| `ConnectionResetError [WinError 10054]` | Ruido de asyncio en Windows | Ignorar |

---

*Documento preparado a partir de una revisión del código fuente y de las pruebas realizadas el 23/10/2026. Las
referencias de línea son aproximadas y pueden moverse con cambios futuros.*
