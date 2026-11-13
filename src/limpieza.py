import numpy as np
import pandas as pd

COLS_SIAP = ["sembrada_ha", "cosechada_ha", "produccion_ton",
             "valor_produccion", "precio_rural_kg"]

COLS_PRECIO = ["precio_min", "precio_max", "precio_frec"]
GRUPO_SERIE = ["origen_estado", "presentacion", "destino_mercado"]


# ---------------------------------------------------------------------
# Paso 2: valores faltantes
# ---------------------------------------------------------------------
def diagnostico_faltantes(df):
    print("Porcentaje de nulos por columna:")
    print((df.isna().mean() * 100).round(1).to_string())

    tmp = df.assign(falta_siap=df["produccion_ton"].isna())
    print("\nFilas con SIAP faltante, por año:")
    print(tmp.groupby("anio")["falta_siap"].agg(["sum", "count", "mean"]).to_string())
    print("\nFilas con SIAP faltante, por estado:")
    print(tmp.groupby("estado")["falta_siap"].agg(["sum", "count", "mean"]).to_string())


def imputar_faltantes(df, siap_anual):
    """Imputa las columnas SIAP con el último año publicado de cada estado.

    Solo se imputan filas de años POSTERIORES al último dato disponible del
    estado (rezago de publicación). Cada fila imputada queda marcada.
    """
    df = df.copy()

    validos = siap_anual.dropna(subset=["produccion_ton"])
    ultimo = (validos.sort_values("anio")
              .groupby("estado").tail(1)
              .set_index("estado"))

    ultimo_anio = df["estado"].map(ultimo["anio"]).astype(float)
    puede_imputar = (df["produccion_ton"].isna()
                     & (df["anio"].astype(float) > ultimo_anio)
                     ).fillna(False).astype(bool)

    df["anio_dato_siap"] = df["anio"].astype(float).where(df["produccion_ton"].notna())
    df.loc[puede_imputar, "anio_dato_siap"] = ultimo_anio[puede_imputar]

    for c in COLS_SIAP:
        df.loc[puede_imputar, c] = df.loc[puede_imputar, "estado"].map(ultimo[c])

    df["siap_imputado"] = puede_imputar
    df["anio_dato_siap"] = df["anio_dato_siap"].astype("Int64")

    print("\nFilas imputadas:", int(puede_imputar.sum()))
    if puede_imputar.any():
        print("Año de origen del dato imputado, por estado:")
        print(df[puede_imputar]
              .groupby("estado")["anio_dato_siap"]
              .agg(["min", "max", "count"]).to_string())
    print("\nNulos restantes tras imputar:")
    print(df[COLS_SIAP].isna().sum().to_string())
    return df


# ---------------------------------------------------------------------
# Paso 3: atípicos y ruido
# ---------------------------------------------------------------------
def _hampel(serie, ventana=15, umbral=3.5, rel_min=0.10, tol_plana=0.30):
    """Z-Score robusto sobre mediana móvil. Devuelve (bandera, mediana_local)."""
    med = serie.rolling(ventana, center=True, min_periods=5).median()
    mad = (serie - med).abs().rolling(ventana, center=True, min_periods=5).median()
    desv = serie - med
    rel = desv.abs() / med

    z = 0.6745 * desv / mad.where(mad > 0)          # MAD = 0 -> z indefinido
    atip_z = (z.abs() > umbral) & (rel > rel_min)
    atip_plana = (mad == 0) & (rel > tol_plana)     # serie plana con salto grande
    return (atip_z | atip_plana).fillna(False), med


def tratar_atipicos(sniim_d, ventana=15, umbral=3.5):
    """Marca atípicos (Hampel) y crea columnas *_corr con la mediana móvil.

    No borra nada: los valores originales se conservan.
    """
    d = sniim_d.sort_values(GRUPO_SERIE + ["fecha"]).copy()
    d["es_atipico"] = False
    for c in COLS_PRECIO:
        d[f"{c}_corr"] = d[c]

    # Incoherencias: son errores, no atípicos (irán a cuarentena en la Puerta de Calidad)
    d["precio_incoherente"] = (
        (d["precio_min"] > d["precio_frec"])
        | (d["precio_frec"] > d["precio_max"])
        | (d[COLS_PRECIO] <= 0).any(axis=1)
    )

    base = d[~d["es_duplicado"]]
    for _, idx in base.groupby(GRUPO_SERIE, dropna=False).groups.items():
        sub = d.loc[idx]
        for c in COLS_PRECIO:
            flag, med = _hampel(sub[c], ventana, umbral)
            malos = flag[flag].index
            d.loc[malos, f"{c}_corr"] = med.loc[malos]
            d.loc[malos, "es_atipico"] = True

    n_base = int((~d["es_duplicado"]).sum())
    n_atip = int(d["es_atipico"].sum())
    print(f"  Atípicos (Hampel, ventana={ventana}, umbral={umbral}): "
          f"{n_atip} de {n_base} registros no duplicados ({n_atip / n_base:.1%})")
    if n_atip:
        print(d[d["es_atipico"]].groupby("origen_estado").size().to_string())
    print(f"  Registros incoherentes (min > frec, frec > max o precio <= 0): "
          f"{int(d['precio_incoherente'].sum())}")
    return d.reset_index(drop=True)


def marcar_atipicos_iqr(df, col, k=1.5):
    """IQR sobre una columna del SIAP. Solo informativo: marca, no corrige."""
    df = df.copy()
    base = df[col].where(df["cosechada_ha"] > 0)
    base = base.where(base > 0)
    q1, q3 = base.quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - k * iqr, q3 + k * iqr
    df[f"{col}_atipico"] = ((base < lo) | (base > hi)).fillna(False)
    print(f"\n  IQR sobre {col}: límites [{lo:.2f}, {hi:.2f}], "
          f"{int(df[f'{col}_atipico'].sum())} de {int(base.notna().sum())} filas marcadas")
    return df

    # ---------------------------------------------------------------------
