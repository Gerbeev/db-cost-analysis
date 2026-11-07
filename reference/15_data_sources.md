# 15 · Data and metrics: why and how

<!-- plain -->
> **Overview.** For every number or file in the playbook: why it is needed and how to obtain it. The same text is shown inside each action of the application. Read-only access is enough for everything listed here.
<!-- /plain -->

Generated from `webapp/metrics.py`; do not edit by hand (`python -m webapp.plain_docs` rewrites it).


## 00 · Frame the question

### 0.1 Choose the months to compare and the currency

**Why.** The periods B, C and P define every comparison in the audit. The app copies them into all tools and SQL queries, so they are entered once.

**How to obtain.**

- Take them from the invoice or Cost Analysis chart: find the month where the monthly cost first stayed higher.
- Provisional values are enough: step 02 refines them from the daily data.

### 0.2 Fill in the scope record

**Why.** A scope fixed in writing prevents the costliest audit error: a change of scope after the data has been collected. The approval of the audit owner is the first gate.

**How to obtain.**

Labels are given for the English Azure portal (gear icon in the top bar, **Language + region**, switches the language). Sign in at `portal.azure.com` with your work account.
- Agreement type and billing scope: in the search box at the top type **Cost Management + Billing** and open it. In the left menu choose **Billing scopes** and select the billing account (if there is a single account, the page opens in it). Then **Properties**: the account type is Enterprise Agreement (EA), Microsoft Customer Agreement (MCA) or Individual. No **Billing scopes** entry means that you have no billing role: ask the billing administrator.
- Subscriptions: search **Subscriptions**; the list shows the name and the subscription ID of each one.
- Workspaces and regions: search **Azure Databricks**; the list shows each workspace with its resource group, location and subscription. Open a workspace: **Overview** shows **Managed Resource Group** and **Pricing Tier** (Standard or Premium).
- Commitments: search **Reservations**; the list contains the reservation orders you can see, including the Databricks pre-purchase plan (DBCU) if one was bought. A billing administrator sees all purchases under **Cost Management + Billing**, the billing scope, **Reservation transactions**. Savings plans: search **Savings plans**.
- Credits: MCA - the billing account, the billing profile, **Payment methods**, **Azure credits**. EA - the billing account, **Credits + Commitments**.
- Access to each source: try it and write OK, DENIED or UNKNOWN. A denied source is a limitation, not a zero.


## 01 · Data quality

### 1.1 Upload the main cost export

**Why.** This file is the ledger of the whole audit. Every later number about money (growth per day, services, meters, resource groups) is computed from it, so it must be Actual cost, complete, and taken once per month.

**How to obtain.**

Rights: **Cost Management Contributor** (or higher) on the scope to create an export, and write access to a storage account. **Cost Management Reader** can only view. Without these rights ask FinOps for an existing export of type **Cost and usage details (actual)** for the same scope and go to step 6.

1. Sign in at `portal.azure.com`. In the search box type **Cost Management** and open it. Press the **Scope** pill at the top left, highlight the scope from action 0.2 and press **Select**. In the left menu choose **Exports**.
2. Press **+ Create**. On the **Basics** tab choose **Create your own export** (press **Show more** if it is not visible) and **Next**.
3. **Datasets** tab: enter an **Export prefix**, for example `dbaudit`. Set **Type of data** to **Cost and usage details (actual)** - not *amortized*, not *FOCUS*, not *usage only*. Keep the offered **Dataset version**, enter an **Export name**, for example `dbaudit-actual`. Frequency: **Monthly export of last month's costs** (a recurring export can be re-run for past months, see step 5). If the portal asks for a date range in UTC, enter the first and last day of one month. Press **Add**, then **Next**.
4. **Destination** tab: **Storage type** Azure blob storage; select the **Subscription**, **Resource group**, **Storage account name** (or create one), **Container** and **Directory path**. **Format** CSV, **Compression type** None (Gzip files need unpacking). File partitioning is always on: a large month arrives in several parts. **Next**, then **Review + create**, then **Create**. New exports are enabled; data can take up to 24 hours to be ready.
5. Back in the **Exports** list select the export and press **Export selected dates**. Choose the first and last day of **one** calendar month (the portal reaches back 13 months, one month per run) and start the run. Wait until the run appears in the run history (press **Refresh**; up to 4 hours). Repeat for every month of the window, each month once. When all months are collected press **Disable** on the export so that no new files appear.
6. Download: in the **Exports** list press the storage account name, then **Open in Explorer** (needs the Azure Storage Explorer application) or, in the portal, **Storage browser** in the left menu, **Blob containers**, your container. The files are in `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/`. Download every `.csv` file and `manifest.json` of the run of each month.
7. A month with several parts: put the parts of that one run into an empty folder, open a terminal there and run `python -c "import glob;p=sorted(glob.glob('*.csv'));o=open('merged.tmp','wb');[o.writelines(l for n,l in enumerate(open(f,'rb')) if n or not i) for i,f in enumerate(p)];o.close()"`; rename `merged.tmp` to `<month>.csv`. It keeps a single header line. Never join runs that cover the same month.
8. The app takes one file: if the window has several month files, join them in the same way into one CSV and upload it.

