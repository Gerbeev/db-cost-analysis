-- Step 5.4 · Daily modeled cost per object, to date each driver's onset (rule R5).
-- Params : :start_date, :end_date   (end exclusive; 30 days before B through end of C)
--          :object_ids               comma-separated object IDs from 5.3, or ALL
-- Read   : object onset within +/- 2 days of the total onset -> trigger candidate;
--          later onset -> additional driver. Same object key logic as 5.3.

WITH keyed AS (
  SELECT
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
    u.sku_name,
    u.usage_unit,
    u.usage_quantity,
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
    AND u.usage_date >= CAST(:start_date AS DATE)
    AND u.usage_date <  CAST(:end_date   AS DATE)
)
SELECT
  usage_date,
  workspace_id,
  object_type,
  object_id,
  currency_code,
  ARRAY_JOIN(ARRAY_SORT(COLLECT_SET(sku_name)), ',')          AS skus,
  ROUND(SUM(cost), 2)                                         AS daily_list_cost,
  ROUND(SUM(CASE WHEN usage_unit = 'DBU' THEN usage_quantity END), 3) AS daily_dbu
FROM keyed
WHERE :object_ids = 'ALL' OR ARRAY_CONTAINS(SPLIT(:object_ids, ','), object_id)
GROUP BY usage_date, workspace_id, object_type, object_id, currency_code
ORDER BY object_type, object_id, usage_date;
