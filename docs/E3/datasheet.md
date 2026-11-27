# Datasheet del dataset — Capa Oro

**Proyecto:** Observatorio del Precio del Limón en Colima  
**Fecha de revisión:** 27 de noviembre de 2026  
**Versión:** E3

## Motivación

El dataset reúne indicadores mensuales sobre precio mayoreo, producción agrícola, clima y linaje geoespacial del limón en estados productores de México. Su propósito es apoyar análisis exploratorio, pronóstico de series temporales y estudios descriptivos de rutas y precios en un contexto académico.

El observatorio se creó para estudiar la relación entre el precio del limón al mayoreo, la producción agrícola y variables climáticas, sin representar una fuente oficial de precios ni una recomendación comercial.

## Composición

El producto principal es `data/entrega-e3/oro_serie_mensual_observatorio_clean.csv`:

- **137 registros**.
- **55 columnas**.
- **Una fila por estado y mes**.
- Cobertura SNIIM de noviembre de 2023 a octubre de 2026, integrada con SIAP hasta 2025 y clima hasta noviembre de 2026.
- 0 filas completamente duplicadas.
- 0 duplicados de la clave conceptual `estado + anio_mes`.
- Sin valores faltantes en variables observadas o derivadas base.
- Los faltantes están concentrados en variables estructurales calculadas:
  - `var_interanual_precio_pct`: 49;
  - `precio_lag_3m`: 13;
  - `precio_lag_2m`: 9;
  - `precio_lag_1m`: 5;
  - `var_mensual_precio_pct`: 5.
- Se conservan como vacíos porque no existen antecedentes suficientes para calcularlos. No se imputaron con cero.

Se incluyen como tablas complementarias:

- `oro_mercados_geoespacial_clean.csv`: 174 rutas mensuales y 24 columnas.
- `oro_linaje_matriz_clean.csv`: 599 enlaces de trazabilidad y 9 columnas.

## Variables principales

| Variable | Significado |
|---|---|
| `anio_mes`, `anio`, `estado` | Periodo y estado productor |
| `precio_frec_media`, `precio_min`, `precio_max` | Estadísticos mensuales del precio frecuente y límites |
| `n_cotizaciones`, `n_atipicos` | Tamaño y calidad de las cotizaciones |
| `produccion_ton`, `valor_produccion`, `precio_rural_kg` | Indicadores anuales SIAP repetidos por mes |
| `temp_media_c`, `temp_min_c`, `temp_max_c`, `precipitacion_mm` | Variables climáticas mensuales |
| `siap_imputado`, `anio_dato_siap` | Banderas de aproximación cuando faltan datos 2026 |
| `precio_lag_1m` a `precio_lag_3m` | Rezagos temporales por estado |
| `var_mensual_precio_pct`, `var_interanual_precio_pct` | Variaciones calculadas |
| `registro_id_oro`, `linaje_id` | Identificadores auditables |

Las columnas de archivos, fechas de ingesta y hashes permiten rastrear los registros hasta Bronce.

## Proceso de recolección

1. Captura de cotizaciones SNIIM en HTML.
2. Descarga de cierres agrícolas municipales SIAP en archivos CSV comprimidos.
3. Consulta de datos históricos Open-Meteo por coordenadas representativas.
4. Conservación de originales, fechas de captura, tamaños y hashes SHA-256 en Bronce.
5. Homologación de nombres, estados y periodos en Plata.
6. Validación con Pandera, agregación mensual y creación de tablas analíticas en Oro.

Las coordenadas geoespaciales son representativas de municipios y centrales de abasto; no representan ubicaciones personales ni mediciones de campo.

## Preprocesamiento

- Se excluyeron cultivos distintos de limón.
- Se marcaron o excluyeron duplicados de cotización según correspondió a la agregación.
- Se identificaron atípicos con Hampel y valores incoherentes con reglas lógicas.
- Los faltantes del SIAP correspondientes a 2026 se aproximaron con el cierre 2025 y se marcaron con banderas.
- Se calcularon rezagos, variaciones, normalizaciones, niveles y jerarquías temporales.
- Las rutas geoespaciales se calcularon con Haversine entre puntos representativos.
- Se excluyó de las agregaciones Oro los registros marcados como duplicados o incoherentes.
- Se mantuvo trazabilidad a los archivos originales mediante identificadores, hashes y matriz de linaje.

## Casos de uso recomendados

- Análisis exploratorio del precio mensual por estado.
- Comparación descriptiva de precio, producción y clima.
- Enseñanza de limpieza, integración, calidad y linaje de datos.
- Pruebas reproducibles de modelos de series temporales.
- Benchmarking de transformaciones y ejecución de pipelines.
- Visualización agregada de mercados y rutas.

## Casos de uso no recomendados

- Afirmar un pronóstico comercial garantizado.
- Estimar costos reales de transporte o rutas terrestres exactas.
- Inferir comportamiento individual de productores, compradores o consumidores.
- Identificar personas o ubicaciones privadas.
- Usar los datos 2026 del SIAP imputados como observaciones oficiales.
- Emitir asesoría financiera, regulatoria o de precios como resultado directo del dataset.
- Realizar inferencias nacionales sin considerar cobertura geográfica desigual.

## Licencia y distribución

El repositorio pretende distribuir una compilación derivada bajo **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)**. El texto aplicable se encuentra en `LICENSE-DATASET.txt`.

La licencia de la compilación no amplía ni reemplaza las condiciones de las fuentes originales. Open-Meteo se identifica con CC BY 4.0; SNIIM y SIAP no exhibieron una licencia reutilizable específica durante la revisión realizada. Por ello:

- SNIIM y SIAP deben atribuirse a sus respectivos portales oficiales.
- Cualquier uso público o comercial requiere verificar nuevamente los términos vigentes de todas las fuentes.
- La ubicación principal de distribución académica es el repositorio GitHub `NaomiAlvarez/observatorio-limon-colima`.
- Los archivos CSV preparados están en `data/entrega-e3/`.
- La publicación externa en Zenodo, Kaggle u otro repositorio permanece pendiente hasta confirmar permisos específicos de las fuentes.

## Privacidad y seguridad

La revisión no encontró nombres de personas, identificadores personales, claves API, credenciales, correos ni teléfonos. Las tablas contienen precios, producción, clima, geografía pública y metadatos agregados. Las coordenadas son representaciones públicas y no datos de personas.
