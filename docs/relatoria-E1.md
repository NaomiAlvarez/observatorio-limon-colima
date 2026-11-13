# Relatoría de Proceso y Calidad (PSP) — Entregable E1

## Información General

* **Proyecto:** Observatorio del Precio del Limón en Colima
* **Fase:** Entregable E1 (Limpieza, Integración, Preprocesamiento y Puerta de Calidad)
* **Fecha de corte:** 13 de noviembre de 2026
* **Institución:** Tecnológico Nacional de México — Campus Colima
* **Integrantes del Equipo:**
  * Laura Naomi Álvarez Neri
  * Gonzalo Fletes Vázquez
* **Asignaturas:**
  * Ingeniería de Datos (Docente: Armando Román Gallardo Heredia)
  * Análisis Estadísticos para la Ciencia de Datos (Docente: Mónico Joel Sánchez Velasco)

---

## 1. Resumen Ejecutivo del Proceso Personal de Software (PSP)

Durante el ciclo de desarrollo del Entregable E1 se aplicaron de forma rigurosa las prácticas de medición del **Proceso Personal de Software (PSP)**, registrando de forma individualizada el esfuerzo temporal (`calidad/tiempo-<nombre>.csv`) y los defectos detectados y removidos (`calidad/defectos-<nombre>.csv`).

### Distribución de Esfuerzo por Fase (Minutos Netos)

| Integrante | Plan | ETL (Desarrollo) | Test (Pruebas) | Docs (Documentación) | Total Neto (min) | Total Horas |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Laura Naomi Álvarez Neri** | 135 | 490 | 105 | 110 | **840 min** | 14.0 h |
| **Gonzalo Fletes Vázquez** | 54 | 117 | 43 | 168 | **382 min** | 6.4 h |
| **Consolidado del Equipo** | **189 min (15.5%)** | **607 min (49.7%)** | **148 min (12.1%)** | **278 min (22.7%)** | **1,222 min** | **20.4 h** |

```
Distribución del Esfuerzo en E1:
[ETL / Desarrollo]   ████████████████████ 49.7%
[Documentación]      █████████ 22.7%
[Planeación]         ██████ 15.5%
[Pruebas / Calidad]  █████ 12.1%
```

---

## 2. Evaluación de los Objetivos de Calidad Medibles (PSP)

En la propuesta inicial (E0) se establecieron **3 objetivos cuantitativos de calidad**. A continuación se presenta su balance y cumplimiento al cierre de E1:

| Métrica PSP | Meta Definida en E0 | Resultado Obtenido en E1 | Estado |
| :--- | :---: | :---: | :---: |
| **1. Tiempo promedio de reparación de defectos** | $\le 30\text{ minutos por defecto}$ | **10.5 min / defecto** (en E1) | **CUMPLIDO** |
| **2. Defectos removidos en la misma fase o la siguiente** | $\ge 80\%\text{ mensual}$ | **88.9%** (8 de 9 defectos) | **CUMPLIDO** |
| **3. Porcentaje de tiempo neto de trabajo** | $\ge 85\%\text{ semanal}$ | **96.8%** | **CUMPLIDO** |

### Análisis Detallado de Métricas

#### Métrica 1: Tiempo Promedio de Reparación
* Durante la fase E1 se registraron defectos puntuales de integración, datos y entorno (ver sección 3).
* El tiempo de resolución en E1 fue altamente eficiente: la corrección de fallos en Pandera tomó 2 minutos, la adición de reglas para cotizaciones incoherentes tomó 15 minutos, y la configuración de `pytest.ini` tomó 5 minutos.
* Promedio en E1: $\frac{2 + 15 + 5}{3} = 7.3\text{ minutos}$, muy por debajo del límite máximo de 30 minutos.

#### Métrica 2: Fase de Inyección vs. Remoción de Defectos
* La mayoría de los defectos originados en la fase de **ETL** fueron detectados y removidos en la fase inmediata de **Test** (pruebas unitarias y ejecución del pipeline).
* 8 de los 9 defectos históricos se corrigieron en la fase de inyección o en la fase inmediata siguiente ($88.9\%$), evitando que los errores se propagaran a etapas tardías de entrega o documentación.

#### Métrica 3: Porcentaje de Tiempo Neto
* De 1,262 minutos brutos dedicados por ambos integrantes, únicamente se registraron 40 minutos en interrupciones o pausas no productivas.
* $\text{Tiempo Neto} = \frac{1,222}{1,262} = 96.8\%$, superando ampliamente el umbral meta del $85\%$.

---

## 3. Bitácora de Defectos Registrados y Acciones Correctivas

A continuación se detallan los defectos técnicos identificados durante la construcción y prueba de la fase E1:

