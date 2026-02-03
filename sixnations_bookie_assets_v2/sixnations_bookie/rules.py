from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ChampionshipRules:
    """Six Nations table-points rules (Men's Championship).

    Match points:
      - win: 4 (or 5 if the winner scores 4+ tries)
      - draw: 2 each (+1 if 4+ tries)
      - loss: 0 (+1 if 4+ tries; +1 if lose by <=7; +2 if both)
      - grand slam: +3 if a team wins all five matches
    """
    win_points: int = 4
    draw_points: int = 2
    try_bonus_points: int = 1
    losing_bonus_points: int = 1
    grand_slam_bonus: int = 3

    def match_points(self, result: str, scored_4_tries: bool, lost_by_le_7: bool) -> int:
        if result not in {"W","D","L"}:
            raise ValueError("result must be 'W', 'D', or 'L'")

        pts = 0
        if result == "W":
            pts += self.win_points
            if scored_4_tries:
                pts += self.try_bonus_points
        elif result == "D":
            pts += self.draw_points
            if scored_4_tries:
                pts += self.try_bonus_points
        else:  # L
            if scored_4_tries:
                pts += self.try_bonus_points
            if lost_by_le_7:
                pts += self.losing_bonus_points
        return pts
