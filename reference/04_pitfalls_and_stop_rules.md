# 04 · Pitfalls and stop rules

<!-- plain -->
> **Overview.** Conditions that produce incorrect results without any error message: an export taken twice, two currencies mixed, a missing month and so on. Each trap says how to notice it and what to do. If the app or the checks mention a **STOP** number, this is the page that explains it.
<!-- /plain -->

## 1. Stop rules - do not compute or report deltas until fixed

| ID | Condition | Detect | Fix |
|---|---|---|---|
| STOP-1 | Overlapping Azure export runs / appended daily month-to-date snapshots | Export total > Cost Analysis total; repeated dates per run | One run per month, partitions once |
| STOP-2 | Mixed currencies in one series | > 1 currency value | Split series; explicit FX bridge |
| STOP-3 | Missing month or partial month | `1.1_usage_coverage.sql` days_with_data < days_in_month; export date gaps | Re-export; or mark `UNKNOWN` (never zero) |
| STOP-4 | Actual and Amortized mixed | `PricingModel`/metric inconsistent between periods | Re-export with one metric |
| STOP-5 | Scope differs between B and C | Subscription/workspace sets differ | Fix scope or report scope change as accounting effect |
| STOP-6 | Ambiguous price join | `1.3_price_join_check.sql` duplicates > 0 | Exclude SKU from modeled cost (R7) |
| STOP-7 | Retention excludes target dates | Earliest row in system table > window start | Shorten window or mark `UNKNOWN` |
| STOP-8 | Current month-to-date included | Window end > last full month | Remove |

## 2. Misinterpretations that produce false root causes

| Pitfall | Why wrong | Correct approach |
|---|---|---|
| Comparing monthly totals Feb vs Mar | +10.7% from day count alone | Per-day rates (reference/03 §1) |
| Ranking by % growth | Small items dominate | Rank by currency/day Δ |
| Adding service + RG + meter subtotals | Same money counted 3× | One grouping per waterfall |
| Adding Databricks modeled cost to Azure Actual | Same DBU counted twice (list vs billed) | Separate ledgers (R1) |
| Treating DBU and VM as duplicates | Classic compute bills both | Attribute separately |
| Adding VM cost to serverless | Serverless includes compute | DBU only |
| Deleting negative usage rows | Corrections removed → overstated usage | Net all `record_type` |
| Summing `usage_quantity` across units | DBU + tokens + GB meaningless | Group by `usage_unit` |
| "NULL job_id = waste" | All-purpose / SQL / platform usage has no job_id by design | Classify as `CLUSTER`/`WAREHOUSE`/`UNATTRIBUTED` |
| Counting `job_run_timeline` rows as runs | Long runs are sliced hourly | Collapse by `workspace_id, job_id, run_id` |
| Counting serverless usage rows as runs | Multiple rows per run | `COUNT(DISTINCT job_run_id)` |
| Joining jobs by `job_id` only | Unique per workspace only | Key = `workspace_id + job_id` |
| SCD2 join without validity window | Duplicates config rows | Latest row ≤ timestamp |
| "New SKU = new resource" | SKU rename / reclassification possible | Check object IDs and price history |
| "New ID in billing = new deployment" | Recreated object, ID rotation | Check SCD2 first change and name |
| Query count ↑ ⇒ cost ↑ | Warehouse bills uptime/size, not queries | Use warehouse events + usage |
| Missing table ⇒ no workload | Regional/preview tables | Mark `UNKNOWN` |
| Managed RG = all Databricks cost | Storage/network/monitoring live elsewhere; non-DBX resources possible | Map dependencies explicitly |
| Anomaly alert absent ⇒ no spike | Alert history regenerates; thresholds/view-specific | Reproduce cost series independently |
| IBM report ↑ ⇒ Azure spend ↑ | Mapping/allocation/model changes move cost without new spend | Trace to source (reference/06) |
| Time correlation ⇒ cause | Coincident changes common | R9 criteria |
| Idle in monthly aggregate ⇒ delete | May be needed (SLA, streaming) | Remediation gate (reference/08) |

## 3. Data-type caveats

- Azure `Date` is usage date; purchases may be dated at purchase, not usage.
- Azure `CostInBillingCurrency` excludes taxes; credits may be outside cost details depending on agreement.
- Databricks `usage_date` is UTC; Azure Cost Analysis daily view may use a different day boundary - expect ±1 day shifts at onset.
- `system.billing.usage` can be restated days later; record query run timestamp.
- `node_timeline` may omit nodes alive < ~10 minutes.
- `instance_events` coverage excludes SQL warehouses; observed pool hours are a lower bound.
- `warehouse_events` initial state before the window can be unknown.
- List prices exclude contract discounts; modeled vs billed ratio can change when commitments change.
