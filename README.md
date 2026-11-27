# PeakPlan

Final group project for **CMU 95-835: Time Series Forecasting in Python, Fall 2026**.

PeakPlan uses monthly Las Vegas hotel statistics to forecast occupancy and average daily room rates (ADR). The product provides market context for independent hotel managers' pricing and budgeting decisions. Forecasts describe a geographic market, rather than an individual hotel's bookings or optimal price.

The archived data cover **January 2019 through September 2026**. A 12-month forecast from that cutoff covers **October 2026 through September 2027**.

## Repository structure

```text
notebooks/
  reference/        Original teammate notebook, including its saved outputs
data/
  raw/lvcva/        Original annual Excel files and their ZIP archive
  processed/        Clean monthly tables produced by the analysis
src/                Shared data, forecasting, and evaluation code
app/                Future application code
outputs/
  forecasts/        Forecast tables for the interface and presentation
  evaluation/       Backtest predictions, metrics, and model comparisons
  figures/          Figures selected for the report, interface, or slides
docs/
  source_reports/   Official reports accompanying the source data
wireframe/          Prototype links, interface designs, and user flows
slides/             Presentation materials
.local/             Private notes and temporary work; ignored by Git
```

See [data/README.md](data/README.md) for source details and units, and [wireframe/README.md](wireframe/README.md) for the current prototype.

## Python environment

Use a separate **Python 3.11** environment in this repository. The analysis package versions match the existing course environment used to check the data notebook. Direct dependencies are pinned in `requirements.txt`.

Run from the repository root on macOS or Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, create and activate the environment with:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

In VS Code, select this repository's `.venv` interpreter and use it as the notebook kernel. JupyterLab is not required for the VS Code workflow.

The original notebook is preserved at [notebooks/reference/Team5_PeakPlan.ipynb](notebooks/reference/Team5_PeakPlan.ipynb). Its original loading cell still downloads and extracts a Drive ZIP using `gdown`; the notebook has not been rewritten. The same source workbooks are already available in `data/raw/lvcva/` for subsequent local analysis. Reference-notebook download files are ignored by Git.

## Working conventions

- Add new modeling and backtesting notebooks directly under `notebooks/`. Keep the original reference notebook intact.
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
