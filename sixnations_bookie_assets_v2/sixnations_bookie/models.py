from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Literal

Team = Literal["ENG","FRA","IRE","ITA","SCO","WAL"]

@dataclass(frozen=True)
class Fixture:
    round: int
    date: str            # YYYY-MM-DD
    kickoff_gmt: str     # HH:MM (GMT)
    home: Team
    away: Team
    venue: str = ""

@dataclass(frozen=True)
class MatchOutcome:
    """Outcome used for table-points simulation (not scoreline)."""
    home_result: Literal["W","D","L"]
    away_result: Literal["W","D","L"]
    home_try_bp: bool
    away_try_bp: bool
    home_lbp: bool
    away_lbp: bool

@dataclass
class TournamentSample:
    """One Monte Carlo draw of table points for all teams."""
    points: Dict[Team, int]
    outcomes: Optional[List[MatchOutcome]] = None
