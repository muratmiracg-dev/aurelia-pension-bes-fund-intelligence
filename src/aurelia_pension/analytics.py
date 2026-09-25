"""Return, risk, rebalancing and deterministic contribution calculations.

No function makes a suitability decision or computes statutory BES entitlements.
All monetary values are TRY; ratios are decimals; risk losses are positive.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

PERIODS = 252


def finite_vector(values: Sequence[float], *, minimum: int = 2) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or len(array) < minimum or not np.isfinite(array).all():
        raise ValueError(f"Expected at least {minimum} finite observations")
    return array


def returns(nav: Sequence[float]) -> np.ndarray:
    values = finite_vector(nav)
    if (values <= 0).any():
        raise ValueError("NAV must be strictly positive")
    return values[1:] / values[:-1] - 1


def historical_tail(daily_returns: Sequence[float], confidence: float = 0.95) -> dict:
    """Historical one-day VaR and fractional-tail Expected Shortfall.

    ES averages exactly (1-confidence)*N worst observations, fractionally weighting
    the boundary when needed. VaR uses an empirical inverted-CDF order statistic.
    Reported loss measures are floored at zero for a wholly positive sample.
    """
    values = finite_vector(daily_returns)
    if not 0 < confidence < 1 or (values <= -1).any():
        raise ValueError("Invalid confidence or return domain")
    losses = np.sort(-values)[::-1]
    mass = (1 - confidence) * len(losses)
    whole = int(math.floor(mass + 1e-12))
    remainder = max(0.0, mass - whole)
    weighted = losses[:whole].sum()
    if remainder > 1e-12:
        weighted += remainder * losses[whole]
    var = float(np.quantile(-values, confidence, method="inverted_cdf"))
    return {"var95": max(0.0, var), "es95": max(0.0, float(weighted / mass))}


def metrics(nav: Sequence[float], benchmark: Sequence[float] | None = None) -> dict:
    if (isinstance(nav, pd.Series) and isinstance(benchmark, pd.Series)
            and not nav.index.equals(benchmark.index)):
        raise ValueError("Benchmark and NAV must share the same dates")
    values = finite_vector(nav, minimum=3)
    daily = returns(values)
    volatility = float(np.std(daily, ddof=1) * np.sqrt(PERIODS))
    wealth = values / values[0]
    drawdown = wealth / np.maximum.accumulate(wealth) - 1
    out = {
        "total_return": float(wealth[-1] - 1),
        "annual_return": float(wealth[-1] ** (PERIODS / len(daily)) - 1),
        "volatility": volatility,
        "max_drawdown": float(drawdown.min()),
        "observations": len(daily),
        **historical_tail(daily),
    }
    if benchmark is not None:
        reference = finite_vector(benchmark, minimum=3)
        if len(reference) != len(values):
            raise ValueError("Benchmark and NAV must share the same dates")
        active = daily - returns(reference)
        tracking_error = float(np.std(active, ddof=1) * np.sqrt(PERIODS))
        out.update({
            "benchmark_return": float(reference[-1] / reference[0] - 1),
            "excess_return": float(wealth[-1] - reference[-1] / reference[0]),
            "tracking_error": tracking_error,
            "information_ratio": (float(active.mean() * PERIODS / tracking_error)
                                  if tracking_error > 1e-12 else None),
        })
    return out


def peer_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    """Descriptive ranks within a category and identical observation window.

    This uses NAV returns, NOT EGM's official gross-return evaluation methodology.
    """
    required = {"fund_id", "category", "total_return"}
    if not required <= set(frame.columns) or frame.fund_id.duplicated().any():
        raise ValueError("Expected unique funds with category and period return")
    out = frame.copy()
    out["peer_rank"] = out.groupby("category")["total_return"].rank(
        ascending=False, method="min"
    ).astype(int)
    out["peer_count"] = out.groupby("category")["fund_id"].transform("size")
    out["peer_median"] = out.groupby("category")["total_return"].transform("median")
    return out


def rebalance_portfolio(prices: pd.DataFrame, weights: dict[str, float],
                        cost_bps: float = 5.0) -> pd.DataFrame:
    """Buy at initial NAV, monthly start-of-period rebalance using previous close.

    Holdings drift between rebalances. Cost = one-way turnover * bps / 10,000.
    Initial allocation has no cost. Output starts at 100 before first return.
    """
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.index.has_duplicates:
        raise ValueError("Unique datetime index required")
    if not prices.index.is_monotonic_increasing or len(prices) < 3:
        raise ValueError("At least three increasing dates required")
    if not weights or not set(weights) <= set(prices.columns):
        raise ValueError("Unknown or missing allocation IDs")
    target = np.array(list(weights.values()), dtype=float)
    if (not np.isfinite(target).all() or (target < 0).any()
            or not np.isclose(target.sum(), 1.0, atol=1e-9, rtol=0)):
        raise ValueError("Non-negative weights must sum to one")
    if not np.isfinite(cost_bps) or not 0 <= cost_bps <= 1000:
        raise ValueError("Cost must be between 0 and 1000 bps")
    matrix = prices[list(weights)].to_numpy(dtype=float)
    if not np.isfinite(matrix).all() or (matrix <= 0).any():
        raise ValueError("Aligned positive NAV observations required; no forward fill")
    holdings = 100.0 * target
    rows = [{"date": prices.index[0], "nav": 100.0, "turnover": 0.0, "cost": 0.0}]
    for i in range(1, len(matrix)):
        turnover = cost = 0.0
        if prices.index[i].to_period("M") != prices.index[i - 1].to_period("M"):
            before = holdings.sum()
            turnover = float(np.abs(holdings / before - target).sum() / 2)
            cost = float(before * turnover * cost_bps / 10000)
            holdings = (before - cost) * target
        holdings *= matrix[i] / matrix[i - 1]
        rows.append({"date": prices.index[i], "nav": float(holdings.sum()),
                     "turnover": turnover, "cost": cost})
    return pd.DataFrame(rows).set_index("date")


def contribution_projection(monthly: float, years: int, annual_return: float,
                            inflation: float, escalation: float = 0.0) -> list[dict]:
    """Month-start deposits; effective annual assumptions; year-start escalation.

    Returns are assumed after fund expenses. State contributions, vesting,
    withholding tax and contract-specific deductions are outside this model.
    """
    vals = [monthly, annual_return, inflation, escalation]
    if not all(math.isfinite(x) for x in vals):
        raise ValueError("Assumptions must be finite")
    if isinstance(years, bool) or not isinstance(years, int) or not 1 <= years <= 40:
        raise ValueError("Years must be an integer between 1 and 40")
    if monthly < 0 or not -0.95 <= annual_return <= 1 or not 0 <= inflation <= 1:
        raise ValueError("Invalid contribution, return or inflation")
    if not 0 <= escalation <= 1:
        raise ValueError("Escalation must be between 0 and 100%")
    monthly_growth = (1 + annual_return) ** (1 / 12)
    balance = paid = 0.0
    rows = [{"month": 0, "balance": 0.0, "paid": 0.0, "real_balance": 0.0}]
    for month in range(1, years * 12 + 1):
        contribution = monthly * (1 + escalation) ** ((month - 1) // 12)
        paid += contribution
        balance = (balance + contribution) * monthly_growth
        rows.append({"month": month, "balance": balance, "paid": paid,
                     "real_balance": balance / (1 + inflation) ** (month / 12)})
    return rows


def walk_forward_var(nav: Sequence[float], window: int = 252) -> dict:
    """Each forecast uses only returns strictly before the tested observation."""
    daily = returns(nav)
    if isinstance(window, bool) or not isinstance(window, int) or window < 20:
        raise ValueError("Window must be an integer of at least 20 observations")
    if len(daily) <= window:
        raise ValueError("Not enough observations for out-of-sample validation")
    forecasts = [historical_tail(daily[i - window:i])["var95"]
                 for i in range(window, len(daily))]
    violations = -daily[window:] > np.asarray(forecasts)
    n = len(violations)
    count = int(violations.sum())
    return {"window": window, "tested_days": n, "exceptions": count,
            "exception_rate": count / n, "reference_rate": 0.05,
            "forecasts": forecasts, "violations": violations.tolist()}
