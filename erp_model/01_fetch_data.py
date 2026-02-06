"""
Fetches all data from free sources and saves to data/raw/.
Run this first. Re-run periodically to get latest data.
"""
import pandas as pd
import requests
import config

# Try to import fredapi, but make it optional
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    print("Warning: fredapi not installed. Run: pip install fredapi")


def fetch_shiller():
    """Download Shiller's S&P 500 dataset (price, earnings, dividends, CPI, CAPE)."""
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    print(f"Fetching Shiller data from {url}...")

    try:
        df = pd.read_excel(url, sheet_name="Data", skiprows=7)
        # Clean up column names (Shiller's sheet is messy)
        df.columns = [
            "date", "sp500_price", "dividend", "earnings", "cpi",
            "date_fraction", "gs10", "real_price", "real_dividend",
            "real_tr_price", "real_earnings", "real_tr_scaled_earnings",
            "cape", "tr_cape", "excess_cape_yield", "monthly_total_bond_return",
            "real_total_bond_return", "10yr_annualized_stock_return",
            "10yr_annualized_bond_return", "10yr_excess_annualized_return"
        ]
        df = df.dropna(subset=["sp500_price"])
        df.to_csv(config.DATA_RAW + "shiller.csv", index=False)
        print(f"Shiller data: {len(df)} rows saved to {config.DATA_RAW}shiller.csv")
        return df
    except Exception as e:
        print(f"Error fetching Shiller data: {e}")
        return None


def fetch_fred():
    """Download all FRED series."""
    if not FRED_AVAILABLE:
        print("Skipping FRED data — fredapi not installed")
        return

    if config.FRED_API_KEY == "your_key_here":
        print("Skipping FRED data — no API key configured")
        print("Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        return

    fred = Fred(api_key=config.FRED_API_KEY)

    for name, code in config.FRED_SERIES.items():
        try:
            series = fred.get_series(code, observation_start=config.START_DATE)
            series.to_csv(config.DATA_RAW + f"fred_{name}.csv", header=True)
            print(f"FRED {name} ({code}): {len(series)} observations")
        except Exception as e:
            print(f"Warning: Could not fetch {name} ({code}): {e}")


def fetch_damodaran_erp():
    """Download Damodaran's implied ERP estimates for benchmarking."""
    url = "https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx"
    print(f"Fetching Damodaran ERP from {url}...")

    try:
        df = pd.read_excel(url)
        df.to_csv(config.DATA_RAW + "damodaran_erp.csv", index=False)
        print(f"Damodaran ERP: {len(df)} rows saved")
        return df
    except Exception as e:
        print(f"Warning: Could not fetch Damodaran ERP: {e}")
        return None


def main():
    print("=" * 60)
    print("  ERP Model — Data Fetcher")
    print("=" * 60)
    print()

    fetch_shiller()
    print()
    fetch_fred()
    print()
    fetch_damodaran_erp()

    print()
    print("=" * 60)
    print(f"  All data fetched. Check {config.DATA_RAW}")
    print("=" * 60)


if __name__ == "__main__":
    main()
