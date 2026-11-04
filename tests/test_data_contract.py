"""Every ingestion control in data.load() must reject the input it guards against."""

import re
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from aurelia_pension.data import generate, load


class DataContractRejectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._source = tempfile.TemporaryDirectory()
        cls.source = Path(cls._source.name)
        generate(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls._source.cleanup()

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.directory = Path(self._temp.name)
        for name in ("funds.csv", "fund_prices.csv", "benchmarks.csv"):
            (self.directory / name).write_bytes((self.source / name).read_bytes())

    def tearDown(self):
        self._temp.cleanup()

    def read(self, name):
        return pd.read_csv(self.directory / name, dtype=str, keep_default_na=False)

    def write(self, name, table):
        table.to_csv(self.directory / name, index=False)

    def assertRejected(self, message):
        with self.assertRaisesRegex(ValueError, message):
            load(self.directory)

    def test_missing_column(self):
        self.write("fund_prices.csv", self.read("fund_prices.csv").drop(columns="nav"))
        self.assertRejected(r"Missing columns: \['nav'\]")

    def test_header_only_table(self):
        self.write("benchmarks.csv", self.read("benchmarks.csv").iloc[0:0])
        self.assertRejected("must be non-empty")

    def test_duplicate_or_blank_fund_id(self):
        funds = self.read("funds.csv")
        funds.loc[1, "fund_id"] = funds.loc[0, "fund_id"]
        self.write("funds.csv", funds)
        self.assertRejected("Fund IDs must be unique and non-empty")
        funds.loc[1, "fund_id"] = "   "
        self.write("funds.csv", funds)
        self.assertRejected("Fund IDs must be unique and non-empty")

    def test_non_try_currency(self):
        funds = self.read("funds.csv")
        funds.loc[0, "currency"] = "USD"
        self.write("funds.csv", funds)
        self.assertRejected("TRY-valued")

    def test_benchmark_data_class_must_match_funds(self):
        benchmarks = self.read("benchmarks.csv")
        benchmarks["data_class"] = "EXTERNAL"
        benchmarks["source_url"] = "https://example.org/benchmarks"
        self.write("benchmarks.csv", benchmarks)
        self.assertRejected("share data classification")

    def test_blank_fund_name(self):
        funds = self.read("funds.csv")
        funds.loc[0, "name"] = "   "
        self.write("funds.csv", funds)
        self.assertRejected("Names and categories must be non-empty")

    def test_non_positive_non_finite_or_non_numeric_nav(self):
        cases = {"0": "0.0", "-1.5": "-1.5", "inf": "inf", "nan": "nan",
                 "abc": "abc", "": "(blank)"}
        for bad, shown in cases.items():
            with self.subTest(nav=bad):
                prices = self.read("fund_prices.csv")
                prices.loc[5, "nav"] = bad
                self.write("fund_prices.csv", prices)
                self.assertRejected(
                    "finite and strictly positive numbers: fund_prices.csv row 7 has "
                    + re.escape(shown) + "$"
                )

    def test_benchmark_nav_error_names_the_file(self):
        benchmarks = self.read("benchmarks.csv")
        benchmarks.loc[0, "nav"] = "n/a"
        self.write("benchmarks.csv", benchmarks)
        self.assertRejected("benchmarks.csv row 2 has n/a$")

    def test_missing_benchmark_category(self):
        benchmarks = self.read("benchmarks.csv")
        dropped = benchmarks["category"].iloc[0]
        self.write("benchmarks.csv", benchmarks[benchmarks["category"] != dropped])
        self.assertRejected("one benchmark series per category")

    def test_history_shorter_than_three_years(self):
        prices, benchmarks = self.read("fund_prices.csv"), self.read("benchmarks.csv")
        keep = sorted(prices["date"].unique())[-700:]
        self.write("fund_prices.csv", prices[prices["date"].isin(keep)])
        self.write("benchmarks.csv", benchmarks[benchmarks["date"].isin(keep)])
        self.assertRejected("At least 757 shared NAV dates")

    def test_fund_observations_after_source_cutoff(self):
        funds = self.read("funds.csv")
        last = max(self.read("fund_prices.csv")["date"])
        cutoff = pd.Timestamp(last) - pd.Timedelta(days=1)
        funds.loc[0, "source_asof"] = cutoff.strftime("%Y-%m-%d")
        self.write("funds.csv", funds)
        self.assertRejected("cannot exceed the declared source cutoff")

    def test_benchmark_observations_after_source_cutoff(self):
        benchmarks = self.read("benchmarks.csv")
        last = max(benchmarks["date"])
        benchmarks["source_asof"] = (pd.Timestamp(last) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        self.write("benchmarks.csv", benchmarks)
        self.assertRejected("Benchmark observation exceeds its source cutoff")


if __name__ == "__main__":
    unittest.main()
