import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise ValueError(f"{key} is not set. Copy .env.example to .env and fill in your API keys.")
    return val

ODDS_API_KEY = _require("ODDS_API_KEY")
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "edgeiq.db")
