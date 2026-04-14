import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ev_endpoint_returns_all_fields():
    payload = {
        "game_log_values": [25, 28, 22, 30, 24, 26, 20, 29, 25, 27],
        "line": 22.5,
        "odds": -110,
        "stat_category": "points",
    }
    r = client.post("/ev", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "your_prob" in data
    assert "implied_prob" in data
    assert "ev" in data
    assert "edge_pct" in data
    assert "kelly_fraction" in data
    assert "distribution" in data
    assert "sample_size" in data
    assert "low_confidence" in data

def test_ev_endpoint_positive_odds():
    payload = {
        "game_log_values": [10] * 10,
        "line": 8.5,
        "odds": 120,
        "stat_category": "points",
    }
    r = client.post("/ev", json=payload)
    assert r.status_code == 200
    assert r.json()["ev"] > 0

def test_ev_endpoint_validates_empty_log():
    payload = {
        "game_log_values": [],
        "line": 22.5,
        "odds": -110,
        "stat_category": "points",
    }
    r = client.post("/ev", json=payload)
    assert r.status_code == 422
