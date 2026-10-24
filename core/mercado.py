"""Inteligencia de mercado con los datos abiertos (OCDS): módulo Oportunidades y "Para crecer".

Importante (dilo así en la demo): los datos abiertos muestran procesos ya ADJUDICADOS.
Sirven para saber dónde se compra tu rubro, cuánto, con cuánta competencia y quién gana;
las convocatorias abiertas en tiempo real son la siguiente fase del producto.
"""
import pandas as pd

from core.fechas import hoy_lima

from core.historial_ocds import clave_proveedor


def _num(serie):
    return pd.to_numeric(serie, errors="coerce")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not len(df):
        return pd.DataFrame()
    d = df.copy()
    d["valor"] = _num(d.get("valor_estimado"))
    d["adjudicado"] = _num(d.get("monto_adjudicado"))
    d["participantes"] = _num(d.get("n_postores"))
    d["anio"] = d.get("fecha", pd.Series([""] * len(d))).astype(str).str[:4]
    if "rubro" not in d:
        d["rubro"] = "Sin rubro"
    d["proveedor"] = d.get("ganador", "").map(clave_proveedor)
    return d


def rubros(d: pd.DataFrame) -> list[str]:
    return sorted(x for x in d["rubro"].dropna().unique() if x) if len(d) else []


def filtrar(d, rubro=None, entidad=None, monto_max=None, desde=None):
    if not len(d):
        return d
    m = pd.Series(True, index=d.index)
    if rubro and rubro != "Todos":
        m &= d["rubro"] == rubro
    if entidad:
        m &= d["entidad"].str.contains(entidad, case=False, na=False, regex=False)
    if monto_max:
        m &= d["valor"] <= monto_max
    if desde:
        m &= d["anio"] >= str(desde)
    return d[m]


def resumen(d) -> dict:
    if not len(d):
        return {"n": 0}
    return {
        "n": len(d),
        "monto_total": float(d["adjudicado"].fillna(d["valor"]).sum()),
        "valor_mediano": float(d["valor"].median()) if d["valor"].notna().any() else None,
        "participantes_mediana": float(d["participantes"].median()) if d["participantes"].notna().any() else None,
        "pct_un_participante": float((d["participantes"] == 1).mean()),
        "entidades": int(d["entidad"].nunique()),
        "ganadores": int(d["proveedor"].nunique()),
    }


def por_anio(d) -> pd.DataFrame:
    if not len(d):
        return pd.DataFrame(columns=["Año", "Procesos", "Monto (S/)"])
    g = d[d["anio"].str.match(r"20\d\d", na=False)].groupby("anio")
    return pd.DataFrame({"Año": g.size().index, "Procesos": g.size().values,
                         "Monto (S/)": g["adjudicado"].sum().values}).sort_values("Año")


def top_entidades(d, k=10) -> pd.DataFrame:
    if not len(d):
        return pd.DataFrame()
    filas = []
    for entidad, g in d.groupby("entidad"):
        conteo = g["proveedor"].value_counts()
        filas.append({
            "Entidad": entidad, "Procesos": len(g), "Monto total (S/)": g["adjudicado"].sum(),
            "Valor típico (S/)": g["valor"].median(), "Participantes (mediana)": g["participantes"].median(),
            "Concentración": conteo.iloc[0] / len(g) if len(conteo) else None,
            "Último": g["fecha"].max(),
        })
    return pd.DataFrame(filas).sort_values(["Procesos", "Monto total (S/)"], ascending=False).head(k)


def a_tu_medida(d, experiencia: float, factor: float = 1.0, k=12) -> pd.DataFrame:
    """Procesos cuyo valor podrías respaldar con tu experiencia (supuesto: piden ~factor × valor)."""
    if not len(d) or not experiencia:
        return pd.DataFrame()
    x = d[(d["valor"] > 0) & (d["valor"] * factor <= experiencia)]
    x = x.sort_values(["fecha", "participantes"], ascending=[False, True]).head(k)
    return pd.DataFrame({"Fecha": x["fecha"], "Entidad": x["entidad"], "Proceso": x["titulo"].str[:90],
                         "Valor (S/)": x["valor"], "Participantes": x["participantes"], "Ganó": x["ganador"]})


