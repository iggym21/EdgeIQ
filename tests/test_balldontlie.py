import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.services.balldontlie import search_players, get_game_logs

MOCK_SEARCH_RESPONSE = {
    "data": [
        {"id": 1, "first_name": "LeBron", "last_name": "James",
         "team": {"full_name": "Los Angeles Lakers"}}
    ]
}

MOCK_STATS_RESPONSE = {
    "data": [
        {"pts": 28, "reb": 7, "ast": 8,
         "stl": 1, "blk": 0, "min": "35:00",
         "team": {"abbreviation": "LAL", "id": 14}, "game": {"home_team_id": 14, "date": "2024-01-10"}},
        {"pts": 32, "reb": 9, "ast": 5,
         "stl": 2, "blk": 1, "min": "38:00",
         "team": {"abbreviation": "LAL", "id": 14}, "game": {"home_team_id": 14, "date": "2024-01-08"}},
    ]
}

@pytest.mark.asyncio
async def test_search_players_returns_list():
    with patch("backend.services.balldontlie.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=MOCK_SEARCH_RESPONSE)
        )
        results = await search_players("LeBron")
    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["name"] == "LeBron James"
    assert results[0]["team"] == "Los Angeles Lakers"

@pytest.mark.asyncio
async def test_get_game_logs_extracts_stat():
    with patch("backend.services.balldontlie.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=MOCK_STATS_RESPONSE)
        )
        logs = await get_game_logs(player_id=1, stat_category="points", window=10)
    assert len(logs) == 2
    assert logs[0]["game_date"] == "2024-01-10"
    assert logs[0]["value"] == 28
    assert "opponent" in logs[0]  # empty string is fine for now
    assert logs[0]["home_away"] == "home"  # team id 14 == home_team_id 14

@pytest.mark.asyncio
async def test_get_game_logs_respects_window():
    many_games = {"data": [
        {"pts": 20, "reb": 5, "ast": 5,
         "stl": 1, "blk": 0, "min": "32:00",
         "team": {"abbreviation": "LAL"}, "game": {"home_team_id": 14, "date": f"2024-01-{i:02d}"}}
        for i in range(1, 21)  # 20 games
    ]}
    with patch("backend.services.balldontlie.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=many_games)
        )
        logs = await get_game_logs(player_id=1, stat_category="points", window=10)
    assert len(logs) == 10  # only last 10
