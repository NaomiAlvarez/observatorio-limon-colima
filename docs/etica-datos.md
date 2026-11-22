# Declaración de ética, legalidad y privacidad de datos

**Proyecto:** Observatorio del Precio del Limón en Colima  
**Entrega:** E2  
**Fecha de revisión:** 22 de noviembre de 2026

## 1. Alcance

Este proyecto integra datos públicos del mercado mayorista de limón, estadísticas agrícolas, datos agroclimáticos y coordenadas geoespaciales para fines académicos de análisis e ingeniería de datos. La declaración cubre las fuentes utilizadas en las etapas Bronce, Plata y Oro y las medidas adoptadas para su uso responsable.

## 2. Fuentes y régimen de uso

| Fuente | Uso en el proyecto | Licencia o condición identificada | Atribución y medidas |
|---|---|---|---|
| SNIIM, Secretaría de Economía | Cotizaciones diarias al mayoreo | Sitio público del Gobierno de México; se aplicaron los términos generales de gob.mx y la política de privacidad publicada por el SNIIM. No se encontró en el sitio consultado una licencia reutilizable específica para las tablas extraídas. | Uso académico y no comercial; conservación de URL, fecha de captura y SHA-256. No se atribuye un supuesto permiso comercial más amplio que el identificado. |
| SIAP/DGSIAP, Secretaría de Agricultura | Producción agrícola municipal y estatal | Datos públicos gubernamentales. Se aplican los términos generales de gob.mx. No se encontró una licencia de datos específica en la captura realizada. | Uso académico; reproducción controlada desde archivos Bronce; exclusión de cultivos no coincidentes con limón. |
| Open-Meteo Historical Weather API | Temperatura y precipitación por zona citrícola | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) para los datos de API; términos de uso para uso no comercial y límites de llamadas. | Menos de 10,000 solicitudes diarias; atribución y enlace a Open-Meteo en documentación y visualizaciones. |
| Catálogo geoespacial propio | Coordenadas aproximadas de municipios y centrales de abasto; cálculo Haversine | Coordenadas seleccionadas para representar zonas o instalaciones, sin atribuir a ellas mediciones exactas de campo. | Se documenta que son puntos representativos y no ubicaciones personales o censadas. |

Revisiones consultadas:

- Términos generales de gob.mx: <https://www.gob.mx/terminos>
- Política de privacidad del SNIIM: <http://www.economia-sniim.gob.mx/PPrivacidadSNIIM.pdf>
- Términos de Open-Meteo: <https://open-meteo.com/en/terms>
- Licencia de Open-Meteo: <https://open-meteo.com/en/licence>
- Datos y servicios DGSIAP: <https://www.gob.mx/agricultura/dgsiap>

Las condiciones y licencias deben volver a revisarse antes de publicar derivados comercialmente o aumentar el volumen de captura.

## 3. Revisión de robots.txt

Se conservó una copia del `robots.txt` correspondiente en `data/bronce/sniim/_robots_20261116.txt`. La revisión vigente durante la captura indicó, entre otras restricciones:

- Bloqueos para `/Analisis/`, `/Sicia/`, `/Sicia2/`, `/SiciaAnt/` y archivos `.xls`.
- No se encontró una regla que desautorizara explícitamente las rutas HTML capturadas por el proyecto.
- Una consulta directa a `/SNIIM-Nacional/robots.txt` respondió 404 el 22 de noviembre de 2026.

La política aplicada fue de capturas limitadas y voluntariamente espaciadas para evitar sobrecarga. El extractor SNIIM guarda bitácora de URLs y respuestas HTTP. Esta revisión no sustituye el criterio jurídico ni autoriza usos comerciales.

## 4. Sesgos identificados y mitigación

| Sesgo o limitación | Impacto posible | Mitigación aplicada |
|---|---|---|
| Cobertura geográfica incompleta | Colima apareció como origen principalmente a partir de febrero de 2024 y Yucatán contó con una sola observación mensual integrada. | Se presentan conteos por estado, se conserva el origen y no se hacen inferencias nacionales sin advertir la cobertura. |
| Rezago de publicación del SIAP | Los datos de 2026 no están disponibles y se aproximan con el cierre de 2025. | Imputación explícita con bandera `siap_imputado=True` y `anio_dato_siap=2025`; exclusión de esos datos para estadísticos poblacionales no imputados. |
| Agregación de escalas | El SNIIM es diario por mercado y el SIAP es anual por municipio. | Se agrega SNIIM por mes y estado; SIAP por estado-año. No se afirma una relación causal individual. |
| Sesgo de supervivencia o publicación | Solo se observan cotizaciones disponibles públicamente y capturadas en períodos descargables. | Se conservan HTML Bronce, fechas de captura y hashes; se documentan rangos cubiertos. |
| Sesgo de atípicos | Los filtros técnicos pueden etiquetar variaciones reales como anómalas o dejar pasar fallos contextuales. | Se conserva el valor original, se marca `es_atipico`, se corrige solo en una columna derivada y se deja evidencia en CSV. |
| Representatividad geográfica aproximada | Una coordenada municipal puede no representar todas las huertas del estado; una central puede no representar rutas reales. | Se usa Haversine como distancia simplificada y se describe como geodésica, no como distancia recorrida ni costo real de transporte. |
| Sesgo temporal de captura | Los documentos descargados pueden solaparse entre rangos. | Los duplicados se marcan y excluyen de agregaciones; el registro original se conserva en Bronce y Plata. |

## 5. Privacidad y protección de datos

Las fuentes contienen datos agregados de mercados y producción; no incluyen nombres de productores ni datos personales de compradores. Los archivos no contienen claves API ni credenciales. Las coordenadas corresponden a municipios o centrales públicas.

Medidas implementadas:

- No se solicita, almacena ni publica información personal.
- Se excluyen datos personales potenciales de las tablas analíticas.
- Los scripts no contienen credenciales; el acceso a Open-Meteo usa únicamente el endpoint público.
- Las bitácoras conservan URL, fecha, tamaño y hash, sin datos personales.
- Los resultados se publican a nivel agregado.
- Los registros inválidos se conservan en cuarentena con identificadores derivados del contenido, no con datos personales.

## 6. Uso responsable y límites

Los resultados no deben interpretarse como asesoría financiera, pronóstico comercial garantizado ni evaluación individual de productores. Las decisiones públicas o comerciales deberán contrastarse con fuentes oficiales vigentes. Antes de un uso comercial, difusión masiva o automatización intensiva, el equipo debe revisar nuevamente las licencias, términos de uso y límites de las APIs.
