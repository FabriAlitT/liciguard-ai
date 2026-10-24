"""Baja bases REALES del SEACE desde TU computadora y las prueba con LiciGuard.

Uso (en la carpeta del proyecto, con el venv activo):
    python bajar_bases_reales.py                              -> busca 10 bases útiles de Uniformes desde 2025
    python bajar_bases_reales.py --utiles 15 --rubro Limpieza --desde 2024
    python bajar_bases_reales.py --sin-abrir                  -> no abre el reporte al terminar
    python bajar_bases_reales.py --a-galeria 4                -> copia 4 bases útiles a ejemplos/reales/ (galería
                                                                 «Ejemplos» de la app publicada; súbelas a GitHub)

Qué hace:
  1. Recorre procesos variados de data/ocds/historial.csv (datos abiertos del OECE) hasta juntar las bases ÚTILES
     que pediste (PDF con texto que parecen bases). Si lo vuelves a ejecutar, CONTINÚA: no repite lo ya intentado.
  2. Saca los PDF de los ZIP (también ZIP dentro de ZIP) y acepta archivos de hasta 50 MB.
  3. Lo dudoso (no parece unas bases) va a data/bases/revisar_a_mano/ para que lo mires tú.
  4. Prueba LiciGuard en cada base útil y abre un REPORTE (data/bases/reporte.html) con la recomendación de cada una
     y los enlaces para bajar a mano las que no se pudieron (RAR, Word, escaneadas).
"""
import argparse
import html
import re
import sys
import time
import webbrowser
from pathlib import Path

import pandas as pd

from core.bases_reales import (ArchivoMuyGrande, contenido_zip, descargar, elegir_procesos, procesar_descarga,
                               revisar_pdf)

RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ / "data" / "bases"
DUDOSOS = CARPETA / "revisar_a_mano"
REGISTRO = CARPETA / "descargas.csv"
ICONO = {"sirve": "✅", "dudoso": "🟡", "manual": "⬇️", "ocr": "📷", "error": "❌"}


def _limpio(texto, n=110):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", texto)[:n]


def clasificar(p) -> dict:
    """Descarga y revisa un proceso. Devuelve una fila del registro."""
    f = {"ocid": p["ocid"], "fecha": p["fecha"], "entidad": p["entidad"], "titulo": p["titulo"][:140],
         "rubro": p.get("rubro", ""),
         "valor_estimado": p.get("valor_estimado", ""), "url": p["url"], "archivo": "", "estado": "error", "motivo": ""}
    try:
        data = descargar(p["url"])
    except ArchivoMuyGrande as e:
        return {**f, "estado": "manual", "motivo": f"muy pesado ({e}): bájalo a mano"}
    except Exception as e:
        return {**f, "motivo": f"no se pudo descargar ({type(e).__name__}); prueba a mano"}
    tipo, pdfs = procesar_descarga(data)
    if not pdfs:
        motivos = {"html": "el SEACE pidió navegador: bájalo a mano", "rar": "viene en RAR: descomprímelo a mano",
                   "doc": "es un Word (.doc): ábrelo y guárdalo como PDF", "docx": "es un Word (.docx): guárdalo como PDF",
                   "zip": f"ZIP sin PDF ({contenido_zip(data)})"}
        return {**f, "estado": "manual", "motivo": motivos.get(tipo, f"formato {tipo}")}
    nombre, pdf = pdfs[0]                                   # los que dicen "bases" van primero
    r = revisar_pdf(pdf)
    archivo = _limpio(f"{p['fecha']}_{p['entidad'][:30]}_{nombre}")
    if r["motivo"] == "sirve":
        (CARPETA / archivo).write_bytes(pdf)
        return {**f, "archivo": archivo, "estado": "sirve", "motivo": f"{r['paginas']} páginas con texto"}
    if r["con_texto"] < 0.5:
        return {**f, "estado": "ocr", "motivo": f"escaneado ({r['paginas']} págs. sin texto): necesitaría OCR"}
    DUDOSOS.mkdir(exist_ok=True)
    (DUDOSOS / archivo).write_bytes(pdf)
    return {**f, "archivo": f"revisar_a_mano/{archivo}", "estado": "dudoso",
            "motivo": "no parece unas bases (quedó en revisar_a_mano/)"}


