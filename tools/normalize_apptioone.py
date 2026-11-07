#!/usr/bin/env python3
"""Map a verified TBM Studio CSV/TSV cost report to the generic Apptio cost-analysis schema.

No API calls, no inferred fiscal calendar, no inferred currency or cost metric.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from analyze_costs import DataError, money, month_sequence
from apptio_api import atomic_write_csv

RESERVED = {"month", "currency", "metric", "view_id", "amount"}


def normalized_month(raw: str) -> str:
    value = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}", value):
        month = value
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise DataError("Invalid ISO date") from exc
        month = value[:7]
    else:
        raise DataError("TBM date must be ISO YYYY-MM or YYYY-MM-DD; explicitly map fiscal dates first")
    if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month):
        raise DataError("Invalid calendar month")
    return month


def convert(src: Path, out: Path, date_column: str, amount_column: str,
            dims: list[str], currency: str | None, currency_column: str | None,
            metric: str, report_label: str, start: str, end: str) -> dict:
    if bool(currency) == bool(currency_column):
        raise DataError("Specify exactly one of --currency or --currency-column")
    if not metric.strip() or not report_label.strip():
        raise DataError("--metric-name and --report-label are required")
    if currency and not re.fullmatch(r"[A-Z]{3}", currency.upper()):
        raise DataError("--currency must be a three-letter report currency")
    if len(set(dims)) != len(dims) or not dims or any(d in RESERVED for d in dims):
        raise DataError("Provide distinct --dimension columns that are not reserved output headers")
    months = set(month_sequence(start, end))
    if src.suffix.lower() not in (".tsv", ".csv"):
        raise DataError("Only .tsv and .csv are supported; use TBM Studio Show API URL to export TSV")
    delimiter = "\t" if src.suffix.lower() == ".tsv" else ","
    if not src.is_file():
        raise DataError(f"Input not found: {src}")
    entries: list[list[str]] = []
    seen = set()
    skipped = 0
    count = 0
    with src.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        if not reader.fieldnames:
            raise DataError("Input report has no headers")
        required = {date_column, amount_column, *dims}
        if currency_column:
            required.add(currency_column)
        missing = required - set(reader.fieldnames)
        if missing:
            raise DataError("Missing report columns: " + ", ".join(sorted(missing)))
        for i, row in enumerate(reader, 2):
            if None in row:
                raise DataError(f"Extra fields at line {i}; verify delimiter and report schema")
            count += 1
            try:
                month = normalized_month(row[date_column] or "")
                if month not in months:
                    skipped += 1
                    continue
                row_currency = currency.upper() if currency else (row[currency_column] or "").strip().upper()
                if not re.fullmatch(r"[A-Z]{3}", row_currency):
                    raise DataError("Missing/invalid report currency")
                value = money(row[amount_column] or "", "TBM report cost")
                entries.append([month, row_currency, metric.strip(), report_label.strip(),
                                *[(row[d] or "").strip() for d in dims], str(value)])
                seen.add(month)
            except DataError as exc:
                raise DataError(f"{src.name}:{i}: {exc}") from exc
    if not entries:
        raise DataError("No cost records in the selected calendar months; scope is unverified")
    atomic_write_csv(out, ["month", "currency", "metric", "view_id", *dims, "amount"], entries)
    manifest = {"source": "IBM ApptioOne / TBM Studio user-selected report",
                "report_label": report_label, "metric_user_defined": metric,
                "currency_user_verified": currency.upper() if currency else "per_row",
                "start_month": start, "end_month": end,
                "date_column": date_column, "cost_column": amount_column,
                "dimensions": dims, "source_rows": count, "skipped_rows": skipped,
                "normalized_rows": len(entries), "missing_months": sorted(months - seen),
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "warning": "Report cost basis, fiscal calendar, allocations and Azure scope must be verified manually. Never add cost ledgers."}
    manifest_path = out.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Normalize a vetted TBM Studio CSV/TSV report for offline cost trends")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("audits/_shared/apptioone_normalized.csv"))
    ap.add_argument("--date-column", required=True)
    ap.add_argument("--cost-column", required=True)
    ap.add_argument("--currency")
    ap.add_argument("--currency-column")
    ap.add_argument("--dimension", action="append", required=True)
    ap.add_argument("--metric-name", required=True, help="Exact cost semantics established in the TBM report UI")
    ap.add_argument("--report-label", required=True)
    ap.add_argument("--start", default="2026-01")
    ap.add_argument("--end", default="2026-10")
    args = ap.parse_args(argv)
    try:
        manifest = convert(args.input, args.out, args.date_column, args.cost_column,
                           args.dimension, args.currency, args.currency_column,
                           args.metric_name, args.report_label, args.start, args.end)
        print(f"Normalized rows: {manifest['normalized_rows']} (skipped: {manifest['skipped_rows']})")
        print(f"Output: {args.out}")
        print("WARNING: TBM Studio fiscal/month mappings and allocation definitions must be validated with Finance.")
        return 0
    except (DataError, OSError, csv.Error, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
