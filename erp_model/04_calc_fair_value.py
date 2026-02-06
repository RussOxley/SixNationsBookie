"""
Estimates a 'fair-value' CAPE that accounts for the interest rate
and inflation environment, following the approach of Davis et al.
and Vanguard's methodology.

The key idea: CAPE shouldn't revert to a fixed mean. Its equilibrium
level depends on real rates and inflation. When real rates are low,
a higher CAPE is rationally justified.
"""
import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
import config


def estimate_fair_value_cape(df, training_window_years=None):
    """
    Uses a rolling regression to estimate what CAPE 'should' be
    given current interest rates and inflation.

    Model: ln(CAPE) = a + b1 * real_rate + b2 * trailing_inflation + error

    The gap between actual CAPE and fair-value CAPE is the key
    predictive signal for future returns.
    """
    if training_window_years is None:
        training_window_years = config.FV_TRAINING_WINDOW

    window = training_window_years * 12

    df = df.copy()

    print(f"Calculating fair-value CAPE with {training_window_years}-year training window...")

    # Calculate 10-year trailing inflation (annualised)
    df["trailing_inflation_10y"] = (
        (df["cpi"] / df["cpi"].shift(120)) ** (1 / 10) - 1
    )

    # Real rate proxy: nominal 10Y minus trailing inflation
    # (Use TIPS yield directly when available post-2003)
    if "treasury_10y" in df.columns:
        df["real_rate"] = df["treasury_10y"] / 100 - df["trailing_inflation_10y"]
    else:
        # Fallback to gs10 from Shiller data
        df["real_rate"] = df["gs10"] / 100 - df["trailing_inflation_10y"]

    if "tips_10y" in df.columns:
        tips_mask = df["tips_10y"].notna()
        df.loc[tips_mask, "real_rate"] = df.loc[tips_mask, "tips_10y"] / 100

    df["ln_cape"] = np.log(df["cape"])

    # Rolling regression
    fair_values = pd.Series(index=df.index, dtype=float)

    for i in range(window, len(df)):
        train = df.iloc[i - window:i]
        mask = train[["ln_cape", "real_rate", "trailing_inflation_10y"]].notna().all(axis=1)
        train = train[mask]

        if len(train) < window * 0.5:
            continue

        X = train[["real_rate", "trailing_inflation_10y"]].values
        y = train["ln_cape"].values

        model = LinearRegression()
        model.fit(X, y)

        # Predict fair value at current point
        current = df.iloc[i:i + 1][["real_rate", "trailing_inflation_10y"]].values
        if not np.isnan(current).any():
            fair_values.iloc[i] = np.exp(model.predict(current)[0])

        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(df)} months...")

    df["fair_value_cape"] = fair_values
    df["cape_gap"] = df["cape"] - df["fair_value_cape"]
    df["cape_gap_pct"] = df["cape_gap"] / df["fair_value_cape"]

    return df


def main():
    print("=" * 60)
    print("  ERP Model — Fair-Value CAPE Calculator")
    print("=" * 60)
    print()

    # Load dataset with P-CAPE
    input_path = config.DATA_PROCESSED + "monthly_with_pcape.csv"
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"P-CAPE dataset not found at {input_path}. Run 03_calc_pcape.py first."
        )

    df = pd.read_csv(input_path, index_col=0, parse_dates=True)
    print(f"Loaded {len(df)} months of data")
    print()

    # Calculate fair-value CAPE
    df = estimate_fair_value_cape(df)

    # Save
    output_path = config.DATA_PROCESSED + "monthly_with_fairvalue.csv"
    df.to_csv(output_path)

    print()
    print("=" * 60)
    print("  Fair-Value CAPE Calculation Complete")
    print("=" * 60)

    # Show latest values
    latest = df.dropna(subset=["fair_value_cape"]).iloc[-1]
    print(f"  Latest date:           {latest.name.strftime('%Y-%m')}")
    print(f"  Traditional CAPE:      {latest['cape']:.1f}")
    print(f"  Fair-Value CAPE:       {latest['fair_value_cape']:.1f}")
    print(f"  CAPE Gap:              {latest['cape_gap']:.1f} ({latest['cape_gap_pct']:.1%})")
    print()
    print(f"  Saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
