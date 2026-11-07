"""Offline regression coverage for approved cost-research correctness fixes.

These tests do not execute SQL against a Databricks tenant.
"""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from analyze_costs import csv_safe_cell, write_csv, read_azure, create_report, month_sequence
from apptio_api import atomic_write_csv


class CsvSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def test_dangerous_formula_prefixes_and_indentation_are_escaped(self):
        for value in ("=1+1", "+SUM(1,1)", "-cmd|' /C calc'!A0", "@SUM(1,2)",
                      "  =1+2", "\t=HYPERLINK(\"https://example.com\")",
                      "\r\n+SHELL", "\ufeff=1+1", "\u200b=1+1"):
            with self.subTest(value=value):
                self.assertEqual(csv_safe_cell(value), "'" + value)

    def test_signed_numeric_amounts_remain_machine_readable(self):
        for value in ("-5.00", "+5.25", "0", "-0.01", "1.2E+6", "+.5"):
            with self.subTest(value=value):
                self.assertEqual(csv_safe_cell(value), value)

    def test_non_formula_values_are_not_modified(self):
        for value in ("Normal service", "O'Brien", "test@example.com", "0=0", ""):
            with self.subTest(value=value):
                self.assertEqual(csv_safe_cell(value), value)

    def test_azure_growth_export_is_neutralized_without_changing_cost_math(self):
        src = self.folder / "azure.csv"
        with src.open("w", newline="", encoding="utf-8") as h:
            w = csv.writer(h)
            w.writerow(["Date", "Cost", "Currency", "ServiceName"])
            w.writerow(["2026-03-03", "9", "EUR", "=1+1"])
            w.writerow(["2026-04-03", "13", "EUR", "=1+1"])
        months = month_sequence("2026-03", "2026-04")
        azure = read_azure(src, months)
        self.assertEqual(azure["totals"][("2026-04", "EUR")], 13)
        out = self.folder / "out"
        create_report(out, months, None, azure)
        with (out / "growth_azure_services.csv").open(newline="", encoding="utf-8") as h:
            rows = list(csv.DictReader(h))
        self.assertEqual(rows[0]["service"], "'=1+1")
        self.assertEqual(rows[0]["delta"], "4.00")

    def test_ibm_api_csv_writer_uses_same_sanitization_policy(self):
        out = self.folder / "ibm.csv"
        atomic_write_csv(out, ["tag", "amount"], [["\t=1+1", "-8.50"]])
        with out.open(newline="", encoding="utf-8") as h:
            record = next(csv.DictReader(h))
        self.assertEqual(record["tag"], "'\t=1+1")
        self.assertEqual(record["amount"], "-8.50")

    def test_generic_csv_writer_neutralizes_all_cells(self):
        out = self.folder / "generic.csv"
        write_csv(out, ["field", "value"], [["@NOW()", "-12.00"]])
        with out.open(newline="", encoding="utf-8") as h:
            row = next(csv.DictReader(h))
        self.assertEqual(row["field"], "'@NOW()")
        self.assertEqual(row["value"], "-12.00")

if __name__ == "__main__":
    unittest.main()
