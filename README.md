# Aurelia Pension — BES Fund Intelligence

**Pension fund performance, portfolio risk and contribution-scenario analytics.**

By **Murat Miraç Gedik** · Python · NumPy · pandas · SQL · JavaScript

[Türkçe açıklama](README.tr.md) · [Methodology](docs/METHODOLOGY.md) · [Data contract](docs/DATA_CONTRACT.md) · [Validation](docs/VALIDATION.md)

A reproducible analytical product for a fictional Turkish pension research team.
It connects category-relative fund comparison, historical downside risk, monthly
portfolio rebalancing, walk-forward VaR diagnostics and inflation-aware contribution
scenarios in a self-contained, five-screen browser application.

**All included fund identities, prices, benchmarks and outcomes are synthetic.**
The product demonstrates analytical methods. It does not give personal investment
advice, determine suitability or reproduce the official EGM evaluation process.

## Open the application

Download the repository/archive and open
[`artifacts/Aurelia_Pension_BES_Dashboard.html`](artifacts/Aurelia_Pension_BES_Dashboard.html)
in a modern desktop browser. No installation, login, API key, external CDN or network
connection is needed for the bundled report. Some mobile file-preview apps disable
JavaScript; use an actual browser or the local server below.

The report is an interactive application: category, period, fund and model-portfolio
selections update the charts and tables; contribution inputs recalculate immediately;
the current fund comparison can be exported to CSV. It is a generated snapshot, not a
live market feed.

## Business questions

- How does a fund compare with peers of the same category over identical dates?
- Is excess return accompanied by greater volatility or drawdown?
- How do three fixed allocations behave after monthly rebalancing costs?
- How often does a historical VaR estimate fail on subsequent observations?
- How do contribution growth, assumed returns and inflation change retirement savings?

## Implemented scope

| Area | Implementation |
|---|---|
| Universe | 30 fictional funds, 5 categories, 1,230 common NAV dates |
| Period | 3 January 2022–18 September 2026, weekday-only simulated calendar |
| Fund analytics | Period return, annualized return/volatility, max drawdown, tracking error, information ratio |
| Peer comparison | Category-only ranks and median; same start/end observations |
| Downside risk | One-day historical 95% VaR and fractional-tail Expected Shortfall |
| Portfolio | Three predetermined allocations; drifted holdings, monthly rebalance, 5 bps one-way turnover cost |
| Model monitoring | 252-observation historical VaR estimated strictly before each test day |
| Stress | Four transparent hypothetical category shocks at target portfolio weights |
| Savings | Month-start contribution, annual contribution escalation, inflation-adjusted terminal value |
| Warehouse | SQLite fact/dimension tables, reporting views and window-function return query |
| Delivery | Offline HTML application, raw CSVs, derived CSVs, JSON evidence, automated tests |

The first alphabetically ordered fund in each category is selected for the model
portfolios. There is no retrospective performance-based fund selection or claimed
portfolio optimization. The allocations are examples, not participant risk profiles.

## Rebuild

Python 3.11 or newer and Node 20+ for JavaScript validation:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python -m aurelia_pension build
python -m unittest discover -s tests -v
node tests/test_engine.cjs
```

Run commands from the repository root. The generator uses seed `20260920`.
Input hashes are recorded in `artifacts/manifest.json`.

Optional local serving:

```bash
python -m aurelia_pension serve --port 8765
```

Open `http://127.0.0.1:8765/Aurelia_Pension_BES_Dashboard.html`.
The server binds to localhost and is intended only for local review.

## Bring your own licensed data

```bash
python -m aurelia_pension build --data-dir /absolute/path/to/validated/csvs
```

Follow the [data contract](docs/DATA_CONTRACT.md) exactly. The external adapter is
file-based; no EGM/TEFAS scraping or API integration is claimed. External sources need
provenance URLs and source cutoff dates. Missing dates fail validation instead of being
silently forward-filled. Use externally supplied data only when you have the necessary
usage rights and have checked the suitability of category and benchmark mappings.

## Repository map

```text
src/aurelia_pension/  Financial calculations, data contracts and deterministic build
web/                 Application template and independently testable JS engine
data/demo/           Synthetic fund metadata, NAVs and benchmark observations
artifacts/           Working report, SQLite, metrics, quality checks and hashes
sql/                 Analytical views
tests/               Financial invariants, data controls, Python/JS reconciliation
docs/                Methodology, source register, data dictionary and validation
.github/             CI, CodeQL and dependency-update configuration
```

## Evidence and boundaries

The local Python suite has 25 passing tests. Browser-side calculations reconcile with
Python across 543 numerical comparisons plus boundary checks. These tests verify
specific calculations, not real-world predictive performance. Interactive visual/browser
QA was blocked by the execution environment's local-file navigation policy; see the
remaining manual acceptance checklist in `docs/VALIDATION.md`.

The following are explicitly excluded: statutory state-contribution entitlement,
vesting, withholding tax, contract-specific deductions, personal suitability, automated
fund switches and official regulatory reporting. The assumed fund NAV already reflects
fund expenses; do not deduct the model fee again.

EGM's official performance evaluation uses gross-return rules and peer-group thresholds.
This product uses descriptive NAV-return ranks. [Official method](https://www.egm.org.tr/fonlar/fon-performans-degerlendirme-sistemi/fon-performans-degerlendirme-yontemi/).

## License

Code and generated synthetic fixtures: [MIT](LICENSE). Third-party data retains its own
rights; the source register is methodological context, not a redistribution license.
