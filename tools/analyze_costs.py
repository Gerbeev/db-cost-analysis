#!/usr/bin/env python3
"""Read-only analysis of Azure Actual Cost and Databricks list-price CSV exports.

No cloud calls and no dependency outside the Python standard library.
Azure actual billed costs and Databricks list-price estimates are NEVER added.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

TRACE = 5
logging.addLevelName(TRACE, "TRACE")
LOG = logging.getLogger("azure_databricks_cost_rca")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
ZERO = Decimal("0")
# Only plain signed decimal literals may start with + or - without escaping.
CSV_NUMERIC_LITERAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
CSV_LEADING_IGNORABLE = " \t\r\n\v\f\u00a0\ufeff\u200b"


def csv_safe_cell(value: object) -> str:
    """Neutralize spreadsheet formulas in untrusted CSV cells; preserve numeric costs.

    This is an export-only transformation. Original values remain unchanged in
    calculations and manifests. CSV quoting by itself does not prevent formulas.
    """
    text = "" if value is None else str(value)
    candidate = text.lstrip(CSV_LEADING_IGNORABLE)
    if candidate.startswith(("=", "+", "-", "@")):
        if not CSV_NUMERIC_LITERAL.fullmatch(text.strip()):
            return "'" + text
    return text



class DataError(ValueError):
    """Input cannot be reliably analyzed."""


def normalize_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def pick_field(fieldnames: list[str], *aliases: str, required: bool = False) -> str | None:
    index = {normalize_header(h): h for h in fieldnames}
    for name in aliases:
        found = index.get(normalize_header(name))
        if found is not None:
            return found
    if required:
        raise DataError(f"Missing required CSV column; expected one of: {', '.join(aliases)}")
    return None


def parse_month(value: str) -> str:
    value = value.strip()
    if not MONTH_RE.fullmatch(value):
        raise DataError(f"Expected YYYY-MM, got {value!r}")
    return value


def month_sequence(start: str, end: str) -> list[str]:
    start, end = parse_month(start), parse_month(end)
    if start > end:
        raise DataError("--start must not be after --end")
    result = []
    year, month = map(int, start.split("-"))
    while f"{year:04d}-{month:02d}" <= end:
        result.append(f"{year:04d}-{month:02d}")
        if len(result) > 120:
            raise DataError("Maximum analysis window is 120 months")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def parse_date_month(raw: str) -> str:
    val = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val[:10] if fmt == "%Y-%m-%d" else val, fmt).strftime("%Y-%m")
        except ValueError:
            pass
    raise DataError(f"Unsupported Azure usage date {val!r}; use ISO date or MM/DD/YYYY")


def money(raw: str, label: str) -> Decimal:
    v = str(raw).strip().replace(",", "")
    if not v:
        raise DataError(f"Missing {label} amount")
    try:
        amount = Decimal(v)
    except InvalidOperation as exc:
        raise DataError(f"Invalid {label} numeric amount {raw!r}") from exc
    if not amount.is_finite():
        raise DataError(f"Non-finite {label} numeric amount")
    return amount


def csv_rows(path: Path, handler: Callable[[dict[str, str], list[str], int], None]) -> int:
    if not path.is_file():
        raise DataError(f"Input file not found: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise DataError(f"Input CSV has no header: {path}")
            if len(set(map(normalize_header, reader.fieldnames))) != len(reader.fieldnames):
                raise DataError(f"Duplicate or ambiguous CSV headers: {path}")
            rows = 0
            for line_num, row in enumerate(reader, start=2):
                if None in row:
                    raise DataError(f"CSV has extra fields on line {line_num}: {path}")
                if not any((v or "").strip() for v in row.values()):
                    continue
                try:
                    handler(row, reader.fieldnames, line_num)
                except DataError as exc:
                    raise DataError(f"{path.name}:{line_num}: {exc}") from exc
                rows += 1
    except UnicodeDecodeError as exc:
        raise DataError(f"CSV must be UTF-8 or UTF-8 with BOM: {path}") from exc
    if rows == 0:
        raise DataError(f"CSV is empty: {path}")
    return rows


def read_databricks(path: Path, months: list[str]) -> dict:
    allowed = set(months)
    totals = defaultdict(lambda: ZERO)
    products = defaultdict(lambda: ZERO)
    sku_rows = defaultdict(lambda: ZERO)
    workspaces = defaultdict(lambda: ZERO)
    uncovered = defaultdict(int)
    present = set()
    skipped = 0
    raw_count = 0
    schema = None

    def process(row: dict, headers: list[str], line: int) -> None:
        nonlocal schema, skipped, raw_count
        if schema is None:
            schema = {k: pick_field(headers, k, required=True) for k in (
                "month", "account_id", "workspace_id", "product", "sku_name",
                "currency_code", "estimated_list_cost", "unpriced_records")}
        raw_count += 1
        m = parse_month(row[schema["month"]])
        if m not in allowed:
            skipped += 1
            return
        present.add(m)
        curr = (row[schema["currency_code"]] or "UNPRICED").strip().upper()
        account = (row[schema["account_id"]] or "UNKNOWN").strip()
        workspace = (row[schema["workspace_id"]] or "UNKNOWN").strip()
        product = (row[schema["product"]] or "UNKNOWN").strip()
        sku = (row[schema["sku_name"]] or "UNKNOWN").strip()
        missing = money(row[schema["unpriced_records"]], "unpriced_records")
        if missing != missing.to_integral_value() or missing < 0:
            raise DataError("unpriced_records must be a non-negative integer")
        uncovered[(m, account, workspace, product, sku)] += int(missing)
        value_raw = (row[schema["estimated_list_cost"]] or "").strip()
        if not value_raw:
            if int(missing) == 0:
                raise DataError("Missing estimated_list_cost without unpriced_records")
            return
        if curr == "UNPRICED":
            raise DataError("Non-empty estimated_list_cost with UNPRICED currency")
        cost = money(value_raw, "Databricks estimated_list_cost")
        totals[(m, curr)] += cost
        products[(m, curr, account, workspace, product, sku)] += cost
        sku_rows[(m, curr, product, sku)] += cost
        workspaces[(m, curr, account, workspace)] += cost

    csv_rows(path, process)
    return dict(totals=totals, products=products, sku_rows=sku_rows,
                workspaces=workspaces, uncovered=uncovered, present=present,
                skipped=skipped, row_count=raw_count)


def read_azure(path: Path, months: list[str]) -> dict:
    allowed = set(months)
    totals = defaultdict(lambda: ZERO)
    services = defaultdict(lambda: ZERO)
    meters = defaultdict(lambda: ZERO)
    resource_groups = defaultdict(lambda: ZERO)
    resources = defaultdict(lambda: ZERO)
    charge_types = defaultdict(lambda: ZERO)
    present = set()
    missing_resource = 0
    skipped = 0
    raw_count = 0
    schema = None

    def process(row: dict, headers: list[str], line: int) -> None:
        nonlocal schema, missing_resource, skipped, raw_count
        if schema is None:
            schema = {
                "date": pick_field(headers, "Date", "UsageDate", required=True),
                "cost": pick_field(headers, "CostInBillingCurrency", "Cost", required=True),
                "currency": pick_field(headers, "BillingCurrency", "BillingCurrencyCode", "Currency", required=True),
                "service": pick_field(headers, "ServiceName", "MeterCategory", "ConsumedService", required=True),
                "meter": pick_field(headers, "MeterName", "Meter", "MeterSubCategory"),
                "rg": pick_field(headers, "ResourceGroup", "ResourceGroupName"),
                "resource": pick_field(headers, "ResourceId", "InstanceId"),
                "subscription": pick_field(headers, "SubscriptionId"),
                "charge": pick_field(headers, "ChargeType"),
            }
        raw_count += 1
        m = parse_date_month(row[schema["date"]] or "")
        if m not in allowed:
            skipped += 1
            return
        present.add(m)
        currency = (row[schema["currency"]] or "").strip().upper()
        if not currency:
            raise DataError("Missing billing currency")
        cost = money(row[schema["cost"]] or "", "Azure Actual cost")
        service = (row[schema["service"]] or "UNKNOWN").strip()
        meter = (row[schema["meter"]] or "UNKNOWN").strip() if schema["meter"] else "UNKNOWN"
        rg = (row[schema["rg"]] or "UNASSIGNED").strip() if schema["rg"] else "UNASSIGNED"
        resource = (row[schema["resource"]] or "").strip() if schema["resource"] else ""
        subscription = (row[schema["subscription"]] or "UNKNOWN").strip() if schema["subscription"] else "UNKNOWN"
        charge = (row[schema["charge"]] or "UNSPECIFIED").strip() if schema["charge"] else "UNSPECIFIED"
        if not resource:
            missing_resource += 1
            resource = "UNASSIGNED"
        totals[(m, currency)] += cost
        services[(m, currency, service)] += cost
        meters[(m, currency, service, meter)] += cost
        resource_groups[(m, currency, subscription, rg)] += cost
        resources[(m, currency, subscription, rg, resource)] += cost
        charge_types[(m, currency, charge)] += cost

    csv_rows(path, process)
    return dict(totals=totals, services=services, meters=meters,
                resource_groups=resource_groups, resources=resources,
                charge_types=charge_types, present=present, skipped=skipped,
                missing_resource=missing_resource, row_count=raw_count)


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([csv_safe_cell(cell) for cell in headers])
        writer.writerows([csv_safe_cell(cell) for cell in row] for row in rows)


def fmt(value: Decimal | None) -> str:
    return "N/A" if value is None else str(value.quantize(Decimal("0.01")))


def growth_rows(grouped: dict, first: str, last: str, total: dict) -> list[tuple]:
    # The same grouping cannot safely be compared if one endpoint currency-month is missing.
    keys = {(key[1], *key[2:]) for key in grouped}
    result = []
    for currency, *dimensions in keys:
        if (first, currency) not in total or (last, currency) not in total:
            continue
        begin = grouped.get((first, currency, *dimensions), ZERO)
        end = grouped.get((last, currency, *dimensions), ZERO)
        delta = end - begin
        percent = f"{(delta / begin * 100):.2f}" if begin > ZERO else "N/A"
        result.append((currency, *dimensions, begin, end, delta, percent))
    result.sort(key=lambda r: r[-2], reverse=True)
    return result


def report_growth(path: Path, grouped: dict, dims: list[str], first: str, last: str, total: dict) -> list[tuple]:
    result = growth_rows(grouped, first, last, total)
    write_csv(path, ["currency", *dims, f"{first}_cost", f"{last}_cost", "delta", "delta_percent"],
              [[*rec[:-4], fmt(rec[-4]), fmt(rec[-3]), fmt(rec[-2]), rec[-1]] for rec in result])
    return result


def month_days(month: str) -> int:
    year, month_index = map(int, parse_month(month).split("-"))
    return calendar.monthrange(year, month_index)[1]


def month_over_month_rows(data: dict, months: list[str]) -> list[list[str]]:
    """Report missing coverage as N/A; normalize month length for change-point checks."""
    currencies = sorted({currency for _, currency in data["totals"]})
    rows = []
    for currency in currencies:
        for index, current in enumerate(months):
            year, month_number = map(int, current.split("-"))
            prior_year, prior_month = ((year - 1, 12) if month_number == 1
                                      else (year, month_number - 1))
            candidate = f"{prior_year:04d}-{prior_month:02d}"
            previous = candidate if candidate in months else None
            current_cost = data["totals"].get((current, currency))
            previous_cost = data["totals"].get((previous, currency)) if previous else None
            current_daily = current_cost / month_days(current) if current_cost is not None else None
            previous_daily = (previous_cost / month_days(previous)
                              if previous_cost is not None and previous is not None else None)
            delta = (current_cost - previous_cost
                     if current_cost is not None and previous_cost is not None else None)
            daily_delta = (current_daily - previous_daily
                           if current_daily is not None and previous_daily is not None else None)
            pct = (f"{delta / previous_cost * 100:.2f}"
                   if delta is not None and previous_cost > ZERO else "N/A")
            daily_pct = (f"{daily_delta / previous_daily * 100:.2f}"
                         if daily_delta is not None and previous_daily > ZERO else "N/A")
            rows.append([current, currency, previous or "N/A", fmt(previous_cost),
                         fmt(current_cost), fmt(delta), pct, fmt(previous_daily),
                         fmt(current_daily), fmt(daily_delta), daily_pct])
    return rows


MOM_HEADERS = ["month", "currency", "previous_month", "previous_month_cost",
               "current_month_cost", "month_delta", "month_delta_percent",
               "previous_daily_average", "current_daily_average", "daily_average_delta",
               "daily_average_delta_percent"]


def inflection_report(out: Path, months: list[str], data: dict, slug: str, label: str) -> list[str]:
    rows = month_over_month_rows(data, months)
    write_csv(out / f"change_point_mom_{slug}.csv", MOM_HEADERS, rows)
    selected = [r for r in rows if r[0] in {"2026-02", "2026-03", "2026-04", "2026-05"}]
    notes = [f"## 2026 March/April change-point analysis - {label}", "",
             "Suspected timing only. The cost increase remains unverified until reconciled to source billing and workload evidence.",
             "Monthly totals are also normalized to average cost per calendar day to account for month length.", "",
             "| Month | Currency | Previous | Cost | Monthly delta | Daily-average delta | Daily-average % |",
             "|---|---|---|---:|---:|---:|---:|"]
    for row in selected:
        notes.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[4]} | {row[5]} | {row[9]} | {row[10]} |")
    notes += ["", f"Full 2026 month-over-month data: `change_point_mom_{slug}.csv`.",
              "Check whether the increase began in March, accelerated in April, and persisted in May; compare February and earlier spend before attributing causality.", ""]
    return notes


def validate_quality(data: dict, label: str, months: list[str]) -> list[str]:
    notes = [f"{label}: read {data['row_count']} rows; skipped {data['skipped']} outside requested window."]
    absent = [m for m in months if m not in data["present"]]
    if absent:
        notes.append(f"WARNING: {label} missing months: {', '.join(absent)}. Missing must not be interpreted as zero.")
    currencies = sorted({c for _, c in data["totals"]})
    if len(currencies) > 1:
        notes.append(f"WARNING: {label} has multiple currencies ({', '.join(currencies)}); never add different currencies.")
    for curr in currencies:
        currency_months = [m for m in months if (m, curr) not in data["totals"]]
        if currency_months:
            notes.append(f"WARNING: {label} currency {curr} has missing months: {', '.join(currency_months)}.")
    if label == "Databricks":
        missing_prices = sum(data["uncovered"].values())
        if missing_prices:
            notes.append(f"WARNING: {missing_prices} unpriced Databricks billing records; estimates are incomplete.")
        notes.append("Databricks totals are effective *list-price estimates*, not invoiced charges.")
    else:
        if data["missing_resource"]:
            notes.append(f"NOTICE: {data['missing_resource']} Azure records lack a ResourceId; can be legitimate charges or allocations.")
        notes.append("Azure totals cover every record in the supplied export; Databricks attribution requires explicit scope filtering.")
        notes.append("WARNING: Cannot detect overlapping full Azure export runs automatically; confirm only one run covers any given date.")
    return notes


def create_report(out: Path, months: list[str], db: dict | None, az: dict | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    start, end = months[0], months[-1]
    quality = ["# Input quality and financial guardrails", "", "Period: " + start + " through " + end + " (inclusive).", ""]
    report = ["# Azure Databricks cost investigation - local summary", "",
              f"**Period:** {start} through {end} (completed months only).", "",
              "**Do not add** Databricks list-price estimates to Azure billed actuals; they are separate lenses.", ""]
    datasets = (("Azure Actual", az, "monthly_azure_actual.csv"),
                ("Databricks Estimated List Price", db, "monthly_databricks_estimated.csv"))
    for title, data, filename in datasets:
        report += [f"## {title}", ""]
        if data is None:
            report += ["No input provided; this view was not analyzed.", ""]
            continue
        label = "Azure" if title.startswith("Azure") else "Databricks"
        quality += [f"## {label}", ""] + [f"- {n}" for n in validate_quality(data, label, months)] + [""]
        currencies = sorted({curr for (_, curr) in data["totals"]})
        write_csv(out / filename, ["month", "currency", "cost"],
                  [[m, c, fmt(data["totals"].get((m, c)))] for c in currencies for m in months])
        report += ["| Month | Currency | Cost |", "|---|---|---:|"]
        for curr in currencies:
            for m in months:
                report.append(f"| {m} | {curr} | {fmt(data['totals'].get((m, curr)))} |")
        report.append("")
        for curr in currencies:
            first_cost = data["totals"].get((start, curr))
            last_cost = data["totals"].get((end, curr))
            if first_cost is None or last_cost is None:
                report.append(f"- {curr}: endpoint comparison unavailable (missing month); investigate coverage.")
                continue
            delta = last_cost - first_cost
            pct = f"{delta / first_cost * 100:.2f}%" if first_cost > 0 else "N/A"
            report.append(f"- {curr}: **{start} → {end} delta: {fmt(delta)} ({pct})**.")
        report.append("")
        slug = "azure_actual" if label == "Azure" else "databricks_estimated"
        report += inflection_report(out, months, data, slug, label)
    if az is not None:
        detail = (
            ("Azure services", "growth_azure_services.csv", az["services"], ["service"]),
            ("Azure meters", "growth_azure_meters.csv", az["meters"], ["service", "meter"]),
            ("Azure resource groups", "growth_azure_resource_groups.csv", az["resource_groups"], ["subscription", "resource_group"]),
            ("Azure resources", "growth_azure_resources.csv", az["resources"], ["subscription", "resource_group", "resource_id"]),
            ("Azure charge types", "growth_azure_charge_types.csv", az["charge_types"], ["charge_type"]),
        )
        for heading, filename, grouped, dims in detail:
            results = report_growth(out / filename, grouped, dims, start, end, az["totals"])
            report += [f"## Largest positive deltas - {heading}", "",
                       f"Detailed file: `{filename}`. These are separate breakdowns of the SAME Azure charges; do not sum across breakdowns.", ""]
            report += ["| Driver | Currency | Delta |", "|---|---|---:|"]
            for curr, *parts in results[:10]:
                driver = " / ".join(str(v).replace("|", "/") for v in parts[:-4])
                report.append(f"| {driver} | {curr} | {fmt(parts[-2])} |")
            report.append("")
            for previous, current, period_key, period_label in (
                ("2026-02", "2026-03", "feb_mar", "February→March"),
                ("2026-03", "2026-04", "mar_apr", "March→April"),
                ("2026-04", "2026-05", "apr_may", "April→May"),
            ):
                if previous not in months or current not in months:
                    continue
                targeted_file = filename.replace("growth_", f"growth_{period_key}_", 1)
                targeted = report_growth(out / targeted_file, grouped, dims,
                                         previous, current, az["totals"])
                report += [f"### {period_label} drivers - {heading}", "",
                           f"Detailed file: `{targeted_file}`.", "",
                           "| Driver | Currency | Delta |", "|---|---|---:|"]
                for currency, *parts in targeted[:10]:
                    driver = " / ".join(str(v).replace("|", "/") for v in parts[:-4])
                    report.append(f"| {driver} | {currency} | {fmt(parts[-2])} |")
                report.append("")
    if db is not None:
        detail = (
            ("Databricks account/workspace/product/SKU", "growth_databricks.csv", db["products"], ["account_id", "workspace_id", "product", "sku_name"]),
            ("Databricks product/SKU", "growth_databricks_skus.csv", db["sku_rows"], ["product", "sku_name"]),
            ("Databricks workspaces", "growth_databricks_workspaces.csv", db["workspaces"], ["account_id", "workspace_id"]),
        )
        for heading, filename, grouped, dims in detail:
            results = report_growth(out / filename, grouped, dims, start, end, db["totals"])
            report += [f"## Largest positive deltas - {heading}", "",
                       f"Detailed file: `{filename}`. These are list-price estimates, NOT Azure billed actuals.", "",
                       "| Driver | Currency | Delta |", "|---|---|---:|"]
            for curr, *parts in results[:10]:
                driver = " / ".join(str(v).replace("|", "/") for v in parts[:-4])
                report.append(f"| {driver} | {curr} | {fmt(parts[-2])} |")
            report.append("")
            for previous, current, period_key, period_label in (
                ("2026-02", "2026-03", "feb_mar", "February→March"),
                ("2026-03", "2026-04", "mar_apr", "March→April"),
                ("2026-04", "2026-05", "apr_may", "April→May"),
            ):
                if previous not in months or current not in months:
                    continue
                targeted_file = filename.replace("growth_", f"growth_{period_key}_", 1)
                targeted = report_growth(out / targeted_file, grouped, dims,
                                         previous, current, db["totals"])
                report += [f"### {period_label} drivers - {heading}", "",
                           f"Detailed file: `{targeted_file}`." + " Modeled list-price estimate only.", "",
                           "| Driver | Currency | Delta |", "|---|---|---:|"]
                for currency, *parts in targeted[:10]:
                    driver = " / ".join(str(v).replace("|", "/") for v in parts[:-4])
                    report.append(f"| {driver} | {currency} | {fmt(parts[-2])} |")
                report.append("")
    quality += ["## Source control", "",
                "- Verify Azure Actual cost totals against Azure Cost Analysis at the identical billing scope.",
                "- One export revision per month; verify no overlapping reruns or omitted partitions.",
                "- Investigate blank/incomplete SKU price joins before trusting Databricks list-price totals.",
                "- Contract discounts, refunds, purchases and commitments can change invoice amounts.",
                "- No silent currency conversions; do not sum different currency totals.",
                "- Grouping output is descriptive. Owner and causal validation must be completed manually.", ""]
    report += ["## Next steps", "", "1. Read `data_quality.md` and resolve gaps.",
               "2. Validate Azure actual totals at the same financial scope and export revision.",
               "3. Review February→March, March→April and April→May per-day-normalized cost changes; investigate March→April top Azure/Databricks drivers and workloads.",
               "4. Capture timestamps, owners, cause and alternatives in `audits/<audit-id>/09_report_and_controls/findings_report.md`.",
               "5. Request approval before making any infrastructure or scheduling change.", ""]
    (out / "summary.md").write_text("\n".join(report), encoding="utf-8")
    (out / "data_quality.md").write_text("\n".join(quality), encoding="utf-8")


def configure_logging(level: str) -> None:
    folder = Path(__file__).resolve().parents[1] / "audits" / "_logs"
    folder.mkdir(parents=True, exist_ok=True)
    LOG.setLevel(TRACE)
    for existing_handler in list(LOG.handlers):
        LOG.removeHandler(existing_handler)
        existing_handler.close()
    file_handler = logging.FileHandler(folder / "analysis.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    levels = {"CRITICAL": logging.CRITICAL, "ERROR": logging.ERROR,
              "WARNING": logging.WARNING, "INFO": logging.INFO, "DEBUG": logging.DEBUG,
              "TRACE": TRACE}
    file_handler.setLevel(levels[level])
    LOG.addHandler(file_handler)
    LOG.propagate = False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Analyze local Azure Actual and Databricks estimated cost exports (separate ledgers).")
    ap.add_argument("--azure", type=Path, help="Single deduplicated Azure Actual-cost CSV")
    ap.add_argument("--databricks", type=Path, help="Databricks SQL 01 CSV export")
    ap.add_argument("--start", default="2026-01", help="First full month, YYYY-MM (default: 2026-01)")
    ap.add_argument("--end", default="2026-10", help="Last full month, YYYY-MM (default: 2026-10)")
    ap.add_argument("--out", type=Path, default=Path("audits/_shared/analyzer"))
    ap.add_argument("--log-level", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"], default="INFO")
    args = ap.parse_args(argv)
    configure_logging(args.log_level)
    try:
        if not args.azure and not args.databricks:
            raise DataError("Provide --azure, --databricks, or both")
        months = month_sequence(args.start, args.end)
        LOG.info("Starting read-only offline analysis for %s through %s", months[0], months[-1])
        az = read_azure(args.azure, months) if args.azure else None
        db = read_databricks(args.databricks, months) if args.databricks else None
        create_report(args.out, months, db, az)
        for label, data in (("Azure", az), ("Databricks", db)):
            if data:
                LOG.info("%s: %s input records, %s analyzed months", label, data["row_count"], len(data["present"]))
        LOG.info("Completed offline report generation")
        print(f"Generated report: {args.out / 'summary.md'}")
        print(f"Data quality:     {args.out / 'data_quality.md'}")
        print("Financial reminder: do not add Azure billed actuals to Databricks list-price estimates.")
        return 0
    except (DataError, OSError, csv.Error) as exc:
        LOG.error("Analysis failed: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