# Paso 4: normalización (Min-Max) y estandarización (Z-Score)
# ---------------------------------------------------------------------
COLS_NORM_MENSUAL = ["precio_frec_media", "precio_min", "precio_max"]
COLS_NORM_ANUAL = ["sembrada_ha", "cosechada_ha", "produccion_ton",
                   "valor_produccion", "precio_rural_kg"]


def normalizar(df):
    """Crea columnas *_minmax y *_z. Los originales se conservan.

    Las variables SIAP son anuales y están repetidas en 12 meses (e imputadas
    en 2026): sus estadísticos se calculan sobre filas únicas estado-año y sin
    imputar, para no darle más peso a unos años que a otros.
    """
    df = df.copy()
    anual = df[~df["siap_imputado"]].drop_duplicates(["estado", "anio"])

    for c in COLS_NORM_MENSUAL + COLS_NORM_ANUAL:
        base = df[c] if c in COLS_NORM_MENSUAL else anual[c]
        mn, mx = base.min(), base.max()
        mu, sd = base.mean(), base.std(ddof=0)
        df[f"{c}_minmax"] = (df[c] - mn) / (mx - mn) if mx > mn else 0.0
        df[f"{c}_z"] = (df[c] - mu) / sd if sd > 0 else 0.0

    print("\n  Normalización aplicada a:", COLS_NORM_MENSUAL + COLS_NORM_ANUAL)
    print(df[[f"{c}_z" for c in COLS_NORM_MENSUAL]].describe().loc[["mean", "std"]]
          .round(3).to_string())
    return df


# ---------------------------------------------------------------------
# Paso 5: discretización y jerarquías conceptuales
# ---------------------------------------------------------------------
# Agrupación propia por zona geográfica; ajústala si tu profesor usa otra
REGION_ESTADO = {
    "colima": "occidente",
    "michoacan": "occidente",
    "guerrero": "sur",
    "sinaloa": "noroeste",
    "yucatan": "sureste",
}


def discretizar(df):
    df = df.copy()

    # Jerarquía temporal: mes -> trimestre -> semestre -> año
    df["mes"] = df["anio_mes"].dt.month
    df["trimestre"] = df["anio_mes"].dt.quarter
    df["semestre"] = (df["mes"] - 1) // 6 + 1

    # Jerarquía geográfica: estado -> región -> país
    df["region"] = df["estado"].map(REGION_ESTADO)
    df["pais"] = "mexico"

    # Precio: dos métodos de discretización para compararlos
    etiquetas = ["bajo", "medio", "alto"]
    df["precio_nivel"] = pd.qcut(df["precio_frec_media"], q=3, labels=etiquetas)   # frecuencias iguales
    df["precio_rango"] = pd.cut(df["precio_frec_media"], bins=3, labels=etiquetas) # anchura igual

    # Producción: cortes por terciles de las filas únicas estado-año (sin imputar)
    anual = df[~df["siap_imputado"]].drop_duplicates(["estado", "anio"])
    cortes = np.unique(anual["produccion_ton"].quantile([0, 1/3, 2/3, 1]).to_numpy())
    etiq_prod = ["baja", "media", "alta"][: len(cortes) - 1]
    df["produccion_nivel"] = pd.cut(df["produccion_ton"], bins=cortes,
                                    labels=etiq_prod, include_lowest=True)

    print("\n  Discretización del precio (frecuencias iguales):")
    print(df["precio_nivel"].value_counts().to_string())
    print("  Discretización del precio (anchura igual):")
    print(df["precio_rango"].value_counts().to_string())
    print("  Nivel de producción:")
    print(df["produccion_nivel"].value_counts(dropna=False).to_string())
    return df


# ---------------------------------------------------------------------
# Paso 6: reducción de datos
# ---------------------------------------------------------------------
def reducir(df, siap_h, sniim_d, umbral_corr=0.95):
    """Agregación (ya aplicada) + selección de variables por correlación."""
    # 1) Reducción por agregación: cuánto se redujo cada fuente
    print("\n  Reducción por agregación:")
    print(f"   SNIIM: {len(sniim_d)} registros diarios -> "
          f"{int((~sniim_d['es_duplicado']).sum())} sin duplicados -> "
          f"{df[['anio_mes', 'estado']].drop_duplicates().shape[0]} filas mensuales por estado")
    print(f"   SIAP:  {len(siap_h)} filas municipales -> "
          f"{siap_h.groupby(['anio', 'estado']).ngroups} filas estado-año")

    # 2) Selección de variables: se elimina la que esté muy correlacionada
    #    con otra ya conservada (correlación calculada con las filas municipales)
    candidatas = ["produccion_ton", "sembrada_ha", "cosechada_ha", "valor_produccion"]
    corr = siap_h[candidatas].corr().abs()
    print("\n  Correlación absoluta entre variables SIAP:")
    print(corr.round(3).to_string())

    conservar, eliminadas = [], {}
    for c in candidatas:
        previo = next((k for k in conservar if corr.loc[c, k] > umbral_corr), None)
        if previo:
            eliminadas[c] = previo
        else:
            conservar.append(c)

    print(f"\n  Variables conservadas: {conservar}")
    for c, k in eliminadas.items():
        print(f"  Variable eliminada: {c} (correlación > {umbral_corr} con {k})")

    cols_borrar = [col for c in eliminadas
                   for col in (c, f"{c}_minmax", f"{c}_z") if col in df.columns]
                   
    return df.drop(columns=cols_borrar), eliminadas 