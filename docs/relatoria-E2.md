# Relatoría de la etapa E2

## Observatorio del precio del limón en Colima

**Responsable documental:** Integrante 2 — Ética, documentación y validación  
**Fecha:** 22 de noviembre de 2026

## 1. Actividades realizadas

Durante la sesión se realizaron las siguientes actividades:

1. Revisión de la implementación técnica de E2 en `src/`, `tests/`, `.github/` y `data/`.
2. Investigación de condiciones de uso y licencias de Open-Meteo, SIAP y SNIIM.
3. Revisión del `robots.txt` conservado para SNIIM y comprobación de rutas públicas.
4. Identificación de sesgos derivados de cobertura geográfica, rezago del SIAP, agregación y georreferenciación.
5. Revisión de privacidad y búsqueda de credenciales o datos personales.
6. Ejecución completa del pipeline Bronce → Plata → Oro.
7. Ejecución de las 13 pruebas unitarias.
8. Creación de la declaración ética, ficha de entrega y relatoría E2.

## 2. Tecnologías y procedimientos documentados

La documentación se enlazó con los módulos reales:

- captura climática y datos históricos de Open-Meteo;
- cálculo geoespacial Haversine;
- generación de las tablas Oro;
- matriz de linaje;
- validación Pandera;
- automatización semanal por GitHub Actions;
- pruebas unitarias de calidad, metadatos, geoespacialidad y linaje.

La ejecución se realizó desde Windows con PowerShell y Python. Los comandos y rutas se validaron con las convenciones del repositorio.

## 3. Dificultades y soluciones

### Disponibilidad de políticas explícitas

**Dificultad:** Las fuentes oficiales no exhibieron todas las licencias de manera uniforme. El sitio de datos no permitió una consulta directa desde el herramienta de acceso web y el SNIIM no publicó una licencia reutilizable específica en la página revisada.

**Solución:** Se documentó con precisión lo que sí fue verificable: términos generales de gob.mx, licencia CC BY 4.0 de Open-Meteo y límites de uso. Cuando no existió evidencia de una licencia específica, se indicó esta ausencia en lugar de asumirla.

### Resolución de rutas

**Dificultad:** Algunas rutas publicadas en la documentación podían diferir de la implementación después de combinar entregas anteriores.

**Solución:** Se verificó el árbol real del repositorio y se enlazaron los documentos con las rutas existentes. La ficha usa rutas relativas desde `docs/E2/` o rutas de repositorio claramente identificadas.

### Diferencias de granularidad y sesgos

**Dificultad:** SNIIM, SIAP y clima tienen frecuencias y extensiones espaciales distintas.

**Solución:** Se describieron las agregaciones utilizadas y se documentaron los límites. Los datos 2026 imputados se identifican con banderas, y las coordenadas se presentan como puntos representativos.

## 4. Resultados

El pipeline terminó de forma correcta. Los resultados verificables fueron:

- 137 filas en la serie mensual Oro;
- 174 filas en la tabla geoespacial Oro;
- 599 vínculos trazables en la matriz de linaje;
- 274 fechas de ingesta auditadas con 0 discrepancias;
- 13 pruebas unitarias aprobadas;
- 1 registro SNIIM aislado en cuarentena y ningún registro integrado rechazado.

Además, se creó la documentación ética y se completaron los entregables solicitados a la Integrante 2.

## 5. Aprendizajes

El trabajo mostró que la documentación técnica no puede separarse de la ingeniería ni de la legalidad:

- Los metadatos y hashes permiten auditar, pero no sustituyen una licencia.
- Las banderas de imputación son necesarias para evitar que aproximaciones se interpreten como observaciones reales.
- Las distancias Haversine son útiles, pero no representan rutas, peajes o costos reales de transporte.
- Los filtros estadísticos deben conservar originales y motivos para que el criterio pueda revisarse.
- Los repositorios académicos deben evitar afirmar permisos comerciales sin evidencia verificable.

## 6. Conclusiones

La documentación de E2 coincide con la implementación revisada y el pipeline produjo los productos esperados. Se cumplieron las responsabilidades de esta parte: declaración de ética y legalidad, ficha de entrega, relatoría y revisión documental.

Antes de una publicación comercial o masiva, deberán verificarse nuevamente términos vigentes, licencias y restricciones de las fuentes. Para el alcance académico actual, los datos agregados, las citas, los límites y las medidas de trazabilidad quedaron establecidos.
