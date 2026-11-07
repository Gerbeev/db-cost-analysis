"""Synthetic tests for period_delta.py and onset_detect.py.  Run: python -m unittest tools/test_tools.py"""
from __future__ import annotations

import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import onset_detect  # noqa: E402
import period_delta  # noqa: E402


def write_csv(path: Path, header: list[str], rows: list[list]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def synthetic_rows(step_day: date, currency: str = "EUR", date_fmt: str = "%Y-%m-%d") -> list[list]:
    """VM flat 100/day, DBU 50/day stepping to 150/day at step_day, new SQL item 20/day from step_day."""
    rows, d = [], date(2026, 1, 1)
    while d < date(2026, 6, 1):
        ds = d.strftime(date_fmt)
        rows.append([ds, "100", currency, "Virtual Machines", "D8s v5"])
        rows.append([ds, "150" if d >= step_day else "50", currency, "Azure Databricks", "Jobs Compute DBU"])
        if d >= step_day:
            rows.append([ds, "20", currency, "Azure Databricks", "Serverless SQL DBU"])
        d += timedelta(1)
    return rows


HEADER = ["Date", "CostInBillingCurrency", "BillingCurrencyCode", "ServiceName", "MeterName"]


class PeriodDeltaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.csv = write_csv(self.tmp / "a.csv", HEADER, synthetic_rows(date(2026, 3, 20)))

    def run_cli(self, *args) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = period_delta.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_identity_and_classes(self):
        rows, _, _ = period_delta.load(self.csv, period_delta.argparse.Namespace(
            filter=None, date_col=None, cost_col=None, currency_col=None, currency=None, group="ServiceName,MeterName"))
        out, rb, rc, dt, *_ = period_delta.deltas(rows, (date(2026, 2, 1), date(2026, 3, 1)),
                                                  (date(2026, 4, 1), date(2026, 5, 1)))
        self.assertEqual(rb, Decimal(150))
        self.assertEqual(rc, Decimal(270))
        self.assertEqual(dt, sum(r["delta_per_day"] for r in out))
        by_meter = {r["key"][1]: r for r in out}
        self.assertEqual(by_meter["Jobs Compute DBU"]["change_class"], "GROWN")
        self.assertEqual(by_meter["Serverless SQL DBU"]["change_class"], "NEW")
        self.assertEqual(by_meter["D8s v5"]["change_class"], "FLAT")
        self.assertTrue(by_meter["Jobs Compute DBU"]["material"])

    def test_month_length_normalization(self):
        code, out, _ = self.run_cli("--csv", str(self.csv), "--monthly")
        self.assertEqual(code, 0)
        lines = {l.split("\t")[0]: l.split("\t") for l in out.splitlines() if l.startswith("2026-")}
        self.assertEqual(lines["2026-02"][4], "150.00")   # Feb 28 days, flat per day
        self.assertEqual(lines["2026-01"][4], "150.00")

    def test_mixed_currency_rejected(self):
        rows = synthetic_rows(date(2026, 3, 20)) + [["2026-02-01", "5", "USD", "Storage", "Hot LRS"]]
        path = write_csv(self.tmp / "mixed.csv", HEADER, rows)
        code, _, err = self.run_cli("--csv", str(path), "--monthly")
        self.assertEqual(code, 2)
        self.assertIn("Mixed currencies", err)

    def test_us_date_format_and_output(self):
        path = write_csv(self.tmp / "us.csv", HEADER, synthetic_rows(date(2026, 3, 20), date_fmt="%m/%d/%Y"))
        out_csv = self.tmp / "d.csv"
        code, out, _ = self.run_cli("--csv", str(path), "--base", "2026-02-01:2026-03-01",
                                    "--cmp", "2026-04-01:2026-05-01", "--group", "MeterName", "--out", str(out_csv))
        self.assertEqual(code, 0)
        self.assertIn("+120.00/day", out)
        with out_csv.open(encoding="utf-8") as fh:
            first = next(csv.DictReader(fh))
        self.assertEqual(first["MeterName"], "Jobs Compute DBU")

    def test_formula_cells_neutralized(self):
        self.assertEqual(period_delta.safe_cell("=1+1"), "'=1+1")
        self.assertEqual(period_delta.safe_cell("-12.5"), "-12.5")


class OnsetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_step_detected_near_true_onset(self):
        path = write_csv(self.tmp / "s.csv", HEADER, synthetic_rows(date(2026, 3, 20)))
        daily, _ = onset_detect.load_daily(path, onset_detect.argparse.Namespace(
            filter=None, date_col=None, cost_col=None, currency_col=None, currency=None))
        r = onset_detect.detect(daily, (date(2026, 1, 1), date(2026, 3, 1)))
        self.assertIsNotNone(r["onset"])
        self.assertLessEqual(abs((r["onset"] - date(2026, 3, 20)).days), 2)

    def test_spike_is_not_onset(self):
        rows = []
        d = date(2026, 1, 1)
        while d < date(2026, 5, 1):
            spike = date(2026, 3, 10) <= d < date(2026, 3, 15)
            rows.append([d.isoformat(), "500" if spike else "100", "EUR", "Azure Databricks", "DBU"])
            d += timedelta(1)
        path = write_csv(self.tmp / "p.csv", HEADER, rows)
        daily, _ = onset_detect.load_daily(path, onset_detect.argparse.Namespace(
            filter=None, date_col=None, cost_col=None, currency_col=None, currency=None))
        r = onset_detect.detect(daily, (date(2026, 1, 1), date(2026, 3, 1)))
        self.assertIsNone(r["onset"])
        self.assertTrue(r["spikes"])


class SqlLibraryTests(unittest.TestCase):
    """Static safety checks for sql/: read-only, parameterized, no hard-coded dates."""
    SQL = sorted((Path(__file__).resolve().parents[2] / "playbook").glob("*/sql/*.sql"))

    def test_library_present(self):
        self.assertEqual(len(self.SQL), 27)

    def test_read_only_and_parameterized(self):
        import re
        write = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|OPTIMIZE|VACUUM)\b")
        for path in self.SQL:
            body = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--"))
            with self.subTest(sql=path.name):
                self.assertIsNone(write.search(body.upper()), "write keyword")
                self.assertRegex(body, r":(start_date|end_date|base_start|cmp_start)")
                self.assertNotRegex(body, r"DATE '20\d\d-|TIMESTAMP '20\d\d-", "hard-coded date")


if __name__ == "__main__":
    unittest.main()
