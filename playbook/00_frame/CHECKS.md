# Step 00 - Frame · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C0.1 Trigger recorded: who, which report, which metric (scope_record §1)
- [ ] C0.2 Audit question stated on Azure Actual Cost with scope S, B and C (§1)
- [ ] C0.3 Scope complete: billing account/profile, subscriptions, workspaces with regions (§2)
- [ ] C0.4 Managed RG per workspace and dependency RGs listed (§2)
- [ ] C0.5 Window = full months only; current month-to-date excluded (§3) - auto
- [ ] C0.6 Provisional B / C / P written (§3) - auto
- [ ] C0.7 Billing currency, agreement type, contracts with dates recorded (§2-§3)
- [ ] C0.8 Every source in §4 has status OK / DENIED / UNKNOWN
- [ ] C0.9 Rule deviations recorded or "none" (§3)
- [ ] G0 Audit owner approved scope (name + date in §8)

## Required outputs

- `scope_record.md` - §1-§4 filled
