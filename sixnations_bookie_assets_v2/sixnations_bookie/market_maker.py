from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import math
import numpy as np

from .models import Team
from .simulator import TEAMS

@dataclass
class MarketMakerParams:
    tick: float = 0.1
    risk_aversion: float = 0.020

    base_half_spread: float = 0.25
    inv_spread_coef: float = 0.06
    uncert_spread_coef: float = 0.10

    slice_size: float = 0.10
    min_slices: int = 1
    max_slices: int = 60

    fee_rate: float = 0.015
    fee_min: float = 0.05

def _round_to_tick(x: float, tick: float) -> float:
    return round(x / tick) * tick

class MarketMaker:
    def __init__(
        self,
        mu: Dict[Team, float],
        Sigma: np.ndarray,
        *,
        stake_per_point: float,
        params: Optional[MarketMakerParams] = None,
    ):
        self.params = params or MarketMakerParams()
        self.stake_per_point = float(stake_per_point)

        self.team_idx = {t:i for i,t in enumerate(TEAMS)}
        self.mu_vec = np.array([mu[t] for t in TEAMS], dtype=float)
        self.Sigma = np.array(Sigma, dtype=float)

        self.q = np.zeros(len(TEAMS), dtype=float)
        self.pot = 0.0

    def set_moments(self, mu: Dict[Team, float], Sigma: np.ndarray) -> None:
        self.mu_vec = np.array([mu[t] for t in TEAMS], dtype=float)
        self.Sigma = np.array(Sigma, dtype=float)

    def _mids_vec(self) -> np.ndarray:
        return self.mu_vec - self.params.risk_aversion * (self.Sigma @ self.q)

    def mids(self) -> Dict[Team, float]:
        v = self._mids_vec()
        return {t: float(v[self.team_idx[t]]) for t in TEAMS}

    def half_spreads(self) -> Dict[Team, float]:
        diag = np.maximum(np.diag(self.Sigma), 0.0)
        sig = np.sqrt(diag)
        hs = self.params.base_half_spread + self.params.inv_spread_coef*np.abs(self.q) + self.params.uncert_spread_coef*sig
        return {t: float(hs[self.team_idx[t]]) for t in TEAMS}

    def quote(self, team: Team) -> Tuple[float, float, float]:
        m = self.mids()[team]
        h = self.half_spreads()[team]
        bid = _round_to_tick(m - h, self.params.tick)
        ask = _round_to_tick(m + h, self.params.tick)
        mid = _round_to_tick(m, self.params.tick)
        return bid, ask, mid

    def _fee(self, qty: float, price: float) -> float:
        notional = abs(qty) * self.stake_per_point * abs(price)
        return float(max(self.params.fee_min, self.params.fee_rate * notional))

    def execute(self, *, team: Team, side: str, qty: float) -> Dict[str, float]:
        if qty <= 0:
            raise ValueError("qty must be positive")
        if side not in {"BUY","SELL"}:
            raise ValueError("side must be BUY or SELL")

        slices = int(math.ceil(qty / self.params.slice_size))
        slices = max(self.params.min_slices, min(self.params.max_slices, slices))
        slice_qty = qty / slices

        fills: List[float] = []
        for _ in range(slices):
            bid, ask, _ = self.quote(team)
            if side == "BUY":
                fill = ask
                self.q[self.team_idx[team]] -= slice_qty
            else:
                fill = bid
                self.q[self.team_idx[team]] += slice_qty
            fills.append(fill)

        avg_fill = float(np.mean(fills))
        fee = self._fee(qty, avg_fill)
        self.pot += fee

        new_bid, new_ask, new_mid = self.quote(team)

        return {
            "avg_fill": avg_fill,
            "fee": fee,
            "new_bid": new_bid,
            "new_ask": new_ask,
            "new_mid": new_mid,
            "pot_total": float(self.pot),
        }
