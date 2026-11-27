# Part 3 — Backtesting, model selection, and final forecast export

Build `notebooks/03_backtesting_and_model_selection.ipynb`. Run and save it with its outputs, produce the evaluation files listed below, and export the selected forecasts and accuracy summary for the interface. The notebook should answer how well each candidate would have predicted the next 12 months from a historical cutoff, whether it improves on repeating last year, and which model to use for each market and target.

The first two notebooks document the data and provide the models. Part 3 can start directly from the historical CSV and the shared forecasting functions. Use the repository environment described in the [root README](../README.md).

## Inputs already available

| File | How to use it |
|---|---|
| [monthly_targets.csv](../data/processed/monthly_targets.csv) | Main input for Part 3. It has 279 rows, one per region and observed month, and columns `region`, `month`, `occupancy`, and `adr`. |
| [peakplan_models.py](../src/peakplan_models.py) | Import the candidate catalog, minimum history lengths, window selector, forecast function, and demand-label function. |
| [peakplan_data.py](../src/peakplan_data.py) | Import the data cutoff, region names, and metric units. It also contains the local workbook reader. |
| [01_data_preparation.ipynb](../notebooks/01_data_preparation.ipynb) | Data provenance, cleaning, and exploratory plots. Read the saved notebook to understand the dataset. |
| [02_model_development.ipynb](../notebooks/02_model_development.ipynb) | Model rationale, example forecasts, and the export code. Run it if you need to regenerate the two CSVs from the local Excel files. |
| [candidate_forecasts.csv](../outputs/forecasts/candidate_forecasts.csv) | The 1,440-row future preview. Use it for the interface schema and candidate comparison examples. Historical scores require new forecasts fitted at the backtest cutoffs. |

Each of `downtown`, `strip`, and `overall` has 93 observed months from January 2019 through September 2026. Occupancy is stored as a fraction and ADR in USD. All dates are month starts. The scope is six monthly market series, with two targets per region.

The 10 candidates in `MODEL_SPECS` are `seasonal_naive`, `naive`, `ets_level`, `ets_seasonal`, `ets_damped`, `arima`, `sarima`, `robust_stl_ets`, `harmonic_ar`, and `seasonal_var`. The shared code carries out transformations, fits, inverse transformations, and interval calculation. The two history policies in `TRAINING_WINDOWS` retain all available history or start in January 2022.

## Evaluation protocol

Use the four rolling origins below as the default. Each predicts 12 months in a single call. Keep the cutoffs and scoring rules explicit if the team chooses a different protocol.

| Last training month (`origin`) | Test months | Full / recent training months |
|---|---|---:|
| 2024-12-01 | January–December 2025 | 72 / 36 |
| 2025-03-01 | April 2025–March 2026 | 75 / 39 |
| 2025-06-01 | July 2025–June 2026 | 78 / 42 |
| 2025-09-01 | October 2025–September 2026 | 81 / 45 |

For each region, target, candidate, origin, and window, slice the observations at the origin and then apply the window. Fit the candidate from that slice and join the actuals after it returns. A 12-month forecast must always start one month after the origin. Use the published observations as the actuals, including published pandemic values whenever relevant. The archived series includes retrospective revisions, so describe these as backtests on a fixed data snapshot.

The default grid has 480 forecast calls and up to 5,760 prediction rows. Each fully evaluated region, target, model, and window has 48 origin–horizon pairs. The test months overlap, so a given observation can appear at different horizons. Keep those forecasts distinct and describe the count as forecast–actual pairs.

### Setup and one working example

Start the notebook in the repo root or in `notebooks/`. Use the same project-root resolution as `02`. This example validates the expected shape before running the full grid.

```python
from pathlib import Path
import sys

import pandas as pd

root = Path.cwd().resolve()
input_path = Path("data/processed/monthly_targets.csv")
if not (root / input_path).is_file():
    root = root.parent
if not (root / input_path).is_file():
    raise FileNotFoundError("Open the notebook from the PeakPlan repo. Run 02 if the CSV is missing.")
sys.path.insert(0, str(root))

from src.peakplan_models import forecast, select_training_window

targets = pd.read_csv(root / input_path, parse_dates=["month"])
history = (
    targets.loc[targets["region"].eq("downtown")]
    .set_index("month")[["occupancy", "adr"]]
    .sort_index()
)
origin = pd.Timestamp("2024-12-01")
train = select_training_window(history.loc[:origin], "since_2022")
prediction = forecast(train, metric="occupancy", model="ets_damped", steps=12)
comparison = prediction.join(history["occupancy"].rename("actual"), validate="one_to_one")
assert comparison.index.equals(pd.date_range("2025-01-01", periods=12, freq="MS"))
assert comparison["actual"].notna().all()
```

