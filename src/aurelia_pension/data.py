"""Synthetic market fixture and strict file-based ingestion contract."""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260920
CATEGORIES = ["Hisse Senedi", "Borçlanma Araçları", "Altın", "Para Piyasası", "Değişken"]
CODES = ["HS", "BA", "AL", "PP", "DG"]


def generate(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    dates = pd.bdate_range("2022-01-03", "2026-09-18")
    n = len(dates) - 1
    market = rng.normal(size=n)
    rows, benchmark_rows, metadata = [], [], []
    specs = [(0.26, 0.30), (0.22, 0.065), (0.25, 0.23), (0.24, 0.008), (0.245, 0.16)]
    for k, (category, code, (mu, sigma)) in enumerate(zip(CATEGORIES, CODES, specs)):
        z = 0.45 * market + np.sqrt(1 - 0.45**2) * rng.normal(size=n)
        log_returns = (mu - sigma**2 / 2) / 252 + sigma / np.sqrt(252) * z
        # Deliberately simulated stress and recovery; never labelled actual market history.
        stress = (dates[1:] >= "2024-05-01") & (dates[1:] <= "2024-05-31")
        recovery = (dates[1:] >= "2024-07-01") & (dates[1:] <= "2024-09-30")
        log_returns[stress] -= [0.011, 0.003, -0.002, 0.0, 0.005][k]
        log_returns[recovery] += [0.002, 0.0004, 0.0004, 0.0, 0.001][k]
        benchmark_nav = np.r_[100, 100 * np.exp(np.cumsum(log_returns))]
        for date, nav in zip(dates, benchmark_nav):
            benchmark_rows.append({"date": date.date(), "category": category,
                                   "nav": nav, "data_class": "SYNTHETIC",
                                   "source_url": "", "source_asof": "2026-09-18"})
        for j in range(6):
            fund = f"DEMO-{code}{j+1:02d}"
            fee = [0.016, 0.01, 0.011, 0.005, 0.014][k]
            alpha = (j - 2.5) * 0.009
            noise = rng.normal(0, max(0.0005, sigma * 0.17) / np.sqrt(252), n)
            r = log_returns + (alpha - fee) / 252 + noise
            nav = np.r_[1, np.exp(np.cumsum(r))]
            metadata.append({"fund_id": fund, "name": f"Aurelia {category} {j+1:02d}",
                             "category": category, "annual_fee_assumption": fee,
                             "currency": "TRY", "data_class": "SYNTHETIC",
                             "source_url": "", "source_asof": "2026-09-18"})
            rows.extend({"date": d.date(), "fund_id": fund, "nav": p}
                        for d, p in zip(dates, nav))
    pd.DataFrame(metadata).to_csv(directory / "funds.csv", index=False)
    pd.DataFrame(rows).to_csv(directory / "fund_prices.csv", index=False, float_format="%.10f")
    pd.DataFrame(benchmark_rows).to_csv(directory / "benchmarks.csv", index=False,
                                      float_format="%.10f")


def load(directory: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    funds = pd.read_csv(directory / "funds.csv", keep_default_na=False)
    prices = pd.read_csv(directory / "fund_prices.csv")
    benchmarks = pd.read_csv(directory / "benchmarks.csv", keep_default_na=False)
    contracts = [(funds, {"fund_id", "name", "category", "currency", "data_class",
                          "source_url", "source_asof"}),
                 (prices, {"date", "fund_id", "nav"}),
                 (benchmarks, {"date", "category", "nav", "data_class", "source_url", "source_asof"})]
    for table, required in contracts:
        if not required <= set(table.columns):
            raise ValueError(f"Missing columns: {sorted(required - set(table.columns))}")
        if table.empty or table[list(required)].isna().any().any():
            raise ValueError("Tables must be non-empty with no null required fields")
    if funds.fund_id.duplicated().any() or (funds.fund_id.str.strip() == "").any():
        raise ValueError("Fund IDs must be unique and non-empty")
    if not funds.currency.eq("TRY").all():
        raise ValueError("Version 1 requires TRY-valued total-return NAV")
    classes = set(funds.data_class)
    if len(classes) != 1 or not classes <= {"SYNTHETIC", "EXTERNAL"}:
        raise ValueError("Use one declared data class; do not silently mix sources")
    if set(benchmarks.data_class) != classes:
        raise ValueError("Benchmarks and funds must share data classification")
    if classes == {"EXTERNAL"}:
        for table in [funds, benchmarks]:
            if not table.source_url.str.startswith("https://").all():
                raise ValueError("External funds and benchmarks need provenance HTTPS URLs")
    pd.to_datetime(funds.source_asof, format="%Y-%m-%d", errors="raise")
    if (funds["name"].str.strip().eq("") | funds.category.str.strip().eq("")).any():
        raise ValueError("Names and categories must be non-empty")
    for table, key in [(prices, "fund_id"), (benchmarks, "category")]:
        table["date"] = pd.to_datetime(table.date, format="%Y-%m-%d", errors="raise")
        if table.duplicated(["date", key]).any():
            raise ValueError("Duplicate date / entity observation")
        table["nav"] = pd.to_numeric(table.nav, errors="raise")
        if not np.isfinite(table.nav).all() or not table.nav.gt(0).all():
            raise ValueError("NAV values must be finite and strictly positive")
    if set(prices.fund_id) != set(funds.fund_id):
        raise ValueError("Orphan or missing fund ID")
    if set(benchmarks.category) != set(funds.category):
        raise ValueError("Exactly one benchmark series per category required")
    wide = prices.pivot(index="date", columns="fund_id", values="nav").sort_index()
    bench = benchmarks.pivot(index="date", columns="category", values="nav").sort_index()
    if wide.isna().any().any() or bench.isna().any().any() or not wide.index.equals(bench.index):
        raise ValueError("All series require an identical complete date grid; no silent fill")
    if len(wide) < 757:
        raise ValueError("At least 757 shared NAV dates required for the three-year view")
    if wide.index[-1] > pd.to_datetime(funds.source_asof).min():
        raise ValueError("Observed dates cannot exceed the declared source cutoff")
    if (benchmarks.date > pd.to_datetime(benchmarks.source_asof, format="%Y-%m-%d")).any():
        raise ValueError("Benchmark observation exceeds its source cutoff")
    checks = [{"control": x, "status": "PASS"} for x in [
        "Required schema", "Unique entity-date keys", "Positive finite NAV", "TRY unit",
        "Fund referential integrity", "Benchmark coverage", "Complete common date grid",
        "Data classification", "Source cutoff", "Minimum observation history"]]
    return funds, wide, bench, checks
