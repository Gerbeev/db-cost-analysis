# 00 · Fundamentals - how Azure Databricks costs are formed

<!-- plain -->
> **Overview.** Prerequisite reading for anyone new to Azure Databricks cost (about 15 minutes). Key points:
>
> 1. Databricks is billed **within the Azure invoice**; there is no separate Databricks invoice.
> 2. Compute is charged in **DBU**; classic compute additionally incurs the cost of the underlying virtual machines.
> 3. The DBU price depends on the compute type: identical work costs very different amounts on different types.
> 4. Storage, network and monitoring are billed separately from compute.
> 5. A bill can rise because of **accounting** (a discount ended, a price changed) without more consumption; the audit separates the two.
>
> Terms are defined in the [glossary](14_glossary.md).
<!-- /plain -->

Minimum theory needed before an audit. ~15 minutes. Details: [01 cost model](01_cost_model.md), formulas: [03 analysis method](03_analysis_method.md), terms: [14 glossary](14_glossary.md).
Prices below are **illustrative**; real rates depend on region, tier, contract and currency - always take them from your bill or `system.billing.list_prices`.

## 1. Architecture → where money is spent

```
 Databricks control plane (Databricks-run)       UI, jobs scheduler, notebooks, Unity Catalog metadata   → no separate line
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Compute plane, CLASSIC  (your subscription,      VMs, managed disks, public IPs, load balancer           → Azure infra meters
   managed RG per workspace)                      + Databricks platform fee per DBU                        → Azure Databricks meter
 Compute plane, SERVERLESS (Databricks-run)       compute included in a higher DBU price                   → Azure Databricks meter
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Your storage accounts (ADLS / Blob)              data, Delta logs, checkpoints, DBFS root                 → Storage meters
 Your network (VNet, NAT, Private Link, FW)       egress, data processing, endpoint hours                  → Network meters
 Your monitoring (Log Analytics)                  diagnostic logs ingestion / retention                    → Monitor meters
```

Azure Databricks is a first-party Azure service: **everything arrives on the Azure bill**; there is no separate Databricks invoice.

## 2. The bill = 5 layers

| # | Layer | What you pay for | Driver (what makes it grow) | Azure meter / source |
|---|---|---|---|---|
| 1 | **Databricks platform (DBU)** | DBUs × $/DBU per SKU | node-hours, node size, compute type, Photon, serverless use, features | *Azure Databricks* meters; `system.billing.usage` |
| 2 | **Classic infrastructure** | VM hours, managed disks, public IP, LB | node-hours, VM family, spot vs on-demand, idle pools | Virtual Machines, Managed Disks… in managed RG |
| 3 | **Data** | storage capacity, transactions, replication | data volume, retention, small files, read/write frequency | Storage |
| 4 | **Network & ops** | egress, NAT / Private Link processing, firewall, log ingestion | cross-region reads, new endpoints, verbose diagnostics | Bandwidth, NAT Gateway, Private Link, Log Analytics |
| 5 | **Financial** | commitments, credits, discounts, FX, tax | contract events, not workload | Charge type, Pricing model, invoice |

Layers 1-2 usually dominate Databricks-related spend; layer 5 can move the bill with zero workload change.

## 3. DBU - the core unit

- **DBU (Databricks Unit)** = normalized unit of processing capacity per hour, **billed per second**.
- **DBU/hour of a node** is fixed by **VM size** (bigger VM → more DBU/h). Photon increases the DBU count.
- **$ per DBU** is fixed by **SKU** = compute type × tier × (serverless or classic) × region, minus contract discount.

| Compute type (SKU family) | Used for | Relative $/DBU | VM billed separately? |
|---|---|---|---|
| Jobs Light | simple scheduled non-Spark tasks | lowest | yes |
| **Jobs** | scheduled job clusters | low | yes |
| SQL classic / **SQL Pro** | classic / pro SQL warehouses | low-mid | yes |
| Pipelines (Lakeflow / DLT) Core / Pro / Advanced | declarative pipelines | rises with edition | yes (classic) |
| **All-Purpose** | interactive notebooks, shared clusters | high (≈ 1.8× Jobs at list) | yes |
| **Serverless** (jobs, notebooks, pipelines, SQL) | Databricks-managed compute | highest per DBU | **no - included** |
| Model serving, Vector Search, Apps, Lakebase, AI functions | AI / apps | product-specific units | usually no |

