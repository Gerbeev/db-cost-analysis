# Step 02 - Confirm and size the increase

[01 Data quality](../01_data_quality/README.md) ← `02` → [03 Accounting effects](../03_accounting_effects/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** This step confirms that the increase is real and quantifies it. Months contain 28 to 31 days, so a longer month appears more expensive without any change in consumption. All comparisons therefore use cost per day.
>
> The application builds the monthly table, identifies the day the cost level changed, and calculates the additional cost per day, per month and per year at the new level. The final periods B, C and P are then fixed from the actual onset date.
>
> **Result:** the growth in money per day and per year, the start date, the shape of the growth, and the total line of the delta bridge.
>
> **Note:** If the increase is a one-off excursion shorter than 14 days, record it as a spike, not as a trend.
<!-- /plain -->

**Goal:** prove the increase exists on Azure Actual, size it per day, date its onset, set final B / C / P.
**Inputs:** G1 passed; `01_data_quality/exports/azure_actual*.csv`. **Work in:** `audits/<id>/02_confirm_and_size/`.
**Formulas:** [reference/03 §1-2](../../reference/03_analysis_method.md).

## Do

| # | Action | Tool | Save to (`audits/<id>/02_confirm_and_size/…`) |
|---|---|---|---|
| 2.1 | Monthly series with per-day rates (full scope, no service filter) | UI action 2.1 | `results/monthly_series.csv` |
| 2.2 | Daily Actual cost, about 90 days around the suspected change (the portal allows at most 3 months per daily range) | Cost Analysis → Actual, Daily → Download (or reuse the export) | `exports/cost_analysis_daily__<from>_<to>.csv` |
| 2.3 | Onset on Azure Actual (rule R5) | UI action 2.3 (baseline pre-filled with B) | `results/onset_azure.csv` + onset date in §6 |
| 2.4 | Onset cross-check on Databricks modeled cost | [`sql/2.1_daily_cost_onset.sql`](sql/2.1_daily_cost_onset.sql) | `results/2.1_daily_cost_onset__….csv` |
| 2.5 | Monthly modeled cost by SKU (also input for the analyzer, UI action 2.9, and R8) | [`sql/2.2_monthly_cost_by_sku.sql`](sql/2.2_monthly_cost_by_sku.sql) | `results/2.2_monthly_cost_by_sku__….csv` |
| 2.6 | Set final B / C / P from the onset (R2: B ≥ 28 stable days before onset; C = first full elevated month; P = month after C) | UI action 2.6 | `scope_record.md` §3 |
| 2.7 | Compute Δ_abs = C - B, Δ_day = C/d(C) - B/d(B), Δ_day %, ×365, persistence r(P) - r(C) | UI action 2.7 (writes §6 and the bridge `TOTAL` row) | `scope_record.md` §6 |
| 2.8 | Classify shape: step / ramp / spike / seasonal | - | §6 |
| 2.9 | Fill the `TOTAL` row of the bridge (per-day B, C, delta, currency) | done by UI action 2.7 | `delta_bridge.csv` |
| 2.10 | Evidence rows `EVD-02-nnn` | added automatically by every UI run / upload; check C2.9 is ticked by the app | `evidence_register.csv` |

## Automatic checks

- `delta_bridge.csv` `TOTAL` row has a numeric `delta_per_day`.

## Gate G2

`Δ_day > 0` on Azure Actual at fixed scope **and** shape classified.
**If Δ_day ≤ 0:** the "growth" is a view artefact (amortized, allocation, list-price model, month length). Record that in §6, do step 03 to explain it, mark steps 04-07 `[-] | artefact path`, go to step 09.
