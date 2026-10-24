"""Códigos de usuario sin contraseña (solo para la demo).

Un código tiene la forma  nombre-apellido-k7m4qx : fácil de recordar y difícil de adivinar.

Antes el sufijo era de 4 dígitos (solo 9 000 combinaciones por nombre: se podía adivinar probando).
Ahora son 6 caracteres de un alfabeto de 31 símbolos (≈ 887 millones de combinaciones por nombre) y además
hay un límite de intentos fallidos (ver `LimiteIntentos`). Los códigos antiguos siguen funcionando.
Para producción: Supabase Auth con enlace al correo u OTP (ver docs/REVISION_TECNICA.md).
"""
import re
import secrets
import threading
import time
import unicodedata

# Sin 0/o, 1/l/i: no se confunden al dictarlos o copiarlos a mano.
ALFABETO = "abcdefghjkmnpqrstuvwxyz23456789"
LARGO_SUFIJO = 6


def _sin_tildes(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normal if not unicodedata.combining(c))


def normalizar_codigo(texto: str) -> str:
    """Convierte lo que escribe la persona en un código comparable.

    'Rosa-Quispe-4821 ' -> 'rosa-quispe-4821'
    """
    t = _sin_tildes(texto or "").lower().strip()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def base_desde_nombre(nombre: str) -> str:
    """Toma hasta dos palabras del nombre: 'María Rosa Quispe' -> 'maria-rosa'."""
    palabras = normalizar_codigo(nombre).split("-")
    palabras = [p for p in palabras if p and not p.isdigit()]
    base = "-".join(palabras[:2])[:24].strip("-")
    return base or "usuario"


def generar_codigo(nombre: str, existe) -> str:
    """Genera un código único. `existe(codigo) -> bool` consulta la base de datos."""
    base = base_desde_nombre(nombre)
    for _ in range(50):
        sufijo = "".join(secrets.choice(ALFABETO) for _ in range(LARGO_SUFIJO))
        codigo = f"{base}-{sufijo}"
        if not existe(codigo):
            return codigo
    raise RuntimeError("No se pudo generar un código único; intenta con otro nombre.")


class LimiteIntentos:
    """Frena a quien prueba códigos al azar.

    Tras `max_fallas` intentos fallidos dentro de `ventana_s`, bloquea esa llave (IP o sesión) durante
    `bloqueo_s`; cada bloqueo nuevo dura el doble (hasta `bloqueo_max_s`). Un acierto limpia el contador.
    Vive en la memoria del servidor: se comparte entre sesiones, se borra al reiniciar la app.
    """

    def __init__(self, max_fallas=5, ventana_s=600, bloqueo_s=60, bloqueo_max_s=1800, reloj=time.time):
        self.max_fallas, self.ventana_s = max_fallas, ventana_s
        self.bloqueo_s, self.bloqueo_max_s = bloqueo_s, bloqueo_max_s
        self.reloj = reloj
        self._fallas: dict[str, list[float]] = {}
        self._bloqueos: dict[str, tuple[float, int]] = {}  # llave -> (bloqueado_hasta, n.º de bloqueos)
        self._candado = threading.Lock()

    def espera(self, *llaves) -> int:
        """Segundos que faltan para poder intentar de nuevo (0 = puede intentar)."""
        ahora = self.reloj()
        with self._candado:
            return max([int(self._bloqueos.get(k, (0, 0))[0] - ahora + 0.999) for k in llaves if k] + [0])

    def fallo(self, *llaves):
        ahora = self.reloj()
        with self._candado:
            for k in filter(None, llaves):
                recientes = [t for t in self._fallas.get(k, []) if ahora - t < self.ventana_s] + [ahora]
                self._fallas[k] = recientes
                if len(recientes) >= self.max_fallas:
                    _, veces = self._bloqueos.get(k, (0, 0))
                    duracion = min(self.bloqueo_max_s, self.bloqueo_s * 2 ** veces)
                    self._bloqueos[k] = (ahora + duracion, veces + 1)
                    self._fallas[k] = []

    def acierto(self, *llaves):
        with self._candado:
            for k in filter(None, llaves):
                self._fallas.pop(k, None)
