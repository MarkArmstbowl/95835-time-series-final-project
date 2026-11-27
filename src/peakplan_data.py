"""Build the model input from the locally archived LVCVA workbooks."""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

DATA_START = pd.Timestamp("2019-01-01")
DATA_CUTOFF = pd.Timestamp("2026-09-01")
TARGET_COLUMNS = {
    "overall": {"occupancy": "Total Occupancy", "adr": "Average Daily Room Rate (ADR)"},
    "strip": {"occupancy": "Strip Occupancy", "adr": "Strip ADR"},
    "downtown": {"occupancy": "Downtown Occupancy", "adr": "Downtown ADR"},
}
REGION_NAMES = {
    "overall": "Las Vegas Overall",
    "strip": "Strip",
    "downtown": "Downtown",
}
METRIC_UNITS = {"occupancy": "fraction", "adr": "USD"}


def load_monthly_targets(raw_dir: str | Path) -> pd.DataFrame:
    """Return one row per (region, month), with occupancy and ADR as published."""
    raw_dir = Path(raw_dir)
    indicators = [label for pair in TARGET_COLUMNS.values() for label in pair.values()]
    annual_frames = []

    for year in range(DATA_START.year, DATA_CUTOFF.year + 1):
        path = raw_dir / f"LVCVA_{year}.xlsx"
        sheet = pd.read_excel(path, sheet_name=f"Las Vegas {year}", header=None)
        labels = sheet[0].fillna("").astype(str).str.split().str.join(" ")
        # Use the date headers and the actual-values block from data preparation.
        start = labels[labels.eq("Tourism Indicators")].index[0]
        end = labels[labels.eq("Change from Previous Year") & (labels.index > start)].index[0]
        dates = sheet.loc[start, sheet.loc[start].map(lambda value: isinstance(value, datetime))]
        months = pd.DatetimeIndex(dates.tolist(), name="month")
        expected = pd.date_range(f"{year}-01-01", periods=12, freq="MS")
        if not months.equals(expected):
            raise ValueError(f"Unexpected monthly headers in {path.name}")

        target_rows = labels.iloc[start + 1 : end]
        target_rows = target_rows[target_rows.isin(indicators)]
        if target_rows.duplicated().any() or set(target_rows) != set(indicators):
            raise ValueError(f"Missing or repeated model targets in {path.name}")
        monthly = sheet.loc[target_rows.index, dates.index].T.copy()
        monthly.index = months
        monthly.columns = target_rows.to_list()
        annual_frames.append(monthly)

    market = pd.concat(annual_frames).loc[DATA_START:DATA_CUTOFF]
    if not market.index.equals(pd.date_range(DATA_START, DATA_CUTOFF, freq="MS")):
        raise ValueError("The archive must contain one row per observed month")
    market = market.apply(pd.to_numeric, errors="raise")

    regions = []
    for region, columns in TARGET_COLUMNS.items():
        pair = market[list(columns.values())].set_axis(list(columns), axis=1)
        regions.append(pair.assign(region=region).reset_index())
    targets = pd.concat(regions, ignore_index=True)[["region", "month", "occupancy", "adr"]]
    if not np.isfinite(targets[["occupancy", "adr"]].to_numpy()).all():
        raise ValueError("The target series contain missing or nonfinite observations")
    if not (targets["occupancy"].between(0, 1).all() and targets["adr"].gt(0).all()):
        raise ValueError("Check target units: occupancy is a fraction and ADR is positive USD")
    return targets
