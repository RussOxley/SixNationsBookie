import numpy as np
from sixnations_bookie.market_maker import MarketMaker, MarketMakerParams

def test_linked_move_via_covariance():
    mu = {"ENG": 10.0, "FRA": 10.0, "IRE": 10.0, "ITA": 10.0, "SCO": 10.0, "WAL": 10.0}
    Sigma = np.eye(6)
    Sigma[0,1] = Sigma[1,0] = -0.7

    mm = MarketMaker(mu, Sigma, stake_per_point=10.0, params=MarketMakerParams(risk_aversion=0.2, base_half_spread=0.0))
    before_eng = mm.quote("ENG")[2]
    before_fra = mm.quote("FRA")[2]

    mm.execute(team="FRA", side="BUY", qty=1.0)
    after_eng = mm.quote("ENG")[2]
    after_fra = mm.quote("FRA")[2]

    assert after_fra >= before_fra
    assert after_eng <= before_eng
