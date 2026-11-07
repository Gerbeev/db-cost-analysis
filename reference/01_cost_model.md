# 01 · Cost model - what is billed, where, and how views relate

<!-- plain -->
> **Overview.** A deeper look at the same picture as the fundamentals: what exactly gets billed, under which Azure meters it shows up, and how the different views of cost (Actual, Amortized, the Databricks model, IBM) relate. Read it when you need to know *which number comes from where* before you compare two numbers.
<!-- /plain -->

New to the topic: read [00 Fundamentals](00_fundamentals.md) first.

## 1. Ledgers and views

| View | Measures | Source | Role in audit | Add to Azure Actual? |
|---|---|---|---|---|
| **Azure Actual Cost** | Billed usage + purchases at selected scope, pre-tax, in billing currency | Cost Management → Cost analysis / Exports (Actual) | **Money truth** (R1) | - |
| Azure Amortized Cost | Same charges; reservation/savings-plan purchases spread over benefit period | Cost analysis (Amortized) | Separate purchase timing from consumption | No |
| Azure FOCUS export | Normalized schema with billed/effective cost columns | Exports → FOCUS | Alternative schema of same charges | No |
| Databricks usage | `system.billing.usage`: quantity per SKU/unit, signed corrections | Databricks SQL | **Consumption driver analysis** | No |
| Databricks modeled cost | usage × `list_prices.pricing.effective_list.default` | Databricks SQL | Diagnostic proxy at list price, excludes discounts | No |
| Databricks usage dashboard / budgets | Same usage, list price | Account console | Convenience view | No |
| IBM Cloudability | Ingested provider cost; adjusted/amortized metrics; mapping; cost sharing | IBM tenant | Cross-check, ownership | No |
| IBM ApptioOne / TBM | Modeled financial allocation (pool → tower → app → BU) | IBM tenant | Allocation lineage | No |
| Invoice / contract | Final booked amount, taxes, support, credits, commitments | Finance | Final authority for paid amount | - |

## 2. How a Databricks workload produces Azure charges

| Compute type | Azure Databricks DBU charge | Azure VM / disk charge | Where VM cost appears | Notes |
|---|---|---|---|---|
| Classic all-purpose cluster | Yes (`ALL_PURPOSE` / `INTERACTIVE`) | **Yes, separate** | Managed RG of the workspace | DBU + VM are both real; not duplicates |
| Classic jobs cluster | Yes (`JOBS`) | **Yes, separate** | Managed RG | Cheaper DBU rate than all-purpose |
| Classic pipeline (DLT) | Yes (`DLT`, tier Core/Pro/Advanced) | **Yes, separate** | Managed RG | |
| Classic / Pro SQL warehouse | Yes (`SQL`) | **Yes, separate** | Managed RG | |
| Instance pool idle instances | **No DBU** while idle | **Yes** | Managed RG | VM ↑ with DBU flat = pool/idle signal |
| Serverless (jobs, notebooks, pipelines, SQL) | Yes, higher DBU rate | **No** (included) | - | Never add hypothetical VM cost |
| Model serving, Vector Search, Apps, Lakebase, AI functions | Product-specific units (DBU, tokens, hours) | Usually no | - | Units are not comparable across products |
| Managed features (predictive optimization, monitoring, FGAC) | Serverless DBU | No | - | Often enabled silently at account/catalog level |
| Storage (ADLS/Blob) | No | Storage meters | Customer storage accounts / DBFS root in managed RG | Shared across products |
| Network (egress, NAT, Private Link, firewall) | Serverless networking SKUs possible | Network meters | Customer VNet RGs | Shared; allocate only with evidence |
| Monitoring (Log Analytics) | No | Monitor meters | Diagnostic settings targets | Shared |

## 3. Azure drill hierarchy vs Databricks hierarchy

| Azure (billed) | Databricks (usage) |
|---|---|
| Billing account → profile → subscription | Account |
| Resource group (incl. managed RG) | Workspace |
| Service name → meter category → meter | `billing_origin_product` → `sku_name` → `usage_unit` |
| Resource ID | `usage_metadata` object ID (job, cluster, warehouse, pipeline, endpoint, app, notebook) |
| Tags | `custom_tags`, `identity_metadata` |

There is **no one-to-one key** between the two hierarchies. Bridges: workspace ↔ managed RG; cluster tags propagated to VMs (`ClusterId`, `ClusterName`, `Creator`, custom tags); SKU ↔ Azure Databricks meter name.

## 4. Decomposition identities

```
Azure Actual Δ  = Σ accounting effects (purchase, credit, FX, scope, correction, calendar)
                + Σ operational bucket Δ (DBX_PLATFORM, DBX_CLASSIC_INFRA, STORAGE, NETWORK, MONITORING)
                + SHARED_UNALLOCATED + OUT_OF_SCOPE

Bucket Δ        = Σ object/driver Δ + unattributed Δ

Cost of a meter = quantity × effective unit price
Δ cost          = volume effect + rate effect               (reference/03 §4)
```

## 5. Meter pattern → first interpretation

| Pattern (B → C) | Most likely | Do not conclude |
|---|---|---|
| DBU ↑ and classic VM ↑ | More classic runtime: runs, duration, workers, idle | That DBU and VM double-count |
| DBU ↑, VM flat | Serverless growth, managed features, list/contract price | That no infrastructure is used |
| VM ↑, DBU flat | Idle pools, spot→on-demand fallback, VM SKU change, reservation coverage loss, non-Databricks VMs | That idle VM belongs to Databricks without RG/tag mapping |
| Storage transactions ↑, capacity flat | More listing/small files, retries, new readers, optimization jobs | That more data is stored |
| Storage capacity ↑ | Retention, new datasets, time travel / VACUUM gaps, replication tier | |
| Network ↑ | Cross-region reads, new egress, NAT/Private Link traffic, data sharing | That all network cost is Databricks |
| Actual ↑, Amortized flat | Purchase timing | Workload growth |
| Modeled ↑, Actual flat | Discount, commitment drawdown, scope mismatch | Invoice error |
| Query count ↑, warehouse cost flat | Cache hits, concurrency absorbed by provisioned capacity | Per-query billing |

## 6. Non-additive rules

1. Never add Azure Actual + Databricks modeled + IBM values.
2. Never add groupings of the same ledger (service subtotal + RG subtotal).
3. Never sum `usage_quantity` across different `usage_unit` values.
4. Never drop negative `RETRACTION` rows - they net out corrections.
5. Never sum IBM direct + shared + allocated unless the model defines them as disjoint.
6. Treat Actual vs Amortized as two recognitions of the same purchases.