Pass both target columns to keep the same interface for all candidates. `forecast()` returns a month-start index and the columns `horizon`, `forecast`, `lower`, and `upper`, in the input metric's original unit. The default interval has a nominal level of 0.80. Read `prediction.attrs["fit_warnings"]` before restructuring the result. Record model-specific `ModelFitError` failures with the attempted configuration and the error message. Handle insufficient training history as a separately logged skip after checking `MODEL_SPECS[model].min_months`. Surface data, date, and programming errors so they can be fixed.

## Suggested notebook layout

Use a short Markdown cell to introduce each section. Keep setup, reusable functions, execution, tables, and figures in separate cells. Add a brief interpretation after each main result.

| Section | Suggested cells and visible outputs |
|---|---|
| **1. Forecast question** | Markdown describing the three markets, two targets, 12-month use case, and how rolling origins simulate earlier forecast decisions. |
| **2. Setup and data checks** | Import packages and shared project modules in one cell. Load the CSV and build one indexed history per region in a second. Show each region's first and last months and number of observations. Check keys, monthly continuity, completeness, and units. |
| **3. Backtest design** | Define origins, horizon, interval level, region IDs, and model/window combinations. Display a small table of training dates, test dates, and counts. Explain the full and recent windows and the seasonal naïve baseline. |
| **4. Run the forecasts** | In one or two cells define a single-run helper that slices, fits, and aligns actuals. Run the grid in a separate cell. Show attempted, successful, skipped, and failed counts and a compact sample of the prediction table. Check forecast start, horizon sequence, expected number of actuals, bounds, and uniqueness. |
| **5. Score and compare** | Add one cell for point-error and interval calculations and one for aggregation. Show per-series MAE and RMSE rankings, seasonal naïve comparison, and results by origin. Show interval coverage and width together. Use a separate table or chart for differences by horizon. |
| **6. Choose the final methods** | Show one row per region and target with the chosen model, window, baseline comparison, and short rationale. Discuss any material tradeoff between average errors, performance across origins, and interval reliability. |
| **7. Visual evidence** | Plot actual, seasonal naïve, and selected forecast from the latest origin for Downtown. Use separate panels for occupancy and ADR. Add a compact six-series plot or table comparing the selected model with the baseline. Label dates and units, then explain a few visible misses or consistent patterns. |
| **8. Refit and export** | Refit each choice on the applicable window through September 2026. Create the app forecast and accuracy tables, preview them, verify their schemas and counts, and write the files below. Show the forecast period and exported paths. |
| **9. Conclusions** | Summarize the strongest improvement, the most important remaining forecast limitation, and what to say on the app and in the class presentation. Describe accuracy at the market level. |

## Metrics and model choice

- Compute errors as forecast minus actual. For occupancy, multiply by 100 for MAE, RMSE, and interval width in percentage points. For ADR, report these in USD. Compute MAPE as `100 * mean(abs(error / actual))` in original units over nonzero actuals and report its contributing count if any zeros occur.
- Pool the absolute and squared errors across forecast–actual pairs for each region, target, model, and window. Compute RMSE from the pooled squared errors. Include per-origin MAE and RMSE in the notebook so an average does not hide a bad window.
- Compute interval coverage as the share of actuals inside the inclusive bounds. Show the share in percent next to average interval width and the nominal 80% level. Treat this as diagnostic evidence given the small, overlapping test windows.
- Use `seasonal_naive` as the main point-forecast benchmark. Report both its absolute error and the percentage change from baseline, using `100 * (baseline_mae - model_mae) / baseline_mae` when the baseline MAE is positive. Label positive values as improvement. Baseline point forecasts are identical across the windows at common origins, while the interval widths can differ.
- As a default, select the lowest pooled MAE among candidates with all four origins and 48 scored forecasts for that series. If two MAEs tie to numerical precision, prefer seasonal naïve when it is among the ties, then use lower RMSE. For otherwise equivalent runs of the same model, the recent window is the default tie break. Record the chosen rule and any exception with its rationale.
- Keep incomplete runs visible in the metrics and fit log. Use common successful dates for any secondary comparison involving incomplete candidates, and label the smaller sample. Leave seasonal naïve eligible as the final method when the evidence favors it.

