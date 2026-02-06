"""
Configuration — edit these values to customise the model.
No need to touch any other file for basic changes.
"""
import os

# FRED API key (free, get one at https://fred.stlouisfed.org/docs/api/api_key.html)
# Can also be set via environment variable FRED_API_KEY
FRED_API_KEY = os.environ.get("FRED_API_KEY", "your_key_here")

# Date range for analysis
START_DATE = "1900-01-01"
END_DATE = "2025-12-31"

# CAPE lookback window (years) — classic is 10, some research uses 7
CAPE_WINDOW = 10

# Fair-value CAPE model training window (years, rolling)
FV_TRAINING_WINDOW = 30

# Forecast horizons to evaluate (years)
FORECAST_HORIZONS = [5, 7, 10]

# FRED series codes
FRED_SERIES = {
    "treasury_10y": "GS10",
    "tips_10y": "DFII10",
    "breakeven_10y": "T10YIE",
    "credit_spread": "BAA10Y",
    "term_spread": "T10Y2Y",
    "vix": "VIXCLS",
    "fed_funds": "FEDFUNDS",
    "cpi": "CPIAUCSL",
    "corp_profits": "CP",
}

# Output paths (relative to erp_model directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw") + os.sep
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed") + os.sep
OUTPUT = os.path.join(BASE_DIR, "output") + os.sep

# Ensure directories exist
os.makedirs(DATA_RAW, exist_ok=True)
os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)
