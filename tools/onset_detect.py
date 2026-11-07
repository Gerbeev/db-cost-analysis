#!/usr/bin/env python3
"""Detect the onset of a persistent cost step-change in a daily series (rule R5).

Input: any CSV with a date and a cost column. Rows are summed per day, so a raw
Azure Actual Cost export can be used directly (optionally with --filter).

Rule R5 (AUDIT_GUIDE): baseline mean mu and stdev sigma over the baseline period;
threshold T = mu + max(k*sigma, rel*mu) (defaults k=2, rel=0.10); m(d) = trailing
7-day mean. Onset = first day after the baseline where m stays above T for
>= 14 consecutive calendar days. Shorter excursions are reported as spikes.

Example
  python onset_detect.py --csv azure_daily.csv --baseline 2026-01-01:2026-03-01
  python onset_detect.py --csv azure_actual.csv --filter "ServiceName=Azure Databricks" \
      --baseline 2026-01-01:2026-03-01 --out onset_daily.csv

Missing days are UNKNOWN: they are excluded from means and break a run (conservative).
Python 3.10+, standard library only. Read-only.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from period_delta import (  # noqa: E402  (shared parsing helpers)
    COST_ALIASES, CURRENCY_ALIASES, DATE_ALIASES, InputError, parse_cost, parse_date, parse_period, pick,
)


def load_daily(path: Path, args: argparse.Namespace) -> tuple[dict[date, float], str]:
    filters = []
    for item in args.filter or []:
        if "=" not in item:
            raise InputError(f"--filter must be COLUMN=VALUE, got '{item}'")
        col, val = item.split("=", 1)
        filters.append((col.strip(), val.strip()))
    daily: dict[date, float] = defaultdict(float)
    currencies = set()
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        if not headers:
            raise InputError("Empty CSV or missing header")
        date_col = pick(headers, args.date_col, DATE_ALIASES, True, "date")
        cost_col = pick(headers, args.cost_col, COST_ALIASES, True, "cost")
        cur_col = pick(headers, args.currency_col, CURRENCY_ALIASES, False, "currency")
        for col, _ in filters:
            if col not in headers:
                raise InputError(f"Column '{col}' not found")
        for row in reader:
            if any((row.get(c) or "").strip() != v for c, v in filters):
                continue
            cur = (row.get(cur_col) or "").strip().upper() if cur_col else "N/A"
            if args.currency and cur != args.currency.upper():
                continue
            currencies.add(cur)
            daily[parse_date(row[date_col])] += float(parse_cost(row[cost_col]))
    if len(currencies) > 1:
        raise InputError(f"Mixed currencies {sorted(currencies)} - rerun with --currency (rule R11)")
    if not daily:
        raise InputError("No rows after filters")
    return dict(daily), (currencies.pop() if currencies else "N/A")


def detect(daily: dict[date, float], base: tuple[date, date], window: int = 7, k: float = 2.0,
           rel: float = 0.10, min_run: int = 14) -> dict:
    base_vals = [v for d, v in daily.items() if base[0] <= d < base[1]]
    if len(base_vals) < 7:
        raise InputError(f"Baseline has {len(base_vals)} days with data; need >= 7 (R2 recommends >= 28)")
    mu = statistics.fmean(base_vals)
    sigma = statistics.stdev(base_vals) if len(base_vals) > 1 else 0.0
    threshold = mu + max(k * sigma, rel * mu)
    first, last = min(daily), max(daily)
    days = [first + timedelta(n) for n in range((last - first).days + 1)]
    missing = [d for d in days if d not in daily]
    series = []
    for d in days:
        win = [daily[x] for x in (d - timedelta(i) for i in range(window)) if x in daily]
        ma = statistics.fmean(win) if win and d in daily else None
        series.append({"date": d, "cost": daily.get(d), "ma": ma,
                       "above": ma is not None and ma > threshold})
    runs, start = [], None
    for i, row in enumerate(series):
        if row["above"] and start is None:
            start = i
        if (not row["above"] or i == len(series) - 1) and start is not None:
            end = i if row["above"] else i - 1
            runs.append((series[start]["date"], series[end]["date"], end - start + 1))
            start = None
    steps = [r for r in runs if r[2] >= min_run and r[0] >= base[1]]
    spikes = [r for r in runs if r[2] < min_run]
    onset = steps[0][0] if steps else None
    post = [daily[d] for d in days if onset and d >= onset and d in daily]
    return {"mu": mu, "sigma": sigma, "threshold": threshold, "baseline_days": len(base_vals),
            "series": series, "steps": steps, "spikes": spikes, "onset": onset, "missing": missing,
            "post_mean": statistics.fmean(post) if post else None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--date-col", help="Date column (auto-detected if omitted)")
    ap.add_argument("--cost-col", help="Cost column (auto-detected if omitted)")
    ap.add_argument("--currency-col", help="Currency column (auto-detected if omitted)")
    ap.add_argument("--currency", help="Keep only this currency")
    ap.add_argument("--filter", action="append", help="COLUMN=VALUE exact match; repeatable")
    ap.add_argument("--baseline", required=True, help="Baseline YYYY-MM-DD:YYYY-MM-DD (end exclusive)")
    ap.add_argument("--window", type=int, default=7, help="Trailing mean window in days (default 7)")
    ap.add_argument("--sigma", type=float, default=2.0, help="k in mu + k*sigma (default 2)")
    ap.add_argument("--min-rel", type=float, default=0.10, help="Minimum relative uplift (default 0.10)")
    ap.add_argument("--min-run", type=int, default=14, help="Consecutive days for a step (default 14)")
    ap.add_argument("--out", type=Path, help="Write daily series with flags to CSV")
    args = ap.parse_args(argv)
    try:
        if not args.csv.is_file():
            raise InputError(f"File not found: {args.csv}")
        daily, currency = load_daily(args.csv, args)
        base = parse_period(args.baseline)
        r = detect(daily, base, args.window, args.sigma, args.min_rel, args.min_run)
        print(f"Currency {currency} | baseline {args.baseline}: {r['baseline_days']} days, "
              f"mean {r['mu']:.2f}/day, stdev {r['sigma']:.2f}")
        print(f"Threshold T = {r['threshold']:.2f}/day")
        if r["missing"]:
            print(f"WARNING: {len(r['missing'])} calendar days without data (UNKNOWN), first {r['missing'][0]}",
                  file=sys.stderr)
        if r["onset"]:
            uplift = r["post_mean"] - r["mu"]
            print(f"ONSET: {r['onset']}  (post-onset mean {r['post_mean']:.2f}/day, "
                  f"+{uplift:.2f}/day, +{uplift / r['mu'] * 100:.1f}% vs baseline)")
        else:
            print("ONSET: none - no excursion above T lasting >= "
                  f"{args.min_run} days after the baseline")
        for s in r["steps"]:
            print(f"  STEP  {s[0]} -> {s[1]}  ({s[2]} days)")
        for s in r["spikes"]:
            print(f"  SPIKE {s[0]} -> {s[1]}  ({s[2]} days)")
        if args.out:
            with args.out.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["date", "cost", f"ma{args.window}", "threshold", "above_threshold", "onset"])
                for row in r["series"]:
                    w.writerow([row["date"].isoformat(),
                                "" if row["cost"] is None else f"{row['cost']:.2f}",
                                "" if row["ma"] is None else f"{row['ma']:.2f}",
                                f"{r['threshold']:.2f}", int(row["above"]),
                                "ONSET" if row["date"] == r["onset"] else ""])
            print(f"Written: {args.out}")
        return 0
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
