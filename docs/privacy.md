# Privacy

This repository is privacy-first:
- raw Garmin exports are local-only
- `data/` artifacts are ignored by Git
- sanitize outputs are the default sharing/analysis boundary

## Rules

- Never commit anything under raw export paths.
- Use Stage 1 sanitize outputs for notebooks, reports, and sharing.
- Treat identifier-like columns as restricted unless explicitly removed.

## What is safe to publish

- Safe by default: source code, docs, tests, and non-sensitive repository metadata.
- Sanitized parquet is appropriate for local analysis, but avoid publishing personal time-series directly without careful aggregation/anonymization.
- Curated figures should be intentionally selected and stored in `docs/img`; full exploratory figure dumps should remain local.

## Git guardrails

- `data/` is gitignored and should remain local-only.
- Figures are exported to reports/figures/ (gitignored).
- The local pre-commit hook prevents accidental staging of raw exports.

## Sanitization gate

Run before analysis/sharing:

```bash
garmin-analytics sanitize
```

Primary sanitize outputs:
- `data/processed/daily_sanitized.parquet`
- `data/processed/daily_uds_sanitized.parquet`
- `data/processed/sleep_sanitized.parquet`
- `data/processed/sanitize_report.json`

## Local pre-commit hook

Use the canonical setup guide in [docs/precommit_hook.md](precommit_hook.md).

Notes:
- Git hooks are local-only and not versioned by default.
- Keep privacy checks close to your local workflow and CI policy.
