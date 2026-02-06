"""
Analysis and visualisation. Generates charts showing:
1. Historical CAPE vs P-CAPE vs Fair-Value CAPE
2. ERP estimate over time with confidence bands
3. Signal decomposition
4. Comparison with Damodaran's published estimates
5. Scatter: our estimate vs actual realised returns (with honest caveats)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import config


def plot_cape_variants(df, save=True):
    """Plot CAPE variants and ERP estimate over time."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Panel 1: CAPE variants
    ax = axes[0]
    ax.plot(df.index, df["cape"], label="Traditional CAPE", alpha=0.8)
    ax.plot(df.index, df["p_cape"], label="P-CAPE (payout-adjusted)", alpha=0.8)
    ax.plot(df.index, df["fair_value_cape"], label="Fair-Value CAPE",
            linestyle="--", alpha=0.7)
    ax.set_ylabel("CAPE Ratio")
    ax.set_title("CAPE Variants Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: ERP estimate
    ax = axes[1]
    ax.plot(df.index, df["estimated_erp"] * 100, label="Estimated ERP", color="navy")
    ax.fill_between(df.index, df["erp_lower"] * 100, df["erp_upper"] * 100,
                    alpha=0.2, color="navy", label="Confidence band")
    ax.axhline(y=0, color="red", linestyle="--", alpha=0.5)
    ax.set_ylabel("ERP (%)")
    ax.set_xlabel("Date")
    ax.set_title("Composite ERP Estimate")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save:
        output_path = config.OUTPUT + "erp_analysis.png"
        plt.savefig(output_path, dpi=150)
        print(f"  Saved: {output_path}")

    plt.show()


def plot_signal_decomposition(df, save=True):
    """Show contribution of each signal component."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Stack the signals
    signals = ["signal_pcaey", "signal_reversion", "signal_credit", "signal_term"]
    labels = ["P-CAPE Yield", "Reversion Adj.", "Credit Spread", "Term Spread"]
    colors = ["#2ecc71", "#e74c3c", "#3498db", "#9b59b6"]

    # Filter to valid data
    mask = df[signals].notna().all(axis=1)
    plot_df = df[mask].copy()

    bottom = np.zeros(len(plot_df))
    for signal, label, color in zip(signals, labels, colors):
        values = plot_df[signal].values * 100
        ax.bar(plot_df.index, values, bottom=bottom, label=label,
               color=color, alpha=0.7, width=30)
        bottom += values

    ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)
    ax.set_ylabel("Contribution to Real Return (%)")
    ax.set_xlabel("Date")
    ax.set_title("ERP Signal Decomposition")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    if save:
        output_path = config.OUTPUT + "signal_decomposition.png"
        plt.savefig(output_path, dpi=150)
        print(f"  Saved: {output_path}")

    plt.show()


def diagnostic_scatter(df, save=True):
    """
    Honest assessment: plot our estimate vs what actually happened.

    CAVEAT: With overlapping 10-year windows, the effective sample
    size is ~15 independent observations. This scatter is illustrative,
    not a rigorous backtest.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    mask = df[["estimated_real_return", "fwd_10yr_real_return"]].notna().all(axis=1)
    subset = df[mask]

    if len(subset) == 0:
        print("  No overlapping data for diagnostic scatter")
        return

    ax.scatter(subset["estimated_real_return"] * 100,
               subset["fwd_10yr_real_return"] * 100, alpha=0.3, s=10)

    # Perfect forecast line
    lims = [-5, 20]
    ax.plot(lims, lims, "r--", alpha=0.5, label="Perfect forecast")

    ax.set_xlabel("Estimated Real Return (%)")
    ax.set_ylabel("Actual 10-Year Real Return (%)")
    ax.set_title("Estimate vs Actual (ILLUSTRATIVE — overlapping windows)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    # R-squared (with caveat)
    corr = subset["estimated_real_return"].corr(subset["fwd_10yr_real_return"])
    ax.text(0.05, 0.95, f"Correlation: {corr:.2f}\n(~15 independent obs.)",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    plt.tight_layout()

    if save:
        output_path = config.OUTPUT + "diagnostic_scatter.png"
        plt.savefig(output_path, dpi=150)
        print(f"  Saved: {output_path}")

    plt.show()


def compare_damodaran(df, save=True):
    """Compare our ERP estimate with Damodaran's published estimates."""
    damodaran_path = config.DATA_RAW + "damodaran_erp.csv"

    if not os.path.exists(damodaran_path):
        print("  Damodaran ERP data not available — skipping comparison")
        return

    try:
        dam = pd.read_csv(damodaran_path)
        # Damodaran format varies — this is a best-effort parse
        # Adjust column names as needed based on actual file format
        print("  Damodaran comparison would go here (format varies)")
        print("  Check the downloaded file structure and adjust parsing")
    except Exception as e:
        print(f"  Could not parse Damodaran data: {e}")


def summary_table(df):
    """Print a summary table of current metrics."""
    latest = df.dropna(subset=["estimated_erp"]).iloc[-1]

    print()
    print("=" * 60)
    print("  CURRENT METRICS SUMMARY")
    print("=" * 60)
    print()
    print(f"  {'Metric':<30} {'Value':>15}")
    print("  " + "-" * 50)
    print(f"  {'Date':<30} {latest.name.strftime('%Y-%m'):>15}")
    print(f"  {'S&P 500 Price':<30} {latest['sp500_price']:>15,.0f}")
    print(f"  {'Traditional CAPE':<30} {latest['cape']:>15.1f}")
    print(f"  {'P-CAPE':<30} {latest['p_cape']:>15.1f}")
    print(f"  {'Fair-Value CAPE':<30} {latest['fair_value_cape']:>15.1f}")
    print(f"  {'CAPE Gap (%)':<30} {latest['cape_gap_pct'] * 100:>15.1f}%")
    print("  " + "-" * 50)
    print(f"  {'Est. Real Return':<30} {latest['estimated_real_return'] * 100:>15.2f}%")
    print(f"  {'Real Risk-Free Rate':<30} {latest['risk_free_real'] * 100:>15.2f}%")
    print(f"  {'Estimated ERP':<30} {latest['estimated_erp'] * 100:>15.2f}%")
    print(f"  {'ERP Range':<30} {latest['erp_lower'] * 100:>6.1f}% to {latest['erp_upper'] * 100:.1f}%")
    print("=" * 60)
    print()


def main():
    print("=" * 60)
    print("  ERP Model — Analysis & Visualisation")
    print("=" * 60)
    print()

    # Load final dataset
    input_path = config.DATA_PROCESSED + "monthly_final.csv"
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Final dataset not found at {input_path}. Run 06_composite_erp.py first."
        )

    df = pd.read_csv(input_path, index_col=0, parse_dates=True)
    print(f"Loaded {len(df)} months of data")
    print()

    # Generate outputs
    print("Generating charts...")
    plot_cape_variants(df)
    plot_signal_decomposition(df)
    diagnostic_scatter(df)
    compare_damodaran(df)

    # Summary
    summary_table(df)

    print(f"Charts saved to: {config.OUTPUT}")
    print()


if __name__ == "__main__":
    main()
