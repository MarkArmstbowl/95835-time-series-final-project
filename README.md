# PeakPlan

Final group project for **CMU 95-835: Time Series Forecasting in Python, Fall 2026**.

PeakPlan uses monthly Las Vegas hotel statistics to forecast occupancy and average daily room rates (ADR). The product provides market context for independent hotel managers' pricing and budgeting decisions. Forecasts describe a geographic market, rather than an individual hotel's bookings or optimal price.

The archived data cover **January 2019 through September 2026**. A 12-month forecast from that cutoff covers **October 2026 through September 2027**.

## Repository structure

```text
notebooks/
  01_data_preparation.ipynb                 Data source, cleaning, and exploration
  02_model_development.ipynb               Candidate models and forecast previews
  03_backtesting_and_model_selection.ipynb Planned evaluation and final export
data/
  raw/lvcva/        Eight original annual Excel files
  processed/        Clean monthly tables produced by the analysis
src/                Shared data, forecasting, and evaluation code
app/                Future application code
outputs/
  forecasts/        Forecast tables for the interface and presentation
  evaluation/       Backtest predictions, metrics, and model comparisons
  figures/          Figures selected for the report, interface, or slides
docs/
  modeling_handoff.md  Evaluation instructions and output schemas
  source_reports/   Official reports accompanying the source data
wireframe/          Prototype links, interface designs, and user flows
slides/             Presentation materials
.local/             Private notes and temporary work; ignored by Git
```

See [data/README.md](data/README.md) for source details and units, and [wireframe/README.md](wireframe/README.md) for the current prototype.

## Python environment

Use **Python 3.11 or newer** in a virtual environment. The notebooks were tested on Python 3.11, and dependency resolution was also checked with Python 3.13 on macOS. Check which interpreter your terminal uses before creating the environment. The direct dependencies are pinned in [requirements.txt](requirements.txt).

Run from the repository root on macOS or Linux:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, create and activate the environment with:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the version command reports Python 3.10 or earlier, use a compatible interpreter to create the environment, for example `python3.13` or `py -3.13`. In VS Code, select the repo's `.venv` as the notebook kernel.

## Analysis notebooks

1. [01_data_preparation.ipynb](notebooks/01_data_preparation.ipynb) documents the full LVCVA data preparation and exploration, with saved results. Rerunning its original setup downloads the source workbooks from Drive through `gdown`.
2. [02_model_development.ipynb](notebooks/02_model_development.ipynb) reads the eight workbooks in `data/raw/lvcva/` and can run independently. Open it in VS Code, select the repo's Python kernel, and run all cells to regenerate the two CSVs.

3. The planned `03_backtesting_and_model_selection.ipynb` reads [monthly_targets.csv](data/processed/monthly_targets.csv) directly and calls the shared models at historical cutoffs. Follow the [Part 3 handoff](docs/modeling_handoff.md) for the notebook layout, evaluation protocol, and expected files.

The [candidate forecast CSV](outputs/forecasts/candidate_forecasts.csv) is available for interface previews. After model selection, the app reads `outputs/forecasts/final_forecasts.csv` for the outlook and `outputs/evaluation/app_accuracy.csv` for historical accuracy.

## Working conventions

- Keep the data preparation, modeling, and backtesting notebooks in numbered order under `notebooks/`.
- Put reusable Python functions in `src/` so modeling, evaluation, and the interface can share the same logic.
- Preserve `data/raw/` unchanged. Write standardized tables to `data/processed/`.
- Use project-relative paths. Resolve paths from the repository root or a notebook's location rather than hard-coding a machine-specific directory.
- Save forecasts, evaluation tables, and presentation figures under the corresponding `outputs/` folders. Small reviewed CSVs and figures can be committed.
- Keep source-region labels, dates, units, and prediction-interval definitions in exported results. Match interface claims to the final backtest evidence.
- Store chat transcripts, scratch notebooks, large temporary runs, and local recordings in `.local/`.
- Coordinate notebook edits through task branches and pull requests, with a designated person integrating each shared notebook.

`app/` is reserved for application code. The current Figma prototype already exists; the implementation framework and any additional web dependencies will be chosen when that work begins.

## Deliverables and milestones

| Milestone | Deadline | Contents |
|---|---|---|
| Part A | December 2, 2026 | In-class product and investment pitch, maximum 10 minutes, with backtest evidence and the investment-use plan |
| Part B | December 9, 2026, 6:30 PM EST | Presentation recording, wireframe, and a reproducible Jupyter notebook with the required data |

The project combines the business case, user needs and differentiation, forecasting evidence, product workflow, and the funding plan. A runnable application demo is an optional extension to the required interface prototype.
