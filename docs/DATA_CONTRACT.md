# CSV contract and data lineage

UTF-8 comma-separated files. Ratios are decimals, not percentages. Dates use
`YYYY-MM-DD`. All prices are positive total-return NAV, in TRY, after fund expenses.

| File | Required columns |
|---|---|
| `funds.csv` | `fund_id,name,category,currency,data_class,source_url,source_asof` |
| `fund_prices.csv` | `date,fund_id,nav` |
| `benchmarks.csv` | `date,category,nav,data_class,source_url,source_asof` |

Optional metadata `annual_fee_assumption` describes the synthetic generator only.
It is not separately deducted by the analytical pipeline.

`fund_id` is unique in metadata and unique with date in prices. The five supported
categories are `Hisse Senedi`, `Borçlanma Araçları`, `Altın`, `Para Piyasası`, `Değişken`.
These are project groupings, not authoritative EGM peer assignments.

All funds and category benchmarks require at least 757 identical NAV dates. No
orphan fund IDs, missing dates, duplicate keys, zero/negative/infinite NAV or silent
currency conversion is allowed. Every source cutoff must cover its observations.

`data_class` must be uniformly `SYNTHETIC` or `EXTERNAL`, including benchmarks.
External records require HTTPS provenance URLs and source-as-of dates. Source URLs
are recorded evidence, not downloaded by the application. The user must independently
validate distribution rights, split/distribution adjustments and comparability.

## Generated evidence

- `fund_metrics.csv`: fund × period; category rank, return and risk metrics.
- `portfolio_metrics.csv`: full-period portfolio metrics and walk-forward diagnostics.
- `data_quality.csv`: validation gates completed by ingestion.
- `dashboard_data.json`: common dates, full NAV histories, metrics and configuration.
- `manifest.json`: source CSV SHA-256 hashes, data class, dates and counts.
- `aurelia_pension.sqlite`: relational data and SQL reporting views.

Run a rebuild from the root after modifying input contracts. A default build regenerates
the synthetic files; `--data-dir` never rewrites supplied CSV inputs.

## Preflight validation

Run `python -m aurelia_pension validate --data-dir PATH --json` before building.
Validation reads the existing three CSVs, applies the same ingestion gates as the build,
and writes no files. Success returns JSON with `status: PASS`, counts, date coverage and
the ten controls. A data or filesystem error returns `status: FAIL`, an error message
and process exit code 2. Source URLs are provenance declarations, not independently
verified by these gates.

Identifiers are parsed as text in both metadata and prices: leading zeros and literal
`NA` are preserved. Empty observation dates and empty source cutoffs are rejected.
All five supported categories must be present during preflight, before any artifact
output is created. `serve --data-dir PATH` always validates and rebuilds the supplied
data before opening the localhost server.
