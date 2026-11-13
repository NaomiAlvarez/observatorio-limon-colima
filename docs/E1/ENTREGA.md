# Reporte de Entrega E1 — Observatorio del Precio del Limón en Colima

## Información General

* **Proyecto:** Observatorio del Precio del Limón en Colima
* **Entrega:** E1 (Limpieza, Preprocesamiento, Integración y Puerta de Calidad)
* **Rama Principal:** `main`
* **Tag de Entrega:** `e1`
* **Institución:** Tecnológico Nacional de México — Campus Colima
* **Asignaturas:** 
  * Ingeniería de Datos (Docente: Armando Román Gallardo Heredia)
  * Análisis Estadísticos para la Ciencia de Datos (Docente: Mónico Joel Sánchez Velasco)
* **Integrantes del Equipo:**
  * Laura Naomi Álvarez Neri
  * Gonzalo Fletes Vázquez

---

## Enlaces de Referencia en el Repositorio

| Recurso | Ruta en el Repositorio | Descripción |
| :--- | :--- | :--- |
| **Pipeline Orquestador** | [`src/pipeline.py`](../../src/pipeline.py) | Ejecución integral del flujo Bronce $\rightarrow$ Plata $\rightarrow$ Calidad |
| **Módulo de Integración** | [`src/integracion.py`](../../src/integracion.py) | Lectura, homologación y cruce de fuentes |
| **Módulo de Limpieza** | [`src/limpieza.py`](../../src/limpieza.py) | Faltantes, atípicos, normalización, discretización y reducción |
| **Puerta de Calidad** | [`src/calidad.py`](../../src/calidad.py) | Esquemas Pandera, validación estricta y cuarentena |
| **Verificación de Duplicados** | [`src/verificar_duplicados.py`](../../src/verificar_duplicados.py) | Análisis de traslape en descargas SNIIM |
| **Metadatos SHA-256** | [`src/metadatos.py`](../../src/metadatos.py) | Generación de sidecars de trazabilidad en Bronce |
| **Pruebas Unitarias** | [`tests/test_calidad.py`](../../tests/test_calidad.py) | Suite de pruebas de esquemas y conservación de filas |
| **Capa Plata (Parquet)** | [`data/plata/`](../../data/plata/) | Tablas limpias, homologadas y transformadas |
| **Cuarentena** | [`data/cuarentena/`](../../data/cuarentena/) | Registros rechazados con motivo documentado |
| **Evidencia de Atípicos** | [`data/plata/reporte_atipicos_sniim.csv`](../../data/plata/reporte_atipicos_sniim.csv) | Cotizaciones marcadas por filtro Hampel e incoherencias |
| **Relatoría del Proceso** | [`docs/relatoria-E1.md`](../relatoria-E1.md) | Bitácora PSP, tiempos, defectos y lecciones aprendidas |

---

## Lista de Verificación de Requerimientos (Checklist E1)

- [x] **Diagnóstico y tratamiento de valores faltantes:** Diagnóstico formal del mecanismo (MAR) e imputación justificada con último año publicado.
- [x] **Detección y tratamiento de atípicos y ruido:** Z-Score robusto (Hampel/MAD) sobre precios diarios, IQR sobre rendimiento agrícola y aislamiento de incoherencias.
- [x] **Normalización y estandarización:** Min-Max y Z-Score sobre variables continuas, con aislamiento muestral para evitar sesgos interanuales.
- [x] **Discretización y jerarquías conceptuales:** Doble discretización de precios (anchura vs. frecuencias iguales), terciles de producción y jerarquías temporal y geográfica.
- [x] **Reducción de datos:** Reducción por agregación temporal/espacial y selección de variables por colinealidad ($|r| > 0.95$).
- [x] **Integración de fuentes y resolución de conflictos:** Homologación léxica, resolución de alias, mapeo de entidades estatales y conciliación de granularidad.
- [x] **Puerta de calidad automática (Pandera):** Esquemas estrictos, validación de tipos, rangos y comprobaciones relacionales.
- [x] **Cuarentena y conservación de registros:** Aislamiento de inválidos con motivo documentado y cumplimiento estricto de la ecuación de conservación ($3,599 = 3,598 + 1$).
- [x] **Sidecars de trazabilidad (Bronce):** 64 archivos `.metadata.json` con hash SHA-256 y tamaño en bytes.
- [x] **Suite de pruebas automatizada:** Configuración `pytest.ini` y pruebas pasando al 100%.

---

## 1. Pipeline de Limpieza y Preprocesamiento

### 1.1. Diagnóstico y Tratamiento de Valores Faltantes

