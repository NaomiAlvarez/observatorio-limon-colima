from io import StringIO
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
bronce = RAIZ / "data/bronce"


def leer_texto(ruta):
    """Lee un archivo probando codificaciones."""
    crudo = Path(ruta).read_bytes()
    for enc in ("utf-8", "latin-1"):
        try:
            return crudo.decode(enc)
        except UnicodeDecodeError:
            continue


# ---------------- SNIIM (HTML) ----------------
htmls = sorted((bronce / "sniim").rglob("*.html"))
print("Total HTML SNIIM:", len(htmls))
ejemplo = htmls[1]
print("Ejemplo:", ejemplo.name)

tablas = pd.read_html(StringIO(leer_texto(ejemplo)))
print("Tablas encontradas:", len(tablas))
for i, t in enumerate(tablas):
    print(f"\n--- Tabla {i}: {t.shape} ---")
    print(t.head(8).to_string())

# ---------------- SIAP (.gz) ----------------
gz = sorted((bronce / "siap" / "municipal").glob("*.gz"))
print("\n\nArchivos SIAP .gz:", len(gz))
for g in gz[:5]:
    print(" ", g.name)

g0 = gz[0]
for enc in ("utf-8", "latin-1"):
    try:
        d = pd.read_csv(g0, compression="gzip", encoding=enc, nrows=5)
        print(f"\nLeído {g0.name} con {enc}")
        print("Columnas:", list(d.columns))
        print(d.to_string())
        break
    except UnicodeDecodeError:
        continue

# ---------------- Bitácora SIAP ----------------
print("\n\nBitácora SIAP:")
b = pd.read_csv(bronce / "siap" / "_bitacora.csv")
print(b[["recurso", "archivo", "resultado"]].head(30).to_string())