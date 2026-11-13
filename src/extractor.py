"""Punto de entrada de la extracción (capa Bronce).

Ejecuta las dos capturas del proyecto:
  - SNIIM: precios de mayoreo (src/sniim_captura.py)
  - SIAP: producción municipal (src/siap_captura.py)

Uso:  python src/extractor.py [--ultimos-dias N]
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent


def main():
    args_sniim = sys.argv[1:]   # se reenvían tal cual a sniim_captura.py
    for script, args in (("sniim_captura.py", args_sniim), ("siap_captura.py", [])):
        subprocess.run([sys.executable, str(SRC / script), *args], check=True)


if __name__ == "__main__":
    main()