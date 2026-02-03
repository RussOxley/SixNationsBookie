from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

from .models import Team, Fixture
from .simulator import TournamentSimulator, SimulatorParams
from .calibration import Target, fit_to_targets
from .market_maker import MarketMaker, MarketMakerParams
from .conditioning import apply_played_matches, simulate_remaining, PlayedMatch, TournamentState

@dataclass
class EngineConfig:
    stake_per_point: float = 10.0
    n_calib_samples: int = 2500
    n_fit_iter: int = 140
    n_price_samples: int = 15000

class SixNationsBookieEngine:
    def __init__(self, fixtures: List[Fixture], targets: Dict[Team, Target], config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.sim = TournamentSimulator(fixtures)
        self.targets = targets

        self.params: Optional[SimulatorParams] = None
        self.mu: Optional[Dict[Team, float]] = None
        self.Sigma: Optional[np.ndarray] = None
        self.mm: Optional[MarketMaker] = None

    def calibrate(self, verbose: bool = True) -> SimulatorParams:
        self.params = fit_to_targets(
            self.sim,
            self.targets,
            n_samples=self.config.n_calib_samples,
            max_iter=self.config.n_fit_iter,
            verbose=verbose,
        )
        return self.params

    def build_market(self, mm_params: Optional[MarketMakerParams] = None) -> MarketMaker:
        if self.params is None:
            raise RuntimeError("Call calibrate() first.")
        samples = self.sim.sample_many(self.params, n=self.config.n_price_samples)
        self.mu, self.Sigma = self.sim.moments(samples)
        self.mm = MarketMaker(self.mu, self.Sigma, stake_per_point=self.config.stake_per_point, params=mm_params)
        return self.mm

    def rebuild_market_given_played(self, played: List[PlayedMatch]) -> MarketMaker:
        if self.params is None:
            raise RuntimeError("Call calibrate() first.")
        state: TournamentState = apply_played_matches(self.sim.fixtures, played, rules=self.sim.rules)
        samples = simulate_remaining(state, self.params, n=self.config.n_price_samples, rules=self.sim.rules)
        self.mu, self.Sigma = self.sim.moments(samples)
        if self.mm is None:
            self.mm = MarketMaker(self.mu, self.Sigma, stake_per_point=self.config.stake_per_point)
        else:
            self.mm.set_moments(self.mu, self.Sigma)
        return self.mm
