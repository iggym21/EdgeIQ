import asyncio
from fastapi import APIRouter, HTTPException, Query
from backend.services.balldontlie import search_players, get_game_logs
from backend.services.propodds import get_player_props, get_historical_lines
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
    logs, prop, historical = await _fetch_logs_and_prop(player_id, stat_category, window, player_name)
    if prop is None:
        raise HTTPException(status_code=404, detail="No odds found for this prop")

    if prop.get("line") is None or prop.get("over_odds") is None:
        raise HTTPException(
            status_code=422,
            detail="Prop data is incomplete (missing line or odds)"
        )

    values = [g["value"] for g in logs]
    if not values:
        raise HTTPException(
            status_code=422,
            detail=f"No game log data found for this player and stat category"
        )

    your_prob = calc_probability(values, prop["line"], stat_category)
    ev_data = calc_ev(your_prob, prop["over_odds"])

    return {
        **prop,
        **ev_data,
        "game_log": logs,
        "distribution": get_distribution(stat_category),
        "window": window if window > 0 else "season",
        "sample_size": len(values),
        "low_confidence": len(values) < 10,
        "historical_lines": historical,
    }


async def _fetch_logs_and_prop(player_id, stat_category, window, player_name):
    return await asyncio.gather(
        get_game_logs(player_id, stat_category, window),
        get_player_props(player_name, stat_category),
        get_historical_lines(player_name, stat_category),
    )
