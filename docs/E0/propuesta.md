# Propuesta de Proyecto: Observatorio del Precio del Limón en Colima

## 1. Ficha del Proyecto

* **Nombre del Proyecto:** Observatorio del Precio del Limón en Colima
* **Organización / Institución:** Tecnológico Nacional de México - Campus Colima
* **Sector:** Agrícola, específicamente producción y comercialización de limón con semilla.
* **Región:** Estado de Colima, con énfasis en Tecomán y los municipios productores; los precios se consultan para los mercados y destinos disponibles en SNIIM.
* **Pregunta detonadora:** ¿Cómo pueden los productores y comerciantes de limón de Colima usar el historial de precios al mayoreo y producción agrícola para planear y negociar con mayor información?
* **Cliente potencial:** Productores, empaques, comercializadores y organizaciones agrícolas de Colima.
* **Repositorio en GitHub:** `observatorio-limon-colima`
* **Rama principal:** `main`
* **Integrantes del Equipo:**
  * Laura Naomi Álvarez Neri
  * Gonzalo Fletes Vázquez
* **Fecha de Entrega:** Lunes, 9 de noviembre de 2026

---

## 2. Definición del Problema y Justificación

El limón con semilla en Colima representa uno de los pilares agrícolas y económicos más importantes de la región. Sin embargo, los productores y comerciantes enfrentan una alta volatilidad en los precios al mayoreo, influenciada por factores de temporalidad, volumen de cosecha municipal e intermediación en centrales de abasto.

El **Observatorio del Precio del Limón** busca integrar datos diarios de precios (SNIIM) y reportes de producción agrícola municipal (SIAP) para ofrecer una plataforma centralizada de análisis, visibilidad histórica y apoyo en la toma de decisiones para el sector cítrico.

---

## 3. Entrevista al Sector Citrícola

* **Entrevistado:** Don Miguel Ángel Preciado (Productor de limón con semilla en Tecomán, Colima – 22 años de experiencia)
* **Entrevistadores:** Equipo del Observatorio del Precio del Limón
* **Fecha y Duración:** Domingo, 8 de noviembre de 2026 (15 minutos)
* **Modalidad:** Llamada telefónica

### Transcripción

#### [Minutos 0:00 - 3:00] Presentación y contexto general

**Equipo:** Don Miguel, muchas gracias por su tiempo. Somos estudiantes y estamos desarrollando un proyecto universitario llamado *Observatorio del Precio del Limón en Colima*. Nuestro objetivo es cruzar los datos históricos de producción del SIAP con los precios al mayoreo del SNIIM. Queremos entender primero: ¿cómo percibe usted la dinámica de los precios en el día a día?

**Don Miguel:** Hola, qué tal. Me parece excelente lo que hacen, porque aquí el limón es un sube y baja. Mira, el precio del limón no se decide en la huerta, se decide en los empaques y en las centrales de abasto como la de la Ciudad de México, Guadalajara o Monterrey. Nosotros entregamos la fruta al empaque o al intermediario ("coyote"), y el precio te lo marcan dependiendo de cómo amaneció el mercado en la madrugada.

#### [Minutos 3:00 - 7:00] Factores de variación y temporalidad (Cruce con SNIIM)

**Equipo:** Vemos en los datos del SNIIM que hay temporadas con picos de precio muy altos y luego caídas drásticas. ¿Qué factores locales causan estos brincos?

**Don Miguel:** Principalmente la oferta y el clima. Entre enero y marzo la producción local baja porque el árbol amarra menos fruta por el frío relativo y el ciclo natural. Si a eso le sumas que en esos meses Michoacán o Veracruz también traen baja producción, el precio al mayoreo se dispara a niveles históricos. En cambio, entre junio y agosto, cuando entra el pico fuerte de cosecha en Colima, hay sobreoferta y el precio se nos cae.

También está el factor del **HLB (Dragón Amarillo)** y el costo de los insumos. Combatir la plaga y fertilizar hoy cuesta el doble que hace unos años. A veces el precio en la central de abasto parece alto, pero al productor le queda muy poco margen por los costos de corte y flete.

#### [Minutos 7:00 - 11:00] Calidad, clasificación y producción (Cruce con SIAP)

