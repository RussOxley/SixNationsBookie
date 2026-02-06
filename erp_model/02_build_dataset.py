"""
Loads raw data, cleans it, and produces a single merged monthly dataset.
"""
import pandas as pd
import numpy as np
import os
import config
from utils import parse_shiller_date


def load_shiller():
    """Load and parse Shiller data."""
    path = config.DATA_RAW + "shiller.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Shiller data not found at {path}. Run 01_fetch_data.py first."
        )

    shiller = pd.read_csv(path)

    # Parse Shiller's date format (e.g., 2024.01 = Jan 2024)
    shiller["date"] = pd.to_datetime(shiller["date"].apply(parse_shiller_date))
    shiller = shiller.set_index("date")

    # Resample to month-start to ensure consistent alignment
    shiller = shiller.resample("MS").last()

    return shiller


def load_fred_series():
    """Load all available FRED series."""
    series_dict = {}

    for name in config.FRED_SERIES.keys():
        path = config.DATA_RAW + f"fred_{name}.csv"
        if os.path.exists(path):
            try:
                s = pd.read_csv(path, index_col=0, parse_dates=True)
                s.columns = [name]
                s = s.resample("MS").last()  # Align to month-start
                series_dict[name] = s
                print(f"  Loaded {name}: {len(s)} observations")
            except Exception as e:
                print(f"  Warning: Could not load {name}: {e}")
        else:
            print(f"  Skipping {name} — file not found")

    return series_dict


def build_monthly_dataset():
    """Build the master monthly dataset."""
    print("Loading Shiller data...")
    df = load_shiller()
    print(f"  Loaded: {len(df)} months")

    print("\nLoading FRED series...")
    fred_series = load_fred_series()

    # Merge FRED series
    for name, series in fred_series.items():
        df = df.join(series, how="left")

    print("\nCalculating derived fields...")

    # Dividend payout ratio
    df["payout_ratio"] = (df["dividend"] / df["earnings"]).clip(0, 1)

    # Earnings yield (from CAPE)
    df["earnings_yield"] = 1 / df["cape"]

    # Forward returns (for evaluation — these are the "answers")
    for horizon in config.FORECAST_HORIZONS:
        months = horizon * 12
        # Using real total return price from Shiller
        df[f"fwd_{horizon}yr_real_return"] = (
            (df["real_tr_price"].shift(-months) / df["real_tr_price"])
            ** (1 / horizon) - 1
        )
        print(f"  Calculated {horizon}-year forward returns")

    # Save
    output_path = config.DATA_PROCESSED + "monthly_master.csv"
    df.to_csv(output_path)
    print(f"\nMaster dataset saved: {len(df)} months, {len(df.columns)} columns")
    print(f"  Path: {output_path}")

    return df


def main():
    print("=" * 60)
    print("  ERP Model — Dataset Builder")
    print("=" * 60)
    print()

    df = build_monthly_dataset()

    print()
    print("=" * 60)
    print("  Dataset Summary")
    print("=" * 60)
    print(f"  Date range: {df.index.min().strftime('%Y-%m')} to {df.index.max().strftime('%Y-%m')}")
    print(f"  Columns: {list(df.columns)}")
    print()


if __name__ == "__main__":
    main()