#### Diagnóstico del Mecanismo (MCAR vs. MAR vs. MNAR)
Al integrar la serie mensual del SNIIM con las estadísticas agrícolas del SIAP, se observó que el **32.1%** de los registros consolidados presentaban valores nulos en las columnas agrícolas (`sembrada_ha`, `cosechada_ha`, `produccion_ton`, `valor_produccion`, `precio_rural_kg`):

| Año | Total Filas | Filas con SIAP Faltante | % Faltante |
| :---: | :---: | :---: | :---: |
| 2023 | 4 | 0 | 0.0% |
| 2024 | 41 | 0 | 0.0% |
| 2025 | 48 | 0 | 0.0% |
| 2026 | 44 | 44 | **100.0%** |

* **Descarte de MCAR (Missing Completely at Random):** No es MCAR porque la probabilidad de ausencia no es uniforme entre observaciones. Depende de forma determinista del año de observación: $P(\text{Nulo} \mid \text{Año} \le 2025) = 0$, mientras que $P(\text{Nulo} \mid \text{Año} = 2026) = 1.0$.
* **Confirmación de MAR (Missing at Random):** El mecanismo es **MAR de origen estructural**, ya que la condición de faltante está condicionada exclusivamente por una variable observada en el conjunto de datos ($\text{Año} = 2026$) debido al ciclo oficial de publicación del SIAP (el cierre definitivo anual se publica al término del ciclo agrícola siguiente), y no por la magnitud o valor intrínseco de la producción no observada ($P(\text{Faltante} \mid \text{Producción}, \text{Año}=2026) = P(\text{Faltante} \mid \text{Año}=2026)$).
* **Descarte de MNAR (Missing Not at Random):** No es MNAR porque la falta del dato no se debe a que la cosecha haya sido atípicamente baja, nula o censurada deliberadamente por los productores.

#### Justificación Agronómica de la Imputación
Se implementó en `imputar_faltantes()` ([`src/limpieza.py`](../../src/limpieza.py)) una imputación mediante el último valor anual publicado por estado (año 2025):
1. **Inercia biológica del cultivo:** El limón mexicano (*Citrus aurantifolia*) es un cultivo leñoso perenne cuya entrada en producción comercial toma entre 3 y 5 años tras la siembra y mantiene una vida productiva de más de 15 años. A diferencia de cultivos cíclicos anuales (como el maíz o frijol), la superficie establecida y la capacidad productiva instalada varían menos del 3–5% entre años consecutivos en ausencia de desastres climatológicos catastróficos.
2. **Superioridad metodológica:** Imputar con la media o mediana global distorsionaría la asimetría regional (Michoacán produce más de 800,000 toneladas anuales frente a las 300,000 de Colima). El último año del propio estado preserva la escala real del sistema productivo.
3. **Trazabilidad estricta:** Para no inducir a falsas interpretaciones en el modelado posterior, cada registro imputado lleva la bandera booleana `siap_imputado = True` y el campo explícito `anio_dato_siap = 2025`.

---

### 1.2. Detección y Tratamiento de Valores Atípicos y Ruido

El pipeline aborda dos naturalezas distintas de datos: series temporales de alta volatilidad (precios diarios SNIIM) y registros transversales de corte agronómico (rendimiento SIAP).

#### Z-Score Robusto con Mediana Móvil (Filtro Hampel) en SNIIM
El precio del limón presenta una fuerte estacionalidad y picos transitorios. Un Z-Score clásico basado en media y desviación estándar se ve distorsionado por los propios atípicos (efecto de enmascaramiento). Se implementó el **Filtro Hampel** en `_hampel()` ([`src/limpieza.py`](../../src/limpieza.py)):

$$\tilde{x}_t = \text{mediana}(x_{t-k}, \dots, x_{t+k})$$
$$\text{MAD}_t = \text{mediana}(|x_{t-i} - \tilde{x}_t|)$$
$$z_{\text{robusto}} = 0.6745 \cdot \frac{|x_t - \tilde{x}_t|}{\text{MAD}_t}$$

* **Parámetros aplicados:** Ventana móvil centrada de 15 días ($k=7$), umbral $z > 3.5$, y comprobación de salto relativo mínimo ($> 10\%$).
* **Granularidad de aplicación:** Se evaluó por cada serie de mercado independiente (`origen_estado`, `presentacion`, `destino_mercado`).
* **Resultados:** De 3,480 cotizaciones diarias válidas no duplicadas, se identificaron **43 cotizaciones atípicas (1.2%)** (Michoacán: 29, Sinaloa: 13, Colima: 1).
* **Tratamiento no destructivo:** Los valores originales se preservan intactos en `precio_min`, `precio_max` y `precio_frec`. Se crearon columnas corregidas `precio_min_corr`, `precio_max_corr`, `precio_frec_corr` donde el valor atípico se sustituye por la mediana local, y se marca `es_atipico = True`.

