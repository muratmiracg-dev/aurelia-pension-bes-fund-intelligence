# Change notes

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
