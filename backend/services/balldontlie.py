import asyncio
from datetime import datetime
from functools import partial
from fastapi import HTTPException
from nba_api.stats.static import players as nba_players
from nba_api.stats.endpoints import playergamelog

STAT_MAP = {
    "points": "PTS",
    "rebounds": "REB",
    "assists": "AST",
    "steals": "STL",
    "blocks": "BLK",
    "minutes": "MIN",
}


def _current_season() -> str:
    now = datetime.now()
    year = now.year
    if now.month >= 10:
        return f"{year}-{str(year + 1)[2:]}"
    return f"{year - 1}-{str(year)[2:]}"


def _search_sync(name: str) -> list[dict]:
    all_active = nba_players.get_active_players()
    matches = [p for p in all_active if name.lower() in p["full_name"].lower()]
    return [
        {"id": p["id"], "name": p["full_name"], "team": ""}
        for p in matches[:10]
    ]


def _logs_sync(player_id: int, stat_category: str, window: int) -> list[dict]:
    field = STAT_MAP.get(stat_category.lower(), "PTS")
    season = _current_season()
    log = playergamelog.PlayerGameLog(player_id=player_id, season=season, timeout=30)
    df = log.get_data_frames()[0]
    if df.empty:
        return []
    if window > 0:
        df = df.head(window)
    result = []
    for _, row in df.iterrows():
        val = row.get(field, 0)
        if field == "MIN":
            val = _parse_minutes(str(val))
        else:
            val = float(val or 0)
        matchup = str(row.get("MATCHUP", ""))
        if "@" in matchup:
            home_away = "away"
            opponent = matchup.split("@")[-1].strip()
        else:
            home_away = "home"
            opponent = matchup.split("vs.")[-1].strip()
        result.append({
            "game_date": str(row.get("GAME_DATE", "")),
            "value": val,
            "opponent": opponent,
            "home_away": home_away,
        })
    return result


async def search_players(name: str) -> list[dict]:
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, partial(_search_sync, name))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"NBA API error: {e}")


async def get_game_logs(player_id: int, stat_category: str, window: int = 10) -> list[dict]:
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, partial(_logs_sync, player_id, stat_category, window))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"NBA API error: {e}")


def _parse_minutes(min_str: str) -> float:
    if not min_str or ":" not in min_str:
        return 0.0
    try:
        parts = min_str.split(":")
        return int(parts[0]) + int(parts[1]) / 60
    except (ValueError, IndexError):
        return 0.0
