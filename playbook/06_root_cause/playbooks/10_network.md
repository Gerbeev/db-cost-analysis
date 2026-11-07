# PB-NETWORK

<!-- plain -->
> **Overview.** Use when the **NETWORK** category grew: data moving between regions, a new private endpoint, NAT or firewall traffic.
<!-- /plain -->

**Signals:** Bandwidth, NAT Gateway, Private Link, Azure Firewall, VPN/ExpressRoute meters ↑.

| # | Check | Source | Read |
|---|---|---|---|
| N1 | Meter split: hours vs GB processed | Cost Analysis by Meter, Resource | Fixed vs volume-driven |
| N2 | Direction and region | Meter names (inter-region, internet egress), `source_region`/`destination_region` in usage for serverless networking | Cross-region flows |
| N3 | New network resources | Activity Log; resource first billed date | New NAT/PE |
| N4 | Workload behind traffic | `5.3` objects with onset ≈ network onset; Delta Sharing recipients | Correlated job |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-NET-01 | Cross-region data transfer | Inter-region meters ↑; workload reading remote region | Flat |
| H-NET-02 | NAT gateway data processing | NAT GB processed ↑ | Flat |
| H-NET-03 | Private Link processing / new endpoints | PE hours or GB ↑ | Flat |
| H-NET-04 | Internet egress / data sharing | Egress meters ↑; sharing recipients ↑ | Flat |
| H-NET-05 | Firewall processing | Firewall GB ↑ | Flat |

Shared network resources: allocate only with evidence (Step 7), else `SHARED_UNALLOCATED`.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
