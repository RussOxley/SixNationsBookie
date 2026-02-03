"""FastAPI skeleton wiring the engine into endpoints.

This is minimal on purpose. Replace in-memory store with a database.
Run:
  pip install -r requirements-dev.txt
  uvicorn backend_skeleton.main:app --reload
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sixnations_bookie.simulator import TournamentSimulator
from sixnations_bookie.calibration import load_targets_json
from sixnations_bookie.engine import SixNationsBookieEngine, EngineConfig
from sixnations_bookie.market_maker import MarketMakerParams
from sixnations_bookie.risk import PositionBook, Wallet
from sixnations_bookie.models import Team

app = FastAPI(title="Six Nations Friends Bookie (skeleton)")

@dataclass
class GroupState:
    group_id: str
    users: Dict[str, Wallet] = field(default_factory=dict)
    book: PositionBook = field(default_factory=lambda: PositionBook(stake_per_point=10.0))
    engine: Optional[SixNationsBookieEngine] = None

GROUPS: Dict[str, GroupState] = {}

class CreateGroupReq(BaseModel):
    stake_per_point: float = 10.0
    starting_balance: float = 50.0

class JoinReq(BaseModel):
    user_id: str
    deposit: float = 50.0

class TradeReq(BaseModel):
    user_id: str
    team: Team
    side: str  # BUY/SELL
    qty: float

class QuoteResp(BaseModel):
    team: Team
    bid: float
    ask: float
    mid: float

def _get_group(group_id: str) -> GroupState:
    if group_id not in GROUPS:
        raise HTTPException(404, "group not found")
    return GROUPS[group_id]

@app.post("/groups")
def create_group(req: CreateGroupReq):
    group_id = str(uuid.uuid4())[:8]
    gs = GroupState(group_id=group_id)
    gs.book = PositionBook(stake_per_point=req.stake_per_point)

    fixtures = TournamentSimulator.load_fixtures_json("sixnations_bookie/data/fixtures_6n_2026.json")
    targets = load_targets_json("sixnations_bookie/data/baseline_targets.json")

    gs.engine = SixNationsBookieEngine(fixtures, targets, config=EngineConfig(
        stake_per_point=req.stake_per_point,
        n_calib_samples=2000,
        n_fit_iter=120,
        n_price_samples=12000,
    ))
    gs.engine.calibrate(verbose=False)
    gs.engine.build_market(mm_params=MarketMakerParams())

    GROUPS[group_id] = gs
    return {"group_id": group_id}

@app.post("/groups/{group_id}/join")
def join_group(group_id: str, req: JoinReq):
    gs = _get_group(group_id)
    if req.user_id in gs.users:
        raise HTTPException(400, "user already exists")
    gs.users[req.user_id] = Wallet(user_id=req.user_id, balance=float(req.deposit))
    return {"ok": True}

@app.get("/groups/{group_id}/quotes", response_model=List[QuoteResp])
def get_quotes(group_id: str):
    gs = _get_group(group_id)
    mm = gs.engine.mm  # type: ignore
    out = []
    for team in ["ENG","FRA","IRE","ITA","SCO","WAL"]:
        bid, ask, mid = mm.quote(team)  # type: ignore
        out.append(QuoteResp(team=team, bid=bid, ask=ask, mid=mid))
    return out

@app.post("/groups/{group_id}/trade")
def trade(group_id: str, req: TradeReq):
    gs = _get_group(group_id)
    if req.user_id not in gs.users:
        raise HTTPException(404, "unknown user")

    mm = gs.engine.mm  # type: ignore
    wallet = gs.users[req.user_id]

    # Execute against bookie first to get fill (skeleton simplicity).
    exec_res = mm.execute(team=req.team, side=req.side, qty=req.qty)  # type: ignore
    fill = exec_res["avg_fill"]
    fee = exec_res["fee"]

    qty_delta = req.qty if req.side == "BUY" else -req.qty
    realised = gs.book.apply_trade(req.user_id, req.team, qty_delta=qty_delta, price=fill)

    wallet.balance += realised
    wallet.balance -= fee

    wallet.locked_margin = gs.book.margin_required_user(req.user_id)

    if wallet.free < 0:
        raise HTTPException(400, "insufficient funds / margin after trade")

    return {
        "fill": fill,
        "fee": fee,
        "realised_pnl": realised,
        "wallet_balance": wallet.balance,
        "wallet_locked_margin": wallet.locked_margin,
        "pot_total": exec_res["pot_total"],
    }