**Equipo:** El SIAP registra hectáreas cosechadas y tonelaje anual, pero no distingue calidades. ¿Cómo afecta la calidad de la fruta al precio real que recibe el productor?

**Don Miguel:** Es clave. El mercado paga por calidad y tamaño. El limón se clasifica por calibres (Primera, Segunda, Tercera y Colima/Industrial). El SNIIM reporta generalmente el precio de caja de primera o calidad media al mayoreo. Pero en campo, si tu huerta tiene problemas de trips o ácaros, la piel del limón se mancha. Ese limón "manchado" se va a la industria juguera por un centavo de lo que vale el limón empacado para mesa. Por eso los datos de rendimiento por hectárea del SIAP hay que leerlos con cuidado: muchas toneladas no significan necesariamente muchas ganancias si la calidad fue baja.

#### [Minutos 11:00 - 15:00] Utilidad de la herramienta y cierre

**Equipo:** Si tuvieran una plataforma que analice 36 meses de precios del SNIIM junto con la producción del SIAP, ¿de qué le serviría a un productor o comerciante en Colima?

**Don Miguel:** Nos serviría para **planear**. Si el productor sabe históricamente en qué semanas exactas el precio tiende a alcanzar su punto más alto, puede ajustar su plan de fertilización y podas para forzar la floración y tener fruta lista en esa ventana de tiempo. También nos ayuda a negociar con más información y no a ciegas con los compradores.

**Equipo:** Si tuvieran una plataforma que analice 36 meses de precios del SNIIM con la producción del SIAP, ¿de qué le serviría al sector citrícola?

**Don Miguel:** Nos serviría para planear. Si sabemos en qué semanas exactas el precio alcanza su punto más alto, podemos programar fertilizaciones y podas para tener fruta lista en esa ventana. Nos daría información para negociar mejor.

**Equipo:** Don Miguel, le agradecemos enormemente su tiempo e información. Será de gran valor para justificar nuestras preguntas de investigación en la propuesta del proyecto.

**Don Miguel:** De nada, mucho éxito con el proyecto. Ojalá compartan los resultados con la comunidad agrícola cuando lo terminen.

### Aprendizajes de la entrevista

1. **Fijación de precios:** El precio recibido en la huerta está influido por empaques, intermediarios y centrales de abasto, y puede variar con las condiciones del mercado.
2. **Estacionalidad y factores externos:** El entrevistado reporta menor producción local entre enero y marzo y mayor oferta entre junio y agosto; también menciona clima, producción de otros estados, HLB e insumos como factores relevantes.
3. **Calidad frente a volumen:** El SIAP no distingue calidades comerciales; el volumen producido no equivale por sí solo al ingreso del productor.
4. **Uso esperado:** Un historial de precios podría apoyar la planeación y negociación, aunque no garantiza precios futuros ni sustituye la evaluación agronómica.

La transcripción contiene cinco preguntas explícitas del equipo y los aprendizajes anteriores resumen las respuestas y su relevancia para el proyecto.

---

## 4. Preguntas de Investigación

### E1: Variable a pronosticar
> **¿Cuál será el precio promedio semanal (MXN/kg) del limón con semilla # 4, calidad Primera, reportado por el SNIIM en los mercados consultados, durante las próximas cuatro semanas?**

**Variable objetivo:** precio promedio semanal en MXN/kg por mercado. Se usarán los últimos 36 meses disponibles como serie histórica; el periodo exacto y los mercados incluidos deberán anotarse al construir el conjunto analítico.

### E2: Factores a experimentar
> **¿Cómo cambia el error de pronóstico del precio promedio semanal al incorporar, de forma individual y conjunta, factores temporales (mes y semana del año), precios rezagados y variables anuales del SIAP (producción, superficie cosechada y rendimiento municipal)?**

Los factores se evaluarán mediante comparación de modelos con y sin cada variable, manteniendo el mismo periodo de evaluación. Producción, superficie y rendimiento son anuales; su disponibilidad no debe presentarse como una medición semanal ni interpretarse como evidencia causal.

### E3: Grupos multivariados a comparar
> **¿Qué diferencias existen entre grupos de municipios de Colima definidos conjuntamente por producción, superficie cosechada y rendimiento, en sus perfiles agrícolas anuales según el SIAP (2003–2025)?**