#### Detección de Incoherencias Lógicas (Ruido Estructural)
Independientemente de la dispersión estadística, se identificó 1 cotización con error lógico evidente en origen:
* Cotización del 05/03/2025 (origen Colima, destino Cd. Obregón): $precio\_min = \$21.05 > precio\_frec = \$20.53$.
* Se clasificó bajo la bandera `precio_incoherente = True` y fue excluida de la agregación mensual y canalizada a cuarentena.

#### Rango Intercuartílico (IQR) en SIAP
Sobre los 15,081 registros de producción municipal del SIAP, se evaluó el rendimiento agrícola (`rendimiento_ton_ha`):
* $Q_1 = 6.15\text{ ton/ha}$, $Q_3 = 13.00\text{ ton/ha}$, $IQR = 6.85\text{ ton/ha}$.
* Límites Tukey ($1.5 \times IQR$): $[-4.12, 23.27]\text{ ton/ha}$.
* Se marcaron **444 registros (3.0%)** como `rendimiento_ton_ha_atipico = True` (rendimientos superiores a 23.27 ton/ha propios de agricultura tecnificada de riego intensivo). No se alteró su valor para no eliminar variabilidad real documentada.

---

### 1.3. Normalización y Estandarización de Variables Continuas

Se aplicó en `normalizar()` ([`src/limpieza.py`](../../src/limpieza.py)) tanto el escalamiento Min-Max como la estandarización Z-Score a las variables continuas:

| Variable | Tipo | Min-Max (`_minmax`) | Z-Score (`_z`) | Justificación Metodológica |
| :--- | :---: | :---: | :---: | :--- |
| `precio_frec_media` | Mensual | $[0, 1]$ | $\mu=0.0, \sigma=1.0$ | Permite comparación uniforme entre mercados de diferente costo de vida. |
| `precio_min`, `precio_max` | Mensual | $[0, 1]$ | $\mu=0.0, \sigma=1.0$ | Estandarización de bandas de fluctuación mensual. |
| `produccion_ton` | Anual | Escala $[0, 1]$ | $\mu=0.0, \sigma=1.0$ | Permite acoplar magnitudes de miles de toneladas con precios en pesos. |
| `valor_produccion` | Anual | Escala $[0, 1]$ | $\mu=0.0, \sigma=1.0$ | Homologa dimensiones macroeconómicas. |
| `precio_rural_kg` | Anual | Escala relativa | $\mu=0.0, \sigma=1.0$ | Facilita el análisis de margen entre precio en huerta y precio mayorista. |

> [!IMPORTANT]
> **Aislamiento muestral riguroso:** Las variables del SIAP son anuales y se repiten en los 12 meses de cada año en la tabla integrada. Calcular la media y desviación sobre las 137 filas mensuales sesgaría los estadísticos hacia los años con mayor número de mercados consultados e incorporaría los datos imputados de 2026. Por ello, los parámetros ($\min, \max, \mu, \sigma$) se calcularon **exclusivamente sobre registros únicos estado-año sin imputar** (`anual = df[~df["siap_imputado"]].drop_duplicates(["estado", "anio"])`), preservando la verdadera distribución poblacional.

---

### 1.4. Discretización y Jerarquías Conceptuales

Se implementó en `discretizar()` ([`src/limpieza.py`](../../src/limpieza.py)):

#### Discretización de Precios y Comparación Empírica
1. **Frecuencias iguales (`precio_nivel`):** Divide la serie en terciles exactos mediante `pd.qcut`:
   * Bajo: $[10.36, 17.50]\text{ MXN/kg}$ (46 registros).
   * Medio: $(17.50, 24.38]\text{ MXN/kg}$ (45 registros).
   * Alto: $(24.38, 48.42]\text{ MXN/kg}$ (46 registros).
2. **Anchura igual (`precio_rango`):** Divide el rango continuo en 3 intervalos de idéntica amplitud mediante `pd.cut`:
   * Bajo: $[10.32, 23.05]\text{ MXN/kg}$ (85 registros).
   * Medio: $(23.05, 35.73]\text{ MXN/kg}$ (46 registros).
   * Alto: $(35.73, 48.42]\text{ MXN/kg}$ (6 registros).
