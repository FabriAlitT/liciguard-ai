"""Recursos compartidos y datos de la persona (con código, con Google o invitada).

Todo se guarda por EMPRESA: la persona elige su «empresa activa» y la app solo muestra lo de esa empresa
(sus revisiones, seguimiento, documentos, su rubro). Los invitados guardan en memoria de su sesión.
"""
import streamlit as st

from core import mercado
from core.buscador import Normativa
from core.db import FaltaMigracion, RepoMemoria, crear_repo
from core.historial_ocds import cargar_historial
from core.ia import RouterIA

ss = st.session_state
INVITADO = "invitado"


@st.cache_resource
def repo():
    return crear_repo()


@st.cache_resource
def normativa():
    return Normativa.cargar()


@st.cache_resource
def historial():
    return cargar_historial()


@st.cache_resource
def mercado_df():
    return mercado.preparar(historial())


def iniciar():
    for k, v in {"usuario": None, "invitado": False, "pdfs": {}, "sha_actual": None, "abierto": None,
                 "pagina": "Inicio", "entradas": {}, "empresa_id": None, "descartadas": set(),
                 "aviso_tablas": False, "aviso_lectura": None}.items():
        ss.setdefault(k, v)
    if "repo_invitado" not in ss:
        ss.repo_invitado = RepoMemoria()       # lo del invitado vive solo en su sesión
    if "router" not in ss:
        ss.router = RouterIA(registrar=lambda **kw: repo().registrar_llamada(**kw))


def ir_a(pagina, **extra):
    ss.pagina = pagina
    if "sha_actual" in extra:  # abrir otra ficha: se limpia el cargador de PDF
        ss.n_subida = ss.get("n_subida", 0) + 1
    for k, v in extra.items():
        ss[k] = v


def _r():
    """Repositorio de la persona: Supabase/memoria del servidor si tiene cuenta, memoria de la sesión si es invitada."""
    return repo() if ss.usuario else ss.repo_invitado


def _uid():
    return ss.usuario["id"] if ss.usuario else INVITADO


def _eid():
    return ss.get("empresa_id")


def _seguro(funcion, por_defecto):
    """Si faltan las tablas nuevas en Supabase, no rompe la app: avisa una vez."""
    try:
        return funcion()
    except Exception:
        ss.aviso_tablas = True
        return por_defecto


def _leer(funcion, por_defecto):
    """Si Supabase no responde al LEER, la app sigue (con datos vacíos) y muestra un aviso arriba."""
    try:
        return funcion()
    except Exception as e:
        ss.aviso_lectura = f"{type(e).__name__}: {str(e)[:160]}"
        return por_defecto


def error_base_de_datos(e):
    """Mensaje claro cuando Supabase no deja entrar (en vez de que la app se caiga)."""
    texto = str(e)
    if "permission denied" in texto or "42501" in texto:
        st.error("La base de datos no le da permisos a LiciGuard. Ejecuta `supabase/05_permisos.sql` en el "
                 "SQL Editor de Supabase y vuelve a intentarlo.", icon=":material/lock:")
    elif "does not exist" in texto or "42P01" in texto or "PGRST205" in texto:
        st.error("Faltan tablas en Supabase. Ejecuta en orden los archivos de la carpeta `supabase/` (01 a 06).",
                 icon=":material/table:")
    else:
        st.error("No pudimos conectar con la base de datos (revisa tu internet o Supabase). Mientras tanto puedes "
                 "entrar como invitado.", icon=":material/cloud_off:")
    st.caption(f"Detalle técnico: {type(e).__name__}: {texto[:160]}")


def _aviso_guardado(e):
    if isinstance(e, FaltaMigracion):
        st.warning(str(e), icon=":material/table:")
        return
    st.warning("No pudimos guardar en la base de datos en este momento (revisa tu internet o Supabase). "
               "Tus resultados siguen en pantalla; vuelve a intentarlo en un rato.", icon=":material/cloud_off:")
    st.caption(f"Detalle técnico: {type(e).__name__}: {str(e)[:200]}")


# Empresas ----------------------------------------------------------------------------------
def empresas() -> list[dict]:
    return _leer(lambda: _r().listar_empresas(_uid()), [])


