-- Step 5.6 · First appearance of products / SKUs (feature enablement, new workload types).
-- Params : :start_date, :end_date   (end exclusive)
-- Scans all retained history up to :end_date so that first_seen is real (bounded by retention).
-- Read   : new_in_window = true with first_seen near the onset -> PB-FEATURES / PB-AI-APPS /
--          PB-SERVERLESS candidate. Confirm enablement actor/time in 6.14 or account console.

SELECT
  COALESCE(billing_origin_product, 'UNKNOWN')         AS product,
  sku_name,
  usage_unit,
  product_features.is_serverless                      AS is_serverless,
  MIN(usage_date)                                     AS first_seen,
  MAX(usage_date)                                     AS last_seen,
  COUNT(DISTINCT usage_date)                          AS active_days,
  COUNT(DISTINCT workspace_id)                        AS workspaces,
  ROUND(SUM(usage_quantity), 4)                       AS net_quantity_to_end,
  MIN(usage_date) >= CAST(:start_date AS DATE)        AS new_in_window
FROM system.billing.usage
WHERE cloud = 'AZURE'
  AND usage_date < CAST(:end_date AS DATE)
GROUP BY ALL
ORDER BY new_in_window DESC, first_seen DESC;
