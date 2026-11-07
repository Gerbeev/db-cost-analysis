# 14 · Glossary

Definitions of all terms used in the playbook. Each term has a one-sentence definition (shown as a tooltip throughout the application) followed by a fuller explanation. Terms in the playbook and the documentation are linked to this page automatically.

If a term is missing, add it in the same format: `### Name {#id}`, an optional line `*Aliases: a, b*`, then the explanation. A trailing `~` in an alias matches any word ending (used in Russian). Keep the ids identical in `14_glossary.ru.md` - a test checks that.

## The bill: where the money comes from

### Azure Actual Cost {#azure-actual}
*Aliases: Actual cost, Actual*
The amount Azure really charged you, on the day it charged it.
This is the **single monetary source of truth** of the audit (rule R1). When a one-year reservation is purchased, its full price appears on the purchase day: that is "actual". Every other view of the cost is auxiliary and is never added to this one.

### Amortized Cost {#amortized}
*Aliases: Amortized*
The same cost, but big purchases are spread evenly over the period they cover.
Good for budgeting, bad for finding what happened on a given day. Never mix Actual and Amortized in one table (STOP-4).

### Cost Management {#cost-management}
*Aliases: Azure Cost Management*
The part of the Azure portal where you see, export and analyze what you spend.
It contains Cost Analysis (charts and downloads) and Exports (scheduled full data files).

### Cost Analysis {#cost-analysis}
A report page in Cost Management with charts and a Download button.
We use it as a **second opinion**: its monthly totals must match our big export within 0.5% (rule R6).

### Export {#export}
*Aliases: Exports, cost details export*
A full, detailed file of every cost line, produced by Azure into a storage account or downloaded.
The main input of the audit. Always take **one export run per month** and never append runs together (STOP-1).

### Scope {#scope}
The part of the estate under audit: which billing account, subscriptions, workspaces and resource groups.
The scope must be the same in the "before" and "after" periods, otherwise you compare different things (STOP-5).

### Subscription {#subscription}
*Aliases: subscriptions*
Azure's container for resources and billing. A company usually has several.

### Resource group (RG) {#resource-group}
*Aliases: resource groups, RG*
A logical container within a subscription that holds related Azure resources (VMs, disks, storage).

### Managed resource group {#managed-rg}
*Aliases: managed RG, managed resource group*
A resource group that Azure Databricks creates for each workspace to hold the virtual machines and disks of classic compute.
A managed RG hints at which workspace a cost belongs to, but is not proof of ownership.

### Charge type {#charge-type}
A cost column that says what kind of charge a line is: Usage, Purchase, Refund or Adjustment.
Used in step 03 to separate real consumption from one-off purchases and corrections.

### Pricing model {#pricing-model}
A cost column that says how the line was priced: OnDemand, Reservation, SavingsPlan or Spot.

### Reservation {#reservation}
*Aliases: reservations, RI*
A discount you get for paying in advance for a fixed amount of Azure capacity for 1 or 3 years.

### Savings plan {#savings-plan}
*Aliases: savings plans, SP*
A discount for committing to spend a fixed amount per hour for 1 or 3 years.

### Commitment {#commitment}
*Aliases: commitments, coverage*
Any pre-paid or promised spend that lowers the unit price (reservation, savings plan, DBCU).
When a commitment is exhausted or expires, the same usage is billed at a higher price. This is an **accounting effect**, not additional consumption.

### DBCU {#dbcu}
*Aliases: Databricks Commit Unit*
A pre-purchased pool of Databricks spend (1 or 3 years) that gives a discount on DBU charges.
While the pool lasts, DBU usage can show almost no on-demand cost; when it is exhausted the cost jumps.

### Credit {#credit}
*Aliases: credits*
An amount Azure refunds or allows to be consumed at no charge (promotions, support credits). Credits mask the real cost until they expire.

### FX (currency exchange) {#fx}
*Aliases: exchange rate, currency conversion*
Conversion between the currency of the price list (usually USD) and the currency of your invoice. A rate change moves the bill with no change in usage.

