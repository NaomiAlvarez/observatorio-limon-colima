#!/usr/bin/env python3
"""Genera sidecars JSON con el tamaño y SHA-256 de los archivos crudos Bronce."""
import hashlib
import json
from pathlib import Path

RAIZ_REPOSITORIO = Path(__file__).resolve().parent.parent
RAIZ_BRONCE = RAIZ_REPOSITORIO / "data" / "bronce"
ARCHIVOS_AUXILIARES = {"_bitacora.csv"}


def calcular_sha256(archivo):
    """Calcula el SHA-256 leyendo el archivo en bloques."""
    digest = hashlib.sha256()
    with Path(archivo).open("rb") as contenido:
        for bloque in iter(lambda: contenido.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def escribir_metadato(archivo, raiz_bronce=RAIZ_BRONCE):
    """Escribe el sidecar JSON de un archivo crudo y devuelve su ruta."""
    archivo = Path(archivo)
    raiz_bronce = Path(raiz_bronce)
    ruta_relativa = archivo.resolve().relative_to(raiz_bronce.resolve())
    metadato = archivo.with_name(f"{archivo.name}.metadata.json")
    datos = {
        "archivo": ruta_relativa.as_posix(),
        "bytes": archivo.stat().st_size,
        "algoritmo": "SHA-256",
        "sha256": calcular_sha256(archivo),
    }
    metadato.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadato


def es_archivo_crudo(archivo):
    """Identifica datos crudos, omitiendo bitácoras y archivos auxiliares."""
    return (
        archivo.is_file()
        and archivo.name != ".gitkeep"
        and archivo.name not in ARCHIVOS_AUXILIARES
        and not archivo.name.startswith("_robots_")
        and not archivo.name.endswith(".metadata.json")
    )


def generar_metadatos(raiz_bronce=RAIZ_BRONCE):
    """Genera o actualiza los sidecars de los archivos crudos encontrados."""
    raiz_bronce = Path(raiz_bronce)
    return [
        escribir_metadato(archivo, raiz_bronce)
        for archivo in sorted(raiz_bronce.rglob("*"))
        if es_archivo_crudo(archivo)
    ]


if __name__ == "__main__":
    generados = generar_metadatos()
    print(f"Metadatos generados: {len(generados)}")
