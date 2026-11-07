-- Step 5.2 · Workspace x product delta between B and C (per day, list price).
-- Params : :base_start, :base_end, :cmp_start, :cmp_end   (end exclusive)
-- Read   : delta concentrated in one workspace -> local workload change;
--          spread evenly across workspaces    -> price, platform feature or account-level change.
--          workspace_id NULL = account-level usage (e.g. networking, some managed features).

WITH params AS (
  SELECT DATEDIFF(CAST(:base_end AS DATE), CAST(:base_start AS DATE)) AS days_b,
         DATEDIFF(CAST(:cmp_end  AS DATE), CAST(:cmp_start  AS DATE)) AS days_c
),
usage_priced AS (
  SELECT
    CASE WHEN u.usage_date < CAST(:base_end AS DATE) AND u.usage_date >= CAST(:base_start AS DATE) THEN 'B'
         ELSE 'C' END                                         AS period,
    u.account_id,
    u.workspace_id,
    COALESCE(u.billing_origin_product, 'UNKNOWN')             AS product,
    COALESCE(p.currency_code, 'UNPRICED')                     AS currency_code,
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
  SELECT account_id, workspace_id, product, currency_code,
         SUM(CASE WHEN period = 'B' THEN cost ELSE 0 END) / MAX(days_b) AS c_b,
         SUM(CASE WHEN period = 'C' THEN cost ELSE 0 END) / MAX(days_c) AS c_c
  FROM usage_priced CROSS JOIN params
  GROUP BY account_id, workspace_id, product, currency_code
)
SELECT
  account_id,
  workspace_id,
  product,
  currency_code,
  ROUND(c_b, 2)                                                   AS cost_per_day_b,
  ROUND(c_c, 2)                                                   AS cost_per_day_c,
  ROUND(c_c - c_b, 2)                                             AS delta_cost_per_day,
  ROUND((c_c - c_b) / NULLIF(SUM(c_c - c_b) OVER (PARTITION BY currency_code), 0), 4)
                                                                  AS share_of_total_delta,
  ROUND(SUM(c_c - c_b) OVER (PARTITION BY currency_code, workspace_id), 2)
                                                                  AS workspace_delta_per_day,
  CASE WHEN c_b = 0 AND c_c > 0 THEN 'NEW'
       WHEN c_c = 0 AND c_b > 0 THEN 'GONE'
       WHEN ABS(c_c - c_b) < 0.01 * ABS(c_b) THEN 'FLAT'
       WHEN c_c > c_b THEN 'GROWN' ELSE 'SHRUNK' END              AS change_class
FROM agg
ORDER BY currency_code, workspace_delta_per_day DESC, delta_cost_per_day DESC;
