# 08 · Remediation and controls (Step 9)

<!-- plain -->
> **Overview.** What to do **after** the audit: how to turn each finding into a fix with an owner, how to prove a saving (measure it in the real bill, at least 14 days after the change) and which simple alerts keep the same growth from coming back unnoticed.
<!-- /plain -->

Remediation is **proposed** in the audit and executed only after owner approval, outside the audit.

## 1. Remediation gate - required per proposal

| Field | Content |
|---|---|
| Driver / finding ID | From findings report |
| Change | Exact setting / code / schedule change |
| Expected savings | **Range** in currency/day and /year, derived from the driver's Δ and the mechanism share |
| Risk | SLA, latency, freshness, failure, security impact |
| Guardrail metric | What must not degrade (p95 runtime, success rate, data freshness, dashboard latency) |
| Rollback | How and how fast |
| Owner / approver | Named |
| Validation | Post-change per-day cost vs pre-change, same method (reference/03), ≥ 14 days |

Savings are reported as realized only after validation on Azure Actual.

## 2. Typical remediation by driver

| Driver | Options | Guardrail |
|---|---|---|
| Idle all-purpose clusters | Auto-termination ≤ 30-60 min via policy; shared clusters | Interrupted sessions |
| Oversized clusters | Right-size workers/node type; autoscale ranges | p95 runtime, OOM |
| Jobs on all-purpose compute | Move to job clusters / serverless jobs | Startup time |
| More runs | Restore/justify schedule; event triggers with debounce | Freshness SLA |
| Longer runs | Incremental processing, partition pruning, Photon where cost-effective | Correctness |
| Retry storms | Max retries, failure alerts, fix root error | Recovery |
| Continuous pipelines | Triggered mode where latency allows | Latency SLA |
| Full refresh | Remove scheduled full refreshes | Data correctness |
| Idle pools | Min idle 0 off-hours; shorter idle termination | Cold start |
| SQL warehouse uptime | Auto-stop 5-10 min (serverless); size/max clusters caps | BI latency |
| BI polling | Dashboard schedules; caching; query result reuse | Freshness |
| Serving endpoints | Scale-to-zero (non-prod); right-size throughput | Latency |
| Managed features | Scope to needed catalogs; refresh frequency | Feature benefit |
| Storage capacity | VACUUM / retention; lifecycle tiering | Time travel / recovery |
| Storage transactions | Compaction; reduce listing | - |
| Cross-region / egress | Co-locate compute and data | Availability design |
| Log ingestion | Diagnostic categories, sampling, retention | Security/audit requirements |
| Commitment expiry | Renew / resize reservations, DBCU | Financial commitment |

## 3. Controls after the audit

| Control | Mechanism | Cadence | Owner |
|---|---|---|---|
| Budget alerts on Azure Actual | Azure Cost Management budgets at audit scope; absolute + forecast thresholds | Continuous | FinOps |
| Databricks budgets | Account console budgets per workspace / tag | Continuous | Platform |
| Top-mover review | `tools/period_delta.py` last 7 days vs prior 28 days; `5.3_object_delta.sql` | Weekly | Platform + FinOps |
| Onset watch | `2.1_daily_cost_onset.sql` / `tools/onset_detect.py` on last 90 days | Weekly | Platform |
| Compute policies | Cluster policies (auto-termination, max workers, node types, tags), warehouse standards | On change | Platform |
| Tag coverage | `5.5_attribution_coverage.sql` - target untagged usage < 5% | Monthly | Platform |
| Config drift | New clusters/warehouses/pipelines/endpoints and size changes (`6.06`, `6.09`, `5.6`) | Weekly | Platform |
| Commitment tracking | Expiry calendar for RI/SP/DBCU/credits | Monthly | Finance |
| Monthly reconciliation | Azure Actual vs Amortized vs Databricks modeled (direction check R8) | Monthly | FinOps |
