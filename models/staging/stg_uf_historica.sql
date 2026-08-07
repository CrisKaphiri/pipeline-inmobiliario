-- stg_uf_historica: normaliza la serie UF, quedándose solo con la fecha (sin la hora fija que trae desde la API) y renombrando 'valor'
-- Resultado esperado: 1461 filas, sin nulos.

SELECT DATE(fecha) AS fecha, valor AS valor_uf
FROM `pipeline-inmobiliario-cso.raw.uf_historica`
ORDER BY fecha

