# Step 08 - Validate findings

[07 Attribution and residual](../07_attribution_and_residual/README.md) ← `08` → [09 Report and controls](../09_report_and_controls/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** Before reporting, the results are tested. The application re-runs every saved tool and SQL query with the recorded parameters and verifies that the outputs are identical. A reviewer who did not perform the analysis then examines it and challenges the conclusions.
>
> If IBM Cloudability or ApptioOne is available, the figures can be compared with theirs. Differences are explained, not added.
>
> **Result:** a reproduction log, downgraded statuses where proof was weak, and a reviewer's signature.
>
> **Note:** Rows created manually cannot be re-run by the application and must be verified by hand.
<!-- /plain -->

**Goal:** findings survive independent review; every reported number is reproducible.
**Inputs:** G7 passed. **Work in:** `audits/<id>/08_validation/`.

## Do

| # | Action | Save to (`audits/<id>/08_validation/…`) |
|---|---|---|
| 8.1 | Re-run every query / tool listed in `evidence_register.csv` with the same parameters; compare values - UI calculator 8.1 re-runs tools (and SQL when connected) automatically; resolve `MANUAL` rows by hand | `results/reproduction_log__….md` (evidence_id, rerun value, match Y/N) |
| 8.2 | Re-check R9 for each `CONFIRMED`; downgrade to `LIKELY` if a criterion is missing | `hypothesis_register.csv` |
| 8.3 | Cross-check alternative views: Azure Amortized (step 03), Databricks usage dashboard; **IBM** if licensed ([reference/06](../../reference/06_ibm_apptio_lens.md)) - differences explained, never added | `results/cross_check.md`; `ibm_discrepancy_register.csv` |
| 8.4 | Persistence: does each driver remain in P? Reverted → spike / one-off | driver cards, `notes.md` |
| 8.5 | Independent peer review (someone who did not build the analysis) | `scope_record.md` §8 |

## Automatic checks

- `evidence_register.csv` has evidence rows.
- Every `CONFIRMED` hypothesis references evidence IDs that exist in the register.

## Gate G8

All numbers reproducible; reviewer sign-off in §8.
