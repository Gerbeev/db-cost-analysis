# 07 · IBM Apptio API setup (optional tools)

<!-- plain -->
> **Overview.** Optional. How to give the app access to IBM Cloudability or ApptioOne (keys and URLs) so that steps 8.4-8.8 can download data for you. Skip it if you do not use IBM tools.
<!-- /plain -->

> **Offline research first:** For the complete Cloudability and TBM Studio research procedures, use [reference/06 IBM Apptio lens](06_ibm_apptio_lens.md). This file only describes **optional, credentialed API tools**; running them is not necessary for the project.

**Status:** Read-only integration built and tested offline. Live tenant access and financial reconciliation remain pending.  
**Products:** IBM Cloudability (v3 cost API) and IBM ApptioOne / TBM Studio (report-specific API downloads).  
**Window:** January 1-October 31, 2026. All dates configurable.

> **Where results go:** the interface saves raw API exports to `audits/<id>/08_validation/exports/` and analyses to `audits/<id>/08_validation/results/`.

## 1. Identify the deployed product

| UI / capability | Use | API output | Analysis support |
|---|---|---|---|
| **IBM Cloudability** (Cloudability cost reports, Views, cost dimensions) | `cloudability` | Ten-month report CSV and evidence manifest | Automated monthly / driver analysis |
| **IBM ApptioOne / TBM Studio** (Cost Transparency, tables/reports) | `apptioone` | Exact TSV/CSV/JSON/XLSX chosen in the UI | Download only; financial fields need schema review |

These products use **different APIs and credentials**. Having ApptioOne alone does not establish that Cloudability endpoints are licensed or accessible. Confirm the Cloudability entitlement with the application administrator. Do not treat Cloudability's reporting balances as additional charges on top of Azure invoices.

## 2. Obtain read-only API access

### A. Cloudability

1. In Cloudability: **User avatar → Manage Profile → Preferences → Cloudability API → Enable Access**. Copy the generated **API Key** to a secure secret manager. **Regenerate Key** invalidates the previous one; do not regenerate an integration already in use without coordination.
2. Verify the Cloudability deployment region. API host selection: `eu` (`api-eu.cloudability.com`), `us`, `apac`, `ca`, `me`, `in`, `jp`, `sg`, `usgov`.
3. Ask a Cloudability administrator for a **read-only view** that includes the relevant Azure subscriptions. Document the view ID or explicitly document that your user default view is in effect. **View ID `0` (field in action 8.5) removes views only if your access permits it**; this is not a privilege bypass.
4. Confirm the **reporting currency** shown in the Cloudability UI. The exporter requires a manually verified currency; it does not infer currency from a cost figure.
5. Enter the key in the password field of action 8.4 / 8.5 (used for that run only) or set the environment variable `CLOUDABILITY_API_KEY` before starting the interface. Never paste the key into a log, ticket or screenshot.

