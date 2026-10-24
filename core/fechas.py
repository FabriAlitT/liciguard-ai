"""Fecha y hora de Lima, sin depender de la zona horaria del servidor.

En Streamlit Community Cloud el servidor corre en UTC: después de las 7 p. m. de Lima, `date.today()`
ya devuelve el día siguiente y los "días que faltan" salen con un día de diferencia.
El Perú no tiene horario de verano, así que basta con un desfase fijo de UTC−5
(y así no se necesita la base de zonas horarias `tzdata`, que Windows no trae).
"""
from datetime import date, datetime, timedelta, timezone

LIMA = timezone(timedelta(hours=-5), "America/Lima")


def ahora_lima() -> datetime:
    return datetime.now(LIMA)


def hoy_lima() -> date:
    return ahora_lima().date()
