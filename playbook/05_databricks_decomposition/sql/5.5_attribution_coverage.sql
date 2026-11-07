-- Step 5.5 / 7.3 · Attribution coverage B vs C: usage without object ID, without
--                  custom tags, without a required tag key, without workspace.
-- Params : :base_start, :base_end, :cmp_start, :cmp_end   (end exclusive)
--          :required_tag   tag key that must be present, e.g. cost_center
-- Read   : delta in unattributed / untagged cost feeds SHARED_UNALLOCATED or UNEXPLAINED (Step 7).
--          Missing IDs are expected for some products (platform features, networking).

WITH params AS (
  SELECT DATEDIFF(CAST(:base_end AS DATE), CAST(:base_start AS DATE)) AS days_b,
         DATEDIFF(CAST(:cmp_end  AS DATE), CAST(:cmp_start  AS DATE)) AS days_c
),
usage_priced AS (
  SELECT
    CASE WHEN u.usage_date >= CAST(:base_start AS DATE) AND u.usage_date < CAST(:base_end AS DATE)
         THEN 'B' ELSE 'C' END                                AS period,
    COALESCE(u.billing_origin_product, 'UNKNOWN')             AS product,
    COALESCE(p.currency_code, 'UNPRICED')                     AS currency_code,
    u.usage_quantity * p.pricing.effective_list.default       AS cost,
    (    u.usage_metadata.job_id IS NULL AND u.usage_metadata.dlt_pipeline_id IS NULL
     AND u.usage_metadata.warehouse_id IS NULL AND u.usage_metadata.cluster_id IS NULL
     AND u.usage_metadata.endpoint_id IS NULL AND u.usage_metadata.app_id IS NULL
     AND u.usage_metadata.notebook_id IS NULL AND u.usage_metadata.instance_pool_id IS NULL)
                                                              AS no_object_id,
    (u.custom_tags IS NULL OR SIZE(u.custom_tags) = 0)        AS no_tags,
    (u.custom_tags IS NULL OR ELEMENT_AT(u.custom_tags, :required_tag) IS NULL)
                                                              AS no_required_tag,
    (u.workspace_id IS NULL)                                  AS no_workspace
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
)
SELECT
  product,
  currency_code,
  ROUND(SUM(CASE WHEN period='B' THEN cost ELSE 0 END) / MAX(days_b), 2)                         AS cost_per_day_b,
  ROUND(SUM(CASE WHEN period='C' THEN cost ELSE 0 END) / MAX(days_c), 2)                         AS cost_per_day_c,
  ROUND(SUM(CASE WHEN period='B' AND no_object_id    THEN cost ELSE 0 END) / MAX(days_b), 2)     AS no_object_id_b,
  ROUND(SUM(CASE WHEN period='C' AND no_object_id    THEN cost ELSE 0 END) / MAX(days_c), 2)     AS no_object_id_c,
  ROUND(SUM(CASE WHEN period='B' AND no_tags         THEN cost ELSE 0 END) / MAX(days_b), 2)     AS untagged_b,
  ROUND(SUM(CASE WHEN period='C' AND no_tags         THEN cost ELSE 0 END) / MAX(days_c), 2)     AS untagged_c,
  ROUND(SUM(CASE WHEN period='B' AND no_required_tag THEN cost ELSE 0 END) / MAX(days_b), 2)     AS missing_required_tag_b,
  ROUND(SUM(CASE WHEN period='C' AND no_required_tag THEN cost ELSE 0 END) / MAX(days_c), 2)     AS missing_required_tag_c,
  ROUND(SUM(CASE WHEN period='C' AND no_workspace    THEN cost ELSE 0 END) / MAX(days_c), 2)     AS no_workspace_c
FROM usage_priced CROSS JOIN params
GROUP BY product, currency_code
ORDER BY currency_code, cost_per_day_c DESC;
