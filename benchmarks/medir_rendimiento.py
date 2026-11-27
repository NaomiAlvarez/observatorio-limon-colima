#!/usr/bin/env python3
"""Arnés de medición de rendimiento (Benchmarking) para el pipeline del Observatorio.

Mide con precisión:
1. Tiempo de ejecución total y por cada fase/etapa (time.perf_counter).
2. Consumo de memoria RAM: memoria pico interna (tracemalloc) y memoria de proceso (psutil RSS).
3. Conteo estricto de errores, excepciones y registros en cuarentena.
4. Ejecución de N iteraciones independientes para análisis de reproducibilidad (media, std, min, max).
5. Exportación de métricas a CSV y JSON como evidencia verificable de auditoría.
"""
import gc
import json
import os
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import psutil

# Asegurar importación de módulos del proyecto
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

# Configurar entorno para ejecuciones limpias
os.environ["DISABLE_PANDERA_IMPORT_WARNING"] = "True"

from src.integracion import integrar, agregar_siap_anual
from src.limpieza import (
    diagnostico_faltantes,
    imputar_faltantes,
    marcar_atipicos_iqr,
    normalizar,
    discretizar,
    reducir,
)
from src.calidad import validar_archivos
from src.oro import (
    construir_oro_mensual,
    construir_oro_geoespacial,
    construir_matriz_linaje,
    verificar_conservacion_fechas_ingesta,
)


@dataclass
class MetricasPaso:
    paso: str
    tiempo_segundos: float
    memoria_pico_mb: float


@dataclass
class CorridaMetricas:
    corrida_id: int
    tiempo_total_segundos: float
    memoria_pico_tracemalloc_mb: float
    memoria_rss_final_mb: float
    memoria_rss_delta_mb: float
    filas_sniim_plata: int
    filas_integrado_plata: int
    filas_oro_mensual: int
    filas_oro_geo: int
    filas_matriz_linaje: int
    cuarentena_total: int
    discrepancias_linaje: int
    errores_conteo: int
    tiempos_por_paso: Dict[str, float]
    memorias_por_paso: Dict[str, float]


