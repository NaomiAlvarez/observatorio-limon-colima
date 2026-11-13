import unicodedata
from io import StringIO
from pathlib import Path
from limpieza import tratar_atipicos
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------
EQUIVALENCIAS_ESTADO = {
    "michoacan de ocampo": "michoacan",
    "veracruz de ignacio de la llave": "veracruz",
    "coahuila de zaragoza": "coahuila",
}

# Nombres posibles de cada columna del SIAP (normalizados: minúsculas, sin acentos)
ALIAS_SIAP = {
    "anio":               ["anio", "ano", "year"],
    "nomestado":          ["nomestado", "estado", "entidad"],
    "nommunicipio":       ["nommunicipio", "municipio"],
    "nomcultivo":         ["nomcultivo", "nomcultivo_sin_um", "cultivo"],
    "nommodalidad":       ["nommodalidad", "modalidad"],
    "nomcicloproductivo": ["nomcicloproductivo", "ciclo", "nomciclo"],
    "sembrada":           ["sembrada"],
    "cosechada":          ["cosechada"],
    "siniestrada":        ["siniestrada"],
    "volumenproduccion":  ["volumenproduccion", "volumen_produccion", "produccion"],
    "rendimiento":        ["rendimiento"],
    "precio":             ["precio", "pmr"],
    "valorproduccion":    ["valorproduccion", "valor_produccion"],
}
OBLIGATORIAS_SIAP = ["anio", "nomestado", "nomcultivo", "volumenproduccion"]

# Cultivos que sí cuentan como limón (nombres normalizados)
CULTIVOS_LIMON = {"limon", "limon real"}

# ---------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------
def limpiar_texto(s):
    """Minúsculas, sin acentos, sin espacios sobrantes."""
    if pd.isna(s):
        return s
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.strip().lower()


def _nombre_col(c):
    return limpiar_texto(c).replace(" ", "_").replace(".", "")


def _leer_texto(ruta):
    crudo = Path(ruta).read_bytes()
    for enc in ("utf-8", "latin-1"):
        try:
            return crudo.decode(enc)
        except UnicodeDecodeError:
            continue


def _a_numero(serie):
    return pd.to_numeric(serie, errors="coerce")


# ---------------------------------------------------------------------
# SNIIM (HTML)
# ---------------------------------------------------------------------
def _tabla_sniim(ruta):
    """Devuelve la tabla de precios de un HTML del SNIIM, o None."""
    try:
        tablas = pd.read_html(StringIO(_leer_texto(ruta)))
    except ValueError:
        return None
    for t in tablas:
        if t.shape[1] >= 7 and str(t.iloc[0, 0]).strip().lower() == "fecha":
            df = t.iloc[1:].copy()
            df.columns = [_nombre_col(c) for c in t.iloc[0]]
            return df
    return None


def leer_sniim(carpeta):
    carpeta = Path(carpeta)
    htmls = sorted(carpeta.rglob("*.html"))
    if not htmls:
        raise FileNotFoundError(f"No hay HTML en {carpeta}")

    frames, sin_tabla = [], []
    for h in htmls:
        df = _tabla_sniim(h)
        if df is None or df.empty:
            sin_tabla.append(h.name)
            continue
        df["producto"] = h.parent.name
        df["archivo_origen"] = h.name
        frames.append(df)

    print(f"  SNIIM: {len(frames)} HTML con datos, {len(sin_tabla)} sin tabla")
    if sin_tabla:
        print("   Sin tabla:", sin_tabla)
    return pd.concat(frames, ignore_index=True)