Los grupos se formarán a partir de esas variables normalizadas y se compararán por sus perfiles y evolución anual. Los precios SNIIM corresponden a mercados y no se atribuirán directamente a un municipio sin una fuente que sustente esa relación.

---

## 5. Plan de Datos

### 5.1. Propósito y Alcance
El proyecto integra precios de mercado del limón y estadísticas de producción agrícola para analizar su evolución en Colima y sus municipios. La frecuencia descrita corresponde a la captura configurada en el proyecto.

### 5.2. Arquitectura de Datos (Medallion)
* **Bronce (`data/bronce/`):** Implementada. Conserva las respuestas descargadas (HTML SNIIM y CSV SIAP comprimidos sin pérdida), el diccionario SIAP y bitácoras con URL, fecha, resultado y huella SHA-256.
* **Plata (`data/plata/`):** Planeada, aún no implementada. Se destinará a extracción, limpieza, normalización de fechas y claves geográficas, validación y tratamiento explícito de valores faltantes.
* **Oro (`data/oro/`):** Planeada, aún no implementada. Se destinará a indicadores agregados y tablas analíticas con unidad, periodo y método documentados.

### 5.3. Fuentes de Información

| Fuente | Datos Utilizados | Frecuencia Configurada | Periodicidad de los Datos |
| :--- | :--- | :--- | :--- |
| **SNIIM** | Precios de limón con semilla, calidad primera, por mercado consultado. | GitHub Actions corre cada lunes a las 12:00 UTC y consulta los últimos 14 días. Hay una captura histórica local de 36 periodos mensuales consecutivos, de noviembre de 2023 a octubre de 2026. | La publicación depende del SNIIM; las consultas recientes pueden recuperar actualizaciones o correcciones. |
| **SIAP** | Producción agrícola, superficie cosechada y rendimiento anual municipal; cierres disponibles de 2003 a 2025 y diccionario. | El workflow revisa la fuente cada lunes; el capturador omite archivos de años ya existentes e incorpora años nuevos disponibles. | Anual |

### 5.4. Calidad y Trazabilidad
La validación de esquemas, rangos numéricos y valores faltantes se realizará en Plata, que aún no está implementada. Los faltantes se conservarán como tales, sin reemplazarlos por ceros. En Bronce, las bitácoras permiten rastrear la URL, fecha, resultado y SHA-256 de las capturas.

### 5.5. Análisis Ético y robots.txt
* **SNIIM:** El `robots.txt` consultado publica restricciones para `/Analisis/`, `/2010/`, rutas `Sicia` y archivos `.xls`; el capturador consulta el archivo y detiene la descarga si la ruta no está permitida. Usa un User-Agent que identifica al proyecto y una pausa de dos segundos entre solicitudes.
* **SIAP:** La consulta a `https://nube.agricultura.gob.mx/robots.txt` respondió HTTP 404. La ausencia de `robots.txt` no constituye una licencia ni autorización legal. El portal remite a los [Términos y condiciones de gob.mx](https://www.gob.mx/terminos); antes de redistribuir archivos o derivados se deben verificar las condiciones específicas aplicables a los datos. El capturador se identifica con User-Agent y espera tres segundos entre descargas.
* **Compromisos:** Consultar solo las rutas y conjuntos necesarios, respetar cualquier cambio de política, limitar la frecuencia, conservar atribución y procedencia, detenerse ante bloqueos o errores reiterados y no recopilar ni inferir datos personales. Los resultados deben explicar cobertura y limitaciones.

---

## 6. Objetivos de Calidad (PSP)

Para asegurar la calidad del software y la gestión del proyecto, se establecen las siguientes 3 métricas objetivas:

| Métrica | Cálculo | Meta |
| :--- | :--- | :--- |
| **Tiempo promedio de reparación** | Suma de `TiempoReparacion(min)` ÷ Total de defectos reparados | $\le 30 \text{ min por defecto (mensual)}$ |
| **Defectos removidos en fase posterior** | `(Defectos con FaseRemovido > FaseInyectado ÷ Total de defectos) × 100` | $\le 20\% \text{ mensual}$ *(Fases: Plan → ETL → Test → Docs)* |
| **Porcentaje de tiempo neto** | `(Suma de TiempoNeto(min) ÷ Suma de tiempo transcurrido) × 100` | $\ge 85\% \text{ semanal}$ |