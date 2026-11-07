# Step 03 - Accounting effects · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C3.1 Calendar effect quantified (per-day vs monthly) - bridge ACC-01
- [ ] C3.2 Charge type and pricing model split B vs C reviewed; purchases quantified - ACC-02
- [ ] C3.3 Actual vs Amortized compared; divergence explained - ACC-02
- [ ] C3.4 Commitment coverage (RI / SP / DBCU) B vs C checked; DBCU plan balance and expiry read in Portal → Reservations - ACC-03
- [ ] C3.5 Credits / refunds / adjustments checked - ACC-04
- [ ] C3.6 Scope change checked (subscriptions, workspaces appeared in window) - ACC-07
- [ ] C3.7 FX checked (billing vs pricing currency, rate B vs C) - ACC-06
- [ ] C3.8 Billed unit price (EffectivePrice) of top meters checked - ACC-05
- [ ] C3.9 Databricks list price versions in window checked (3.1) - ACC-05
- [ ] C3.10 Late corrections checked - ACC-08
- [ ] C3.11 Direction check R8 passed or deviation explained
- [ ] C3.12 Operational Δ = TOTAL - Σ ACC recorded in scope §7
- [ ] C3.13 Hypotheses H-RAT-01…11 statuses set in hypothesis_register.csv
- [ ] C3.14 Workspace tier (Standard / Premium) in B vs C checked; tier change date recorded - ACC-05
- [ ] C3.15 Evidence rows EVD-03-nnn added - auto
- [ ] G3 Every accounting test resolved; operational Δ computed

## Required outputs

- `03_accounting_effects/exports/charge_type*.csv` - Cost Analysis by charge type, B and C
- `03_accounting_effects/exports/amortized_monthly*.csv` - Amortized monthly, same scope
- `03_accounting_effects/results/3.1_list_price_history*.csv` - SQL 3.1
- `03_accounting_effects/results/R8_direction_check*` - direction check result
