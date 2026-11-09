# Observatorio del Precio del Limón en Colima

Proyecto académico para recopilar y analizar precios al mayoreo del limón con
semilla, calibre 4 y calidad primera, junto con estadísticas municipales de
producción agrícola para apoyar la toma de decisiones en el sector citrícola.

## Estructura actual del repositorio

```text
observatorio-limon-colima/
├── .github/
│   └── workflows/
│       └── captura.yml                  # Captura automática semanal
├── calidad/
│   ├── defectos-Gonzalo.csv
│   ├── defectos-Naomi.csv
│   ├── tiempo-Gonzalo.csv
│   └── tiempo-Naomi.csv
├── data/
│   └── bronce/                          # Única capa de datos implementada
│       ├── siap/
│       │   ├── _bitacora.csv
│       │   ├── diccionario_datos_municipal.xlsx
│       │   └── municipal/
│       │       └── cierre_<año>.csv.gz
│       └── sniim/
│           ├── _bitacora.csv
│           ├── _robots_<fecha>.txt
│           └── limon_c_semilla_4_primera/
│               └── <fecha_inicio>_<fecha_fin>.html
├── docs/
│   └── E0/
│       ├── ENTREGA.md
│       └── propuesta.md
├── src/
│   ├── extractor.py                    # Archivo vacío, reservado
│   ├── siap_captura.py                 # Captura datos del SIAP
│   └── sniim_captura.py                # Captura consultas del SNIIM
├── .gitignore
├── README.md
└── requirements.txt
```

Los nombres entre `< >` representan patrones, no nombres literales. Bronce
conserva las respuestas de origen y las bitácoras de captura. SIAP guarda los
cierres anuales comprimidos sin pérdida; SNIIM guarda las respuestas HTML por
intervalo consultado.

## Estado de las capas de datos

El proyecto plantea una arquitectura tipo Medallion:

- **Bronce (`data/bronce/`): implementada.** Capturas originales y bitácoras.
- **Plata (`data/plata/`): pendiente.** No existe todavía; se destinará a
  extracción, limpieza, normalización y validación de los datos.
- **Oro (`data/oro/`): pendiente.** No existe todavía; se destinará a
  indicadores y agregaciones listos para análisis.

Por lo tanto, actualmente no hay scripts ni resultados de procesamiento en
Plata u Oro. `src/extractor.py` está vacío y no realiza transformaciones.

## Captura automática

El workflow de GitHub Actions (`.github/workflows/captura.yml`) se ejecuta cada
lunes a las 12:00 UTC, y también puede iniciarse manualmente. En cada ejecución:

1. Consulta los últimos 14 días de precios disponibles en SNIIM.
2. Comprueba SIAP e incorpora los años que aún no estén descargados.
3. Registra las capturas en `data/bronce/` y guarda los cambios en el
   repositorio cuando haya datos nuevos.

La captura histórica local incluye 36 periodos mensuales consecutivos
(noviembre de 2023 a octubre de 2026), además de registros recientes
actualizados al 7 de noviembre de 2026. La frecuencia de ejecución no implica
que las fuentes publiquen datos nuevos en cada consulta.

## Ejecución local

Instala las dependencias y ejecuta los capturadores desde la raíz del proyecto:

```bash
pip install -r requirements.txt
python src/sniim_captura.py --ultimos-dias 14
python src/siap_captura.py
```

Los capturadores también permiten consultar periodos históricos y forzar una
recaptura. Ejecuta `python src/sniim_captura.py --help` y
`python src/siap_captura.py --help` para ver sus opciones.

## Documentación y calidad

- `docs/E0/propuesta.md`: propuesta final de la entrega E0, con las preguntas
  de investigación E1, E2 y E3 y la arquitectura de datos.
- `docs/E0/ENTREGA.md`: estado y checklist de la entrega.
- `calidad/`: plantillas CSV para registrar tiempo y defectos de Naomi y
  Gonzalo.

Las preguntas de investigación del proyecto son:

- E1: precio promedio semanal del limón con semilla, calibre 4 y calidad
  primera en los mercados SNIIM.
- E2: evaluación del error de pronóstico al incorporar factores temporales,
  rezagos y variables anuales del SIAP.
- E3: comparación de grupos de municipios productores de México según
  producción, superficie cosechada y rendimiento.

Antes de redistribuir datos descargados o derivados, verifica las condiciones
de uso aplicables de cada fuente y respeta sus políticas de acceso.
