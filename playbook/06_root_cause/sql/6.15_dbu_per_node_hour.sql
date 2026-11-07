-- Step 6 · PB-CLASSIC C7 · Observed DBU per node-hour by node type, SKU and Photon,
--          computed from your own data (classic compute only).
-- Params : :start_date, :end_date   (end exclusive; node_timeline keeps ~90 days)
-- Method : per cluster: DBUs from system.billing.usage (unit DBU, classic, cluster_id set)
--          / node-hours from system.compute.node_timeline (one row per node per minute;
--          driver + workers). Then weighted by node type / dominant SKU / Photon.
-- Read   : dbu_per_node_hour = what one node of this type really costs in DBU per hour.
--          Compare B vs C (run twice): a rise with the same node type = Photon / SKU / tier
--          change (H-CLS-07, H-RAT-11); a different node type = H-CLS-03.
--          classic cost/h ~ nodes * (dbu_per_node_hour * $/DBU + VM $/h)  (reference/00 §4).
-- Limits : nodes alive < ~10 min may be missing from node_timeline (ratio slightly high);
--          MIXED_DRIVER_WORKER rows blend two node types; pooled idle instances have VM but no DBU.

WITH dbu AS (
  SELECT
    u.workspace_id,
    u.usage_metadata.cluster_id                                   AS cluster_id,
    SUM(u.usage_quantity)                                         AS dbus,
    MAX_BY(u.sku_name, u.usage_quantity)                          AS dominant_sku,
    COUNT(DISTINCT u.sku_name)                                    AS sku_count,
    MAX(CAST(COALESCE(u.product_features.is_photon, FALSE) AS INT)) AS photon
  FROM system.billing.usage u
  WHERE u.cloud = 'AZURE'
    AND u.usage_unit = 'DBU'
    AND u.usage_metadata.cluster_id IS NOT NULL
    AND COALESCE(u.product_features.is_serverless, FALSE) = FALSE
    AND u.usage_date >= CAST(:start_date AS DATE)
    AND u.usage_date <  CAST(:end_date   AS DATE)
  GROUP BY u.workspace_id, u.usage_metadata.cluster_id
),
nodes AS (
  SELECT
    workspace_id,
    cluster_id,
    COUNT(*) / 60.0                                               AS node_hours,
    MAX(CASE WHEN driver THEN node_type END)                      AS driver_node_type,
    MAX(CASE WHEN NOT driver THEN node_type END)                  AS worker_node_type,
    COUNT(DISTINCT node_type)                                     AS node_types
  FROM system.compute.node_timeline
  WHERE start_time >= CAST(:start_date AS TIMESTAMP)
    AND start_time <  CAST(:end_date   AS TIMESTAMP)
  GROUP BY workspace_id, cluster_id
),
per_cluster AS (
  SELECT
    d.*, n.node_hours, n.driver_node_type, n.node_types,
    COALESCE(n.worker_node_type, n.driver_node_type)              AS worker_node_type,
    d.dbus / NULLIF(n.node_hours, 0)                              AS cluster_dbu_per_node_hour
  FROM dbu d
  JOIN nodes n USING (workspace_id, cluster_id)
)
SELECT
  worker_node_type,
  driver_node_type,
  dominant_sku,
  photon,
  CASE WHEN node_types > 1 THEN 'MIXED_DRIVER_WORKER' ELSE 'SINGLE_NODE_TYPE' END AS node_mix,
  COUNT(*)                                                        AS clusters,
  ROUND(SUM(node_hours), 1)                                       AS node_hours,
  ROUND(SUM(dbus), 1)                                             AS dbus,
  ROUND(SUM(dbus) / NULLIF(SUM(node_hours), 0), 3)                AS dbu_per_node_hour,
  ROUND(PERCENTILE_APPROX(cluster_dbu_per_node_hour, 0.5), 3)     AS median_cluster_ratio,
  ROUND(MIN(cluster_dbu_per_node_hour), 3)                        AS min_cluster_ratio,
  ROUND(MAX(cluster_dbu_per_node_hour), 3)                        AS max_cluster_ratio,
  SUM(CASE WHEN sku_count > 1 THEN 1 ELSE 0 END)                  AS clusters_with_multiple_skus
FROM per_cluster
GROUP BY ALL
ORDER BY dbus DESC;
