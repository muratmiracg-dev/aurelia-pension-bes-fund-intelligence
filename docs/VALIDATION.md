# Validation record

Local execution: **20 September 2026**.

| Check | Observed result |
|---|---|
| Python environment | Python 3.12, NumPy 2.3.5, pandas 2.2.3 |
| `python -m unittest discover -s tests -v` | **25 tests passed** |
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

CI and CodeQL workflow files are supplied; remote successful runs are not claimed
until the repository has been uploaded to GitHub and Actions has executed them.
