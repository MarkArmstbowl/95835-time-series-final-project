# Data

## Source snapshot

The raw files come from the [LVCVA Executive Summary of Southern Nevada Tourism Indicators](https://www.lvcva.com/research/reports/post/lvcva-executive-summary-of-southern-nevada-tourism-indicators/), also linked from the [LVCVA Research Center](https://www.lvcva.com/research/).

`raw/lvcva/` holds the eight original workbooks, `LVCVA_2019.xlsx` through `LVCVA_2026.xlsx`.

The analysis snapshot contains **93 monthly observations, January 2019 through September 2026**. The 2026 workbook has date headers for October through December, but those months have no observations in this snapshot. YTD summaries, revision flags, and the separate year-over-year-change block are not additional monthly observations.

The accompanying August 2026 official PDF is stored under `docs/source_reports/`. It provides source commentary and spot checks; it is not a model-evaluation report.

## Targets and units

| Market segment | Occupancy field | ADR field |
|---|---|---|
| Las Vegas Overall | `Total Occupancy` | `Average Daily Room Rate (ADR)` |
| Strip | `Strip Occupancy` | `Strip ADR` |
| Downtown | `Downtown Occupancy` | `Downtown ADR` |

- Occupancy is stored as a fraction: `0.62` means **62%**. Absolute occupancy errors can be reported in percentage points after multiplying by 100.
- ADR is the average daily rate for sold rooms, in **USD**.
- These are market or segment statistics. Las Vegas Overall includes the broader market; the three entries above are not three independent cities.
- RevPAR and other published indicators are also retained for exploration. Some auxiliary fields have missing or pending values and reporting changes.

## Processing

[01_data_preparation.ipynb](../notebooks/01_data_preparation.ipynb) documents the extraction, label reconciliation, validation, and exploratory analysis. It creates `cleaned_market_indicators` and the two-column overall-market target table `hotel_monthly` in memory.

[02_model_development.ipynb](../notebooks/02_model_development.ipynb) rebuilds the six target series from the same local workbooks and saves them to [monthly_targets.csv](processed/monthly_targets.csv). The CSV has 279 rows, with one row per region and month and columns for occupancy and ADR. Use it directly for the model evaluation.

The key is `region, month`. The region IDs are `overall`, `strip`, and `downtown`. Parse `month` as a date and sort within region before passing its occupancy and ADR history to a model. The [Part 3 handoff](../docs/modeling_handoff.md) shows the exact input shape and a working forecast at a historical cutoff.

Subsequent analysis should write standardized tables to `data/processed/`, retaining dates and units and identifying the selected market segment. The original observations, including the COVID period, remain in `raw/`. Any training-window selection or transformation belongs in the model pipeline and must use only information available at the forecast origin.

The workbooks contain retrospective revisions. Backtests on this archive evaluate a fixed revised snapshot rather than reproducing each historical release vintage.

Raw and small processed data files can be tracked in Git. Keep private or temporary material under `.local/` instead of adding it to this directory.
