# Observatorio del precio del limón en Colima

Proyecto integrador de **Ingeniería de Datos** (Tecnológico Nacional de México, Campus Colima).
Integra el precio al mayoreo del limón (SNIIM) con la producción agrícola municipal (SIAP)
mediante una arquitectura de capas **Bronce → Plata → Oro**.

## Estado de las entregas

| Entrega | Contenido | Tag | Estado |
|---|---|---|---|
| E0 | Ingesta y capa Bronce (datos crudos con bitácora) | `e0` | Entregada |
| E1 | Limpieza y preprocesamiento, integración, Puerta de Calidad y capa Plata | `e1` | Completa (Lista para entrega) |
| E2 | Experimentación, factores y capa Oro | `e2` | Por iniciar |

Avance de la E1:

- [x] Integración y resolución de conflictos de esquema (SNIIM + SIAP)
- [x] Valores faltantes: diagnóstico del mecanismo e imputación
- [x] Atípicos y ruido (Z-Score robusto con ventana móvil, IQR)
- [x] Normalización y estandarización (Min-Max y Z-Score)
- [x] Discretización y jerarquías conceptuales
- [x] Reducción de datos (agregación y selección de variables)
- [x] Puerta de Calidad automática con cuarentena (Pandera)
- [x] Ficha técnica (`docs/E1/ENTREGA.md`) y relatoría (`docs/relatoria-E1.md`)
- [x] Cuaderno interactivo de exploración (`docs/E1/limpieza.ipynb`)

## Fuentes de datos

| Fuente | Qué contiene | Formato en Bronce | Granularidad |
|---|---|---|---|
| **SNIIM** (Mercados Nacionales Agrícolas) | Precios al mayoreo de *Limón c/semilla # 4 Primera*, en pesos por kilogramo calculado, con presentación, origen (estado productor) y destino (mercado) | HTML, uno por rango de fechas | Diaria, por mercado |
| **SIAP** (Cierre agrícola municipal) | Superficie sembrada y cosechada, producción, rendimiento, precio rural y valor de la producción | `cierre_AAAA.csv.gz` (2003–2025) | Anual, por municipio |

Cada fuente trae su `_bitacora.csv` de descarga (URL, fecha de captura, `sha256`, resultado), que se conserva para trazabilidad.
El SIAP aún no publica 2026.

## Arquitectura de capas

| Capa | Carpeta | Contenido |
|---|---|---|
| Bronce | `data/bronce/` | Datos tal como se descargaron, sin modificar, con sidecars JSON de tamaño y SHA-256 |
| Plata | `data/plata/` | Datos homologados, limpios y validados |
| Cuarentena | `data/cuarentena/` | Registros rechazados, con el motivo documentado (nunca se borran en silencio) |
| Oro | `data/oro/` | Tablas agregadas listas para el análisis del observatorio |

## Estructura del repositorio

```
observatorio-limon-colima/
├── data/
│   ├── bronce/
│   │   ├── sniim/            # HTML por rango de fechas + bitácora
│   │   └── siap/             # diccionario, bitácora y municipal/*.csv.gz
│   ├── plata/
│   ├── cuarentena/
│   └── oro/
├── src/
│   ├── integracion.py        # lectura, homologación, agregación y fusión
│   ├── limpieza.py           # faltantes, atípicos, normalización, discretización, reducción
│   ├── calidad.py            # Puerta de Calidad (Pandera) y cuarentena
│   ├── pipeline.py           # orquesta todo el flujo
│   └── verificar_duplicados.py
├── docs/
│   ├── E1/
│   │   ├── limpieza.ipynb
│   │   └── ENTREGA.md
│   └── relatoria-E1.md
├── requirements.txt
└── README.md
```

## Requisitos e instalación

Python 3.10 o superior.

```powershell
pip install -r requirements.txt
```

## Cómo ejecutar el pipeline

Desde la raíz del repositorio (la carpeta que contiene `data/` y `src/`):

```powershell
python src\pipeline.py
```

El script imprime el resumen de cada paso y escribe los resultados en `data/plata/` y `data/cuarentena/`.

### Metadatos de los datos crudos

Cada archivo de datos crudos en `data/bronce/` tiene un sidecar junto al original,
con sufijo `.metadata.json` (por ejemplo, `cierre_2025.csv.gz.metadata.json`).
El hash SHA-256 se calcula sobre los bytes almacenados, incluido el archivo
comprimido. Las bitácoras, los archivos `robots.txt` guardados y `.gitkeep` no
se consideran lotes de datos. Los extractores actualizan el sidecar al guardar
una captura; para regenerarlos todos localmente y sin conexión:

```powershell
python src\metadatos.py
```

La suite unitaria también es offline y se ejecuta con:

```powershell
python -m unittest discover -s tests -v
```

## Pipeline de la E1

