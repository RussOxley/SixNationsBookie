from sixnations_bookie.rules import ChampionshipRules

def test_match_points_win_try():
    r = ChampionshipRules()
    assert r.match_points("W", True, False) == 5

def test_match_points_loss_both_bonuses():
    r = ChampionshipRules()
    assert r.match_points("L", True, True) == 2

def test_match_points_draw_try():
    r = ChampionshipRules()
    assert r.match_points("D", True, False) == 3