### List price {#list-price}
*Aliases: list prices, price list*
The public price of a product before any contract discount.
Databricks list prices live in `system.billing.list_prices`. We use them to build a model of cost, not as the money truth.

### Effective price {#effective-price}
*Aliases: EffectivePrice*
The unit price you really paid per meter, after discounts, taken from the Azure export column `EffectivePrice`.

### Agreement type (EA / MCA / MPA) {#agreement}
*Aliases: EA, MCA, MPA*
The contract under which you buy Azure: Enterprise Agreement, Microsoft Customer Agreement or Microsoft Partner Agreement. Column names in the export differ between them.

### FOCUS {#focus}
An open cost-data format. Azure can export it, but this audit needs the plain Actual cost details export instead.

## Databricks building blocks

### Databricks workspace {#workspace}
*Aliases: workspaces*
One Databricks environment where people run notebooks, jobs and queries. Usually one per team, region or stage (dev / prod).

### Unity Catalog {#unity-catalog}
Databricks' central place for data permissions and metadata. It is also where the system tables live.

### System tables {#system-tables}
*Aliases: system table, system.billing*
Read-only tables inside Databricks (schema `system`) that record usage, prices, jobs, clusters and queries.
We query them with SQL. Retention is limited, so old dates may be missing (STOP-7).

### DBU {#dbu}
*Aliases: DBUs, Databricks Unit*
The unit Databricks uses to measure how much compute you consumed per hour.
A larger machine consumes more DBU per hour. Your Databricks charge is DBU × the price of one DBU. The price depends on the SKU.

### SKU {#sku}
*Aliases: SKUs, sku_name*
One exact billable product with its own price, for example "Jobs compute, Premium, West Europe".

### SKU family {#sku-family}
The compute type behind a SKU: Jobs, All-Purpose, SQL, Pipelines, Serverless and so on. It sets the price per DBU.

### Tier {#tier}
*Aliases: Standard, Premium*
The workspace plan: Standard or Premium. Premium costs more per DBU. Azure retires Standard on 1 Oct 2026, which raises the price with no change in usage.

### Photon {#photon}
Databricks' faster query engine. It also raises the number of DBU per hour, so it can raise the bill even when it makes jobs shorter.

### Classic compute {#classic-compute}
Compute that runs in **your** Azure subscription. You pay twice: DBU to Databricks and virtual machines to Azure.

### Serverless {#serverless}
Compute that Databricks runs for you. The machines are included in a higher DBU price, so there is no separate VM line. Never add VM cost to serverless usage.

### All-purpose compute {#all-purpose}
*Aliases: all-purpose cluster, interactive cluster*
Clusters for interactive work in notebooks. About 1.8 times pricier per DBU than Jobs compute for the same work.

### Jobs compute {#jobs-compute}
*Aliases: job cluster, jobs cluster*
Clusters created for a scheduled job and removed after it. The cheapest way to run the same workload.

### Job {#job}
*Aliases: jobs, workflow*
A scheduled or triggered piece of work in Databricks. When a job runs on an all-purpose cluster, its `job_id` is empty in usage data and the cost shows up as the cluster.

### Pipeline {#pipeline}
*Aliases: pipelines, DLT, Lakeflow, Delta Live Tables*
A declarative data pipeline (Lakeflow / Delta Live Tables). It has an edition (Core, Pro, Advanced) that affects the price.

### SQL warehouse {#sql-warehouse}
*Aliases: SQL warehouses, warehouse, warehouses*
Compute for SQL queries and dashboards. Sizes run from 2X-Small to 2X-Large; each size has a fixed DBU rate per hour.

### Cluster {#cluster}
*Aliases: clusters*
A group of virtual machines that runs Spark code: one driver and several workers.

### Instance pool {#instance-pool}
*Aliases: instance pools, pool, pools*
A set of ready, idle virtual machines that start clusters faster. Idle pool machines cost VM money with no DBU.

