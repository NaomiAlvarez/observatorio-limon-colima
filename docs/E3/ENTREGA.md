# Ficha de entrega E3

## Observatorio del precio del limón en Colima

- **Etapa:** E3 — Optimización, publicación y documentación del dataset
- **Fecha de cierre:** 27 de noviembre de 2026
- **Institución:** Tecnológico Nacional de México — Campus Colima
- **Responsable de esta parte:** Integrante 2 — Dataset y documentación

## 1. Objetivo

Completar la preparación, revisión, licencia y documentación del dataset final de Capa Oro. La entrega incorpora los resultados reales de rendimiento proporcionados por el Integrante 1 y deja una versión CSV preparada para distribución académica.

## 2. Dataset final seleccionado

La tabla principal es `oro_serie_mensual_observatorio`, publicada en formato CSV limpio:

- `data/entrega-e3/oro_serie_mensual_observatorio_clean.csv`
- 137 filas y 55 columnas.
- 137 identificadores `registro_id_oro` únicos.
- 0 filas completamente duplicadas.
- 0 duplicados de `estado + anio_mes`.
- Los únicos faltantes de la tabla son rezagos o variaciones calculadas al inicio de una serie por estado.

Se incluyen las tablas complementarias derivadas del mismo Gold:

- `data/entrega-e3/oro_mercados_geoespacial_clean.csv`: 174 filas y 24 columnas.
- `data/entrega-e3/oro_linaje_matriz_clean.csv`: 599 vínculos y 9 columnas.
- `data/entrega-e3/SHA256SUMS.txt`: integridad de los CSV.

Los Parquet originales continúan disponibles en `data/oro/`.

## 3. Calidad del dataset

Se verificaron:

- **Faltantes:** variables base completas; faltantes esperados únicamente en rezagos y variaciones.
- **Duplicados:** ninguna fila duplicada ni clave mensual-estado duplicada.
- **Tipos:** fechas normalizadas como `YYYY-MM-01`, enteros y números consistentes, banderas booleanas conservadas en la fuente Parquet y convertibles desde CSV.
- **Consistencia:** estados válidos, periodos dentro de la cobertura documentada y enlaces de linaje completos.
- **Privacidad:** no se encontraron datos personales o confidenciales.

La matriz de linaje contiene 599 enlaces sin valores faltantes y conserva hashes SHA-256 de los archivos Bronce.

## 4. Licencia y distribución

Se seleccionó CC BY 4.0 para la compilación derivada. El archivo de licencia es `LICENSE-DATASET.txt`.

La revisión anterior documentó que:

- Open-Meteo declara CC BY 4.0.
- SNIIM y SIAP no exhibieron una licencia reutilizable específica.
- Por lo anterior, esta licencia cubre la compilación académica propia, pero no concede derechos que las fuentes originales no tengan.

La distribución actual está preparada dentro del repositorio. El repositorio GitHub `NaomiAlvarez/observatorio-limon-colima` es la ubicación publicada; una publicación externa de datos en Zenodo/Kaggle/Hugging Face queda como trámite pendiente sujeto a validación jurídica.

## 5. Documentación creada

| Entregable | Ruta |
|---|---|
| Dataset limpio mensual | `data/entrega-e3/oro_serie_mensual_observatorio_clean.csv` |
| Dataset geoespacial limpio | `data/entrega-e3/oro_mercados_geoespacial_clean.csv` |
| Linaje limpio | `data/entrega-e3/oro_linaje_matriz_clean.csv` |
| Manifest de hashes | `data/entrega-e3/SHA256SUMS.txt` |
| Licencia | `LICENSE-DATASET.txt` |
| Datasheet | `docs/E3/datasheet.md` |
| Ficha de entrega | `docs/E3/ENTREGA.md` |
| Relatoría | `docs/relatoria-E3.md` |

## 6. Resultados de rendimiento E3

El integrante 1 proporcionó 5 corridas independientes para cada versión. Las métricas globales fueron:

| Métrica | Baseline | Optimizado | Resultado |
|---|---:|---:|---|
| Tiempo total medio | 27.379 s | 22.236 s | 18.8% más rápido |
| Desviación estándar | 2.357 s | 0.420 s | 82.2% más estable |
| Tiempo mínimo | 25.962 s | 22.005 s | 15.2% más rápido |
| Tiempo máximo | 32.084 s | 23.076 s | 28.1% más rápido |
| Memoria trazada pico | 10.69 MB | 10.64 MB | 0.5% menor |

La fase de generación de Capa Oro pasó de 1.3098 s a 0.5534 s, una mejora de 57.7% y un speedup de 2.37x. La integración pasó de 23.279 s a 18.9564 s.

La integridad fue idéntica:

- 137 filas Oro mensual.
- 174 rutas geoespaciales.
- 599 enlaces de linaje.
- 0 discrepancias de fechas de ingesta.
- 0 errores de ejecución.
- 16 pruebas aprobadas en la versión optimizada.

## 7. Conclusiones

La Capa Oro cuenta ya con una versión CSV distribuible y documentada, acompañada de la matriz de linaje y la licencia. Los vacíos restantes corresponden a rezagos temporales y no indican pérdida de variables base.

Antes de una publicación masiva o comercial falta obtener confirmación jurídica específica de SNIIM y SIAP y seleccionar un repositorio externo. Para el alcance académico actual, el repositorio permite reproducir y consultar el dataset, sus fuentes y su trazabilidad.