def empresa_activa() -> dict | None:
    if not _eid():
        return None
    return _leer(lambda: _r().obtener_empresa(_uid(), _eid()), None)


def elegir_empresa(empresa_id):
    """Cambia la empresa activa: se cierra la ficha abierta para no mezclar lo de una empresa con otra."""
    ss.empresa_id = empresa_id
    ss.sha_actual, ss.abierto, ss.tour_paso = None, None, None
    ss.n_subida = ss.get("n_subida", 0) + 1
    ss.pop("ejemplo_activo", None)


def entrar_como(usuario, invitado=False):
    """Al entrar (código, Google o invitado) se empieza sin empresa elegida: si tiene una sola, entra directo."""
    ss.usuario, ss.invitado, ss.pagina = usuario, invitado, "Inicio"
    ss.empresa_id, ss.elegir_empresa, ss.sha_actual, ss.abierto = None, False, None, None


def cambiar_de_empresa():
    elegir_empresa(None)
    ss.pagina = "Inicio"


def crear_empresa(datos) -> str | None:
    try:
        e = _r().crear_empresa(_uid(), datos)
    except Exception as ex:
        _aviso_guardado(ex)
        ss.aviso_empresa = str(ex)
        return None
    return e["id"]


def borrar_empresa(empresa_id):
    _r().borrar_empresa(_uid(), empresa_id)
    if _eid() == empresa_id:
        cambiar_de_empresa()


def varias_empresas() -> bool:
    try:
        return bool(_r().varias_empresas)
    except Exception:
        return False


# Perfil (= la empresa activa) --------------------------------------------------------------
def perfil():
    return empresa_activa()


def rubro() -> str | None:
    return (perfil() or {}).get("rubro")


def guardar_perfil(datos) -> bool:
    try:
        if _eid():
            _r().guardar_empresa(_uid(), _eid(), datos)
        else:
            nuevo = _r().crear_empresa(_uid(), datos)
            ss.empresa_id = nuevo["id"]
        return True
    except Exception as e:
        _aviso_guardado(e)
        return False


# Análisis ----------------------------------------------------------------------------------
def analisis():
    if not _eid():
        return []
    return _leer(lambda: _r().listar_analisis(_uid(), _eid()), [])


def guardar_analisis(fila) -> bool:
    if not _eid():
        return False
    try:
        _r().guardar_analisis(_uid(), _eid(), fila)
    except Exception as e:
        _aviso_guardado(e)
        return False
    return True


# Seguimiento -------------------------------------------------------------------------------
def seguimientos() -> list[dict]:
    if not _eid():
        return []
    return _seguro(lambda: _r().listar_seguimiento(_uid(), _eid()), [])


def seguimiento_de(sha):
    return next((s for s in seguimientos() if s["sha256"] == sha), None)


def guardar_seguimiento(seg):
    if _eid():
        _seguro(lambda: _r().guardar_seguimiento(_uid(), _eid(), seg), None)


# Documentos --------------------------------------------------------------------------------
def documentos():
    if not _eid():
        return []
    return _seguro(lambda: _r().listar_documentos(_uid(), _eid()), [])


def agregar_documento(nombre, tipo, vence):
    if _eid():
        _seguro(lambda: _r().agregar_documento(_uid(), _eid(), nombre, tipo, vence), None)


def borrar_documento(doc_id):
    _seguro(lambda: _r().borrar_documento(_uid(), doc_id), None)


# Privacidad --------------------------------------------------------------------------------
def exportar_mis_datos() -> dict:
    """Todo lo que LiciGuard guarda de la persona (derecho de acceso, Ley 29733)."""
    datos = _r().exportar_datos(_uid())
    if not ss.usuario:
        datos["usuario"] = "invitado (nada se guarda al cerrar la pestaña)"
    return datos


def borrar_mi_cuenta():
    """Borra la cuenta y todos sus datos (derecho de cancelación). Cierra la sesión."""
    if ss.usuario:
        repo().borrar_usuario(_uid())
    ss.repo_invitado = RepoMemoria()
    ss.pdfs, ss.chats = {}, {}
    ss.usuario, ss.invitado, ss.abierto, ss.sha_actual, ss.empresa_id = None, False, None, None, None
