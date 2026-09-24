-- Run against artifacts/aurelia_pension.sqlite.
-- Ratios are decimals; percentage outputs below multiply them by 100.

-- Category-relative leaders: ties at rank 1 are intentionally retained.
SELECT category, fund_id, name, peer_rank, peer_count,
       ROUND(100 * total_return, 2) AS return_pct,
       ROUND(100 * volatility, 2) AS annual_volatility_pct,
       ROUND(100 * max_drawdown, 2) AS max_drawdown_pct
FROM vw_peer_performance
WHERE period = '1Y' AND peer_rank = 1
ORDER BY category, fund_id;

-- All-period illustrative portfolio risk and out-of-sample VaR diagnostics.
SELECT name, ROUND(100 * annual_return, 2) AS annual_return_pct,
       ROUND(100 * max_drawdown, 2) AS max_drawdown_pct,
       ROUND(100 * var95, 2) AS daily_var95_pct,
       ROUND(100 * es95, 2) AS daily_es95_pct,
       tested_days, exceptions, ROUND(100 * exception_rate, 2) AS exception_rate_pct
FROM portfolio_metrics
ORDER BY annual_return DESC;

-- Input reconciliation: one first-date NULL return per fund is expected.
SELECT fund_id, COUNT(*) AS nav_observations,
       COUNT(daily_return) AS return_observations,
       SUM(CASE WHEN daily_return IS NULL THEN 1 ELSE 0 END) AS initial_nulls
FROM vw_daily_return
GROUP BY fund_id
ORDER BY fund_id;
