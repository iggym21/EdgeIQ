import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from backend.services.balldontlie import search_players, get_game_logs

MOCK_PLAYERS = [
    {"id": 2544, "full_name": "LeBron James", "first_name": "LeBron",
     "last_name": "James", "is_active": True},
]

MOCK_DF = pd.DataFrame([
    {"GAME_DATE": "JAN 10, 2024", "PTS": 28, "REB": 7, "AST": 8,
     "STL": 1, "BLK": 0, "MIN": "35:00", "MATCHUP": "LAL vs. BOS"},
    {"GAME_DATE": "JAN 08, 2024", "PTS": 32, "REB": 9, "AST": 5,
     "STL": 2, "BLK": 1, "MIN": "38:00", "MATCHUP": "LAL @ GSW"},
])


@pytest.mark.asyncio
async def test_search_players_returns_list():
    with patch("backend.services.balldontlie.nba_players.get_active_players",
               return_value=MOCK_PLAYERS):
        results = await search_players("LeBron")
    assert len(results) == 1
    assert results[0]["id"] == 2544
    assert results[0]["name"] == "LeBron James"


@pytest.mark.asyncio
async def test_get_game_logs_extracts_stat():
    mock_log = MagicMock()
    mock_log.get_data_frames.return_value = [MOCK_DF]
    with patch("backend.services.balldontlie.playergamelog.PlayerGameLog",
               return_value=mock_log):
        logs = await get_game_logs(player_id=2544, stat_category="points", window=10)
    assert len(logs) == 2
    assert logs[0]["value"] == 28.0
    assert logs[0]["home_away"] == "home"
    assert logs[1]["home_away"] == "away"
    assert "opponent" in logs[0]


@pytest.mark.asyncio
async def test_get_game_logs_respects_window():
    many_rows = [
        {"GAME_DATE": f"JAN {i:02d}, 2024", "PTS": 20, "REB": 5, "AST": 5,
         "STL": 1, "BLK": 0, "MIN": "32:00", "MATCHUP": "LAL vs. BOS"}
        for i in range(1, 21)
    ]
    big_df = pd.DataFrame(many_rows)
    mock_log = MagicMock()
    mock_log.get_data_frames.return_value = [big_df]
    with patch("backend.services.balldontlie.playergamelog.PlayerGameLog",
               return_value=mock_log):
        logs = await get_game_logs(player_id=2544, stat_category="points", window=10)
    assert len(logs) == 10
