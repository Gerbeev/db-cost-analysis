-- Step 6 · PB-SERVERLESS / PB-AI-APPS / PB-FEATURES · Monthly usage and modeled cost by
--          product, SKU, serverless flag and performance target.
-- Params : :start_date, :end_date   (end exclusive)
-- Read   : serverless share trend; products that appear or step up (predictive optimization,
--          monitoring, serving, vector search, apps, networking ...).
-- Limits : list price (R1); units differ per product - compare quantity only within a unit.

SELECT
  DATE_FORMAT(u.usage_date, 'yyyy-MM')                                  AS month,
  COALESCE(u.billing_origin_product, 'UNKNOWN')                         AS product,
  u.sku_name,
  u.usage_unit,
  u.product_features.is_serverless                                      AS is_serverless,
  u.product_features.performance_target                                 AS performance_target,
  COUNT(DISTINCT u.workspace_id)                                        AS workspaces,
  ROUND(SUM(u.usage_quantity), 4)                                       AS net_quantity,
  COALESCE(p.currency_code, 'UNPRICED')                                 AS currency_code,
  ROUND(SUM(u.usage_quantity * p.pricing.effective_list.default), 2)    AS list_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices p
  ON  p.account_id = u.account_id
  AND p.cloud      = u.cloud
  AND p.sku_name   = u.sku_name
  AND p.usage_unit = u.usage_unit
  AND u.usage_start_time >= p.price_start_time
  AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
WHERE u.cloud = 'AZURE'
  AND u.usage_date >= CAST(:start_date AS DATE)
  AND u.usage_date <  CAST(:end_date   AS DATE)
  AND (u.product_features.is_serverless = TRUE
       OR u.billing_origin_product NOT IN ('JOBS', 'ALL_PURPOSE', 'INTERACTIVE', 'SQL', 'DLT'))
GROUP BY ALL
ORDER BY product, sku_name, month;
