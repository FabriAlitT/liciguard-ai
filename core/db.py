"""Acceso a datos.

- Con SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .streamlit/secrets.toml -> guarda en Supabase.
- Sin ellas -> modo local en memoria (sirve para probar la app el primer día). Los invitados usan siempre memoria.

Una persona puede tener VARIAS empresas (p. ej. un consultor con varios clientes). Todo lo que se guarda
(revisiones, seguimiento, documentos) pertenece a una empresa: así nada se mezcla.
Requiere supabase/06_varias_empresas.sql; si aún no se ejecutó, la app sigue con UNA empresa por persona.

La clave service_role solo vive en el servidor de Streamlit; nunca llega al navegador.
"""
from datetime import datetime, timezone
from itertools import count

from core.config import secreto

CAMPOS_EMPRESA = ["razon_social", "rubro", "region", "es_mype", "experiencia_soles", "produccion_mensual",
                  "maquinas", "personal", "certificaciones", "rnp_vigente"]


def _ahora():
    return datetime.now(timezone.utc).isoformat()


class FaltaMigracion(Exception):
    """La base de datos aún no permite varias empresas (falta supabase/06_varias_empresas.sql)."""


class RepoMemoria:
    """Guarda todo en diccionarios. Se pierde al reiniciar la app (o al cerrar la pestaña, si es invitado)."""

    modo = "memoria"
    varias_empresas = True

    def __init__(self):
        self.usuarios: dict[str, dict] = {}
        self.empresas: dict[str, dict] = {}
        self.analisis: dict[tuple, dict] = {}
        self.llamadas: list[dict] = []
        self.seguimientos: dict[tuple, dict] = {}
        self.documentos: list[dict] = []
        self._n = count(1)

    # Usuarios
    def existe_codigo(self, codigo):
        return codigo in self.usuarios

    def crear_usuario(self, codigo, nombre, acepto_privacidad_en=None):
        u = {"id": codigo, "codigo": codigo, "nombre": nombre, "acepto_privacidad_en": acepto_privacidad_en}
        self.usuarios[codigo] = u
        return u

    def buscar_usuario(self, codigo):
        return self.usuarios.get(codigo)

    # Empresas
    def listar_empresas(self, usuario_id):
        return sorted((e for e in self.empresas.values() if e["usuario_id"] == usuario_id),
                      key=lambda e: e["creado_en"])

    def obtener_empresa(self, usuario_id, empresa_id):
        e = self.empresas.get(empresa_id)
        return e if e and e["usuario_id"] == usuario_id else None

    def crear_empresa(self, usuario_id, datos):
        eid = f"e{next(self._n)}"
        self.empresas[eid] = {k: datos.get(k) for k in CAMPOS_EMPRESA} | {
            "id": eid, "usuario_id": usuario_id, "creado_en": f"{_ahora()}#{eid:>8}"}
        return self.empresas[eid]

    def guardar_empresa(self, usuario_id, empresa_id, datos):
        e = self.obtener_empresa(usuario_id, empresa_id)
        if not e:
            raise KeyError("Esa empresa no existe")
        e.update({k: datos.get(k) for k in CAMPOS_EMPRESA})
        return e

    def borrar_empresa(self, usuario_id, empresa_id):
        if not self.obtener_empresa(usuario_id, empresa_id):
            return
        self.empresas.pop(empresa_id)
        self.analisis = {k: v for k, v in self.analisis.items() if k[1] != empresa_id}
        self.seguimientos = {k: v for k, v in self.seguimientos.items() if k[1] != empresa_id}
        self.documentos = [d for d in self.documentos if d["empresa_id"] != empresa_id]

    # Análisis
    def guardar_analisis(self, usuario_id, empresa_id, datos):
        clave = (usuario_id, empresa_id, datos["sha256"])
        fila = {**self.analisis.get(clave, {"creado_en": f"{_ahora()}#{next(self._n):>8}"}), **datos,
                "usuario_id": usuario_id, "empresa_id": empresa_id, "id": f"{empresa_id}:{datos['sha256'][:12]}"}
        self.analisis[clave] = fila
        return fila

    def listar_analisis(self, usuario_id, empresa_id):
        return sorted((a for (u, e, _), a in self.analisis.items() if u == usuario_id and e == empresa_id),
                      key=lambda a: a["creado_en"], reverse=True)

    def registrar_llamada(self, **kw):
        self.llamadas.append({**kw, "creado_en": _ahora()})

    # Seguimiento
    def listar_seguimiento(self, usuario_id, empresa_id):
        return [s for (u, e, _), s in self.seguimientos.items() if u == usuario_id and e == empresa_id]

    def guardar_seguimiento(self, usuario_id, empresa_id, datos):
        clave = (usuario_id, empresa_id, datos["sha256"])
        self.seguimientos[clave] = {**datos, "usuario_id": usuario_id, "empresa_id": empresa_id}
        return self.seguimientos[clave]

    # Documentos
    def listar_documentos(self, usuario_id, empresa_id):
        return [d for d in self.documentos if d["usuario_id"] == usuario_id and d["empresa_id"] == empresa_id]

    def agregar_documento(self, usuario_id, empresa_id, nombre, tipo, vence_el):
        d = {"id": f"d{next(self._n)}", "usuario_id": usuario_id, "empresa_id": empresa_id, "nombre": nombre,
             "tipo": tipo, "vence_el": vence_el}
        self.documentos.append(d)
        return d

    def borrar_documento(self, usuario_id, doc_id):
        self.documentos = [d for d in self.documentos if not (d["usuario_id"] == usuario_id and d["id"] == doc_id)]

    # Privacidad (Ley 29733): ver y borrar mis datos
    def exportar_datos(self, usuario_id):
        u = next((x for x in self.usuarios.values() if x["id"] == usuario_id), None)
        return {"usuario": u, "empresas": self.listar_empresas(usuario_id),
                "analisis": [a for (x, _, _), a in self.analisis.items() if x == usuario_id],
                "seguimiento": [s for (x, _, _), s in self.seguimientos.items() if x == usuario_id],
                "documentos": [d for d in self.documentos if d["usuario_id"] == usuario_id]}

    def borrar_usuario(self, usuario_id):
        self.usuarios = {k: v for k, v in self.usuarios.items() if v["id"] != usuario_id}
        self.empresas = {k: v for k, v in self.empresas.items() if v["usuario_id"] != usuario_id}
        self.analisis = {k: v for k, v in self.analisis.items() if k[0] != usuario_id}
        self.seguimientos = {k: v for k, v in self.seguimientos.items() if k[0] != usuario_id}
        self.documentos = [d for d in self.documentos if d["usuario_id"] != usuario_id]


