-- Step 3.6 · List-price versions of SKUs used in the window (H-RAT-05).
-- Params : :start_date, :end_date   (end exclusive)
-- Read   : new_version_in_window = true near the onset -> rate effect candidate.
-- Limits : list price only. Contract discounts / DBCU are visible only in Azure
--          EffectivePrice and the contract.

WITH used AS (
  SELECT DISTINCT account_id, sku_name, usage_unit
  FROM system.billing.usage
  WHERE cloud = 'AZURE'
    AND usage_date >= CAST(:start_date AS DATE)
    AND usage_date <  CAST(:end_date   AS DATE)
)
SELECT
  p.sku_name,
  p.usage_unit,
  p.currency_code,
  p.price_start_time,
  p.price_end_time,
  p.pricing.default                                   AS published_price,
  p.pricing.effective_list.default                    AS effective_list_price,
  LAG(p.pricing.effective_list.default) OVER (
    PARTITION BY p.account_id, p.sku_name, p.usage_unit, p.currency_code
    ORDER BY p.price_start_time)                      AS previous_effective_price,
  p.price_start_time >= CAST(:start_date AS TIMESTAMP)
    AND p.price_start_time < CAST(:end_date AS TIMESTAMP) AS new_version_in_window
FROM system.billing.list_prices p
JOIN used u
  ON  u.account_id = p.account_id
  AND u.sku_name   = p.sku_name
  AND u.usage_unit = p.usage_unit
WHERE p.cloud = 'AZURE'
  AND p.price_start_time < CAST(:end_date AS TIMESTAMP)
  AND (p.price_end_time IS NULL OR p.price_end_time >= CAST(:start_date AS TIMESTAMP))
ORDER BY new_version_in_window DESC, p.sku_name, p.price_start_time;
