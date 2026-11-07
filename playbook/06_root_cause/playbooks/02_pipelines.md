# PB-PIPELINES

<!-- plain -->
> **Overview.** Use when a **data pipeline** (Lakeflow / DLT) costs more: more updates, a change of edition, a bigger cluster or a switch to continuous mode.
<!-- /plain -->

**Signals:** `DLT` product SKUs ↑; `5.3` objects of type `PIPELINE` ↑; serverless pipeline SKUs ↑.

**Diagnostics**

| # | Check | Source | Read |
|---|---|---|---|
| L1 | Updates/month, duration, trigger, results, full refresh | [`6.05_pipeline_updates.sql`](../sql/6.05_pipeline_updates.sql) | Update count ↑, full refresh ↑, `last_trigger` |
| L2 | Pipeline cost B vs C | [`5.3_object_delta.sql`](../../05_databricks_decomposition/sql/5.3_object_delta.sql) (object_type `PIPELINE`) | Which pipelines |
| L3 | Daily pipeline cost | [`5.4_object_daily.sql`](../../05_databricks_decomposition/sql/5.4_object_daily.sql) | Onset |
| L4 | Pipeline settings: continuous vs triggered, edition, cluster | Pipeline UI → Settings / JSON; audit `6.14` (service `deltaPipelines`) | Mode/edition change timestamp |

**Mechanisms**

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-PIP-01 | Continuous mode enabled | Update duration ≈ 24h slices; DBU flat-high every day from onset | Triggered updates with gaps |
| H-PIP-02 | Full refresh / backfill / checkpoint reset | `updates_with_full_refresh_selection` > 0 near onset; one-off spike | No full refresh selections |
| H-PIP-03 | More frequent triggers | Update count ↑ with stable duration | Count flat |
| H-PIP-04 | Edition change (Core → Pro → Advanced) | SKU name changes for same pipeline | Same SKU |
| H-PIP-05 | Failures / retries | `failed_updates` ↑ | Stable |
| H-PIP-06 | New pipelines / materialized views / streaming tables | `NEW` pipeline objects; first seen ≈ onset | Existed in B |

**Remediation options:** triggered instead of continuous where latency allows; avoid scheduled full refreshes; right-size or enhanced autoscaling; edition per pipeline need.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