def socios(d, monto_minimo: float = 0, k=12) -> pd.DataFrame:
    """Empresas que ganaron en el rubro (posibles socios para consorcio), por experiencia acumulada."""
    if not len(d):
        return pd.DataFrame()
    x = d[~d["ganador"].fillna("").str.contains(" / ", regex=False)]  # sin consorcios
    g = x.groupby("proveedor").agg(Empresa=("ganador", "first"), Ganados=("ocid", "count"),
                                   Experiencia=("adjudicado", "sum"), Último=("fecha", "max"))
    g = g[g["Experiencia"] >= monto_minimo].sort_values(["Experiencia"], ascending=False)
    return g.rename(columns={"Experiencia": "Experiencia acumulada (S/)"}).head(k).reset_index(drop=True)


RANGOS = [(0, 100_000, "Hasta 100 mil"), (100_000, 500_000, "100–500 mil"), (500_000, 1_000_000, "500 mil–1 M"),
          (1_000_000, 5_000_000, "1–5 M"), (5_000_000, float("inf"), "Más de 5 M")]


def rangos(d) -> pd.DataFrame:
    """Cuántos procesos hay por tamaño de compra (para ver dónde está tu mercado)."""
    if not len(d):
        return pd.DataFrame(columns=["Rango", "Procesos", "orden"])
    v = d["valor"].dropna()
    v = v[v > 0]
    return pd.DataFrame([{"Rango": n, "Procesos": int(((v >= a) & (v < b)).sum()), "orden": i}
                         for i, (a, b, n) in enumerate(RANGOS)])


def top_ganadores(d, k=8) -> pd.DataFrame:
    """Proveedores que más monto ganaron y su participación en el total."""
    if not len(d):
        return pd.DataFrame()
    total = d["adjudicado"].sum() or 1
    g = d.groupby("proveedor").agg(Empresa=("ganador", "first"), Ganados=("ocid", "count"),
                                   Monto=("adjudicado", "sum")).sort_values("Monto", ascending=False).head(k)
    g["Participación"] = g["Monto"] / total
    g["Empresa"] = g["Empresa"].astype(str).str[:42]
    return g.reset_index(drop=True)


def variacion_anual(d) -> tuple[str, str, float | None]:
    """Compara los dos últimos años completos (por número de procesos)."""
    anual = por_anio(d)
    anual = anual[anual["Año"] < str(hoy_lima().year)]
    if len(anual) < 2:
        return "", "", None
    a, b = anual.iloc[-2], anual.iloc[-1]
    return a["Año"], b["Año"], (b["Procesos"] - a["Procesos"]) / a["Procesos"] if a["Procesos"] else None


def percentil(d, monto: float) -> float | None:
    """Qué parte de los procesos tiene un valor menor o igual a ese monto."""
    v = d["valor"].dropna() if len(d) else pd.Series(dtype=float)
    v = v[v > 0]
    return float((v <= monto).mean()) if len(v) and monto else None


def brechas(d, experiencia: float, factor: float = 1.0) -> pd.DataFrame:
    """% de procesos del rubro a los que podrías acceder hoy y con más experiencia."""
    if not len(d):
        return pd.DataFrame()
    valores = d["valor"].dropna()
    valores = valores[valores > 0]
    if not len(valores):
        return pd.DataFrame()
    base = max(experiencia or 0, 0)
    metas = [("Hoy", base), ("+ S/ 200 mil", base + 200_000), ("+ S/ 500 mil", base + 500_000),
             ("+ S/ 1 millón", base + 1_000_000)]
    return pd.DataFrame([{"Meta": n, "Experiencia (S/)": e,
                          "Procesos accesibles (%)": round(float((valores * factor <= e).mean()) * 100, 1)}
                         for n, e in metas])
