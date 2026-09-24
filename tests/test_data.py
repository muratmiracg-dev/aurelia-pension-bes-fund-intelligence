import tempfile
import unittest
from pathlib import Path

import pandas as pd

from aurelia_pension.data import generate, load


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        generate(self.directory)

    def tearDown(self):
        self.temp.cleanup()

    def test_reproducible_inputs(self):
        original = (self.directory / "fund_prices.csv").read_bytes()
        generate(self.directory)
        self.assertEqual(original, (self.directory / "fund_prices.csv").read_bytes())

    def test_complete_grid(self):
        funds, prices, benchmark, checks = load(self.directory)
        self.assertEqual(len(funds), 30)
        self.assertTrue(prices.index.equals(benchmark.index))
        self.assertEqual(len(checks), 10)

    def test_missing_nav_rejected(self):
        file = self.directory / "fund_prices.csv"
        table = pd.read_csv(file).iloc[1:]
        table.to_csv(file, index=False)
        with self.assertRaisesRegex(ValueError, "complete date grid"):
            load(self.directory)

    def test_duplicate_rejected(self):
        file = self.directory / "fund_prices.csv"
        table = pd.read_csv(file)
        pd.concat([table, table.iloc[:1]]).to_csv(file, index=False)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load(self.directory)

    def test_external_source_required(self):
        for name in ["funds.csv", "benchmarks.csv"]:
            file = self.directory / name
            table = pd.read_csv(file, keep_default_na=False)
            table["data_class"] = "EXTERNAL"
            table.to_csv(file, index=False)
        with self.assertRaisesRegex(ValueError, "provenance"):
            load(self.directory)

    def test_mixed_classes_rejected(self):
        file = self.directory / "funds.csv"
        table = pd.read_csv(file, keep_default_na=False)
        table.loc[0, "data_class"] = "EXTERNAL"
        table.to_csv(file, index=False)
        with self.assertRaisesRegex(ValueError, "data class"):
            load(self.directory)

    def test_unknown_fund_rejected(self):
        file = self.directory / "fund_prices.csv"
        table = pd.read_csv(file)
        table.loc[0, "fund_id"] = "MISSING"
        table.to_csv(file, index=False)
        with self.assertRaisesRegex(ValueError, "Orphan"):
            load(self.directory)


if __name__ == "__main__":
    unittest.main()
