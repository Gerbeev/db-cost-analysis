"""Synthetic January-October cost series and March/April change-point tests."""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
import analyze_costs as costs  # noqa: E402
import analyze_apptio as apptio  # noqa: E402


class ChangePointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.months = costs.month_sequence('2026-01', '2026-10')
        # Baseline 10 units/day through March; double in April, persist thereafter.
        self.values = [310, 280, 310, 600, 620, 600, 620, 620, 600, 620]

    def write(self, name, header, rows):
        path = self.root / name
        with path.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        return path

    def test_jan_oct_and_daily_normalized_change_point(self):
        self.assertEqual(len(self.months), 10)
        azure = self.write('azure.csv', ['Date', 'CostInBillingCurrency', 'BillingCurrency', 'ServiceName'],
                           [[month + '-01', str(value), 'EUR', 'Databricks VMs']
                            for month, value in zip(self.months, self.values)])
        data = costs.read_azure(azure, self.months)
        records = {row[0]: row for row in costs.month_over_month_rows(data, self.months)}
        self.assertEqual(records['2026-01'][5], 'N/A')
        self.assertEqual(records['2026-03'][5], '30.00')
        self.assertEqual(records['2026-03'][9], '0.00')  # March: 31 days vs February: 28.
        self.assertEqual(records['2026-04'][5], '290.00')
        self.assertEqual(records['2026-04'][9], '10.00')
        self.assertEqual(records['2026-04'][10], '100.00')
        output = self.root / 'reports'
        costs.create_report(output, self.months, None, data)
        with (output / 'growth_mar_apr_azure_services.csv').open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]['delta'], '290.00')
        self.assertTrue((output / 'growth_feb_mar_azure_services.csv').exists())
        self.assertTrue((output / 'growth_apr_may_azure_services.csv').exists())
        summary = (output / 'summary.md').read_text(encoding='utf-8')
        self.assertIn('March/April change-point analysis', summary)

    def test_missing_march_is_not_zero_and_disables_march_april_driver(self):
        csv_path = self.write('partial.csv', ['Date', 'Cost', 'Currency', 'ServiceName'],
                              [['2026-02-01', '100', 'EUR', 'SQL'],
                               ['2026-04-01', '400', 'EUR', 'SQL']])
        data = costs.read_azure(csv_path, self.months)
        rows = {row[0]: row for row in costs.month_over_month_rows(data, self.months)}
        self.assertEqual(rows['2026-03'][5], 'N/A')
        self.assertEqual(rows['2026-04'][5], 'N/A')
        output = self.root / 'report_missing'
        costs.create_report(output, self.months, None, data)
        with (output / 'growth_mar_apr_azure_services.csv').open(newline='', encoding='utf-8') as f:
            self.assertEqual(list(csv.DictReader(f)), [])
        self.assertIn('missing months', (output / 'data_quality.md').read_text(encoding='utf-8'))

    def test_separate_databricks_estimates_and_azure_actual(self):
        db_path = self.write('db.csv',
                             ['month', 'account_id', 'workspace_id', 'product', 'sku_name',
                              'currency_code', 'estimated_list_cost', 'unpriced_records'],
                             [[month, 'acct', 'workspace', 'JOBS', 'JOBS_SKU', 'USD',
                               str(cost), '0'] for month, cost in zip(self.months, self.values)])
        db = costs.read_databricks(db_path, self.months)
        output = self.root / 'db_out'
        costs.create_report(output, self.months, db, None)
        self.assertEqual(db['totals'][('2026-04', 'USD')], Decimal('600'))
        with (output / 'growth_mar_apr_databricks.csv').open(newline='', encoding='utf-8') as f:
            self.assertEqual(list(csv.DictReader(f))[0]['delta'], '290.00')
        self.assertTrue((output / 'change_point_mom_databricks_estimated.csv').exists())

    def test_apptio_change_point_and_driver_ranking(self):
        path = self.write('apptio.csv',
                          ['month', 'currency', 'metric', 'view_id', 'vendor', 'enhanced_service_name', 'amount'],
                          [[month, 'EUR', 'unblended_cost', 'USER_DEFAULT', 'Azure', 'Databricks', str(cost)]
                           for month, cost in zip(self.months, self.values)])
        data = apptio.analyze(path, self.months)
        out = self.root / 'apptio_out'
        apptio.create_report(data, self.months, out, None)
        with (out / 'apptio_growth_mar_apr_drivers.csv').open(newline='', encoding='utf-8') as f:
            self.assertEqual(list(csv.DictReader(f))[0]['delta'], '290.00')
        with (out / 'apptio_change_point_mom.csv').open(newline='', encoding='utf-8') as f:
            rows = {row['month']: row for row in csv.DictReader(f)}
        self.assertEqual(rows['2026-04']['daily_average_delta_percent'], '100.00')

    def test_sparse_months_not_treated_as_consecutive(self):
        apptio_data = {'totals': {('2026-02', 'EUR'): Decimal('100'),
                                  ('2026-04', 'EUR'): Decimal('500')}}
        rows = costs.month_over_month_rows(apptio_data, ['2026-02', '2026-04'])
        self.assertEqual(rows[1][2], 'N/A')
        self.assertEqual(rows[1][5], 'N/A')


if __name__ == '__main__':
    unittest.main()
