"""Pruebas de las mejoras P0/P1: RNP, IA resiliente, códigos de acceso, fecha de Lima y caché del análisis."""
from datetime import timedelta

import pytest

from core import ia
from core.borrador import crear_borrador
from core.fechas import hoy_lima
from core.ia import RouterIA
from core.pdf_parser import extraer_paginas
from core.preguntas import analisis_fijo, analizar, completar_analisis, evaluar_puedo
from core.seguimiento import dias_hasta, perfil_efectivo, rnp_segun_documentos
from core.usuarios import ALFABETO, LimiteIntentos, generar_codigo
from tests.bases_ejemplo import crear_pdf

RNP = [{"categoria": "rnp", "valor": None, "pagina": 3, "cita": "Inscripción vigente en el RNP"}]
SIN_HALLAZGOS = {"hallazgos": []}


# --- RNP ---------------------------------------------------------------------------------
def _rnp(perfil):
    return next(i for i in evaluar_puedo(RNP, perfil, SIN_HALLAZGOS)["items"] if i["requisito"] == "RNP vigente")


def test_rnp_no_registrado_ya_no_sale_como_cumplido():
    assert _rnp({"experiencia_soles": 1})["estado"] == "verificar"


def test_rnp_registrado():
    assert _rnp({"rnp_vigente": True})["estado"] == "cumple"
    assert _rnp({"rnp_vigente": False})["estado"] == "no_cumple"


def test_rnp_desde_documentos():
    hoy = hoy_lima()
    vigente = {"tipo": "Constancia RNP", "vence_el": (hoy + timedelta(days=30)).isoformat()}
    vencida = {"tipo": "Constancia RNP", "vence_el": (hoy - timedelta(days=1)).isoformat()}
    assert rnp_segun_documentos([]) is None
    assert rnp_segun_documentos([vigente]) is True
    assert rnp_segun_documentos([vencida]) is False
    assert rnp_segun_documentos([vencida, vigente]) is True
    # el documento manda sobre lo marcado en el perfil
    assert perfil_efectivo({"rnp_vigente": True}, [vencida])["rnp_vigente"] is False
    assert perfil_efectivo({"rnp_vigente": True}, [])["rnp_vigente"] is True
    assert perfil_efectivo(None, [vigente]) is None


# --- Análisis en dos partes (caché) ------------------------------------------------------
def test_analisis_por_partes_igual_al_completo():
    paginas = extraer_paginas(crear_pdf())
    perfil = {"experiencia_soles": 320000, "certificaciones": []}
    costos = {"tela": 410000, "mano": 210000, "otros": 45000}
    fijo = analisis_fijo(paginas)
    assert completar_analisis(fijo, perfil, 800000, costos) == analizar(paginas, perfil, oferta=800000, costos=costos)
    # cambiar números no toca la parte fija
    otro = completar_analisis(fijo, perfil, 700000, costos)
    assert otro["justa"] is fijo["justa"] and otro["conviene"] != completar_analisis(fijo, perfil, 800000, costos)["conviene"]


# --- Fechas de Lima ----------------------------------------------------------------------
def test_dias_hasta_usa_fecha_de_lima():
    assert dias_hasta(hoy_lima().isoformat()) == 0
    assert dias_hasta((hoy_lima() + timedelta(days=3)).isoformat()) == 3


def test_borrador_usa_region_y_fecha_de_lima():
    res = {"datos": {"entidad": "X", "objeto": "Y"}}
    texto = crear_borrador(res, [], "Mi SAC", ciudad="arequipa")
    assert texto.startswith(f"Arequipa, {hoy_lima():%d/%m/%Y}")
    assert crear_borrador(res, [], "Mi SAC").startswith("Lima, ")


# --- Códigos de acceso -------------------------------------------------------------------
def test_codigo_largo_y_sin_caracteres_confusos():
    sufijo = generar_codigo("Rosa Quispe", lambda c: False).split("-")[-1]
    assert len(sufijo) == 6 and set(sufijo) <= set(ALFABETO)
    assert not set("01lio") & set(ALFABETO)


def test_limite_de_intentos():
    reloj = [1000.0]
    lim = LimiteIntentos(max_fallas=3, bloqueo_s=60, reloj=lambda: reloj[0])
    for _ in range(2):
        lim.fallo("ip:1")
    assert lim.espera("ip:1") == 0
    lim.fallo("ip:1")
    assert lim.espera("ip:1") == 60
    assert lim.espera("ip:2", "sesion:x") == 0          # otra persona no se ve afectada
    reloj[0] += 61
    assert lim.espera("ip:1") == 0
    for _ in range(3):                                   # segundo bloqueo: dura el doble
        lim.fallo("ip:1")
    assert lim.espera("ip:1") == 120
    lim.acierto("ip:1")


# --- IA: reintentos, timeouts, pausa y caché ---------------------------------------------
class ErrorAPI(Exception):
    def __init__(self, status, retry_after=None):
        super().__init__(f"Error code: {status}")
        self.status_code = status
        self.response = type("R", (), {"headers": {"retry-after": retry_after} if retry_after else {}})()


