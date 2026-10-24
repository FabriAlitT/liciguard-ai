"""Prueba rápida de la IA SIN abrir la app.  Ejecuta:  python probar_ia.py   (versión 4)

No muestra tus claves: solo OK o el error de cada proveedor.
"""
import time
import tomllib

from openai import OpenAI

s = tomllib.loads(open(".streamlit/secrets.toml", encoding="utf-8-sig").read())
cuenta_cf = (s.get("CLOUDFLARE_ACCOUNT_ID") or "").strip()
pruebas = [
    ("Groq", s.get("GROQ_API_KEY"), "https://api.groq.com/openai/v1", s.get("GROQ_MODEL", "openai/gpt-oss-120b")),
    ("Cloudflare", s.get("CLOUDFLARE_API_TOKEN") if cuenta_cf else None,
     f"https://api.cloudflare.com/client/v4/accounts/{cuenta_cf}/ai/v1", s.get("CLOUDFLARE_MODEL", "@cf/openai/gpt-oss-120b")),
    ("Gemini", s.get("GEMINI_API_KEY"), "https://generativelanguage.googleapis.com/v1beta/openai/",
     s.get("GEMINI_MODEL", "gemini-3.8-flash")),
    ("Hugging Face", s.get("HF_TOKEN"), "https://router.huggingface.co/v1", s.get("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")),
]
for nombre, clave, url, modelo in pruebas:
    clave = (clave or "").strip()
    if not clave:
        extra = " (falta CLOUDFLARE_ACCOUNT_ID o CLOUDFLARE_API_TOKEN)" if nombre == "Cloudflare" else ""
        print(f"-- {nombre}: sin clave, se omite{extra}")
        continue
    cliente = OpenAI(api_key=clave, base_url=url, timeout=60, max_retries=0)
    piensa = "gpt-oss" in modelo or modelo.startswith("gemini-3") or "qwen3" in modelo.lower()
    t0 = time.time()
    try:
        try:
            r = cliente.chat.completions.create(model=modelo, max_tokens=800,
                                                messages=[{"role": "user", "content": "Saluda en una frase corta."}],
                                                **({"reasoning_effort": "low"} if piensa else {}))
        except Exception as e:
            if piensa and getattr(e, "status_code", None) == 400 and "reason" in str(e).lower():
                r = cliente.chat.completions.create(model=modelo, max_tokens=800,
                                                    messages=[{"role": "user", "content": "Saluda en una frase corta."}])
            else:
                raise
        texto = (r.choices[0].message.content or "").strip()
        print(f"OK {nombre} ({modelo}) en {time.time() - t0:.1f} s: «{texto[:80]}»")
    except Exception as e:
        print(f"XX {nombre} ({modelo}) en {time.time() - t0:.1f} s: {type(e).__name__}: {str(e)[:250]}")
        if getattr(e, "status_code", None) == 404:
            try:
                ids = sorted(m.id.removeprefix("models/") for m in cliente.models.list())
                print(f"   Modelos disponibles en tu cuenta de {nombre} (copia uno a secrets.toml):")
                for i in ids[:40]:
                    print("   -", i)
            except Exception as e2:
                print("   No se pudo listar los modelos:", str(e2)[:120])
