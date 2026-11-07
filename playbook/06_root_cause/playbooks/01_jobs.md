# PB-JOBS

<!-- plain -->
> **Overview.** Use when a **scheduled job** costs more. The usual reasons: it runs more often, each run takes longer, it got a bigger cluster, or it processes more data. The checks tell them apart.
<!-- /plain -->

**Signals:** `5.1` JOBS SKUs ↑ (classic `*JOBS_COMPUTE*` or `*JOBS_SERVERLESS*`); `5.3` objects of type `JOB` with class `NEW`/`GROWN`.

**Diagnostics**

| # | Check | Source | Read |
|---|---|---|---|
| J1 | Runs/day vs cost/run per job, B vs C | [`6.01_job_cost_per_run.sql`](../sql/6.01_job_cost_per_run.sql) | `frequency_effect` vs `unit_cost_effect` |
| J2 | Monthly runs, avg/p95 duration, failures | [`6.02_job_runs_monthly.sql`](../sql/6.02_job_runs_monthly.sql) | Duration drift, failure ↑ |
| J3 | Daily run starts and run-hours | [`6.03_job_runs_daily.sql`](../sql/6.03_job_runs_daily.sql) | Onset day of extra runs |
| J4 | Definition changes (SCD2), first seen | [`6.04_job_definition_changes.sql`](../sql/6.04_job_definition_changes.sql) | Change timestamp near onset |
| J5 | Cluster spec of the job cluster | [`6.06_cluster_config_history.sql`](../sql/6.06_cluster_config_history.sql) (filter `cluster_source = 'JOB'`) | Workers/node type change |
| J6 | Input volume | Spark UI / job metrics; [`6.11_query_trends.sql`](../sql/6.11_query_trends.sql) for SQL tasks (`read_bytes`) | Data growth |
| J7 | Change actor | [`6.14_audit_change_events.sql`](../sql/6.14_audit_change_events.sql) (service `jobs`) ; Git / bundle history | Who changed what |

**Mechanisms**

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-JOB-01 | New scheduled job | `5.3` class `NEW`; `6.04` first change ≈ onset; runs start ≈ onset | Job existed in B with same cost/day |
| H-JOB-02 | Higher run frequency (schedule/trigger, file arrival, continuous) | `6.01` frequency effect ≥ 70% of job Δ; `6.04` schedule edit ≈ onset | Runs/day unchanged |
| H-JOB-03 | Longer runs (more data, skew, regression) | Unit-cost effect dominant; duration ↑ with same cluster size; input bytes ↑ | Duration flat or cluster size explains it |
| H-JOB-04 | Retry / failure storm | Failed runs ↑; repair runs ↑; cost in failed runs | Failure rate unchanged |
| H-JOB-05 | Moved to all-purpose cluster / pricier tier (Photon, Premium) | Job usage shifts from `JOB` to `CLUSTER` objects; SKU changes to `ALL_PURPOSE`/`PHOTON` | Same SKU in B and C |
| H-JOB-06 | Larger job cluster (workers, node type, autoscale max) | `6.06` change ≈ onset; DBU/hour per run ↑ | Spec unchanged |
| H-JOB-07 | Migration to serverless jobs (mix shift) | Classic JOBS ↓ and serverless JOBS ↑ for same job IDs | No SKU shift |

**Remediation options:** restore schedule; job clusters instead of all-purpose; right-size workers; fix retry loops (max retries, alerting); incremental processing instead of full reload; cluster policies with max workers.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
