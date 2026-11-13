from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
d = pd.read_parquet(RAIZ / "data/plata/sniim_diario_homologado.parquet")
claves = ["fecha", "presentacion", "origen_estado", "destino_mercado"]

distintos = d.groupby(claves)["precio_frec"].nunique()
print("Claves con precios distintos entre archivos:", (distintos > 1).sum())
print("\nDuplicados por archivo de origen:")
print(d[d["es_duplicado"]]["archivo_origen"].value_counts().to_string())
