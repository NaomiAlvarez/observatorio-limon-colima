# Observatorio del Precio del Limón en Colima

Proyecto académico para recopilar y analizar precios al mayoreo del limón con
semilla y estadísticas municipales de producción agrícola, con enfoque en
Colima.

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

La frecuencia de ejecución no implica que las fuentes publiquen datos nuevos
en cada consulta.

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

- `docs/E0/propuesta.md`: propuesta de la entrega E0.
- `docs/E0/ENTREGA.md`: estado y checklist de la entrega.
- `calidad/`: plantillas CSV para registrar tiempo y defectos de Naomi y
  Gonzalo.

Antes de redistribuir datos descargados o derivados, verifica las condiciones
de uso aplicables de cada fuente y respeta sus políticas de acceso.
