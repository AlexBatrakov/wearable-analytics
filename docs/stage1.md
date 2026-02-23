# Stage 1 — Sanitize, Data Dictionary, and Quality

Stage 1 is the privacy and data-quality gate between ingestion and EDA.

## Commands

```bash
garmin-analytics sanitize
garmin-analytics data-dictionary
garmin-analytics quality
```

Alternative module mode:

```bash
PYTHONPATH=src python -m garmin_analytics sanitize
PYTHONPATH=src python -m garmin_analytics data-dictionary
PYTHONPATH=src python -m garmin_analytics quality
```

## Outputs

Sanitize:
- `data/processed/daily_sanitized.parquet`
- `data/processed/daily_uds_sanitized.parquet`
- `data/processed/sleep_sanitized.parquet`
- `data/processed/sanitize_report.json`

Data dictionary:
- `reports/data_dictionary.csv`
- `reports/data_dictionary.md`
  - includes a full column inventory plus summary sections for key analysis signals and quality-relevant columns
- `reports/data_dictionary_summary.md` (optional; generated with `--markdown-mode summary|both`)

Quality:
- `reports/quality_summary.md`
- `reports/suspicious_days.csv`
- `reports/suspicious_days_artifacts.csv` (artifact-focused ranking of suspicious days)
- `data/processed/daily_quality.parquet` (written by default; disable with `--no-parquet`)

## Current Stage 1 metrics

- rows: **580**
- date range: **2023-05-26 to 2026-02-05**
- strict labels: **good 90.52%, partial 3.79%, bad 5.69%**
- loose labels: **good 93.45%, partial 0.86%, bad 5.69%**
- corrupted stress-only days: **21 (3.62%)**

## Interpretation

- Quality labels describe **day-level analysis readiness / signal coverage** (not medical-grade measurement quality).
- Strict labels emphasize robust day completeness for downstream analysis.
- Loose labels allow borderline but still usable days.
- `corrupted_stress_only_day` flags artifact-like records with near-full-day stress but missing corroborating signals; these are forced to `bad`.
- `has_bodybattery_end` is intentionally used in scoring (not just any Body Battery presence) because end-of-day Body Battery is more useful for day-outcome analysis.
- Days with Body Battery `start` present but `end` missing usually indicate partial coverage (watch was worn earlier, then powered off / battery depleted), not a parser failure.

## Data dictionary notes

- `reports/data_dictionary.md` now serves as both a full column appendix and a decision-support report:
  - `Executive summary`
  - `Key analysis signals`
  - `Quality-relevant columns`
  - `Quality-readiness rationale`
- Use the quality-relevant coverage table to justify or recalibrate quality thresholds when needed.
- If you want a shorter recruiter-/developer-friendly report, run:
  - `garmin-analytics data-dictionary --markdown-mode both`
  - this writes `reports/data_dictionary_summary.md` in addition to the full appendix

## Quality calibration snapshot (current dataset)

Quick sensitivity checks (strict labels) used to validate that defaults are reasonable and not arbitrary:

| setting | good | partial | bad | note |
| --- | --- | --- | --- | --- |
| `strict_min_score=4` (current) | 525 | 22 | 33 | balanced default |
| `strict_min_score=5` | 438 | 109 | 33 | too strict for current coverage |
| `stress_any_hours=6` (current) | 525 | 22 | 33 | balanced default |
| `stress_any_hours=12` | 509 | 35 | 36 | noticeably harsher |
| `steps_min=50` (current) | 525 | 22 | 33 | low sensitivity in current data |
| `steps_min=200` | 523 | 24 | 33 | only minor shift |

## Sanitize notes

- `sleep_sanitized.parquet` may be identical to `sleep.parquet` on some exports if the sleep ingestion step already excluded identifier-like nested fields.

## Suspicious-day diagnostics notes

- `reports/suspicious_days.csv` is optimized for general debugging (sparse/low-quality rows first).
- `reports/suspicious_days_artifacts.csv` is optimized for artifact hunting (e.g., high/full-day stress with missing corroborating signals).

## Exit criteria

Proceed to Stage 2 after:
- sanitize outputs are generated,
- dictionary reports are available,
- quality summary and suspicious-day diagnostics are reviewed.

For command options and thresholds, see [CLI](cli.md).