### 1.2 Upload the export manifests

**Why.** The manifest records the run ID and the list of files of each export run. It proves that every month was taken exactly once; without it a duplicated run cannot be told apart from real cost.

**How to obtain.**

- Each run has its own folder `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/` in the storage container; it holds the data files and `manifest.json`. Download the `manifest.json` of every run you used together with the data files (step 6 of action 1.1).
- Check: every month of the window has exactly one run folder.
- No manifests (a file received from FinOps)? Write the run IDs or file names in `export_manifest.md` and upload that file instead.

### 1.3 Download the monthly totals from Cost Analysis

**Why.** An independent monthly total from a different Azure screen. If it differs from the export by more than 0.5%, the export is incomplete or duplicated and no later number can be trusted (rule R6).

**How to obtain.**

1. `portal.azure.com`, search **Cost Management**, open it. Check the **Scope** pill at the top left: it must be the scope of the export (select it as in action 1.1). In the left menu choose **Cost analysis**.
2. Cost analysis opens either a list of views or a chart. Open **All views** and choose a customizable view, for example **Cost by service**: customizable views show the date range, granularity and **Group by** controls.
3. Metric: the cost figure must read **Actual cost**. Its down arrow switches between **Actual cost** and **Amortized cost**.
4. Date range: press the date pill and choose a custom range from the first day of the first month to the last day of the last month of the window. Granularity: **Monthly**. **Group by**: choose **None** (or remove the grouping). No filters.
5. Press **Download** at the top, choose **CSV**, and upload the file here.
Note: the export and Cost analysis both come from Cost Management, so they are compared with each other, not with the PDF invoice: the invoice contains taxes and credits that Cost Management does not.

### 1.4 Calculate monthly totals from the export

**Why.** Turns the raw export into a monthly total and a cost per day. The cost per day is the unit of comparison for the whole audit because months differ in length.

**How to obtain.**

Nothing to enter: the app reads the main export and writes `export_monthly`.

### 1.5 Check that the export matches Cost Analysis (rule R6)

**Why.** Confirms that the export is complete by comparing two independent sources month by month (rule R6). A failed check stops the audit until the export is fixed.

**How to obtain.**

Nothing to enter: the app takes the results of 1.3 and 1.4. A difference above 0.5% usually means a duplicated run or a missing day - repeat 1.1.

### 1.6 Check that Databricks has data for every day

**Why.** Databricks usage records are the basis of the cost model. A day without records produces a false drop or a false rise, and the second query lists workspaces that appeared or disappeared in the window.

**How to obtain.**

- Source: `system.billing.usage`.
- Before the first run: by default only users who are both **account admin** and **metastore admin** can read system tables. For everyone else an admin grants `USE CATALOG` on the `system` catalog and `USE SCHEMA` and `SELECT` on the schemas `billing`, `compute`, `lakeflow`, `query`, `access`. System tables exist only if the account has a workspace with Unity Catalog, and are not available in Azure China, Azure Government, West India and Switzerland West.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).
- Result files: `1.1_usage_coverage` and `1.1_workspace_presence`.

