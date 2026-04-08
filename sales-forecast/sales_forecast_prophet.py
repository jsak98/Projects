"""
Sales Forecasting with Meta Prophet
=====================================
Dataset: Walmart Store Sales (train.csv)
Columns: Store, Dept, Date, Weekly_Sales, IsHoliday

This script:
  1. Loads and explores the data
  2. Aggregates weekly sales (total across all stores/depts, or per store)
  3. Trains a Prophet model with holiday effects
  4. Evaluates using cross-validation
  5. Forecasts future sales
  6. Plots and saves results

Requirements:
    pip install prophet pandas matplotlib plotly
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
DATA_PATH    = "train.csv"          # path to CSV
OUTPUT_DIR   = "forecast_outputs"   # folder where results are saved
FORECAST_WEEKS = 52                 # how many weeks ahead to forecast

# Granularity:
#   "total"   → aggregate all stores & departments
#   "store"   → one model per store (aggregated across depts)
#   "dept"    → one model for a specific store+dept combo
GRANULARITY  = "total"

# Only used when GRANULARITY == "store" or "dept"
TARGET_STORE = 1
TARGET_DEPT  = 1


# ─────────────────────────────────────────────
# 1.  LOAD DATA
# ─────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    print(f"  Loaded {len(df):,} rows")
    print(f"    Date range : {df['Date'].min().date()} → {df['Date'].max().date()}")
    print(f"    Stores     : {df['Store'].nunique()}")
    print(f"    Departments: {df['Dept'].nunique()}")
    print(f"    Missing    : {df.isnull().sum().sum()}\n")
    return df


# ─────────────────────────────────────────────
# 2.  AGGREGATE TIME SERIES
# ─────────────────────────────────────────────
def prepare_series(df: pd.DataFrame, granularity: str,
                   store: int = None, dept: int = None) -> pd.DataFrame:
    """
    Returns a DataFrame with columns  ds (date) and  y (sales).
    Prophet requires exactly these names.
    """
    if granularity == "total":
        ts = (df.groupby("Date")["Weekly_Sales"]
                .sum()
                .reset_index()
                .rename(columns={"Date": "ds", "Weekly_Sales": "y"}))
        print(f"  Aggregated: total chain sales — {len(ts)} weeks\n")

    elif granularity == "store":
        ts = (df[df["Store"] == store]
                .groupby("Date")["Weekly_Sales"]
                .sum()
                .reset_index()
                .rename(columns={"Date": "ds", "Weekly_Sales": "y"}))
        print(f"  Aggregated: Store {store} — {len(ts)} weeks\n")

    elif granularity == "dept":
        ts = (df[(df["Store"] == store) & (df["Dept"] == dept)]
                .groupby("Date")["Weekly_Sales"]
                .sum()
                .reset_index()
                .rename(columns={"Date": "ds", "Weekly_Sales": "y"}))
        print(f"  Aggregated: Store {store}, Dept {dept} — {len(ts)} weeks\n")

    else:
        raise ValueError("granularity must be 'total', 'store', or 'dept'")

    # Clip negative sales (returns/adjustments) to 0
    ts["y"] = ts["y"].clip(lower=0)
    ts = ts.sort_values("ds").reset_index(drop=True)
    return ts


# ─────────────────────────────────────────────
# 3.  BUILD HOLIDAY DATAFRAME
# ─────────────────────────────────────────────
def build_holidays(df: pd.DataFrame) -> pd.DataFrame:
    """
    Use the IsHoliday flag already in the data.
    Prophet expects a DataFrame with  holiday, ds  columns.
    You can also add standard US holidays for robustness.
    """
    holiday_dates = df[df["IsHoliday"]]["Date"].drop_duplicates()

    holidays = pd.DataFrame({
        "holiday": "super_bowl_or_holiday",
        "ds": holiday_dates,
        "lower_window": -1,   # effect starts 1 day before
        "upper_window": 1,    # effect lasts 1 day after
    })

    event_map = {
        "Super Bowl"  : ["2010-02-12", "2011-02-11", "2012-02-10"],
        "Labor Day"   : ["2010-09-10", "2011-09-09", "2012-09-07"],
        "Thanksgiving": ["2010-11-26", "2011-11-25"],
        "Christmas"   : ["2010-12-31", "2011-12-30"],
    }
    rows = []
    for name, dates in event_map.items():
        for d in dates:
            rows.append({"holiday": name, "ds": pd.Timestamp(d),
                         "lower_window": -2, "upper_window": 2})

    named = pd.DataFrame(rows)
    holidays = pd.concat([named], ignore_index=True)
    print(f"  Holidays defined: {holidays['holiday'].nunique()} event types, "
          f"{len(holidays)} rows\n")
    return holidays


# ─────────────────────────────────────────────
# 4.  TRAIN PROPHET MODEL
# ─────────────────────────────────────────────
def train_prophet(ts: pd.DataFrame, holidays: pd.DataFrame):
    """
    Fit a Prophet model.
    Key hyperparameters explained inline — adjust for your dataset.
    """
    from prophet import Prophet

    model = Prophet(
        # ── Trend ──────────────────────────────────────────────────────
        growth="linear",            # "linear" for steady growth; "logistic" if you
                                    # have a known market cap (add 'cap' col to ts)
        changepoint_prior_scale=0.05,   # How flexible the trend is.
                                        # Higher → more bends (risk: overfitting)
                                        # Lower  → smoother trend
        n_changepoints=25,          # Number of potential trend change-points

        # ── Seasonality ────────────────────────────────────────────────
        yearly_seasonality=True,    # Auto-detected; True forces it on
        weekly_seasonality=False,   # Data is already weekly aggregated
        daily_seasonality=False,

        seasonality_prior_scale=10, # Strength of seasonality effect
        seasonality_mode="multiplicative",  # multiplicative works well when
                                            # amplitude grows with the level

        # ── Holidays ───────────────────────────────────────────────────
        holidays=holidays,
        holidays_prior_scale=10,    # How much holidays can shift the forecast

        # ── Uncertainty ────────────────────────────────────────────────
        interval_width=0.95,        # 95 % confidence interval
        mcmc_samples=0,             # 0 -> fast MAP estimation; >0 -> full Bayesian
    )

    model.fit(ts)
    print("  Prophet model trained\n")
    return model


# ─────────────────────────────────────────────
# 5.  CROSS-VALIDATION (walk-forward)
# ─────────────────────────────────────────────
def cross_validate_model(model, ts: pd.DataFrame):
    """
    Prophet's built-in cross-validation:
      initial  = size of first training window
      period   = spacing between cutoff dates
      horizon  = forecast horizon to evaluate
    """
    from prophet.diagnostics import cross_validation, performance_metrics

    total_days = (ts["ds"].max() - ts["ds"].min()).days
    initial_days = int(total_days * 0.6)   # 60 % for first training window
    horizon_days = 7 * 8                   # evaluate 8-week horizon

    print(f"[...] Running cross-validation  (initial={initial_days}d, "
          f"period=30d, horizon={horizon_days}d) — may take ~30–60 s …")

    cv_df = cross_validation(
        model,
        initial=f"{initial_days} days",
        period="30 days",
        horizon=f"{horizon_days} days",
        parallel="processes",
    )

    metrics = performance_metrics(cv_df)

    print("\n  Cross-validation metrics (first 5 horizons):")
    print(metrics[["horizon", "mae", "rmse", "mape"]].head(5).to_string(index=False))
    print()

    return cv_df, metrics


# ─────────────────────────────────────────────
# 6.  FORECAST
# ─────────────────────────────────────────────
def make_forecast(model, periods: int) -> pd.DataFrame:
    """
    Generate a future dataframe and predict.
    freq="W-FRI" because Walmart weeks end on Friday in this dataset.
    """
    future = model.make_future_dataframe(periods=periods, freq="W-FRI")
    forecast = model.predict(future)
    print(f"  Forecast generated: {periods} weeks ahead\n")
    return forecast


# ─────────────────────────────────────────────
# 7.  PLOTS
# ─────────────────────────────────────────────
def plot_forecast(model, forecast: pd.DataFrame, ts: pd.DataFrame,
                  output_dir: str, title_suffix: str = ""):
    os.makedirs(output_dir, exist_ok=True)

    # ── 7a. Main forecast plot ──────────────────────────────────────
    fig1, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(forecast["ds"], forecast["yhat_lower"],
                    forecast["yhat_upper"], alpha=0.2, color="steelblue",
                    label="95 % CI")
    ax.plot(forecast["ds"], forecast["yhat"], color="steelblue",
            linewidth=1.8, label="Forecast")
    ax.scatter(ts["ds"], ts["y"], color="black", s=6, zorder=5,
               label="Actual (train)")
    # Shade forecast region
    cutoff = ts["ds"].max()
    ax.axvline(cutoff, color="red", linestyle="--", linewidth=1.2,
               label="Forecast start")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    ax.set_title(f"Weekly Sales Forecast — Prophet{title_suffix}", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Weekly Sales ($)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend()
    plt.tight_layout()
    path1 = os.path.join(output_dir, "forecast.png")
    fig1.savefig(path1, dpi=150)
    print(f"  Saved: {path1}")
    plt.close(fig1)

    # ── 7b. Components plot ─────────────────────────────────────────
    fig2 = model.plot_components(forecast)
    path2 = os.path.join(output_dir, "components.png")
    fig2.savefig(path2, dpi=150, bbox_inches="tight")
    print(f"  Saved: {path2}")
    plt.close(fig2)


def plot_cv_metrics(metrics: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, col, color in zip(axes,
                               ["mae", "rmse", "mape"],
                               ["#4C72B0", "#DD8452", "#55A868"]):
        ax.plot(metrics["horizon"].dt.days, metrics[col],
                marker="o", color=color, linewidth=2)
        ax.set_title(col.upper())
        ax.set_xlabel("Horizon (days)")
        ax.set_ylabel(col.upper())
        ax.grid(alpha=0.3)
    fig.suptitle("Cross-Validation Metrics vs Forecast Horizon", fontsize=13,
                 fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "cv_metrics.png")
    fig.savefig(path, dpi=150)
    print(f"  Saved: {path}")
    plt.close(fig)


# ─────────────────────────────────────────────
# 8.  SAVE RESULTS
# ─────────────────────────────────────────────
def save_results(forecast: pd.DataFrame, output_dir: str):
    cols = ["ds", "yhat", "yhat_lower", "yhat_upper",
            "trend", "yearly", "holidays"]
    # Only keep columns that exist (holidays col may be absent if no dates match)
    cols = [c for c in cols if c in forecast.columns]
    out = forecast[cols].copy()
    out.rename(columns={"ds": "Date", "yhat": "Forecast",
                        "yhat_lower": "Lower_95", "yhat_upper": "Upper_95"},
               inplace=True)
    path = os.path.join(output_dir, "forecast_results.csv")
    out.to_csv(path, index=False)
    print(f"  Saved: {path}\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Sales Forecasting with Meta Prophet")
    print("=" * 55 + "\n")

    # 1. Load
    df = load_data(DATA_PATH)

    # 2. Prepare series
    ts = prepare_series(df, GRANULARITY, store=TARGET_STORE, dept=TARGET_DEPT)

    # 3. Holidays
    holidays = build_holidays(df)

    # 4. Train
    model = train_prophet(ts, holidays)

    # 5. Cross-validate
    cv_df, metrics = cross_validate_model(model, ts)

    # 6. Forecast
    forecast = make_forecast(model, FORECAST_WEEKS)

    # Suffix for plot titles
    suffix_map = {
        "total": " (All Stores)",
        "store": f" (Store {TARGET_STORE})",
        "dept" : f" (Store {TARGET_STORE}, Dept {TARGET_DEPT})",
    }

    # 7. Plots
    plot_forecast(model, forecast, ts, OUTPUT_DIR, suffix_map[GRANULARITY])
    plot_cv_metrics(metrics, OUTPUT_DIR)

    # 8. Save CSV
    save_results(forecast, OUTPUT_DIR)

    # ── Print the next N weeks ────────────────────────────────────
    future_only = forecast[forecast["ds"] > ts["ds"].max()][
        ["ds", "yhat", "yhat_lower", "yhat_upper"]
    ].copy()
    future_only.columns = ["Week", "Forecast", "Lower_95", "Upper_95"]
    print(f"{'─'*55}")
    print(f"  Next {FORECAST_WEEKS}-week forecast preview")
    print(f"{'─'*55}")
    print(future_only.head(10).to_string(index=False,
          float_format=lambda x: f"${x:>13,.0f}"))
    print("\n  All done! Check the 'forecast_outputs/' folder.\n")


if __name__ == "__main__":
    main()