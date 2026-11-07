# Step 07 - Attribution and residual · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C7.1 Owner recorded for every CONFIRMED / LIKELY bridge line
- [ ] C7.2 Shared resources allocated with an evidenced key, or in SH-01
- [ ] C7.3 Unattributed / untagged Databricks Δ quantified
- [ ] C7.4 Out-of-scope Δ in OOS-01
- [ ] C7.5 Bridge identity holds within 1% - auto
- [ ] C7.6 UNEXPLAINED ≤ 10% of TOTAL (R4) - auto; or `[!] | accepted by <owner>`
- [ ] C7.7 Evidence rows EVD-07-nnn added - auto
- [ ] G7 Bridge closes; residual within R4 or accepted

## Required outputs

- `delta_bridge.csv` - complete bridge
- `07_attribution_and_residual/results/shared_allocation*.csv` - allocation keys (optional) if shared resources exist
