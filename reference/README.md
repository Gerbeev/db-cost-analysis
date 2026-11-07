# Reference

Background knowledge. The procedure itself is in [`../playbook/`](../playbook/README.md).

| # | File | Read when | Content |
|---|---|---|---|
| 00 | [Fundamentals](00_fundamentals.md) | **first, before any audit** | Architecture, 5 cost layers, DBU, formulas, tiers, commitments, Azure billing basics, typical growth causes |
| 01 | [Cost model](01_cost_model.md) | step 00, attribution | Ledgers and views, what each compute type bills, Azure ↔ Databricks hierarchies, meter patterns, non-additive rules |
| 02 | [Access and data collection](02_access_and_data_collection.md) | steps 00-01 | Permissions, Cost Analysis and Exports how-to, system tables, data handling |
| 03 | [Analysis method](03_analysis_method.md) | steps 02-07 | Per-day delta, onset, contribution, volume × rate, frequency × unit cost, bridge, evidence grading |
| 04 | [Pitfalls and stop rules](04_pitfalls_and_stop_rules.md) | every step | Conditions that invalidate numbers; common false conclusions |
| 05 | [Audit rules R1-R12](05_audit_rules.md) | every step | Binding thresholds, statuses, check marking |
| 06 | [IBM Apptio lens](06_ibm_apptio_lens.md) | steps 03, 08 (if licensed) | Cloudability / ApptioOne as cross-check views |
| 07 | [IBM API setup](07_ibm_api_setup.md) | if licensed | Credentials; the IBM tools are actions 8.4-8.8 in the interface |
| 08 | [Remediation and controls](08_remediation_and_controls.md) | step 09 | Remediation gate, typical fixes, post-audit controls |
| 09 | [Sources](09_sources_and_glossary.md) | lookup | Official documentation |
| 10 | [Legacy mapping](10_legacy_mapping.md) | migration | Where old workbench content went |
| 11 | [SQL conventions](11_sql_conventions.md) | before running SQL | Parameters, price join, file naming |
| 12 | [Web UI theme](12_web_ui_theme.md) | changing the interface | Dark “true black” palette, tokens, contributor rules |
| 13 | [Punctuation](13_punctuation.md) | writing or translating | ASCII hyphen only; no en/em dashes |
| 14 | [Glossary](14_glossary.md) | **any unknown word** | Definitions of all playbook terms, with links |
| 15 | [Data and metrics](15_data_sources.md) | **before collecting a number or file** | Why each metric is needed and how to obtain it (portal path, system table) |
| - | [source_catalog.csv](source_catalog.csv) | lookup | Source IDs → URLs |
