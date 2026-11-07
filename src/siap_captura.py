#!/usr/bin/env python3
"""Capa Bronce: captura CRUDA de la Estadistica de Produccion Agricola (SIAP).

Descarga el CSV anual a nivel municipal (cierre definitivo de cada anio) y lo
guarda sin modificar. Para ahorrar espacio en el repositorio, los bytes se
comprimen con gzip (compresion sin perdida: al descomprimir se obtiene el
archivo original, byte por byte). Registra cada descarga en una bitacora.

Uso:
  python src/siap_captura.py --desde 2003 --hasta 2025
  python src/siap_captura.py                # anios 2003 hasta el anio actual
Opciones:
  --forzar   vuelve a descargar aunque el archivo ya exista
"""
import argparse
import csv
import gzip
import hashlib
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.robotparser import RobotFileParser

import requests

BASE = "https://nube.agricultura.gob.mx"
VISTA_MUNICIPAL = "10AE434F-A2158368-A120BC5A-EDF4AFAA"      # cierres 2003-2025
VISTA_DICCIONARIO = "5D24F995-E734D711-1EA6F8D2-9D1387D7"    # diccionario de datos (XLSX)
PRIMER_ANIO = 2003

USER_AGENT = "observatorio-limon-colima/1.0 (proyecto academico TecNM Campus Colima)"
HEADERS = {"User-Agent": USER_AGENT}
PAUSA_SEG = 3
DESTINO = Path("data/bronce/siap")
BITACORA = DESTINO / "_bitacora.csv"
CAMPOS = ["fecha_captura_utc", "recurso", "url", "http", "bytes_originales", "sha256",
          "archivo", "resultado"]


def url_anio(anio):
    return f"{BASE}/index.php?view={VISTA_MUNICIPAL}&ANIO={anio}"


def url_diccionario():
    return f"{BASE}/index.php?view={VISTA_DICCIONARIO}"


def cargar_robots():
    url = f"{BASE}/robots.txt"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"[robots] no se pudo consultar ({e}); se continua con precaucion")
        return None
    print(f"[robots] {url} -> HTTP {r.status_code}")
    if r.status_code != 200:
        return None          # sin robots.txt: el sitio no declara restricciones
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / f"_robots_{date.today():%Y%m%d}.txt").write_text(r.text, encoding="utf-8")
    rp = RobotFileParser()
    rp.parse(r.text.splitlines())
    return rp


def descargar(url):
    for intento in range(1, 4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=180)
            if r.status_code == 200:
                return r
            print(f"  HTTP {r.status_code} (intento {intento})")
            if r.status_code in (404, 410):
                return r         # no tiene caso reintentar
        except requests.RequestException as e:
            print(f"  error de red: {e} (intento {intento})")
        time.sleep(PAUSA_SEG * intento * 2)
    return None


def anotar(fila):
    DESTINO.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with BITACORA.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def parece_html(contenido):
    return contenido[:200].lstrip().lower().startswith((b"<!doctype", b"<html", b"<?xml"))


def capturar(recurso, url, archivo, comprimir, rp, forzar):
    if archivo.exists() and not forzar:
        print(f"[omitido] ya existe {archivo.name}")
        return
    if rp is not None and not rp.can_fetch(USER_AGENT, url):
        sys.exit("robots.txt NO permite esta ruta. Deteniendo la captura.")
    print(f"[captura] {recurso}")
    r = descargar(url)
    time.sleep(PAUSA_SEG)
    base = {"fecha_captura_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "recurso": recurso, "url": url}
    if r is None or r.status_code != 200:
        codigo = "" if r is None else r.status_code
        anotar({**base, "http": codigo, "bytes_originales": 0, "sha256": "",
                "archivo": "", "resultado": "no_disponible"})
        print("  no disponible (se registra en la bitacora)")
        return
    if comprimir and parece_html(r.content):
        anotar({**base, "http": r.status_code, "bytes_originales": len(r.content),
                "sha256": hashlib.sha256(r.content).hexdigest(), "archivo": "",
                "resultado": "respuesta_html_no_csv"})
        print("  AVISO: el servidor devolvio una pagina HTML y no un CSV; no se guarda")
        return

    archivo.parent.mkdir(parents=True, exist_ok=True)
    if comprimir:
        with gzip.open(archivo, "wb") as f:
            f.write(r.content)
    else:
        archivo.write_bytes(r.content)
    anotar({**base, "http": r.status_code, "bytes_originales": len(r.content),
            "sha256": hashlib.sha256(r.content).hexdigest(), "archivo": str(archivo),
            "resultado": "ok"})
    print(f"  guardado {archivo} ({len(r.content)} bytes originales)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", type=int, default=PRIMER_ANIO)
    ap.add_argument("--hasta", type=int, default=date.today().year)
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args()

    rp = cargar_robots()
    capturar("diccionario_municipal", url_diccionario(),
             DESTINO / "diccionario_datos_municipal.xlsx", False, rp, a.forzar)
    for anio in range(max(a.desde, PRIMER_ANIO), a.hasta + 1):
        capturar(f"produccion_municipal_{anio}", url_anio(anio),
                 DESTINO / "municipal" / f"cierre_{anio}.csv.gz", True, rp, a.forzar)


if __name__ == "__main__":
    main()