### Notebook {#notebook}
*Aliases: notebooks*
An interactive document with code, run on a cluster or serverless.

### Model serving, Vector Search, Apps {#ai-apps}
*Aliases: Model Serving, Vector Search, Databricks Apps, Lakebase*
AI and application products priced in their own units, usually serverless.

### Usage unit {#usage-unit}
*Aliases: usage_unit*
The unit a quantity is measured in (DBU, GB, hours). Never add quantities with different units.

### Price join {#price-join}
How the audit attaches a price to each usage row. It is valid only if every row matches exactly one price (rule R7).

### SCD2 history {#scd2}
*Aliases: SCD2, slowly changing dimension*
A table that keeps one row per version of a setting with the time of change. This is how we find *when* a cluster, job or warehouse was reconfigured.

### Tag {#tag}
*Aliases: tags, custom tags*
A label (owner, cost_center, application) on a resource. Untagged cost cannot be assigned to an owner.

## Azure infrastructure around Databricks

### Virtual machine (VM) {#vm}
*Aliases: VMs, virtual machines*
A virtual server rented in Azure. Classic compute is built from VMs.

### Managed disk {#managed-disk}
*Aliases: managed disks*
Disk storage attached to a VM.

### On-demand and Spot {#spot}
*Aliases: on-demand, Spot*
On-demand: fixed price, no commitment. Spot: spare capacity at a big discount that Azure can take back at any time.

### Egress {#egress}
Data leaving an Azure region or going to the internet. Moving data across regions costs money.

### NAT gateway and Private Link {#nat-private-link}
*Aliases: NAT, NAT Gateway, Private Link, Private Endpoint*
Network services that give private or outbound connectivity. They charge per hour and per gigabyte processed.

### Log Analytics {#log-analytics}
Azure's log storage and search. Verbose diagnostic settings can raise its cost a lot.

### ADLS / Blob storage {#adls}
*Aliases: ADLS, Blob, Storage account*
Azure storage where Databricks keeps data (Delta tables, checkpoints, logs).

## The audit method

### Delta (Δ) {#delta}
*Aliases: Δ*
The difference between "after" and "before". Δ per day is the daily cost in C minus the daily cost in B.

### Per-day rate {#per-day}
*Aliases: per day, daily rate, cost per day*
Cost of a period divided by the number of calendar days in it. Months have 28 to 31 days, so we always compare per-day rates, not monthly totals.

### Baseline, Comparison, Persistence (B / C / P) {#bcp}
*Aliases: B / C / P, baseline, comparison period*
The three periods of the audit. **B** is the calm period before the growth (at least 28 stable days). **C** is the first full month at the higher level. **P** is the month after C, used to check that the growth stays.

### Onset {#onset}
The first day the cost moved to a new, higher level and stayed there for 14 days or more (rule R5).

### Spike {#spike}
A short rise that ends within 14 days. Not a trend.

### Shape: step, ramp, spike, seasonal {#shape}
*Aliases: step change, ramp, seasonal*
How the growth looks over time: a one-time jump (step), a gradual climb (ramp), a short peak (spike) or a repeating pattern (seasonal).

### Delta bridge {#bridge}
*Aliases: bridge, delta_bridge*
A table that splits the total growth into parts that add up to it: accounting effects, root causes, shared cost, out-of-scope and unexplained.
If the parts do not add up to the total, the audit is not finished.

### Bucket {#bucket}
*Aliases: buckets*
A cost category used in step 04: Databricks platform, classic infrastructure, storage, network, monitoring, shared and out of scope.

### Material line {#material}
*Aliases: material, materiality*
A line big enough to investigate: at least 5% of the total change per day, or among the top 10 increases (rule R3).

### Driver {#driver}
*Aliases: drivers*
A specific thing that made the cost grow - for example a job that now runs hourly instead of daily.

