# Relatoría de la etapa E3

## Observatorio del precio del limón en Colima

- **Responsable documental:** Integrante 2 — Dataset y documentación
- **Fecha:** 27 de noviembre de 2026

## 1. Actividades realizadas

1. Identificación de las tablas finales de Capa Oro.
2. Revisión de dimensiones, duplicados, faltantes y tipos de datos.
3. Inspección de nombres y contenido con el objetivo de descartar datos personales.
4. Exportación de tablas Oro a CSV con fechas normalizadas.
5. Generación de una suma SHA-256 para cada archivo distribuible.
6. Investigación y selección de CC BY 4.0 como licencia de la compilación derivada.
7. Incorporación de una licencia y documentación de restricciones por fuente.
8. Creación del datasheet y de la ficha de entrega.
9. Incorporación de los resultados de rendimiento proporcionados por el Integrante 1.

## 2. Selección del dataset

Se seleccionó `oro_serie_mensual_observatorio` como dataset principal porque contiene la integración mensual de precios, producción, clima y variables derivadas. Las tablas geoespacial y de linaje se documentaron como complementarias.

La revisión encontró:

- 137 filas mensuales y 55 columnas.
- 0 filas completas duplicadas.
- 0 duplicados de estado y mes.
- 81 valores faltantes, concentrados en rezagos y variaciones construidas al inicio de las series.
- 174 rutas geoespaciales y 599 vínculos de linaje.

Los faltantes estructurales se conservaron, no se rellenaron con ceros o promedios, y quedaron explicados en el datasheet.

## 3. Licencia y distribución

Se añadió `LICENSE-DATASET.txt` con Creative Commons Atribución 4.0 Internacional.

La decisión toma en cuenta que Open-Meteo declara CC BY 4.0, mientras que SNIIM y SIAP no presentaron una licencia reutilizable específica durante la revisión. Por ello, la licencia se limita a la compilación y deriva propia. No se afirma que otorgue derechos más amplios sobre los datos originales.

Los CSV fueron preparados en `data/entrega-e3/`. El repositorio GitHub es la distribución académica disponible. Para una plataforma externa se documentó como pendiente la confirmación de permisos y la revisión jurídica de las fuentes.

## 4. Rendimiento incorporado

Se incorporaron los resultados de 5 iteraciones independientes. El pipeline optimizado tardó 22.236 s frente a 27.379 s del baseline, una mejora de 18.8%. La desviación disminuyó de 2.357 s a 0.420 s.

La generación Oro pasó de 1.3098 s a 0.5534 s. Los conteos permanecieron idénticos: 137 filas mensuales, 174 rutas y 599 enlaces. No hubo discrepancias de linaje ni errores de ejecución.

Estos valores se tomaron de `evidencias/E3/benchmark_*.json` y de `evidencias/E3/reporte_optimizacion_E3.md`, no de una medición adicional realizada en esta parte.

## 5. Dificultades y soluciones

### Interpretación de los faltantes

**Dificultad:** algunas columnas presentan faltantes legítimos porque los rezagos o variaciones interanuales requieren observaciones previas.

**Solución:** se verificó que las variables base estuvieran completas y se documentó el recuento exacto por columna. No se realizó imputación artificial.

### Licencias heterogéneas

**Dificultad:** las fuentes no tenían un régimen uniforme; Open-Meteo sí indicó CC BY 4.0, mientras que SNIIM y SIAP no exhibieron licencias específicas.

**Solución:** se eligió CC BY 4.0 para la compilación derivada y se añadió una advertencia expresa. El datasheet prohíbe leer la licencia como una ampliación de derechos sobre fuentes originales.

### Publicación externa

**Dificultad:** no existía evidencia suficiente para afirmar que el conjunto completo puede publicarse comercialmente o redistribuirse libremente.

**Solución:** se dejó una distribución académica preparada en el repositorio y se documentó el procedimiento pendiente para Zenodo, Kaggle u otro servicio.

### Integridad y reproducibilidad

**Dificultad:** CSV, Parquet y matriz de linaje pueden divergir si se exportan con formatos distintos.

**Solución:** se generaron los CSV a partir de los archivos Oro existentes y se creó `SHA256SUMS.txt` para verificar exactamente los archivos preparados.

## 6. Conclusiones

La parte de Dataset y documentación quedó preparada:

- El dataset mensual final fue identificado y exportado.
- Se completaron comprobaciones de duplicados, faltantes, tipos y privacidad.
- Se incorporaron licencia, datasheet, ficha de entrega y relatoría.
- Se documentaron los resultados de rendimiento de la optimización.
- Se dejó clara la diferencia entre distribución académica disponible y publicación externa pendiente.

La limitación principal es jurídica: antes de publicar masivamente deben confirmarse términos vigentes de SNIIM y SIAP. Esto no impide la entrega académica ni el uso reproducible dentro del proyecto.
