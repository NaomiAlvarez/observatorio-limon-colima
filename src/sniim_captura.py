#!/usr/bin/env python3
"""Capa Bronce: captura CRUDA de precios SNIIM (limon con semilla).

Guarda el HTML tal como lo entrega el sitio (sin limpiar ni transformar) y
deja una bitacora de cada captura con fecha, URL, tamano y huella SHA-256.

Uso:
  Historico  : python src/sniim_captura.py --desde 2023-11-01 --hasta 2026-10-31
  Incremental: python src/sniim_captura.py --ultimos-dias 14
Opciones utiles:
  --ventana dia|semana|mes   tamano de cada consulta del historico (por defecto: mes)
  --forzar                   vuelve a descargar aunque el archivo ya exista
"""
import argparse
import csv
import hashlib
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.robotparser import RobotFileParser

import requests

from metadatos import escribir_metadato

BASE = "http://www.economia-sniim.gob.mx"
RUTA = ("/nuevo/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/"
        "ResultadosConsultaFechaFrutasYHortalizas.aspx")

# nombre de carpeta -> ProductoId (el que aparece en la URL de resultados)
PRODUCTOS = {"limon_c_semilla_4_primera": 419}
PRECIOS_POR_ID = 2          # el mismo valor que usa el formulario al elegir Kilogramo
REGISTROS_POR_PAGINA = 500

USER_AGENT = "observatorio-limon-colima/1.0 (proyecto academico TecNM Campus Colima)"
HEADERS = {"User-Agent": USER_AGENT}
PAUSA_SEG = 2               # pausa entre peticiones
DESTINO = Path("data/bronce/sniim")
BITACORA = DESTINO / "_bitacora.csv"
CAMPOS = ["fecha_captura_utc", "producto", "producto_id", "fecha_inicio", "fecha_fin",
          "url", "http", "bytes", "sha256", "paginas", "archivo", "resultado"]


def construir_url(producto_id, ini, fin):
    return (f"{BASE}{RUTA}?fechaInicio={ini:%d/%m/%Y}&fechaFinal={fin:%d/%m/%Y}"
            f"&ProductoId={producto_id}&OrigenId=-1&Origen=Todos&DestinoId=-1"
            f"&Destino=Todos&PreciosPorId={PRECIOS_POR_ID}"
            f"&RegistrosPorPagina={REGISTROS_POR_PAGINA}")


def ventanas(desde, hasta, tipo):
    d = desde
    while d <= hasta:
        if tipo == "dia":
            f = d
        elif tipo == "semana":
            f = min(d + timedelta(days=6), hasta)
        else:  # mes
            siguiente = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
            f = min(siguiente - timedelta(days=1), hasta)
        yield d, f
        d = f + timedelta(days=1)


def cargar_robots():
    """Lee robots.txt. Si no existe o no responde, sigue con precaucion."""
    url = f"{BASE}/robots.txt"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"[robots] no se pudo consultar ({e}); se continua con precaucion")
        return None
    print(f"[robots] {url} -> HTTP {r.status_code}")
    if r.status_code != 200:
        return None
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / f"_robots_{date.today():%Y%m%d}.txt").write_text(r.text, encoding="utf-8")
    rp = RobotFileParser()
    rp.parse(r.text.splitlines())
    return rp


def descargar(url):
    for intento in range(1, 4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return r
            print(f"  HTTP {r.status_code} (intento {intento})")
        except requests.RequestException as e:
            print(f"  error de red: {e} (intento {intento})")
        time.sleep(PAUSA_SEG * intento * 2)
    return None


def paginas(contenido):
    """Devuelve N de 'Pagina 1 de N' si aparece en el HTML."""
    texto = contenido.decode("utf-8", errors="ignore")
    m = re.search(r"gina\s+\d+\s+de\s+(\d+)", texto)
    return int(m.group(1)) if m else None


def anotar(fila):
    DESTINO.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with BITACORA.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def capturar(nombre, pid, ini, fin, rp, forzar):
    archivo = DESTINO / nombre / f"{ini:%Y-%m-%d}_{fin:%Y-%m-%d}.html"
    if archivo.exists() and not forzar:
        escribir_metadato(archivo)
        print(f"[omitido] ya existe {archivo.name}")
        return
    url = construir_url(pid, ini, fin)
    if rp is not None and not rp.can_fetch(USER_AGENT, url):
        sys.exit("robots.txt NO permite esta ruta. Deteniendo la captura.")

    print(f"[captura] {nombre} {ini} -> {fin}")
    r = descargar(url)
    time.sleep(PAUSA_SEG)
    base = {"fecha_captura_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "producto": nombre, "producto_id": pid, "fecha_inicio": ini,
            "fecha_fin": fin, "url": url}
    if r is None:
        anotar({**base, "http": "", "bytes": 0, "sha256": "", "paginas": "",
                "archivo": "", "resultado": "error_descarga"})
        print("  ERROR: no se pudo descargar tras 3 intentos")
        return

    n = paginas(r.content)
    if n and n > 1 and ini < fin:
        # Hay varias paginas: dividimos el rango en dos y volvemos a pedir.
        anotar({**base, "http": r.status_code, "bytes": len(r.content),
                "sha256": hashlib.sha256(r.content).hexdigest(), "paginas": n,
                "archivo": "", "resultado": "dividido_por_paginas"})
        medio = ini + (fin - ini) // 2
        print(f"  {n} paginas: se divide en {ini}->{medio} y {medio + timedelta(days=1)}->{fin}")
        capturar(nombre, pid, ini, medio, rp, forzar)
        capturar(nombre, pid, medio + timedelta(days=1), fin, rp, forzar)
        return

    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_bytes(r.content)          # bytes tal cual: Bronce no se toca
    escribir_metadato(archivo)
    resultado = "ok"
    if n and n > 1:
        resultado = "ok_con_mas_paginas_sin_capturar"
        print("  AVISO: un solo dia con mas de una pagina; revisar manualmente")
    anotar({**base, "http": r.status_code, "bytes": len(r.content),
            "sha256": hashlib.sha256(r.content).hexdigest(), "paginas": n or "",
            "archivo": str(archivo), "resultado": resultado})
    print(f"  guardado {archivo} ({len(r.content)} bytes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", type=date.fromisoformat, help="AAAA-MM-DD")
    ap.add_argument("--hasta", type=date.fromisoformat, help="AAAA-MM-DD")
    ap.add_argument("--ultimos-dias", type=int, help="captura incremental")
    ap.add_argument("--ventana", choices=["dia", "semana", "mes"], default="mes")
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args()

    if a.ultimos_dias:
        hasta = date.today()
        rangos = [(hasta - timedelta(days=a.ultimos_dias - 1), hasta)]
    elif a.desde and a.hasta:
        rangos = list(ventanas(a.desde, a.hasta, a.ventana))
    else:
        ap.error("usa --ultimos-dias N, o bien --desde y --hasta")

    rp = cargar_robots()
    for nombre, pid in PRODUCTOS.items():
        for ini, fin in rangos:
            capturar(nombre, pid, ini, fin, rp, a.forzar)


if __name__ == "__main__":
    main()