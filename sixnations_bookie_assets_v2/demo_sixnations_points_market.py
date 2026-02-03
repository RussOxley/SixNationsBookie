"""Demo: fit -> simulate -> quote -> trade -> linked moves."""

import pathlib
from sixnations_bookie.simulator import TournamentSimulator
from sixnations_bookie.calibration import load_targets_json
from sixnations_bookie.engine import SixNationsBookieEngine, EngineConfig
from sixnations_bookie.market_maker import MarketMakerParams

ROOT = pathlib.Path(__file__).parent
fixtures_path = ROOT / "sixnations_bookie" / "data" / "fixtures_6n_2026.json"
targets_path  = ROOT / "sixnations_bookie" / "data" / "baseline_targets.json"

fixtures = TournamentSimulator.load_fixtures_json(str(fixtures_path))
targets = load_targets_json(str(targets_path))

engine = SixNationsBookieEngine(fixtures, targets, config=EngineConfig(
    stake_per_point=10.0,
    n_calib_samples=2200,
    n_fit_iter=120,
    n_price_samples=12000,
))
engine.calibrate(verbose=True)
mm = engine.build_market(mm_params=MarketMakerParams())

print("\nOpening quotes (bid/ask):")
for t in ["FRA","ENG","IRE","SCO","ITA","WAL"]:
    b,a,m = mm.quote(t)
    print(f"  {t}: {b:.1f} / {a:.1f} (mid {m:.1f})")

print("\nTrade: BUY FRA qty=0.8 contracts")
r = mm.execute(team="FRA", side="BUY", qty=0.8)
print("  result:", r)

print("\nQuotes after France gets bought (linked moves via covariance):")
for t in ["FRA","ENG","IRE","SCO","ITA","WAL"]:
    b,a,m = mm.quote(t)
    print(f"  {t}: {b:.1f} / {a:.1f} (mid {m:.1f})")

print(f"\nNight-out pot so far: £{mm.pot:.2f}")
