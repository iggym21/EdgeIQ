import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

MOCK_PLAYERS = [{"id": 1, "name": "LeBron James", "team": "Los Angeles Lakers"}]
MOCK_LOGS = [{"game_date": "2024-01-10", "value": 28, "opponent": "BOS", "home_away": "away"}]
MOCK_PROP = {
    "game_id": "abc", "player_name": "LeBron James", "stat_category": "points",
    "line": 25.5, "over_odds": -110, "under_odds": -110,
    "book": "DraftKings", "source": "propodds",
}
MOCK_HISTORICAL = []


def test_search_players_returns_200():
    with patch("backend.routes.props.search_players", new_callable=AsyncMock,
               return_value=MOCK_PLAYERS):
        r = client.get("/props/search?q=LeBron")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "LeBron James"


def test_get_prop_returns_200_with_ev():
    with patch("backend.routes.props.get_game_logs", new_callable=AsyncMock,
               return_value=MOCK_LOGS * 10), \
         patch("backend.routes.props.get_player_props", new_callable=AsyncMock,
               return_value=MOCK_PROP), \
         patch("backend.routes.props.get_historical_lines", new_callable=AsyncMock,
               return_value=MOCK_HISTORICAL):
        r = client.get("/props/1/points?window=10&player_name=LeBron+James")
    assert r.status_code == 200
    data = r.json()
    assert "line" in data
    assert "ev" in data
    assert "your_prob" in data


def test_get_prop_returns_404_when_no_odds():
    with patch("backend.routes.props.get_game_logs", new_callable=AsyncMock,
               return_value=MOCK_LOGS * 10), \
         patch("backend.routes.props.get_player_props", new_callable=AsyncMock,
               return_value=None), \
         patch("backend.routes.props.get_historical_lines", new_callable=AsyncMock,
               return_value=MOCK_HISTORICAL):
        r = client.get("/props/1/points?window=10&player_name=LeBron+James")
    assert r.status_code == 404


def test_get_prop_returns_422_when_no_game_logs():
    with patch("backend.routes.props.get_game_logs", new_callable=AsyncMock,
               return_value=[]), \
         patch("backend.routes.props.get_player_props", new_callable=AsyncMock,
               return_value=MOCK_PROP), \
         patch("backend.routes.props.get_historical_lines", new_callable=AsyncMock,
               return_value=[]):
        r = client.get("/props/1/points?window=10&player_name=LeBron+James")
    assert r.status_code == 422
