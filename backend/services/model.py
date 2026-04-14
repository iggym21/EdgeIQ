import numpy as np
from scipy.stats import poisson, norm

POISSON_STATS = {"points", "rebounds", "assists", "steals", "blocks"}


def get_distribution(stat_category: str) -> str:
    return "poisson" if stat_category.lower() in POISSON_STATS else "normal"


def calc_probability(values: list[float], line: float, stat_category: str) -> float:
    if not values:
        raise ValueError("values must not be empty")
    dist = get_distribution(stat_category)
    if dist == "poisson" and line < 0:
        raise ValueError("line must be non-negative for counting stats")
    if dist == "poisson":
        lam = float(np.mean(values))
        return float(1 - poisson.cdf(int(np.floor(line)), lam))
    else:
        mu = float(np.mean(values))
        sigma = float(np.std(values))
        if sigma == 0:
            return 1.0 if mu > line else 0.0
        return float(1 - norm.cdf(line, mu, sigma))


def calc_ev(your_prob: float, odds: int) -> dict:
    if odds == 0:
        raise ValueError("odds must not be zero")
    if not (0.0 <= your_prob <= 1.0):
        raise ValueError("your_prob must be between 0 and 1")
    if odds > 0:
        implied_prob = 100 / (odds + 100)
        potential_win = odds / 100
    else:
        implied_prob = abs(odds) / (abs(odds) + 100)
        potential_win = 100 / abs(odds)

    ev = (your_prob * potential_win) - ((1 - your_prob) * 1)
    kelly_raw = (your_prob * (potential_win + 1) - 1) / potential_win
    kelly = max(0.0, kelly_raw)

    return {
        "your_prob": round(your_prob, 4),
        "implied_prob": round(implied_prob, 4),
        "ev": round(ev, 4),
        "edge_pct": round((your_prob - implied_prob) * 100, 2),
        "kelly_fraction": round(kelly, 4),
        "potential_win": round(potential_win, 4),
    }