| Paso | Módulo | Qué hace |
|---|---|---|
| 1. Integración | `integracion.py` | Extrae la tabla de precios de cada HTML del SNIIM, lee los `.csv.gz` del SIAP, homologa nombres, tipos y estados, agrega el SNIIM a mes y estado, y lo une con el SIAP anual por (año, estado productor) |
| 2. Faltantes | `limpieza.py` | Diagnostica el mecanismo de los nulos e imputa con el último año publicado de cada estado, marcando cada valor imputado |
| 3. Atípicos | `limpieza.py` | Z-Score robusto (MAD) con ventana móvil sobre el precio diario; IQR informativo sobre el rendimiento del SIAP |
| 4. Normalización | `limpieza.py` | Columnas `*_minmax` y `*_z`, conservando los valores originales |
| 5. Discretización | `limpieza.py` | Niveles de precio (frecuencias iguales y anchura igual), niveles de producción y jerarquías temporal y geográfica |
| 6. Reducción | `limpieza.py` | Agregación (diario → mensual, municipal → estado-año) y eliminación de variables con correlación mayor a 0.95 |
| 7. Puerta de Calidad | `calidad.py` | Valida esquema y rangos con Pandera; los registros inválidos pasan a cuarentena con su motivo |

### Decisiones principales

- **Filtro de cultivo (SIAP):** se conservan `Limón` y `Limón real`. Se excluyen `Limonium` (flor) y `Té limón`.
- **Clave de unión:** año y estado **productor** (origen en el SNIIM). El precio queda mensual y la producción anual se repite en los 12 meses de su año.
- **Duplicados del SNIIM:** algunos HTML se traslapan en fechas. Los duplicados se **marcan** (`es_duplicado`), no se borran, y se excluyen al agregar.
- **Faltantes:** los nulos del SIAP corresponden únicamente a 2026 (rezago de publicación). El mecanismo es MAR de origen estructural, no MCAR. Se imputa con el último año publicado, porque el limón es un cultivo perenne cuya superficie y producción cambian poco entre años. Cada fila imputada lleva `siap_imputado` y `anio_dato_siap`.
- **Atípicos:** se marcan (`es_atipico`) y el valor se reemplaza por la mediana móvil en columnas `*_corr`; el valor original se conserva. Los errores lógicos (mínimo mayor que el frecuente, precios menores o iguales a cero) se marcan aparte como `precio_incoherente`.
- **Estadísticos de normalización del SIAP:** se calculan sobre filas únicas estado-año sin imputar, para no sobreponderar años repetidos en 12 meses.

## Salidas

Capa Plata (`data/plata/`):

| Archivo | Contenido |
|---|---|
| `sniim_diario_homologado.parquet` | SNIIM diario homologado, con banderas de duplicado, atípico e incoherencia |
| `siap_municipal_homologado.parquet` | SIAP municipal homologado (solo limón) |
| `integrado_sin_validar.parquet` | Integración mensual por estado, antes de imputar |
| `integrado_imputado.parquet` | Integración con los faltantes imputados |
| `integrado_transformado.parquet` | Con normalización, discretización y jerarquías |
| `integrado_reducido.parquet` | Tabla final tras la reducción de variables |
| `reporte_atipicos_sniim.csv` | Evidencia de atípicos e incoherencias detectados |
| `*_validado.parquet` | Registros que pasaron la Puerta de Calidad |

Cuarentena (`data/cuarentena/`): un CSV por fuente validada, con las columnas originales, `motivo`, `fuente`, `fecha_cuarentena` y un identificador idempotente para evitar duplicar filas al volver a ejecutar la validación.

## Puerta de Calidad

Se implementa con **Pandera** (`src/calidad.py`) y valida esquema y rangos de `sniim_diario_homologado.parquet` e `integrado_reducido.parquet`. La validación se ejecuta con `lazy=True` para reunir todos los fallos de una vez. Los registros válidos se guardan en `sniim_diario_validado.parquet` e `integrado_reducido_validado.parquet`. Las filas inválidas se conservan en `data/cuarentena/` con sus columnas originales y el motivo documentado; los registros archivados no se eliminan ni se duplican al repetir la ejecución. Se comprueba siempre que:

```
filas de entrada = filas en Plata + filas en cuarentena
```

La puerta se ejecuta al terminar `python src\pipeline.py`, o de forma independiente con `python src\calidad.py`. Las cotizaciones atípicas y duplicadas marcadas se conservan; las cotizaciones con `precio_incoherente=True` van a cuarentena. Las columnas normalizadas se validan por finitud, sin exigir el rango `[0, 1]` a columnas SIAP que pueden exceder el rango de referencia tras imputación.

## Limitaciones conocidas

- Colima aparece como estado de origen en el SNIIM solo desde febrero de 2024 y con pocas cotizaciones.
- La producción de 2026 es una aproximación (valor de 2025), marcada como imputada.
- El SNIIM cubre de noviembre de 2023 a octubre de 2026; el SIAP llega hasta 2025.

## Equipo

- Laura Naomi Alvarez Neri
- Gonzalo Fletes Vazquez 

Materia: Ingeniería de Datos. Docente: Armando Roman Gallardo Heredia.
Materia: Analisis Estadisticaos para la Ciencia de Datos. Docente: Monico Joel Sanchez Velasco