## Deliverables and destinations

All paths below are relative to the repository root. Create missing output directories in the notebook. The notebook should regenerate these products from a fresh kernel and write to the same paths when rerun.

| Path | Required contents for the handoff |
|---|---|
| `notebooks/03_backtesting_and_model_selection.ipynb` | Executed notebook with the protocol, code, metrics, figures, selection rationale, and export checks. |
| `outputs/evaluation/backtest_predictions.csv` | One row per successful `region, metric, model, training_window, origin, month`. Include `horizon, train_start, unit, actual, forecast, lower, upper, interval_level`. |
| `outputs/evaluation/backtest_metrics.csv` | One pooled row per `region, metric, model, training_window`. Include `error_unit, n_origins, n_forecasts, mae, rmse, mape_pct, mape_n, coverage_pct, mean_interval_width, interval_level`. Retain the count for incomplete candidates. |
| `outputs/evaluation/fit_log.csv` | One row per attempted configuration, with `region, metric, model, training_window, origin, train_start, n_train, status, warnings, message`. Use statuses such as `ok`, `skipped`, and `failed` consistently. |
| `outputs/evaluation/model_selection.csv` | Six rows keyed by `region, metric`. Include `model, training_window, error_unit, mae, rmse, baseline_mae, mae_improvement_pct, coverage_pct, n_origins, n_forecasts, rationale`. |
| `outputs/forecasts/final_forecasts.csv` | 72 rows keyed by `region, metric, month`, using the same columns as the candidate CSV. October 2026 through September 2027 for each series. |
| `outputs/evaluation/app_accuracy.csv` | Six rows keyed by `region, metric`. Include `model, training_window, error_unit, mae, rmse, baseline_mae, mae_improvement_pct, coverage_pct, interval_level, n_origins, n_forecasts, test_start, test_end`. |
| `outputs/figures/` | Save the Downtown actual-versus-forecast comparison and a selected-vs-baseline figure here if they are used in the presentation or app. Keep the notebook figures visible as well. |

Use `percentage_points` and `USD` for `error_unit`. Use month-start dates for `test_start` and `test_end`, based on the actuals scored for that selection. Fields with the `_pct` suffix use percentage values, while `interval_level` uses a fraction.

### Final forecast fields

For each region and metric, call `forecast()` with the selected window after slicing through `DATA_CUTOFF`. Use the resulting month index in the export. Add the same metadata as the candidate CSV.

```text
region,metric,unit,model,training_window,train_start,origin,month,horizon,
forecast,lower,upper,interval_level,last_year_actual,demand_band
```

Get `last_year_actual` from the same market and metric 12 months before the forecast date. For occupancy, call `demand_labels(prediction["forecast"], train["occupancy"])`. The labels use the most recent 36 observations for that market and are relative to its recent history. Leave the label blank for ADR. Keep fractions and USD in the CSV and format them at display time. If a selected model cannot refit, document the failure and the next eligible choice in the selection table before exporting.

The app reads the selected forecast table for the calendar and the accuracy summary for the accuracy view. One forecast row per market, metric, and month lets the interface filter by market and date without choosing a model itself. Use `last_year_actual` and the prediction bounds for comparison and uncertainty in the detail view. What-if calculations use the occupancy forecast as a scenario input together with the user's room count and room rate.

## Checks before handing off

- Run all cells from a fresh kernel using the local CSV and shared code. Confirm that rerunning the notebook writes all exports to the documented locations.
- Confirm every scored forecast begins one month after its origin, contains the intended number of months, and joins to actuals for the matching region and date. Count successful and failed runs and verify that the reference points equal the corresponding training observations from one year earlier.
- Confirm that the final table has six complete 12-row groups, a September 2026 origin, horizons 1–12, finite values, and ordered bounds. Check occupancy values and bounds in `[0, 1]` and ADR values and bounds greater than zero.
- Verify that every accuracy and forecast row agrees with the selected model/window and its evaluation results. Show exactly what metric and unit stands behind any number quoted in the app or slides.
- In the handoff message, link the notebook and output files and give a short explanation of the selected models, their performance against the baseline, and any limitations the product or presentation should mention.
