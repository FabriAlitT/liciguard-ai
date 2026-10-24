# Cambios — versión 3.3 (24/10/2026): varias empresas, todo filtrado por rubro y asistente

Pruebas: **78 passed**. Probado en el navegador (computadora y celular).

- **Varias empresas por persona** (p. ej. un consultor con varios clientes). Al entrar se elige la empresa en
  **cartas**; todo lo que se ve y se guarda (revisiones, seguimiento, documentos) es solo de esa empresa.
  «Cambiar de empresa» en el menú; «Eliminar esta empresa» en Mi empresa. Quien tiene una sola entra directo.
  Requiere `supabase/06_varias_empresas.sql` (sin él, la app sigue con una empresa por persona).
- **Demo guiada**: «Ver la demo» muestra 4 empresas de ejemplo; al elegir una se abre la ficha de unas bases de su
  rubro con el recorrido guiado. **8 bases ficticias** (2 por rubro: una para postular y otra con alertas).
- **Todo filtrado por el rubro** de la empresa activa: Ejemplos, Oportunidades (rubro fijo), Inicio y los títulos.
- **Asistente flotante** («Pregúntale a LiciGuard»), con el contexto de la empresa y de la pantalla (ficha abierta,
  documentos, plazos, normativa). Guardrails: largo máximo, se niega a temas ajenos, a cambiar sus reglas o revelar
  instrucciones y a dar datos de otras personas; la IA responde FUERA_DE_TEMA si algo se escapa; sin IA responde
  con reglas (glosario, guía de la app y datos de la ficha). `core/asistente.py`, `ui/asistente.py`.
- En el celular el menú lateral empieza cerrado para no tapar la ficha ni el recorrido.

# Cambios — versión 3.2 (24/10/2026): app más fácil de recorrer

Pruebas: **71 passed**. Recorrido guiado y ayudas probados en el navegador.

- **Recorrido guiado (5 pasos)** de la ficha de decisión: resalta cada parte (recomendación, datos clave, las 4
  preguntas, pestañas y menú) con una burbuja «Siguiente / Atrás / Saltar». Arranca solo con «Ver la demo» y
  también desde el menú («Recorrido guiado (1 min)») o desde la ficha de un ejemplo. (`ui/guia.py`)
- **Ayudas al pasar el cursor**: cada página del menú dice qué hace; cada indicador (con «?») explica qué significa.
- **Glosario**: RNP, MYPE, garantía, carta fianza, retención, consorcio, buena pro, IGV… se subrayan con puntos y
  muestran su significado; además hay un «Glosario» en el menú. Textos en `core/ayuda.py`.
- **Guía de cada página** («¿Para qué sirve?» con 3 pasos), que se cierra con la X y vuelve con «Volver a mostrar
  las guías».
- **Siguiente paso** al final de cada página, según lo que te falta (p. ej. sin perfil → Mi empresa).
- Corrección: pruebas aisladas del `secrets.toml` real (Streamlit lo copiaba a variables de entorno);
  `supabase/05_permisos.sql` y aviso claro si Supabase niega permisos (la app ya no se cae).
- Pestañas con el nuevo estilo de Streamlit 1.66.

# Cambios — versión 3.1 (24/10/2026): Ejemplos en 1 clic y más color

Pruebas: **66 passed**. Recorrido probado en el navegador (portada → demo → Ejemplos → Mi empresa → Inicio).

- **Nueva página «Ejemplos»** (`ui/ejemplos.py`, `core/ejemplos.py`):
  - 4 **empresas modelo** (uniformes, limpieza, mobiliario, útiles) que llenan *Mi empresa* y sus documentos con
    fechas calculadas desde hoy (vigentes, por vencer y vencidos). No se duplican si cargas dos veces.
  - **Galería de bases**: las 3 ficticias (cada una con su empresa sugerida, su resultado esperado y cifras de
    ejemplo para «¿Me conviene?») + las reales de `ejemplos/reales/` (con `catalogo.csv`) + las que bajaste en
    `data/bases/` (solo en tu PC).
  - **Demo completa en 1 clic** desde la portada (entra como invitado), Inicio, Ejemplos y Revisar bases.
- `bajar_bases_reales.py --a-galeria 4`: copia las mejores bases útiles a `ejemplos/reales/` con su catálogo.
- **Más color**: menú lateral con un color por página, botones de colores (secundarios azul suave, descargas en
  verde, enlaces en violeta, borrar en rojo, ejemplos con el color de su tarjeta), indicadores con barra de color,
  pestañas en degradado, cargador de PDF en español («Elegir PDF»), bandas de demo en degradado.
- El cuadro «Revisando tus bases… Listo» desaparece al terminar.

# Cambios — versión 3 (23/10/2026, noche)