### 1.7 List the units and SKUs in use

**Why.** Shows which units each SKU is measured in. Quantities in different units (DBU, GB, hours) must never be added together.

**How to obtain.**

- Source: `system.billing.usage`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 1.8 Check that every usage record has exactly one price (rule R7)

**Why.** The modeled cost is usage multiplied by list price. If a usage row has no price or several prices, the modeled cost of that SKU is wrong (rule R7); such SKUs are excluded from money conclusions.

**How to obtain.**

- Sources: `system.billing.usage` and `system.billing.list_prices`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).
- Read the column `verdict`: `FAIL_*` means exclude.

### 1.9 Write the data-quality summary

**Why.** Records what the data allows and what it does not, so that later conclusions are read within these limits.

**How to obtain.**

- Table availability: open the Databricks workspace, click **Catalog** (Catalog Explorer) in the left sidebar, open the catalog `system` and its schemas `billing`, `compute`, `lakeflow`, `query`, `access`. A missing schema is UNKNOWN, not zero. A schema that exists but has not been enabled has to be enabled by a metastore admin first.
- Retention of each table: reference 02, section 3.
- Limitations: copy the failed SKUs of 1.8 and the largest R6 difference of 1.5.


## 02 · Confirm and size

### 2.1 Build the monthly table with cost per day

**Why.** Shows the growth in the real billed amount and normalises it per day. Without a service filter, so that growth outside Databricks is visible too.

**How to obtain.**

Nothing to enter: the app reads the main export (1.1) and writes `monthly_series`.

### 2.2 Download daily costs (optional)

**Why.** A monthly series cannot show the exact day of the change. A daily series is needed only when the main export does not cover all days.

**How to obtain.**

1. `portal.azure.com`, **Cost Management**, check the **Scope** pill, **Cost analysis**, a customizable view (**All views**, for example **Cost by service**), metric **Actual cost**.
2. Granularity **Daily**. The portal allows at most three months in one daily range: choose a range of about 90 days around the suspected change. **Group by**: **None**; no filters.
3. **Download**, **CSV**, upload.

### 2.3 Find the day the growth started (rule R5)

**Why.** The start date of the growth narrows the search for the cause: a change event must precede it. A short rise is a spike, not a step (rule R5).

**How to obtain.**

Nothing to enter: the app detects the first day of a level that held for 14 days or more, using B as the baseline.

### 2.4 Cross-check the start day in Databricks

**Why.** Checks the start date from the Databricks side. A gap of more than a day means that something other than Databricks is moving the bill.

**How to obtain.**

- Source: `system.billing.usage` with `system.billing.list_prices`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 2.5 Get the monthly modeled cost by SKU

**Why.** The monthly modeled cost per SKU is the input for the direction check (3.9) and the volume and rate split (5.1).

**How to obtain.**

- Source: `system.billing.usage` with `system.billing.list_prices`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 2.6 Fix the final periods B, C and P (rule R2)

**Why.** Final B, C and P turn the growth into a measurable difference. B must be stable; C must be a full month on the higher level (rule R2).

**How to obtain.**

- B: at least 28 days before the start date from 2.3, without other changes.
- C: the first full month after the start date.
- P: the month after C.

### 2.7 Calculate the size of the growth

**Why.** Produces the number the audit must explain: growth per day, in percent, per year, and its persistence. It becomes the TOTAL line of the bridge.

**How to obtain.**

Nothing to enter: the app uses the main export and the periods from 2.6.

### 2.8 Describe the shape of the growth

**Why.** The shape decides which causes are plausible: a step suggests a change or a price; a ramp suggests accumulation; a spike suggests an event; a seasonal pattern suggests nothing changed.

**How to obtain.**

- Open the daily series (2.2 or the export) as a chart and compare with the same months of the previous year, if the export covers them.


## 03 · Accounting effects

### 3.1 Calendar effect (ACC-01)

**Why.** Rules out an apparent growth caused only by month length. Because the audit compares cost per day, the effect is zero unless someone compared monthly totals.

