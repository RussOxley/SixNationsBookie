from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
import math
import numpy as np

from .models import Fixture, MatchOutcome, TournamentSample, Team
from .rules import ChampionshipRules

TEAMS: Tuple[Team, ...] = ("ENG","FRA","IRE","ITA","SCO","WAL")
MAX_TABLE_POINTS = 28

@dataclass
class SimulatorParams:
    strengths: Dict[Team, float]
    home_adv: float = 0.30
    draw_k: float = 0.35

    try_base: float = -0.10
    try_strength_coef: float = 0.25
    try_matchup_coef: float = 0.10

    lbp_base: float = -0.20
    lbp_closeness_coef: float = 1.25

    seed: int = 7

class TournamentSimulator:
    def __init__(self, fixtures: List[Fixture], rules: Optional[ChampionshipRules] = None):
        self.fixtures = fixtures
        self.rules = rules or ChampionshipRules()

    @staticmethod
    def load_fixtures_json(path: str) -> List[Fixture]:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return [Fixture(**row) for row in obj["fixtures"]]

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    @staticmethod
    def _clamp(p: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, p))

    def _match_probs(self, d: float, draw_k: float) -> Tuple[float, float, float]:
        a = math.exp(d)
        b = math.exp(-d)
        denom = a + b + draw_k
        return (a/denom, draw_k/denom, b/denom)

    def _sample_match(self, params: SimulatorParams, home: Team, away: Team, rng: np.random.Generator) -> MatchOutcome:
        sH = params.strengths[home] + params.home_adv
        sA = params.strengths[away]
        d = sH - sA

        pH, pD, pA = self._match_probs(d, params.draw_k)
        u = rng.random()
        if u < pH:
            home_res, away_res = "W", "L"
        elif u < pH + pD:
            home_res, away_res = "D", "D"
        else:
            home_res, away_res = "L", "W"

        p_try_home = self._sigmoid(params.try_base + params.try_strength_coef*params.strengths[home] + params.try_matchup_coef*(params.strengths[home]-params.strengths[away]))
        p_try_away = self._sigmoid(params.try_base + params.try_strength_coef*params.strengths[away] + params.try_matchup_coef*(params.strengths[away]-params.strengths[home]))
        home_try = rng.random() < self._clamp(p_try_home, 0.02, 0.85)
        away_try = rng.random() < self._clamp(p_try_away, 0.02, 0.85)

        closeness = math.exp(-abs(d))
        p_lbp = self._sigmoid(params.lbp_base + params.lbp_closeness_coef*closeness)
        p_lbp = self._clamp(p_lbp, 0.02, 0.75)

        home_lbp = (home_res == "L") and (rng.random() < p_lbp)
        away_lbp = (away_res == "L") and (rng.random() < p_lbp)

        return MatchOutcome(
            home_result=home_res,
            away_result=away_res,
            home_try_bp=home_try,
            away_try_bp=away_try,
            home_lbp=home_lbp,
            away_lbp=away_lbp,
        )

    def sample_many(self, params: SimulatorParams, n: int, keep_outcomes: bool = False) -> List[TournamentSample]:
        rng = np.random.default_rng(params.seed)
        out: List[TournamentSample] = []
        for _ in range(n):
            points = {t: 0 for t in TEAMS}
            wins = {t: 0 for t in TEAMS}
            outcomes: List[MatchOutcome] = []

            for fx in self.fixtures:
                mo = self._sample_match(params, fx.home, fx.away, rng)
                points[fx.home] += self.rules.match_points(mo.home_result, mo.home_try_bp, mo.home_lbp)
                points[fx.away] += self.rules.match_points(mo.away_result, mo.away_try_bp, mo.away_lbp)
                if mo.home_result == "W":
                    wins[fx.home] += 1
                if mo.away_result == "W":
                    wins[fx.away] += 1
                if keep_outcomes:
                    outcomes.append(mo)

            for t in TEAMS:
                if wins[t] == 5:
                    points[t] += self.rules.grand_slam_bonus

            out.append(TournamentSample(points=points, outcomes=outcomes if keep_outcomes else None))
        return out

    @staticmethod
    def moments(samples: List[TournamentSample]) -> Tuple[Dict[Team, float], np.ndarray]:
        team_idx = {t:i for i,t in enumerate(TEAMS)}
        X = np.zeros((len(samples), len(TEAMS)), dtype=float)
        for r, s in enumerate(samples):
            for t, v in s.points.items():
                X[r, team_idx[t]] = v
        mu_vec = X.mean(axis=0)
        Sigma = np.cov(X, rowvar=False, ddof=1)
        mu = {t: float(mu_vec[team_idx[t]]) for t in TEAMS}
        return mu, Sigma

    @staticmethod
    def quantiles(samples: List[TournamentSample], q: float) -> Dict[Team, float]:
        team_idx = {t:i for i,t in enumerate(TEAMS)}
        X = np.zeros((len(samples), len(TEAMS)), dtype=float)
        for r, s in enumerate(samples):
            for t, v in s.points.items():
                X[r, team_idx[t]] = v
        qs = np.quantile(X, q, axis=0)
        return {t: float(qs[team_idx[t]]) for t in TEAMS}
