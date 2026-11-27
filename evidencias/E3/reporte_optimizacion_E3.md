# Reporte de Optimización de Pipeline — Etapa 3 (E3)
**Proyecto:** Observatorio del Precio del Limón en Colima  
**Rol Técnico:** Ingeniero de Datos (Especialista en Rendimiento)  
**Metodología:** Benchmarking empírico con 5 iteraciones independientes por fase, trazado con `time.perf_counter` y `tracemalloc`.

---

## 1. Resumen Ejecutivo de la Optimización

Se diagnosticaron y resolvieron los principales cuellos de botella del pipeline en las capas Bronce, Plata y Oro:
1. **Descompresión e Ingesta de SIAP:** Reemplazo de la lectura monolítica secuencial en C por **lectura multihilo con PyArrow (`engine="pyarrow"`)** sobre los 23 archivos `.csv.gz`.
2. **Cálculo Geodésico de Rutas Comerciales:** Reemplazo de bucles escalares `itertuples()` por **fórmula de Haversine vectorizada en C/NumPy (`haversine_km_vectorizado`)**, reduciendo el cálculo de rutas de mercados de forma drástica.
3. **Mapeos Hash de Linaje O(1):** Sustitución de funciones lambda y `.map(limpiar_texto)` redundantes por tablas hash precompiladas para resolución inmediata de metadatos SHA-256 y fechas de ingesta.
4. **Persistencia Columnar con Compresión Snappy:** Especificación de `engine="pyarrow", compression="snappy"` en todas las salidas Parquet intermedias y finales.
5. **Integridad de Datos Certificada al 100%:** Todas las dimensiones (filas de SNIIM, filas integradas, series Oro, rutas geoespaciales y matriz de linaje) son **exactamente idénticas** a la línea base, pasando el 100% de las pruebas automatizadas.

---

## 2. Tabla Comparativa Global (Baseline vs Optimizado)

| Métrica | Línea Base (Baseline) | Optimizado | Diferencia Absoluta | Mejora (%) | Factor (Speedup) |
|---|---|---|---|---|---|
| **Tiempo Total de Ejecución (Media)** | 27.379 s | 22.236 s | -5.143 s | +18.8% más rápido | 1.23x |
| **Desviación Estándar de Tiempo (Varianza)** | 2.357 s | 0.420 s | -1.937 s | +82.2% más estable | 5.61x más reproducible |
| **Tiempo Mínimo Registrado** | 25.962 s | 22.005 s | -3.957 s | +15.2% | 1.18x |
| **Tiempo Máximo Registrado** | 32.084 s | 23.076 s | -9.008 s | +28.1% | 1.39x |
| **Memoria RAM Pico (tracemalloc)** | 10.69 MB | 10.64 MB | -0.05 MB | 0.5% | Consumo controlado |
| **Errores de Ejecución y Excepciones** | 0 errores | 0 errores | 0 | 100% robustez | 1.00x |
| **Discrepancias en Linaje y Fechas** | 0 discrepancias | 0 discrepancias | 0 | 100% integridad | 1.00x |

---

## 3. Desglose Detallado por Fase del Pipeline

| Fase del Pipeline | Tiempo Baseline (s) | Tiempo Optimizado (s) | Ahorro (s) | Mejora (%) | Speedup |
|---|---|---|---|---|---|
| **Paso 1: Ingesta e Integración (SNIIM + SIAP + Clima)** | 23.279 s | 18.9564 s | 4.3226 s | +18.6% | 1.23x |
| **Paso 2: Diagnóstico e Imputación MAR** | 0.1935 s | 0.1954 s | -0.0019 s | -1.0% | 0.99x |
| **Paso 3: Normalización (Min-Max) y Z-Score** | 0.0757 s | 0.0802 s | -0.0045 s | -5.9% | 0.94x |
| **Paso 4: Discretización y Jerarquías Conceptuales** | 0.0997 s | 0.0952 s | 0.0045 s | +4.5% | 1.05x |
| **Paso 5: Reducción de Datos (Selección de Variables)** | 0.0641 s | 0.0667 s | -0.0026 s | -4.1% | 0.96x |
| **Paso 6: Puerta de Calidad (Pandera Plata y Oro)** | 2.323 s | 2.2537 s | 0.0693 s | +3.0% | 1.03x |
| **Paso 7: Generación de Capa Oro y Linaje** | 1.3098 s | 0.5534 s | 0.7564 s | +57.7% | 2.37x |
| **Paso 8: Auditoría de Fechas de Ingesta y Linaje** | 0.0309 s | 0.0318 s | -0.0009 s | -2.9% | 0.97x |

---

## 4. Auditoría de Integridad de Datos

Para verificar que ninguna optimización alteró los datos ni causó pérdida de información, se contrastaron los recuentos y validaciones entre ambas versiones:

| Entidad / Artefacto | Recuento Baseline | Recuento Optimizado | Estado de Integridad |
|---|---|---|---|
| **SNIIM Diario Plata (Válidos)** | 3634 filas | 3634 filas | ✅ 100% Idéntico |
| **Integrado Mensual Plata** | 137 filas | 137 filas | ✅ 100% Idéntico |
| **Capa Oro: Serie Mensual** | 137 filas | 137 filas | ✅ 100% Idéntico |
| **Capa Oro: Rutas Geoespaciales** | 174 rutas | 174 rutas | ✅ 100% Idéntico |
| **Matriz de Linaje Bronce-Oro** | 599 enlaces | 599 enlaces | ✅ 100% Idéntico |
| **Discrepancias de Fechas de Ingesta** | 0 discrepancias | 0 discrepancias | ✅ Cero discrepancias |
| **Errores y Excepciones** | 0 errores | 0 errores | ✅ Cero errores |
| **Pruebas Automatizadas (pytest)** | 13 aprobadas | 16 aprobadas | ✅ 100% Aprobadas |

---

## 5. Reproducibilidad de los Resultados

Las mediciones se ejecutaron de manera automática a lo largo de **5 iteraciones completas** para cada versión.  
* **Estabilidad:** La desviación estándar disminuyó de **2.357 s** a **0.420 s** (5.61 veces más consistente), eliminando la variabilidad de I/O en la lectura cruda.
* **Archivos de Evidencia Guardados:**
  - `evidencias/E3/benchmark_baseline.json`
  - `evidencias/E3/benchmark_baseline_corridas.csv`
  - `evidencias/E3/benchmark_optimizado.json`
  - `evidencias/E3/benchmark_optimizado_corridas.csv`
  - `evidencias/E3/tabla_comparativa_global.csv`
  - `evidencias/E3/tabla_comparativa_pasos.csv`
