# Step 06 - Root-cause each material driver

[05 Databricks decomposition](../05_databricks_decomposition/README.md) ← `06` → [07 Attribution and residual](../07_attribution_and_residual/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** This step establishes causality. For each candidate from step 05 you determine what changed (a new schedule, a larger cluster, a warehouse that no longer stops, a newly enabled feature), when it changed, and how much of the growth the change explains.
>
> Each type of candidate has a ready playbook with the SQL queries to run. Results are recorded on a one-page driver card. A cause is confirmed only when it satisfies four proofs (rule R9); a coincidence in time alone is insufficient.
>
> **Result:** a driver card per big driver, statuses in the hypothesis register, ROOT_CAUSE lines in the bridge.
>
> **Note:** Disprove at least one alternative explanation for every driver. This separates evidence from assumption.
<!-- /plain -->

**Goal:** for every material driver: a dated technical mechanism with quantified effect, evidenced per rule R9.
**Inputs:** G5 passed; bucket lines (step 04) and DRIVER_CANDIDATE lines (step 05). **Work in:** `audits/<id>/06_root_cause/`.

## 1. Route each driver to its playbook

| Signal from steps 04-05 | Playbook |
|---|---|
| `JOBS` product ↑; job objects `NEW` / `GROWN` | [01 Jobs](playbooks/01_jobs.md) |
| `DLT` / pipeline objects ↑ | [02 Pipelines](playbooks/02_pipelines.md) |
| `ALL_PURPOSE` / `INTERACTIVE` ↑, or classic VM ↑ together with DBU ↑ | [03 Classic compute](playbooks/03_classic_compute.md) |
| Classic VM ↑ while DBU flat | [04 Instance pools](playbooks/04_instance_pools.md) |
| `SQL` product ↑; warehouse objects ↑ | [05 SQL warehouses](playbooks/05_sql_warehouses.md) |
| Serverless SKUs ↑ (`is_serverless`) | [06 Serverless](playbooks/06_serverless.md) |
| `MODEL_SERVING`, `VECTOR_SEARCH`, `AI_*`, `FOUNDATION_MODEL_*`, `APPS`, `DATABASE` ↑ | [07 AI and apps](playbooks/07_ai_and_apps.md) |
| `PREDICTIVE_OPTIMIZATION`, `*_MONITORING`, `FINE_GRAINED_ACCESS_CONTROL`, `NETWORKING`, `DEFAULT_STORAGE` ↑ | [08 Platform features](playbooks/08_platform_features.md) |
| Bucket `STORAGE` ↑ | [09 Storage](playbooks/09_storage.md) |
| Bucket `NETWORK` ↑ | [10 Network](playbooks/10_network.md) |
| Bucket `MONITORING` ↑ | [11 Monitoring](playbooks/11_monitoring.md) |
| Rate / purchase / credit effects (step 03) | [12 Rate and accounting](playbooks/12_rate_and_accounting.md) |

## 2. Procedure per driver

| # | Action | Save to (`audits/<id>/06_root_cause/…`) |
|---|---|---|
| 6.1 | UI action 6.1 *New driver card* creates `driver_<nn>_<short-name>.md` from the template | `driver_01_nightly_etl.md` |
| 6.2 | Open the playbook; list candidate hypotheses (IDs `H-…`) | driver card §Hypotheses |
| 6.3 | Run the playbook diagnostics (UI action 6.2 lists all SQL in [`sql/`](sql/); other evidence via 6.3 upload) | `results/6.xx_<name>__….csv` |
| 6.4 | Quantify: frequency × unit cost (`6.01_job_cost_per_run.sql`) or volume × rate (`5.1`) | driver card §Quantification |
| 6.5 | Find the change event: SCD2 history (`6.04`, `6.06`, `6.09`), audit (`6.14`), release / Git / Activity Log / tickets | driver card §Change event |
| 6.6 | Falsify ≥ 1 alternative hypothesis | driver card §Alternatives |
| 6.7 | Set status per R9: `CONFIRMED` (a+b+c+d) / `LIKELY` / `REJECTED` / `UNKNOWN` | `hypothesis_register.csv` |
| 6.8 | Add a `ROOT_CAUSE` line to the bridge: Δ/day in Azure Actual currency, status, hypothesis_id, evidence_ids | `delta_bridge.csv` |

R9 recap: (a) Δ visible in Azure Actual · (b) change timestamp within ±2 days of the driver onset · (c) mechanism explains ≥ 70% of the driver Δ · (d) ≥ 1 alternative falsified. Time correlation alone is never `CONFIRMED`.

Driver measured in list price → convert: `ratio = Azure DBX_PLATFORM Δ / modeled DBX Δ`; record the ratio in the card ([reference/03 §7](../../reference/03_analysis_method.md)).

## Automatic checks

- Every `ROOT_CAUSE` bridge line with a value has status ≠ `HYPOTHESIS`; every hypothesis it references is not `HYPOTHESIS` in the register.

## Gate G6

Every material driver has a driver card and a status other than `HYPOTHESIS`.
