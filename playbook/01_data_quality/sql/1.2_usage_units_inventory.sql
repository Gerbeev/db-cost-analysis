-- Step 1.4 · Inventory of products, SKUs, usage types and units.
-- Params : :start_date, :end_date   (end exclusive)
-- Rule   : quantities are comparable only within one usage_unit (DBU, TOKEN, GB, HOUR, ...).
--          Net quantity includes signed corrections.

SELECT
  DATE_FORMAT(usage_date, 'yyyy-MM')                AS month,
  billing_origin_product                            AS product,
  sku_name,
  usage_type,
  usage_unit,
  product_features.is_serverless                    AS is_serverless,
  COUNT(*)                                          AS records,
  ROUND(SUM(usage_quantity), 4)                     AS net_usage_quantity,
  COUNT_IF(record_type <> 'ORIGINAL')               AS correction_records
FROM system.billing.usage
WHERE cloud = 'AZURE'
  AND usage_date >= CAST(:start_date AS DATE)
  AND usage_date <  CAST(:end_date   AS DATE)
GROUP BY ALL
ORDER BY product, sku_name, usage_unit, month;
