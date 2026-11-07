# PB-SERVERLESS

<!-- plain -->
> **Overview.** Use when **serverless** products cost more. There are no virtual machines to look at - the price is all DBU - so the question is *what is being run, how often and with which feature switched on*.
<!-- /plain -->

**Signals:** `6.13` serverless share ↑ (`product_features.is_serverless = true`); `5.6` new serverless SKUs.

| # | Check | Source | Read |
|---|---|---|---|
| V1 | Serverless usage by product/SKU/month | [`6.13_serverless_and_features.sql`](../sql/6.13_serverless_and_features.sql) | Which product drives |
| V2 | Classic vs serverless for the same objects | `5.3` grouped by object across SKUs | Mix shift vs net new |
| V3 | Notebook / user attribution | `5.3` object_type `NOTEBOOK`; `sample_run_as` | New users |
| V4 | Budget policy / tags coverage | [`5.5_attribution_coverage.sql`](../../05_databricks_decomposition/sql/5.5_attribution_coverage.sql) | Untagged serverless |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-SRV-01 | Migration from classic (mix shift) | Classic ↓ for same objects; compare net (serverless Δ + classic DBU Δ + VM Δ) | No classic reduction |
| H-SRV-02 | New serverless notebook usage | `NOTEBOOK` objects NEW; users ↑ | Stable |
| H-SRV-03 | Performance-optimized mode | `usage_metadata`/`product_features.performance_target` = performance optimized | Standard mode |
| H-SRV-04 | Serverless networking / egress SKUs | `NETWORKING` product ↑ | Flat |

**Remediation options:** standard (cost-optimized) mode for non-latency jobs; budget policies; serverless usage policies per team.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
