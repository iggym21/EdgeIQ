from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from backend.services.model import calc_probability, calc_ev, get_distribution

router = APIRouter(prefix="/ev", tags=["ev"])


class EVRequest(BaseModel):
    game_log_values: list[float]
    line: float
    odds: int
    stat_category: str

    @field_validator("game_log_values")
    @classmethod
    def must_not_be_empty(cls, v):
        if not v:
            raise ValueError("game_log_values must not be empty")
        return v


@router.post("")
def calculate_ev(payload: EVRequest):
    your_prob = calc_probability(
        payload.game_log_values, payload.line, payload.stat_category
    )
    ev_data = calc_ev(your_prob, payload.odds)
    return {
        **ev_data,
        "distribution": get_distribution(payload.stat_category),
        "sample_size": len(payload.game_log_values),
        "low_confidence": len(payload.game_log_values) < 10,
    }