**How to obtain.**

- Compare the number of days of B and C. The effect is the monthly cost multiplied by the difference in days divided by the days of B.

### 3.2 Charge type and pricing model (ACC-02, ACC-03)

**Why.** A one-off purchase (a reservation) or an ended commitment changes the bill without any change in usage (ACC-02, ACC-03).

**How to obtain.**

1. **Cost Management**, **Cost analysis**, check the **Scope** pill, a customizable view (**All views**), metric **Actual cost**, granularity **Monthly**.
2. Date range: the custom range of period B. Open **Group by** and choose **Charge type**. **Download**, **CSV**. Repeat for period C.
3. Repeat both downloads with **Group by** **Pricing model**.
4. Upload the four files named as suggested. Charge types you will see: Usage, Purchase, Refund, Adjustment (and UnusedReservation or UnusedSavingsPlan in the Amortized view).

### 3.3 Compare Actual with Amortized (ACC-02)

**Why.** Actual shows purchases when they are paid; Amortized spreads them over the term. A large gap in C points to a purchase (ACC-02).

**How to obtain.**

1. **Cost Management**, **Cost analysis**, the same scope, view and months as in action 1.3.
2. Press the down arrow next to the cost figure and choose **Amortized cost**. Granularity **Monthly**, **Group by** **None**, **Download**, **CSV**, upload.
3. If **Amortized cost** is not offered, the scope has no amortized data (for an EA only the billing account scope has both datasets): record UNKNOWN in the scope record.

### 3.4 Credits, refunds and corrections (ACC-04)

**Why.** An exhausted credit or a refund changes the invoice although usage is the same (ACC-04).

**How to obtain.**

- Refunds and adjustments: the file of 3.2 grouped by **Charge type** contains the lines Refund and Adjustment.
- Credits are not part of Cost analysis; they are on the billing pages. MCA: **Cost Management + Billing**, the billing account, the billing profile, **Payment methods**, **Azure credits** (balance and transactions). EA: the billing account, **Credits + Commitments** (Azure Prepayment, and the Microsoft Azure Consumption Commitment, MACC). These pages need a billing role: Reader or higher for MCA, Enterprise administrator for EA.
- Write the balance and the expiry date, or UNKNOWN if the page is not accessible.

### 3.5 Did the scope change between B and C? (ACC-07)

**Why.** A subscription or workspace that appeared between B and C adds cost that was simply not counted before (ACC-07). It is not an operational change.

**How to obtain.**

Nothing to enter: the app compares subscriptions of B and C in the main export. Add the workspaces marked `APPEARED_IN_WINDOW` in 1.6 by hand.

### 3.6 Did the unit price change? (ACC-05)

**Why.** Higher unit price at unchanged usage is a price effect (ACC-05), not an operational change.

**How to obtain.**

- The app ranks meters by change per day; the column `EffectivePrice` of the export gives the unit price of B and C.
- Typical case: Standard to Premium workspace tier, visible as `STANDARD_*` replaced by `PREMIUM_*` in the SKU list of 1.7. The current tier: portal, **Azure Databricks**, the workspace, **Overview**, **Pricing Tier**.

### 3.7 Did the Databricks list price change? (ACC-05)

**Why.** A new version of the Databricks price list inside the window is a price change, not a usage change (ACC-05).

**How to obtain.**

- Source: `system.billing.list_prices`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 3.8 Exchange rate and late corrections (ACC-06, ACC-08)

**Why.** A change of the exchange rate between price currency and billing currency changes the bill without any change in usage (ACC-06). Late corrections shift costs between months (ACC-08).

**How to obtain.**

- Rate: open the main export in a spreadsheet and look at the header row for the exchange-rate column (its name depends on the agreement type, for example `ExchangeRatePricingToBilling` in MCA); compare its value for B and C. If the column does not exist, write UNKNOWN.
- Corrections: re-run an old month (**Export selected dates**, action 1.1) into a separate export prefix and compare it with the first copy; count `RETRACTION` and `RESTATEMENT` in the result of 1.6.

