# Entrega Integrante 1 — Unidad 3, Actividad E1
## Análisis Estadístico y Caracterización de la Serie de Tiempo

- **Proyecto:** Observatorio del Precio del Limón en Colima
- **Integrante 1:** Naomi Alvarez
- **Fecha:** 28 de noviembre de 2026
- **Notebook principal (ejecutado con gráficas y salidas):** `docs/U3-E1/analisis_series_tiempo.ipynb`
- **Figuras generadas:** `evidencias/U3E1/` (7 gráficos PNG)

---

## 1. Datasets preparados para el Integrante 2

Todos los archivos están limpios, ordenados cronológicamente y con **0 valores faltantes** y **0 duplicados**:

| Archivo | Dimensiones | Uso sugerido |
|---|---|---|
| `data/series_tiempo/serie_colima_univariada.csv` | 33 filas × 2 cols | Modelos ARIMA / SARIMA |
| `data/series_tiempo/serie_colima_multivariada.csv` | 33 filas × 10 cols | Exploración ARIMAX / SARIMAX con clima |
| `data/series_tiempo/panel_5_estados.csv` | 131 filas × 12 cols | Chequeos de robustez o modelos de panel |

---

## 2. Variable objetivo y frecuencia

- **Variable objetivo:** `precio_frec_media` (precio mayorista frecuente del limón con semilla en MXN/kg, promedio mensual SNIIM).
- **Columna de fecha:** `anio_mes` (exportada como `fecha` en formato `YYYY-MM-DD`).
- **Frecuencia:** Mensual, inicio de mes (`MS`).
- **Estado focal:** Colima (Tecomán).
- **Cobertura:** Febrero 2024 – Octubre 2026 (**33 observaciones**, sin huecos).
- **Estadísticos base:** Media = 22.516 $/kg · Mediana = 21.050 $/kg · DE = 4.688 $/kg · CV = 20.8 % · Mín = 15.790 $/kg (oct 2025) · Máx = 36.009 $/kg (sep 2024) · Asimetría = 1.667 · Shapiro-Wilk p < 0.001 (no normal).

---

## 3. Descomposición (elección justificada)

- **Modelo elegido:** **Multiplicativo** (`period=12`).
- **Justificación:** La dispersión crece con el nivel de la serie (Spearman entre media móvil y desviación móvil de 6 meses: **ρ = 0.626, p = 0.0004**; en 2024 la media fue 25.22 con DE 6.72, mientras que en 2025 fue 19.89 con DE 1.88) y el residuo multiplicativo expresado en $/kg presenta menor desviación estándar (**4.606 $/kg** frente a **4.729 $/kg** del aditivo).
- **Hallazgos:** Tendencia entre 20.02 y 29.35 $/kg (cambios de nivel, sin tendencia sostenida). Factores estacionales pico en **agosto (+14.2 %)** y **septiembre (+16.3 %)** y valle en **febrero (−10.3 %)**, aunque el patrón no se repite de forma estable entre los 3 años.

---

## 4. Prueba de estacionariedad (ADF) y diferenciación

| Prueba | Estadístico | p-valor | Crítico 5 % | Conclusión |
|---|---:|---:|---:|---|
| **ADF (constante `c`)** | **−3.3209** | **0.0140** | −2.9605 | Rechaza H₀ al 5 % → **Estacionaria** (no al 1 %, crítico −3.6614) |
| **ADF (constante + tendencia `ct`)** | −3.5245 | 0.0368 | −3.5630 | Limítrofe (rechaza al 10 %, crítico −3.2153; p-valor < 0.05) |
| **KPSS (confirmación, H₀: estacionaria)** | 0.1245 | ≥ 0.10 | 0.4630 | No rechaza H₀ → **Estacionaria** |
| **ADF sobre Δ1 (solo referencia)** | −3.8091 | 0.0028 | −2.9605 | No se usa para evitar sobrediferenciación |

- **Número de diferenciaciones recomendado:** **`d = 0`**. No se aplica diferenciación porque la serie original ya es estacionaria en media según ADF y KPSS.

---

## 5. Interpretación de ACF y PACF (parámetros ARIMA / SARIMA)

Calculadas hasta el rezago 15 (banda 95 % PACF = ±0.3412):

- **ACF:** Significativa solo en el **rezago 1 (+0.7502)**; luego decae de forma oscilante (negativa en rezagos 4–7). **Rezago 12 = −0.1801 (no significativo)**.
- **PACF:** Significativa en el **rezago 1 (+0.7502)** y **rezago 2 (−0.4989)**, con corte abrupto a partir del rezago 3. **Rezago 12 = −0.1661 (no significativo)**.
- **Recomendación para el Integrante 2:**
  - **Modelo base sugerido:** **`ARIMA(2, 0, 0)` con constante** (en verificación orientativa obtiene el menor AIC = **165.23** y BIC = **171.22**, con φ₁ = 1.1294, φ₂ = −0.4942 y residuos que pasan Ljung-Box: p = 0.868 en lag 6 y p = 0.965 en lag 10).
  - **Alternativas a comparar:** `ARIMA(1, 0, 1)` (AIC 168.25) y `ARIMA(2, 0, 1)` (AIC 167.06).
  - **Componente estacional (SARIMA):** El rezago 12 no es significativo en ACF ni PACF; no hay respaldo estadístico para términos `(P, D, Q)`. Si se prueban, deben justificarse con validación fuera de muestra.

---

## 6. Correlación cruzada con clima (Open-Meteo)

- **Correlación contemporánea (Colima, Pearson):**
  - Precio – Temperatura media: **r = +0.1207 (p = 0.5035)** → no significativa.
  - Precio – Precipitación: **r = +0.1963 (p = 0.2735)** → no significativa.
  - Panel de 5 estados (n = 131): tampoco significativa (temp. media r = +0.0703, p = 0.4246; precipitación r = +0.1546, p = 0.0779).
- **CCF sin preblanqueo (banda 95 % = ±0.3412):**
  - *Temperatura:* rezagos significativos en **k = 5 (−0.4020)** y **k = 6 (−0.4241)**.
  - *Precipitación:* ningún rezago significativo (máximo k = 1 con +0.2928).
- **CCF con preblanqueo Box-Jenkins (AR(2), banda 95 % = ±0.3520):**
  - **Temperatura:** **0 rezagos significativos** (`[]`).
  - **Precipitación:** **0 rezagos significativos** (`[]`).
- **Conclusión para modelado:** La señal en rezagos 5–6 de temperatura era **espuria** (producto de la autocorrelación del precio y el ciclo anual térmico). Con estos datos no hay evidencia para incluir clima en ARIMAX; si se prueba, debe ser solo de forma exploratoria y validado fuera de muestra. **Correlación no implica causalidad.**

---

## 7. Limitaciones documentadas

1. Serie corta (**33 meses**, 2.75 ciclos anuales): reduce potencia de ADF/KPSS y dificulta confirmar estacionalidad anual.
2. Meses parciales: febrero 2024 y octubre 2026 tienen solo **4 cotizaciones** (junio 2024, 7).
3. Tramos con precio constante real: mayo–septiembre 2025 (21.05 $/kg) y agosto–octubre 2026 (20.53 $/kg), con 20–23 cotizaciones reales por mes (no imputados).
4. Episodio extremo agosto–noviembre 2024 (atípicos IQR altos) domina la tendencia y la relación dispersión-nivel.
5. Clima puntual (Tecomán) y producción SIAP anual/imputada en 2026 (`siap_imputado`).
