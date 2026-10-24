"""Búsqueda local tipo BM25 (la parte "R" del RAG), sin servicios externos ni tokens.

Se usa para:
  - encontrar artículos de la normativa relacionados con cada señal,
  - encontrar las páginas de las bases que responden la pregunta del asistente.
"""
import json
import math
import re
from collections import Counter

from core.config import ARCHIVO_NORMATIVA
from core.extraccion import sin_tildes

VACIAS = set("""a al algo ante bajo cada como con contra cual cuando de del desde donde dos e el ella ellos
en entre era es esa ese esta este esto estos fue ha han hasta la las le les lo los mas me mi muy no nos o
para pero por que se si sin sobre su sus tambien te tiene un una uno unos y ya debe deberá sera será dicho
dicha cuyo cuya asi""".split())


def tokens(texto: str) -> list[str]:
    palabras = re.findall(r"[a-z0-9]+", sin_tildes(texto.lower()))
    return [w[:7] for w in palabras if len(w) > 2 and w not in VACIAS]  # raíz simple: 7 letras


class BM25:
    def __init__(self, documentos: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = [tokens(d) for d in documentos]
        self.n = len(self.docs)
        self.prom = sum(map(len, self.docs)) / self.n if self.n else 0
        self.df = Counter(t for d in self.docs for t in set(d))
        self.tf = [Counter(d) for d in self.docs]
        self.k1, self.b = k1, b

    def puntajes(self, consulta: str) -> list[float]:
        q = tokens(consulta)
        res = []
        for i, tf in enumerate(self.tf):
            s, largo = 0.0, len(self.docs[i]) or 1
            for t in q:
                if t not in tf:
                    continue
                idf = math.log(1 + (self.n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                s += idf * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * largo / self.prom))
            res.append(s)
        return res

    def top(self, consulta: str, k: int = 3) -> list[tuple[int, float]]:
        p = self.puntajes(consulta)
        orden = sorted(range(len(p)), key=lambda i: p[i], reverse=True)
        return [(i, p[i]) for i in orden[:k] if p[i] > 0]


class Normativa:
    """Artículos de la Ley 32069, su Reglamento, bases estándar y opiniones (preparados en el notebook)."""

    def __init__(self, articulos: list[dict]):
        self.articulos = articulos
        self.indice = BM25([f"{a.get('articulo', '')} {a.get('titulo', '')} {a['texto']}" for a in articulos]) \
            if articulos else None

    @classmethod
    def cargar(cls, ruta=ARCHIVO_NORMATIVA):
        try:
            return cls(json.loads(ruta.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls([])

    @property
    def disponible(self) -> bool:
        return bool(self.articulos)

    def buscar(self, consulta: str, k: int = 3) -> list[dict]:
        if not self.indice:
            return []
        return [{**self.articulos[i], "puntaje": round(s, 2)} for i, s in self.indice.top(consulta, k)]


def buscar_en_paginas(paginas: list[dict], consulta: str, k: int = 3) -> list[dict]:
    if not paginas:
        return []
    indice = BM25([p["texto"] for p in paginas])
    return [{**paginas[i], "puntaje": round(s, 2)} for i, s in indice.top(consulta, k)]
