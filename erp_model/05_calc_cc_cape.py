"""
Calculates CC-CAPE (Current Constituents CAPE) following Research Affiliates (Feb 2025).

The key idea: the S&P 500 systematically adds expensive, high-growth companies
and drops cheaper, slower-growth ones. Traditional CAPE calculates its 10-year
average earnings using the constituents as they existed at each point in time.
CC-CAPE fixes this by calculating CAPE at the individual company level for each
current constituent, then aggregating with a market-cap weighted average.

NOTE: This module requires constituent-level data which is not freely available
for long histories. This is a placeholder/framework for when such data is available.
"""
import pandas as pd
import numpy as np
import os
import config


def load_constituent_data():
    """
    Load S&P 500 constituent data.

    Expected format:
    - ticker: company symbol
    - weight: market-cap weight in index
    - earnings_10yr_real: company's 10yr avg real earnings
    - market_cap: company market cap

    Returns None if data not available.
    """
    path = config.DATA_RAW + "sp500_constituents.csv"
    if not os.path.exists(path):
        return None

    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        print(f"Warning: Could not load constituent data: {e}")
        return None


def calculate_cc_cape(constituents_df):
    """
    Calculate CC-CAPE from constituent-level data.

    Parameters
    ----------
    constituents_df : DataFrame
        Must have columns: ticker, weight, earnings_10yr_real, market_cap

    Returns
    -------
    dict with cc_cape and diagnostics
    """
    if constituents_df is None:
        return None

    df = constituents_df.copy()

    # Calculate company-level CAPE
    df["company_cape"] = df["market_cap"] / df["earnings_10yr_real"]

    # Handle negative earnings (companies with losses)
    df = df[df["earnings_10yr_real"] > 0]

    # Renormalize weights
    df["weight_norm"] = df["weight"] / df["weight"].sum()

    # Weighted average CAPE
    cc_cape = (df["company_cape"] * df["weight_norm"]).sum()

    return {
        "cc_cape": cc_cape,
        "n_constituents": len(df),
        "top_contributors": df.nlargest(10, "weight_norm")[
            ["ticker", "weight_norm", "company_cape"]
        ].to_dict("records"),
    }


def main():
    print("=" * 60)
    print("  ERP Model — CC-CAPE Calculator")
    print("=" * 60)
    print()

    # Try to load constituent data
    constituents = load_constituent_data()

    if constituents is None:
        print("  CC-CAPE requires constituent-level data which is not available.")
        print()
        print("  To use CC-CAPE, you need to provide a CSV file at:")
        print(f"    {config.DATA_RAW}sp500_constituents.csv")
        print()
        print("  Required columns:")
        print("    - ticker: company symbol (e.g., 'AAPL')")
        print("    - weight: market-cap weight in index (e.g., 0.07)")
        print("    - earnings_10yr_real: 10-year avg real earnings per share")
        print("    - market_cap: company market cap")
        print()
        print("  Potential data sources:")
        print("    - S&P Global (paid)")
        print("    - Bloomberg (paid)")
        print("    - Scrape from SEC filings + Wikipedia weights (free but manual)")
        print()
        print("  Skipping CC-CAPE calculation.")
        return

    result = calculate_cc_cape(constituents)

    print(f"  CC-CAPE: {result['cc_cape']:.1f}")
    print(f"  Based on {result['n_constituents']} constituents")
    print()
    print("  Top 10 contributors by weight:")
    for item in result["top_contributors"]:
        print(f"    {item['ticker']:6s}  weight: {item['weight_norm']:.2%}  CAPE: {item['company_cape']:.1f}")

    # If we have traditional CAPE, calculate the spread
    try:
        fv_path = config.DATA_PROCESSED + "monthly_with_fairvalue.csv"
        if os.path.exists(fv_path):
            df = pd.read_csv(fv_path, index_col=0, parse_dates=True)
            latest_cape = df["cape"].dropna().iloc[-1]
            cape_spread = result["cc_cape"] - latest_cape
            print()
            print(f"  Traditional CAPE: {latest_cape:.1f}")
            print(f"  CAPE Spread (CC - Traditional): {cape_spread:.1f}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