def probar_con_liciguard(registro: pd.DataFrame) -> pd.DataFrame:
    """Analiza cada base útil con las mismas reglas de la app (sin IA)."""
    from core.buscador import Normativa
    from core.historial_ocds import cargar_historial
    from core.pdf_parser import extraer_paginas
    from core.preguntas import analizar
    norm, hist = Normativa.cargar(), cargar_historial()
    perfil = {"experiencia_soles": 320000, "es_mype": True, "rnp_vigente": True, "certificaciones": []}
    salida = []
    for fila in registro[registro["estado"] == "sirve"].itertuples():
        try:
            r = analizar(extraer_paginas((CARPETA / fila.archivo).read_bytes()), perfil, norm, hist)
            d = r["datos"]
            salida.append({"url": fila.url, "recomendacion": r["recomendacion"]["codigo"],
                           "alertas": len(r["justa"]["hallazgos"]), "requisitos": len(r["requisitos"]),
                           "valor_leido": d.get("valor_estimado"), "cronograma": len(r["cronograma"])})
        except Exception as e:
            salida.append({"url": fila.url, "recomendacion": f"error: {type(e).__name__}"})
    return pd.DataFrame(salida)


def reporte(registro, analisis, ruta):
    reco = {"postular": ("Postular", "#059669", "#E3F8EF"), "observar": ("Observar primero", "#D97706", "#FFF4DD"),
            "no_postular": ("No te conviene", "#DC2626", "#FDECEC")}
    info = analisis.set_index("url").to_dict("index") if len(analisis) else {}
    cuenta = registro["estado"].value_counts()
    chips = "".join(f'<span class="chip">{ICONO[e]} {n} {t}</span>' for e, t, n in [
        ("sirve", "útiles", cuenta.get("sirve", 0)), ("dudoso", "dudosas", cuenta.get("dudoso", 0)),
        ("manual", "para bajar a mano", cuenta.get("manual", 0)), ("ocr", "escaneadas", cuenta.get("ocr", 0)),
        ("error", "con error", cuenta.get("error", 0))])
    filas = []
    for r in registro.sort_values("estado", key=lambda s: s.map({"sirve": 0, "dudoso": 1, "manual": 2})
                                  .fillna(3)).itertuples():
        a = info.get(r.url, {})
        t, c, bg = reco.get(a.get("recomendacion"), ("—", "#51607A", "#EEF2F7"))
        detalle = (f'<span class="pill" style="color:{c};background:{bg}">{t}</span> '
                   f'<small>{a.get("alertas", 0)} alertas · {a.get("requisitos", 0)} requisitos · '
                   f'valor {"leído" if a.get("valor_leido") else "<b>no leído</b>"} · '
                   f'cronograma {a.get("cronograma", 0)}/3</small>') if a else ""
        accion = (f'<a href="{html.escape(r.url)}" target="_blank">Bajar del SEACE</a>'
                  if r.estado != "sirve" else f'<code>{html.escape(r.archivo)}</code>')
        filas.append(f'<tr><td>{ICONO.get(r.estado, "")}</td><td style="white-space:nowrap">{html.escape(str(r.fecha))}</td>'
                     f'<td><b>{html.escape(str(r.entidad))}</b><br><small>{html.escape(str(r.titulo))}</small></td>'
                     f'<td>{html.escape(str(r.motivo))}<br>{detalle}</td><td>{accion}</td></tr>')
    ruta.write_text(f"""<!doctype html><html lang="es"><meta charset="utf-8"><title>LiciGuard · Bases reales</title>
<style>
body{{font-family:'Segoe UI',system-ui,sans-serif;margin:0;background:#F4F7FC;color:#0B1B3F}}
.band{{background:linear-gradient(120deg,#1D4ED8,#2563EB 45%,#06B6D4);color:#fff;padding:28px 36px}}
.band h1{{margin:4px 0;font-size:26px}} .band p{{margin:0;opacity:.9}} main{{padding:24px 36px}}
.chip{{display:inline-block;background:#fff;border:1px solid #E2E8F2;border-radius:999px;padding:6px 14px;margin:0 6px 8px 0;
font-weight:700;font-size:14px}} table{{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;
box-shadow:0 1px 3px rgba(11,27,63,.08)}} td,th{{padding:10px 12px;border-bottom:1px solid #EEF2F7;text-align:left;font-size:14px;
vertical-align:top}} th{{background:#F8FAFF;color:#51607A;font-size:12px;text-transform:uppercase;letter-spacing:.05em}}
small{{color:#7A879C}} a{{color:#2563EB;font-weight:700}} .pill{{border-radius:999px;padding:2px 10px;font-weight:700;font-size:12px}}
.tip{{background:#FFF7E6;border:1px solid #FCE2B0;border-radius:12px;padding:12px 16px;margin:14px 0;color:#8A4B00}}
</style>
<div class="band"><small style="color:#DBEAFE;font-weight:700;letter-spacing:.08em">LICIGUARD · BASES REALES DEL SEACE</small>
<h1>{cuenta.get("sirve", 0)} bases listas para probar</h1><p>Generado el {time.strftime("%d/%m/%Y %H:%M")} ·
{len(registro)} procesos intentados · las útiles están en <b>data/bases/</b></p></div>
<main>{chips}
<div class="tip">⬇️ Para las que dicen <b>Bajar del SEACE</b>: haz clic, guarda el archivo en <b>data/bases/</b>
(si es ZIP o RAR, descomprímelo; si es Word, ábrelo y «Guardar como PDF»). Luego súbelas en la app.<br>
🔎 Si muchas dicen <b>valor no leído</b> o <b>cronograma 0/3</b>, anótalo: son los patrones que hay que mejorar.</div>
<table><tr><th></th><th>Fecha</th><th>Proceso</th><th>Resultado</th><th>Archivo</th></tr>{"".join(filas)}</table></main>""",
                    encoding="utf-8")


