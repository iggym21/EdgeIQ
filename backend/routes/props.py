import asyncio
from fastapi import APIRouter, HTTPException, Query
from backend.services.balldontlie import search_players, get_game_logs
from backend.services.odds_api import get_player_props
from backend.services.model import calc_probability, calc_ev, get_distribution

router = APIRouter(prefix="/props", tags=["props"])


@router.get("/search")
async def search(q: str = Query(..., min_length=2)):
    return await search_players(q)


@router.get("/{player_id}/{stat_category}")
async def get_prop(
    player_id: int,
    stat_category: str,
    window: int = Query(default=10, ge=0),
    player_name: str = Query(...),
):
    # Fetch full season + windowed logs + odds concurrently
    full_logs, prop = await asyncio.gather(
        get_game_logs(player_id, stat_category, 0),   # full season (window=0)
        get_player_props(player_name, stat_category),
    )

    logs = full_logs[:window] if window > 0 else full_logs
    historical = []

    values = [g["value"] for g in logs]
    if not values:
        raise HTTPException(
            status_code=422,
            detail="No game log data found for this player and stat category"
        )

    # No odds available — return logs without EV so the frontend can offer manual input
    if prop is None or prop.get("line") is None or prop.get("over_odds") is None:
        return {
            "player_name": player_name,
            "stat_category": stat_category,
            "game_log": logs,
            "full_season_log": full_logs,
            "distribution": get_distribution(stat_category),
            "window": window if window > 0 else "season",
            "sample_size": len(values),
            "low_confidence": len(values) < 10,
            "historical_lines": historical,
            "odds_available": False,
        }

    your_prob = calc_probability(values, prop["line"], stat_category)
    ev_data = calc_ev(your_prob, prop["over_odds"])

    return {
        **prop,
        **ev_data,
        "game_log": logs,
        "full_season_log": full_logs,
        "distribution": get_distribution(stat_category),
        "window": window if window > 0 else "season",
        "sample_size": len(values),
        "low_confidence": len(values) < 10,
        "historical_lines": historical,
        "odds_available": True,
    }
