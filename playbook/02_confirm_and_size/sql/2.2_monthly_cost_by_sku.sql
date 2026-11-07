-- Step 2.1 (Databricks side) · Monthly modeled cost by workspace / product / SKU.
-- Params : :start_date, :end_date   (end exclusive; use full months)
-- Contract: column names are the input contract of ../scripts/analyze_costs.py --databricks.
--           Export the full result (no UI row limit) as CSV without renaming columns.
-- Limits : historical effective list price, NOT Azure invoiced cost (R1).
--          unpriced_records > 0 -> modeled cost incomplete for that row (R7).

WITH priced AS (
  SELECT
    DATE_FORMAT(u.usage_date, 'yyyy-MM')                          AS month,
    u.account_id,
    u.workspace_id,
    COALESCE(u.billing_origin_product, 'UNKNOWN')                 AS product,
    u.sku_name,
    COALESCE(p.currency_code, 'UNPRICED')                         AS currency_code,
    u.usage_unit,
    u.usage_quantity,
    u.usage_quantity * p.pricing.effective_list.default           AS list_cost,
    CASE WHEN p.pricing.effective_list.default IS NULL THEN 1 ELSE 0 END AS unpriced
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
)
SELECT
  month, account_id, workspace_id, product, sku_name, currency_code, usage_unit,
  ROUND(SUM(usage_quantity), 6)   AS net_usage_quantity,
  ROUND(SUM(list_cost), 6)        AS estimated_list_cost,
  SUM(unpriced)                   AS unpriced_records,
  COUNT(*)                        AS billing_records
FROM priced
GROUP BY ALL
ORDER BY month, account_id, workspace_id, product, sku_name, currency_code;