Same job, same VM: on All-Purpose it costs noticeably more than on a Jobs cluster - compute-type choice is a top cost lever.

## 4. Cost formulas

**Classic cluster, per hour**
```
cost/h = Σ nodes [ DBU/h(node size, Photon) × $/DBU(SKU) ]  +  Σ nodes [ VM $/h ]  (+ disks, IP)
```
Illustrative: 1 driver + 4 workers, 1.5 DBU/h each, Jobs $0.30/DBU, VM $0.50/h
→ 5 × (1.5 × 0.30 + 0.50) = **$4.75/h**; the same on All-Purpose at $0.55/DBU → 5 × (0.825 + 0.50) = **$6.63/h**.

**Serverless, per hour**
```
cost/h = DBU/h(size or workload) × multiplier(feature) × $/DBU(serverless SKU)     - no VM line
```
Serverless SQL warehouse sizes (DBU/h): 2X-Small 4 · X-Small 6 · Small 12 · Medium 24 · Large 40 · X-Large 80 · 2X-Large 144.
Feature multipliers exist (e.g. data-quality monitoring 2×, Databricks Apps medium 0.5×) - see Microsoft "Serverless DBU consumption by SKU".

**Workload view (what an audit decomposes)**
```
cost/day = executions/day × duration × nodes × (DBU/h × $/DBU + VM $/h)
           └ frequency ┘   └──── unit cost per execution ────────────┘
```
Each factor maps to a typical root cause: more runs, longer runs, bigger clusters, pricier SKU, higher price.

## 5. Tiers and 2026 changes

| Fact | Audit impact |
|---|---|
| Tiers on Azure: **Standard** and **Premium** (Unity Catalog, RBAC, SQL warehouses, serverless only on Premium) | Premium $/DBU is higher than Standard |
| No new Standard workspaces since **1 Apr 2026**; remaining Standard workspaces auto-upgraded to Premium on **1 Oct 2026** | A rate step on 1 Oct 2026 with flat usage = tier change, not workload (H-RAT-11) |

## 6. Discounts and commitments

| Instrument | Covers | Mechanics | How it looks in the bill |
|---|---|---|---|
| **DBCU pre-purchase** (1 or 3 years) | DBU charges, all workloads/tiers | prepaid pool; usage draws it down at its list-price ratio; earliest-expiring plan used first; up to ~37% off | while covered, DBU usage shows **0** on-demand cost; purchase is one Actual line. **Pool exhausted or expired → DBU costs suddenly appear in Actual** (H-RAT-02) |
| **VM reservations** (1 / 3 years) | classic VMs only | per-hour usage commitment | Actual: purchase line; Amortized: spread over term |
| **Savings plan for compute** | classic VMs (and other compute) | hourly spend commitment | same |
| **Spot VMs** | classic workers | deep discount, can be evicted; fallback to on-demand raises cost | Pricing model *Spot* vs *OnDemand* |
| **Negotiated discount / MACC** | per contract | effective price below list | `EffectivePrice` < list; Databricks `list_prices` does **not** show it |

Serverless has no VM line, so VM reservations / savings plans do not apply to it - moving workloads to serverless can strand VM commitments.

## 7. Azure billing basics

| Concept | Meaning |
|---|---|
| Billing account type | **EA** (Enterprise Agreement), **MCA** (Microsoft Customer Agreement), MPA (partner/CSP) - column names in exports differ |
| Scope | billing account → billing profile → subscription → resource group; costs are always "at a scope" |
| Meter | the billable item with its own unit price (e.g. *Premium Jobs Compute DBU*, *D8s v5*, *Hot LRS Data Stored*) |
| **Actual cost** | as charged; purchases appear in the purchase month → spikes |
| **Amortized cost** | purchases spread over their term → use for operational trends |
| Charge type | Usage, Purchase, Refund, Adjustment |
| Pricing model | OnDemand, Reservation, SavingsPlan, Spot |
| Cost details export | row-level data (date, meter, quantity, effective price, cost, resource, tags) - the audit's raw material |

