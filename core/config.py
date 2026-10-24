"""Configuración central: secretos, modelos de IA y umbrales de alerta.

Los umbrales son criterios de ALERTA del sistema para pedir una revisión, no límites legales.
Ajústalos con tu asesor y explícalos así en el pitch.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
ARCHIVO_NORMATIVA = DATA / "normativa" / "articulos.json"
ARCHIVO_HISTORIAL = DATA / "ocds" / "historial.csv"


def secreto(nombre: str, por_defecto: str | None = None) -> str | None:
    try:
        import streamlit as st
        if nombre in st.secrets:
            valor = st.secrets[nombre]
            return str(valor) if valor not in (None, "") else por_defecto
    except Exception:
        pass
    return os.environ.get(nombre) or por_defecto


# --- Proveedores de IA (todos con API compatible con OpenAI) -----------------------------
# Los nombres de modelo cambian con el tiempo: confírmalos en la consola de cada proveedor y escríbelos en
# .streamlit/secrets.toml. Si un modelo ya no existe (error 404), la app busca otro disponible (core/ia.py).
# Revisado en octubre de 2026: Gemini 2.5 Flash ya no está disponible para cuentas nuevas; Groq retiró
# Llama 3.3 70B del plan gratuito (reemplazo: openai/gpt-oss-120b); Hugging Face casi no da crédito gratis.
# Cloudflare Workers AI: 10 000 "neuronas" gratis al día y no usa tus datos para entrenar.
def proveedores_ia() -> list[dict]:
    cf_cuenta = (secreto("CLOUDFLARE_ACCOUNT_ID") or "").strip()
    candidatos = [
        {
            "nombre": "Groq",
            "clave": secreto("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "modelo": secreto("GROQ_MODEL", "openai/gpt-oss-120b"),
        },
        {
            "nombre": "Cloudflare",
            "clave": secreto("CLOUDFLARE_API_TOKEN") if cf_cuenta else None,   # necesita cuenta + token
            "base_url": f"https://api.cloudflare.com/client/v4/accounts/{cf_cuenta}/ai/v1",
            "modelo": secreto("CLOUDFLARE_MODEL", "@cf/openai/gpt-oss-120b"),
        },
        {
            "nombre": "Gemini",
            "clave": secreto("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "modelo": secreto("GEMINI_MODEL", "gemini-3.8-flash"),
        },
        {
            "nombre": "Hugging Face",
            "clave": secreto("HF_TOKEN"),
            "base_url": "https://router.huggingface.co/v1",
            "modelo": secreto("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
        },
    ]
    orden = [x.strip().lower() for x in (secreto("ORDEN_IA", "groq,cloudflare,gemini,hugging face") or "").split(",")]
    activos = [p for p in candidatos if p["clave"]]
    return sorted(activos, key=lambda p: orden.index(p["nombre"].lower()) if p["nombre"].lower() in orden else 99)


def avisos_configuracion() -> list[str]:
    """Errores frecuentes al llenar secrets.toml que conviene mostrar en la barra lateral."""
    avisos = []
    if secreto("CLOUDFLARE_API_TOKEN") and not secreto("CLOUDFLARE_ACCOUNT_ID"):
        avisos.append("Cloudflare: falta CLOUDFLARE_ACCOUNT_ID (está el token, pero sin la cuenta no se puede usar).")
    if secreto("CLOUDFLARE_ACCOUNT_ID") and not secreto("CLOUDFLARE_API_TOKEN"):
        avisos.append("Cloudflare: falta CLOUDFLARE_API_TOKEN.")
    return avisos


# --- Resiliencia de la IA ----------------------------------------------------------------
# Tiempo máximo de espera por proveedor (segundos). Groq responde en < 2 s: si tarda más, mejor pasar
# al siguiente. El ÚLTIMO proveedor disponible siempre recibe TIMEOUT_ULTIMO (ya no hay a quién pasar).
TIMEOUTS_IA = {"Groq": 15, "Cloudflare": 25, "Gemini": 25, "Hugging Face": 30}
TIMEOUT_ULTIMO = 45
REINTENTOS_IA = 2           # reintentos extra SOLO para 429 / 5xx (saturación temporal)
ESPERA_BASE_S = 1.0         # 1.ª espera ≈ 1 s, 2.ª ≈ 2 s (con jitter aleatorio)
ESPERA_MAX_S = 6.0          # si el proveedor pide esperar más (Retry-After), pasamos al siguiente
FALLAS_PARA_PAUSA = 3       # fallas seguidas para "pausar" un proveedor (circuit breaker)
PAUSA_S = 300               # 5 min de pausa tras fallas seguidas
PAUSA_LARGA_S = 1800        # 30 min si la falla no se arregla sola (clave inválida, sin créditos)


# --- Umbrales de alerta ------------------------------------------------------------------
UMBRALES = {
    "experiencia_media": 1.0,     # experiencia exigida > 1 vez el valor estimado -> señal media
    "experiencia_fuerte": 1.5,    # > 1,5 veces -> señal fuerte
    "plazo_entrega_corto": 10,    # días o menos -> señal media
    "plazo_entrega_muy_corto": 3, # días o menos -> señal fuerte
    "muestras_horas_corto": 48,   # horas o menos para presentar muestras -> señal leve
    "margen_bueno": 10.0,         # % de margen para "Sí te conviene"
    "margen_justo": 5.0,          # % entre justo y bueno -> "Ojo"
    "ganador_repetido": 0.6,      # mismo ganador en >= 60 % de procesos parecidos -> cuidado
    "participantes_pocos": 2.0,   # promedio de participantes registrados <= 2 -> ojo (poca competencia)
}

# Supuestos para "¿Me conviene?" (el usuario puede cambiarlos en pantalla)
SUPUESTOS = {
    "garantia_pct": 10.0,         # % de la garantía de fiel cumplimiento si las bases no lo dicen
    "comision_fianza_anual": 3.0, # % anual que cobra el banco por la carta fianza (aprox.)
    "meses_contrato": 3,
    "penalidad_max_pct": 10.0,    # tope de penalidad si las bases no lo dicen
    "aplica_igv": True,           # la oferta al Estado incluye IGV (desmarcar si tu empresa está exonerada)
    "igv_pct": 18.0,
    "tasa_mensual": 2.0,          # % mensual que te cuesta el dinero (préstamo o capital propio)
    "dias_pago": 30,              # si las bases no dicen en cuántos días pagan
    "dias_entrega": 30,           # si las bases no dicen el plazo de entrega
}

CERTIFICACIONES_POCO_COMUNES = {
    "14001": "gestión ambiental",
    "45001": "seguridad y salud en el trabajo",
    "37001": "gestión antisoborno",
    "27001": "seguridad de la información",
    "50001": "gestión de la energía",
}
