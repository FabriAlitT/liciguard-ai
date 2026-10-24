"""Configuración común de las pruebas.

Las pruebas NUNCA deben leer tu .streamlit/secrets.toml real: si lo hicieran, usarían tus claves (Supabase, IA)
y, si una prueba fallara, pytest podría imprimirlas en pantalla. Aquí se reemplaza la lectura de secretos para
que solo mire variables de entorno, y se borran las variables de claves que tengas en tu computadora.
"""
import os
from pathlib import Path

import pytest

# Streamlit copia las claves de secrets.toml a las variables de entorno cuando lo lee. Para que eso nunca pase en
# las pruebas, se le indica un archivo de secretos que no existe (las pruebas ponen sus propios valores falsos).
from streamlit import config as _config

_config.set_option("secrets.files", [str(Path(__file__).resolve().parent / "_sin_secretos_" / "secrets.toml")])

CLAVES = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "HF_TOKEN",
          "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "ORDEN_IA", "GROQ_MODEL", "GEMINI_MODEL",
          "CLOUDFLARE_MODEL", "HF_MODEL")


def _solo_entorno(nombre, por_defecto=None):
    return os.environ.get(nombre) or por_defecto


@pytest.fixture(autouse=True)
def sin_secretos_reales(monkeypatch):
    import streamlit as st
    try:
        st.secrets._secrets = None          # olvida lo que se haya leído antes
    except Exception:
        pass
    for k in CLAVES:
        monkeypatch.delenv(k, raising=False)
    import core.config
    monkeypatch.setattr(core.config, "secreto", _solo_entorno)
    import core.db
    monkeypatch.setattr(core.db, "secreto", _solo_entorno)
