# Playbook - Azure Databricks cost-growth audit

<!-- plain -->
> **Overview.** The playbook is ten steps done in order. Each step answers one question and ends with a **gate** - a check you must tick before moving on. You never need to type a command: every action is a button on the step page of the app, and every result is saved in your audit folder.
>
> Sequence: *agree on the question (00) → trust the data (01) → prove the growth (02) → remove accounting effects (03) → find where the money went in Azure (04) and in Databricks (05) → find the cause (06) → check the numbers add up (07) → have someone repeat them (08) → write it up (09).*
<!-- /plain -->

Prerequisite knowledge: [reference/00_fundamentals.md](../reference/00_fundamentals.md).

Ten steps, executed in order. Each step folder has:

- `README.md` - what to do, which tool/SQL, **where each result is saved** in your audit workspace. In the interface every row is an action on the step page.
- `CHECKS.md` - the tick-list for the step (copied into the audit when it is created in the interface). The step closes when every line is resolved, required outputs exist and automatic checks pass - the step page shows all three live.
- `sql/` - read-only Databricks SQL for the step (where needed).

| Step | Question it answers | Gate |
|---|---|---|
| [00 Frame](00_frame/README.md) | What exactly are we auditing - scope, periods, currency, ledger? | G0 scope approved |
| [01 Data quality](01_data_quality/README.md) | Is the data complete, deduplicated, single-currency, priceable? | G1 R6 + R7 pass |
| [02 Confirm and size](02_confirm_and_size/README.md) | Did billed cost really grow, by how much per day, since when? | G2 Δ/day > 0, onset dated |
| [03 Accounting effects](03_accounting_effects/README.md) | How much is calendar / purchases / credits / FX / scope / price? | G3 operational Δ computed |
| [04 Azure decomposition](04_azure_decomposition/README.md) | Which Azure services / meters / resources were billed more? | G4 buckets reconcile |
| [05 Databricks decomposition](05_databricks_decomposition/README.md) | Which products / SKUs / workspaces / objects consumed more? | G5 ≥ 90 % covered |
| [06 Root cause](06_root_cause/README.md) | What changed, when, and how much does it explain? | G6 no driver left as hypothesis |
| [07 Attribution and residual](07_attribution_and_residual/README.md) | Who owns each part; what is unexplained? | G7 bridge closes, residual ≤ 10 % |
| [08 Validation](08_validation/README.md) | Are the numbers reproducible and the claims evidenced? | G8 reviewer sign-off |
| [09 Report and controls](09_report_and_controls/README.md) | What do we report, fix and monitor? | G9 report approved |

```
00 Frame → 01 Data quality → 02 Confirm & size → 03 Accounting effects → 04 Azure decomposition
                                                                                │
09 Report ← 08 Validation ← 07 Attribution & residual ← 06 Root cause ← 05 Databricks decomposition
```

## Rules that apply to every step

[reference/05_audit_rules.md](../reference/05_audit_rules.md) - R1 ledgers · R2 periods · R3 materiality · R4 coverage · R5 onset · R6 reconciliation · R7 price model · R8 direction check · R9 evidence · R10 statuses · R11 currency · R12 read-only.

Stop rules (when not to compute anything): [reference/04](../reference/04_pitfalls_and_stop_rules.md).

## Living registers (audit root, updated across steps)

| File | Started | Updated in |
|---|---|---|
| `scope_record.md` | 00 | 01 (§5), 02 (§3, §6), 03 (§7), 08 (§8) |
| `evidence_register.csv` | 01 | every step - one row per saved result, ID `EVD-<step>-<nnn>` |
| `delta_bridge.csv` | 02 | 03 (ACCOUNTING), 04 (BUCKET), 05 (DRIVER_CANDIDATE), 06 (ROOT_CAUSE), 07 (SH, OOS, UNX) |
| `hypothesis_register.csv` | 03 | 03, 05, 06, 08 |

## Fast path (first 2 hours)

To find the dominant driver quickly, run only: 02 (2.1, 2.3, 2.7) → 03 (3.2, 3.3) → 04 (4.1) → 01 (1.8 price join) → 05 (5.1, 5.3) → 06 (one playbook). Everything found this way is `LIKELY` until steps 07-08 are completed.
