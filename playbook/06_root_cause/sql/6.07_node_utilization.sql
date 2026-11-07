-- Step 6 · PB-CLASSIC C2 · Classic node-minutes and CPU / memory utilization per cluster.
-- Params : :start_date, :end_date   (end exclusive; node_timeline retention is ~90 days)
-- Read   : observed_node_minutes up B->C = more node-hours (VM + DBU both rise);
--          low_cpu_share >= 0.5 in C = oversizing / idle candidate (H-CLS-01, H-CLS-05).
-- Limits : operational metric, not VM cost. Nodes alive < ~10 min may be missing.

SELECT
  DATE_FORMAT(start_time, 'yyyy-MM')                                       AS month,
  workspace_id,
  cluster_id,
  node_type,
  driver                                                                   AS is_driver,
  COUNT(*)                                                                 AS observed_node_minutes,
  COUNT(DISTINCT instance_id)                                              AS observed_instances,
  ROUND(AVG(cpu_user_percent + cpu_system_percent), 2)                     AS avg_cpu_busy_pct,
  ROUND(AVG(mem_used_percent), 2)                                          AS avg_mem_used_pct,
  COUNT_IF(cpu_user_percent + cpu_system_percent < 10)                     AS low_cpu_minutes,
  ROUND(COUNT_IF(cpu_user_percent + cpu_system_percent < 10) / COUNT(*), 3) AS low_cpu_share
FROM system.compute.node_timeline
WHERE start_time >= CAST(:start_date AS TIMESTAMP)
  AND start_time <  CAST(:end_date   AS TIMESTAMP)
GROUP BY ALL
ORDER BY month, observed_node_minutes DESC;
