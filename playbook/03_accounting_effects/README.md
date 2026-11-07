# Step 03 - Remove accounting and rate effects

[02 Confirm and size](../02_confirm_and_size/README.md) ← `03` → [04 Azure decomposition](../04_azure_decomposition/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** A bill can increase without additional consumption: a reservation expired, a credit ran out, a subscription joined the scope, the exchange rate moved, the workspace tier changed. These are accounting effects, not technical defects. Mixing them with consumption growth directs engineering effort at causes that do not exist.
>
> This step tests each accounting cause, quantifies it and subtracts it from the total. The remainder is the operational growth, which the rest of the audit explains.
>
> **Result:** lines ACC-01 to ACC-08 in the delta bridge and the operational growth in section 7.
>
> **Note:** Enter 0 for a cause without effect. An empty cell is indistinguishable from an unchecked cause.
<!-- /plain -->

**Goal:** separate non-operational movement (calendar, purchases, credits, FX, scope, price, corrections) from consumption growth **before** any workload analysis.
**Inputs:** G2 passed; B / C fixed. **Work in:** `audits/<id>/03_accounting_effects/`.
**Hypotheses covered:** `H-RAT-01 … H-RAT-11`. Background (commitments, tiers, Actual vs Amortized): [reference/00 §5-7](../../reference/00_fundamentals.md) ([playbook PB-RATE](../06_root_cause/playbooks/12_rate_and_accounting.md)).

## Do

| # | Test | How | Save to (`audits/<id>/03_accounting_effects/…`) | Bridge line |
|---|---|---|---|---|
| 3.1 | **Calendar** | Per-day Δ vs monthly Δ from step 02 (Feb 28 d → Mar 31 d = +10.7% at flat usage) | - | `ACC-01` |
| 3.2 | **Purchases / commitments** | Cost Analysis, Actual, group by *Charge type* and *Pricing model*, B and C | `exports/charge_type__B_C.csv`, `exports/pricing_model__B_C.csv` | `ACC-02`, `ACC-03` |
| 3.3 | **Actual vs Amortized** | Cost Analysis **Amortized**, monthly, same scope | `exports/amortized_monthly.csv` | `ACC-02` |
| 3.4 | **Credits / refunds / adjustments** | Charge type Refund / Adjustment; credit balances and expiry dates in billing profile | `exports/credits__B_C.csv` (optional) | `ACC-04` |
| 3.5 | **Scope change** | Subscriptions B vs C (UI action 3.5); workspaces `APPEARED_IN_WINDOW` from step 01 | `results/delta_by_subscription_scope.csv` | `ACC-07` |
| 3.6 | **FX** | Billing currency vs pricing currency; rate B vs C | notes.md | `ACC-06` |
| 3.7 | **Billed rate change** | Top meters: `EffectivePrice` B vs C (export columns `MeterName`, `EffectivePrice`, `Quantity`) | `results/effective_price_top_meters.csv` (optional) | `ACC-05` |
| 3.7b | **Tier change** | Workspace properties / Activity Log: Standard → Premium (auto-upgrade 1 Oct 2026); SKU names `STANDARD_*` → `PREMIUM_*` in 1.2 | notes.md | `ACC-05` |
| 3.8 | **List price change** | [`sql/3.1_list_price_history.sql`](sql/3.1_list_price_history.sql) | `results/3.1_list_price_history__….csv` | `ACC-05` |
| 3.9 | **Late corrections** | Re-export one month and compare; `RETRACTION` / `RESTATEMENT` counts from 1.1 | notes.md | `ACC-08` |
| 3.10 | **Direction check (R8)** | Δ% of Azure meter *Azure Databricks* vs Δ% of modeled cost (2.2) - same sign, ≤ 15 pp apart (UI calculator) | `results/R8_direction_check.md` | - |

Then: `operational Δ = TOTAL Δ - Σ ACC lines` → scope_record §7 (UI calculator *Operational Δ*). Evidence rows `EVD-03-nnn`.

## Gate G3

Every test is `PASS / EFFECT QUANTIFIED / N/A` in §7; operational Δ computed. If R8 fails, resolve discount / commitment / scope before step 05.
