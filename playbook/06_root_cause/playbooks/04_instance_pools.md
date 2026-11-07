# PB-POOLS

<!-- plain -->
> **Overview.** Use when **virtual machines** cost more but DBU did not. Idle machines kept warm in an instance pool cost VM money and show no Databricks usage.
<!-- /plain -->

**Signals:** Azure VM cost ↑ in managed RG while DBU flat; pools exist (`worker_instance_pool_id` in `6.06`).

| # | Check | Source | Read |
|---|---|---|---|
| P1 | Observed idle vs placed hours per pool/month | [`6.08_pool_idle.sql`](../sql/6.08_pool_idle.sql) | `observed_idle_hours` ↑ |
| P2 | Pool configuration | Compute → Pools → min idle, max capacity, idle auto-termination; audit `6.14` (service `instancePools`) | Min idle ↑ at onset |
| P3 | VM meters for pool node types | Cost Analysis by Meter / Resource | VM hours ↑ |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-POL-01 | Min idle instances increased | Config/audit change ≈ onset; idle hours ↑ | Idle hours flat |
| H-POL-02 | Idle instance auto-termination increased | Longer READY intervals | Interval lengths unchanged |
| H-POL-03 | New pool | Pool first seen ≈ onset | Existed in B |

**Remediation options:** min idle = 0 outside business hours; shorter idle termination; consolidate pools.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
