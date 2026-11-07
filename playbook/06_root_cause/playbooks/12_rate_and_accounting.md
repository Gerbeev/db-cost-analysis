# PB-RATE

<!-- plain -->
> **Overview.** Use for the effects from step 03: a price change, an ended commitment or credit, a currency move. These are not about workload, so the proof is in billing data and contracts, not in Databricks.
<!-- /plain -->

**Signals:** Step 3 found non-operational effects; onset on the 1st of a month; Actual ≠ Amortized; R8 direction check failed.

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-RAT-01 | Reservation / savings plan purchase booked in Actual | `ChargeType = Purchase` in C; Amortized flat | No purchase rows |
| H-RAT-02 | Commitment coverage expired or exhausted (RI / SP / DBCU pool) | `PricingModel` shifts Reservation → OnDemand; DBU meters that showed 0 on-demand cost while the DBCU pool lasted now show cost; DBCU plan balance 0 / expired (Portal → Reservations) | Pricing model mix unchanged; DBCU balance remaining |
| H-RAT-03 | Credits expired / reduced | Credit lines in B absent in C; billing profile credit balance | Credits unchanged |
| H-RAT-04 | Contract discount change | `EffectivePrice` ↑ at contract date; Databricks list flat | Effective price flat |
| H-RAT-05 | List price change | [`3.1_list_price_history.sql`](../../03_accounting_effects/sql/3.1_list_price_history.sql) new price version ≈ onset; `5.1` rate effect | No new version |
| H-RAT-06 | FX change | Billing currency ≠ pricing currency; rate change at month boundary | Same currency or stable rate |
| H-RAT-07 | Scope expansion | New subscription / workspace first billed in C | Same scope list |
| H-RAT-08 | Export duplication | Duplicate run IDs / overlapping snapshots; export total > Cost Analysis | R6 passes |
| H-RAT-09 | Late correction / restatement | Re-export differs; `RETRACTION`/`RESTATEMENT` spike | Stable |
| H-RAT-10 | Calendar effect only | Per-day Δ ≈ 0 | Per-day Δ > 0 |
| H-RAT-11 | Workspace tier change Standard → Premium (auto-upgrade 1 Oct 2026) | DBU unit price steps up on one date with flat quantity; SKU names change `STANDARD_*` → `PREMIUM_*`; workspace properties / Activity Log show tier change | Workspace already Premium in B |

**Remediation options:** renew/resize commitments; align purchase timing reporting (use Amortized for operational KPIs); fix export pipeline.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
