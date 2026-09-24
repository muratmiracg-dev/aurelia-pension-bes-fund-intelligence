CREATE INDEX IF NOT EXISTS ix_nav_entity_date ON fact_fund_nav(fund_id, date);
CREATE INDEX IF NOT EXISTS ix_benchmark_date ON fact_benchmark_nav(category, date);
DROP VIEW IF EXISTS vw_peer_performance;
CREATE VIEW vw_peer_performance AS
SELECT m.fund_id, f.name, m.category, m.period, m.total_return,
       m.annual_return, m.volatility, m.max_drawdown, m.var95, m.es95,
       m.peer_rank, m.peer_count, m.peer_median, m.excess_return,
       f.data_class, f.source_url, f.source_asof
FROM fund_metrics m JOIN dim_fund f ON m.fund_id = f.fund_id;

DROP VIEW IF EXISTS vw_daily_return;
CREATE VIEW vw_daily_return AS
SELECT date, fund_id, nav,
       nav / LAG(nav) OVER (PARTITION BY fund_id ORDER BY date) - 1 AS daily_return
FROM fact_fund_nav;
