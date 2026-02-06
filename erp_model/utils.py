"""
Shared helper functions for the ERP model.
"""
import pandas as pd
import numpy as np


def parse_shiller_date(date_value):
    """
    Parse Shiller's date format (e.g., 2024.01 = Jan 2024).

    Parameters
    ----------
    date_value : float
        Date in Shiller format (year.month as decimal)

    Returns
    -------
    str
        Date string in YYYY-MM-01 format
    """
    year = int(date_value)
    month = int(round((date_value % 1) * 100))
    if month == 0:
        month = 1
    return f"{year}-{month:02d}-01"


def annualized_return(start_value, end_value, years):
    """
    Calculate annualized return from start and end values.

    Parameters
    ----------
    start_value : float
        Starting value
    end_value : float
        Ending value
    years : float
        Number of years

    Returns
    -------
    float
        Annualized return as decimal (e.g., 0.07 for 7%)
    """
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return np.nan
    return (end_value / start_value) ** (1 / years) - 1


def rolling_mean(series, window_months):
    """
    Calculate rolling mean with minimum 80% coverage requirement.

    Parameters
    ----------
    series : pd.Series
        Input series
    window_months : int
        Rolling window size in months

    Returns
    -------
    pd.Series
        Rolling mean with NaN where coverage < 80%
    """
    min_periods = int(window_months * 0.8)
    return series.rolling(window=window_months, min_periods=min_periods).mean()


def format_pct(value, decimals=2):
    """Format a decimal as a percentage string."""
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_ratio(value, decimals=1):
    """Format a ratio value."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"
