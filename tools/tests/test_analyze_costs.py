"""Synthetic fixtures only; no production data or cloud access."""
import csv
import importlib.util
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("analyze_costs", HERE / "tools" / "analyze_costs.py")
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)


class CostAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.months = analyzer.month_sequence("2026-06", "2026-10")

    def write(self, name, headers, rows):
        path = self.root / name
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def azure_csv(self):
        rows = [
            [f"2026-{month:02d}-02", f"{50 + i * 10}", "EUR", "Virtual Machines", "VM Meter", "databricks-rg-test", "/subscriptions/test/resource1", "sub-test", "Usage"]
            for i, month in enumerate(range(6, 11))
        ]
        rows += [["2026-10-04", "-5.00", "EUR", "Virtual Machines", "VM Meter", "databricks-rg-test", "/subscriptions/test/resource1", "sub-test", "Adjustment"]]
        return self.write("azure.csv", ["Date", "CostInBillingCurrency", "BillingCurrency", "ServiceName", "MeterName", "ResourceGroup", "ResourceId", "SubscriptionId", "ChargeType"], rows)

    def databricks_csv(self):
        rows = [
            [f"2026-{month:02d}", "acc-synthetic", "ws-synthetic", "JOBS", "PREMIUM_JOBS_COMPUTE", "USD", "DBU", "100", str(100 + i * 20), "0", "100"]
            for i, month in enumerate(range(6, 11))
        ]
        return self.write("db.csv", ["month", "account_id", "workspace_id", "product", "sku_name", "currency_code", "usage_unit", "net_usage_quantity", "estimated_list_cost", "unpriced_records", "billing_records"], rows)

    def test_five_month_sequence(self):
        self.assertEqual(self.months, ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"])
        with self.assertRaises(analyzer.DataError):
            analyzer.month_sequence("2026-11", "2026-06")

    def test_azure_credits_not_discarded(self):
        data = analyzer.read_azure(self.azure_csv(), self.months)
        self.assertEqual(data["totals"][("2026-10", "EUR")], Decimal("85"))
        self.assertEqual(data["totals"][("2026-06", "EUR")], Decimal("50"))
        self.assertEqual(data["charge_types"][("2026-10", "EUR", "Adjustment")], Decimal("-5"))

    def test_databricks_list_price_is_separate(self):
        azure = analyzer.read_azure(self.azure_csv(), self.months)
        db = analyzer.read_databricks(self.databricks_csv(), self.months)
        out = self.root / "reports"
        analyzer.create_report(out, self.months, db, azure)
        report = (out / "summary.md").read_text(encoding="utf-8")
        self.assertIn("Databricks list-price estimates to Azure billed actuals", report)
        self.assertIn("2026-06 → 2026-10 delta: 35.00", report)
        self.assertIn("2026-06 → 2026-10 delta: 80.00", report)
        with (out / "growth_azure_services.csv").open(newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        self.assertEqual(row["delta"], "35.00")
        self.assertEqual(row["service"], "Virtual Machines")

    def test_missing_currency_rejected(self):
        path = self.write("bad.csv", ["Date", "CostInBillingCurrency", "ServiceName"], [["2026-06-01", "100", "Azure Databricks"]])
        with self.assertRaisesRegex(analyzer.DataError, "billingcurrency|BillingCurrency"):
            analyzer.read_azure(path, self.months)

    def test_unpriced_detected_without_fabricating_zero(self):
        path = self.write("partial.csv", ["month", "account_id", "workspace_id", "product", "sku_name", "currency_code", "estimated_list_cost", "unpriced_records"],
                          [["2026-06", "acc", "ws", "JOBS", "SKU", "UNPRICED", "", "2"]])
        db = analyzer.read_databricks(path, self.months)
        self.assertEqual(sum(db["uncovered"].values()), 2)
        notes = analyzer.validate_quality(db, "Databricks", self.months)
        self.assertTrue(any("unpriced Databricks billing records" in x for x in notes))
        self.assertNotIn(("2026-06", "USD"), db["totals"])

    def test_currency_missing_month_is_not_zero(self):
        path = self.write("azure.csv", ["Date", "Cost", "Currency", "MeterCategory"],
                          [["2026-06-01", "12", "EUR", "Analytics"], ["2026-10-01", "18", "USD", "Analytics"]])
        azure = analyzer.read_azure(path, self.months)
        notes = analyzer.validate_quality(azure, "Azure", self.months)
        self.assertTrue(any("multiple currencies" in n for n in notes))
        self.assertEqual(analyzer.growth_rows(azure["services"], "2026-06", "2026-10", azure["totals"]), [])

    def test_duplicate_csv_header_rejected(self):
        path = self.write("dup.csv", ["Date", "Date", "CostInBillingCurrency", "BillingCurrency", "ServiceName"],
                          [["2026-06-01", "2026-06-01", "10", "EUR", "SQL"]])
        with self.assertRaisesRegex(analyzer.DataError, "Duplicate"):
            analyzer.read_azure(path, self.months)

    def test_cli_produces_reports(self):
        out = self.root / "output"
        rc = analyzer.main(["--azure", str(self.azure_csv()), "--databricks", str(self.databricks_csv()),
                            "--start", "2026-06", "--end", "2026-10", "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue((out / "data_quality.md").is_file())
        self.assertTrue((HERE / "audits" / "_logs" / "analysis.log").is_file())

    def test_cli_invalid_data_returns_error(self):
        bad = self.write("invalid.csv", ["Date", "CostInBillingCurrency", "BillingCurrency", "ServiceName"],
                         [["2026-06-01", "not-money", "EUR", "SQL"]])
        rc = analyzer.main(["--azure", str(bad), "--start", "2026-06", "--end", "2026-10", "--out", str(self.root / "out")])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