def homologar_sniim(df):
    # Filas separadoras ("Frutas" en todas las celdas): son estructura, no datos
    es_separador = df["fecha"].map(limpiar_texto).eq("frutas")
    print(f"  SNIIM: {es_separador.sum()} filas separadoras descartadas")
    df = df[~es_separador]

    out = pd.DataFrame(index=df.index)
    out["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    out["anio"] = out["fecha"].dt.year.astype("Int64")
    out["anio_mes"] = out["fecha"].dt.to_period("M").dt.to_timestamp()
    out["producto"] = df["producto"]
    out["presentacion"] = df["presentacion"].map(limpiar_texto)
    out["origen_estado"] = df["origen"].map(limpiar_texto).replace(EQUIVALENCIAS_ESTADO)
    out["destino_mercado"] = df["destino"].astype(str).str.strip()
    out["destino_estado"] = (df["destino"].astype(str).str.split(":").str[0]
                             .map(limpiar_texto))
    for c in ("precio_min", "precio_max", "precio_frec"):
        out[c] = _a_numero(df[c])
    out["archivo_origen"] = df["archivo_origen"]
    out = out.reset_index(drop=True)
    claves = ["fecha", "presentacion", "origen_estado", "destino_mercado"]
    out["es_duplicado"] = out.duplicated(subset=claves, keep="first")
    print(f"  SNIIM: {out['es_duplicado'].sum()} registros duplicados marcados "
          f"(de {len(out)})")
    return out

# ---------------------------------------------------------------------
# SIAP (CSV comprimido)
# ---------------------------------------------------------------------
def _estandarizar_siap(df, nombre_archivo):
    df = df.copy()
    df.columns = [_nombre_col(c) for c in df.columns]

    renombres = {}
    for canonico, alias in ALIAS_SIAP.items():
        # 1) coincidencia exacta con algún alias
        encontrado = next((a for a in alias if a in df.columns), None)
        # 2) si no, una columna que empiece con el nombre canónico
        if encontrado is None:
            encontrado = next(
                (c for c in df.columns
                 if c.startswith(canonico) and c not in renombres), None)
            if encontrado is not None and canonico in OBLIGATORIAS_SIAP:
                print(f"   Aviso: {nombre_archivo}: '{encontrado}' tratada como '{canonico}'")
        if encontrado is not None:
            renombres[encontrado] = canonico
    df = df.rename(columns=renombres)

    faltan = [c for c in OBLIGATORIAS_SIAP if c not in df.columns]
    if faltan:
        raise KeyError(
            f"{nombre_archivo}: faltan columnas {faltan}. "
            f"Columnas del archivo: {list(df.columns)}"
        )

    # Las opcionales que no vengan se crean vacías (quedan como NaN)
    for canonico in ALIAS_SIAP:
        if canonico not in df.columns:
            df[canonico] = pd.NA
    return df[list(ALIAS_SIAP)]

def leer_siap(carpeta):
    carpeta = Path(carpeta)
    archivos = sorted(carpeta.rglob("*.csv.gz"))
    if not archivos:
        raise FileNotFoundError(f"No hay .csv.gz en {carpeta}")

    frames = []
    for a in archivos:
        df = None
        for enc in ("utf-8-sig", "latin-1"):   # utf-8-sig también quita el BOM
            try:
                df = pd.read_csv(a, compression="gzip", encoding=enc,
                                 low_memory=False)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise ValueError(f"No se pudo leer {a}")

        df = _estandarizar_siap(df, a.name)
        es_limon = df["nomcultivo"].map(limpiar_texto).isin(CULTIVOS_LIMON)
        df = df[es_limon].copy()
        df["archivo_origen"] = a.name
        frames.append(df)

    siap = pd.concat(frames, ignore_index=True)
    print(f"  SIAP: {len(archivos)} archivos, {len(siap)} filas de limón")
    print("   Cultivos incluidos:", sorted(siap["nomcultivo"].unique()))
    return siap


def homologar_siap(df):
    out = pd.DataFrame(index=df.index)
    out["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    out["estado"] = df["nomestado"].map(limpiar_texto).replace(EQUIVALENCIAS_ESTADO)
    out["municipio"] = df["nommunicipio"].map(limpiar_texto)
    out["cultivo"] = df["nomcultivo"].map(limpiar_texto)
    out["modalidad"] = df["nommodalidad"].map(limpiar_texto)
    out["ciclo"] = df["nomcicloproductivo"].map(limpiar_texto)
    for origen, destino in [("sembrada", "sembrada_ha"),
                            ("cosechada", "cosechada_ha"),
                            ("siniestrada", "siniestrada_ha"),
                            ("volumenproduccion", "produccion_ton"),
                            ("rendimiento", "rendimiento_ton_ha"),
                            ("precio", "precio_rural_ton"),
                            ("valorproduccion", "valor_produccion")]:
        out[destino] = _a_numero(df[origen])
    out["archivo_origen"] = df["archivo_origen"]
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------
# Agregación y fusión
# ---------------------------------------------------------------------
def agregar_sniim_mensual(sniim_d):
    sniim_d = sniim_d[~sniim_d["es_duplicado"]]
    return (sniim_d
            .groupby(["anio_mes", "anio", "origen_estado"],
                     as_index=False, dropna=False)
            .agg(precio_frec_media=("precio_frec_corr", "mean"),
                 precio_min=("precio_min_corr", "min"),
                 precio_max=("precio_max_corr", "max"),
                 n_cotizaciones=("precio_frec_corr", "count"),
                 n_atipicos=("es_atipico", "sum"))
            .rename(columns={"origen_estado": "estado"}))

def agregar_siap_anual(siap_h):
    anual = (siap_h
             .groupby(["anio", "estado"], as_index=False)
             .agg(sembrada_ha=("sembrada_ha", "sum"),
                  cosechada_ha=("cosechada_ha", "sum"),
                  produccion_ton=("produccion_ton", "sum"),
                  valor_produccion=("valor_produccion", "sum")))
    anual["precio_rural_kg"] = (anual["valor_produccion"]
                                / anual["produccion_ton"] / 1000)
    anual["precio_rural_kg"] = anual["precio_rural_kg"].replace(
        [np.inf, -np.inf], np.nan)
    return anual


def fusionar(sniim_mes, siap_anual):
    """SNIIM (precio mensual) es la base; se le une la producción anual del SIAP."""
    integrado = sniim_mes.merge(
        siap_anual, on=["anio", "estado"],
        how="left", indicator=True, validate="many_to_one",
    )
    print("\nResultado del cruce (filas mensuales SNIIM):")
    print(integrado["_merge"].value_counts().to_string())

    sin_cruce = (integrado.loc[integrado["_merge"] == "left_only",
                               ["anio", "estado"]]
                 .drop_duplicates().sort_values(["estado", "anio"]))
    if not sin_cruce.empty:
        print("\nCombinaciones año-estado SIN producción SIAP:")
        print(sin_cruce.to_string(index=False))

    # Cambia la columna técnica _merge por una bandera con significado
    integrado["en_siap"] = integrado["_merge"].eq("both")
    integrado = integrado.drop(columns="_merge")

    return integrado

def integrar(carpeta_sniim, carpeta_siap):
    print("Leyendo fuentes...")
    sniim_raw = leer_sniim(carpeta_sniim)
    siap_raw = leer_siap(carpeta_siap)

    print("\nHomologando...")
    sniim_d = homologar_sniim(sniim_raw)
    siap_h = homologar_siap(siap_raw)

    print("\nValores únicos de origen_estado (SNIIM):")
    print(sorted(sniim_d["origen_estado"].dropna().unique()))

    print("\nTratamiento de atípicos (SNIIM diario)...")
    sniim_d = tratar_atipicos(sniim_d)

    sniim_mes = agregar_sniim_mensual(sniim_d)
    siap_anual = agregar_siap_anual(siap_h)
    integrado = fusionar(sniim_mes, siap_anual)
    
    return integrado, sniim_d, siap_h