class RepoSupabase:
    modo = "supabase"

    def __init__(self, url, key):
        from supabase import create_client
        self.sb = create_client(url, key)
        self._varias = None

    @property
    def varias_empresas(self) -> bool:
        """¿Ya se ejecutó supabase/06_varias_empresas.sql? (se revisa una vez)."""
        if self._varias is None:
            try:
                self.sb.table("analisis").select("empresa_id").limit(1).execute()
                self._varias = True
            except Exception as e:
                if "empresa_id" not in str(e):
                    raise
                self._varias = False
        return self._varias

    def _de_empresa(self, consulta, empresa_id):
        return consulta.eq("empresa_id", empresa_id) if self.varias_empresas else consulta

    def _con_empresa(self, fila, empresa_id):
        return fila | {"empresa_id": empresa_id} if self.varias_empresas else fila

    def _conflicto(self):
        return "empresa_id,sha256" if self.varias_empresas else "usuario_id,sha256"

    # Usuarios
    def existe_codigo(self, codigo):
        return bool(self.sb.table("usuarios").select("id").eq("codigo", codigo).limit(1).execute().data)

    def crear_usuario(self, codigo, nombre, acepto_privacidad_en=None):
        fila = {"codigo": codigo, "nombre": nombre, "acepto_privacidad_en": acepto_privacidad_en}
        try:
            return self.sb.table("usuarios").insert(fila).execute().data[0]
        except Exception as e:
            # Base creada antes de supabase/04_privacidad.sql: crea el usuario igual (sin la fecha) y avisa.
            if "acepto_privacidad_en" not in str(e):
                raise
            fila.pop("acepto_privacidad_en")
            self.falta_columna_privacidad = True
            return self.sb.table("usuarios").insert(fila).execute().data[0]

    def buscar_usuario(self, codigo):
        r = self.sb.table("usuarios").select("*").eq("codigo", codigo).limit(1).execute()
        return r.data[0] if r.data else None

    # Empresas
    def listar_empresas(self, usuario_id):
        q = self.sb.table("empresas").select("*").eq("usuario_id", usuario_id)
        return q.order("creado_en" if self.varias_empresas else "actualizado_en").execute().data

    def obtener_empresa(self, usuario_id, empresa_id):
        r = self.sb.table("empresas").select("*").eq("usuario_id", usuario_id).eq("id", empresa_id).limit(1).execute()
        return r.data[0] if r.data else None

    def _fila_empresa(self, usuario_id, datos):
        return {k: datos.get(k) for k in CAMPOS_EMPRESA} | {"usuario_id": usuario_id, "actualizado_en": _ahora()}

    def _escribir(self, accion):
        try:
            return accion(rnp=True)
        except Exception as e:
            # Base creada antes de supabase/03_rnp_vigente.sql: guarda el resto y avisa.
            if "rnp_vigente" not in str(e):
                raise
            self.falta_columna_rnp = True
            return accion(rnp=False)

    def crear_empresa(self, usuario_id, datos):
        if not self.varias_empresas and self.listar_empresas(usuario_id):
            raise FaltaMigracion("Para tener varias empresas ejecuta supabase/06_varias_empresas.sql en Supabase.")

        def insertar(rnp):
            fila = self._fila_empresa(usuario_id, datos)
            if not rnp:
                fila.pop("rnp_vigente", None)
            return self.sb.table("empresas").insert(fila).execute().data[0]
        try:
            return self._escribir(insertar)
        except Exception as e:
            if "duplicate" in str(e) or "23505" in str(e):
                raise FaltaMigracion("Para tener varias empresas ejecuta supabase/06_varias_empresas.sql en "
                                     "Supabase.") from e
            raise

    def guardar_empresa(self, usuario_id, empresa_id, datos):
        def actualizar(rnp):
            fila = self._fila_empresa(usuario_id, datos)
            if not rnp:
                fila.pop("rnp_vigente", None)
            return (self.sb.table("empresas").update(fila).eq("usuario_id", usuario_id).eq("id", empresa_id)
                    .execute().data[0])
        return self._escribir(actualizar)

    def borrar_empresa(self, usuario_id, empresa_id):
        # Con 06_varias_empresas.sql el borrado es en cascada (sus análisis, seguimiento y documentos).
        self.sb.table("empresas").delete().eq("usuario_id", usuario_id).eq("id", empresa_id).execute()

    # Análisis
    def guardar_analisis(self, usuario_id, empresa_id, datos):
        fila = self._con_empresa({**datos, "usuario_id": usuario_id}, empresa_id)
        return self.sb.table("analisis").upsert(fila, on_conflict=self._conflicto()).execute().data[0]

    def listar_analisis(self, usuario_id, empresa_id):
        q = self.sb.table("analisis").select("*").eq("usuario_id", usuario_id)
        return self._de_empresa(q, empresa_id).order("creado_en", desc=True).execute().data

    def registrar_llamada(self, **kw):
        try:
            self.sb.table("llm_llamadas").insert(kw).execute()
        except Exception:
            pass  # el registro nunca debe romper la app

    # Seguimiento (requiere supabase/02_seguimiento_y_documentos.sql)
    def listar_seguimiento(self, usuario_id, empresa_id):
        q = self.sb.table("seguimiento").select("*").eq("usuario_id", usuario_id)
        return self._de_empresa(q, empresa_id).execute().data

    def guardar_seguimiento(self, usuario_id, empresa_id, datos):
        fila = {k: v for k, v in datos.items() if k not in ("id", "usuario_id", "empresa_id")}
        fila = self._con_empresa(fila | {"usuario_id": usuario_id, "actualizado_en": _ahora()}, empresa_id)
        return self.sb.table("seguimiento").upsert(fila, on_conflict=self._conflicto()).execute().data[0]

    # Documentos
    def listar_documentos(self, usuario_id, empresa_id):
        q = self.sb.table("documentos").select("*").eq("usuario_id", usuario_id)
        return self._de_empresa(q, empresa_id).order("vence_el").execute().data

    def agregar_documento(self, usuario_id, empresa_id, nombre, tipo, vence_el):
        fila = self._con_empresa({"usuario_id": usuario_id, "nombre": nombre, "tipo": tipo, "vence_el": vence_el},
                                 empresa_id)
        return self.sb.table("documentos").insert(fila).execute().data[0]

    def borrar_documento(self, usuario_id, doc_id):
        self.sb.table("documentos").delete().eq("usuario_id", usuario_id).eq("id", doc_id).execute()

    # Privacidad (Ley 29733): ver y borrar mis datos
    def exportar_datos(self, usuario_id):
        def tabla(nombre):
            try:
                return self.sb.table(nombre).select("*").eq("usuario_id", usuario_id).execute().data
            except Exception:
                return []   # tabla aún no creada (scripts 02/03/04 sin ejecutar)
        u = self.sb.table("usuarios").select("*").eq("id", usuario_id).limit(1).execute().data
        return {"usuario": u[0] if u else None, "empresas": tabla("empresas"),
                "analisis": tabla("analisis"), "seguimiento": tabla("seguimiento"), "documentos": tabla("documentos")}

    def borrar_usuario(self, usuario_id):
        # "on delete cascade" borra también empresas, análisis, seguimiento y documentos.
        self.sb.table("usuarios").delete().eq("id", usuario_id).execute()


def crear_repo():
    url, key = secreto("SUPABASE_URL"), secreto("SUPABASE_SERVICE_ROLE_KEY")
    if url and key:
        return RepoSupabase(url, key)
    return RepoMemoria()
