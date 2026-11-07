#!/usr/bin/env python3
"""Check an audit workspace step by step and write STATUS.md.

    python tools/check_audit.py 2026-04-dbx-growth
    (the web interface runs this evaluation after every change)

For every step folder (00_ ... 09_) it verifies:
  1. CHECKS.md  - every line is resolved: [x] done, [-] not applicable, [!] done with limitation.
                  [-] and [!] must carry a reason after " | ". Gate lines (ID starting with G)
                  must be [x].
  2. Required outputs - every path pattern listed under "## Required outputs" exists
                  (patterns are relative to the audit root; lines marked "(optional)" are skipped).
  3. Automatic checks - data checks on the saved files (currency, month gaps, price-join
                  verdicts, delta-bridge identity, hypothesis/evidence consistency).
  4. Derived checks - a check that only restates a fact proven by the files (evidence rows exist, an output file exists,
                  an automatic check passed) counts as done without a manual tick; see derive().
A step is PASSED only when all three hold. Steps after the first non-passed step are shown
as LOCKED (still evaluated). Exit code: 0 = all passed, 1 = open items, 2 = usage error.
Python 3.10+, stdlib only. Read-only except STATUS.md.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from period_delta import COST_ALIASES, CURRENCY_ALIASES, DATE_ALIASES, InputError, parse_date, pick  # noqa: E402

CHECK_RE = re.compile(r"^- \[( |x|X|-|!)\] (\S+)\s+(.*)$")
OUTPUT_RE = re.compile(r"^- `([^`]+)`(.*)$")
PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
# Categories that make up the bridge identity TOTAL = sum(lines). BUCKET and DRIVER_CANDIDATE are informational.
BRIDGE_CATEGORIES = ("ACCOUNTING", "ROOT_CAUSE", "SHARED_UNALLOCATED", "OUT_OF_SCOPE", "UNEXPLAINED")


# ---------------------------------------------------------------- helpers
def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def num(value: str | None) -> float | None:
    try:
        return float((value or "").replace(",", "").strip())
    except ValueError:
        return None


def latest(audit: Path, pattern: str) -> Path | None:
    hits = sorted(Path(p) for p in glob.glob(str(audit / pattern)))
    return hits[-1] if hits else None


# ---------------------------------------------------------------- automatic checks
def auto_01(audit: Path) -> list[tuple[str, str]]:
    out = []
    exports = sorted(Path(p) for p in glob.glob(str(audit / "01_data_quality/exports/azure_actual*.csv")))
    for exp in exports:
        try:
            with exp.open(newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                headers = reader.fieldnames or []
                dcol = pick(headers, None, DATE_ALIASES, True, "date")
                pick(headers, None, COST_ALIASES, True, "cost")
                ccol = pick(headers, None, CURRENCY_ALIASES, False, "currency")
                months, currencies, hashes, rows = set(), Counter(), Counter(), 0
                for row in reader:
                    rows += 1
                    months.add(parse_date(row[dcol]).strftime("%Y-%m"))
                    if ccol:
                        currencies[(row[ccol] or "").strip().upper()] += 1
                    hashes[hashlib.md5("\x1f".join(str(v) for v in row.values()).encode()).hexdigest()] += 1
        except (InputError, KeyError, ValueError) as exc:
            out.append((FAIL, f"{exp.name}: unreadable ({exc})"))
            continue
        out.append((FAIL if len(currencies) > 1 else PASS,
                    f"{exp.name}: currencies {sorted(currencies) or ['n/a']} (STOP-2)"))
        ms = sorted(months)
        if ms:
            y0, m0 = map(int, ms[0].split("-"))
            y1, m1 = map(int, ms[-1].split("-"))
            expected = {f"{y:04d}-{m:02d}" for y in range(y0, y1 + 1) for m in range(1, 13)
                        if (y, m) >= (y0, m0) and (y, m) <= (y1, m1)}
            gaps = sorted(expected - months)
            out.append((FAIL if gaps else PASS, f"{exp.name}: months {ms[0]}..{ms[-1]}, gaps {gaps or 'none'} (STOP-3)"))
        dups = sum(c - 1 for c in hashes.values() if c > 1)
        out.append((WARN if dups else PASS,
                    f"{exp.name}: {rows} rows, {dups} exact duplicate rows (verify not an overlapping export, STOP-1)"))
    pj = latest(audit, "01_data_quality/results/1.3_price_join_check*.csv")
    if pj:
        rows = read_csv(pj)
        failing = [f"{r.get('sku_name')}:{r.get('verdict')}" for r in rows if (r.get("verdict") or "").startswith("FAIL")]
        out.append((WARN if failing else PASS,
                    f"{pj.name}: {len(failing)} SKU(s) fail R7 - must be excluded from modeled cost "
                    f"{failing[:5]}{' ...' if len(failing) > 5 else ''}"))
    return out


def bridge(audit: Path) -> list[dict[str, str]]:
    path = audit / "delta_bridge.csv"
    return read_csv(path) if path.is_file() else []


def auto_02(audit: Path) -> list[tuple[str, str]]:
    total = next((r for r in bridge(audit) if r.get("line_id") == "TOTAL"), None)
    if total is None or num(total.get("delta_per_day")) is None:
        return [(FAIL, "delta_bridge.csv: TOTAL row has no numeric delta_per_day")]
    return [(PASS, f"delta_bridge.csv: TOTAL delta_per_day = {num(total['delta_per_day']):.2f} {total.get('currency', '')}")]


def auto_04(audit: Path) -> list[tuple[str, str]]:
    files = sorted(Path(p) for p in glob.glob(str(audit / "04_azure_decomposition/results/delta_by_*.csv")))
    sums = {}
    for f in files:
        rows = read_csv(f)
        if rows and "delta_per_day" in rows[0]:
            sums[f.name] = sum(num(r["delta_per_day"]) or 0.0 for r in rows)
    if len(sums) < 2:
        return [(WARN, "fewer than 2 delta_by_*.csv files - grouping consistency not checked")]
    ref = next(iter(sums.values()))
    bad = {k: v for k, v in sums.items() if abs(v - ref) > max(0.005 * abs(ref), 0.01)}
    detail = ", ".join(f"{k}={v:.2f}" for k, v in sums.items())
    return [(FAIL if bad else PASS, f"groupings of the same ledger must total the same delta/day: {detail}")]


def auto_05(audit: Path) -> list[tuple[str, str]]:
    f = latest(audit, "05_databricks_decomposition/results/5.3_object_delta*.csv")
    if not f:
        return []
    rows = read_csv(f)
    hit = next((r for r in rows if (num(r.get("cumulative_share")) or 0) >= 0.9), None)
    if hit:
        return [(PASS, f"{f.name}: {hit.get('rank_by_delta')} objects reach >= 90% of modeled delta (R4)")]
    return [(WARN, f"{f.name}: 90% coverage not reached in exported rows - export more rows or quantify remainder")]


def hypotheses(audit: Path) -> dict[str, dict[str, str]]:
    path = audit / "hypothesis_register.csv"
    return {r["hypothesis_id"]: r for r in read_csv(path)} if path.is_file() else {}


def auto_06(audit: Path) -> list[tuple[str, str]]:
    out = []
    hyp = hypotheses(audit)
    rc = [r for r in bridge(audit) if r.get("category") == "ROOT_CAUSE" and num(r.get("delta_per_day")) is not None]
    if not rc:
        return [(FAIL, "delta_bridge.csv: no ROOT_CAUSE line with numeric delta_per_day")]
    for r in rc:
        status = (r.get("status") or "").strip()
        out.append((PASS if status in ("CONFIRMED", "LIKELY", "REJECTED", "UNKNOWN") else FAIL,
                    f"bridge {r['line_id']}: status {status or '(blank)'}"))
        for hid in filter(None, (h.strip() for h in (r.get("hypothesis_id") or "").replace(";", ",").split(","))):
            hs = hyp.get(hid, {}).get("status", "MISSING")
            out.append((FAIL if hs in ("HYPOTHESIS", "MISSING") else PASS,
                        f"bridge {r['line_id']} -> {hid}: register status {hs}"))
    return out


def auto_07(audit: Path) -> list[tuple[str, str]]:
    rows = bridge(audit)
    total = next((num(r.get("delta_per_day")) for r in rows if r.get("line_id") == "TOTAL"), None)
    if total is None:
        return [(FAIL, "delta_bridge.csv: TOTAL missing")]
    parts = [r for r in rows if r.get("category") in BRIDGE_CATEGORIES]
    s = sum(num(r.get("delta_per_day")) or 0.0 for r in parts)
    unx = next((num(r.get("delta_per_day")) for r in rows if r.get("line_id") == "UNX"), None)
    out = [(PASS if abs(s - total) <= max(0.01 * abs(total), 0.01) else FAIL,
            f"bridge identity: sum of lines {s:.2f} vs TOTAL {total:.2f} (tolerance 1%)")]
    if unx is None:
        out.append((FAIL, "UNX (UNEXPLAINED) line has no numeric delta_per_day"))
    elif total:
        share = abs(unx) / abs(total)
        out.append((PASS if share <= 0.10 else FAIL, f"UNEXPLAINED = {share:.1%} of TOTAL (R4: <= 10% or accepted in CHECKS)"))
    return out


def auto_08(audit: Path) -> list[tuple[str, str]]:
    ev_path = audit / "evidence_register.csv"
    ev = {r["evidence_id"] for r in read_csv(ev_path) if r.get("evidence_id") and "YYYYMMDD" not in r["evidence_id"]} \
        if ev_path.is_file() else set()
    out = [(PASS if ev else FAIL, f"evidence_register.csv: {len(ev)} evidence rows")]
    for hid, r in hypotheses(audit).items():
        if r.get("status") == "CONFIRMED":
            ids = [e.strip() for e in (r.get("evidence_ids") or "").replace(";", ",").split(",") if e.strip()]
            missing = [e for e in ids if e not in ev]
            out.append((FAIL if not ids or missing else PASS,
                        f"{hid} CONFIRMED: evidence {ids or 'none'}{' missing ' + str(missing) if missing else ''}"))
    return out


def auto_09(audit: Path) -> list[tuple[str, str]]:
    f = audit / "09_report_and_controls/findings_report.md"
    if not f.is_file():
        return []
    blanks = f.read_text(encoding="utf-8").count("____")
    return [(WARN if blanks else PASS, f"findings_report.md: {blanks} unfilled '____' placeholders")]


# ---------------------------------------------------------------- derived checks
# A check that only restates a fact visible in the audit files is satisfied without a manual tick (the file is
# the proof). It applies only to an OPEN line: [x], [-] and [!] set by the auditor are never overridden.
def settings_of(audit: Path) -> dict[str, str]:
    f = audit / "audit.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    except ValueError:
        return {}


def evidence_ids(audit: Path) -> list[str]:
    path = audit / "evidence_register.csv"
    if not path.is_file():
        return []
    return [r["evidence_id"] for r in read_csv(path) if r.get("evidence_id") and "YYYYMMDD" not in r["evidence_id"]]


def has_output(audit: Path, pattern: str) -> bool:
    return bool(glob.glob(str(audit / pattern)))


def passed_marker(auto: list[tuple[str, str]], marker: str) -> bool:
    hits = [a for a in auto if marker in a[1]]
    return bool(hits) and all(a[0] == PASS for a in hits)


def no_fail(auto: list[tuple[str, str]]) -> bool:
    return bool(auto) and not any(a[0] == FAIL for a in auto)


def derive(audit: Path, nn: str, auto: list[tuple[str, str]]) -> set[str]:
    """IDs of checks proven by the files of the audit (see the comment above)."""
    out: set[str] = set()
    ev = [e for e in evidence_ids(audit) if e.startswith(f"EVD-{nn}-")]
    if ev and nn != "00":
        out.add({"01": "C1.11", "02": "C2.9", "03": "C3.15", "04": "C4.11", "05": "C5.10", "06": "C6.10",
                 "07": "C7.7"}.get(nn, ""))
    total = next((r for r in bridge(audit) if r.get("line_id") == "TOTAL"), None)
    total_ok = total is not None and num(total.get("delta_per_day")) is not None
    if nn == "00":
        s = settings_of(audit)
        if all(s.get(k) for k in ("window_start", "window_end", "b_start", "b_end", "c_start", "c_end")):
            out |= {"C0.5", "C0.6"}
    elif nn == "01":
        if passed_marker(auto, "(STOP-2)"):
            out.add("C1.3")
        if passed_marker(auto, "(STOP-3)"):
            out.add("C1.4")
    elif nn == "02":
        if has_output(audit, "02_confirm_and_size/results/monthly_series*.csv"):
            out.add("C2.1")
        if total_ok:
            out |= {"C2.6", "C2.8"}
    elif nn == "04":
        for cid, pat in (("C4.1", "subscription"), ("C4.2", "service"), ("C4.3", "meter"), ("C4.4", "resource_group"),
                         ("C4.5", "resource")):
            if has_output(audit, f"04_azure_decomposition/results/delta_by_{pat}__*.csv"):
                out.add(cid)
        if has_output(audit, "04_azure_decomposition/results/workspace_rg_map*"):
            out.add("C4.9")
        if passed_marker(auto, "groupings of the same ledger"):
            out.add("C4.6")
    elif nn == "05":
        if passed_marker(auto, "(R4)"):
            out.add("C5.4")
    elif nn == "06":
        if has_output(audit, "06_root_cause/driver_*.md"):
            out.add("C6.2")
        if has_output(audit, "06_root_cause/results/*.csv"):
            out.add("C6.3")
        if no_fail(auto):
            out.add("C6.8")
    elif nn == "07":
        if passed_marker(auto, "bridge identity"):
            out.add("C7.5")
        if passed_marker(auto, "UNEXPLAINED ="):
            out.add("C7.6")
    elif nn == "08":
        if no_fail(auto):
            out.add("C8.3")
    elif nn == "09":
        if passed_marker(auto, "unfilled"):
            out.add("C9.7")
    out.discard("")
    return out


def derived_ids(audit: Path, step: Path) -> set[str]:
    nn = step.name[:2]
    return derive(audit, nn, AUTO.get(nn, lambda _a: [])(audit))


AUTO = {"01": auto_01, "02": auto_02, "04": auto_04, "05": auto_05, "06": auto_06, "07": auto_07,
        "08": auto_08, "09": auto_09}


# ---------------------------------------------------------------- step evaluation
def evaluate(audit: Path, step: Path) -> dict:
    checks, outputs, section = [], [], None
    text = (step / "CHECKS.md").read_text(encoding="utf-8") if (step / "CHECKS.md").is_file() else ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        m = CHECK_RE.match(line)
        if m and section != "required outputs":
            state, cid, body = m.group(1).lower(), m.group(2), m.group(3)
            problem = None
            if state == " ":
                problem = "open"
            elif state in "-!" and " | " not in body:
                problem = "reason missing after ' | '"
            elif cid.startswith("G") and state != "x":
                problem = "gate must be [x]"
            checks.append((cid, state, problem))
            continue
        o = OUTPUT_RE.match(line)
        if o and section == "required outputs":
            optional = "(optional)" in o.group(2)
            found = bool(glob.glob(str(audit / o.group(1))))
            outputs.append((o.group(1), optional, found))
    auto = AUTO.get(step.name[:2], lambda _a: [])(audit)
    proven = derive(audit, step.name[:2], auto)
    checks = [(cid, "x", None) if state == " " and cid in proven else (cid, state, problem)
              for cid, state, problem in checks]
    open_checks = [c for c in checks if c[2]]
    missing = [o for o in outputs if not o[1] and not o[2]]
    fails = [a for a in auto if a[0] == FAIL]
    gate = any(c[0].startswith("G") for c in checks)
    passed = bool(checks) and gate and not open_checks and not missing and not fails
    return {"name": step.name, "checks": checks, "open": open_checks, "outputs": outputs, "missing": missing,
            "auto": auto, "fails": fails, "passed": passed,
            "derived": sorted(proven)}


def render(audit: Path, results: list[dict]) -> str:
    lines = [f"# Audit status - {audit.name}", "", f"Checked {datetime.now():%Y-%m-%d %H:%M}. "
             "Regenerated by the web interface after every change.", "",
             "| Step | Status | Checks done | Outputs | Auto checks |", "|---|---|---|---|---|"]
    blocked = False
    for r in results:
        status = "PASSED" if r["passed"] else ("LOCKED" if blocked else "IN PROGRESS")
        if not r["passed"]:
            blocked = True
        done = len(r["checks"]) - len(r["open"])
        req = [o for o in r["outputs"] if not o[1]]
        auto = "-" if not r["auto"] else (f"{len(r['fails'])} FAIL" if r["fails"] else
                                         ("WARN" if any(a[0] == WARN for a in r["auto"]) else "PASS"))
        lines.append(f"| `{r['name']}` | **{status}** | {done}/{len(r['checks'])} | "
                     f"{len(req) - len(r['missing'])}/{len(req)} | {auto} |")
    current = next((r for r in results if not r["passed"]), None)
    lines += ["", f"**Current step:** `{current['name']}`" if current else "**All steps passed.**", ""]
    for r in results:
        if r["passed"] and not any(a[0] == WARN for a in r["auto"]):
            continue
        lines.append(f"## {r['name']}")
        for cid, state, problem in r["open"]:
            lines.append(f"- [ ] {cid}: {problem}")
        for pattern, _, _ in r["missing"]:
            lines.append(f"- missing output: `{pattern}`")
        for level, msg in r["auto"]:
            if level != PASS:
                lines.append(f"- {level}: {msg}")
        lines.append("")
    lines += ["## Automatic check details", ""]
    for r in results:
        for level, msg in r["auto"]:
            lines.append(f"- `{r['name']}` {level}: {msg}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audit", help="Audit id (folder under audits/) or path")
    ap.add_argument("--no-write", action="store_true", help="Print only; do not write STATUS.md")
    args = ap.parse_args(argv)
    audit = Path(args.audit)
    if not audit.is_dir():
        audit = ROOT / "audits" / args.audit
    if not audit.is_dir():
        print(f"ERROR: audit not found: {args.audit}", file=sys.stderr)
        return 2
    steps = sorted(p for p in audit.iterdir() if p.is_dir() and re.match(r"^\d\d_", p.name))
    results = [evaluate(audit, s) for s in steps]
    report = render(audit, results)
    print(report)
    if not args.no_write:
        (audit / "STATUS.md").write_text(report, encoding="utf-8")
    return 0 if results and all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