def a_galeria(registro: pd.DataFrame, analisis: pd.DataFrame, cuantas: int, max_mb: float = 15) -> int:
    """Copia las bases útiles más livianas (y variadas) a ejemplos/reales/ con su catalogo.csv."""
    destino = RAIZ / "ejemplos" / "reales"
    destino.mkdir(parents=True, exist_ok=True)
    utiles = registro[registro["estado"] == "sirve"].copy()
    utiles = utiles[utiles["archivo"].map(lambda a: (CARPETA / a).exists())]
    if not len(utiles):
        return 0
    utiles["mb"] = utiles["archivo"].map(lambda a: (CARPETA / a).stat().st_size / 1e6)
    utiles = utiles[utiles["mb"] <= max_mb]
    if len(analisis):
        utiles = utiles.merge(analisis[["url", "recomendacion"]], on="url", how="left")
        utiles["orden"] = utiles.groupby("recomendacion").cumcount()      # una de cada recomendación primero
        utiles = utiles.sort_values(["orden", "mb"])
    else:
        utiles = utiles.sort_values("mb")
    elegidas = utiles.head(cuantas)
    for a in elegidas["archivo"]:
        (destino / a).write_bytes((CARPETA / a).read_bytes())
    columnas = ["archivo", "entidad", "titulo", "valor_estimado", "fecha", "url", "rubro"]
    catalogo = destino / "catalogo.csv"
    previo = pd.read_csv(catalogo, dtype=str, keep_default_na=False) if catalogo.exists() else pd.DataFrame()
    nuevo = elegidas.reindex(columns=columnas).fillna("")
    pd.concat([previo, nuevo]).drop_duplicates("archivo", keep="last").to_csv(catalogo, index=False)
    return len(elegidas)