class ClienteFalso:
    """Imita openai.OpenAI: responde según una lista de respuestas/errores."""

    def __init__(self, guion):
        self.guion, self.llamadas = list(guion), []
        self.chat = type("C", (), {"completions": self})()

    def create(self, **kw):
        self.llamadas.append(kw)
        paso = self.guion.pop(0) if self.guion else "ok"
        if isinstance(paso, Exception):
            raise paso
        msg = type("M", (), {"content": paso})()
        return type("R", (), {"choices": [type("Ch", (), {"message": msg})()], "usage": None})()


@pytest.fixture(autouse=True)
def salud_limpia():
    ia.reactivar_todos()
    yield
    ia.reactivar_todos()


def _router(guiones):
    provs = [{"nombre": n, "clave": "x", "base_url": "", "modelo": "m"} for n in guiones]
    esperas = []
    r = RouterIA(provs, dormir=esperas.append)
    for n, g in guiones.items():
        r._clientes[n] = ClienteFalso(g)
    return r, esperas


def test_reintenta_503_y_responde_el_mismo_proveedor():
    r, esperas = _router({"Groq": [ErrorAPI(503), "hola"], "Gemini": []})
    out = r.completar("p")
    assert out["proveedor"] == "Groq" and out["texto"] == "hola"
    assert len(esperas) == 1 and 0 < esperas[0] <= ia.ESPERA_MAX_S


def test_respeta_retry_after_corto_y_salta_si_es_largo():
    r, esperas = _router({"Groq": [ErrorAPI(429, "2"), "ok groq"]})
    assert r.completar("p")["proveedor"] == "Groq" and esperas == [2.0]
    r, esperas = _router({"Groq": [ErrorAPI(429, "120")], "Gemini": ["ok gemini"]})
    assert r.completar("p")["proveedor"] == "Gemini" and esperas == []
    assert ia.en_pausa("Groq") > 60   # el proveedor pidió 2 min: se respeta


def test_no_reintenta_clave_invalida_y_la_pausa():
    r, esperas = _router({"Groq": [ErrorAPI(401)], "Gemini": ["ok"]})
    out = r.completar("p")
    assert out["proveedor"] == "Gemini" and esperas == [] and len(r._clientes["Groq"].llamadas) == 1
    assert ia.en_pausa("Groq") > 0
    out2 = r.completar("otra pregunta")
    assert out2["intentos"][0]["estado"] == "saltado" and len(r._clientes["Groq"].llamadas) == 1


def test_pausa_tras_fallas_seguidas_y_se_recupera():
    r, _ = _router({"Groq": [ErrorAPI(500)] * 9, "Gemini": ["a", "b", "c", "d"]})
    for i in range(ia.FALLAS_PARA_PAUSA):
        assert r.completar(f"p{i}")["proveedor"] == "Gemini"
    assert ia.en_pausa("Groq") > 0
    ia.reactivar_todos()
    assert ia.en_pausa("Groq") == 0


def test_timeout_corto_para_groq_y_largo_para_el_ultimo():
    r, _ = _router({"Groq": [ErrorAPI(401)], "Gemini": ["ok"]})
    r.completar("p")
    assert r._clientes["Groq"].llamadas[0]["timeout"] == ia.TIMEOUTS_IA["Groq"]
    assert r._clientes["Gemini"].llamadas[0]["timeout"] == ia.TIMEOUT_ULTIMO


def test_todos_en_pausa_se_prueba_igual():
    r, _ = _router({"Groq": [ErrorAPI(401), "volvió"]})
    assert r.completar("p")["texto"] is None
    assert r.completar("q")["texto"] == "volvió"


def test_cache_no_gasta_cuota_y_caida_simulada_no_pausa():
    r, _ = _router({"Groq": ["uno"], "Gemini": ["dos"]})
    assert r.completar("p")["texto"] == "uno"
    out = r.completar("p")
    assert out["desde_cache"] and len(r._clientes["Groq"].llamadas) == 1
    r.simular_caida = {"Groq"}
    assert r.completar("p")["proveedor"] == "Gemini"
    assert ia.en_pausa("Groq") == 0


def test_cloudflare_necesita_cuenta_y_token(monkeypatch):
    from core.config import avisos_configuracion, proveedores_ia
    for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "HF_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "ORDEN_IA"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "tok")
    # se comparan solo los NOMBRES: así, si la prueba falla, pytest nunca muestra una clave en pantalla
    assert [p["nombre"] for p in proveedores_ia()] == [] and "CLOUDFLARE_ACCOUNT_ID" in avisos_configuracion()[0]
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_x")
    provs = proveedores_ia()
    assert [p["nombre"] for p in provs] == ["Groq", "Cloudflare"]
    assert provs[1]["base_url"] == "https://api.cloudflare.com/client/v4/accounts/abc123/ai/v1"
    assert provs[1]["modelo"] == "@cf/openai/gpt-oss-120b" and not avisos_configuracion()


def test_constancia_rnp_sin_fecha_no_se_da_por_vigente():
    sin_fecha = {"tipo": "Constancia RNP", "vence_el": None}
    assert rnp_segun_documentos([sin_fecha]) is None
    assert perfil_efectivo({"rnp_vigente": None}, [sin_fecha])["rnp_vigente"] is None
