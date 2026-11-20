#!/usr/bin/env python3
"""Capa Oro: generación de tablas analíticas consolidadas, enriquecimiento
con variables predictivas y geoespaciales, y auditoría estricta de linaje
y trazabilidad Bronce -> Plata -> Oro.
"""
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from src.geoespacial import enriquecer_mercados_geoespacial
except ImportError:
    from geoespacial import enriquecer_mercados_geoespacial

RAIZ = Path(__file__).resolve().parent.parent
PLATA = RAIZ / "data" / "plata"
ORO = RAIZ / "data" / "oro"


def generar_id_registro(prefijo, clave):
    """Genera un hash determinista SHA-256 para identificar un registro en Oro."""
    texto = f"{prefijo}:{clave}".encode("utf-8")
    return hashlib.sha256(texto).hexdigest()


def construir_oro_mensual(integrado_df):
    """Construye la tabla analítica mensual (oro_serie_mensual_observatorio).

    Enriquece con retardos temporales (lags) y variaciones porcentuales requeridas
    para los modelos de pronóstico de la Etapa 2, conservando el linaje a Bronce.
    """
    df = integrado_df.copy().sort_values(["estado", "anio_mes"]).reset_index(drop=True)

    # Identificador único determinista de fila en Oro
    df["registro_id_oro"] = [
        generar_id_registro("oro_mensual", f"{r.estado}:{r.anio_mes:%Y-%m}")
        for r in df.itertuples()
    ]

    # Rezagos temporales (lags de 1, 2 y 3 meses por estado)
    df["precio_lag_1m"] = df.groupby("estado")["precio_frec_media"].shift(1)
    df["precio_lag_2m"] = df.groupby("estado")["precio_frec_media"].shift(2)
    df["precio_lag_3m"] = df.groupby("estado")["precio_frec_media"].shift(3)

    # Variación porcentual mensual e interanual
    df["var_mensual_precio_pct"] = (
        (df["precio_frec_media"] - df["precio_lag_1m"]) / df["precio_lag_1m"] * 100
    ).round(2)
    
    precio_lag_12m = df.groupby("estado")["precio_frec_media"].shift(12)
    df["var_interanual_precio_pct"] = (
        (df["precio_frec_media"] - precio_lag_12m) / precio_lag_12m * 100
    ).round(2)

    return df


def construir_oro_geoespacial(sniim_diario, siap_anual=None):
    """Construye la tabla analítica geoespacial de rutas y mercados.

    Calcula la distancia geodésica huerta -> central de abasto y el spread
    de precios entre origen y destino, conservando la trazabilidad a Bronce.
    """
    # Excluye cotizaciones duplicadas e incoherentes
    base = sniim_diario[~sniim_diario["es_duplicado"] & ~sniim_diario["precio_incoherente"]].copy()
    
    # Enriquecimiento geoespacial (coordenadas oficiales y Haversine)
    geo = enriquecer_mercados_geoespacial(base)

    # Agregación a nivel mensual por ruta de mercado
    rutas = (
        geo.groupby(["anio_mes", "anio", "origen_estado", "destino_mercado", "destino_estado"], as_index=False)
        .agg(
            precio_frec_media=("precio_frec_corr", "mean"),
            precio_min=("precio_min_corr", "min"),
            precio_max=("precio_max_corr", "max"),
            n_cotizaciones=("precio_frec_corr", "count"),
            origen_lat=("origen_lat", "first"),
            origen_lon=("origen_lon", "first"),
            origen_municipio=("origen_municipio", "first"),
            destino_lat=("destino_lat", "first"),
            destino_lon=("destino_lon", "first"),
            destino_ciudad=("destino_ciudad", "first"),
            distancia_transporte_km=("distancia_transporte_km", "first"),
            archivos_bronce_sniim=("archivo_origen", lambda s: "; ".join(sorted(set(s)))),
            fecha_ingesta_bronce=("fecha_ingesta_bronce", "max"),
            sha256_bronce_sniim=("sha256_bronce", lambda s: "; ".join(sorted(set(s)))),
        )
    )

    # Cruce con precio rural del SIAP si está disponible para calcular el margen comercial
    if siap_anual is not None:
        siap_sub = siap_anual[["anio", "estado", "precio_rural_kg"]].rename(columns={"estado": "origen_estado"})
        rutas = rutas.merge(siap_sub, on=["anio", "origen_estado"], how="left")
        rutas["spread_precio_kg"] = (rutas["precio_frec_media"] - rutas["precio_rural_kg"]).round(2)
        rutas["spread_por_1000km"] = (
            rutas["spread_precio_kg"] / (rutas["distancia_transporte_km"] / 1000.0)
        ).round(2)

    # Identificador único de fila en Oro
    rutas["registro_id_oro"] = [
        generar_id_registro("oro_geo", f"{r.origen_estado}:{r.destino_mercado}:{r.anio_mes:%Y-%m}")
        for r in rutas.itertuples()
    ]
    rutas["linaje_id"] = [
        hashlib.sha256(f"{r.registro_id_oro}:{r.sha256_bronce_sniim}".encode("utf-8")).hexdigest()
        for r in rutas.itertuples()
    ]

    return rutas


