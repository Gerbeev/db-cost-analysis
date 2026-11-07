"""Offline IBM Apptio integration tests. No live HTTP calls or secrets."""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE / "tools"))
import apptio_api as api
import analyze_apptio as analyzer


class ApptioApiTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)

    def test_url_host_and_scheme_enforced(self):
        allowed = {"customer.apptio.com"}
        self.assertEqual(api.validated_https("https://customer.apptio.com/biit/api/v2/example.tsv", allowed),
                         "https://customer.apptio.com/biit/api/v2/example.tsv")
        for url in ("http://customer.apptio.com/x", "https://evil.example/x",
                    "https://customer.apptio.com:1234/x", "https://user:pass@customer.apptio.com/x"):
            with self.subTest(url=url), self.assertRaises(api.ExportError):
                api.validated_https(url, allowed)

    def test_basic_auth_uses_key_as_username_empty_password(self):
        import base64
        encoded = api.cloudability_headers("offline-secret")["Authorization"].split()[1]
        self.assertEqual(base64.b64decode(encoded), b"offline-secret:")

    def test_pagination_sends_token_and_stops_at_end(self):
        queries = []
        def respond(url, headers, timeout):
            parsed = parse_qs(urlsplit(url).query)
            queries.append(parsed)
            if len(queries) == 1:
                return {"results": [{"vendor": "Azure", "unblended_cost": "7"}],
                        "pagination": {"next": "next-page"}}
            return {"results": [{"vendor": "Azure", "unblended_cost": "8"}], "pagination": {}}
        with patch.object(api, "request_json", side_effect=respond):
            rows, pages = api.get_cost_rows("key", "eu", [("start_date", "2026-06-01")], 5)
        self.assertEqual([r["unblended_cost"] for r in rows], ["7", "8"])
        self.assertEqual(pages, 2)
        self.assertNotIn("token", queries[0])
        self.assertEqual(queries[1]["token"], ["next-page"])

    def test_repeated_pagination_token_rejected(self):
        with patch.object(api, "request_json", return_value={"results": [], "pagination": {"next": "again"}}):
            with self.assertRaisesRegex(api.ExportError, "repeated"):
                api.get_cost_rows("key", "eu", [("start_date", "2026-06-01")], 5)

    def test_invalid_request_measure_rejected(self):
        args = api.parser().parse_args(["cloudability", "export", "--currency", "EUR",
                                        "--dimensions", "unknown_field", "--out", str(self.root / "cost.csv")])
        with patch.dict(os.environ, {"CLOUDABILITY_API_KEY": "secret"}), patch.object(api, "request_json", return_value=[
            {"name": "vendor", "type": "dimension"}, {"name": "unblended_cost", "type": "metric"}
        ]), self.assertRaisesRegex(api.ExportError, "not available"):
            api.run_cloudability(args)

    def test_cloudability_five_month_export_manifest(self):
        target = self.root / "cost.csv"
        args = api.parser().parse_args(["cloudability", "export", "--region", "eu", "--currency", "EUR",
                                        "--filter", "vendor==Azure", "--start", "2026-06", "--end", "2026-10",
                                        "--out", str(target)])
        measures = [{"name": "vendor", "type": "dimension"},
                    {"name": "enhanced_service_name", "type": "dimension"},
                    {"name": "unblended_cost", "type": "metric"}]
        all_queries = []
        def cost_rows(key, region, query, timeout, max_pages):
            all_queries.append(query)
            return [{"vendor": "Azure", "enhanced_service_name": "Virtual Machines", "unblended_cost": "12.50"}], 1
        with patch.dict(os.environ, {"CLOUDABILITY_API_KEY": "secret"}), \
             patch.object(api, "request_json", return_value=measures), \
             patch.object(api, "get_cost_rows", side_effect=cost_rows):
            api.run_cloudability(args)
        with target.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["month"], "2026-06")
        self.assertEqual(rows[-1]["month"], "2026-10")
        self.assertEqual(rows[0]["amount"], "12.50")
        self.assertEqual(rows[0]["currency"], "EUR")
        self.assertTrue(all(("filters", "vendor==Azure") in q for q in all_queries))
        manifest = json.loads(target.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["total_rows"], 5)
        self.assertEqual(manifest["filters"], ["vendor==Azure"])
        self.assertNotIn("secret", target.read_text(encoding="utf-8"))
        self.assertNotIn("secret", target.with_suffix(".manifest.json").read_text(encoding="utf-8"))

    def test_missing_export_currency_is_error(self):
        with patch.dict(os.environ, {"CLOUDABILITY_API_KEY": "secret"}):
            self.assertEqual(api.main(["cloudability", "export"]), 2)

    def test_apptioone_token_env_discovery_and_export(self):
        target = self.root / "report.tsv"
        args = api.parser().parse_args(["apptioone", "--customer", "customer.example",
                                        "--api-url", "https://customer.apptio.com/biit/api/v2/my.tsv",
                                        "--out", str(target)])
        got = []
        def download(url, headers, timeout):
            got.append((url, headers))
            return b"Month\tCost\nJun\t100\n", {"Content-Type": "text/tab-separated-values"}
        with patch.dict(os.environ, {"APPTIO_KEY_ACCESS": "public", "APPTIO_KEY_SECRET": "private"}), \
             patch.object(api, "post_frontdoor", return_value="token"), \
             patch.object(api, "request_json", return_value={"id": "env123"}), \
             patch.object(api, "response_bytes", side_effect=download):
            api.run_apptioone(args)
        self.assertEqual(target.read_text(encoding="utf-8"), "Month\tCost\nJun\t100\n")
        self.assertEqual(got[0][1]["apptio-current-environment"], "env123")
        self.assertEqual(got[0][1]["apptio-opentoken"], "token")

    def test_apptioone_rejects_report_on_other_host(self):
        target = self.root / "report.tsv"
        args = api.parser().parse_args(["apptioone", "--environment-id", "23",
                                        "--api-url", "https://bad.example/report.tsv", "--out", str(target)])
        with patch.dict(os.environ, {"APPTIO_KEY_ACCESS": "public", "APPTIO_KEY_SECRET": "private"}), \
             self.assertRaisesRegex(api.ExportError, "allowed-host"):
            api.run_apptioone(args)

    def test_frontdoor_token_in_response_header(self):
        fake_response = MagicMock()
        fake_response.headers.get.return_value = "private-token"
        fake_response.__enter__.return_value = fake_response
        with patch.object(api.OPENER, "open", return_value=fake_response):
            token = api.post_frontdoor("https://frontdoor-eu.apptio.com/service/apikeylogin",
                                       {"keyAccess": "access", "keySecret": "secret"}, 5)
        self.assertEqual(token, "private-token")

    def test_cloudability_api_response_shape_required(self):
        with patch.object(api, "request_json", return_value={"data": [{"cost": "100"}]}):
            with self.assertRaisesRegex(api.ExportError, "results array"):
                api.get_cost_rows("key", "us", [("start_date", "2026-06-01")], 5)


class ApptioAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.path = self.root / "cost.csv"

    def write(self, data):
        with self.path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["month", "currency", "metric", "view_id", "vendor", "enhanced_service_name", "amount"])
            writer.writerows(data)

    def test_growth_and_missing_month_alert(self):
        self.write([["2026-06", "EUR", "unblended_cost", "USER_DEFAULT", "Azure", "Databricks", "10.00"],
                    ["2026-10", "EUR", "unblended_cost", "USER_DEFAULT", "Azure", "Databricks", "40.00"]])
        months = ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
        data = analyzer.analyze(self.path, months)
        analyzer.create_report(data, months, self.root / "reports", None)
        summary = (self.root / "reports" / "apptio_summary.md").read_text(encoding="utf-8")
        quality = (self.root / "reports" / "apptio_quality.md").read_text(encoding="utf-8")
        self.assertIn("30.00", summary)
        self.assertIn("2026-07 has no rows", quality)
        self.assertIn("NOT an assumed zero", quality)

    def test_mixed_metric_rejected(self):
        self.write([["2026-06", "EUR", "unblended_cost", "USER_DEFAULT", "Azure", "Databricks", "10.00"],
                    ["2026-10", "EUR", "total_amortized_cost", "USER_DEFAULT", "Azure", "Databricks", "40.00"]])
        with self.assertRaisesRegex(analyzer.DataError, "different IBM Apptio cost metrics"):
            analyzer.analyze(self.path, ["2026-06", "2026-10"])

    def test_incomplete_currency_not_comparable(self):
        self.write([["2026-06", "EUR", "unblended_cost", "USER_DEFAULT", "Azure", "Databricks", "10"],
                    ["2026-10", "USD", "unblended_cost", "USER_DEFAULT", "Azure", "Databricks", "40"]])
        months = ["2026-06", "2026-10"]
        data = analyzer.analyze(self.path, months)
        analyzer.create_report(data, months, self.root / "reports", None)
        with (self.root / "reports" / "apptio_growth_drivers.csv").open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertFalse(rows)
        self.assertIn("Multiple currencies", (self.root / "reports" / "apptio_quality.md").read_text(encoding="utf-8"))

    def test_bad_number_rejected(self):
        self.write([["2026-06", "EUR", "unblended_cost", "USER_DEFAULT", "Azure", "Databricks", "nope"]])
        with self.assertRaises(analyzer.DataError):
            analyzer.analyze(self.path, ["2026-06"])