## 8. Where growth usually comes from (check in this order)

| # | Typical cause | Signal | Playbook |
|---|---|---|---|
| 1 | Commitment / credit / tier / price event | step on the 1st of a month, Actual ≠ Amortized, quantity flat | [12 rate](../playbook/06_root_cause/playbooks/12_rate_and_accounting.md) |
| 2 | New or more frequent jobs, backfills | `JOBS` DBU ↑, runs/day ↑ | [01 jobs](../playbook/06_root_cause/playbooks/01_jobs.md) |
| 3 | Idle / oversized all-purpose clusters | `ALL_PURPOSE` DBU + VM ↑, low CPU | [03 classic](../playbook/06_root_cause/playbooks/03_classic_compute.md) |
| 4 | SQL warehouses up longer / bigger, BI polling | `SQL` DBU ↑, warehouse uptime ↑ | [05 SQL](../playbook/06_root_cause/playbooks/05_sql_warehouses.md) |
| 5 | Pipelines switched to continuous / full refresh | `DLT` DBU ↑ | [02 pipelines](../playbook/06_root_cause/playbooks/02_pipelines.md) |
| 6 | Serverless adoption / managed features switched on | new serverless SKUs | [06](../playbook/06_root_cause/playbooks/06_serverless.md), [08](../playbook/06_root_cause/playbooks/08_platform_features.md) |
| 7 | Data growth → longer runs, storage, transactions | duration ↑, Storage ↑ | [09 storage](../playbook/06_root_cause/playbooks/09_storage.md) |
| 8 | Network / logging side effects | NAT, egress, Log Analytics ↑ | [10](../playbook/06_root_cause/playbooks/10_network.md), [11](../playbook/06_root_cause/playbooks/11_monitoring.md) |

## 9. Where to see each number

| Question | Source |
|---|---|
| What did we pay? | Azure Cost Management → Cost analysis (Actual) / Exports |
| What did Databricks consume (DBU, by job/cluster/warehouse)? | `system.billing.usage` |
| What is the list price per SKU over time? | `system.billing.list_prices` |
| What did we really pay per unit? | Azure export `EffectivePrice` |
| How are clusters / warehouses / jobs configured and when did it change? | `system.compute.*`, `system.lakeflow.*` (history) |
| Who changed what? | `system.access.audit`, Azure Activity Log |
| Commitment balance and expiry | Azure portal → Reservations (DBCU plan, VM reservations) |

## 10. Rules of thumb

1. The invoice (Azure Actual) is the truth; Databricks list-price cost is a **model** - never add the two.
2. Classic = DBU **and** VM; serverless = DBU only.
3. Compare **cost per day**, not per month.
4. Most growth = more node-hours (runs × duration × nodes) or a more expensive SKU; price changes are rarer but sudden.
5. A step on the 1st of a month → look at contracts before workloads.
6. Commitments hide cost while they last; their end looks like growth.
7. All-purpose compute for scheduled work and missing auto-termination are the most common waste.
8. Every growth claim needs a dated change event behind it.

## Sources

- [Azure Databricks pricing](https://azure.microsoft.com/en-us/pricing/details/databricks/) - DBU definition, compute types, Photon note, serverless SQL sizes, Standard tier retirement notice, DBCU tiers
- [Serverless DBU consumption by SKU](https://learn.microsoft.com/en-us/azure/databricks/resources/pricing) - serverless SKUs and DBU multipliers
- [Optimize Azure Databricks costs with a pre-purchase](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepay-databricks-reserved-capacity) - DBCU drawdown ratios
- [How the Databricks pre-purchase discount is applied](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/reservation-discount-databricks) - earliest-expiring plan first; on-demand charges shown as zero
- [Billable usage system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing), [Pricing system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/pricing)
- [Cost analysis - Actual vs Amortized](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-analysis-common-uses)
