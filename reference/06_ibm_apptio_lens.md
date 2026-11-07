# 06 · IBM Apptio lens (optional)

<!-- plain -->
> **Overview.** Only for companies that also use IBM Cloudability or ApptioOne. These tools show the same Azure charges in their own way. This page explains how to compare them with the audit - and why their totals are never added to Azure's. Skip it if you do not have IBM tools.
<!-- /plain -->

Use only if **IBM Cloudability** and/or **IBM ApptioOne / TBM Studio** is licensed and in scope. Both are **views of the same Azure charges** (plus, for TBM, other finance sources). Never add their amounts to Azure Actual.

## 1. Which product

| You see | Product | Answers |
|---|---|---|
| Cost reports, Views, Business Mapping, Cost Sharing, Anomaly Detection | **Cloudability** | Provider cost by service/account; ownership mapping; shared-cost allocation |
| Data Studio, Model Studio, Report Studio, towers, applications, BUs | **ApptioOne / TBM Studio** | Source → pool → tower → application → BU allocation; Cost vs Charge vs Budget |

Cloudability does not necessarily feed TBM. Trace the actual lineage.

## 2. When to use in the audit

| Step | Use |
|---|---|
| 0 | If the growth was first seen in an IBM report: record report path, metric, View/model version - the audit question must still be stated on Azure Actual |
| 3 | Test whether IBM-visible growth is scope/metric/mapping/allocation/model change (H-IBM-*) |
| 8 | Cross-check Azure Actual monthly totals vs Cloudability invoice-like metric for identical scope |

## 3. Comparability contract

Lock before comparing: vendor = Azure; billing account; subscription set; View ID (Cloudability) or model version/environment (TBM); metric ID (`unblended_cost` = Cost (Total), invoice-like; never mix with amortized/adjusted); currency; calendar vs fiscal period (with approved mapping); report/export timestamp; allocation projection (pre/post sharing).

## 4. Checks

### Cloudability
| ID | Check | Where | Failure signal |
|---|---|---|---|
| IB-C1 | Connected Azure billing accounts and subscription membership over time | Vendor credentials / accounts | New/missing subscription at onset |
| IB-C2 | View definition used by the report | Views / report filters | Different population across months |
| IB-C3 | Metric ID constant across months | Report metric selector / API `metrics` | Metric changed |
| IB-C4 | Monthly Azure total vs Azure Actual (same scope) | Cost report by month and account | Residual unexplained |
| IB-C5 | Service / account contribution to Δ | Cost report by service, account | - |
| IB-C6 | Business Mapping rule changes | Organize → Business Mappings (read-only) | Owner Δ with flat source total |
| IB-C7 | Cost Sharing rules / weights | Cost Sharing setup | Recipient Δ with flat source pool |
| IB-C8 | Ingestion restatements | Ingest history | Historical months changed |
| IB-C9 | Anomaly alerts | Insights → Anomaly Detection | Context only, not evidence |

### ApptioOne / TBM Studio
| ID | Check | Where | Failure signal |
|---|---|---|---|
| IB-T1 | Report path, metric (Cost/Charge/Budget/Forecast), cost object | Report Studio | Wrong metric compared |
| IB-T2 | Source table and batch for Azure costs | Data Studio | Source includes GL/manual/non-Azure |
| IB-T3 | Fiscal ↔ calendar mapping | Approved finance calendar | Period shift |
| IB-T4 | Transform joins/filters/dedup | Data Studio transforms | Double import, dropped rows |
| IB-T5 | Allocation drivers and versions | Model Studio, Check-In History | Rule change ≈ onset |
| IB-T6 | Unallocated / default buckets | Model Studio | Δ in default bucket |
| IB-T7 | Build / promotion freshness | Build → Calculation Queue | Stale model |
| IB-T8 | Trace one source amount to recipients | Single Object Modeler / Trace cost flows | Residual |

## 5. Mechanisms (see hypothesis register H-IBM-*)

| Observation | Interpretation | Second check |
|---|---|---|
| Source ↑, all layers ↑ | Real provider growth | Azure Actual + Databricks drivers (Steps 4-6) |
| Source flat, recipient A ↑ / B ↓ | Mapping or allocation shift | Rule history, equal-and-opposite deltas |
| Source flat, report Charge ↑ | Model/charge policy | Charge definition |
| Source ↑, recipient flat | Model lag / unallocated | Build freshness, default bucket |
| Report ↑ only in fiscal view | Period shift | Calendar bridge |

## 6. Records

- Discrepancy register: [`templates/ibm_discrepancy_register.csv`](../templates/ibm_discrepancy_register.csv).
- Optional read-only API tools (unchanged): `../tools/apptio_api.py`, `../tools/analyze_apptio.py`, `../tools/normalize_apptioone.py`, interface actions 8.4-8.8 (step 08); setup in [`07_ibm_api_setup.md`](07_ibm_api_setup.md).
