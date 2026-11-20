#!/usr/bin/env python3
"""Capa Bronce: captura CRUDA de datos agroclimáticos (API Open-Meteo).

Descarga la serie meteorológica diaria georreferenciada para los principales
estados productores de limón con semilla (Colima, Michoacán, Guerrero, Sinaloa,
Yucatán) y la almacena en formato JSON crudo sin modificar, junto con una
bitácora de auditoría y metadatos SHA-256.

Uso:
  python src/clima_captura.py
  python src/clima_captura.py --desde 2023-11-01 --hasta 2026-10-31
  python src/clima_captura.py --forzar
"""
import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

# Importación de catálogos y utilidades
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from geoespacial import COORDENADAS_ORIGEN
from metadatos import escribir_metadato

RAIZ = SRC.parent
DESTINO = RAIZ / "data" / "bronce" / "clima"
BITACORA = DESTINO / "_bitacora.csv"
CAMPOS_BITACORA = [
    "fecha_captura_utc",
    "fuente",
    "estado",
    "lat",
    "lon",
    "fecha_inicio",
    "fecha_fin",
    "url",
    "http",
    "bytes",
    "sha256",
    "archivo",
    "resultado",
]

BASE_API = "https://archive-api.open-meteo.com/v1/archive"
USER_AGENT = "observatorio-limon-colima/2.0 (proyecto academico TecNM Campus Colima)"


def calcular_sha256_bytes(datos_bytes):
    return hashlib.sha256(datos_bytes).hexdigest()


def registrar_bitacora(fila):
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    existe = BITACORA.exists()
    with open(BITACORA, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_BITACORA)
        if not existe:
            writer.writeheader()
        writer.writerow(fila)


def construir_url(lat, lon, ini, fin):
    vars_clima = "temperature_2m_mean,temperature_2m_min,temperature_2m_max,precipitation_sum"
    return (
        f"{BASE_API}?latitude={lat}&longitude={lon}"
        f"&start_date={ini}&end_date={fin}"
        f"&daily={vars_clima}&timezone=America%2FMexico_City"
    )


def capturar_clima(desde="2023-11-01", hasta="2026-11-10", forzar=False):
    DESTINO.mkdir(parents=True, exist_ok=True)
    archivos_generados = []

    for estado, info in COORDENADAS_ORIGEN.items():
        nombre_archivo = f"{estado}_{desde}_{hasta}.json"
        ruta_archivo = DESTINO / nombre_archivo

        if ruta_archivo.exists() and not forzar:
            print(f"  Clima {estado}: ya existe ({nombre_archivo}), omitiendo.")
            archivos_generados.append(ruta_archivo)
            continue

        url = construir_url(info["lat"], info["lon"], desde, hasta)
        fecha_captura = datetime.now(timezone.utc).isoformat()
        print(f"  Descargando clima {estado} ({info['municipio']})...")

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status_code = resp.status
                contenido_bytes = resp.read()

            sha256 = calcular_sha256_bytes(contenido_bytes)
            ruta_archivo.write_bytes(contenido_bytes)
            sidecar = escribir_metadato(ruta_archivo, RAIZ / "data" / "bronce")

            registrar_bitacora({
                "fecha_captura_utc": fecha_captura,
                "fuente": "open-meteo-historical-weather",
                "estado": estado,
                "lat": info["lat"],
                "lon": info["lon"],
                "fecha_inicio": desde,
                "fecha_fin": hasta,
                "url": url,
                "http": status_code,
                "bytes": len(contenido_bytes),
                "sha256": sha256,
                "archivo": str(ruta_archivo.relative_to(RAIZ)),
                "resultado": "ok",
            })
            archivos_generados.append(ruta_archivo)
            time.sleep(1)  # Pausa de cortesía para la API
        except Exception as e:
            print(f"  Error al capturar {estado}: {e}")
            registrar_bitacora({
                "fecha_captura_utc": fecha_captura,
                "fuente": "open-meteo-historical-weather",
                "estado": estado,
                "lat": info["lat"],
                "lon": info["lon"],
                "fecha_inicio": desde,
                "fecha_fin": hasta,
                "url": url,
                "http": getattr(e, "code", 0),
                "bytes": 0,
                "sha256": "",
                "archivo": str(ruta_archivo.relative_to(RAIZ)),
                "resultado": f"error: {str(e)[:100]}",
            })

    return archivos_generados


def main():
    parser = argparse.ArgumentParser(description="Captura de clima histórico Open-Meteo")
    parser.add_argument("--desde", default="2023-11-01", help="AAAA-MM-DD")
    parser.add_argument("--hasta", default="2026-11-10", help="AAAA-MM-DD")
    parser.add_argument("--forzar", action="store_true", help="Sobrescribir existentes")
    args = parser.parse_args()

    print(f"Iniciando captura agroclimática ({args.desde} a {args.hasta})...")
    capturados = capturar_clima(args.desde, args.hasta, args.forzar)
    print(f"Captura finalizada: {len(capturados)} archivos listos en {DESTINO}")


if __name__ == "__main__":
    main()
