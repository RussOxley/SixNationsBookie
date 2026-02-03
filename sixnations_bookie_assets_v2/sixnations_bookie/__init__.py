"""Six Nations friends 'bookie' engine (math assets).

This package is the core engine for a small-group bookmaker simulation.
It is dependency-light and focuses on:

- joint tournament simulation (fixtures -> correlated team points)
- linked market making using covariance shading
- slippage via slice fills (harder to game)
- wallet + position + conservative margin checks

See:
  - demo_sixnations_points_market.py
  - DEVELOPER_GUIDE.md
"""

from .rules import ChampionshipRules
from .simulator import TournamentSimulator, SimulatorParams, TEAMS, MAX_TABLE_POINTS
from .calibration import fit_to_targets, load_targets_json, Target
from .market_maker import MarketMaker, MarketMakerParams
from .risk import Wallet, PositionBook
from .conditioning import PlayedMatch, TournamentState
