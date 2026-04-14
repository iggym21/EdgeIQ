import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import init_db

client = TestClient(app)

BET_PAYLOAD = {
    "player_name": "LeBron James",
    "stat_category": "points",
    "line": 25.5,
    "direction": "over",
    "odds": -110,
    "stake": 50.0,
    "ev_at_bet": 0.08,
}

def test_post_bet_returns_201():
    r = client.post("/bets", json=BET_PAYLOAD)
    assert r.status_code == 201
    data = r.json()
    assert data["player_name"] == "LeBron James"
    assert data["result"] == "pending"
    assert "id" in data

def test_get_bets_returns_list():
    client.post("/bets", json=BET_PAYLOAD)
    r = client.get("/bets")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1

def test_patch_bet_result():
    post_r = client.post("/bets", json=BET_PAYLOAD)
    bet_id = post_r.json()["id"]
    r = client.patch(f"/bets/{bet_id}", json={"result": "win", "profit_loss": 45.45})
    assert r.status_code == 200
    assert r.json()["result"] == "win"
    assert r.json()["profit_loss"] == 45.45

def test_patch_bet_invalid_result():
    post_r = client.post("/bets", json=BET_PAYLOAD)
    bet_id = post_r.json()["id"]
    r = client.patch(f"/bets/{bet_id}", json={"result": "maybe"})
    assert r.status_code == 422
