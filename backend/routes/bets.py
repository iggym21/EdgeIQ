from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from backend.db import get_connection

router = APIRouter(prefix="/bets", tags=["bets"])


class BetCreate(BaseModel):
    player_name: str
    stat_category: str
    line: float
    direction: Literal["over", "under"]
    odds: int
    stake: float
    ev_at_bet: Optional[float] = None


class BetUpdate(BaseModel):
    result: Optional[Literal["win", "loss", "push", "pending"]] = None
    profit_loss: Optional[float] = None


@router.post("", status_code=201)
def create_bet(payload: BetCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO bets (player_name, stat_category, line, direction, odds,
                             stake, ev_at_bet)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (payload.player_name, payload.stat_category, payload.line,
         payload.direction, payload.odds, payload.stake, payload.ev_at_bet),
    )
    conn.commit()
    return _get_bet(cur.lastrowid, conn)


@router.get("")
def list_bets():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM bets ORDER BY placed_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.patch("/{bet_id}")
def update_bet(bet_id: int, payload: BetUpdate):
    conn = get_connection()
    fields, values = [], []
    if payload.result is not None:
        fields.append("result = ?")
        values.append(payload.result)
    if payload.profit_loss is not None:
        fields.append("profit_loss = ?")
        values.append(payload.profit_loss)
    if not fields:
        raise HTTPException(status_code=422, detail="No fields to update")
    values.append(bet_id)
    conn.execute(f"UPDATE bets SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    return _get_bet(bet_id, conn)


def _get_bet(bet_id: int, conn):
    row = conn.execute("SELECT * FROM bets WHERE id = ?", (bet_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Bet not found")
    return dict(row)
