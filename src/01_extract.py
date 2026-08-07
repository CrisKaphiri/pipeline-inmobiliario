import logging
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROPIEDADES_CSV = DATA_DIR / "clean_alquiler_02_11_2023cc.csv"
UF_HISTORICA_CSV = DATA_DIR / "uf_historica.csv"
UF_API_URL = "https://mindicador.cl/api/uf/{year}"
UF_YEARS = range(2020, 2024)
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 2

logger = logging.getLogger(__name__)


def extraer_propiedades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)  # lee el CSV en la ruta indicada
    logger.info("Propiedades leídas desde %s: %d filas, %d columnas", path, *df.shape)
    return df


def _es_formato_valido(data: dict) -> bool:
    serie = (
        data.get("serie") if isinstance(data, dict) else None
    )  # get 'serie' solo si data es un diccionario
    if (
        not isinstance(serie, list) or not serie
    ):  # Si no es lista o si está vacía, return False
        return False
    return all(
        isinstance(item, dict) and "fecha" in item and "valor" in item for item in serie
    )  # True solo si TODOS los items tienen 'fecha' y 'valor'


def fetch_uf_year(
    year: int,
    session: requests.Session,
    max_retries: int = MAX_RETRIES,
    backoff_base: int = BACKOFF_BASE_SECONDS,
) -> list[dict]:
    url = UF_API_URL.format(year=year)  # arma la URL con el año real
    for intento in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()  # explota si el código HTTP es de error
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning(
                "Intento %d/%d falló para año %d: %s", intento, max_retries, year, e
            )
        else:
            if _es_formato_valido(data):
                return data["serie"]  # éxito -> corta el loop y la función acá mismo
            logger.warning(
                "Intento %d/%d: formato inesperado en la respuesta para año %d",
                intento,
                max_retries,
                year,
            )

        if intento < max_retries:  # no esperar después del último intento
            espera = backoff_base**intento  # 2, 4, 8... segundos
            time.sleep(espera)

    # se agotaron los intentos sin éxito
    logger.error(
        "No se pudo obtener la serie UF del año %d tras %d intentos", year, max_retries
    )
    raise RuntimeError(f"Fallo al obtener la serie UF del año {year}")


def extraer_uf_historica(years: range, session: requests.Session) -> pd.DataFrame:
    registros = []  # acá se van juntando los diccionarios de todos los años
    for year in years:
        registros.extend(
            fetch_uf_year(year, session)
        )  # trae la lista del año y la agrega
    df = pd.DataFrame(registros)  # lista de diccionarios -> tabla
    return df.sort_values("fecha", ascending=True).reset_index(
        drop=True
    )  # orden cronológico


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    extraer_propiedades(PROPIEDADES_CSV)

    with requests.Session() as session:
        uf_df = extraer_uf_historica(UF_YEARS, session)

    uf_df.to_csv(UF_HISTORICA_CSV, index=False)
    logger.info("Serie UF guardada en %s (%d filas)", UF_HISTORICA_CSV, len(uf_df))


if __name__ == "__main__":
    main()
