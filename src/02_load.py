import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery, storage

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROPIEDADES_CSV = DATA_DIR / "clean_alquiler_02_11_2023cc.csv"
UF_HISTORICA_CSV = DATA_DIR / "uf_historica.csv"

DATASET = "raw"
LOCATION = "southamerica-west1"
ARCHIVOS = [  # (ruta local, destino en el bucket, nombre de tabla en BigQuery)
    (PROPIEDADES_CSV, "raw/propiedades.csv", "propiedades"),
    (UF_HISTORICA_CSV, "raw/uf_historica.csv", "uf_historica"),
]
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 2

logger = logging.getLogger(__name__)


def subir_a_gcs(
    path: Path,
    blob_name: str,
    bucket_name: str,
    storage_client: storage.Client,
    max_retries: int = MAX_RETRIES,
    backoff_base: int = BACKOFF_BASE_SECONDS,
) -> str:
    bucket = storage_client.bucket(bucket_name)  # apunta al bucket
    blob = bucket.blob(
        blob_name
    )  # 'blob' = el archivo dentro del bucket, todavía no existe
    uri = f"gs://{bucket_name}/{blob_name}"

    for intento in range(1, max_retries + 1):
        try:
            blob.upload_from_filename(str(path))  # sube el contenido real
        except GoogleAPIError as e:  # equivalente a requests.RequestException
            logger.warning(
                "Intento %d/%d falló al subir %s a %s: %s",
                intento,
                max_retries,
                path,
                uri,
                e,
            )
            if intento < max_retries:  # no esperar después del último intento
                time.sleep(backoff_base**intento)
        else:
            logger.info(
                "Subido %s (%d bytes) a %s", path.name, path.stat().st_size, uri
            )
            return uri  # éxito -> corta el loop y la función acá mismo

    raise RuntimeError(f"No se pudo subir {path} a {uri} tras {max_retries} intentos")


def cargar_a_bigquery(
    uri: str,
    table_name: str,
    dataset: str,
    project_id: str,
    location: str,
    bq_client: bigquery.Client,
    max_retries: int = MAX_RETRIES,
    backoff_base: int = BACKOFF_BASE_SECONDS,
) -> int:
    table_id = f"{project_id}.{dataset}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # salta la fila de encabezados del CSV
        autodetect=True,  # BigQuery adivina los tipos de columna (solo)
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # reemplaza la tabla en vez de duplicar filas
    )

    for intento in range(1, max_retries + 1):
        try:
            job = bq_client.load_table_from_uri(
                uri, table_id, job_config=job_config, location=location
            )
            job.result()  # bloquea hasta que el job termine o falle
        except GoogleAPIError as e:
            logger.warning(
                "Intento %d/%d falló al cargar %s en %s: %s",
                intento,
                max_retries,
                uri,
                table_id,
                e,
            )
            if intento < max_retries:
                time.sleep(backoff_base**intento)
        else:
            tabla = bq_client.get_table(
                table_id
            )  # vuelve a preguntar los metadatos ya cargados
            logger.info(
                "Cargadas %d filas en %s desde %s", tabla.num_rows, table_id, uri
            )
            return tabla.num_rows

    raise RuntimeError(
        f"No se pudo cargar {uri} en {table_id} tras {max_retries} intentos"
    )


def main() -> None:
    load_dotenv()  # lee .env y lo mete como variables de entorno
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    project_id = os.environ["GCP_PROJECT_ID"]  # datos de .env
    bucket_name = os.environ["GCS_BUCKET_NAME"]

    storage_client = storage.Client(
        project=project_id
    )  # conexión autenticada a Storage
    bq_client = bigquery.Client(project=project_id)  # conexión autenticada a BigQuery

    for path, blob_name, table_name in ARCHIVOS:  # desempaqueta cada tupla de ARCHIVOS
        uri = subir_a_gcs(path, blob_name, bucket_name, storage_client)
        cargar_a_bigquery(uri, table_name, DATASET, project_id, LOCATION, bq_client)


if __name__ == "__main__":
    main()
