"""Build a self-contained interactive report, CSV evidence and SQLite warehouse."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from .analytics import metrics, peer_ranking, rebalance_portfolio, walk_forward_var
from .data import CATEGORIES, SEED, generate, load

PERIODS = {"1Y": 252, "3Y": 756, "ALL": None}
ALLOCATIONS = {
    "Temkinli": [0.10, 0.35, 0.10, 0.35, 0.10],
    "Dengeli": [0.30, 0.25, 0.20, 0.10, 0.15],
    "Büyüme": [0.55, 0.10, 0.15, 0.05, 0.15],
}
STRESSES = {
    "Hisse düzeltmesi": [-0.20, -0.02, 0.06, 0.0, -0.10],
    "Faiz yükselişi": [-0.08, -0.10, 0.02, 0.0, -0.06],
    "Altın geri çekilmesi": [-0.03, 0.0, -0.18, 0.0, -0.05],
    "Birleşik stres": [-0.25, -0.12, -0.10, -0.01, -0.15],
}


def build(root: Path, data_dir: Path | None = None) -> dict:
    directory = data_dir or root / "data/demo"
    if data_dir is None:
        generate(directory)
    funds, prices, benchmarks, checks = load(directory)
    out = root / "artifacts"
    out.mkdir(exist_ok=True)
    # Portfolio fixtures select the first fund ID alphabetically, never by performance.
    if set(funds.category) != set(CATEGORIES):
        raise ValueError("Version 1 model allocations require the five documented categories")
    selected = {c: funds.loc[funds.category.eq(c), "fund_id"].sort_values().iloc[0]
                for c in CATEGORIES}
    portfolios = []
    for name, weights in ALLOCATIONS.items():
        mapping = {selected[c]: w for c, w in zip(CATEGORIES, weights)}
        path = rebalance_portfolio(prices, mapping)
        backtest = walk_forward_var(path.nav)
        backtest.pop("forecasts")
        backtest.pop("violations")
        portfolios.append({"name": name, "weights": weights, "funds": mapping,
                           "nav": path.nav.tolist(), "turnover_total": path.turnover.sum(),
                           "cost_nav_units": path.cost.sum(), "backtest": backtest,
                           "metrics": {p: metrics(path.nav.iloc[-n-1:] if n else path.nav)
                                       for p, n in PERIODS.items()},
                           "stress": {s: sum(w * shock for w, shock in zip(weights, shocks))
                                      for s, shocks in STRESSES.items()}})
    records = funds.to_dict("records")
    metric_frames = []
    for period, n in PERIODS.items():
        subset = prices.iloc[-n-1:] if n else prices
        bsubset = benchmarks.loc[subset.index]
        metric_frame = peer_ranking(pd.DataFrame([
            {"fund_id": r["fund_id"], "category": r["category"],
             **metrics(subset[r["fund_id"]], bsubset[r["category"]])}
            for r in records
        ]))
        metric_frame["period"] = period
        metric_frames.append(metric_frame)
        lookup = metric_frame.set_index("fund_id").to_dict("index")
        for r in records:
            r.setdefault("metrics", {})[period] = lookup[r["fund_id"]]
    for r in records:
        r["nav"] = prices[r["fund_id"]].tolist()
    metrics_frame = pd.concat(metric_frames, ignore_index=True)
    metrics_frame.to_csv(out / "fund_metrics.csv", index=False, float_format="%.10f")
    pd.DataFrame(checks).to_csv(out / "data_quality.csv", index=False)
    portfolio_rows = [{"name": p["name"], **p["metrics"]["ALL"],
                       **{k: v for k, v in p["backtest"].items() if k != "window"}}
                      for p in portfolios]
    pd.DataFrame(portfolio_rows).to_csv(out / "portfolio_metrics.csv", index=False)
    data_class = funds.data_class.iloc[0]
    payload = {
        "version": "1.0.0", "seed": SEED if data_class == "SYNTHETIC" else None,
        "data_class": data_class, "dates": prices.index.strftime("%Y-%m-%d").tolist(),
        "categories": CATEGORIES, "funds": records,
        "benchmarks": {c: benchmarks[c].tolist() for c in CATEGORIES},
        "portfolios": portfolios, "checks": checks, "stresses": STRESSES,
    }
    # Null is used for undefined ratios, never NaN/Infinity in JSON.
    clean = json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False,
                                  default=lambda value: value.item()))
    encoded = json.dumps(clean, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    (out / "dashboard_data.json").write_text(encoded, encoding="utf-8")
    template = (root / "web/index.html").read_text(encoding="utf-8")
    dashboard = template.replace("/*__DATA__*/", encoded.replace("<", "\\u003c"))
    dashboard = dashboard.replace("/*__ENGINE__*/", (root / "web/engine.js").read_text())
    (out / "Aurelia_Pension_BES_Dashboard.html").write_text(dashboard, encoding="utf-8")
    db = out / "aurelia_pension.sqlite"
    with sqlite3.connect(db) as conn:
        funds.to_sql("dim_fund", conn, if_exists="replace", index=False)
        prices.rename_axis("date").reset_index().melt("date", var_name="fund_id", value_name="nav").to_sql(
            "fact_fund_nav", conn, if_exists="replace", index=False)
        benchmarks.rename_axis("date").reset_index().melt("date", var_name="category", value_name="nav").to_sql(
            "fact_benchmark_nav", conn, if_exists="replace", index=False)
        metrics_frame.to_sql("fund_metrics", conn, if_exists="replace", index=False)
        pd.DataFrame(portfolio_rows).to_sql("portfolio_metrics", conn, if_exists="replace", index=False)
        conn.executescript((root / "sql/views.sql").read_text())
    manifest = {"version": "1.0.0", "data_class": data_class,
                "fund_count": len(funds), "nav_dates": len(prices),
                "price_observations": prices.size, "start": clean["dates"][0],
                "end": clean["dates"][-1], "checks_passed": len(checks),
                "portfolios": portfolio_rows,
                "inputs": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                           for f in sorted(directory.glob("*.csv"))}}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