### 3.9 Sanity check: do both views move the same way? (rule R8)

**Why.** A consistency test of two independent views: the Azure bill and the Databricks cost model must move in the same direction (rule R8). A mismatch means a discount, a commitment or the scope distorts one of them.

**How to obtain.**

Nothing to enter: the app uses the export and the result of 2.5.

### 3.10 Fill in the accounting lines of the bridge

**Why.** The accounting lines remove from the total the part of the growth that is not operational. What remains is the part that has causes in the platform.

**How to obtain.**

- Take the figures from 3.1-3.8; write 0 where a test had no effect.

### 3.11 Calculate the operational growth

**Why.** Operational growth is the number that steps 04-07 must explain.

**How to obtain.**

Nothing to enter: the app subtracts the accounting lines from TOTAL.


## 04 · Azure decomposition

### 4.1 Run the Azure decomposition (five groupings)

**Why.** Shows what was billed more, in five mutually exclusive views: subscription, service, meter, resource group, resource. The totals of all views must be equal; a difference indicates a filtering error.

**How to obtain.**

Nothing to enter: the app uses the main export and B and C from settings, writes five files `delta_by_*` and one evidence row for each.
If a grouping is skipped because the export has no such column (EA and MCA schemas differ), the warning names it; the other groupings are still written.

### 4.2 Map workspaces to their resource groups

**Why.** Links the Databricks workspaces to the Azure resources that are billed under other names: virtual machines sit in the managed resource group, not in the workspace.

**How to obtain.**

- Azure CLI (read-only): install it once (Microsoft documentation, *Install Azure CLI*), open a terminal and run `az login`; a browser window opens, sign in with the work account. `az account list --output table` must list the subscriptions of the audit. With several tenants use `az login --tenant <tenant ID>`. Then press **Run**.
- Without the CLI: portal, search **Azure Databricks**, open each workspace, **Overview**, copy **Managed Resource Group** and the subscription; upload the table in the next action.

### 4.2b Upload the workspace map by hand

**Why.** A fallback for the previous action, if the Azure CLI is not available.

**How to obtain.**

- CSV `workspace_rg_map.csv` with one line per workspace: workspace name, subscription, managed resource group, dependent resource groups (storage, network, monitoring).

### 4.3 Put every big line into a category

**Why.** Every big line must have exactly one category, otherwise the bridge cannot close and the same cost is counted twice.

**How to obtain.**

- Take the lines from the `delta_by_*` files of 4.1 and the map of 4.2. A managed resource group is a hint, not proof of ownership.


## 05 · Databricks decomposition

### 5.1 Is it more usage or a higher price? (by SKU)

**Why.** Separates more usage (volume) from a higher price (rate) per SKU. A SKU that disappears while a similar one appears is a mix shift: usage only moved.

**How to obtain.**

- Source: `system.billing.usage` with `system.billing.list_prices`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 5.2 Which workspaces grew

**Why.** Shows whether the growth is local (one workspace, probably one team's change) or platform-wide.

**How to obtain.**

- Source: `system.billing.usage`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 5.3 Which jobs, pipelines, warehouses and clusters grew

**Why.** Finds the objects (jobs, pipelines, warehouses, clusters) that explain the growth. The list continues until 90% of the modeled growth is covered (rule R4).

**How to obtain.**

- Source: `system.billing.usage` (columns `usage_metadata`, `identity_metadata`).
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 5.4 Look at the daily cost of the top objects

**Why.** The start day of an object must match the overall start day (within 2 days). Otherwise it is probably not the main cause.

**How to obtain.**

- The app fills `object_ids` with the objects of 5.3 up to 90% coverage; check the list and run.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 5.5 How much cost has no owner

**Why.** Cost without an object ID or required tags cannot be assigned to an owner; its share goes to step 07.

**How to obtain.**

- Source: `system.billing.usage` (`custom_tags`, `usage_metadata`).
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).
- Parameter `required_tag`: the tag key your company requires, for example `cost_center`.

### 5.6 What is new in the window

**Why.** New products and SKUs near the start date are frequent causes of growth.

**How to obtain.**

