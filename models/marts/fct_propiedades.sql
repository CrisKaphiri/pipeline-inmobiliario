-- fct_propiedades: une stg_propiedades con la serie UF (join por fecha de published).
-- convierte todo a precio en UF, y agrega ranking + promedio de precio por comuna.
-- Resultado esperado: 1760 filas, 28 comunas, ranking mín. 1 por comuna.

SELECT
  id,
  comuna_final AS comuna,
  DATE(published) AS fecha_publicacion,
  precio_uf,
  superficie_util,
  RANK() OVER (PARTITION BY comuna_final ORDER BY precio_uf) AS ranking_precio_comuna,
  AVG(precio_uf) OVER (PARTITION BY comuna_final) AS precio_promedio_comuna
FROM (
  SELECT
    p.*,
    CASE
      WHEN p.divisa_limpia = 'UF' THEN p.precio_limpio
      ELSE p.precio_limpio / uf.valor_uf
    END AS precio_uf
  FROM `pipeline-inmobiliario-cso.staging.stg_propiedades` AS p
  LEFT JOIN `pipeline-inmobiliario-cso.staging.stg_uf_historica` AS uf
    ON DATE(p.published) = uf.fecha
)