def ejecutar_pipeline_instrumentado(corrida_id: int = 1) -> CorridaMetricas:
    """Ejecuta una iteración completa del pipeline midiendo cada fase."""
    gc.collect()
    proceso = psutil.Process()
    rss_inicial_mb = proceso.memory_info().rss / (1024 * 1024)

    tracemalloc.start()
    t_inicio_total = time.perf_counter()

    tiempos_paso: Dict[str, float] = {}
    memorias_paso: Dict[str, float] = {}
    errores = 0

    plata = RAIZ / "data" / "plata"
    oro = RAIZ / "data" / "oro"
    cuarentena = RAIZ / "data" / "cuarentena"
    plata.mkdir(parents=True, exist_ok=True)
    oro.mkdir(parents=True, exist_ok=True)
    cuarentena.mkdir(parents=True, exist_ok=True)

    try:
        # ---------------------------------------------------------
        # Paso 1: Ingesta e Integración
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        integrado, sniim_d, siap_h, clima_d, bitacoras = integrar(
            RAIZ / "data/bronce/sniim",
            RAIZ / "data/bronce/siap",
            RAIZ / "data/bronce/clima",
        )
        siap_h = marcar_atipicos_iqr(siap_h, "rendimiento_ton_ha")
        integrado.to_parquet(plata / "integrado_sin_validar.parquet", index=False, engine="pyarrow", compression="snappy")
        sniim_d.to_parquet(plata / "sniim_diario_homologado.parquet", index=False, engine="pyarrow", compression="snappy")
        siap_h.to_parquet(plata / "siap_municipal_homologado.parquet", index=False, engine="pyarrow", compression="snappy")
        if not clima_d.empty:
            clima_d.to_parquet(plata / "clima_diario_homologado.parquet", index=False, engine="pyarrow", compression="snappy")
        reporte = sniim_d[sniim_d["es_atipico"] | sniim_d["precio_incoherente"]]
        reporte.to_csv(plata / "reporte_atipicos_sniim.csv", index=False)
        tiempos_paso["1_integracion"] = time.perf_counter() - t0
        memorias_paso["1_integracion"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 2: Tratamiento de Faltantes
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        diagnostico_faltantes(integrado)
        siap_anual = agregar_siap_anual(siap_h)
        integrado = imputar_faltantes(integrado, siap_anual)
        integrado.to_parquet(plata / "integrado_imputado.parquet", index=False, engine="pyarrow", compression="snappy")
        tiempos_paso["2_faltantes_imputacion"] = time.perf_counter() - t0
        memorias_paso["2_faltantes_imputacion"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 3: Normalización y Estandarización
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        integrado = normalizar(integrado)
        tiempos_paso["3_normalizacion"] = time.perf_counter() - t0
        memorias_paso["3_normalizacion"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 4: Discretización y Jerarquías
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        integrado = discretizar(integrado)
        integrado.to_parquet(plata / "integrado_transformado.parquet", index=False, engine="pyarrow", compression="snappy")
        tiempos_paso["4_discretizacion"] = time.perf_counter() - t0
        memorias_paso["4_discretizacion"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 5: Reducción de Datos
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        reducido, eliminadas = reducir(integrado, siap_h, sniim_d)
        reducido.to_parquet(plata / "integrado_reducido.parquet", index=False, engine="pyarrow", compression="snappy")
        tiempos_paso["5_reduccion"] = time.perf_counter() - t0
        memorias_paso["5_reduccion"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 6: Puerta de Calidad (Pandera Plata y Oro)
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        res_calidad = validar_archivos(plata, cuarentena, oro)
        tiempos_paso["6_puerta_calidad"] = time.perf_counter() - t0
        memorias_paso["6_puerta_calidad"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 7: Generación de Capa Oro
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        reducido_validado = pd.read_parquet(plata / "integrado_reducido_validado.parquet")
        sniim_validado = pd.read_parquet(plata / "sniim_diario_validado.parquet")

        oro_mensual = construir_oro_mensual(reducido_validado)
        oro_mensual.to_parquet(oro / "oro_serie_mensual_observatorio.parquet", index=False, engine="pyarrow", compression="snappy")

        oro_geo = construir_oro_geoespacial(sniim_validado, siap_anual)
        oro_geo.to_parquet(oro / "oro_mercados_geoespacial.parquet", index=False, engine="pyarrow", compression="snappy")

        matriz_linaje = construir_matriz_linaje(oro_mensual, oro_geo, bitacoras)
        matriz_linaje.to_parquet(oro / "oro_linaje_matriz.parquet", index=False, engine="pyarrow", compression="snappy")
        matriz_linaje.to_csv(oro / "oro_linaje_matriz.csv", index=False)
        tiempos_paso["7_capa_oro"] = time.perf_counter() - t0
        memorias_paso["7_capa_oro"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

        # ---------------------------------------------------------
        # Paso 8: Auditoría y Verificación de Linaje
        # ---------------------------------------------------------
        t0 = time.perf_counter()
        tracemalloc.reset_peak()
        total_rev, disc = verificar_conservacion_fechas_ingesta(oro_mensual, bitacoras)
        tiempos_paso["8_auditoria_linaje"] = time.perf_counter() - t0
        memorias_paso["8_auditoria_linaje"] = tracemalloc.get_traced_memory()[1] / (1024 * 1024)

    except Exception as e:
        errores += 1
        raise e
    finally:
        tiempo_total = time.perf_counter() - t_inicio_total
        pico_tracemalloc_mb = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
        tracemalloc.stop()

    rss_final_mb = proceso.memory_info().rss / (1024 * 1024)
    rss_delta_mb = max(0.0, rss_final_mb - rss_inicial_mb)

    # Conteo de cuarentena
    cuarentena_filas = 0
    for archivo_c in cuarentena.glob("*.csv"):
        try:
            cuarentena_filas += len(pd.read_csv(archivo_c))
        except Exception:
            pass

    return CorridaMetricas(
        corrida_id=corrida_id,
        tiempo_total_segundos=round(tiempo_total, 4),
        memoria_pico_tracemalloc_mb=round(pico_tracemalloc_mb, 2),
        memoria_rss_final_mb=round(rss_final_mb, 2),
        memoria_rss_delta_mb=round(rss_delta_mb, 2),
        filas_sniim_plata=len(sniim_validado),
        filas_integrado_plata=len(reducido_validado),
        filas_oro_mensual=len(oro_mensual),
        filas_oro_geo=len(oro_geo),
        filas_matriz_linaje=len(matriz_linaje),
        cuarentena_total=cuarentena_filas,
        discrepancias_linaje=disc,
        errores_conteo=errores,
        tiempos_por_paso={k: round(v, 4) for k, v in tiempos_paso.items()},
        memorias_por_paso={k: round(v, 2) for k, v in memorias_paso.items()},
    )


def ejecutar_benchmarking(n_iteraciones: int = 5, etiqueta: str = "baseline") -> Dict[str, Any]:
    """Ejecuta N iteraciones y consolida estadísticas para reproducibilidad."""
    print(f"\n=======================================================")
    print(f"INICIANDO BENCHMARKING [{etiqueta.upper()}]: {n_iteraciones} ITERACIONES")
    print(f"=======================================================")

    corridas: List[CorridaMetricas] = []
    for i in range(1, n_iteraciones + 1):
        print(f"-> Ejecutando corrida {i}/{n_iteraciones}...")
        metricas = ejecutar_pipeline_instrumentado(corrida_id=i)
        corridas.append(metricas)
        print(
            f"   Corrida {i}: {metricas.tiempo_total_segundos:.3f} s | "
            f"RAM Pico: {metricas.memoria_pico_tracemalloc_mb:.2f} MB | "
            f"RSS: {metricas.memoria_rss_final_mb:.2f} MB | Errores: {metricas.errores_conteo}"
        )

    tiempos_totales = [c.tiempo_total_segundos for c in corridas]
    memorias_pico = [c.memoria_pico_tracemalloc_mb for c in corridas]
    memorias_rss = [c.memoria_rss_final_mb for c in corridas]

    # Estadísticas por paso
    pasos = list(corridas[0].tiempos_por_paso.keys())
    estadisticas_pasos = {}
    for p in pasos:
        tiempos_p = [c.tiempos_por_paso[p] for c in corridas]
        memorias_p = [c.memorias_por_paso[p] for c in corridas]
        estadisticas_pasos[p] = {
            "tiempo_medio_s": round(float(np.mean(tiempos_p)), 4),
            "tiempo_std_s": round(float(np.std(tiempos_p)), 4),
            "tiempo_min_s": round(float(np.min(tiempos_p)), 4),
            "tiempo_max_s": round(float(np.max(tiempos_p)), 4),
            "memoria_pico_media_mb": round(float(np.mean(memorias_p)), 2),
            "memoria_pico_std_mb": round(float(np.std(memorias_p)), 2),
        }

    resumen = {
        "etiqueta": etiqueta,
        "n_iteraciones": n_iteraciones,
        "tiempo_total": {
            "media_s": round(float(np.mean(tiempos_totales)), 4),
            "std_s": round(float(np.std(tiempos_totales)), 4),
            "min_s": round(float(np.min(tiempos_totales)), 4),
            "max_s": round(float(np.max(tiempos_totales)), 4),
        },
        "memoria_pico_tracemalloc_mb": {
            "media_mb": round(float(np.mean(memorias_pico)), 2),
            "std_mb": round(float(np.std(memorias_pico)), 2),
            "min_mb": round(float(np.min(memorias_pico)), 2),
            "max_mb": round(float(np.max(memorias_pico)), 2),
        },
        "memoria_rss_mb": {
            "media_mb": round(float(np.mean(memorias_rss)), 2),
            "std_mb": round(float(np.std(memorias_rss)), 2),
        },
        "integridad": {
            "filas_sniim_plata": corridas[0].filas_sniim_plata,
            "filas_integrado_plata": corridas[0].filas_integrado_plata,
            "filas_oro_mensual": corridas[0].filas_oro_mensual,
            "filas_oro_geo": corridas[0].filas_oro_geo,
            "filas_matriz_linaje": corridas[0].filas_matriz_linaje,
            "cuarentena_total": corridas[0].cuarentena_total,
            "discrepancias_linaje": corridas[0].discrepancias_linaje,
            "errores_totales": sum(c.errores_conteo for c in corridas),
        },
        "estadisticas_pasos": estadisticas_pasos,
        "corridas_detalle": [asdict(c) for c in corridas],
    }

    # Guardar evidencias en evidencias/E3
    salida_dir = RAIZ / "evidencias" / "E3"
    salida_dir.mkdir(parents=True, exist_ok=True)

    ruta_json = salida_dir / f"benchmark_{etiqueta}.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    df_detalle = pd.DataFrame([asdict(c) for c in corridas])
    df_detalle.to_csv(salida_dir / f"benchmark_{etiqueta}_corridas.csv", index=False)

    print(f"\nResultados guardados exitosamente en:")
    print(f" -> {ruta_json}")
    print(f" -> {salida_dir / f'benchmark_{etiqueta}_corridas.csv'}")
    return resumen


if __name__ == "__main__":
    etiqueta = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    n_iter = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    ejecutar_benchmarking(n_iteraciones=n_iter, etiqueta=etiqueta)
