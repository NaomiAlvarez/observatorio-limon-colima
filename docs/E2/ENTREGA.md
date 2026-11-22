# Ficha de entrega E2

## Observatorio del precio del limón en Colima

- **Etapa:** E2 — Fuente especializada, capa Oro y linaje
- **Fecha de cierre:** 22 de noviembre de 2026
- **Institución:** Tecnológico Nacional de México — Campus Colima
- **Asignaturas:** Ingeniería de Datos y Análisis Estadísticos para la Ciencia de Datos
- **Integrantes:** Laura Naomi Álvarez Neri y Gonzalo Fletes Vázquez

## 1. Objetivo de la etapa

Integrar una fuente especializada agroclimática, enriquecer los registros con información geoespacial y construir una capa Oro trazable desde los datos crudos hasta las tablas analíticas. La entrega también incluye una revisión ética y documental de las fuentes utilizadas.

## 2. Fuente especializada integrada

Se integró la API histórica de Open-Meteo para incorporar:

- temperatura media;
- temperatura mínima;
- temperatura máxima;
- precipitación acumulada.

Los datos se capturan por coordenadas representativas de Colima, Michoacán, Guerrero, Sinaloa y Yucatán. Se homologaron a nivel mensual y se anexaron a la tabla integrada por estado y mes. Open-Meteo se utiliza bajo CC BY 4.0 y se atribuye en este documento y en la documentación pública.

## 3. Tecnologías, herramientas y procedimientos

| Componente | Implementación |
|---|---|
| Lenguaje | Python 3.12 en GitHub Actions y entorno local |
| Datos tabulares | pandas y PyArrow/Parquet |
| Validación | Pandera con validación estricta y lazy |
| Captura SNIIM | `src/sniim_captura.py` y archivos HTML |
| Captura SIAP | `src/siap_captura.py` y archivos CSV.GZ |
| Captura climática | `src/clima_captura.py` y JSON de Open-Meteo |
| Geoespacial | `src/geoespacial.py`, coordenadas representativas y Haversine |
| Capa Oro | `src/oro.py` |
| Orquestación | `src/pipeline.py` |
| Automatización | `.github/workflows/captura.yml` |
| Pruebas | `unittest` y suite pytest |

Procedimiento Bronce → Plata → Oro:

1. Captura o uso de archivos crudos en `data/bronce/`.
2. Homologación e integración SNIIM, SIAP y clima.
3. Limpieza, imputación, normalización y reducción.
4. Validación Pandera y cuarentena de registros inválidos.
5. Construcción de tablas Oro mensual y geoespacial.
6. Construcción de matriz de linaje extremo a extremo.
7. Comprobación de fechas de ingesta y ejecución de pruebas.

## 4. Productos generados

| Producto | Ruta | Evidencia |
|---|---|---|
| Clima diario homologado | `data/plata/clima_diario_homologado.parquet` | 5 estados; 5,530 días procesados por el pipeline |
| Serie mensual Oro | `data/oro/oro_serie_mensual_observatorio.parquet` | 137 filas, 55 columnas |
| Mercados geoespacial Oro | `data/oro/oro_mercados_geoespacial.parquet` | 174 filas, 24 columnas |
| Matriz de linaje | `data/oro/oro_linaje_matriz.parquet` | 599 vínculos |
| Matriz de linaje CSV | `data/oro/oro_linaje_matriz.csv` | Versión inspeccionable |
| Declaración ética | `docs/etica-datos.md` | Términos, licencias, sesgos y privacidad |

Rutas principales del código:

- Captura climática: [`src/clima_captura.py`](../../src/clima_captura.py)
- Georreferenciación y Haversine: [`src/geoespacial.py`](../../src/geoespacial.py)
- Construcción de Oro: [`src/oro.py`](../../src/oro.py)
- Orquestador completo: [`src/pipeline.py`](../../src/pipeline.py)
- Pruebas de linaje: [`tests/test_linaje.py`](../../tests/test_linaje.py)
- Pruebas geoespaciales: [`tests/test_geoespacial.py`](../../tests/test_geoespacial.py)

## 5. Evidencias y resultados reales

Ejecución completa realizada el 22 de noviembre de 2026:

- 41 archivos HTML SNIIM procesados y 3,635 registros diarios iniciales.
- 139 registros duplicados marcados.
- 43 atípicos Hampel (1.2%) y 1 registro incoherente.
- 15,081 registros municipales SIAP de `Limón` y `Limón real`.
- 444 registros con rendimiento IQR atípico marcados.
- 137 filas mensuales integradas.
- 44 filas de 2026 con producción SIAP imputada con datos de 2025.
- 3,634 de 3,635 filas SNIIM aprobadas por calidad; 1 en cuarentena.
- 137 de 137 filas integradas aprobadas.
- 137 filas Oro mensual validadas.
- 274 fechas de ingesta revisadas y 0 discrepancias.
- 599 vínculos Bronce → Plata → Oro en la matriz de linaje.

Pruebas unitarias ejecutadas:

```powershell
python -m unittest discover -s tests -v
```

Resultado: **13 pruebas ejecutadas, todas aprobadas**.

## 6. Verificación documental

Se verificaron las rutas mencionadas en esta ficha y en el repositorio. No se encontraron credenciales, API keys ni secretos personales en `src/`, `.github/`, `docs/` o `README.md` durante la revisión. Los archivos contienen datos agregados y públicos.

La ficha distingue:

- datos observados;
- datos imputados;
- datos marcados como atípicos;
- datos rechazados en cuarentena;
- distancias aproximadas derivadas de coordenadas representativas.

Para reproducir la entrega desde la raíz:

```powershell
pip install -r requirements.txt
python src\pipeline.py
python -m unittest discover -s tests -v
```

## 7. Conclusiones

La etapa E2 quedó integrada y reproducible: una fuente especializada amplió las variables ambientales, la georreferenciación permitió calcular distancias geodésicas y la capa Oro conserva trazabilidad por origen, archivo, fecha de ingesta y SHA-256. Los límites metodológicos y legales quedaron documentados. Las principales limitaciones son el rezago 2026 del SIAP, la cobertura desigual del SNIIM y el carácter representativo de las coordenadas geoespaciales.
