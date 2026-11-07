-- Step 1.5 · Validate the historical list-price join (rule R7) BEFORE any modeled cost.
-- Params : :start_date, :end_date   (end exclusive)
-- Verdict: FAIL_DUPLICATE  -> any usage record matched > 1 price row (overcount risk)
--          FAIL_UNPRICED   -> > 1% of records have no price
--          PASS            -> SKU usable for modeled cost
-- If every SKU is unpriced, remove the account_id predicate (list_prices may carry a
-- different account_id in some tenants) and re-run.

WITH matches AS (
  SELECT
    u.record_id,
    u.sku_name,
    u.usage_unit,
    COUNT(p.price_start_time)                       AS price_matches
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
  GROUP BY u.record_id, u.sku_name, u.usage_unit
)
SELECT
  sku_name,
  usage_unit,
  COUNT(*)                                          AS records,
  COUNT_IF(price_matches = 0)                       AS unpriced_records,
  COUNT_IF(price_matches > 1)                       AS multi_matched_records,
  MAX(price_matches)                                AS max_matches,
  ROUND(COUNT_IF(price_matches = 0) / COUNT(*), 4)  AS unpriced_share,
  CASE WHEN COUNT_IF(price_matches > 1) > 0                 THEN 'FAIL_DUPLICATE'
       WHEN COUNT_IF(price_matches = 0) / COUNT(*) > 0.01   THEN 'FAIL_UNPRICED'
       ELSE 'PASS' END                              AS verdict
FROM matches
GROUP BY sku_name, usage_unit
ORDER BY verdict, records DESC;
