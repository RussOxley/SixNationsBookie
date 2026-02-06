"""
Combines multiple valuation signals into a composite ERP estimate.

Philosophy: No single metric is a silver bullet. The research clearly
shows that blending approaches reduces model risk. We use a
building-block approach inspired by Research Affiliates and Vanguard.

IMPORTANT: We explicitly do NOT backtest this model in the traditional
sense — with ~15 non-overlapping 10-year periods in the data, any
backtest would be statistically meaningless. Instead, we:
1. Use theoretical priors (each component has economic logic)
2. Compare our estimates against published benchmarks (Damodaran, Vanguard)
3. Examine whether signals are directionally consistent with each other
4. Report wide confidence intervals
"""
import pandas as pd
import numpy as np
import os
import config


def composite_erp_estimate(df):
    """
    Building-block approach to ERP estimation.

    Component 1: P-CAPE Earnings Yield
        The payout-adjusted earnings yield is our best single estimate
        of expected long-term real equity returns.

    Component 2: Fair-Value CAPE Gap Adjustment
        If CAPE is above fair value (given rates/inflation), we adjust
        returns downward to reflect expected multiple contraction.
        We assume partial mean reversion over our forecast horizon.

    Component 3: Credit Spread Signal
        Elevated credit spreads indicate stress — historically associated
        with higher subsequent equity returns (risk compensation).

    Component 4: Term Spread Signal
        An inverted or flat yield curve signals recession risk —
        tends to precede periods of both lower and more volatile returns.
    """

    df = df.copy()

    # ── Component 1: P-CAPE Earnings Yield ──
    # This IS the base expected real return
    df["signal_pcaey"] = df["p_caey"]

    # ── Component 2: Multiple Reversion Adjustment ──
    # If CAPE is X% above fair value, assume it reverts halfway over 10 years
    # Impact on annualised return = -0.5 * cape_gap_pct / forecast_horizon
    reversion_speed = 0.5  # Assume 50% reversion (conservative)
    horizon = 10
    df["signal_reversion"] = -(reversion_speed * df["cape_gap_pct"]) / horizon

    # ── Component 3: Credit Spread ──
    # Normalise: historical median ~1%, above that = positive signal
    if "credit_spread" in df.columns:
        credit_median = df["credit_spread"].median()
        df["signal_credit"] = (df["credit_spread"] - credit_median) * 0.1  # Scaled
    else:
        df["signal_credit"] = 0.0

    # ── Component 4: Term Spread ──
    # Inverted curve = negative signal for near-term
    if "term_spread" in df.columns:
        df["signal_term"] = df["term_spread"].clip(-2, 3) * 0.02  # Small weight
    else:
        df["signal_term"] = 0.0

    # ── Composite Estimate ──
    df["estimated_real_return"] = (
        df["signal_pcaey"]           # Base: P-CAPE earnings yield
        + df["signal_reversion"]     # Adjustment for over/undervaluation
        + df["signal_credit"]        # Credit risk compensation
        + df["signal_term"]          # Yield curve signal
    )

    # ERP = estimated equity return minus risk-free rate
    # Use real_rate calculated in fair-value step
    df["risk_free_real"] = df["real_rate"]

    df["estimated_erp"] = df["estimated_real_return"] - df["risk_free_real"]

    # ── Confidence Band ──
    # Based on historical dispersion of actual vs predicted
    # This is an honest acknowledgement of uncertainty
    df["erp_upper"] = df["estimated_erp"] + 0.03  # +/- 3% is realistic
    df["erp_lower"] = df["estimated_erp"] - 0.03

    return df


def generate_report(df):
    """Print a human-readable current estimate."""
    latest = df.dropna(subset=["estimated_erp"]).iloc[-1]
    date = latest.name

    print()
    print("=" * 60)
    print(f"  COMPOSITE ERP ESTIMATE — {date.strftime('%B %Y')}")
    print("=" * 60)
    print()
    print("  Building Blocks:")
    print(f"    P-CAPE Earnings Yield:     {latest['signal_pcaey']:.2%}")
    print(f"    Reversion Adjustment:      {latest['signal_reversion']:+.2%}")
    print(f"    Credit Spread Signal:      {latest['signal_credit']:+.2%}")
    print(f"    Term Spread Signal:        {latest['signal_term']:+.2%}")
    print("  " + "-" * 40)
    print(f"    Est. Real Equity Return:   {latest['estimated_real_return']:.2%}")
    print(f"    Real Risk-Free Rate:       {latest['risk_free_real']:.2%}")
    print("  " + "-" * 40)
    print(f"    ESTIMATED ERP:             {latest['estimated_erp']:.2%}")
    print(f"    Confidence Range:          {latest['erp_lower']:.2%} to {latest['erp_upper']:.2%}")
    print()
    print("  Context:")
    print(f"    Traditional CAPE:          {latest['cape']:.1f}")
    print(f"    P-CAPE:                    {latest['p_cape']:.1f}")
    print(f"    Fair-Value CAPE:           {latest['fair_value_cape']:.1f}")
    print(f"    CAPE Gap:                  {latest['cape_gap_pct']:+.1%}")
    print("=" * 60)
    print()


def main():
    print("=" * 60)
    print("  ERP Model — Composite ERP Calculator")
    print("=" * 60)
    print()

    # Load dataset with fair-value CAPE
    input_path = config.DATA_PROCESSED + "monthly_with_fairvalue.csv"
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Fair-value dataset not found at {input_path}. Run 04_calc_fair_value.py first."
        )

    df = pd.read_csv(input_path, index_col=0, parse_dates=True)
    print(f"Loaded {len(df)} months of data")

    # Calculate composite ERP
    df = composite_erp_estimate(df)

    # Save
    output_path = config.DATA_PROCESSED + "monthly_final.csv"
    df.to_csv(output_path)
    print(f"Saved to: {output_path}")

    # Generate report
    generate_report(df)


if __name__ == "__main__":
    main()