def construir_matriz_linaje(oro_mensual, oro_geoespacial, bitacoras):
    """Construye la matriz completa de linaje Bronce -> Plata -> Oro.

    Permite que cada registro de Oro sea auditado directamente hasta los
    archivos crudos de Bronce, su hash SHA-256 y su fecha de ingesta exacta.
    """
    filas_linaje = []

    # 1. Linaje de registros de oro_serie_mensual_observatorio
    for r in oro_mensual.itertuples():
        reg_id = r.registro_id_oro
        particion = f"{r.estado} | {r.anio_mes:%Y-%m}"
        
        # SNIIM
        sniim_archs = [a.strip() for a in str(r.archivos_bronce_sniim).split(";") if a.strip()]
        for arch in sniim_archs:
            info = bitacoras.get("sniim", {}).get(arch, {})
            filas_linaje.append({
                "tabla_oro": "oro_serie_mensual_observatorio",
                "registro_id_oro": reg_id,
                "clave_particion": particion,
                "capa_plata_fuente": "integrado_reducido_validado.parquet",
                "fuente_bronce": "sniim",
                "archivo_bronce": arch,
                "sha256_bronce": info.get("sha256", ""),
                "fecha_ingesta_bronce": r.fecha_ingesta_sniim,
                "tipo_transformacion": "hampel_atipicos -> agregacion_mensual -> fusion",
            })
            
        # SIAP
        siap_arch = str(r.archivo_bronce_siap)
        info_siap = bitacoras.get("siap", {}).get(siap_arch, {})
        filas_linaje.append({
            "tabla_oro": "oro_serie_mensual_observatorio",
            "registro_id_oro": reg_id,
            "clave_particion": particion,
            "capa_plata_fuente": "integrado_reducido_validado.parquet",
            "fuente_bronce": "siap",
            "archivo_bronce": siap_arch,
            "sha256_bronce": info_siap.get("sha256", ""),
            "fecha_ingesta_bronce": r.fecha_ingesta_siap,
            "tipo_transformacion": "filtro_cultivo -> suma_estatal -> imputacion_mar" if r.siap_imputado else "filtro_cultivo -> suma_estatal",
        })

        # Clima
        clima_arch = str(r.archivo_bronce_clima)
        info_clima = bitacoras.get("clima", {}).get(clima_arch, {})
        filas_linaje.append({
            "tabla_oro": "oro_serie_mensual_observatorio",
            "registro_id_oro": reg_id,
            "clave_particion": particion,
            "capa_plata_fuente": "integrado_reducido_validado.parquet",
            "fuente_bronce": "clima_open_meteo",
            "archivo_bronce": clima_arch,
            "sha256_bronce": info_clima.get("sha256", ""),
            "fecha_ingesta_bronce": r.fecha_ingesta_clima,
            "tipo_transformacion": "json_parse -> promedio_mensual -> fusion",
        })

    # 2. Linaje de registros de oro_mercados_geoespacial
    for r in oro_geoespacial.itertuples():
        reg_id = r.registro_id_oro
        particion = f"{r.origen_estado} -> {r.destino_mercado} | {r.anio_mes:%Y-%m}"
        archs = [a.strip() for a in str(r.archivos_bronce_sniim).split(";") if a.strip()]
        for arch in archs:
            info = bitacoras.get("sniim", {}).get(arch, {})
            filas_linaje.append({
                "tabla_oro": "oro_mercados_geoespacial",
                "registro_id_oro": reg_id,
                "clave_particion": particion,
                "capa_plata_fuente": "sniim_diario_validado.parquet",
                "fuente_bronce": "sniim",
                "archivo_bronce": arch,
                "sha256_bronce": info.get("sha256", ""),
                "fecha_ingesta_bronce": r.fecha_ingesta_bronce,
                "tipo_transformacion": "haversine_distancia -> agregacion_mercado_mes",
            })

    matriz = pd.DataFrame(filas_linaje)
    return matriz


def rastrear_linaje_registro(registro_id_oro, ruta_matriz=None):
    """Herramienta de auditoría: recupera los orígenes en Bronce de un registro de Oro."""
    if ruta_matriz is None:
        ruta_matriz = ORO / "oro_linaje_matriz.parquet"
    matriz = pd.read_parquet(ruta_matriz)
    resultado = matriz[matriz["registro_id_oro"] == registro_id_oro]
    return resultado


def verificar_conservacion_fechas_ingesta(oro_mensual, bitacoras):
    """Comprueba formalmente que ninguna fecha de ingesta en Oro fue alterada o perdida."""
    discrepancias = 0
    total_revisados = 0

    for r in oro_mensual.itertuples():
        # Verificar clima
        arch_clima = str(r.archivo_bronce_clima)
        if arch_clima in bitacoras.get("clima", {}):
            fecha_esperada = bitacoras["clima"][arch_clima]["fecha_captura_utc"]
            if r.fecha_ingesta_clima != fecha_esperada:
                discrepancias += 1
            total_revisados += 1
            
        # Verificar siap
        arch_siap = str(r.archivo_bronce_siap)
        if arch_siap in bitacoras.get("siap", {}):
            fecha_esperada = bitacoras["siap"][arch_siap]["fecha_captura_utc"]
            if r.fecha_ingesta_siap != fecha_esperada:
                discrepancias += 1
            total_revisados += 1

    return total_revisados, discrepancias
