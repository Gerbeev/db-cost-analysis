-- Step 5.3 · Object-level delta between B and C: which job / pipeline / warehouse /
--            cluster / serving endpoint / app / notebook / pool moved. Per day, list price.
-- Params : :base_start, :base_end, :cmp_start, :cmp_end   (end exclusive)
-- Read   : top rows by delta_cost_per_day; cumulative_share reaches 0.90 -> stop (R4).
--          change_class NEW = object had no usage in B; GONE = no usage in C.
-- Key precedence: JOB > PIPELINE > WAREHOUSE > SERVING_ENDPOINT > APP > CLUSTER > NOTEBOOK > POOL.
--          Jobs on all-purpose clusters have no job_id -> they appear as CLUSTER (by design).
-- Names  : object_name is filled only where usage_metadata carries it; use 6.04 (jobs),
--          6.06 (clusters), 6.09 (warehouses) for names.
-- Privacy: sample_run_as may contain user e-mail / service principal ID - redact before sharing.

WITH params AS (
  SELECT DATEDIFF(CAST(:base_end AS DATE), CAST(:base_start AS DATE)) AS days_b,
         DATEDIFF(CAST(:cmp_end  AS DATE), CAST(:cmp_start  AS DATE)) AS days_c
),
usage_priced AS (
  SELECT
    CASE WHEN u.usage_date >= CAST(:base_start AS DATE) AND u.usage_date < CAST(:base_end AS DATE)
         THEN 'B' ELSE 'C' END                                AS period,
    u.usage_date,
    u.workspace_id,
    CASE
      WHEN u.usage_metadata.job_id           IS NOT NULL THEN 'JOB'
      WHEN u.usage_metadata.dlt_pipeline_id  IS NOT NULL THEN 'PIPELINE'
      WHEN u.usage_metadata.warehouse_id     IS NOT NULL THEN 'WAREHOUSE'
      WHEN u.usage_metadata.endpoint_id      IS NOT NULL THEN 'SERVING_ENDPOINT'
      WHEN u.usage_metadata.app_id           IS NOT NULL THEN 'APP'
      WHEN u.usage_metadata.cluster_id       IS NOT NULL THEN 'CLUSTER'
      WHEN u.usage_metadata.notebook_id      IS NOT NULL THEN 'NOTEBOOK'
      WHEN u.usage_metadata.instance_pool_id IS NOT NULL THEN 'POOL'
      ELSE 'UNATTRIBUTED'
    END                                                       AS object_type,
    COALESCE(
      CAST(u.usage_metadata.job_id           AS STRING),
      CAST(u.usage_metadata.dlt_pipeline_id  AS STRING),
      CAST(u.usage_metadata.warehouse_id     AS STRING),
      CAST(u.usage_metadata.endpoint_id      AS STRING),
      CAST(u.usage_metadata.app_id           AS STRING),
      CAST(u.usage_metadata.cluster_id       AS STRING),
      CAST(u.usage_metadata.notebook_id      AS STRING),
      CAST(u.usage_metadata.instance_pool_id AS STRING),
      CONCAT('product:', COALESCE(u.billing_origin_product, 'UNKNOWN'))
    )                                                         AS object_id,
    COALESCE(u.usage_metadata.job_name, u.usage_metadata.endpoint_name,
             u.usage_metadata.app_name, u.usage_metadata.notebook_path) AS object_name,
    u.billing_origin_product                                  AS product,
    u.sku_name,
    u.identity_metadata.run_as                                AS run_as,
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
  SELECT
    workspace_id, object_type, object_id, currency_code,
    MAX(object_name)                                                  AS object_name,
    ARRAY_JOIN(ARRAY_SORT(COLLECT_SET(product)), ',')                 AS products,
    ARRAY_JOIN(ARRAY_SORT(COLLECT_SET(sku_name)), ',')                AS skus,
    MAX(run_as)                                                       AS sample_run_as,
    MIN(usage_date)                                                   AS first_usage_in_periods,
    MIN(CASE WHEN period = 'C' THEN usage_date END)                   AS first_usage_in_c,
    SUM(CASE WHEN period = 'B' THEN cost ELSE 0 END) / MAX(days_b)    AS c_b,
    SUM(CASE WHEN period = 'C' THEN cost ELSE 0 END) / MAX(days_c)    AS c_c
  FROM usage_priced CROSS JOIN params
  GROUP BY workspace_id, object_type, object_id, currency_code
),
ranked AS (
  SELECT *,
         c_c - c_b                                                    AS delta,
         SUM(c_c - c_b) OVER (PARTITION BY currency_code)             AS total_delta,
         SUM(c_c - c_b) OVER (PARTITION BY currency_code ORDER BY c_c - c_b DESC
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_delta,
         ROW_NUMBER() OVER (PARTITION BY currency_code ORDER BY c_c - c_b DESC) AS rank_by_delta
  FROM agg
)
SELECT
  rank_by_delta,
  currency_code,
  workspace_id,
  object_type,
  object_id,
  object_name,
  products,
  skus,
  ROUND(c_b, 2)                                                       AS cost_per_day_b,
  ROUND(c_c, 2)                                                       AS cost_per_day_c,
  ROUND(delta, 2)                                                     AS delta_cost_per_day,
  ROUND(delta / NULLIF(total_delta, 0), 4)                            AS share_of_total_delta,
  ROUND(running_delta / NULLIF(total_delta, 0), 4)                    AS cumulative_share,
  CASE WHEN c_b = 0 AND c_c > 0 THEN 'NEW'
       WHEN c_c = 0 AND c_b > 0 THEN 'GONE'
       WHEN ABS(delta) < 0.01 * ABS(c_b) THEN 'FLAT'
       WHEN delta > 0 THEN 'GROWN' ELSE 'SHRUNK' END                  AS change_class,
  first_usage_in_periods,
  first_usage_in_c,
  sample_run_as
FROM ranked
ORDER BY currency_code, rank_by_delta;
