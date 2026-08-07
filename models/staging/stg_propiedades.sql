-- stg_propiedades: limpia 'divisa' y 'comuna', acota a RM
-- divisa: 'undefined' y 'undefinedconcentavos' son en realidad UF (a la 2da le falta dividir el precio por 100); se excluyen 2 outliers que no calzaron con ninguna hipótesis
-- comuna: nulos, 'None' y el error "Rm (metropolitana)" se rellenan desde direction; mayúsculas normalizadas
-- alcance: se acota a RM según la pregunta de negocio
-- Resultado esperado: 1760 filas, 215 UF / 1545 pesos, 28 comunas distintas de RM.

WITH divisa_procesada AS (
  SELECT
    *,
    CASE
      WHEN divisa IN ('undefined', 'undefinedconcentavos') THEN 'UF'
      ELSE 'pesos'
    END AS divisa_limpia,
    CASE
      WHEN divisa = 'undefinedconcentavos' THEN (precio / 100)
      ELSE precio
    END AS precio_limpio
  FROM `pipeline-inmobiliario-cso.raw.propiedades`
  WHERE NOT (divisa = 'undefined' AND precio > 200)
),

comuna_procesada AS (
  SELECT
    *,
    CASE
      WHEN comuna IS NULL OR comuna = 'None' OR REGEXP_CONTAINS(comuna, r'(?i)metropolitana')
        THEN TRIM(SPLIT(direction, ',')[SAFE_OFFSET(ARRAY_LENGTH(SPLIT(direction, ',')) - 1)])
      ELSE comuna
    END AS comuna_rellena
  FROM divisa_procesada
)

SELECT
  * EXCEPT (divisa, precio, comuna),
  REPLACE(REPLACE(REPLACE(
    INITCAP(comuna_rellena)
    , ' Del ', ' del ')
    , ' De ', ' de ')
    , ' La ', ' la ')
  AS comuna_final
FROM comuna_procesada
WHERE REGEXP_CONTAINS(region, r'(?i)^rm')