if __name__ == "__main__":
    unittest.main()

class ApptioOneNormalizerTests(unittest.TestCase):
    """Verify report-specific column mapping without inventing financial semantics."""

    def setUp(self):
        from normalize_apptioone import convert
        self.convert = convert
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.input = self.root / "report.tsv"
        self.out = self.root / "normalized.csv"

    def write(self, rows):
        with self.input.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t")
            writer.writerow(["CalendarMonth", "CostCenter", "ActualCost", "Currency"])
            writer.writerows(rows)

    def convert_input(self, **kwargs):
        return self.convert(self.input, self.out, "CalendarMonth", "ActualCost", ["CostCenter"],
                            kwargs.get("currency"), kwargs.get("currency_column"),
                            "AllocatedCost", "CostTransparency", "2026-06", "2026-10")

    def test_tbm_normalization_with_per_row_currency(self):
        self.write([["2026-06", "IT", "50.25", "EUR"], ["2026-10-01", "IT", "101.00", "EUR"]])
        manifest = self.convert_input(currency_column="Currency")
        self.assertEqual(manifest["normalized_rows"], 2)
        self.assertIn("2026-07", manifest["missing_months"])
        with self.out.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(rows[0]["metric"], "AllocatedCost")
        self.assertEqual(rows[1]["month"], "2026-10")
        self.assertEqual(rows[1]["amount"], "101.00")

    def test_tbm_fiscal_period_not_guessed(self):
        from analyze_costs import DataError
        self.write([["Jun:FY2026", "IT", "50", "EUR"]])
        with self.assertRaisesRegex(DataError, "fiscal dates"):
            self.convert_input(currency="EUR")

    def test_tbm_requires_currency_and_cost_definition(self):
        from analyze_costs import DataError
        self.write([["2026-06", "IT", "50", "EUR"]])
        with self.assertRaisesRegex(DataError, "exactly one"):
            self.convert_input()
        with self.assertRaisesRegex(DataError, "exactly one"):
            self.convert_input(currency="EUR", currency_column="Currency")

    def test_tbm_wrong_header_refused(self):
        from analyze_costs import DataError
        self.write([["2026-06", "IT", "50", "EUR"]])
        with self.assertRaisesRegex(DataError, "Missing report columns"):
            self.convert(self.input, self.out, "WrongMonth", "ActualCost", ["CostCenter"],
                         "EUR", None, "AllocatedCost", "CostTransparency", "2026-06", "2026-10")