* **Hallazgo analítico:** La discretización por anchura igual evidencia la asimetría positiva (*right-skewness*) de los precios: los picos históricos altos son infrecuentes pero extremos, concentrando la mayor parte de las observaciones en el rango bajo.

#### Discretización de Producción Agrícola
* `produccion_nivel`: Cortes en terciles sobre filas únicas estado-año (`baja`, `media`, `alta`).

#### Jerarquías Conceptuales
* **Jerarquía Temporal:** $\text{mes} \ (1\text{--}12) \longrightarrow \text{trimestre} \ (1\text{--}4) \longrightarrow \text{semestre} \ (1\text{--}2) \longrightarrow \text{año} \ (2023\text{--}2026)$.
* **Jerarquía Geográfica:** $\text{estado} \longrightarrow \text{región} \ (\text{occidente, sur, noroeste, sureste}) \longrightarrow \text{país} \ (\text{mexico})$.

---

### 1.5. Reducción de Datos

Se implementó en `reducir()` ([`src/limpieza.py`](../../src/limpieza.py)) a través de dos mecanismos complementarios:

#### 1. Reducción por Agregación
* **SNIIM:** 3,599 registros diarios crudos $\longrightarrow$ 3,480 sin duplicados $\longrightarrow$ **137 filas mensuales consolidadas por estado**.
* **SIAP:** 15,081 filas municipales de limón $\longrightarrow$ **626 registros anuales a nivel estatal**.

#### 2. Reducción por Selección de Variables (Multicolinealidad)
Se evaluó la matriz de correlación de Pearson entre las variables continuas de producción:

| Variable | `produccion_ton` | `sembrada_ha` | `cosechada_ha` | `valor_produccion` |
| :--- | :---: | :---: | :---: | :---: |
| `produccion_ton` | 1.000 | **0.967** | **0.974** | 0.831 |
| `sembrada_ha` | **0.967** | 1.000 | **0.992** | 0.820 |
| `cosechada_ha` | **0.974** | **0.992** | 1.000 | 0.818 |
| `valor_produccion` | 0.831 | 0.820 | 0.818 | 1.000 |

* **Criterio de exclusión:** Umbral $|r| > 0.95$.
* **Decisión:** `sembrada_ha` ($r = 0.967$) y `cosechada_ha` ($r = 0.974$) presentan colinealidad casi perfecta con `produccion_ton`. Mantener las tres variables provocaría problemas de rango e inestabilidad numérica en modelos lineales de pronóstico.
* **Resultado:** Se eliminaron `sembrada_ha` y `cosechada_ha` (así como sus derivadas normalizadas), conservando `produccion_ton` (volumen físico) y `valor_produccion` (dimensión económica).

---

## 2. Integración y Resolución de Conflictos

El módulo `src/integracion.py` consolida las dos fuentes con esquemas y granularidades dispares:

1. **Resolución de esquemas heterogéneos:** A lo largo de los 23 años del SIAP (2003–2025), los nombres de columnas cambiaron repetidamente (`ano` vs `anio`, `volumenproduccion` vs `volumen_produccion`, `precio` vs `pmr`). Se construyó el mapa `ALIAS_SIAP` que estandariza automáticamente cualquier archivo histórico al esquema canónico.
2. **Normalización léxica y de formato:** Se aplicó `limpiar_texto()` (conversión a minúsculas, remoción de acentos mediante descomposición NFKD ASCII, reemplazo de espacios por guiones bajos y remoción de signos).
3. **Homologación de entidades federativas:** Se mapearon variaciones oficiales mediante `EQUIVALENCIAS_ESTADO` (ej. `"michoacan de ocampo" \longrightarrow "michoacan"`, `"veracruz de ignacio de la llave" \longrightarrow "veracruz"`).
4. **Filtro agronómico estricto:** El SIAP incluye registros de productos botánicamente distintos. Se filtraron estrictamente `Limón` y `Limón real`, excluyendo deliberadamente `Limonium` (planta ornamental) y `Té limón` (gramínea aromática).
5. **Conciliación de granularidad:** El SNIIM tiene frecuencia diaria por mercado mayorista; el SIAP tiene frecuencia anual por municipio. Se reconciliaron agregando SNIIM a promedio mensual por estado productor y SIAP a total anual por estado, fusionando bajo la clave compuesta `['anio', 'estado']`.

---

## 3. Puerta de Calidad Automática y Cuarentena (Pandera)

La puerta de calidad se implementó en `src/calidad.py` utilizando **Pandera**, ejecutada en modo perezoso (`lazy=True`) para capturar la totalidad de los fallos de esquema y reglas de negocio.