Official IBM: [Cloudability API v3 authentication and regional hosts](https://www.ibm.com/docs/en/cloudability-commercial/cloudability-enterprise/saas?topic=api-getting-started-cloudability-v3), [Cost reporting parameters and pagination](https://www.ibm.com/docs/en/cloudability-commercial/cloudability-essentials/saas?topic=api-cost-reporting-end-point).

### B. ApptioOne / TBM Studio

1. In **Enhanced Access Administration**, generate an **API key pair** (`keyAccess`, `keySecret`), assign it to the intended user/service account, and **Grant Access** to the target environment. Only download/view permissions are needed; do not grant upload or write permissions for this investigation.
2. Identify the regional Frontdoor host (`frontdoor-eu.apptio.com` for EU, or the host assigned to your tenant) and the customer domain (for example `yourdomain.com`). The script obtains a short-lived `apptio-opentoken` through `POST /service/apikeylogin` and can obtain the environment ID through `GET /api/environment/{customer}/{environment}`. A known environment ID can instead be supplied directly.
3. Open the relevant **TBM Studio cost report**. For a table, **Home → Export → Show API URL**; for a report table/chart, open its context menu → **Show API URL**. Copy the complete **HTTPS API URL** for the intended data and date/fiscal period. Do not fabricate endpoints or modify a report ID by hand.
4. Put the key pair into environment variables `APPTIO_KEY_ACCESS` and `APPTIO_KEY_SECRET`, or enter them in the password fields of action 8.6. **Do not place either key in CMD files**. Exports are saved inside the private audit folder (`audits/<id>/08_validation/`).
5. Confirm the exported **report's allocation and fiscal/calendar period**, currency, cost measure and business mapping columns before any comparison with Azure Actual. Reports can be modeled/allocated instead of raw Azure billed costs.

Official IBM: [API keys/OpenToken](https://www.ibm.com/docs/en/apptio-platform/access-administration/saas?topic=apis-authentication-via-api-keys), [Environment discovery](https://www.ibm.com/docs/en/apptio-platform/access-administration/saas?topic=apis-get-user-environment-information), [Download a TBM Studio table/report](https://www.ibm.com/docs/en/apptio-gov/tbm-studio/saas?topic=integration-how-download-data-via-api).

## 3. Running the tools from the interface

Open the audit → **step 08 Validation**. The IBM tools are actions there; results go to `audits/<id>/08_validation/exports/` and `…/results/` and get evidence rows.

| Action | Does | Credentials |
|---|---|---|
| 8.4 Cloudability: verify access | lists the metrics / dimensions your user may query (`cloudability_measures__….json`) | API key field (not stored) or env `CLOUDABILITY_API_KEY` |
| 8.5 Cloudability: export | monthly cost report for the window; **currency must be the one shown in the Cloudability UI**; filters e.g. `vendor==Azure` | same |
| 8.6 ApptioOne: download report | downloads the TBM Studio report from its **Show API URL** | key access / secret fields (not stored) or env `APPTIO_KEY_ACCESS` / `APPTIO_KEY_SECRET` |
| 8.7 ApptioOne: normalize | maps a verified TBM report to the generic schema (choose date, cost and dimension columns) | - |
| 8.8 Analyze export | monthly / driver analysis of the Cloudability export or the normalized ApptioOne file | - |

Keys typed into the form are passed to the tool process as environment variables for that single run and are never written to disk or logs.

Cloudability artifacts:

- `apptio_cloudability__….csv` (step 08 `exports/`): group-level monthly amounts (`metric=unblended_cost` by default).
- `apptio_cloudability__….manifest.json`: extraction timestamp, view, metric, filters, counts and missing-month warnings.
- `cloudability_measures__….json`: measures available to your user for choosing more granular dimensions.
- analysis (action 8.8): `apptio_summary.md`, `apptio_quality.md`, `apptio_monthly.csv`, change-point and growth-driver CSVs in `08_validation/results/apptio_analysis__…/`.

**Granularity:** Default dimensions are `vendor,enhanced_service_name`. Use dimensions `vendor,enhanced_service_name,resource_identifier` only if action 8.4 confirms those dimensions and the result size/pagination is practical. Add a subscription/account dimension when supported to reconcile the exact Azure subscription scope. The client validates all requested dimensions/metrics against tenant API metadata. Filters: one per line. Applying allocations changes the cost basis and must be explicitly documented. Cloudability can use organization-specific currency and Views; compare only compatible scopes and measures.

**ApptioOne:** copy a real API URL from the TBM Studio interface into action 8.6 and give either the customer domain (`yourdomain.com`) or a known environment ID. Nothing is uploaded; report endpoints are **GET-only**. The URL and its fiscal period are taken from the UI, not generated by this project.

## 4. RCA checks to perform inside Apptio

| ID | Check in the UI or API | Comparison / deliverable |
|---|---|---|
| APP-01 | Product, license and reporting permissions | Record Cloudability vs ApptioOne and selected View/environment |
| APP-02 | Month-by-month Azure spending for Jan-Oct 2026 | Compare `unblended_cost` Cloudability and Azure Actual using identical currency and scope |
| APP-03 | Cloud provider, service, account/subscription, resource and tags | Rank April-minus-March **currency delta**, not percentage alone |
| APP-04 | Cost dimensions for Databricks vs supporting compute/storage/network | Identify charges Azure data attributes to Databricks and managed resource groups |
| APP-05 | Allocation mapping and allocation rules (if ApptioOne / Cost Transparency) | Distinguish raw, adjusted, amortized, invoiced and allocated cost |
| APP-06 | Cloudability anomalies (if available) and missing cost ingestion | Determine when spikes started and whether cloud ingestion was delayed |
| APP-07 | Views, exclusion filters, credits, FX and business mapping changes | Explain mismatches and apparent growth due to configuration |
| APP-08 | Top increased workload groups | Map Apptio service/resource to Azure meters and Databricks SKU/jobs |

Optional Cloudability anomaly endpoint (product/permission dependent): [`GET /v3/anomalies`](https://www.ibm.com/docs/en/cloudability-commercial/cloudability-enterprise/saas?topic=api-anomaly-detection-endpoint). Its parameters and `viewId` must be validated against the tenant before relying on results; anomaly data is not a financial ledger.

## 5. Scope reconciliation - mandatory

- **Azure Actual**: the billed-ledger baseline for a declared Azure Cost Management billing scope.
- **Databricks `system.billing`**: consumption/estimated product attribution (may be list price, discounts differ).
- **Cloudability**: an independent FinOps aggregation of ingested cloud costs; may already include the same Azure charges, and might use different adjustments, allocations, delays, or filters.
- **ApptioOne / TBM Studio**: TBM modeled/allocated totals may be based on the same ingested Azure data; inspect the table and column definitions, not just the displayed number.

**Never sum these four views.** For an apples-to-apples check, align period, billed currency, subscription scope, provider, view, allocations, cost measure (Actual vs amortized), credits and export update timestamp. Record any differences as unresolved until explained by evidence.

## 6. Failure handling and security

| Symptom | Action |
|---|---|
| HTTP 401 / 403 | Confirm key, region, entitlement and selected view/environment permissions |
| HTTP 404 | Confirm the endpoint path or TBM Studio copied API URL |
| HTTP 429 / 5xx | Read-only GET uses bounded retries, `Retry-After` and capped backoff; retry a narrower query if needed |
| Missing/unknown measures | Run action 8.4, then choose only names returned by the tenant |
| Missing month / mixed currency | Do not treat gaps as zero, do not compare endpoints across currency changes |
| Output has zero rows | Check Azure filter, selected view, ingest delay, data coverage and billing dates |
| API key rotation | Update secret outside the project; never save credentials in the archive |

Export requests use TLS validation, block HTTP redirects (to avoid token leakage), cap response sizes and pagination, write CSV atomically, and never log credential values. The scripts do not call any write/update/delete APIs. `audits/_logs/apptio_api.log` is reset at each API invocation; offline analyzer logs to `audits/_logs/analysis.log`.

## 7. Acceptance gate

- [ ] Product and region confirmed, API key enabled with read-only access.
- [ ] API access probe passes and dimensions/metrics are documented.
- [ ] Ten full months exported with manifest, complete row/page counts and a defined view.
- [ ] Cloudability currency and cost metric verified against the UI.
- [ ] Missing-month, pagination and data-quality warnings resolved.
- [ ] Monthly totals reconciled to the matching Azure Actual scope or exceptions itemized.
- [ ] Top increases linked to Azure services/meters and Databricks Jobs/SKUs, with supporting evidence.
- [ ] Evidence register and RCA findings updated; no production optimization without approval.

## 8. Normalize an ApptioOne CSV/TSV for local analysis

**Only after verifying the actual report schema and cost semantics.** The TBM Studio exporter preserves the report's original columns; it cannot safely infer calendar months, currency, fiscal mapping or what each cost field represents.

1. In TBM Studio, choose a read-only **monthly** cost table with columns for calendar month, numeric cost and at least one meaningful business dimension (cost center, application or service). Prefer TSV from **Show API URL**.
2. Confirm whether the report uses calendar dates or a fiscal calendar. `normalize_apptioone.py` only accepts `YYYY-MM` and `YYYY-MM-DD`. For fiscal periods, obtain a verified calendar mapping before normalization; the script never guesses a fiscal month.
3. In action 8.7 pick the **exact columns** of the exported report (month, cost, one or more dimensions), the currency, the cost metric name established in the TBM UI and a report label. Then analyze the normalized file with action 8.8, separately from Cloudability.

The output includes an evidence manifest and missing-month warnings. Never merge or add this report's totals to Azure Actual or Cloudability.
