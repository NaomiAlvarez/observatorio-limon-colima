#!/usr/bin/env python3
"""Módulo Geoespacial y Agroclimático.

Proporciona catálogos de georreferenciación oficial para los centros de
producción (orígenes) y centrales de abasto (destinos) de limón con semilla,
funciones de cálculo geodésico (distancia Haversine en kilómetros) y
transformaciones de series agroclimáticas.
"""
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
import json
import numpy as np
import pandas as pd

# Catálogo Geoespacial de Zonas Citrícolas Productoras (Orígenes SNIIM y SIAP)
COORDENADAS_ORIGEN = {
    "colima": {
        "municipio": "tecoman",
        "cve_ent": "06",
        "cve_mun": "06009",
        "lat": 18.913,
        "lon": -103.874,
        "altitud_msnm": 33,
    },
    "michoacan": {
        "municipio": "apatzingan",
        "cve_ent": "16",
        "cve_mun": "16006",
        "lat": 19.088,
        "lon": -102.354,
        "altitud_msnm": 325,
    },
    "guerrero": {
        "municipio": "juan_r_escudero",
        "cve_ent": "12",
        "cve_mun": "12039",
        "lat": 17.165,
        "lon": -99.530,
        "altitud_msnm": 270,
    },
    "sinaloa": {
        "municipio": "el_rosario",
        "cve_ent": "25",
        "cve_mun": "25014",
        "lat": 22.991,
        "lon": -105.859,
        "altitud_msnm": 40,
    },
    "yucatan": {
        "municipio": "oxkutzcab",
        "cve_ent": "31",
        "cve_mun": "31056",
        "lat": 20.306,
        "lon": -89.418,
        "altitud_msnm": 32,
    },
}

# Catálogo Geoespacial de Centrales de Abasto y Mercados Mayoristas (Destinos SNIIM)
COORDENADAS_DESTINO = {
    "Sonora: Central de Abasto de Cd. Obregón": {
        "ciudad": "ciudad_obregon",
        "cve_ent": "26",
        "lat": 27.486,
        "lon": -109.940,
        "estado": "sonora",
    },
    "Guerrero: Central de Abastos de Acapulco": {
        "ciudad": "acapulco",
        "cve_ent": "12",
        "lat": 16.883,
        "lon": -99.850,
        "estado": "guerrero",
    },
    "DF: Central de Abasto de Iztapalapa DF": {
        "ciudad": "ciudad_de_mexico",
        "cve_ent": "09",
        "lat": 19.371,
        "lon": -99.092,
        "estado": "distrito_federal",
    },
    "México: Central de Abasto de Ecatepec": {
        "ciudad": "ecatepec",
        "cve_ent": "15",
        "lat": 19.601,
        "lon": -99.030,
        "estado": "mexico",
    },
    "Puebla: Central de Abasto de Puebla": {
        "ciudad": "puebla",
        "cve_ent": "21",
        "lat": 19.092,
        "lon": -98.188,
        "estado": "puebla",
    },
    "Yucatán: Centro Mayorista Oxkutzcab": {
        "ciudad": "oxkutzcab",
        "cve_ent": "31",
        "lat": 20.308,
        "lon": -89.418,
        "estado": "yucatan",
    },
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Calcula la distancia geodésica en kilómetros entre dos coordenadas (Haversine)."""
    if any(pd.isna([lat1, lon1, lat2, lon2])):
        return np.nan
    # Convertir grados a radianes
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # Fórmula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    radio_tierra_km = 6371.0
    return round(c * radio_tierra_km, 2)


def enriquecer_mercados_geoespacial(df_sniim):
    """Enriquece cotizaciones del SNIIM con coordenadas y distancia de transporte."""
    df = df_sniim.copy()
    
    # Coordenadas de origen
    df["origen_lat"] = df["origen_estado"].map(
        lambda e: COORDENADAS_ORIGEN.get(e, {}).get("lat", np.nan)
    )
    df["origen_lon"] = df["origen_estado"].map(
        lambda e: COORDENADAS_ORIGEN.get(e, {}).get("lon", np.nan)
    )
    df["origen_municipio"] = df["origen_estado"].map(
        lambda e: COORDENADAS_ORIGEN.get(e, {}).get("municipio", "")
    )
    
    # Coordenadas de destino
    df["destino_lat"] = df["destino_mercado"].map(
        lambda m: COORDENADAS_DESTINO.get(m, {}).get("lat", np.nan)
    )
    df["destino_lon"] = df["destino_mercado"].map(
        lambda m: COORDENADAS_DESTINO.get(m, {}).get("lon", np.nan)
    )
    df["destino_ciudad"] = df["destino_mercado"].map(
        lambda m: COORDENADAS_DESTINO.get(m, {}).get("ciudad", "")
    )
    
    # Distancia de transporte geodésica (Haversine)
    distancias = [
        haversine_km(r.origen_lat, r.origen_lon, r.destino_lat, r.destino_lon)
        for r in df.itertuples()
    ]
    df["distancia_transporte_km"] = distancias
    return df


def parsear_json_clima(ruta_json, estado):
    """Convierte el archivo JSON crudo de Open-Meteo en un DataFrame tabular."""
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    daily = data.get("daily", {})
    df = pd.DataFrame({
        "fecha": pd.to_datetime(daily["time"]),
        "estado": estado,
        "temp_media_c": daily.get("temperature_2m_mean"),
        "temp_min_c": daily.get("temperature_2m_min"),
        "temp_max_c": daily.get("temperature_2m_max"),
        "precipitacion_mm": daily.get("precipitation_sum"),
    })
    df["anio"] = df["fecha"].dt.year.astype("Int64")
    df["anio_mes"] = df["fecha"].dt.to_period("M").dt.to_timestamp()
    df["archivo_origen"] = Path(ruta_json).name
    return df

