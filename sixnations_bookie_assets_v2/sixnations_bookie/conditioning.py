from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from .models import Fixture, MatchOutcome, TournamentSample, Team
from .rules import ChampionshipRules
from .simulator import TEAMS, SimulatorParams, TournamentSimulator

@dataclass(frozen=True)
class PlayedMatch:
    home: Team
    away: Team
    home_result: str  # "W","D","L"
    home_try_bp: bool
    away_try_bp: bool
    home_lbp: bool
    away_lbp: bool

    def as_outcome(self) -> MatchOutcome:
        if self.home_result == "W":
            away_result = "L"
        elif self.home_result == "L":
            away_result = "W"
        else:
            away_result = "D"
        return MatchOutcome(
            home_result=self.home_result,
            away_result=away_result,
            home_try_bp=self.home_try_bp,
            away_try_bp=self.away_try_bp,
            home_lbp=self.home_lbp,
            away_lbp=self.away_lbp,
        )

@dataclass
class TournamentState:
    points_so_far: Dict[Team, int]
    wins_so_far: Dict[Team, int]
    remaining_fixtures: List[Fixture]

def apply_played_matches(
    fixtures: List[Fixture],
    played: List[PlayedMatch],
    rules: Optional[ChampionshipRules] = None,
) -> TournamentState:
    rules = rules or ChampionshipRules()
    points = {t: 0 for t in TEAMS}
    wins = {t: 0 for t in TEAMS}

    played_map: Dict[Tuple[Team, Team], PlayedMatch] = {(pm.home, pm.away): pm for pm in played}

    remaining: List[Fixture] = []
    for fx in fixtures:
        key = (fx.home, fx.away)
        if key not in played_map:
            remaining.append(fx)
            continue

        pm = played_map[key]
        out = pm.as_outcome()

        points[fx.home] += rules.match_points(out.home_result, out.home_try_bp, out.home_lbp)
        points[fx.away] += rules.match_points(out.away_result, out.away_try_bp, out.away_lbp)

        if out.home_result == "W":
            wins[fx.home] += 1
        if out.away_result == "W":
            wins[fx.away] += 1

    return TournamentState(points_so_far=points, wins_so_far=wins, remaining_fixtures=remaining)

def simulate_remaining(
    state: TournamentState,
    params: SimulatorParams,
    *,
    n: int,
    rules: Optional[ChampionshipRules] = None,
    seed_offset: int = 101,
) -> List[TournamentSample]:
    rules = rules or ChampionshipRules()
    rng = np.random.default_rng(params.seed + seed_offset)
    sim = TournamentSimulator(state.remaining_fixtures, rules=rules)

    out: List[TournamentSample] = []
    for _ in range(n):
        points = dict(state.points_so_far)
        wins = dict(state.wins_so_far)

        for fx in state.remaining_fixtures:
            mo = sim._sample_match(params, fx.home, fx.away, rng)
            points[fx.home] += rules.match_points(mo.home_result, mo.home_try_bp, mo.home_lbp)
            points[fx.away] += rules.match_points(mo.away_result, mo.away_try_bp, mo.away_lbp)
            if mo.home_result == "W":
                wins[fx.home] += 1
            if mo.away_result == "W":
                wins[fx.away] += 1

        for t in TEAMS:
            if wins[t] == 5:
                points[t] += rules.grand_slam_bonus

        out.append(TournamentSample(points=points, outcomes=None))

    return out
