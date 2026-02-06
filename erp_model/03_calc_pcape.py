"""
Calculates P-CAPE (Payout-adjusted CAPE) following Haghani & White (2024).

The key idea: retained earnings compound and grow future EPS.
Traditional CAPE ignores this. P-CAPE corrects for it.
"""
import pandas as pd
import numpy as np
import os
import config


def calculate_pcape(df, window_years=None):
    """
    For each month, look back over the CAPE window and adjust each
    historical earnings observation for the compounding effect of
    retained earnings.

    Parameters
    ----------
    df : DataFrame with columns: real_earnings, earnings_yield, payout_ratio, real_price
    window_years : int, lookback window (default from config)

    Returns
    -------
    DataFrame with p_cae, p_cape, p_caey columns added
    """
    if window_years is None:
        window_years = config.CAPE_WINDOW

    window_months = window_years * 12

    print(f"Calculating P-CAPE with {window_years}-year window...")

    p_cae_values = []

    for i in range(len(df)):
        if i < window_months:
            p_cae_values.append(np.nan)
            continue

        # Look back over the window
        adjusted_earnings = []
        for j in range(window_months):
            lookback_idx = i - j
            months_ago = j
            years_ago = months_ago / 12

            # Historical values at time (i - j)
            real_e = df["real_earnings"].iloc[lookback_idx]
            ey = df["earnings_yield"].iloc[lookback_idx]
            pr = df["payout_ratio"].iloc[lookback_idx]

            if pd.isna(real_e) or pd.isna(ey) or pd.isna(pr):
                adjusted_earnings.append(np.nan)
                continue

            # Compound retained earnings forward to present
            # Growth rate from retention = earnings_yield * (1 - payout_ratio)
            retention_growth = ey * (1 - pr)
            adjustment_factor = (1 + retention_growth) ** years_ago

            adjusted_earnings.append(real_e * adjustment_factor)

        # P-CAE = average of adjusted earnings over the window
        valid = [e for e in adjusted_earnings if not np.isnan(e)]
        if len(valid) > window_months * 0.8:  # Require 80% coverage
            p_cae_values.append(np.mean(valid))
        else:
            p_cae_values.append(np.nan)

        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(df)} months...")

    df = df.copy()
    df["p_cae"] = p_cae_values
    df["p_cape"] = df["real_price"] / df["p_cae"]
    df["p_caey"] = 1 / df["p_cape"]  # P-CAPE earnings yield

    return df


def main():
    print("=" * 60)
    print("  ERP Model — P-CAPE Calculator")
    print("=" * 60)
    print()

    # Load master dataset
    input_path = config.DATA_PROCESSED + "monthly_master.csv"
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Master dataset not found at {input_path}. Run 02_build_dataset.py first."
        )

    df = pd.read_csv(input_path, index_col=0, parse_dates=True)
    print(f"Loaded {len(df)} months of data")
    print()

    # Calculate P-CAPE
    df = calculate_pcape(df)

    # Save
    output_path = config.DATA_PROCESSED + "monthly_with_pcape.csv"
    df.to_csv(output_path)

    print()
    print("=" * 60)
    print("  P-CAPE Calculation Complete")
    print("=" * 60)

    # Show latest values
    latest = df.dropna(subset=["p_cape"]).iloc[-1]
    print(f"  Latest date:           {latest.name.strftime('%Y-%m')}")
    print(f"  Traditional CAPE:      {latest['cape']:.1f}")
    print(f"  P-CAPE:                {latest['p_cape']:.1f}")
    print(f"  P-CAPE Earnings Yield: {latest['p_caey']:.2%}")
    print()
    print(f"  Saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
