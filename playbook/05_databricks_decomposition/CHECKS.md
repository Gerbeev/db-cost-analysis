# Step 05 - Databricks decomposition · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C5.1 Only R7-passing SKUs used for money conclusions
- [ ] C5.2 5.1: top SKUs classified as volume-driven or rate-driven; MIX_SHIFT pairs (GONE + NEW) netted
- [ ] C5.3 5.2: workspace concentration of the delta noted
- [ ] C5.4 5.3: objects listed until cumulative_share ≥ 0.90 - auto
- [ ] C5.5 5.4: onset date of each top object compared with total onset (±2 days)
- [ ] C5.6 5.5: unattributed / untagged delta quantified
- [ ] C5.7 5.6: new products / SKUs in window listed with first_seen date
- [ ] C5.8 DRIVER_CANDIDATE lines added to delta_bridge.csv
- [ ] C5.9 Hypotheses opened for each candidate in hypothesis_register.csv
- [ ] C5.10 Evidence rows EVD-05-nnn added - auto
- [ ] G5 Top objects explain ≥ 90% of modeled DBX delta, or remainder quantified

## Required outputs

- `05_databricks_decomposition/results/5.1_sku_volume_rate*.csv` - SQL 5.1
- `05_databricks_decomposition/results/5.2_workspace_delta*.csv` - SQL 5.2
- `05_databricks_decomposition/results/5.3_object_delta*.csv` - SQL 5.3
- `05_databricks_decomposition/results/5.4_object_daily*.csv` - SQL 5.4
- `05_databricks_decomposition/results/5.5_attribution_coverage*.csv` - SQL 5.5
- `05_databricks_decomposition/results/5.6_first_seen_skus*.csv` - SQL 5.6