- Source: `system.billing.usage`.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 5.7 Record the candidates

**Why.** Candidates are the objects that step 06 will investigate; each one is entered with its growth at list price.

**How to obtain.**

- Take the objects and growth values from the result of 5.3.


## 06 · Root cause

### 6.1 Create a driver card

**Why.** A driver card keeps the whole proof of one cause in one place: what changed, when, how much, the evidence and the alternatives that were disproved (rule R9).

**How to obtain.**

Nothing to enter except the driver name: the app creates the card from the template.

### 6.2 Run the diagnostic queries from the playbook

**Why.** Answers two questions for every driver: how much (frequency times unit cost, or volume times price) and what changed (a dated event).

**How to obtain.**

- Cost and frequency: `system.billing.usage`, `system.lakeflow.*`, `system.compute.*`, `system.query.history`.
- Change events: configuration history in `system.compute.clusters`, `system.compute.warehouses`, `system.lakeflow.jobs`; `system.access.audit` for who and when.
- Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).
- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result tab, choose **Download**, **CSV**, and upload the file here.
- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).

### 6.3 Upload other evidence

**Why.** Some change events are outside the system tables: a release, a Git commit, a ticket, an Azure resource change.

**How to obtain.**

- Azure change: portal, open the resource group (or the resource) and choose **Activity log** in the left menu; the page opens pre-filtered to that object. Set **Timespan** to a custom range around the start date (a short range keeps the export fast), use **Add filter** (for example *Operation*) to narrow it, and press **Download as CSV**. The portal keeps the activity log for 90 days: a change older than that is not here (write UNKNOWN and use `system.access.audit`).
- Release or code: the Git or deployment history of the object; export the page as PDF or text.


## 07 · Attribution and residual

### 7.1 Name an owner for every confirmed cause

**Why.** Each confirmed cause needs a person who can accept or reject the fix.

**How to obtain.**

- Databricks: the column `sample_run_as` of 5.3, the job or workspace owner, tags `owner`, `cost_center`, `application`.
- Azure: tags on the resource group.

### 7.2 Shared cost allocation keys (optional)

**Why.** Shared cost can be split only by a provable key. An estimated share would turn the report into an opinion.

**How to obtain.**

- A key is a measured quantity: usage share, bytes, requests. Take it from the system tables or from the owners' reports.

### 7.3 Describe the cost without tags or owner

**Why.** Quantifies the part of the growth that cannot be assigned because of missing tags or IDs, and explains why.

**How to obtain.**

- Take the share from the result of 5.5.

### 7.5 Calculate the unexplained part

**Why.** The unexplained part shows how much of the growth the audit could not attribute. Up to 10% of the total is acceptable (rule R4).

**How to obtain.**

Nothing to enter: the app computes it from the bridge.


## 08 · Validation

### 8.1 Re-run everything and compare

**Why.** A result that cannot be repeated is not evidence. The repetition proves that the numbers come from the saved files and parameters.

**How to obtain.**

Nothing to enter: the app repeats every evidence row; SQL rows need the Databricks connection.

### 8.3 Compare with other views of the cost

**Why.** Other views of the cost (Amortized, the Databricks usage dashboard, IBM) confirm the main numbers. Their differences are explained and never added.

**How to obtain.**

- Amortized: the file of 3.3.
- Usage dashboard: open `accounts.azuredatabricks.net` and sign in as an **account admin**. Click the **Usage** icon in the left menu. Choose the months of the window and switch the **$USD/DBU** picker to compare cost and DBUs. The dollar figures are an estimate from list prices: they can be adjusted in the settings panel (kebab menu at the top right of the page). **Download** (top right of the graph) gives the aggregated data; the settings panel, **Download** at the bottom, gives all usage by date. The page does not show every product: Databricks recommends the system tables for complete usage.
- IBM: the actions 8.4-8.8, if the licence exists.


## 09 · Report and controls

### 9.1 Get the bridge as a table for the report

**Why.** The bridge in the report must be identical to the working file, otherwise the report cannot be checked.

**How to obtain.**

Nothing to enter: the app converts the bridge into a table for the report.
