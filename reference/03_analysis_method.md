# 03 · Analysis method - formulas and decision rules

<!-- plain -->
> **Overview.** The formulas behind the app, written once so anyone can check them: cost per day, growth, the day it started, volume versus price, and how the delta bridge adds up. You do not need it to use the app, but you need it to explain a number to a skeptical colleague.
<!-- /plain -->

Notation: **B** baseline period, **C** comparison period, **P** persistence period, `d(X)` = calendar days in period X, `cost(X)` = total cost in X in one currency and one ledger.

## 1. Size of the change

| Metric | Formula | Use |
|---|---|---|
| Absolute monthly Δ | `cost(C) - cost(B)` | Budget impact of the specific months |
| Per-day rate | `r(X) = cost(X) / d(X)` | Removes month-length effect |
| Per-day Δ | `Δr = r(C) - r(B)` | **Primary size metric** |
| Relative Δ | `Δr / r(B)` (only if `r(B) > 0`) | Communication |
| Annualized run-rate impact | `Δr × 365` | Prioritization |
| Persistence | `r(P) - r(C)` | ≈ 0 → step persisted; ≈ -Δr → spike reverted |
| Calendar effect | `cost(C) - r(B) × d(C)` vs `cost(C) - cost(B)` | Shows how much monthly Δ is only day count |

Month lengths 2026: Jan 31, Feb 28, Mar 31, Apr 30, May 31, Jun 30, Jul 31, Aug 31, Sep 30, Oct 31. Flat usage Feb → Mar shows **+10.7%** monthly.

## 2. Onset detection (rule R5)

Input: daily cost series (Azure Actual daily or Databricks modeled daily).

1. Baseline statistics on B: `μ = mean(daily)`, `σ = stdev(daily)`.
2. Threshold `T = μ + max(2σ, 0.10 × μ)`.
3. `m(d)` = trailing 7-day mean ending on day `d`.
4. **Onset** = first `d` after B such that `m(d') > T` for all `d' ∈ [d, d+13]`.
5. If `m > T` for fewer than 14 consecutive days → **spike** (record start/end).
6. Weekly seasonality: the 7-day mean removes weekday pattern; also compare weekday-only means if workloads are weekday-heavy.

Implemented in `tools/onset_detect.py` and `2.1_daily_cost_onset.sql`.

Interpretation:
- Total onset vs object onset (Step 5.4): the driver's onset must match the total onset (±2 days) to be the trigger; a later onset = additional driver.
- Onset at month boundary (1st) → suspect billing/price/commitment/scope events before workload.

## 3. Contribution analysis (one grouping at a time)

For grouping key `k` (service, meter, SKU, workspace, object):

```
Δr_k        = r_k(C) - r_k(B)
share_k     = Δr_k / Δr_total               (can be < 0 or > 100%)
coverage(n) = Σ_{top n positive} Δr_k / Δr_total
```

Rules:
- Rank by `Δr_k` (currency/day), not by % growth.
- Keep negative contributors; `Σ Δr_k = Δr_total` must hold for a complete grouping.
- Never mix two groupings in one waterfall.
- Materiality (R3): `|Δr_k| ≥ 0.05 × |Δr_total|` or top-10 positive.
- Change class per key: `NEW` (`r_k(B)=0`), `GONE` (`r_k(C)=0`), `GROWN` (Δ > 0), `SHRUNK` (Δ < 0), `FLAT` (`|Δr_k| < 1% of r_k(B)`).

## 4. Volume vs rate decomposition

For one meter/SKU with a single unit:

```
Q = quantity per day, p = effective unit price = cost / quantity

Δcost = (Q_C - Q_B) × p_B        ← volume effect
      + (p_C - p_B) × Q_C        ← rate effect
```

Exact identity (no residual). For a `NEW` item, `p_B` := `p_C` → all volume. Rate effect on Databricks modeled cost reflects **list price** changes only; the billed rate effect comes from Azure `EffectivePrice` (Step 3.6).

**Mix effect** (several SKUs with different prices, e.g. jobs → all-purpose, classic → serverless): compute volume/rate per SKU, then sum. A shift of the same workload between SKUs appears as `GONE` on one SKU + `NEW` on another; net them in the bridge and label `MIX_SHIFT`.

Implemented in `5.1_sku_volume_rate.sql`.

## 5. Frequency × unit-cost decomposition (workloads)

For a job, pipeline or warehouse:

```
cost/day = executions/day × cost/execution

Δcost = (n_C - n_B) × c_B       ← frequency effect (more runs/updates/queries)
      + (c_C - c_B) × n_C       ← unit-cost effect (longer, bigger, retried, more data)
```

Unit-cost effect splits further:
```
cost/execution = duration × (nodes or DBU/hour) × price
```
Use: run duration (job_run_timeline), cluster size (clusters SCD2), DBU/hour (usage ÷ duration).

Implemented for jobs in `6.01_job_cost_per_run.sql`.

## 6. Classic compute: DBU vs VM consistency

For classic workloads both meters move with node-hours:
```
VM cost ≈ node_hours × VM price          DBU ≈ node_hours × DBU/node-hour
```
- Both ↑ proportionally → more node-hours (runtime/workers/idle).
- VM ↑ ≫ DBU ↑ → idle pool instances, spot fallback to on-demand, VM price/reservation change.
- DBU ↑ ≫ VM ↑ → SKU tier change (e.g. jobs → all-purpose, Photon, Premium), serverless shift.

## 7. Delta bridge

The bridge is the audit's central artefact (`templates/delta_bridge.csv`).

```
TOTAL Δr (Azure Actual)
 ├─ ACCOUNTING      calendar | purchase timing | credits | FX | scope | corrections | billed rate
 ├─ ROOT_CAUSE      driver 1 … driver n   (status CONFIRMED / LIKELY)
 ├─ SHARED_UNALLOCATED
 ├─ OUT_OF_SCOPE
 └─ UNEXPLAINED     = TOTAL - all lines above
```

Rules:
- Bridge amounts are in **Azure Actual** currency/day. When a driver is measured in Databricks list price, convert with the **observed ratio** for that bucket: `ratio = Azure DBX_PLATFORM Δr / modeled DBX Δr`, and record the ratio as a limitation.
- A driver appears in the bridge once.
- `UNEXPLAINED ≤ 10%` (R4) or explicit acceptance.

## 8. Evidence grading (R9/R10)

| Status | Required |
|---|---|
| `CONFIRMED` | (a) billed Δ in Azure Actual, (b) change timestamp within ±2 days of driver onset, (c) mechanism quantity explains ≥ 70% of driver Δ, (d) ≥ 1 alternative falsified |
| `LIKELY` | (a) + (b), or (a) + (c) |
| `HYPOTHESIS` | Plausible, untested; falsification test defined |
| `REJECTED` | Evidence contradicts the mechanism in the measured window |
| `UNKNOWN` | Data absent / retention / access denied |

Correlation in time alone is never sufficient for `CONFIRMED`.
