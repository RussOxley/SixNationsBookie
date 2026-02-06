# Predictive ERP Model

A Python framework for estimating the Equity Risk Premium using free data and modern CAPE variants.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your FRED API key (get one free at fred.stlouisfed.org)
export FRED_API_KEY="your_key_here"

# Run the complete pipeline
python run_all.py
```

## What It Does

This model estimates expected equity returns and the Equity Risk Premium (ERP) using three key improvements over traditional Shiller CAPE:

1. **P-CAPE** (Haghani & White, 2024) — Adjusts for retained earnings compounding
2. **Fair-Value CAPE** (Vanguard/Davis) — Accounts for interest rate and inflation environment
3. **Composite signals** — Blends valuation, credit spreads, and yield curve

## Pipeline Steps

| Script | Purpose |
|--------|---------|
| `01_fetch_data.py` | Downloads Shiller, FRED, and Damodaran data |
| `02_build_dataset.py` | Merges into single monthly dataset |
| `03_calc_pcape.py` | Calculates payout-adjusted CAPE |
| `04_calc_fair_value.py` | Estimates fair-value CAPE from rates + inflation |
| `05_calc_cc_cape.py` | (Optional) Current-constituents CAPE |
| `06_composite_erp.py` | Combines signals into ERP estimate |
| `07_analyse.py` | Generates charts and summary |

Or run everything at once:
```bash
python run_all.py
```

## Data Sources (All Free)

- **Shiller** — S&P 500 price, earnings, dividends, CPI, CAPE (1871–present)
- **FRED** — Interest rates, credit spreads, VIX, inflation (various start dates)
- **Damodaran** — Published implied ERP for benchmarking

## Configuration

Edit `config.py` to customise:
- FRED API key
- Date range
- CAPE window (default: 10 years)
- Fair-value training window (default: 30 years)

## Output

After running, check:
- `data/processed/monthly_final.csv` — Complete dataset with all signals
- `output/erp_analysis.png` — CAPE variants and ERP over time
- `output/signal_decomposition.png` — Signal contributions
- `output/diagnostic_scatter.png` — Estimate vs actual returns

## Important Caveats

- **Backtesting limitations**: With ~15 non-overlapping 10-year periods, statistical significance is limited
- **Confidence intervals**: Report ±3% around point estimates — this is honest uncertainty
- **Model risk**: No single metric is a silver bullet; blending reduces but doesn't eliminate risk

## References

- Haghani & White (2024) — P-CAPE methodology
- Research Affiliates (2025) — CC-CAPE and CAPE Spread
- Davis et al. / Vanguard — Fair-value CAPE approach
- Shiller — Original CAPE methodology
