"""Candidate forecasts that fit only the history passed by the caller."""

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import norm
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.vector_ar.var_model import VAR

from src.peakplan_data import METRIC_UNITS

SEASON = 12
HORIZON = 12
INTERVAL_LEVEL = 0.80
RECENT_START = pd.Timestamp("2022-01-01")
TRAINING_WINDOWS = ("all_history", "since_2022")


@dataclass(frozen=True)
class ModelSpec:
    family: str
    min_months: int
    description: str


MODEL_SPECS = {
    "seasonal_naive": ModelSpec("Baseline", 24, "Repeat the same month last year"),
    "naive": ModelSpec("Baseline", 24, "Repeat the latest observation"),
    "ets_level": ModelSpec("ETS", 24, "Smoothed level"),
    "ets_seasonal": ModelSpec("ETS", 24, "Smoothed level and annual seasonality"),
    "ets_damped": ModelSpec("ETS", 36, "Damped trend and annual seasonality"),
    "arima": ModelSpec("ARIMA", 24, "ARIMA(1,1,0)"),
    "sarima": ModelSpec("ARIMA", 36, "SARIMA(0,1,1)(0,1,1)[12]"),
    "robust_stl_ets": ModelSpec("STL + ETS", 36, "Robust STL with a damped ETS trend"),
    "harmonic_ar": ModelSpec("Dynamic regression", 36, "Annual Fourier terms with AR(1) errors"),
    "seasonal_var": ModelSpec("VAR", 36, "VAR(1) on seasonally differenced occupancy and ADR"),
}


class ModelFitError(RuntimeError):
    """A candidate could not supply usable forecasts for the requested history."""


def select_training_window(history: pd.DataFrame, window: str) -> pd.DataFrame:
    """Apply the window to a history frame that already ends at the forecast origin."""
    if window == "all_history":
        return history
    if window == "since_2022":
        return history.loc[RECENT_START:]
    raise ValueError(f"Unknown training window {window!r}. Use one of {TRAINING_WINDOWS}.")


def _transformed(series: pd.Series, metric: str) -> pd.Series:
    # An empirical boundary adjustment makes a reported 0% or 100% fit on the logit scale.
    if metric == "occupancy":
        return logit(series.clip(0.0001, 0.9999))
    return np.log(series)


def _symmetric_band(center, standard_error, level: float) -> np.ndarray:
    radius = norm.ppf((1 + level) / 2) * np.asarray(standard_error)
    return np.column_stack((center, center - radius, center + radius))


def _ets(series: pd.Series, steps: int, level: float, **options) -> np.ndarray:
    result = ETSModel(series, error="add", **options).fit(disp=False)
    if not result.mle_retvals.get("converged", False):
        raise ModelFitError("ETS optimizer did not converge")
    interval = result.get_prediction(
        start=len(series), end=len(series) + steps - 1, method="exact"
    ).summary_frame(alpha=1 - level)
    return interval[["mean", "pi_lower", "pi_upper"]].to_numpy()


