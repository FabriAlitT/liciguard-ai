"""Pruebas de PANTALLAS con streamlit.testing (AppTest): recorren la app como lo haría una persona.

No usan internet ni Supabase (modo local en memoria) ni IA (sin claves). Ejecutar: python -m pytest -q
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.pdf_parser import extraer_paginas, huella
from tests.bases_ejemplo import crear_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PAGINAS = ["Inicio", "Ejemplos", "Revisar bases", "Oportunidades", "Seguimiento", "Mi empresa", "Privacidad"]


@pytest.fixture(autouse=True)
def sin_secretos(monkeypatch):
    """Que la prueba no use claves reales aunque existan en la computadora."""
    for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "HF_TOKEN",
              "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"):
        monkeypatch.delenv(k, raising=False)


def nueva_app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["SUPABASE_URL"] = ""   # fuerza el modo local aunque haya un secrets.toml en la carpeta
    for k in ("SUPABASE_SERVICE_ROLE_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "HF_TOKEN", "CLOUDFLARE_API_TOKEN",
              "CLOUDFLARE_ACCOUNT_ID"):
        at.secrets[k] = ""
    return at.run()


def boton(at, texto):
    return next(b for b in at.button if b.label == texto)


def sin_errores(at):
    assert not at.exception, [e.value for e in at.exception]


# Datos del invitado (viven en un repositorio en memoria dentro de su sesión, separados por empresa)
def _inv(at):
    return at.session_state["repo_invitado"], at.session_state["empresa_id"]


def perfil_inv(at):
    r, eid = _inv(at)
    return r.obtener_empresa("invitado", eid)


def docs_inv(at):
    r, eid = _inv(at)
    return r.listar_documentos("invitado", eid)


def analisis_inv(at):
    r, eid = _inv(at)
    return r.listar_analisis("invitado", eid)


def invitado_con_empresa(perfil=None):
    at = nueva_app()
    at.button(key="demo_portada").click().run()
    r = at.session_state["repo_invitado"]
    at.session_state["empresa_id"] = r.crear_empresa("invitado", perfil or {"razon_social": "Mi empresa"})["id"]
    return at.run()


def test_portada_se_muestra():
    at = nueva_app()
    sin_errores(at)
    assert any("Accede en segundos" in m.value for m in at.markdown)


def test_crear_codigo_pide_aceptar_privacidad():
    at = nueva_app()
    at.text_input(key="in_nombre").input("Rosa Quispe")
    boton(at, "Crear mi código").click().run()
    assert at.session_state["usuario"] is None
    assert any("aviso de privacidad" in w.value for w in at.warning)
    at.checkbox(key="in_acepto").check()
    boton(at, "Crear mi código").click().run()
    sin_errores(at)
    u = at.session_state["usuario"]
    assert u["codigo"].startswith("rosa-quispe-") and u["acepto_privacidad_en"]


def test_codigo_equivocado_y_limite_de_intentos():
    at = nueva_app()
    for _ in range(5):
        at.text_input(key="in_codigo").input("nadie-existe-zzzzzz")
        boton(at, "Entrar").click().run()
    at.text_input(key="in_codigo").input("nadie-existe-zzzzzz")
    boton(at, "Entrar").click().run()
    assert any("Demasiados intentos" in e.value for e in at.error)


def test_invitado_recorre_todas_las_paginas():
    at = invitado_con_empresa({"razon_social": "Muebles Huancayo SAC", "rubro": "Mobiliario",
                               "experiencia_soles": 600000})
    for pagina in PAGINAS:
        at.session_state["pagina"] = pagina
        at.run()
        sin_errores(at)


def _con_bases(at, perfil=None):
    data = crear_pdf()
    sha = huella(data)
    at.session_state["invitado"] = True
    r = at.session_state["repo_invitado"]
    at.session_state["empresa_id"] = r.crear_empresa("invitado", perfil or {"razon_social": "Mi empresa"})["id"]
    at.session_state["pdfs"] = {sha: {"data": data, "paginas": extraer_paginas(data), "nombre": "bases.pdf"}}
    at.session_state["sha_actual"] = sha
    at.session_state["pagina"] = "Revisar bases"
    return at.run(), sha


def test_ficha_completa_con_las_cuatro_preguntas():
    perfil = {"razon_social": "Confecciones Andinas SAC", "rubro": "Uniformes y textiles", "experiencia_soles": 320000,
              "produccion_mensual": 3000, "maquinas": 6, "personal": 8, "es_mype": True, "rnp_vigente": True,
              "region": "Cusco"}
    at, sha = _con_bases(nueva_app(), perfil)
    sin_errores(at)
    for i in range(4):   # ¿Es justa? · ¿Puedo? · ¿Me conviene? · ¿Puedo ganar?
        radio = at.radio(key=f"det_{sha}")
        radio.set_value(radio.options[i]).run()
        sin_errores(at)
    # ¿Me conviene?: con costos se calcula ganancia con IGV y financiamiento
    at.radio(key=f"det_{sha}").set_value(at.radio(key=f"det_{sha}").options[2]).run()
    at.number_input(key=f"ma_{sha}").set_value(330000).run()
    at.number_input(key=f"mo_{sha}").set_value(170000).run()
    sin_errores(at)
    assert any("IGV" in c.value for c in at.caption)


def test_explicame_simple_sin_ia_usa_reglas():
    at, sha = _con_bases(nueva_app(), {"experiencia_soles": 100000})
    at.button(key=f"simple_{sha}").click().run()
    sin_errores(at)
    assert at.session_state[f"exp_{sha}"][1] == "reglas (sin IA)"


def test_borrar_cuenta_con_confirmacion():
    at = nueva_app()
    at.text_input(key="in_nombre").input("Rosa Quispe")
    at.checkbox(key="in_acepto").check()
    boton(at, "Crear mi código").click().run()
    codigo = at.session_state["usuario"]["codigo"]
    at.text_input(key="nueva_razon").input("Textiles Rosa SAC")
    at.button(key="tono_azul_crear_empresa").click().run()          # primera empresa: va a Mi empresa
    assert at.session_state["pagina"] == "Mi empresa"
    sin_errores(at)
    at.text_input(key="borrar_confirma").input("otro-codigo")
    at.button(key="borrar_cuenta").click().run()
    assert at.session_state["usuario"] is not None          # código equivocado: no borra
    at.text_input(key="borrar_confirma").input(codigo)
    at.button(key="borrar_cuenta").click().run()
    sin_errores(at)
    assert at.session_state["usuario"] is None
    assert any("borramos tu cuenta" in s.value for s in at.success)


def test_google_codigo_interno_y_boton():
    import re
    from ui.google import codigo_de
    c = codigo_de("  Jurado.NY@Gmail.com ")
    assert c == codigo_de("jurado.ny@gmail.com") and re.fullmatch(r"g-[0-9a-f]{16}", c)
    at = nueva_app()
    assert not any(b.label == "Entrar con Google" for b in at.button)        # sin configurar: no aparece
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["auth"] = {"redirect_uri": "http://localhost:8501/oauth2callback", "cookie_secret": "x" * 32,
                          "google": {"client_id": "id", "client_secret": "s",
                                     "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration"}}
    at.run()
    sin_errores(at)
    assert any(b.label == "Entrar con Google" for b in at.button)


def test_primera_vez_con_google_pide_aceptar_y_luego_entra_directo(monkeypatch):
    import ui.google as g
    monkeypatch.setattr(g, "conectado", lambda: True)          # simula que Google ya devolvió a la persona
    monkeypatch.setattr(g, "correo", lambda: "jurado@gmail.com")
    monkeypatch.setattr(g, "nombre", lambda: "Jurado Demo")
    at = nueva_app()
    sin_errores(at)
    assert at.session_state["usuario"] is None
    assert any("Hola, Jurado Demo" in m.value for m in at.markdown)
    at.checkbox(key="g_acepto").check().run()
    boton(at, "Continuar").click().run()
    sin_errores(at)
    u = at.session_state["usuario"]
    assert u["codigo"] == g.codigo_de("jurado@gmail.com") and u["acepto_privacidad_en"]
    otra = nueva_app()                                          # vuelve otro día: entra directo, sin preguntar
    sin_errores(otra)
    assert otra.session_state["usuario"]["codigo"] == u["codigo"] and otra.session_state["via_google"]


def test_demo_elige_empresa_en_cartas_y_todo_es_de_su_rubro():
    at = nueva_app()
    at.button(key="demo_portada").click().run()
    sin_errores(at)
    assert at.session_state["invitado"] and at.session_state["empresa_id"] is None
    assert any("Elige una empresa para" in m.value for m in at.markdown)          # cartas de empresas
    at.button(key="tono_ambar_demo_muebles").click().run()
    sin_errores(at)
    assert at.session_state["pagina"] == "Revisar bases" and at.session_state["tour_paso"] == 0
    assert perfil_inv(at)["razon_social"] == "Muebles Huancayo SAC" and len(docs_inv(at)) == 2
    assert at.session_state["ejemplo_activo"]["titulo"] == "Mobiliario escolar"
    assert analisis_inv(at)[0]["recomendacion"] == "no_postular"
    at.session_state["pagina"] = "Ejemplos"
    at.run()
    claves = [b.key for b in at.button if (b.key or "").startswith("tono_") and "_base_" in b.key]
    assert claves and all("mobiliario" in k for k in claves)                     # solo bases de su rubro


def test_cambiar_de_empresa_separa_los_datos():
    at = nueva_app()
    at.button(key="demo_portada").click().run()
    at.button(key="tono_violeta_demo_andinas").click().run()
    andinas = at.session_state["empresa_id"]
    assert analisis_inv(at)[0]["recomendacion"] == "observar"
    at.button(key="cambiar_empresa").click().run()
    sin_errores(at)
    assert at.session_state["empresa_id"] is None
    assert any(b.key == f"tono_violeta_entrar_{andinas}" for b in at.button)       # «Tus empresas»
    at.button(key="tono_cian_demo_limpieza").click().run()
    sin_errores(at)
    assert perfil_inv(at)["rubro"] == "Limpieza"
    assert [a["nombre_archivo"] for a in analisis_inv(at)] == ["5_limpieza_observar.pdf"]   # nada de uniformes
    at.button(key="cambiar_empresa").click().run()
    at.button(key=f"tono_violeta_entrar_{andinas}").click().run()
    assert [a["nombre_archivo"] for a in analisis_inv(at)] == ["1_uniformes_observar.pdf"]


def test_crear_mi_propia_empresa_desde_las_cartas():
    at = nueva_app()
    at.button(key="demo_portada").click().run()
    at.text_input(key="nueva_razon").input("Textiles del Norte SAC")
    at.selectbox(key="nueva_rubro").set_value("Uniformes y textiles").run()
    at.button(key="tono_azul_crear_empresa").click().run()
    sin_errores(at)
    assert at.session_state["pagina"] == "Mi empresa"
    assert perfil_inv(at)["razon_social"] == "Textiles del Norte SAC"


def test_si_supabase_niega_permisos_la_portada_avisa_y_no_se_cae(monkeypatch):
    from core.db import RepoMemoria

    def negar(*a, **k):
        raise RuntimeError("{'message': 'permission denied for table usuarios', 'code': '42501'}")
    monkeypatch.setattr(RepoMemoria, "buscar_usuario", negar)
    monkeypatch.setattr(RepoMemoria, "existe_codigo", negar)
    at = nueva_app()
    at.text_input(key="in_codigo").input("rosa-quispe-abc123")
    boton(at, "Entrar").click().run()
    sin_errores(at)
    assert any("05_permisos.sql" in e.value for e in at.error)
    at.text_input(key="in_nombre").input("Rosa Quispe")
    at.checkbox(key="in_acepto").check()
    boton(at, "Crear mi código").click().run()
    sin_errores(at)
    assert at.session_state["usuario"] is None


def test_entrar_con_codigo_vacio_no_rompe():
    at = nueva_app()
    boton(at, "Entrar").click().run()
    sin_errores(at)
    assert any("No encontramos" in e.value for e in at.error)


def test_recorrido_guiado_de_la_demo():
    at = nueva_app()
    at.button(key="demo_portada").click().run()
    at.button(key="tono_violeta_demo_andinas").click().run()
    sin_errores(at)
    assert at.session_state["tour_paso"] == 0
    assert any("RECORRIDO GUIADO · 1 DE 5" in m.value for m in at.markdown)
    for _ in range(4):
        at.button(key="tono_violeta_tour_sig").click().run()
        sin_errores(at)
    assert any("5 DE 5" in m.value for m in at.markdown)
    at.button(key="tono_verde_tour_fin").click().run()
    sin_errores(at)
    assert at.session_state["tour_paso"] is None and at.session_state["tour_visto"]


def test_guia_de_pagina_se_cierra_y_siguiente_paso():
    at = invitado_con_empresa()
    assert any("Tu panel" in m.value for m in at.markdown)
    assert any("SIGUIENTE PASO" in m.value for m in at.markdown)
    at.button(key="guia_x_inicio").click().run()
    sin_errores(at)
    assert not any("Tu panel" in m.value for m in at.markdown)
    at.button(key="guias_de_nuevo").click().run()
    assert any("Tu panel" in m.value for m in at.markdown)
    at.button(key="tono_verde_sig_Revisar_bases").click().run()   # sin revisiones: sugiere revisar bases
    assert at.session_state["pagina"] == "Revisar bases"


def test_glosario_subraya_terminos():
    from ui.tema import con_glosario
    t = con_glosario("Inscripción en el RNP <vigente>")
    assert 'class="lg-term"' in t and "&lt;vigente&gt;" in t


def test_asistente_flotante_responde_sin_ia_y_se_niega_fuera_de_tema():
    at = invitado_con_empresa({"razon_social": "Muebles Huancayo SAC", "rubro": "Mobiliario"})
    at.button(key="asistente_toggle").click().run()
    sin_errores(at)
    at.text_input(key="chat_in").input("¿Qué es el RNP?")
    at.button(key="FormSubmitter:asistente_form-Enviar").click().run()
    sin_errores(at)
    chat = at.session_state["chats"][at.session_state["empresa_id"]]
    assert "Registro Nacional" in chat[-1]["texto"]
    at.text_input(key="chat_in").input("Dame una receta de ceviche")
    at.button(key="FormSubmitter:asistente_form-Enviar").click().run()
    assert "Solo puedo ayudarte" in at.session_state["chats"][at.session_state["empresa_id"]][-1]["texto"]
