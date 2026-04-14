import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.services.odds_api import get_player_props as odds_api_get_props

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
