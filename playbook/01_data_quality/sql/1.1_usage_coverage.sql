-- Step 1.3 · Databricks usage coverage, corrections and workspace scope.
-- Params : :start_date, :end_date   (YYYY-MM-DD, end exclusive)
-- Pass   : days_with_data = days_in_month for every full month;
--          workspace list (query B) matches the scope record.
-- Note   : RETRACTION / RESTATEMENT rows are corrections, not duplicates. Never drop them.

-- A. Monthly coverage
SELECT
  DATE_FORMAT(usage_date, 'yyyy-MM')                AS month,
  account_id,
  COUNT(DISTINCT usage_date)                        AS days_with_data,
  DAY(LAST_DAY(MIN(usage_date)))                    AS days_in_month,
  COUNT(DISTINCT workspace_id)                      AS workspaces,
  COUNT(DISTINCT sku_name)                          AS skus,
  COUNT(*)                                          AS records,
  COUNT_IF(workspace_id IS NULL)                    AS records_without_workspace,
  COUNT_IF(record_type = 'RETRACTION')              AS retraction_records,
  COUNT_IF(record_type = 'RESTATEMENT')             AS restatement_records,
  MAX(ingestion_date)                               AS latest_ingestion_date
FROM system.billing.usage
WHERE cloud = 'AZURE'
  AND usage_date >= CAST(:start_date AS DATE)
  AND usage_date <  CAST(:end_date   AS DATE)
GROUP BY ALL
ORDER BY month, account_id;

-- B. Workspace presence: first_seen inside the window = possible scope change (H-RAT-07)
SELECT
  account_id,
  workspace_id,
  MIN(usage_date)                                   AS first_seen,
  MAX(usage_date)                                   AS last_seen,
  COUNT(DISTINCT usage_date)                        AS active_days,
  CASE WHEN MIN(usage_date) > CAST(:start_date AS DATE) THEN 'APPEARED_IN_WINDOW'
       WHEN MAX(usage_date) < DATE_SUB(CAST(:end_date AS DATE), 7) THEN 'INACTIVE_AT_END'
       ELSE 'PRESENT' END                           AS presence
FROM system.billing.usage
WHERE cloud = 'AZURE'
  AND usage_date >= CAST(:start_date AS DATE)
  AND usage_date <  CAST(:end_date   AS DATE)
GROUP BY account_id, workspace_id
ORDER BY first_seen, workspace_id;