def main():
    a = argparse.ArgumentParser(description="Baja bases reales del SEACE y las prueba con LiciGuard")
    a.add_argument("--rubro", default="Uniformes y textiles")
    a.add_argument("--desde", default="2025")
    a.add_argument("--utiles", type=int, default=10, help="cuántas bases útiles quieres juntar")
    a.add_argument("--max-intentos", type=int, default=60, help="máximo de procesos a intentar en esta corrida")
    a.add_argument("--pausa", type=float, default=2.5, help="segundos entre descargas (sé amable con el SEACE)")
    a.add_argument("--sin-abrir", action="store_true", help="no abrir el reporte en el navegador al terminar")
    a.add_argument("--a-galeria", type=int, default=0,
                   help="copia N bases útiles a ejemplos/reales/ para la galería de la app publicada")
    args = a.parse_args()

    hist = pd.read_csv(RAIZ / "data" / "ocds" / "historial.csv", dtype=str, keep_default_na=False)
    if args.rubro not in set(hist["rubro"]):
        sys.exit(f"Rubro no encontrado. Usa uno de: {', '.join(sorted(hist['rubro'].unique()))}")
    CARPETA.mkdir(parents=True, exist_ok=True)
    previo = pd.read_csv(REGISTRO, dtype=str, keep_default_na=False) if REGISTRO.exists() else pd.DataFrame()
    ya = set(previo["url"]) if len(previo) else set()
    utiles = int((previo["estado"] == "sirve").sum()) if len(previo) else 0
    candidatos = elegir_procesos(hist, args.rubro, args.desde, cuantos=100000, max_por_entidad=2)
    candidatos = candidatos[~candidatos["url"].isin(ya)].head(args.max_intentos)
    print(f"\nLiciGuard · bases reales · {args.rubro} desde {args.desde}")
    print(f"Ya tenías {utiles} útiles. Meta: {args.utiles}. Procesos nuevos por intentar: {len(candidatos)}\n")

    nuevas = []
    for i, p in enumerate(candidatos.to_dict("records"), 1):
        if utiles >= args.utiles:
            break
        f = clasificar(p)
        utiles += f["estado"] == "sirve"
        nuevas.append(f)
        print(f"{ICONO[f['estado']]} [{utiles:>2}/{args.utiles}] {f['motivo'][:48]:<48} · {p['entidad'][:42]}")
        time.sleep(args.pausa)

    registro = pd.concat([previo, pd.DataFrame(nuevas)], ignore_index=True) if nuevas else previo
    if not len(registro):
        sys.exit("No hubo procesos para intentar.")
    registro.to_csv(REGISTRO, index=False)
    print("\nProbando LiciGuard en las bases útiles…")
    analisis = probar_con_liciguard(registro)
    if len(analisis):
        analisis.to_csv(CARPETA / "resultados_liciguard.csv", index=False)
        print(analisis["recomendacion"].value_counts().to_string())
    if args.a_galeria:
        n = a_galeria(registro, analisis, args.a_galeria)
        print(f"\n🖼️  {n} bases copiadas a ejemplos/reales/ (súbelas a GitHub para que las vean los jurados)")
    ruta = CARPETA / "reporte.html"
    reporte(registro, analisis, ruta)
    print(f"\n✅ {utiles} bases útiles en data/bases/ · reporte: {ruta}")
    if utiles < args.utiles:
        print("   No se llegó a la meta: vuelve a ejecutar (continúa donde quedó) o baja a mano desde el reporte.")
    if not args.sin_abrir:
        webbrowser.open(ruta.as_uri())


if __name__ == "__main__":
    main()
