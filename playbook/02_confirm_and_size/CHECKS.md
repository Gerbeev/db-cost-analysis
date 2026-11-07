# Step 02 - Confirm and size · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C2.1 Monthly series with per-day rates produced from the Step-01 export (no service filter) - auto
- [ ] C2.2 Daily series covers ≥ 30 days before and ≥ 30 days after the suspected change
- [ ] C2.3 Onset on Azure Actual per R5 recorded (date, or "spike only" with start/end)
- [ ] C2.4 Databricks modeled onset (2.1) compared; difference in days recorded (±1 day expected)
- [ ] C2.5 Final B / C / P set per R2 in scope §3 (B ≥ 28 stable days, C full elevated month, P month after C)
- [ ] C2.6 Δ_abs, Δ_day, Δ_day %, annualized and persistence recorded in §6 - auto
- [ ] C2.7 Shape classified (step / ramp / spike / seasonal); seasonal checked against prior year if data exists
- [ ] C2.8 delta_bridge.csv TOTAL row filled (cost_per_day_b, cost_per_day_c, delta_per_day, currency) - auto
- [ ] C2.9 Evidence rows EVD-02-nnn added - auto
- [ ] G2 Δ_day > 0 on Azure Actual at fixed scope - or artefact path decided and recorded in §6

## Required outputs

- `02_confirm_and_size/results/monthly_series*.csv` - monthly totals and per-day rates
- `02_confirm_and_size/exports/cost_analysis_daily*.csv` - daily Actual cost (optional) if the export is used instead
- `02_confirm_and_size/results/onset_azure*.csv` - onset_detect output on Azure Actual
- `02_confirm_and_size/results/2.1_daily_cost_onset*.csv` - SQL 2.1
- `02_confirm_and_size/results/2.2_monthly_cost_by_sku*.csv` - SQL 2.2
