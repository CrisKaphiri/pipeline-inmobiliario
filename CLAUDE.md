# Pipeline Inmobiliario Chile

Pipeline de datos end-to-end (ELT) en Google Cloud Platform: extrae datos inmobiliarios sucios + la serie histórica de la UF (API mindicador.cl), los carga crudos a BigQuery, y los transforma con SQL por capas (staging → marts) para un dashboard en Power BI. Proyecto de portafolio para ingeniería/análisis de datos.

## Stack

- Lenguaje: Python 3.11+
- Cloud: Google Cloud Platform (Cloud Storage, BigQuery)
- SQL: BigQuery Standard SQL
- Visualización: Power BI (conector nativo a BigQuery)

## Comandos

- `source venv/bin/activate` — activa el entorno virtual
- `python src/01_extract.py` — extrae el CSV crudo + la serie UF desde la API
- `python src/02_load.py` — sube a Cloud Storage y carga a BigQuery (raw)
- El SQL de `models/staging/` y `models/marts/` se prueba primero en la consola de BigQuery, y una vez que funciona se guarda en el repo

## Estructura del proyecto

- `data/` — dataset crudo local (no se sube a GitHub)
- `notebooks/` — exploración rápida (opcional)
- `models/staging/` — limpieza y normalización (prefijo `stg_`)
- `models/marts/` — tablas finales de negocio (prefijo `fct_`/`dim_`)
- `src/` — scripts Python de extracción y carga

## Convenciones

- Es un pipeline ELT, no ETL: la limpieza va en SQL dentro de BigQuery, nunca en Python
- Archivos SQL con prefijo según capa: `stg_`, `fct_`, `dim_`
- snake_case para todo

## No hagas

- No subas credenciales de GCP ni archivos `.json` de service account al repo
- No hardcodees IDs de proyecto de GCP en el código — usa variables de entorno
- No cargues datos ya limpios a la capa `raw` — el dato crudo entra tal cual
- No uses `SELECT *` sin filtrar columnas — cuida el costo de BigQuery
- No corras el pipeline de carga sin el MERGE — evita duplicar datos si se corre dos veces

## Flujo de trabajo

- Antes de una tarea no trivial, proponme un plan y espera mi OK
- Una tarea a la vez; al terminar, dime qué cambiaste para que lo revise
- Si no estás seguro al 80%, pregunta. No inventes