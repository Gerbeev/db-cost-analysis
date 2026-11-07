# Step 09 - Report and controls

[08 Validation](../08_validation/README.md) ← `09` · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** The final step converts the analysis into an actionable result: a report with the delta bridge, one finding per cause, a remediation list with owners, and alerts that detect the next increase within days instead of months.
>
> A saving exists only when it is visible in the actual bill. Until then it is a plan.
>
> **Result:** `findings_report.md` with the bridge table, a fix list and a control plan.
>
> **Note:** The bridge table in the report must be identical to delta_bridge.csv.
<!-- /plain -->

**Goal:** an approved findings report, remediation backlog and control plan.
**Inputs:** G8 passed. **Work in:** `audits/<id>/09_report_and_controls/findings_report.md`.

## Do

| # | Action | Where |
|---|---|---|
| 9.1 | Executive summary: one sentence per confirmed driver with currency/day and share | report §1 |
| 9.2 | Size/timing table, charts (monthly per-day series; daily series with R5 threshold) | report §2 |
| 9.3 | Delta bridge copied from `delta_bridge.csv` (UI action 9.1 renders it as a markdown table) | report §3 |
| 9.4 | One finding block per driver (from driver cards) | report §4 |
| 9.5 | Rejected hypotheses, residual, limitations | report §5-§7 |
| 9.6 | Remediation per driver: change, savings **range**, risk, guardrail metric, rollback, owner, validation ([reference/08](../../reference/08_remediation_and_controls.md)) | report §8 |
| 9.7 | Control plan: budgets / alerts, compute policies, weekly top-mover review, tag coverage target | report §8 |
| 9.8 | Approval by audit owner; remediation owners named | report §9 |

Savings are claimed only after post-change measurement on Azure Actual (≥ 14 days, same method).

## Automatic checks

- `findings_report.md` has no unfilled `____` placeholders (warning).

## Gate G9

Report approved; every remediation item has an owner.