def _fourier(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Calendar predictors are already known for every forecast month."""
    phase = 2 * np.pi * (index.month.to_numpy() - 1) / SEASON
    columns = {}
    for k in (1, 2):
        columns[f"sin{k}"] = np.sin(k * phase)
        columns[f"cos{k}"] = np.cos(k * phase)
    return pd.DataFrame(columns, index=index)


def _arima(series: pd.Series, future: pd.DatetimeIndex, level: float, model: str) -> np.ndarray:
    options = {"order": (1, 1, 0)}
    future_exog = None
    if model == "sarima":
        options = {"order": (0, 1, 1), "seasonal_order": (0, 1, 1, SEASON)}
    elif model == "harmonic_ar":
        options = {"order": (1, 0, 0), "trend": "c", "exog": _fourier(series.index)}
        future_exog = _fourier(future)
    result = SARIMAX(series, **options).fit(disp=False, maxiter=200)
    if not result.mle_retvals.get("converged", False):
        raise ModelFitError("ARIMA optimizer did not converge")
    prediction = result.get_forecast(steps=len(future), exog=future_exog)
    return np.column_stack((prediction.predicted_mean, prediction.conf_int(alpha=1 - level)))


def _seasonal_var(history: pd.DataFrame, steps: int, level: float) -> np.ndarray:
    transformed = pd.DataFrame(
        {metric: _transformed(history[metric], metric) for metric in METRIC_UNITS}
    )
    differences = transformed.diff(SEASON).dropna().asfreq("MS")
    result = VAR(differences).fit(maxlags=1, trend="c")
    if not result.is_stable():
        raise ModelFitError("Seasonally differenced VAR is unstable on this training window")
    forecasts = result.forecast_interval(
        differences.to_numpy()[-result.k_ar :], steps=steps, alpha=1 - level
    )
    # Up to 12 steps, every inversion anchor is a known observation from training.
    anchors = transformed.iloc[-SEASON:].to_numpy()[:steps]
    return np.stack(forecasts, axis=-1) + anchors[:, :, None]


def _model_band(history, metric, model, future, level):
    series = _transformed(history[metric], metric)
    steps = len(future)

    if model == "naive":
        center = np.repeat(series.iloc[-1], steps)
        return _symmetric_band(center, series.diff().std() * np.sqrt(np.arange(1, steps + 1)), level)
    if model == "seasonal_naive":
        center = series.iloc[-SEASON:].to_numpy()[:steps]
        return _symmetric_band(center, series.diff(SEASON).std(), level)
    if model == "ets_level":
        return _ets(series, steps, level)
    if model == "ets_seasonal":
        return _ets(series, steps, level, seasonal="add", seasonal_periods=SEASON)
    if model == "ets_damped":
        return _ets(
            series, steps, level, trend="add", damped_trend=True,
            seasonal="add", seasonal_periods=SEASON,
        )
    if model == "robust_stl_ets":
        decomposition = STL(series, period=SEASON, robust=True).fit()
        adjusted = series - decomposition.seasonal
        band = _ets(adjusted, steps, level, trend="add", damped_trend=True)
        return band + decomposition.seasonal.iloc[-SEASON:].to_numpy()[:steps, None]
    if model == "seasonal_var":
        column = list(METRIC_UNITS).index(metric)
        return _seasonal_var(history, steps, level)[:, column, :]
    return _arima(series, future, level, model)


def forecast(
    history: pd.DataFrame,
    metric: str,
    model: str,
    steps: int = HORIZON,
    interval_level: float = INTERVAL_LEVEL,
) -> pd.DataFrame:
    """Predict from a single region's monthly, already-sliced training history.

    history has a month-start DatetimeIndex and columns occupancy (fraction) and
    adr (USD). Return month, horizon, forecast, lower and upper in original units.
    """
    if metric not in METRIC_UNITS or model not in MODEL_SPECS:
        raise ValueError(f"Unknown metric or model: {metric!r}, {model!r}")
    if not isinstance(steps, int) or not 1 <= steps <= HORIZON or not 0 < interval_level < 1:
        raise ValueError("Use an integer horizon of 1–12 months and an interval level in (0, 1)")
    if len(history) < MODEL_SPECS[model].min_months:
        raise ValueError(f"{model} needs at least {MODEL_SPECS[model].min_months} training months")
    index = history.index
    if not isinstance(index, pd.DatetimeIndex) or not index.equals(
        pd.date_range(index[0], periods=len(index), freq="MS")
    ):
        raise ValueError("History must cover consecutive, ordered month starts")
    needed = list(METRIC_UNITS) if model == "seasonal_var" else [metric]
    values = history[needed].astype(float).asfreq("MS")
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Training observations must be finite")
    if "occupancy" in values and not values["occupancy"].between(0, 1).all():
        raise ValueError("Occupancy must be in [0, 1]")
    if "adr" in values and not values["adr"].gt(0).all():
        raise ValueError("ADR must be positive")

    future = pd.date_range(index[-1] + pd.offsets.MonthBegin(), periods=steps, freq="MS")
    with warnings.catch_warnings(record=True) as fit_warnings:
        warnings.simplefilter("always")
        try:
            band = _model_band(values, metric, model, future, interval_level)
        except (np.linalg.LinAlgError, FloatingPointError) as error:
            raise ModelFitError(str(error)) from error
    with np.errstate(over="ignore"):
        band = expit(band) if metric == "occupancy" else np.exp(band)
    # Baseline points should always equal the actual reference, even at 0% or 100%.
    if model in {"naive", "seasonal_naive"}:
        observed = values[metric]
        band[:, 0] = observed.iloc[-1] if model == "naive" else observed.iloc[-SEASON:].to_numpy()[:steps]
        band[:, 1] = np.minimum(band[:, 1], band[:, 0])
        band[:, 2] = np.maximum(band[:, 2], band[:, 0])
    center, lower, upper = band.T
    if not np.isfinite(band).all() or (lower > center).any() or (center > upper).any():
        raise ModelFitError("The model produced nonfinite values or invalid interval bounds")
    if metric == "adr" and (lower <= 0).any():
        raise ModelFitError("The model produced an unrepresentable positive ADR range")

    result = pd.DataFrame(band, columns=["forecast", "lower", "upper"], index=future)
    result.index.name = "month"
    result.insert(0, "horizon", np.arange(1, steps + 1))
    result.attrs["fit_warnings"] = tuple(dict.fromkeys(str(item.message) for item in fit_warnings))
    return result


def demand_labels(occupancy_forecast: pd.Series, training_occupancy: pd.Series) -> pd.Series:
    """Classify occupancy against the lower/upper terciles of the latest 36 observations."""
    reference = training_occupancy.tail(36)
    if len(reference) < 36:
        raise ValueError("Demand labels need 36 observed months for their reference")
    low, high = reference.quantile([1 / 3, 2 / 3])
    labels = np.select(
        [occupancy_forecast < low, occupancy_forecast > high], ["slow", "busy"], default="normal"
    )
    return pd.Series(labels, index=occupancy_forecast.index, name="demand_band")