Base: la "versión mejorada" del 23/10 (secciones de más abajo). Encima se agregó lo pendiente del pedido.
Pruebas: **56 passed** (40 anteriores + 16 nuevas). Recorrido completo probado en el navegador sin errores.

## A. Cloudflare Workers AI como segunda IA (reemplaza a Hugging Face, que ya no da crédito gratis)
- Orden por defecto: **Groq → Cloudflare → Gemini → Hugging Face (si tiene clave)**. Usa los mismos reintentos,
  pausas y caché de la versión anterior. Modelo: `@cf/openai/gpt-oss-120b`.
- Necesita `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN` en `secrets.toml` (si falta uno, la barra lateral lo
  avisa en «Probar conexión con la IA»). `probar_ia.py` (versión 4) también prueba Cloudflare.
- Archivos: `core/config.py` (`proveedores_ia`, `avisos_configuracion`, `TIMEOUTS_IA`), `core/ia.py`, `probar_ia.py`,
  `.streamlit/secrets.toml.example`.

## B. «¿Puedo?» usa producción, máquinas, personal y la condición MYPE
- Nuevo dato extraído de las bases: **cantidad requerida** (p. ej. «2 400 prendas»), `core/extraccion.py`.
- Nuevo requisito **«Capacidad para entregar a tiempo»**: producción mensual × plazo vs. cantidad. Si no alcanza,
  dice cuánto falta y propone salidas (máquinas extra con tu ritmo actual, subcontratar/consorcio, observar el plazo).
  Sin dato de producción sale «Verifica».
- Si las bases permiten **retención MYPE** y la empresa es MYPE, aparece como **beneficio** (no cuenta como requisito).
- Corrección de la revisión: una **Constancia RNP sin fecha** ya no se da por vigente; el formulario de Mi empresa
  muestra si la fecha de tus documentos está mandando sobre lo que marcaste.

## C. «¿Me conviene?» con IGV y costo financiero
- La ganancia ahora descuenta el **IGV (18 %)** incluido en la oferta y el **costo de financiarte** (capital × tasa
  mensual × meses hasta que te pagan = plazo de entrega + días de pago). Si eres MYPE y las bases lo permiten, usa la
  **retención** en lugar de la carta fianza. Supuestos editables: % mensual del dinero y «mi oferta incluye IGV».
- **Ojo:** los márgenes bajan respecto de la versión anterior (antes no se descontaba el IGV). Es lo correcto.

## D. Plataforma
- **Lecturas de Supabase protegidas:** si la base no responde al leer el perfil o el historial, la app sigue y avisa.
- **Límite de intentos por IP más permisivo (25) y por sesión estricto (5):** así varias personas detrás de la misma
  IP (oficina, servidor) no se bloquean entre sí.
- **Privacidad (Ley 29733):** aviso de privacidad (`core/privacidad.py`; completar responsable y contacto), casilla
  obligatoria al crear el código (se guarda la fecha), y en Mi empresa → **Tus datos y privacidad**: descargar mis
  datos (JSON) y **borrar mi cuenta** (pide escribir el código). SQL nuevo: `supabase/04_privacidad.sql`.
- **Versiones fijas** en `requirements.txt` (las probadas) y `requirements-dev.txt` (pytest) aparte.

## E. Pruebas y datos de prueba
- `tests/test_app.py`: **pruebas de pantallas** con AppTest (portada, privacidad obligatoria, límite de intentos,
  invitado en las 5 páginas, ficha completa con las 4 preguntas, explicación sin IA, borrar cuenta).
- `notebooks/04_bajar_bases_reales.ipynb` + `core/bases_reales.py`: baja **bases reales del SEACE** a partir de los
  enlaces de `historial.csv`, descarta RAR/Word/escaneados y prueba LiciGuard en todas. Probado sin internet
  (con descargas simuladas); **la descarga real desde el SEACE no se pudo probar desde aquí**.
- `ejemplos/`: 3 bases ficticias (observar / postular / no conviene) y el script que las crea.

## Pendiente
Rotar claves; corpus etiquetado con bases reales y mejorar patrones; OCR; Supabase Auth + RLS; CI en GitHub;
completar responsable/contacto del aviso de privacidad y revisarlo con un abogado.

---

# Cambios — versión mejorada (23/10/2026)

Mejoras del backlog P0/P1 de `docs/REVISION_TECNICA.md`. Pruebas: **40 passed** (25 originales + 15 nuevas en
`tests/test_mejoras.py`). Recorrido completo probado en el navegador (crear código → Mi empresa → subir bases →
¿Puedo? → Actuar) sin errores.

## 1. «RNP vigente» ya no sale siempre como cumplido (backlog #4, P0)
- **Antes:** `perfil.get("rnp_vigente", True)` → si el perfil no tenía el dato, se daba por cumplido.
- **Ahora:** en *Mi empresa* hay una pregunta «¿Tu inscripción en el RNP está vigente?» (Sí / No / No lo he registrado).
  - Si no lo registraste → el requisito sale **«Verifica»** (ámbar) con la salida «Marca en Mi empresa…».
  - Si registraste una **«Constancia RNP»** en *Tus documentos*, **su fecha de vencimiento manda** sobre lo marcado
    (vigente → cumple; vencida → no cumple).
