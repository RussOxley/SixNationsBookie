#!/usr/bin/env python3
"""
Run the complete ERP model pipeline.

Usage:
    python run_all.py           # Run all steps
    python run_all.py --fetch   # Only fetch data
    python run_all.py --calc    # Only run calculations (skip fetch)
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    args = sys.argv[1:]

    fetch_only = "--fetch" in args
    calc_only = "--calc" in args

    print()
    print("=" * 60)
    print("  ERP MODEL — FULL PIPELINE")
    print("=" * 60)
    print()

    if not calc_only:
        print("Step 1/6: Fetching data...")
        print("-" * 60)
        import importlib
        fetch = importlib.import_module("01_fetch_data")
        fetch.main()
        print()

        if fetch_only:
            print("Fetch complete. Run with --calc to continue processing.")
            return

    print("Step 2/6: Building dataset...")
    print("-" * 60)
    import importlib
    build = importlib.import_module("02_build_dataset")
    build.main()
    print()

    print("Step 3/6: Calculating P-CAPE...")
    print("-" * 60)
    pcape = importlib.import_module("03_calc_pcape")
    pcape.main()
    print()

    print("Step 4/6: Calculating Fair-Value CAPE...")
    print("-" * 60)
    fv = importlib.import_module("04_calc_fair_value")
    fv.main()
    print()

    print("Step 5/6: Calculating Composite ERP...")
    print("-" * 60)
    erp = importlib.import_module("06_composite_erp")
    erp.main()
    print()

    print("Step 6/6: Generating analysis...")
    print("-" * 60)
    analyse = importlib.import_module("07_analyse")
    analyse.main()
    print()

    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
