from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import json
import numpy as np

from .simulator import TournamentSimulator, SimulatorParams, TEAMS
from .models import Team

@dataclass
class Target:
    min: float
    likely: float
    max: float

def load_targets_json(path: str) -> Dict[Team, Target]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return {t: Target(min=float(v["min"]), likely=float(v["likely"]), max=float(v["max"])) for t, v in obj.items()}

def _loss(targets: Dict[Team, Target], q025, q50, q975) -> float:
    w_med, w_lo, w_hi = 1.0, 0.6, 0.6
    loss = 0.0
    for t in TEAMS:
        trg = targets[t]
        loss += w_med * (q50[t] - trg.likely) ** 2
        loss += w_lo  * (q025[t] - trg.min) ** 2
        loss += w_hi  * (q975[t] - trg.max) ** 2
    return float(loss)

def fit_to_targets(
    simulator: TournamentSimulator,
    targets: Dict[Team, Target],
    *,
    n_samples: int = 4000,
    max_iter: int = 250,
    seed: int = 123,
    initial_strengths: Optional[Dict[Team, float]] = None,
    step_strength: float = 0.18,
    step_global: float = 0.10,
    verbose: bool = True,
) -> SimulatorParams:
    rng = np.random.default_rng(seed)

    if initial_strengths is None:
        ranked = sorted(TEAMS, key=lambda t: targets[t].likely)
        init = {}
        for j, t in enumerate(ranked):
            init[t] = -1.0 + 2.0 * (j / (len(TEAMS)-1))
        initial_strengths = init

    best = SimulatorParams(strengths=dict(initial_strengths), seed=seed)

    def eval_params(p: SimulatorParams):
        samples = simulator.sample_many(p, n=n_samples)
        q025 = simulator.quantiles(samples, 0.025)
        q50  = simulator.quantiles(samples, 0.50)
        q975 = simulator.quantiles(samples, 0.975)
        return _loss(targets, q025, q50, q975), q025, q50, q975

    best_loss, best_q025, best_q50, best_q975 = eval_params(best)
    if verbose:
        print(f"[fit] start loss={best_loss:.3f}")

    for it in range(1, max_iter+1):
        cand = SimulatorParams(**{**best.__dict__})
        cand.strengths = dict(best.strengths)

        for t in TEAMS:
            cand.strengths[t] += rng.normal(0.0, step_strength)

        cand.home_adv = best.home_adv + rng.normal(0.0, step_global*0.4)
        cand.draw_k   = max(0.05, best.draw_k + rng.normal(0.0, step_global*0.4))
        cand.try_base = best.try_base + rng.normal(0.0, step_global*0.3)
        cand.lbp_base = best.lbp_base + rng.normal(0.0, step_global*0.3)

        anchor = "ITA"
        shift = cand.strengths[anchor]
        for t in TEAMS:
            cand.strengths[t] -= shift

        loss, q025, q50, q975 = eval_params(cand)
        if loss < best_loss:
            best, best_loss = cand, loss
            best_q025, best_q50, best_q975 = q025, q50, q975
            if verbose and (it % 10 == 0 or it < 10):
                print(f"[fit] iter={it:03d} improved loss={best_loss:.3f}")

    if verbose:
        print(f"[fit] done loss={best_loss:.3f}")
        print("[fit] strengths:", {t: round(best.strengths[t],3) for t in TEAMS})
        print("[fit] medians:", {t: round(best_q50[t],2) for t in TEAMS})

    return best
