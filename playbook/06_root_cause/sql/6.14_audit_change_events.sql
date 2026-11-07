-- Step 6.4 · Change events from the audit log: configuration-changing actions per day,
--            service and action. No identities, request parameters or statement text.
-- Params : :start_date, :end_date   (end exclusive; e.g. 14 days before onset to 14 days after)
-- Read   : actions on clusters / jobs / pipelines / warehouses / pools / serving clustered
--          around a driver onset -> open the object history for the exact change.
-- Limits : regional, retention-bound; service and action names evolve - inspect
--          SELECT DISTINCT service_name, action_name first if results look empty.
--          Correlation in time is not proof (R9).

SELECT
  event_date,
  workspace_id,
  service_name,
  action_name,
  COUNT(*)                                          AS events,
  COUNT_IF(response.status_code >= 400)             AS failed_events
FROM system.access.audit
WHERE event_date >= CAST(:start_date AS DATE)
  AND event_date <  CAST(:end_date   AS DATE)
  AND service_name IN ('clusters', 'jobs', 'deltaPipelines', 'databrickssql', 'instancePools',
                       'serverlessRealTimeInference', 'vectorSearch', 'apps', 'accounts',
                       'workspace', 'clusterPolicies', 'budgetPolicyCentral')
  AND NOT LOWER(action_name) RLIKE '^(get|list|read|view|describe|search|fetch)'
GROUP BY ALL
ORDER BY event_date, events DESC;
