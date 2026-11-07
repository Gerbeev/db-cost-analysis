-- Step 6 · PB-JOBS J1 · Job delta split into frequency effect (runs/day) and
--          unit-cost effect (cost/run). Classic job clusters and serverless jobs.
-- Params : :base_start, :base_end, :cmp_start, :cmp_end   (end exclusive)
-- Identity: delta_cost_per_day = frequency_effect + unit_cost_effect   (docs/03 §5)
--           exact when every usage row carries job_run_id.
-- Limits : jobs on all-purpose clusters have no job_id in usage (see PB-CLASSIC).
--          A run spanning the B/C boundary is counted in both periods.
--          rows_without_run_id > 0 -> frequency effect is approximate.

WITH params AS (
  SELECT DATEDIFF(CAST(:base_end AS DATE), CAST(:base_start AS DATE)) AS days_b,
         DATEDIFF(CAST(:cmp_end  AS DATE), CAST(:cmp_start  AS DATE)) AS days_c
),
job_usage AS (
  SELECT
    CASE WHEN u.usage_date >= CAST(:base_start AS DATE) AND u.usage_date < CAST(:base_end AS DATE)
         THEN 'B' ELSE 'C' END                                AS period,
    u.workspace_id,
    u.usage_metadata.job_id                                   AS job_id,
    u.usage_metadata.job_run_id                               AS run_id,
    u.usage_metadata.job_name                                 AS job_name,
    u.product_features.is_serverless                          AS is_serverless,
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
    AND u.usage_metadata.job_id IS NOT NULL
    AND (   (u.usage_date >= CAST(:base_start AS DATE) AND u.usage_date < CAST(:base_end AS DATE))
         OR (u.usage_date >= CAST(:cmp_start  AS DATE) AND u.usage_date < CAST(:cmp_end  AS DATE)))
),
per_job AS (
  SELECT
    workspace_id, job_id, currency_code,
    MAX(job_name)                                                         AS job_name,
    MAX(CAST(is_serverless AS INT))                                       AS any_serverless,
    COUNT(DISTINCT CASE WHEN period = 'B' THEN run_id END) / MAX(days_b)  AS n_b,
    COUNT(DISTINCT CASE WHEN period = 'C' THEN run_id END) / MAX(days_c)  AS n_c,
    SUM(CASE WHEN period = 'B' THEN cost ELSE 0 END) / MAX(days_b)        AS c_b,
    SUM(CASE WHEN period = 'C' THEN cost ELSE 0 END) / MAX(days_c)        AS c_c,
    COUNT_IF(run_id IS NULL)                                              AS rows_without_run_id
  FROM job_usage CROSS JOIN params
  GROUP BY workspace_id, job_id, currency_code
),
unit AS (
  SELECT *, c_b / NULLIF(n_b, 0) AS u_b, c_c / NULLIF(n_c, 0) AS u_c FROM per_job
)
SELECT
  workspace_id,
  job_id,
  job_name,
  currency_code,
  any_serverless,
  ROUND(n_b, 3)                                                   AS runs_per_day_b,
  ROUND(n_c, 3)                                                   AS runs_per_day_c,
  ROUND(u_b, 2)                                                   AS cost_per_run_b,
  ROUND(u_c, 2)                                                   AS cost_per_run_c,
  ROUND(c_b, 2)                                                   AS cost_per_day_b,
  ROUND(c_c, 2)                                                   AS cost_per_day_c,
  ROUND(c_c - c_b, 2)                                             AS delta_cost_per_day,
  ROUND((n_c - n_b) * COALESCE(u_b, u_c, 0), 2)                   AS frequency_effect,
  ROUND((COALESCE(u_c, u_b, 0) - COALESCE(u_b, u_c, 0)) * n_c, 2) AS unit_cost_effect,
  CASE WHEN c_b = 0 AND c_c > 0 THEN 'NEW'
       WHEN c_c = 0 AND c_b > 0 THEN 'GONE'
       WHEN ABS(c_c - c_b) < 0.01 * ABS(c_b) THEN 'FLAT'
       WHEN c_c > c_b THEN 'GROWN' ELSE 'SHRUNK' END              AS change_class,
  rows_without_run_id
FROM unit
ORDER BY currency_code, delta_cost_per_day DESC;
