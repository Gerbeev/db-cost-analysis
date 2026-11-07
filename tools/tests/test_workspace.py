"""Tests for new_audit.py and check_audit.py on a temporary workspace."""
from __future__ import annotations

import csv
import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_audit  # noqa: E402
import new_audit  # noqa: E402


def tick_all(checks: Path) -> None:
    text = checks.read_text(encoding="utf-8")
    checks.write_text(re.sub(r"^- \[ \]", "- [x]", text, flags=re.M), encoding="utf-8")


def write_bridge(path: Path, rows: list[tuple]) -> None:
    with path.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, header)
        w.writeheader()
        for line_id, cat, delta, status, hyp in rows:
            w.writerow({"line_id": line_id, "category": cat, "delta_per_day": delta, "status": status,
                        "hypothesis_id": hyp, "currency": "EUR"})


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.audit = new_audit.create("t-audit", self.base)

    def evaluate(self):
        steps = sorted(p for p in self.audit.iterdir() if p.is_dir() and re.match(r"^\d\d_", p.name))
        return {s.name[:2]: check_audit.evaluate(self.audit, s) for s in steps}

    def test_layout(self):
        steps = sorted(p.name for p in (ROOT / "playbook").iterdir() if p.is_dir() and p.name[:2].isdigit())
        self.assertEqual(len(steps), 10)
        for name in steps:
            self.assertTrue((self.audit / name / "CHECKS.md").is_file(), name)
        for name in ("scope_record.md", "evidence_register.csv", "hypothesis_register.csv", "delta_bridge.csv"):
            self.assertTrue((self.audit / name).is_file(), name)
        self.assertTrue((self.audit / "01_data_quality" / "exports").is_dir())
        self.assertTrue((self.audit / "09_report_and_controls" / "findings_report.md").is_file())
        with self.assertRaises(SystemExit):
            new_audit.create("t-audit", self.base)

    def test_every_step_has_gate_and_outputs(self):
        for step in (ROOT / "playbook").glob("[0-9][0-9]_*"):
            r = check_audit.evaluate(self.audit, self.audit / step.name)
            self.assertTrue(any(c[0].startswith("G") for c in r["checks"]), step.name)
            self.assertTrue(r["outputs"], step.name)

    def test_fresh_audit_open_and_step00_passes_when_ticked(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = check_audit.main([str(self.audit)])
        self.assertEqual(code, 1)
        self.assertTrue((self.audit / "STATUS.md").is_file())
        self.assertFalse(self.evaluate()["00"]["passed"])
        tick_all(self.audit / "00_frame" / "CHECKS.md")
        self.assertTrue(self.evaluate()["00"]["passed"])

    def test_na_requires_reason(self):
        p = self.audit / "00_frame" / "CHECKS.md"
        tick_all(p)
        p.write_text(p.read_text(encoding="utf-8").replace("- [x] C0.9", "- [-] C0.9", 1), encoding="utf-8")
        self.assertFalse(self.evaluate()["00"]["passed"])
        p.write_text(p.read_text(encoding="utf-8").replace("(§3)\n- [x] G0", "(§3) | none needed\n- [x] G0", 1),
                     encoding="utf-8")
        self.assertTrue(self.evaluate()["00"]["passed"])

    def test_bridge_identity_and_residual(self):
        bridge = self.audit / "delta_bridge.csv"
        write_bridge(bridge, [("TOTAL", "TOTAL", "100", "", ""), ("ACC-02", "ACCOUNTING", "10", "", ""),
                              ("BKT-01", "BUCKET", "70", "", ""), ("RC-01", "ROOT_CAUSE", "75", "CONFIRMED", "H-JOB-02"),
                              ("UNX", "UNEXPLAINED", "15", "", "")])
        res = dict((lvl, msg) for lvl, msg in check_audit.auto_07(self.audit))
        self.assertIn(check_audit.FAIL, res)          # 15% unexplained > 10%
        write_bridge(bridge, [("TOTAL", "TOTAL", "100", "", ""), ("ACC-02", "ACCOUNTING", "10", "", ""),
                              ("RC-01", "ROOT_CAUSE", "85", "CONFIRMED", "H-JOB-02"), ("UNX", "UNEXPLAINED", "5", "", "")])
        self.assertTrue(all(lvl == check_audit.PASS for lvl, _ in check_audit.auto_07(self.audit)))
        # register still says HYPOTHESIS for H-JOB-02 -> step 06 auto check fails
        self.assertTrue(any(lvl == check_audit.FAIL for lvl, _ in check_audit.auto_06(self.audit)))

    def test_groupings_must_agree(self):
        res = self.audit / "04_azure_decomposition" / "results"
        for name, values in (("delta_by_service.csv", ["60", "40"]), ("delta_by_meter.csv", ["50", "30"])):
            with (res / name).open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["key", "delta_per_day"])
                w.writerows([[f"k{i}", v] for i, v in enumerate(values)])
        self.assertEqual(check_audit.auto_04(self.audit)[0][0], check_audit.FAIL)

    def test_export_checks(self):
        exp = self.audit / "01_data_quality" / "exports" / "azure_actual__test.csv"
        exp.write_text("Date,CostInBillingCurrency,BillingCurrencyCode\n2026-01-05,1,EUR\n2026-03-05,1,USD\n",
                       encoding="utf-8")
        levels = [lvl for lvl, _ in check_audit.auto_01(self.audit)]
        self.assertEqual(levels.count(check_audit.FAIL), 2)   # mixed currency + Feb gap


if __name__ == "__main__":
    unittest.main()