- Archivos: `core/preguntas.py`, `core/seguimiento.py` (`rnp_segun_documentos`, `perfil_efectivo`), `ui/empresa.py`,
  `core/db.py`, `supabase/01_esquema.sql`, **nuevo** `supabase/03_rnp_vigente.sql`.
- Si la base de Supabase aún no tiene la columna, el perfil se guarda igual (sin ese campo) y la app avisa.
- **Ojo en la demo:** con un perfil sin RNP registrado, «¿Puedo?» cuenta un requisito cumplido menos que antes
  (antes contaba el RNP como cumplido sin saberlo). Marca «Sí, vigente» en Mi empresa para la demo.

## 2. IA más resistente (backlog #3 y #7; IA-2, IA-3, IA-4, IA-7)
`core/ia.py` + parámetros en `core/config.py`:
- **Reintentos con espera exponencial + jitter** solo para errores temporales (429/500/502/503/504). Respeta
  `Retry-After`; si el proveedor pide esperar más de 6 s, pasa directo al siguiente. Nunca reintenta 401/402/403/404.
  (El cliente `openai` ahora usa `max_retries=0` para que no se dupliquen los reintentos.)
- **Tiempo límite por proveedor:** Groq 15 s, Gemini 25 s, Hugging Face 30 s; el **último** proveedor disponible
  siempre tiene 45 s. Antes todos tenían 45 s.
- **Pausa automática (circuit breaker):** un proveedor con 3 fallas seguidas se salta 5 min; con error de clave o
  sin créditos (401/402/403/404), 30 min. Se comparte entre todas las sesiones del servidor. Si todos están en pausa,
  se prueban igual. Un acierto (o «Probar conexión con la IA») lo reactiva.
  La barra lateral muestra «Gemini (en pausa 4 min)» y un botón **«Reactivar IA en pausa»**.
- La **caída simulada** de la demo no cuenta como falla real (no pausa al proveedor).
- **Caché de respuestas:** la misma pregunta con el mismo contexto no vuelve a gastar cuota («respuesta guardada»).
- «¿Por qué no respondió la IA?» ahora también explica los proveedores saltados y los timeouts.
- Indicadores de carga («Pidiendo la explicación a la IA…») mientras responde.

## 3. Códigos de acceso más seguros (backlog #6, P1)
- Formato nuevo `nombre-apellido-k7m4qx`: 6 caracteres de 31 símbolos (≈ 887 millones de combinaciones por nombre,
  antes 9 000). Sin `0/o/1/l/i` para que no se confundan al copiarlos. **Los códigos antiguos siguen funcionando.**
- **Límite de intentos:** 5 fallos en 10 min bloquean esa IP/sesión 60 s; cada bloqueo nuevo dura el doble (máx. 30 min).
  Recargar la página no reinicia el contador. `core/usuarios.py` (`LimiteIntentos`), `ui/entrada.py`.
- Sigue pendiente para producción: Supabase Auth (enlace al correo / OTP) y RLS con `auth.uid()`.

## 4. Rendimiento (backlog #11, P1)
- El análisis se separó en **parte fija** (regex + normativa BM25 + OCDS; se calcula **una vez por PDF**) y
  **parte variable** (perfil y tus números). Escribir un costo ya no vuelve a leer todo el PDF.
  `core/preguntas.py` (`analisis_fijo`, `completar_analisis`; `analizar` sigue igual para compatibilidad).
- La imagen de la página con la cita resaltada se guarda y no se vuelve a dibujar en cada clic.
- Se guardan en memoria solo los **últimos 4 PDFs** de la sesión (antes, sin límite).

## 5. Fecha y hora de Lima (backlog #10, P1)
- Nuevo `core/fechas.py` (`hoy_lima()`, UTC−5 fijo: el Perú no tiene horario de verano y así no hace falta `tzdata`
  en Windows). Se usa en los «días que faltan», la fecha del encabezado, el borrador y el año de Oportunidades.
- El borrador de observación ya no dice siempre «Lima,»: usa la **región** del perfil.

## 6. Errores de Supabase con mensaje amable (backlog #13, P1)
- `guardar_perfil` y `guardar_analisis` ya no muestran un error técnico si la base falla: avisan en español y el
  resultado sigue en pantalla.

## Pendiente (no tocado)
Rotar claves (#1, lo hace la responsable), decidir el 3.er proveedor de IA (#2), ensayo de demo con bases reales
del SEACE (#5), corpus etiquetado y patrones (#8, #9), fijar dependencias + CI (#12), aviso de privacidad (#14) y los P2.
