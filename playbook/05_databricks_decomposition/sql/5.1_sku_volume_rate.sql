-- Step 5.1 · Product / SKU delta between baseline B and comparison C, split into
--            volume effect and (list) rate effect. Per-day normalized.
-- Params : :base_start, :base_end, :cmp_start, :cmp_end   (end exclusive)
-- Identity: delta_cost_per_day = volume_effect + rate_effect   (docs/03 §4)
-- Read   : rank by delta_cost_per_day; change_class NEW/GONE = new or removed SKU usage;
--          GONE on one SKU + NEW on another for the same workload = MIX_SHIFT.
-- Limits : list prices (R1). Rows with currency_code = 'UNPRICED' carry quantity only.

WITH params AS (
  SELECT DATEDIFF(CAST(:base_end AS DATE), CAST(:base_start AS DATE)) AS days_b,
         DATEDIFF(CAST(:cmp_end  AS DATE), CAST(:cmp_start  AS DATE)) AS days_c
),
usage_priced AS (
  SELECT
    CASE WHEN u.usage_date >= CAST(:base_start AS DATE) AND u.usage_date < CAST(:base_end AS DATE) THEN 'B'
         WHEN u.usage_date >= CAST(:cmp_start  AS DATE) AND u.usage_date < CAST(:cmp_end  AS DATE) THEN 'C'
    END                                                       AS period,
    COALESCE(u.billing_origin_product, 'UNKNOWN')             AS product,
    u.sku_name,
    u.usage_unit,
    u.product_features.is_serverless                          AS is_serverless,
    COALESCE(p.currency_code, 'UNPRICED')                     AS currency_code,
    u.usage_quantity                                          AS qty,
    u.usage_quantity * p.pricing.effective_list.default       AS cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices p
    ON  p.account_id = u.account_id
    AND p.cloud      = u.cloud
    AND p.sku_name   = u.sku_name
    AND p.usage_unit = u.usage_unit
    AND u.usage_start_time >= p.price_start_time
    AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
  WHERE u.cloud = 'AZURE'
    AND (   (u.usage_date >= CAST(:base_start AS DATE) AND u.usage_date < CAST(:base_end AS DATE))
         OR (u.usage_date >= CAST(:cmp_start  AS DATE) AND u.usage_date < CAST(:cmp_end  AS DATE)))
),
agg AS (
  SELECT
    product, sku_name, usage_unit, is_serverless, currency_code,
    SUM(CASE WHEN period = 'B' THEN qty  ELSE 0 END) / MAX(days_b) AS q_b,
    SUM(CASE WHEN period = 'C' THEN qty  ELSE 0 END) / MAX(days_c) AS q_c,
    SUM(CASE WHEN period = 'B' THEN cost ELSE 0 END) / MAX(days_b) AS c_b,
    SUM(CASE WHEN period = 'C' THEN cost ELSE 0 END) / MAX(days_c) AS c_c
  FROM usage_priced CROSS JOIN params
  GROUP BY product, sku_name, usage_unit, is_serverless, currency_code
),
priced AS (
  SELECT *,
         c_b / NULLIF(q_b, 0) AS p_b,
         c_c / NULLIF(q_c, 0) AS p_c
  FROM agg
)
SELECT
  product,
  sku_name,
  usage_unit,
  is_serverless,
  currency_code,
  ROUND(q_b, 4)                                                   AS qty_per_day_b,
  ROUND(q_c, 4)                                                   AS qty_per_day_c,
  ROUND(p_b, 6)                                                   AS unit_price_b,
  ROUND(p_c, 6)                                                   AS unit_price_c,
  ROUND(c_b, 2)                                                   AS cost_per_day_b,
  ROUND(c_c, 2)                                                   AS cost_per_day_c,
  ROUND(c_c - c_b, 2)                                             AS delta_cost_per_day,
  ROUND((q_c - q_b) * COALESCE(p_b, p_c, 0), 2)                   AS volume_effect,
  ROUND((COALESCE(p_c, p_b, 0) - COALESCE(p_b, p_c, 0)) * q_c, 2) AS rate_effect,
  ROUND((c_c - c_b) / NULLIF(SUM(c_c - c_b) OVER (PARTITION BY currency_code), 0), 4)
                                                                  AS share_of_total_delta,
  CASE WHEN c_b = 0 AND c_c > 0                 THEN 'NEW'
       WHEN c_c = 0 AND c_b > 0                 THEN 'GONE'
       WHEN ABS(c_c - c_b) < 0.01 * ABS(c_b)    THEN 'FLAT'
       WHEN c_c > c_b                           THEN 'GROWN'
       ELSE 'SHRUNK' END                                          AS change_class
FROM priced
ORDER BY currency_code, delta_cost_per_day DESC;
