import httpx
from fastapi import HTTPException
from backend.config import BDL_API_KEY

BASE_URL = "https://api.balldontlie.io/v1"
HEADERS = {"Authorization": BDL_API_KEY}

STAT_MAP = {
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "steals": "stl",
    "blocks": "blk",
    "minutes": "min",
}


async def search_players(name: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BASE_URL}/players",
            params={"search": name, "per_page": 10},
            headers=HEADERS,
        )
    if r.status_code == 401:
        raise HTTPException(status_code=502, detail="BallDontLie API key is invalid or missing")
    if r.status_code == 429:
        raise HTTPException(status_code=429, detail="BallDontLie rate limit hit — try again in a moment")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"BallDontLie error: {r.status_code}")
    return [
        {
            "id": p["id"],
            "name": f"{p['first_name']} {p['last_name']}",
            "team": p.get("team", {}).get("full_name", ""),
        }
        for p in r.json()["data"]
    ]


async def get_game_logs(
    player_id: int, stat_category: str, window: int = 10
) -> list[dict]:
    field = STAT_MAP.get(stat_category.lower(), "pts")
    # window=0 means full season — fetch up to 100 games
    per_page = 100 if window == 0 else max(window, 25)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BASE_URL}/stats",
            params={
                "player_ids[]": player_id,
                "per_page": per_page,
                "seasons[]": 2024,  # TODO: update to current season each year
            },
            headers=HEADERS,
        )
    if r.status_code == 401:
        raise HTTPException(status_code=502, detail="BallDontLie API key is invalid or missing")
    if r.status_code == 429:
        raise HTTPException(status_code=429, detail="BallDontLie rate limit hit — try again in a moment")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"BallDontLie error: {r.status_code}")

    games = sorted(r.json()["data"], key=lambda g: g.get("game", {}).get("date", ""), reverse=True)
    if window > 0:
        games = games[:window]

    result = []
    for g in games:
        player_team_id = g.get("team", {}).get("id")
        home_team_id = g.get("game", {}).get("home_team_id")
        result.append({
            "game_date": g.get("game", {}).get("date", ""),
            "value": _parse_minutes(g[field]) if field == "min" else (g[field] or 0),
            "opponent": "",  # BDL stats endpoint doesn't include opponent team details
            "home_away": "home" if player_team_id == home_team_id else "away",
        })
    return result


def _parse_minutes(min_str: str) -> float:
    """Convert '35:30' → 35.5"""
    if not min_str or ":" not in min_str:
        return 0.0
    try:
        parts = min_str.split(":")
        return int(parts[0]) + int(parts[1]) / 60
    except (ValueError, IndexError):
        return 0.0
