import httpx
from datetime import date
from backend.config import PROPODDS_API_KEY

BASE_URL = "https://api.prop-odds.com/beta"

MARKET_MAP = {
    "points": "player_points",
    "rebounds": "player_rebounds",
    "assists": "player_assists",
    "steals": "player_steals",
    "blocks": "player_blocks",
    "minutes": "player_minutes",
}


async def get_player_props(player_name: str, stat_category: str) -> dict | None:
    market = MARKET_MAP.get(stat_category.lower(), "player_points")
    today = date.today().isoformat()

    async with httpx.AsyncClient(timeout=10.0) as client:
        games_r = await client.get(
            f"{BASE_URL}/games/basketball_nba",
            params={"date": today, "tz": "America/New_York", "apiKey": PROPODDS_API_KEY},
        )
        if games_r.status_code >= 400:
            games_r.raise_for_status()
        games = games_r.json().get("games", [])
        if not games:
            return None

        for game in games:
            props_r = await client.get(
                f"{BASE_URL}/props/{game['game_id']}/{market}",
                params={"apiKey": PROPODDS_API_KEY},
            )
            if props_r.status_code != 200:
                continue
            for prop in props_r.json().get("props", []):
                if prop.get("player_name", "").lower() == player_name.lower():
                    return {
                        "game_id": game["game_id"],
                        "player_name": prop.get("player_name", player_name),
                        "stat_category": stat_category,
                        "line": prop.get("handicap"),
                        "over_odds": prop.get("over_price"),
                        "under_odds": prop.get("under_price"),
                        "book": prop.get("book_name", "consensus"),
                        "source": "propodds",
                    }
    return None


async def get_historical_lines(player_name: str, stat_category: str) -> list[dict]:
    """Fetch historical odds snapshots for line movement chart."""
    market = MARKET_MAP.get(stat_category.lower(), "player_points")

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BASE_URL}/historical/basketball_nba/{market}",
            params={"player_name": player_name, "apiKey": PROPODDS_API_KEY},
        )
        if r.status_code != 200:
            return []
        snaps = r.json().get("props", [])

    return [
        {
            "line": snap.get("handicap"),
            "over_odds": snap.get("over_price"),
            "under_odds": snap.get("under_price"),
            "book": snap.get("book_name", "consensus"),
            "source": "propodds",
            "snapshot_time": snap.get("timestamp"),
        }
        for snap in snaps
        if snap.get("player_name", "").lower() == player_name.lower()
    ]
