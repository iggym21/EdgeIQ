import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.services.propodds import get_player_props, get_historical_lines
from backend.services.odds_api import get_player_props as odds_api_get_props

MOCK_PROPODDS_GAMES = {
    "games": [
        {"game_id": "game_abc123", "away_team": "BOS", "home_team": "LAL",
         "start_timestamp": "2024-01-12T00:00:00Z"}
    ]
}

MOCK_PROPODDS_PROPS = {
    "props": [
        {
            "player_name": "LeBron James",
            "handicap": 25.5,
            "over_price": -110,
            "under_price": -110,
            "book_name": "DraftKings",
            "timestamp": "2024-01-12T18:00:00Z",
        }
    ]
}

@pytest.mark.asyncio
async def test_get_player_props_returns_snapshot():
    with patch("backend.services.propodds.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(side_effect=[
            httpx.Response(200, json=MOCK_PROPODDS_GAMES),
            httpx.Response(200, json=MOCK_PROPODDS_PROPS),
        ])
        mock_client.return_value.__aenter__.return_value.get = mock_get
        result = await get_player_props("LeBron James", "points")

    assert result is not None
    assert result["line"] == 25.5
    assert result["over_odds"] == -110
    assert result["source"] == "propodds"

@pytest.mark.asyncio
async def test_get_player_props_returns_none_when_not_found():
    empty = {"games": []}
    with patch("backend.services.propodds.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=empty)
        )
        result = await get_player_props("Unknown Player", "points")
    assert result is None


MOCK_ODDS_API_RESPONSE = [
    {
        "id": "event_xyz",
        "bookmakers": [
            {
                "title": "FanDuel",
                "markets": [
                    {
                        "key": "player_points",
                        "outcomes": [
                            {"name": "Over", "description": "LeBron James", "price": -115, "point": 25.5},
                            {"name": "Under", "description": "LeBron James", "price": -105, "point": 25.5},
                        ]
                    }
                ]
            }
        ]
    }
]

@pytest.mark.asyncio
async def test_odds_api_get_player_props_returns_snapshot():
    with patch("backend.services.odds_api.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=MOCK_ODDS_API_RESPONSE)
        )
        result = await odds_api_get_props("LeBron James", "points")
    assert result is not None
    assert result["line"] == 25.5
    assert result["over_odds"] == -115
    assert result["source"] == "odds_api"

@pytest.mark.asyncio
async def test_odds_api_get_player_props_returns_none_when_not_found():
    with patch("backend.services.odds_api.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=[])
        )
        result = await odds_api_get_props("Unknown Player", "points")
    assert result is None


MOCK_HISTORICAL_RESPONSE = {
    "props": [
        {
            "player_name": "LeBron James",
            "handicap": 24.5,
            "over_price": -108,
            "under_price": -112,
            "book_name": "DraftKings",
            "timestamp": "2024-01-10T12:00:00Z",
        },
        {
            "player_name": "Anthony Davis",
            "handicap": 30.5,
            "over_price": -110,
            "under_price": -110,
            "book_name": "DraftKings",
            "timestamp": "2024-01-10T12:00:00Z",
        }
    ]
}

@pytest.mark.asyncio
async def test_get_historical_lines_filters_by_player():
    with patch("backend.services.propodds.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=MOCK_HISTORICAL_RESPONSE)
        )
        result = await get_historical_lines("LeBron James", "points")
    assert len(result) == 1
    assert result[0]["line"] == 24.5
    assert result[0]["source"] == "propodds"
