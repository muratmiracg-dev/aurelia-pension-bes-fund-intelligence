# Change notes

## 1 November 2026 — Committed report brought in line with current controls

### Fixed
- The bundled dashboard, `manifest.json`, `dashboard_data.json`, `data_quality.csv` and
  SQLite snapshot were generated before the *Unique fund names* control was added and
  still reported 10 of 11 ingestion gates. They are regenerated from the current code.
- README, Turkish summary, validation record and data contract now state 43 Python tests
  and 11 ingestion controls.
- The *Veri & yöntem* screen now HTML-escapes the reporting date range like every other
  data-derived string (defence in depth for `--data-dir` inputs; flagged by CodeQL).

### Added
- `tests/test_artifacts.py`: rebuilds the report in a temporary directory and fails if the
  committed demo inputs or text artifacts differ, so CI catches a stale snapshot.

Financial formulas, model weights and fund-level results are unchanged.

## 24 September 2026 — Documentation and ingestion reliability

### Added
- English README: project banner, live CI badges, guided walkthrough, architecture,
  metric conventions, SQL examples, command reference and troubleshooting.
- Turkish documentation for validation, external inputs and review workflows.
- Read-only `validate` command with optional JSON output and explicit exit status.
- Executable SQLite examples for peer leaders, portfolio risk and data reconciliation.
- Seven regression tests; 32 Python tests in total.

### Fixed
- `serve --data-dir` now rebuilds explicitly supplied inputs before serving.
  Invalid inputs stop startup instead of displaying an older snapshot.
- CSV identifiers preserve leading zeros and literal text labels such as `NA`.
- Category compatibility is enforced at ingestion, including standalone validation.
- Blank observation dates and source cutoffs are rejected explicitly.

Financial formulas, model weights and the bundled synthetic snapshot are unchanged.
