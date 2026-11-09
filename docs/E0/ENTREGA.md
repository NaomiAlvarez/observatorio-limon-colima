# Reporte de Entrega E0 — Observatorio del Precio del Limón en Colima

## Información General

* **Proyecto:** Observatorio del Precio del Limón en Colima
* **Entrega:** E0 (Propuesta y Pipeline Inicial)
* **Rama Principal:** `main`
* **Tag de Entrega:** `e0` (pendiente de crear sobre la versión final confirmada)
* **Integrantes:**
  * Naomi Álvarez Neri
  * Gonzalo Fletes Vázquez

---

## Enlaces de Referencia en el Repositorio

| Recurso | Ruta en el Repositorio |
| :--- | :--- |
| **Documento Maestro (Propuesta)** | [`docs/E0/propuesta.md`](propuesta.md) |
| **Workflow de GitHub Actions** | [`.github/workflows/captura.yml`](../../.github/workflows/captura.yml) |
| **Script de Captura SNIIM** | [`src/sniim_captura.py`](../../src/sniim_captura.py) |
| **Script de Captura SIAP** | [`src/siap_captura.py`](../../src/siap_captura.py) |
| **Datos Crudos (Bronce)** | [`data/bronce/`](../../data/bronce/) |
| **Registros PSP (Calidad)** | [`calidad/`](../../calidad/) |

---

## Lista de Verificación de Requerimientos (Checklist E0)

### 1. Entorno de Trabajo y Versionado
- [x] Repositorio `observatorio-limon-colima` configurado en GitHub.
- [x] Trabajo en ramas secundarias (`Rama-Naomi`) y fusión exitosa mediante Pull Request a `main`.
- [ ] Tag `e0` creado y publicado para la versión final de la entrega.

### 2. Extracción de Datos (ETL Bronce)
- [x] Extractor `src/sniim_captura.py` desarrollado y ejecutado para obtener 36 periodos mensuales históricos consecutivos (noviembre de 2023–octubre de 2026), además de capturas recientes actualizadas al 7 de noviembre de 2026; las capturas constan como exitosas en la bitácora local.
- [x] Extractor `src/siap_captura.py` desarrollado y ejecutado para obtener datos anuales de producción municipal (2003–2025).
- [x] Archivos descargados y respaldados en `data/bronce/` con bitácoras de trazabilidad (URL, fecha y SHA-256).

### 3. Automatización (CI/CD)
- [x] Workflow `.github/workflows/captura.yml` configurado con disparadores manuales (`workflow_dispatch`) y programados (`schedule/cron`); el cron está programado para los lunes a las 12:00 UTC.
- [x] Ejecución exitosa verificada en GitHub Actions: las ejecuciones manuales [#5](https://github.com/NaomiAlvarez/observatorio-limon-colima/actions/runs/42424539141) en `main` y [#6](https://github.com/NaomiAlvarez/observatorio-limon-colima/actions/runs/42424744813) en `Rama-Gonzalo` finalizaron correctamente el 7 de noviembre de 2026.

### 4. Propuesta y Análisis Contextual
- [x] Análisis ético de fuentes y revisión de `robots.txt` para SNIIM y SIAP.
- [x] Entrevista de 15 minutos documentada con cinco preguntas explícitas y aprendizajes.
- [x] Redacción de las tres preguntas conforme a los objetivos E1 (precio semanal del limón con semilla, calibre 4 y calidad primera), E2 (factores a experimentar) y E3 (comparación de municipios productores de México).
- [x] Arquitectura de datos descrita bajo el modelo Medallion, distinguiendo Bronce implementada y Plata/Oro planeadas, aún no implementadas.
- [x] Ficha del observatorio con sector, región, pregunta detonadora y cliente potencial.

### 5. Calidad y Proceso Personal de Software (PSP)
- [x] Archivos `calidad/tiempo-<nombre>.csv` y `calidad/defectos-<nombre>.csv` creados e inicializados por cada integrante.
- [x] Definición de 3 objetivos de calidad medibles: tiempo de reparación, defectos removidos en la misma fase o la siguiente y porcentaje de tiempo neto.

## Pendientes para cerrar la entrega

1. Revisar y aprobar la versión final, crear el tag `e0` sobre el commit aprobado y publicarlo en el repositorio remoto.