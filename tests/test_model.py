import pytest
from backend.services.model import (
    get_distribution,
    calc_probability,
    calc_ev,
)

def test_get_distribution_poisson_for_counting_stats():
    assert get_distribution("points") == "poisson"
    assert get_distribution("rebounds") == "poisson"
    assert get_distribution("assists") == "poisson"
    assert get_distribution("steals") == "poisson"
    assert get_distribution("blocks") == "poisson"

def test_get_distribution_normal_for_minutes():
    assert get_distribution("minutes") == "normal"

def test_calc_probability_poisson_over_line():
    # Player averaged 25 pts over 10 games, line is 22.5
    values = [25, 28, 22, 30, 24, 26, 20, 29, 25, 27]
    prob = calc_probability(values, 22.5, "points")
    assert 0.5 < prob < 1.0  # high probability, line is below average

def test_calc_probability_poisson_under_line():
    values = [10, 12, 8, 11, 9, 13, 10, 11, 9, 10]
    prob = calc_probability(values, 20.5, "points")
    assert 0.0 < prob < 0.1  # very low probability, line is far above average

def test_calc_probability_normal_minutes():
    values = [32.0, 34.0, 30.0, 33.0, 31.0, 35.0, 32.0, 33.0, 31.0, 34.0]
    prob = calc_probability(values, 28.5, "minutes")
    assert prob > 0.9  # nearly certain to exceed 28.5

def test_calc_probability_raises_on_empty_values():
    with pytest.raises(ValueError, match="values must not be empty"):
        calc_probability([], 20.5, "points")

def test_calc_ev_positive_odds():
    # +110 odds, 60% modeled probability
    result = calc_ev(0.60, 110)
    assert result["implied_prob"] == pytest.approx(100 / 210, abs=0.001)
    assert result["potential_win"] == pytest.approx(1.10, abs=0.001)
    assert result["ev"] > 0  # should be positive EV
    assert result["kelly_fraction"] > 0

def test_calc_ev_negative_odds():
    # -120 odds, 55% modeled probability
    result = calc_ev(0.55, -120)
    assert result["implied_prob"] == pytest.approx(120 / 220, abs=0.001)
    assert result["potential_win"] == pytest.approx(100 / 120, abs=0.001)

def test_calc_ev_kelly_never_negative():
    # Low probability vs high negative odds → kelly should be 0, not negative
    result = calc_ev(0.30, -200)
    assert result["kelly_fraction"] == 0.0

def test_calc_ev_edge_pct():
    result = calc_ev(0.60, 110)
    implied = 100 / 210
    assert result["edge_pct"] == pytest.approx((0.60 - implied) * 100, abs=0.01)

def test_calc_ev_raises_on_zero_odds():
    with pytest.raises(ValueError, match="odds must not be zero"):
        calc_ev(0.55, 0)

def test_calc_ev_raises_on_invalid_prob():
    with pytest.raises(ValueError):
        calc_ev(1.5, 110)

def test_calc_probability_raises_on_negative_line_for_poisson():
    with pytest.raises(ValueError, match="non-negative"):
        calc_probability([25, 28, 22], -1.0, "points")
