# Methodology

## Intended user and decision scope

A pension analytics or investment reporting analyst comparing fund behavior and
illustrative allocations. The tool supplies analytical evidence, not a personal
recommendation or an executable fund-switch instruction.

## Returns and peer comparisons

NAV simple return is `P[t] / P[t-1] - 1`. Period return is `P[end]/P[start]-1`.
Annualization uses 252 observations: `growth ** (252 / number_of_returns) - 1`.
This convention is explicit; the generated calendar is weekdays, not the official
Turkish market calendar. All funds and benchmarks must share a complete date grid.
For indexed pandas series, benchmark-relative metrics require exact date-index
equality; equal-length series with different dates are rejected rather than compared
by position. No prices are forward-filled. 1Y and 3Y mean 252 and 756 return
observations.

NAV is assumed net of fund expenses. The synthetic generator deducts an illustrative
expense drag once. Period NAV returns therefore cannot be substituted for the gross
returns in official EGM performance evaluation. Ranks are descriptive, category-only
and use minimum rank for ties. Category median includes the selected fund.

Category benchmarks are independent synthetic factor series, not the average of fund
prices and not official EGM indices. Excess return is the difference between period
fund and benchmark simple returns. Tracking error is sample standard deviation of
daily active returns times sqrt(252). Information ratio is mean daily active return
times 252 divided by annual tracking error. Zero tracking error returns null.

## Risk

Volatility uses sample standard deviation (`ddof=1`). Maximum drawdown includes the
initial NAV and is reset at the start of the selected analysis window.

One-day historical 95% VaR is the inverted empirical CDF of daily losses at 95%.
Expected Shortfall averages exactly the worst 5% probability mass; a fractional
boundary observation avoids over- or underweighting the tail. Both displayed loss
measures are floored at zero if the sample contains no positive losses.
Historical quantiles do not bound future losses.

## Portfolio accounting

Three fixed allocations are stored in `pipeline.py`, in category order Hisse Senedi,
Borçlanma Araçları, Altın, Para Piyasası, Değişken:

| Example | Equity | Bonds | Gold | Money market | Flexible |
|---|---:|---:|---:|---:|---:|
| Temkinli | 10% | 35% | 10% | 35% | 10% |
| Dengeli | 30% | 25% | 20% | 10% | 15% |
| Büyüme | 55% | 10% | 15% | 5% | 15% |

Select the first alphabetically ordered ID within each category, never the best
performer. Invest 100 NAV units initially without entry cost. Holdings drift with
returns. Before the first return of a new month, rebalance at the preceding close.
One-way turnover is half the sum of absolute differences between current and target
weights. Deduct `portfolio value × turnover × 0.0005`; then allocate the net balance
and apply that day's asset returns. This is a simplified friction assumption, not a
claim about actual BES fund-switch charges or settlement delays.

Hypothetical stresses multiply target weights by explicitly stored category shocks.
They are instantaneous fixed-weight shocks, not scenario paths or probability forecasts.

## Walk-forward risk diagnostic

For each tested day, use only the previous 252 daily returns to calculate VaR.
Count an exception when the realized daily loss strictly exceeds the forecast.
Do not include the tested day in estimation. Report the number of exceptions and
tested observations with a 5% reference rate. There is no pass/fail regulatory claim,
independence test or official traffic-light classification.

## Contribution scenarios

Each contribution is paid at the beginning of the month and participates in that
month's return. Monthly growth is `(1 + annual_assumed_return) ** (1/12)`.
Contribution escalation applies at months 13, 25, etc. Terminal purchasing power is
`terminal nominal balance / (1+annual_inflation)**years`.

The model is deterministic. Returns, inflation and escalation are assumptions, not
forecasts derived from the fund dataset. Total paid contributions are nominal; do
not compare that number directly to real terminal wealth as a measure of real profit.
State contributions, vesting, tax, contract deductions, contribution holidays and
withdrawals are outside the model. Assumed returns are after fund expenses.

## Limits

The fixture has a balanced panel with no fund launches/closures; consequently it
does not address survivorship bias or changing category membership. Synthetic
correlations and stress regimes are design choices. Actual deployment needs point-in-time
fund metadata, licensed observations, settlement rules, independently checked metrics
and human review. External CSV support does not independently verify a supplier's truth.
