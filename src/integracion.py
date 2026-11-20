import csv
import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.geoespacial import parsear_json_clima
    from src.limpieza import tratar_atipicos
except ImportError:
    from geoespacial import parsear_json_clima
    from limpieza import tratar_atipicos

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


def cargar_bitacora(carpeta_o_archivo):
    """Carga la bitácora de capturas crudas para obtener fecha de ingesta y SHA-256."""
    ruta = Path(carpeta_o_archivo)
    if ruta.is_dir():
        ruta = ruta / "_bitacora.csv"
    
    registros = {}
    if ruta.exists():
        with open(ruta, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = Path(row["archivo"]).name
                registros[nombre] = {
                    "fecha_captura_utc": row.get("fecha_captura_utc", ""),
                    "sha256": row.get("sha256", ""),
                }
    return registros


def _info_archivo_bronce(archivo, bitacora):
    """Obtiene fecha de captura UTC y hash SHA-256 de un archivo crudo de Bronce."""
    archivo = Path(archivo)
    nombre = archivo.name
    if nombre in bitacora:
        return bitacora[nombre]["fecha_captura_utc"], bitacora[nombre]["sha256"]

    # Fallback si no está en _bitacora.csv: consultar sidecar .metadata.json
    sidecar = archivo.with_name(f"{nombre}.metadata.json")
    sha256 = ""
    if sidecar.exists():
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            sha256 = data.get("sha256", "")
        except Exception:
            pass
    
    fecha_mtime = datetime.fromtimestamp(archivo.stat().st_mtime, tz=timezone.utc).isoformat()
    return fecha_mtime, sha256


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
        df["_ruta_archivo"] = str(h)
        frames.append(df)

    print(f"  SNIIM: {len(frames)} HTML con datos, {len(sin_tabla)} sin tabla")
    if sin_tabla:
        print("   Sin tabla:", sin_tabla)
    return pd.concat(frames, ignore_index=True)


def homologar_sniim(df, bitacora=None):
    if bitacora is None:
        bitacora = {}

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

    # Linaje y trazabilidad directa a Bronce
    info_bronce = df["archivo_origen"].map(lambda a: bitacora.get(a, {}))
    out["fecha_ingesta_bronce"] = info_bronce.map(lambda d: d.get("fecha_captura_utc", ""))
    out["sha256_bronce"] = info_bronce.map(lambda d: d.get("sha256", ""))

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
        encontrado = next((a for a in alias if a in df.columns), None)
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
        for enc in ("utf-8-sig", "latin-1"):
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


def homologar_siap(df, bitacora=None):
    if bitacora is None:
        bitacora = {}

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

    # Linaje y trazabilidad directa a Bronce
    info_bronce = df["archivo_origen"].map(lambda a: bitacora.get(a, {}))
    out["fecha_ingesta_bronce"] = info_bronce.map(lambda d: d.get("fecha_captura_utc", ""))
    out["sha256_bronce"] = info_bronce.map(lambda d: d.get("sha256", ""))

    return out.reset_index(drop=True)


# ---------------------------------------------------------------------
# Clima / Geoespacial (JSON de Open-Meteo)
# ---------------------------------------------------------------------
def leer_clima(carpeta, bitacora=None):
    """Lee y homologa los datos agroclimáticos crudos de Bronce."""
    if bitacora is None:
        bitacora = {}

    carpeta = Path(carpeta)
    archivos = sorted([p for p in carpeta.glob("*.json") if not p.name.endswith(".metadata.json")])
    if not archivos:
        print(f"  Aviso: No se encontraron archivos de clima en {carpeta}")
        return pd.DataFrame()

    frames = []
    for a in archivos:
        estado = a.name.split("_")[0]
        df = parsear_json_clima(a, estado)
        
        # Linaje
        info = bitacora.get(a.name, {})
        df["fecha_ingesta_bronce"] = info.get("fecha_captura_utc", "")
        df["sha256_bronce"] = info.get("sha256", "")
        frames.append(df)

    clima_d = pd.concat(frames, ignore_index=True)
    print(f"  Clima: {len(archivos)} archivos JSON, {len(clima_d)} días procesados")
    return clima_d


def agregar_clima_mensual(clima_d):
    """Agrega variables agroclimáticas a promedio y acumulado mensual por estado."""
    if clima_d is None or clima_d.empty:
        return pd.DataFrame()

    mensual = (
        clima_d.groupby(["anio_mes", "anio", "estado"], as_index=False)
        .agg(
            temp_media_c=("temp_media_c", "mean"),
            temp_min_c=("temp_min_c", "min"),
            temp_max_c=("temp_max_c", "max"),
            precipitacion_mm=("precipitacion_mm", "sum"),
            archivo_bronce_clima=("archivo_origen", "first"),
            fecha_ingesta_clima=("fecha_ingesta_bronce", "first"),
            sha256_bronce_clima=("sha256_bronce", "first"),
        )
    )
    mensual["temp_media_c"] = mensual["temp_media_c"].round(2)
    mensual["temp_min_c"] = mensual["temp_min_c"].round(2)
    mensual["temp_max_c"] = mensual["temp_max_c"].round(2)
    mensual["precipitacion_mm"] = mensual["precipitacion_mm"].round(2)
    return mensual


# ---------------------------------------------------------------------
# Agregación y fusión
# ---------------------------------------------------------------------
def agregar_sniim_mensual(sniim_d):
    sniim_d = sniim_d[~sniim_d["es_duplicado"] & ~sniim_d["precio_incoherente"]]
    return (sniim_d
            .groupby(["anio_mes", "anio", "origen_estado"],
                     as_index=False, dropna=False)
            .agg(
                precio_frec_media=("precio_frec_corr", "mean"),
                precio_min=("precio_min_corr", "min"),
                precio_max=("precio_max_corr", "max"),
                n_cotizaciones=("precio_frec_corr", "count"),
                n_atipicos=("es_atipico", "sum"),
                archivos_bronce_sniim=("archivo_origen", lambda s: "; ".join(sorted(set(s)))),
                fecha_ingesta_sniim=("fecha_ingesta_bronce", "max"),
                sha256_bronce_sniim=("sha256_bronce", lambda s: "; ".join(sorted(set(s)))),
            )
            .rename(columns={"origen_estado": "estado"}))


def agregar_siap_anual(siap_h):
    anual = (siap_h
             .groupby(["anio", "estado"], as_index=False)
             .agg(
                 sembrada_ha=("sembrada_ha", "sum"),
                 cosechada_ha=("cosechada_ha", "sum"),
                 produccion_ton=("produccion_ton", "sum"),
                 valor_produccion=("valor_produccion", "sum"),
                 archivo_bronce_siap=("archivo_origen", "first"),
                 fecha_ingesta_siap=("fecha_ingesta_bronce", "first"),
                 sha256_bronce_siap=("sha256_bronce", "first"),
             ))
    anual["precio_rural_kg"] = (anual["valor_produccion"]
                                / anual["produccion_ton"] / 1000)
    anual["precio_rural_kg"] = anual["precio_rural_kg"].replace(
        [np.inf, -np.inf], np.nan)
    return anual


def fusionar(sniim_mes, siap_anual, clima_mes=None):
    """SNIIM (precio mensual) es la base; se une producción anual SIAP y clima mensual."""
    integrado = sniim_mes.merge(
        siap_anual, on=["anio", "estado"],
        how="left", indicator=True, validate="many_to_one",
    )
    print("\nResultado del cruce SNIIM + SIAP:")
    print(integrado["_merge"].value_counts().to_string())

    integrado["en_siap"] = integrado["_merge"].eq("both")
    integrado = integrado.drop(columns="_merge")

    # Integración de la fuente agroclimática geoespacial
    if clima_mes is not None and not clima_mes.empty:
        integrado = integrado.merge(clima_mes, on=["anio_mes", "anio", "estado"], how="left")
        print("  Clima mensual integrado a las observaciones mensuales.")

    # Trazabilidad consolidada y linaje determinista
    fechas_ingesta = []
    linajes = []
    for r in integrado.itertuples():
        # Fechas de ingesta conservadas
        fechas = [
            getattr(r, "fecha_ingesta_sniim", ""),
            getattr(r, "fecha_ingesta_siap", ""),
            getattr(r, "fecha_ingesta_clima", ""),
        ]
        fechas_validas = [f for f in fechas if f and pd.notna(f)]
        fechas_ingesta.append(max(fechas_validas) if fechas_validas else "")
        
        # Hash compuesto de linaje
        hash_componentes = (
            f"{r.estado}:{r.anio_mes}:{getattr(r, 'sha256_bronce_sniim', '')}:"
            f"{getattr(r, 'sha256_bronce_siap', '')}:{getattr(r, 'sha256_bronce_clima', '')}"
        )
        linajes.append(hashlib.sha256(hash_componentes.encode("utf-8")).hexdigest())

    integrado["fecha_ingesta_reciente_bronce"] = fechas_ingesta
    integrado["linaje_id"] = linajes

    return integrado


def integrar(carpeta_sniim, carpeta_siap, carpeta_clima=None):
    print("Leyendo fuentes crudas de Bronce...")
    bitacora_sniim = cargar_bitacora(carpeta_sniim)
    bitacora_siap = cargar_bitacora(carpeta_siap)
    bitacora_clima = cargar_bitacora(carpeta_clima) if carpeta_clima else {}

    bitacoras = {
        "sniim": bitacora_sniim,
        "siap": bitacora_siap,
        "clima": bitacora_clima,
    }

    # Completar archivos que tengan sidecars si faltaran en _bitacora.csv
    for p in Path(carpeta_sniim).rglob("*.html"):
        if p.name not in bitacora_sniim:
            f, h = _info_archivo_bronce(p, bitacora_sniim)
            bitacora_sniim[p.name] = {"fecha_captura_utc": f, "sha256": h}

    sniim_raw = leer_sniim(carpeta_sniim)
    siap_raw = leer_siap(carpeta_siap)
    clima_d = leer_clima(carpeta_clima, bitacora_clima) if carpeta_clima else pd.DataFrame()

    print("\nHomologando con linaje y trazabilidad...")
    sniim_d = homologar_sniim(sniim_raw, bitacora_sniim)
    siap_h = homologar_siap(siap_raw, bitacora_siap)

    print("\nTratamiento de atípicos (SNIIM diario)...")
    sniim_d = tratar_atipicos(sniim_d)

    sniim_mes = agregar_sniim_mensual(sniim_d)
    siap_anual = agregar_siap_anual(siap_h)
    clima_mes = agregar_clima_mensual(clima_d) if not clima_d.empty else None

    integrado = fusionar(sniim_mes, siap_anual, clima_mes)
    
    return integrado, sniim_d, siap_h, clima_d, bitacoras
