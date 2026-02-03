from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from .models import Team
from .simulator import MAX_TABLE_POINTS, TEAMS

@dataclass
class Wallet:
    user_id: str
    balance: float
    locked_margin: float = 0.0

    @property
    def free(self) -> float:
        return self.balance - self.locked_margin

@dataclass
class Position:
    qty: float = 0.0
    avg_price: float = 0.0

class PositionBook:
    def __init__(self, stake_per_point: float, x_min: int = 0, x_max: int = MAX_TABLE_POINTS):
        self.stake_per_point = float(stake_per_point)
        self.x_min = int(x_min)
        self.x_max = int(x_max)
        self.positions: Dict[str, Dict[Team, Position]] = {}

    def get(self, user_id: str, team: Team) -> Position:
        self.positions.setdefault(user_id, {t: Position() for t in TEAMS})
        return self.positions[user_id][team]

    def apply_trade(self, user_id: str, team: Team, qty_delta: float, price: float) -> float:
        pos = self.get(user_id, team)
        realised = 0.0

        if pos.qty == 0.0 or (pos.qty > 0 and qty_delta > 0) or (pos.qty < 0 and qty_delta < 0):
            new_qty = pos.qty + qty_delta
            if new_qty == 0.0:
                pos.qty = 0.0
                pos.avg_price = 0.0
            else:
                pos.avg_price = (pos.avg_price * pos.qty + price * qty_delta) / new_qty
                pos.qty = new_qty
            return realised

        close_qty = min(abs(qty_delta), abs(pos.qty))
        close_qty_signed = close_qty if pos.qty > 0 else -close_qty

        pnl_per_point = (price - pos.avg_price) * close_qty_signed
        realised = pnl_per_point * self.stake_per_point

        remaining_qty = pos.qty + qty_delta
        if remaining_qty == 0.0:
            pos.qty = 0.0
            pos.avg_price = 0.0
        else:
            if (pos.qty > 0 and remaining_qty < 0) or (pos.qty < 0 and remaining_qty > 0):
                pos.qty = remaining_qty
                pos.avg_price = price
            else:
                pos.qty = remaining_qty
        return float(realised)

    def margin_required_user(self, user_id: str) -> float:
        if user_id not in self.positions:
            return 0.0
        req = 0.0
        for _, pos in self.positions[user_id].items():
            if pos.qty == 0:
                continue
            if pos.qty > 0:
                req += pos.qty * (pos.avg_price - self.x_min) * self.stake_per_point
            else:
                req += (-pos.qty) * (self.x_max - pos.avg_price) * self.stake_per_point
        return max(0.0, float(req))

    def settle_user(self, user_id: str, final_points: Dict[Team, int]) -> float:
        if user_id not in self.positions:
            return 0.0
        pnl = 0.0
        for team, pos in self.positions[user_id].items():
            if pos.qty == 0:
                continue
            X = float(final_points[team])
            pnl += pos.qty * (X - pos.avg_price) * self.stake_per_point
            pos.qty = 0.0
            pos.avg_price = 0.0
        return float(pnl)
