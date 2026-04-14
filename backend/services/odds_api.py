import httpx
from backend.config import ODDS_API_KEY

BASE_URL = "https://api.the-odds-api.com/v4"

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

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BASE_URL}/sports/basketball_nba/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": market,
                "oddsFormat": "american",
            },
        )
        if r.status_code >= 400:
            return None
        events = r.json()

    for event in events:
        for bookmaker in event.get("bookmakers", []):
            for market_data in bookmaker.get("markets", []):
                for outcome in market_data.get("outcomes", []):
                    if (
                        outcome.get("description", "").lower() == player_name.lower()
                        and outcome.get("name") == "Over"
                    ):
                        over_price = outcome["price"]
                        under_price = next(
                            (o["price"] for o in market_data["outcomes"]
                             if o.get("description", "").lower() == player_name.lower()
                             and o.get("name") == "Under"),
                            None,
                        )
                        return {
                            "game_id": event["id"],
                            "player_name": player_name,
                            "stat_category": stat_category,
                            "line": outcome.get("point"),
                            "over_odds": over_price,
                            "under_odds": under_price,
                            "book": bookmaker["title"],
                            "source": "odds_api",
                        }
    return None
