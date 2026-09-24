# Validation record

Local regression update: **24 September 2026**.

| Check | Observed result |
|---|---|
| Python environment | Python 3.12, NumPy 2.3.5, pandas 2.2.3 |
| `python -m unittest discover -s tests -v` | **32 tests passed** |
| `node tests/test_engine.cjs` | **543 numerical comparisons passed**, plus boundary assertions |
| Demo generation | **30 funds; 1,230 NAV dates; 36,900 fund-price observations** |
| Input quality gates | **10 passed** |
| Generated HTML / JavaScript | Embedded JSON parses; both executable scripts pass Node syntax check |
| SQL reconciliation | 36,900 NAV rows; 90 fund-period rows; 30 initial null returns |

The tests cover known-answer return and drawdown calculations, fractional Expected
Shortfall, category rank isolation, undefined information ratio, beginning-of-month
annuity timing, contribution escalation, inflation deflation, invalid input domains,
holdings drift, rebalance transaction costs, weight validation and look-ahead exclusion.

The data suite covers byte-identical regeneration, full-grid reconciliation, missing
observations, duplicate keys, required external provenance, mixed data classes and
orphan fund identifiers. JavaScript metrics are reconciled against the generated Python
results for every fund and every period. This is computational validation, not evidence
that synthetic results predict actual investment outcomes.

## Remaining browser acceptance checks

Cloud browser navigation to local HTML was rejected by the environment's URL security
policy. No workaround was attempted. Visual appearance, mobile layout and direct UI
interaction have **not been browser-verified** in this delivery. The following manual
checks should be completed in a normal desktop browser before public promotion:

- Open all five navigation screens.
- Change category and period; verify selected fund, date range and chart update together.
- Select a different fund and each portfolio example.
- Move every scenario slider; verify zero growth produces contributions-only balance.
- Export a comparison CSV; compare selected category and period with the screen.
- Check keyboard navigation and narrow-screen overflow.

## GitHub execution evidence

The initial publication passed [analytics CI on Python 3.11 and 3.12](https://github.com/muratmiracg-dev/aurelia-pension-bes-fund-intelligence/actions/runs/36000463013).
The initial [Python and JavaScript CodeQL run](https://github.com/muratmiracg-dev/aurelia-pension-bes-fund-intelligence/actions/runs/36000463006) also completed successfully.
For the status of subsequent commits, use the live workflow badges in the README.
Local regression counts above describe the updated suite; they do not retroactively
change the test count in an earlier GitHub run.

## Added regression cases

- CLI validation returns a JSON summary without changing any input bytes or creating artifacts.
- Missing inputs produce a machine-readable failure and exit code 2.
- Invalid explicit input prevents serving an existing stale report.
- Fund identifiers preserve leading zeros and the literal label `NA`.
- Unsupported category mappings fail during ingestion, before report generation.
- Blank observation dates and source cutoff dates fail validation.

A clean build with the updated ingestion code reproduced the bundled dashboard, JSON
and metric CSVs byte-for-byte. The SQL examples returned 5 category leaders, 3 portfolio
summaries and 30 fund observation counts against the bundled warehouse. The header illustration
is a project identity graphic, not a screenshot or a depiction of investment returns.
