# 05 · Audit rules R1-R12

<!-- plain -->
> **Overview.** The twelve rules of the method. Most important rules:
>
> - **R1** - only the real Azure bill (Actual) counts as money; other views never get added to it.
> - **R2** - compare per-day rates over a calm period (B) and a high period (C).
> - **R4** - explain at least 90%; show the rest openly.
> - **R6** - the export must match Cost Analysis within 0.5%.
> - **R9** - a cause is *confirmed* only with four proofs.
> - **R12** - the audit is read-only.
>
> The table below is the exact wording; the app refers to the rules by their number.
<!-- /plain -->

Binding for every step. A deviation must be justified in `scope_record.md` §3.

| ID | Rule |
|---|---|
| **R1 Ledgers** | **Azure Actual Cost** is the money truth. Databricks `system.billing.usage × list_prices` is a **diagnostic model** (list price, no discounts). Azure Amortized, IBM Cloudability / ApptioOne are **alternative views**. Never add amounts from different ledgers. |
| **R2 Periods** | Baseline **B** = ≥ 28 consecutive stable days before the onset (default: 2 full months). Comparison **C** = first full month at the elevated level. Persistence **P** = the month after C. Compare **per-day rates** (cost / calendar days) plus absolute monthly totals. |
| **R3 Materiality** | A line is material if `|Δ per day| ≥ 5%` of total `|Δ per day|`, or it is among the top 10 positive movers. All material lines are investigated. |
| **R4 Coverage** | Decomposition stops when explained positive Δ ≥ **90%** of net Δ. The remainder is reported as `UNEXPLAINED`, never spread across drivers. |
| **R5 Onset** | Onset = first day `d` where the 7-day trailing mean exceeds `baseline_mean + max(2σ, 10% × baseline_mean)` and stays above it for **≥ 14 consecutive days**. A shorter excursion is a **spike**. |
| **R6 Reconciliation** | Azure export total vs Cost Analysis total, same scope / month / currency: difference ≤ **0.5%** or explained. |
| **R7 Price model** | Modeled Databricks cost is valid only if **0** usage records have > 1 price match and unpriced records ≤ **1%** per SKU. Otherwise exclude that SKU from modeled-cost conclusions. |
| **R8 Direction check** | Δ% of the Azure *Azure Databricks* meter and Δ% of the Databricks modeled cost (same scope) have the same sign and differ by ≤ **15 pp**. Otherwise investigate discount / commitment / scope before workload analysis. |
| **R9 Evidence** | `CONFIRMED` requires all four: (a) Δ visible in Azure Actual; (b) mechanism timestamp within ±2 days of the driver's onset; (c) mechanism quantity explains ≥ 70% of the driver's Δ; (d) ≥ 1 alternative explanation falsified. |
| **R10 Statuses** | `CONFIRMED` · `LIKELY` (a+b or a+c) · `HYPOTHESIS` (untested) · `REJECTED` (falsified) · `UNKNOWN` (data absent). One vocabulary everywhere. |
| **R11 Currency** | One currency per series. No implicit FX. Databricks list prices are usually USD; Azure billing currency may differ. |
| **R12 Read-only** | No create / modify / delete / start / stop in Azure or Databricks. Running SQL consumes warehouse compute - get approval. |

## Check marking (all `CHECKS.md` files)

| Mark | Meaning | Requirement |
|---|---|---|
| `[ ]` | open | blocks the step |
| `[x]` | done | - |
| `[-]` | not applicable | reason after ` | `, e.g. `[-] C8.5 … | IBM not licensed` |
| `[!]` | done with limitation | limitation after ` | `; recorded in scope §5 / report §7 |
| Gate `G…` | step exit | must be `[x]` |

## Evidence IDs

`EVD-<step>-<nnn>`, e.g. `EVD-04-003`. One evidence row per saved result file; the row names the file, parameters, run time, observation and limits.
