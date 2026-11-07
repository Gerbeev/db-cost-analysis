-- Step 6 · PB-CLASSIC C1 / PB-POOLS · Classic cluster configuration history (SCD2) with
--          the last pre-window version as baseline and the list of fields changed per version.
-- Params : :start_date, :end_date   (end exclusive)
--          :cluster_sources   ALL | comma list of cluster_source values, e.g. UI,API  or  JOB
--                             (JOB clusters create one cluster per run -> large output)
-- Read   : changed_fields + change_time near a driver onset -> change event candidate.
-- Limits : a pre-window row can be a deletion snapshot (snapshot_state = DELETED).

WITH scoped AS (
  SELECT *
  FROM system.compute.clusters
  WHERE change_time < CAST(:end_date AS TIMESTAMP)
    AND (:cluster_sources = 'ALL' OR ARRAY_CONTAINS(SPLIT(:cluster_sources, ','), cluster_source))
),
marked AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY workspace_id, cluster_id
                       ORDER BY CASE WHEN change_time < CAST(:start_date AS TIMESTAMP) THEN 0 ELSE 1 END,
                                change_time DESC) AS pre_rank
  FROM scoped
),
history AS (
  SELECT
    CASE WHEN change_time < CAST(:start_date AS TIMESTAMP) THEN 'BASELINE_PRE_WINDOW'
         ELSE 'CHANGE_IN_WINDOW' END                          AS record_kind,
    *
  FROM marked
  WHERE change_time >= CAST(:start_date AS TIMESTAMP)
     OR (change_time < CAST(:start_date AS TIMESTAMP) AND pre_rank = 1)
),
diffed AS (
  SELECT *,
    CONCAT_WS(',',
      IF(LAG(worker_count)             OVER w <=> worker_count,             NULL, 'worker_count'),
      IF(LAG(min_autoscale_workers)    OVER w <=> min_autoscale_workers,    NULL, 'min_autoscale_workers'),
      IF(LAG(max_autoscale_workers)    OVER w <=> max_autoscale_workers,    NULL, 'max_autoscale_workers'),
      IF(LAG(auto_termination_minutes) OVER w <=> auto_termination_minutes, NULL, 'auto_termination_minutes'),
      IF(LAG(driver_node_type)         OVER w <=> driver_node_type,         NULL, 'driver_node_type'),
      IF(LAG(worker_node_type)         OVER w <=> worker_node_type,         NULL, 'worker_node_type'),
      IF(LAG(dbr_version)              OVER w <=> dbr_version,              NULL, 'dbr_version'),
      IF(LAG(azure_attributes.availability) OVER w <=> azure_attributes.availability, NULL, 'availability'),
      IF(LAG(worker_instance_pool_id)  OVER w <=> worker_instance_pool_id,  NULL, 'worker_instance_pool_id'),
      IF(LAG(policy_id)                OVER w <=> policy_id,                NULL, 'policy_id')
    )                                                         AS changed_fields_raw,
    LAG(change_time) OVER w                                   AS previous_change_time
  FROM history
  WINDOW w AS (PARTITION BY workspace_id, cluster_id ORDER BY change_time)
)
SELECT
  record_kind,
  workspace_id,
  cluster_id,
  cluster_name,
  cluster_source,
  owned_by,
  change_time,
  delete_time,
  CASE WHEN delete_time IS NOT NULL THEN 'DELETED' ELSE 'CONFIGURED' END   AS snapshot_state,
  CASE WHEN previous_change_time IS NULL THEN 'FIRST_VISIBLE_VERSION'
       ELSE NULLIF(changed_fields_raw, '') END                             AS changed_fields,
  driver_node_type,
  worker_node_type,
  worker_count,
  min_autoscale_workers,
  max_autoscale_workers,
  auto_termination_minutes,
  azure_attributes.availability                                            AS azure_availability,
  worker_instance_pool_id,
  driver_instance_pool_id,
  dbr_version,
  policy_id
FROM diffed
ORDER BY workspace_id, cluster_id, change_time;
