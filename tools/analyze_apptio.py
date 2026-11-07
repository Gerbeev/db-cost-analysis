#!/usr/bin/env python3
"""Offline analysis of normalized IBM Apptio exports, kept separate from Azure billing."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from analyze_costs import (DataError, csv_rows, fmt, money, month_sequence, write_csv,
                           configure_logging, month_over_month_rows, MOM_HEADERS, LOG)


def analyze(path: Path, months: list[str]) -> dict:
    totals: dict[tuple, Decimal] = defaultdict(lambda: Decimal("0"))
    groups: dict[tuple, Decimal] = defaultdict(lambda: Decimal("0"))
    present = set()
    analyzed = 0
    all_count = 0
    dims = []
    metric_set = set()
    views = set()
    schema = None

    def handler(row: dict[str, str], headers: list[str], line: int) -> None:
        nonlocal schema, analyzed, all_count, dims
        all_count += 1
        if schema is None:
            required = {"month", "currency", "metric", "view_id", "amount"}
            if not required.issubset(headers):
                raise DataError(f"IBM Apptio CSV missing headers: {', '.join(sorted(required - set(headers)))}")
            dims = [h for h in headers if h not in required]
            schema = True
        month = row["month"].strip()
        if month not in months:
            return
        currency, metric, view = row["currency"].strip(), row["metric"].strip(), row["view_id"].strip()
        if not currency or not metric or not view:
            raise DataError("IBM Apptio CSV is missing currency, metric, or view")
        metric_set.add(metric)
        views.add(view)
        cost = money(row["amount"], "IBM Apptio cost")
        present.add(month)
        analyzed += 1
        totals[(month, currency)] += cost
        groups[(month, currency, *[row[k].strip() for k in dims])] += cost

    csv_rows(path, handler)
    if len(metric_set) != 1 or len(views) != 1:
        raise DataError("Do not combine different IBM Apptio cost metrics or view scopes in one analysis")
    return {"totals": totals, "groups": groups, "present": present, "dimensions": dims,
            "metrics": metric_set, "views": views, "analyzed": analyzed, "all_count": all_count}


def create_report(data: dict, months: list[str], out: Path, manifest: dict | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    currencies = sorted({curr for _, curr in data["totals"]})
    first, last = months[0], months[-1]
    notes = ["# IBM Apptio cost analysis", "",
             "**Separate attribution lens:** do not add these amounts to Azure Actual or Databricks estimates.", "",
             f"Metric: `{next(iter(data['metrics']))}` | View: `{next(iter(data['views']))}`", "",
             "## Monthly totals", "", "| Month | Currency | Cost |", "|---|---|---:|"]
    monthly = []
    for curr in currencies:
        for month in months:
            cost = data["totals"].get((month, curr))
            notes.append(f"| {month} | {curr} | {fmt(cost)} |")
            monthly.append([month, curr, fmt(cost)])
    write_csv(out / "apptio_monthly.csv", ["month", "currency", "cost"], monthly)
    mom = month_over_month_rows(data, months)
    write_csv(out / "apptio_change_point_mom.csv", MOM_HEADERS, mom)
    notes += ["", "## March/April 2026 change-point focus", "",
              "Suspected inflection only; amounts may reflect modeled or allocated costs and are not independent Azure charges.",
              "Daily-average comparison compensates for different month lengths; verify the underlying allocation methodology.", "",
              "| Month | Currency | Prior month | Monthly delta | Daily-average delta | Daily-average % |",
              "|---|---|---|---:|---:|---:|"]
    for row in mom:
        if row[0] in {"2026-02", "2026-03", "2026-04", "2026-05"}:
            notes.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[5]} | {row[9]} | {row[10]} |")
    notes += ["", "Full timeline: `apptio_change_point_mom.csv`.", ""]
    warnings = ["# IBM Apptio export quality", "",
                f"Source CSV rows: {data['all_count']}; analyzed rows: {data['analyzed']}.",
                f"View scope: {next(iter(data['views']))}. Verify view access and subscription coverage in Apptio.",
                "Reporting currency must match the source report UI; API report rows do not necessarily carry currency metadata.",
                "Source allocations, ingestion lag and metric definition may differ from Azure Actual Cost.",
                "No automated financial reconciliation is implied by matching labels.", ""]
    if manifest:
        expected_rows = manifest.get("total_rows", manifest.get("normalized_rows"))
        if expected_rows != data["all_count"]:
            warnings.append("WARNING: Manifest row count does not equal CSV row count.")
        if manifest.get("currency_user_verified") not in (*currencies, "per_row"):
            warnings.append("WARNING: Manifest currency does not match exported data.")
        if manifest.get("metric", manifest.get("metric_user_defined")) not in data["metrics"]:
            warnings.append("WARNING: Manifest cost metric does not match exported data.")
        if "view_id" in manifest and str(manifest["view_id"]) not in data["views"]:
            warnings.append("WARNING: Manifest reporting view does not match exported data.")
    else:
        warnings.append("WARNING: Export manifest not provided; provenance and filter scope were not checked.")
    for month in months:
        if month not in data["present"]:
            warnings.append(f"WARNING: {month} has no rows. This is missing coverage, NOT an assumed zero.")
    if len(currencies) > 1:
        warnings.append("WARNING: Multiple currencies; never sum across currencies.")
    for currency in currencies:
        for month in months:
            if (month, currency) not in data["totals"]:
                warnings.append(f"WARNING: {month}/{currency} missing; endpoint growth is not comparable.")
    notes += ["", "## Growth drivers", "", "| Dimension values | Currency | First month | Last month | Delta |", "|---|---|---:|---:|---:|"]
    keys = {(key[1], *key[2:]) for key in data["groups"]}
    drivers = []
    for curr, *dim_values in keys:
        if (first, curr) not in data["totals"] or (last, curr) not in data["totals"]:
            continue
        start = data["groups"].get((first, curr, *dim_values), Decimal("0"))
        end = data["groups"].get((last, curr, *dim_values), Decimal("0"))
        drivers.append((curr, dim_values, start, end, end-start))
    drivers.sort(key=lambda item: item[-1], reverse=True)
    write_csv(out / "apptio_growth_drivers.csv",
              ["currency", *data["dimensions"], f"{first}_cost", f"{last}_cost", "delta"],
              [[curr, *vals, fmt(begin), fmt(end), fmt(delta)] for curr, vals, begin, end, delta in drivers])
    for curr, vals, begin, end, delta in drivers[:15]:
        notes.append(f"| {' / '.join(v.replace('|', '/') for v in vals)} | {curr} | {fmt(begin)} | {fmt(end)} | {fmt(delta)} |")
    for previous, current, period_key, period_label in (
        ("2026-02", "2026-03", "feb_mar", "February→March"),
        ("2026-03", "2026-04", "mar_apr", "March→April"),
        ("2026-04", "2026-05", "apr_may", "April→May"),
    ):
        if previous not in months or current not in months:
            continue
        target = []
        for curr, *dimension_values in keys:
            if (previous, curr) not in data["totals"] or (current, curr) not in data["totals"]:
                continue
            before = data["groups"].get((previous, curr, *dimension_values), Decimal("0"))
            after = data["groups"].get((current, curr, *dimension_values), Decimal("0"))
            target.append((curr, dimension_values, before, after, after - before))
        target.sort(key=lambda item: item[-1], reverse=True)
        filename = f"apptio_growth_{period_key}_drivers.csv"
        write_csv(out / filename,
                  ["currency", *data["dimensions"], f"{previous}_cost", f"{current}_cost", "delta"],
                  [[curr, *dim_values, fmt(before), fmt(after), fmt(delta)]
                   for curr, dim_values, before, after, delta in target])
        notes += ["", f"## Top {period_label} 2026 growth drivers", "",
                  f"Detailed file: `{filename}`.", "",
                  "| Dimensions | Currency | Before | After | Delta |", "|---|---|---:|---:|---:|"]
        for curr, dim_values, before, after, delta in target[:15]:
            notes.append(f"| {' / '.join(v.replace('|', '/') for v in dim_values)} | {curr} | {fmt(before)} | {fmt(after)} | {fmt(delta)} |")
    notes += ["", "## Next verification", "",
              "1. Match the metric basis (actual/unblended vs amortized) and selected Apptio view.",
              "2. Filter to the same Azure subscriptions, date ranges and charge types where possible.",
              "3. Validate matched totals and timing against Azure Cost Management Actual. Investigate gaps.",
              "4. Trace top Apptio service groups to Azure meters and Databricks workloads.", ""]
    (out / "apptio_summary.md").write_text("\n".join(notes), encoding="utf-8")
    (out / "apptio_quality.md").write_text("\n".join(warnings) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Analyze IBM Cloudability v3 or normalized TBM Studio exports separately from the Azure Actual ledger")
    ap.add_argument("--input", type=Path, default=Path("audits/_shared/apptio_cloudability.csv"))
    ap.add_argument("--manifest", type=Path, help="Optional manifest generated by Apptio exporter/normalizer")
    ap.add_argument("--start", default="2026-01")
    ap.add_argument("--end", default="2026-10")
    ap.add_argument("--out", type=Path, default=Path("audits/_shared/apptio_analysis"))
    ap.add_argument("--log-level", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"], default="INFO")
    args = ap.parse_args(argv)
    configure_logging(args.log_level)
    try:
        months = month_sequence(args.start, args.end)
        data = analyze(args.input, months)
        manifest = None
        if args.manifest:
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise DataError("Manifest must contain a JSON object")
        create_report(data, months, args.out, manifest)
        LOG.info("IBM Apptio offline analysis succeeded; %d cost rows", data["analyzed"])
        print(f"Generated {args.out / 'apptio_summary.md'}")
        print(f"Quality checks: {args.out / 'apptio_quality.md'}")
        return 0
    except (DataError, OSError, csv.Error, ValueError) as exc:
        LOG.error("Apptio analysis failed: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
