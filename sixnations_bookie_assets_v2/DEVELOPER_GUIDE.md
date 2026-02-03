# Developer guide (Six Nations points market)

This guide tells your devs exactly what to build, and how to wire the engine in.
The goal is: it feels like a bookmaker, but it is hard to game.

## 1) What you are building

A private friends app that runs six linked “spread” markets:

- ENG, FRA, IRE, SCO, ITA, WAL final **table points** (0..28)

Users can buy or sell points. Trades move prices. Fees fund a night out.

## 2) The contract

For a team market, final points are X. Quote price is P (in points).

- BUY profit = (X - P) * stake_per_point * qty
- SELL profit = (P - X) * stake_per_point * qty

Your suggested stake is £1 per 0.1 point => stake_per_point = 10.

Keep stake_per_point configurable. It is a single number.

## 3) Why prices must be linked

Team points are linked through fixtures. If France win, someone else usually loses.
Bonus points add some slack, but not much.

So you should not price each team independently.

The engine simulates the whole tournament jointly and computes a covariance matrix.
That covariance drives cross-market price moves.

## 4) Engine flow (the devs just call functions)

### 4.1 Load config
- fixtures: `sixnations_bookie/data/fixtures_6n_2026.json`
- baseline targets: `sixnations_bookie/data/baseline_targets.json`

### 4.2 Fit strengths to your baseline
- `fit_to_targets(sim, targets, ...)` returns `SimulatorParams`

Interpretation of targets:
- min = 2.5% quantile
- likely = median
- max = 97.5% quantile

This is a pragmatic mapping. It is fine for a friends market.

### 4.3 Simulate to get pricing moments
- run 10k–20k Monte Carlo tournament paths
- compute:
  - mu = expected points per team
  - Sigma = covariance matrix across teams

### 4.4 Initialise the market maker
- `MarketMaker(mu, Sigma, stake_per_point=10.0)`

## 5) Market making mechanics

### 5.1 Inventory-aware linked mids

Let q be house inventory per team in contracts (positive = house long).

Mid prices are:

    mid = mu - risk_aversion * Sigma @ q

If users BUY France, the house sells France (q[FRA] falls).
That pushes the France mid up.
Because Sigma has cross-terms from shared fixtures, other teams shift too.

This gives you “France lifted -> others down”.

### 5.2 Bid/ask spread

bid = mid - h
ask = mid + h

Half-spread h widens with:
- house imbalance in that market |q_i|
- uncertainty sqrt(Sigma_ii)

### 5.3 Slippage

Trades are sliced into small fills.
Inventory is updated after each slice.
Average fill price is returned.

This stops the easy manipulation loop (nudge price with a tiny bet then trade big the other way).

## 6) Risk and wallets

Use `PositionBook`:

- Tracks each user’s qty and average price per team.
- Computes conservative margin from bounds X in [0,28].

Reject a trade if:
- after applying it, wallet free balance would go negative.

Do not soften this. It is what keeps it honest.

## 7) Fees and the night-out pot

The engine charges a fee per trade:
- fee = max(fee_min, fee_rate * notional)

It accumulates in `MarketMaker.pot`.

You can also add a group entry fee, but per-trade fees work well and are transparent.

## 8) Live tournament updates

After real matches:
- enter outcomes as `PlayedMatch(...)`
- call `apply_played_matches(...)` and then `simulate_remaining(...)`
- recompute mu and Sigma
- update quotes using `MarketMaker.set_moments(mu, Sigma)`

This keeps the market consistent with real results.

## 9) Backend plan (FastAPI)

The included `backend_skeleton/main.py` shows one wiring pattern.

Minimal endpoints:

- POST /groups
- POST /groups/{id}/join
- GET /groups/{id}/quotes
- POST /groups/{id}/trade
- POST /groups/{id}/settle (admin)

In production:
- use a DB (SQLite/Postgres)
- add auth (magic link, or a group invite code)
- store trades append-only and rebuild positions from trades if needed

## 10) Front end plan

Three screens is enough:

1) Markets
- list teams with bid/ask
- tap team -> trade ticket

2) Trade ticket
- BUY/SELL toggle
- qty slider
- shows: average fill, fee, and “after-trade” quote preview

3) Wallet + positions
- balance, locked margin, pot
- per-team qty and average price
- rough mark-to-market P&L using current mid

Admin:
- close market
- input match results (optional)
- final settlement

## 11) Suggested starting parameters

For stake_per_point=10:
- starting wallet: £50–£100 each
- max trade size: 0.2–0.5 contracts
- slice_size: 0.1 (default)

Tune:
- risk_aversion: cross-market linkage strength
- base_half_spread: “bookie feel”
- fee_rate/fee_min: pot growth rate

## 12) Acceptance tests

- BUY then immediate SELL loses spread + fee.
- Buying France pushes France up, and usually moves others down a bit.
- Margin prevents bankrupting trades.
- Settlement P&L matches the contract exactly.

Done.