### Driver candidate {#driver-candidate}
*Aliases: driver candidates, DRIVER_CANDIDATE*
A suspected driver found in step 05 that is not yet proven.

### Driver card {#driver-card}
*Aliases: driver cards*
A one-page document about one driver: what changed, when, how much it explains, the proof and the fix.

### Root cause {#root-cause}
The technical reason behind a driver, with a date and a measured effect.

### Hypothesis {#hypothesis}
*Aliases: hypotheses*
A proposed explanation that is tested and then confirmed or rejected. The hypothesis register holds 80 ready ones.

### Evidence {#evidence}
*Aliases: evidence row, EVD*
A saved result file plus a row in the evidence register that says where it came from, with which parameters and what it shows. IDs look like `EVD-04-003`.

### Residual (unexplained) {#residual}
*Aliases: UNEXPLAINED, unexplained, UNX*
The part of the growth that no driver or accounting effect covers. It is shown openly, never spread across drivers (rule R4). Up to 10% is normal.

### Attribution {#attribution}
*Aliases: attributed, unattributed*
Assigning cost to an owner or team, usually through tags and workspace ownership.

### Volume effect and rate effect {#volume-rate}
*Aliases: volume_effect, rate_effect*
Growth caused by more usage (volume) versus growth caused by a higher unit price (rate).

### Mix shift {#mix-shift}
*Aliases: MIX_SHIFT*
Usage moved from one SKU to another. The old one drops, the new one rises, and together they roughly cancel.

### Change class {#change-class}
*Aliases: change_class*
A label for each object between B and C: NEW, GONE, GROWN, SHRUNK or FLAT.

### Cumulative share {#cumulative-share}
*Aliases: cumulative_share*
The running total of the share of growth explained when objects are listed from biggest to smallest. We stop at 90%.

### Gate {#gate}
*Aliases: gates, G0*
The exit condition of a step. You do not move on until the gate check is ticked.

### Audit rules R1-R12 {#rules}
*Aliases: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12*
Twelve binding rules of the method, such as "one money truth" (R1) or "read-only" (R12). See [reference 05](05_audit_rules.md).

### STOP rules {#stop-rules}
*Aliases: STOP-1, STOP-2, STOP-3, STOP-4, STOP-5, STOP-6, STOP-7, STOP-8*
Known data traps (overlapping exports, mixed currencies, missing months and others). When one triggers, fix the data first.

### Status: CONFIRMED, LIKELY, HYPOTHESIS, REJECTED, UNKNOWN {#status}
*Aliases: CONFIRMED, LIKELY, REJECTED*
The one vocabulary for how sure we are. CONFIRMED needs four proofs (rule R9); LIKELY has two; HYPOTHESIS is untested; REJECTED is disproved; UNKNOWN means data is missing.

### Direction check (R8) {#direction-check}
A sanity check: the Azure Databricks meter and the Databricks cost model must move the same way, within 15 percentage points.

### Reconciliation (R6) {#reconciliation}
*Aliases: reconcile*
Comparing two sources of the same number. The export total and Cost Analysis must agree within 0.5%.

### Read-only {#read-only}
The audit never changes anything in Azure or Databricks. Running SQL does use warehouse compute, so ask for approval first.

### Statement Execution API {#statement-api}
*Aliases: Databricks SQL connection*
The Databricks interface the app uses to run your SELECT queries. It only reads.

### Personal access token (PAT) {#pat}
*Aliases: PAT, token*
A password-like key for Databricks. The app keeps it in memory only and never saves it to disk.

### IBM Cloudability and ApptioOne {#ibm}
*Aliases: Cloudability, ApptioOne, Apptio, IBM*
IBM's FinOps tools that some companies use to report cloud cost. Their numbers are an alternative view and are never added to Azure Actual.

### Audit owner {#audit-owner}
The person who asked for the audit and approves the scope and the report.

### Reproducibility {#reproducibility}
*Aliases: reproduce, reproducible*
Anyone can re-run a saved step with the saved parameters and get the same numbers (step 08).