| ID | Fecha | Integrante | Tipo | Inyectado | Removido | Tiempo Rep. | Descripción del Defecto y Solución Aplicada |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **D-05** | 2026-11-12 | Naomi | Datos | ETL | Test | 15 min | **Incoherencia en cotización SNIIM:** Se detectó una fila en Cd. Obregón donde $precio\_min > precio\_frec$. *Solución:* Se programó la bandera `precio_incoherente` para excluirla de la agregación mensual y canalizarla a la cuarentena de Pandera. |
| **D-06** | 2026-11-13 | Gonzalo | Codificación | ETL | Test | 2 min | **Duplicación de motivos en Pandera:** La extracción de `failure_cases` duplicaba mensajes globales por cada fila. *Solución:* Se agrupó la asociación de motivos por índice de fila en `validar_dataframe()`. |
| **D-07** | 2026-11-13 | Naomi | Entorno | Test | Test | 5 min | **Fallo de importación en `pytest`:** Al invocar `pytest` directamente, `src/` no estaba en `sys.path`. *Solución:* Se creó el archivo de configuración `pytest.ini` con `pythonpath = .`. |
| **D-08** | 2026-11-13 | Equipo | Entorno | ETL | Test | 3 min | **Ruta relativa en `verificar_duplicados.py`:** El script asumía ejecución desde la raíz y fallaba si se invocaba desde `src/`. *Solución:* Se cambió la ruta a absoluta mediante `Path(__file__).resolve().parent.parent`. |

---

## 4. Retos Técnicos y Decisiones de Ingeniería de Datos

1. **Heterogeneidad temporal y granularidad:**
   * *Problema:* El SNIIM reporta precios diarios por central de abasto, mientras que el SIAP reporta superficie y tonelaje anualmente por municipio.
   * *Decisión:* Para responder a la pregunta de investigación E1 sin crear falsas atribuciones espaciales, se consolidó el SNIIM a promedio mensual por estado productor (`origen_estado`) y el SIAP a total anual estatal. Esto resolvió el problema de escala conservando suficiente sensibilidad temporal.
2. **Tratamiento del rezago del SIAP en 2026 (MAR):**
   * *Problema:* El 32.1% del conjunto integrado carecía de datos agrícolas porque el SIAP aún no publica el cierre de 2026.
   * *Decisión:* Se demostró formalmente que el mecanismo es MAR (la ausencia depende del año 2026, no del volumen cosechado). Aprovechando la inercia agronómica del limón mexicano como cultivo perenne, se imputó con el año 2025 del respectivo estado y se crearon banderas explícitas (`siap_imputado`, `anio_dato_siap`) para que los modelos analíticos puedan distinguir entre datos observados y aproximados.
3. **Multicolinealidad en variables agrícolas:**
   * *Problema:* `sembrada_ha`, `cosechada_ha` y `produccion_ton` presentaron coeficientes de correlación mayores a 0.96.
   * *Decisión:* Con base en el criterio estadístico de reducción ($|r| > 0.95$), se eliminaron las hectáreas sembradas y cosechadas, conservando `produccion_ton` (volumen físico) y `valor_produccion` (valor económico). Esto previene matrices singulares y coeficientes inestables en regresiones posteriores.
4. **Validación estricta y cuarentena (Pandera):**
   * *Problema:* Evitar la eliminación silenciosa de datos anómalos o corruptos.
   * *Decisión:* Se implementó un esquema de validación perezosa (`lazy=True`) acoplado a un archivo de cuarentena persistente. Se garantiza la conservación total de registros ($3,599 = 3,598\text{ válidos} + 1\text{ en cuarentena}$) con identificadores idempotentes SHA-256.

---

## 5. Lecciones Aprendidas

1. **La importancia de los sidecars y metadatos:** Generar los archivos `.metadata.json` con SHA-256 en la capa Bronce permitió auditar la integridad de cada captura sin necesidad de reprocesar gigabytes de información.
2. **Normalización contextualizada:** No se debe normalizar ciegamente sobre tablas intermedias combinadas; haber aislado el cálculo de Min-Max y Z-Score sobre registros únicos de estado-año evitó que los años con más cotizaciones mayoristas distorsionaran los estadísticos poblacionales del campo agrícola.
3. **El valor del PSP en proyectos de datos:** Registrar los defectos en el momento en que ocurren permitió identificar que la mayor parte del tiempo se pierde en detalles de entorno y discrepancias de esquemas, lo que motivó la estandarización de `ALIAS_SIAP` y `pytest.ini`.

---

## 6. Acuerdos de Trabajo para el Entregable E2

1. **Capa Oro:** Construir las vistas agregadas y matrices de características con rezagos temporales (lags de 1, 2, 4 semanas) requeridas para la pregunta detonadora.
2. **Modelado y Experimentación:** Iniciar los experimentos de pronóstico evaluando el impacto de incorporar las variables anuales del SIAP junto con factores estacionales.
3. **Mantenimiento del PSP:** Continuar el registro diario de tiempos y defectos en los archivos de calidad correspondientes.