### Esquemas Validados
* **`ESQUEMA_SNIIM`:** 18 columnas validadas con `strict=True` sobre `sniim_diario_homologado.parquet`.
  * Comprobaciones de no nulidad, finitud, rangos ($precio > 0, anio \ge 2000$).
  * Comprobaciones relacionales: `precio_min <= precio_frec <= precio_max`, consistencia entre `fecha`, `anio` y `anio_mes`.
* **`ESQUEMA_INTEGRADO`:** 34 columnas validadas con `strict=True` sobre `integrado_reducido.parquet`.
  * Comprobaciones de rango: `mes` $\in [1, 12]$, `trimestre` $\in [1, 4]$, `semestre` $\in [1, 2]$, categorías permitidas en `region`, `precio_nivel`, `precio_rango`, `produccion_nivel`.
  * Restricciones relacionales: coherencia de fechas, cotizaciones $\ge$ atípicos, y coherencia temporal en imputación (`anio_dato_siap <= anio`).

### Principio de No Eliminación Silenciosa y Conservación de Filas
Se asegura matemáticamente en tiempo de ejecución:

$$\text{Filas de Entrada} = \text{Filas en Plata} + \text{Filas en Cuarentena}$$

* **SNIIM Diario:** 3,599 filas entraron $\longrightarrow$ **3,598 válidas** en `sniim_diario_validado.parquet` + **1 fila en cuarentena** en `data/cuarentena/sniim_diario.csv`.
* **Integrado Reducido:** 137 filas entraron $\longrightarrow$ **137 válidas** en `integrado_reducido_validado.parquet` + **0 en cuarentena**.

### Estructura de la Cuarentena
El registro rechazado no se descarta: se conserva en `data/cuarentena/sniim_diario.csv` agregando:
* `fuente`: Nombre del flujo emisor (`sniim_diario`).
* `fecha_cuarentena`: Marca temporal en formato ISO 8601 UTC.
* `registro_id`: Hash SHA-256 idempotente generado a partir del contenido de la fila, lo que evita duplicaciones si la validación se ejecuta múltiples veces.
* `motivo`: Descripción exacta de la regla violada: `orden_precios; precio_incoherente: equal_to(False)`.

---

## 4. Estructura de Productos Generados en Capa Plata

| Archivo | Formato | Registros | Descripción |
| :--- | :---: | :---: | :--- |
| `sniim_diario_homologado.parquet` | Parquet | 3,599 | Precios diarios con banderas `es_duplicado`, `es_atipico` y `precio_incoherente`. |
| `sniim_diario_validado.parquet` | Parquet | 3,598 | Cotizaciones que superaron la Puerta de Calidad. |
| `siap_municipal_homologado.parquet` | Parquet | 15,081 | Producción municipal histórica homologada con IQR en rendimiento. |
| `integrado_sin_validar.parquet` | Parquet | 137 | Cruce mensual inicial antes del tratamiento de valores faltantes. |
| `integrado_imputado.parquet` | Parquet | 137 | Tabla con imputación del 2026 y banderas de trazabilidad. |
| `integrado_transformado.parquet` | Parquet | 137 | Tabla con normalización (Min-Max/Z-Score) y jerarquías conceptuales. |
| `integrado_reducido.parquet` | Parquet | 137 | Tabla analítica final tras reducción de variables por colinealidad. |
| `integrado_reducido_validado.parquet` | Parquet | 137 | Producto Plata certificado por la Puerta de Calidad. |
| `reporte_atipicos_sniim.csv` | CSV | 44 | Registro auditable de cotizaciones anómalas e incoherentes. |
| `data/cuarentena/sniim_diario.csv` | CSV | 1 | Repositorio de aislamiento de registros inválidos con motivo documentado. |

---

## 5. Instrucciones de Reproducción y Verificación

Para reproducir localmente todo el flujo desde la raíz del repositorio:

```powershell
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la suite completa de pruebas unitarias
pytest -v

# 3. Regenerar metadatos SHA-256 de datos crudos (Bronce)
python src\metadatos.py

# 4. Ejecutar el pipeline de Limpieza, Integración y Calidad (Plata)
python src\pipeline.py

# 5. Ejecutar la Puerta de Calidad de forma independiente
python src\calidad.py
```

---

## Conclusión

El Entregable E1 cumple cabalmente con todos los requerimientos técnicos, estadísticos y de ingeniería de datos. El conjunto de datos resultante en la capa Plata se encuentra depurado, normalizado, reducido, enriquecido conceptualmente y rigurosamente certificado por la Puerta de Calidad, dejando la base preparada para el modelado y la construcción de la capa Oro en la fase E2.

