#!/usr/bin/env python3
"""Rank cost deltas between a baseline and a comparison period (per-day normalized).

Works on any cost CSV with a date column and a cost column, e.g. an Azure Actual
Cost export, a Cost Analysis download or a Databricks SQL result.

Examples
  python period_delta.py --csv azure_actual.csv --monthly
  python period_delta.py --csv azure_actual.csv --base 2026-02-01:2026-03-01 \
      --cmp 2026-04-01:2026-05-01 --group ServiceName,MeterName --top 25 --out deltas.csv
  python period_delta.py --csv azure_actual.csv --filter "ServiceName=Azure Databricks" ...

Rules implemented (AUDIT_GUIDE): per-day rates (R2), materiality flag (R3),
cumulative coverage (R4), one currency per series (R11). Period ends are exclusive.
Python 3.10+, standard library only. Read-only: never modifies the input file.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATE_ALIASES = ("Date", "UsageDate", "usage_date", "BillingPeriodStartDate", "ChargePeriodStart", "day", "date")
COST_ALIASES = ("CostInBillingCurrency", "Cost", "PreTaxCost", "BilledCost", "cost", "estimated_list_cost",
                "daily_list_cost", "list_cost")
CURRENCY_ALIASES = ("BillingCurrencyCode", "BillingCurrency", "Currency", "currency_code")
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S",
                "%d.%m.%Y", "%Y%m%d")
ZERO = Decimal("0")


class InputError(Exception):
    """Invalid input; reported without a traceback."""


def pick(headers: list[str], explicit: str | None, aliases: tuple[str, ...], required: bool, label: str) -> str | None:
    if explicit:
        if explicit not in headers:
            raise InputError(f"Column '{explicit}' not found. Available: {', '.join(headers)}")
        return explicit
    lower = {h.strip().lower(): h for h in headers}
    for alias in aliases:
        if alias.strip().lower() in lower:
            return lower[alias.strip().lower()]
    if required:
        raise InputError(f"No {label} column found (tried {', '.join(aliases)}). Use --{label}-col.")
    return None


def parse_date(raw: str) -> date:
    value = (raw or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    if len(value) >= 10:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            pass
    raise InputError(f"Unrecognized date '{raw}'")


def parse_cost(raw: str) -> Decimal:
    value = (raw or "").strip().replace(",", "")
    if value == "":
        return ZERO
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise InputError(f"Invalid cost value '{raw}'") from exc


def parse_period(text: str) -> tuple[date, date]:
    try:
        start, end = text.split(":")
        s, e = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        raise InputError(f"Period must be YYYY-MM-DD:YYYY-MM-DD (end exclusive), got '{text}'") from exc
    if e <= s:
        raise InputError(f"Period end must be after start: '{text}'")
    return s, e


def safe_cell(value: object) -> str:
    """Neutralize spreadsheet formulas in text cells; keep plain numbers numeric."""
    text = "" if value is None else str(value)
    stripped = text.lstrip(" \t\r\n")
    if stripped[:1] in ("=", "+", "-", "@"):
        try:
            Decimal(stripped)
            return text
        except InvalidOperation:
            return "'" + text
    return text


def load(path: Path, args: argparse.Namespace):
    filters = []
    for item in args.filter or []:
        if "=" not in item:
            raise InputError(f"--filter must be COLUMN=VALUE, got '{item}'")
        col, val = item.split("=", 1)
        filters.append((col.strip(), val.strip()))
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        if not headers:
            raise InputError("Empty CSV or missing header")
        date_col = pick(headers, args.date_col, DATE_ALIASES, True, "date")
        cost_col = pick(headers, args.cost_col, COST_ALIASES, True, "cost")
        cur_col = pick(headers, args.currency_col, CURRENCY_ALIASES, False, "currency")
        groups = [g.strip() for g in (args.group or "").split(",") if g.strip()]
        for col in groups + [f[0] for f in filters]:
            if col not in headers:
                raise InputError(f"Column '{col}' not found. Available: {', '.join(headers)}")
        rows = []
        for row in reader:
            if any((row.get(c) or "").strip() != v for c, v in filters):
                continue
            currency = (row.get(cur_col) or "").strip().upper() if cur_col else "N/A"
            if args.currency and currency != args.currency.upper():
                continue
            key = tuple((row.get(g) or "").strip() or "(blank)" for g in groups)
            rows.append((parse_date(row[date_col]), currency, key, parse_cost(row[cost_col])))
    currencies = {r[1] for r in rows}
    if len(currencies) > 1:
        raise InputError(f"Mixed currencies {sorted(currencies)} - rerun with --currency (rule R11)")
    return rows, groups, (currencies.pop() if currencies else "N/A")


def monthly(rows) -> list[list[str]]:
    totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    days: dict[str, set[date]] = defaultdict(set)
    for d, _, _, cost in rows:
        m = d.strftime("%Y-%m")
        totals[m] += cost
        days[m].add(d)
    out = []
    prev_rate = None
    for m in sorted(totals):
        y, mo = map(int, m.split("-"))
        nxt = date(y + (mo == 12), mo % 12 + 1, 1)
        cal_days = (nxt - date(y, mo, 1)).days
        rate = totals[m] / cal_days
        delta = "" if prev_rate is None else f"{rate - prev_rate:.2f}"
        pct = "" if prev_rate in (None, ZERO) else f"{(rate - prev_rate) / prev_rate * 100:.1f}"
        out.append([m, str(cal_days), str(len(days[m])), f"{totals[m]:.2f}", f"{rate:.2f}", delta, pct])
        prev_rate = rate
    return out


def deltas(rows, base: tuple[date, date], cmp: tuple[date, date]):
    days_b = (base[1] - base[0]).days
    days_c = (cmp[1] - cmp[0]).days
    cb: dict[tuple, Decimal] = defaultdict(lambda: ZERO)
    cc: dict[tuple, Decimal] = defaultdict(lambda: ZERO)
    seen_b, seen_c = set(), set()
    for d, _, key, cost in rows:
        if base[0] <= d < base[1]:
            cb[key] += cost
            seen_b.add(d)
        elif cmp[0] <= d < cmp[1]:
            cc[key] += cost
            seen_c.add(d)
    warnings = []
    if len(seen_b) < days_b:
        warnings.append(f"Baseline has data on {len(seen_b)} of {days_b} days - missing days are UNKNOWN, not zero")
    if len(seen_c) < days_c:
        warnings.append(f"Comparison has data on {len(seen_c)} of {days_c} days - missing days are UNKNOWN, not zero")
    result = []
    for key in set(cb) | set(cc):
        rb, rc = cb[key] / days_b, cc[key] / days_c
        result.append([key, cb[key], cc[key], rb, rc, rc - rb])
    total_delta = sum((r[5] for r in result), ZERO)
    total_rb = sum((r[3] for r in result), ZERO)
    total_rc = sum((r[4] for r in result), ZERO)
    result.sort(key=lambda r: r[5], reverse=True)
    positives = [r for r in result if r[5] > 0]
    top10 = {id(r) for r in positives[:10]}
    running = ZERO
    rows_out = []
    for i, (key, sb, sc, rb, rc, dr) in enumerate(result, 1):
        running += dr
        if rb == 0 and rc > 0:
            cls = "NEW"
        elif rc == 0 and rb > 0:
            cls = "GONE"
        elif abs(dr) < abs(rb) * Decimal("0.01"):
            cls = "FLAT"
        else:
            cls = "GROWN" if dr > 0 else "SHRUNK"
        share = dr / total_delta if total_delta else None
        material = (total_delta != 0 and abs(dr) >= abs(total_delta) * Decimal("0.05")) or id(result[i - 1]) in top10
        rows_out.append({
            "rank": i, "key": key, "cost_b": sb, "cost_c": sc, "per_day_b": rb, "per_day_c": rc,
            "delta_per_day": dr, "share": share, "cumulative": (running / total_delta) if total_delta else None,
            "change_class": cls, "material": material,
        })
    return rows_out, total_rb, total_rc, total_delta, days_b, days_c, warnings


def fmt(v: Decimal | None, places: int = 2) -> str:
    return "" if v is None else f"{v:.{places}f}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", required=True, type=Path, help="Input cost CSV")
    ap.add_argument("--date-col", help="Date column (auto-detected if omitted)")
    ap.add_argument("--cost-col", help="Cost column (auto-detected if omitted)")
    ap.add_argument("--currency-col", help="Currency column (auto-detected if omitted)")
    ap.add_argument("--currency", help="Keep only this currency (required if the file mixes currencies)")
    ap.add_argument("--filter", action="append", help="COLUMN=VALUE, exact match; repeatable")
    ap.add_argument("--group", help="Comma-separated grouping columns, e.g. ServiceName,MeterName")
    ap.add_argument("--base", help="Baseline period YYYY-MM-DD:YYYY-MM-DD (end exclusive)")
    ap.add_argument("--cmp", help="Comparison period YYYY-MM-DD:YYYY-MM-DD (end exclusive)")
    ap.add_argument("--monthly", action="store_true", help="Print monthly totals and per-day rates")
    ap.add_argument("--top", type=int, default=20, help="Rows to print (default 20)")
    ap.add_argument("--out", type=Path, help="Write full ranked result to this CSV")
    args = ap.parse_args(argv)
    try:
        if not args.csv.is_file():
            raise InputError(f"File not found: {args.csv}")
        rows, groups, currency = load(args.csv, args)
        if not rows:
            raise InputError("No rows after filters")
        if args.monthly:
            print(f"Monthly series ({currency}) - per-day rate = total / calendar days")
            header = ["month", "calendar_days", "days_with_data", "total", "per_day", "delta_per_day_vs_prev", "delta_pct"]
            print("\t".join(header))
            for r in monthly(rows):
                print("\t".join(r))
            if args.out and not (args.base and args.cmp):
                with args.out.open("w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    w.writerow(header)
                    w.writerows(monthly(rows))
        if args.base or args.cmp:
            if not (args.base and args.cmp):
                raise InputError("Both --base and --cmp are required")
            base, cmp = parse_period(args.base), parse_period(args.cmp)
            out, rb, rc, dt, db, dc, warnings = deltas(rows, base, cmp)
            for w in warnings:
                print(f"WARNING: {w}", file=sys.stderr)
            pct = f"{dt / rb * 100:.1f}%" if rb else "n/a"
            print(f"\nCurrency {currency} | B {args.base} ({db} d) | C {args.cmp} ({dc} d)")
            print(f"Per day: B {rb:.2f} -> C {rc:.2f} | delta {dt:+.2f}/day ({pct}) | annualized {dt * 365:+.0f}")
            label = ",".join(groups) if groups else "(total)"
            print(f"\nTop {args.top} by delta per day - grouping: {label}")
            print("rank\tdelta/day\tshare\tcum\tclass\tmaterial\tkey")
            for r in out[: args.top]:
                print(f"{r['rank']}\t{r['delta_per_day']:+.2f}\t{fmt(r['share'], 3)}\t{fmt(r['cumulative'], 3)}\t"
                      f"{r['change_class']}\t{'Y' if r['material'] else ''}\t{' | '.join(r['key'])}")
            reached = next((r["rank"] for r in out if r["cumulative"] is not None and r["cumulative"] >= Decimal("0.9")), None)
            print(f"\nRows needed for >= 90% of net delta (R4): {reached if reached else 'not reached'}")
            if args.out:
                with args.out.open("w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    w.writerow(["rank", *(groups or ["key"]), "currency", "cost_b", "cost_c", "per_day_b", "per_day_c",
                                "delta_per_day", "share_of_total", "cumulative_share", "change_class", "material"])
                    for r in out:
                        key_cells = [safe_cell(k) for k in r["key"]] or ["(total)"]
                        w.writerow([r["rank"], *key_cells, currency,
                                    fmt(r["cost_b"]), fmt(r["cost_c"]), fmt(r["per_day_b"], 4), fmt(r["per_day_c"], 4),
                                    fmt(r["delta_per_day"], 4), fmt(r["share"], 4), fmt(r["cumulative"], 4),
                                    r["change_class"], "Y" if r["material"] else ""])
                print(f"Written: {args.out}")
        if not args.monthly and not (args.base or args.cmp):
            raise InputError("Nothing to do: use --monthly and/or --base/--cmp")
        return 0
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
