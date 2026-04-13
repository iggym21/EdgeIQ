# EdgeIQ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack NBA player prop analysis tool with distribution modeling, EV calculation, line movement tracking, and an AI chat assistant.

**Architecture:** React/Vite frontend (Vercel) communicates via REST and SSE to a FastAPI backend (Render). The backend fetches NBA game logs from BallDontLie, odds from PropOdds (primary) and The Odds API (manual refresh fallback), runs scipy-based distribution fitting, and streams Claude responses. SQLite stores all cached data, snapshots, and bets — schema includes nullable `user_id` on every table for future multi-user migration.

**Tech Stack:** Python 3.11, FastAPI, sqlite3, scipy, numpy, httpx, anthropic SDK (claude-sonnet-4-6), pytest, pytest-asyncio, React 18, Vite, Recharts, TailwindCSS, Axios

---

## File Map

```
edgeiq/
├── backend/
│   ├── config.py               # Env vars (API keys, DB path)
│   ├── db.py                   # SQLite connection + table creation
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── props.py            # GET /props/search, GET /props/{player}/{stat}
│   │   ├── ev.py               # POST /ev
│   │   ├── chat.py             # POST /chat (SSE stream)
│   │   └── bets.py             # GET/POST/PATCH /bets
│   ├── services/
│   │   ├── __init__.py
│   │   ├── balldontlie.py      # BallDontLie API client
│   │   ├── propodds.py         # PropOdds API client
│   │   ├── odds_api.py         # The Odds API client (manual refresh)
│   │   └── model.py            # Distribution fitting + EV math
│   └── ai/
│       ├── __init__.py
│       └── prompt.py           # System prompt builder
├── tests/
│   ├── conftest.py             # Shared fixtures (test DB, test client)
│   ├── test_db.py
│   ├── test_model.py
│   ├── test_ev_route.py
│   ├── test_props_route.py
│   └── test_bets_route.py
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx             # React Router setup
│   │   ├── api/
│   │   │   └── client.js       # Axios instance + request helpers
│   │   ├── pages/
│   │   │   ├── Analyze.jsx     # Search + prop analysis layout
│   │   │   └── Tracker.jsx     # Bet history + P&L
│   │   └── components/
│   │       ├── DistChart.jsx   # Histogram + fitted curve + threshold
│   │       ├── EVCard.jsx      # EV verdict + Log Bet button
│   │       ├── LineMove.jsx    # Odds sparkline + sharp flag
│   │       ├── ChatSidebar.jsx # SSE streaming chat panel
│   │       └── BetForm.jsx     # Bet logging modal
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── .env                        # PROPODDS_API_KEY, ODDS_API_KEY, ANTHROPIC_API_KEY, BDL_API_KEY
├── .env.example
└── requirements.txt
```

---

## Phase 1 — Foundation

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `backend/config.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/routes backend/services backend/ai tests
touch backend/__init__.py backend/routes/__init__.py backend/services/__init__.py backend/ai/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
httpx==0.27.0
scipy==1.13.0
numpy==1.26.4
anthropic==0.28.0
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.6
httpx==0.27.0
```

- [ ] **Step 3: Create .env.example**

```
BDL_API_KEY=your_balldontlie_api_key
PROPODDS_API_KEY=your_propodds_api_key
ODDS_API_KEY=your_odds_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=edgeiq.db
```

- [ ] **Step 4: Create backend/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

BDL_API_KEY = os.environ["BDL_API_KEY"]
PROPODDS_API_KEY = os.environ["PROPODDS_API_KEY"]
ODDS_API_KEY = os.environ["ODDS_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DATABASE_URL = os.getenv("DATABASE_URL", "edgeiq.db")
```

- [ ] **Step 5: Install Python dependencies**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 6: Scaffold React/Vite frontend**

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install axios recharts react-router-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 7: Configure tailwind.config.js**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 8: Add Tailwind to frontend/src/index.css** (create if not present)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 9: Update frontend/src/main.jsx**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 10: Verify frontend dev server starts**

```bash
cd frontend && npm run dev
```

Expected: Vite dev server running at http://localhost:5173

- [ ] **Step 11: Commit**

```bash
git add requirements.txt .env.example backend/ frontend/ tests/
git commit -m "chore: scaffold monorepo — FastAPI backend + React/Vite frontend"
```

---

### Task 2: Database Layer

**Files:**
- Create: `backend/db.py`
- Create: `tests/test_db.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_db.py
import sqlite3
import pytest
from backend.db import get_connection, init_db

def test_init_db_creates_all_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "player_stats" in tables
    assert "odds_snapshots" in tables
    assert "bets" in tables
    assert "line_movements" in tables
    conn.close()

def test_player_stats_has_user_id_column(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(player_stats)")
    columns = {row[1] for row in cursor.fetchall()}
    assert "user_id" in columns
    assert "window" in columns
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_db.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `backend.db` doesn't exist yet.

- [ ] **Step 3: Create backend/db.py**

```python
import sqlite3
from backend.config import DATABASE_URL


def get_connection(db_path: str = DATABASE_URL) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DATABASE_URL) -> sqlite3.Connection:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id     TEXT NOT NULL,
            player_name   TEXT NOT NULL,
            sport         TEXT NOT NULL DEFAULT 'nba',
            game_date     DATE NOT NULL,
            stat_category TEXT NOT NULL,
            value         REAL NOT NULL,
            opponent      TEXT,
            home_away     TEXT,
            window        INTEGER NOT NULL DEFAULT 10,
            fetched_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id       TEXT
        );

        CREATE TABLE IF NOT EXISTS odds_snapshots (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id       TEXT,
            player_name   TEXT NOT NULL,
            stat_category TEXT NOT NULL,
            line          REAL NOT NULL,
            over_odds     INTEGER NOT NULL,
            under_odds    INTEGER NOT NULL,
            book          TEXT NOT NULL,
            source        TEXT NOT NULL DEFAULT 'propodds',
            snapshot_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id       TEXT
        );

        CREATE TABLE IF NOT EXISTS bets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name   TEXT NOT NULL,
            stat_category TEXT NOT NULL,
            line          REAL NOT NULL,
            direction     TEXT NOT NULL CHECK (direction IN ('over', 'under')),
            odds          INTEGER NOT NULL,
            stake         REAL NOT NULL,
            ev_at_bet     REAL,
            result        TEXT NOT NULL DEFAULT 'pending'
                              CHECK (result IN ('win', 'loss', 'push', 'pending')),
            profit_loss   REAL,
            placed_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id       TEXT
        );

        CREATE TABLE IF NOT EXISTS line_movements (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            odds_snapshot_id INTEGER REFERENCES odds_snapshots(id),
            open_line        REAL NOT NULL,
            current_line     REAL NOT NULL,
            delta            REAL NOT NULL,
            sharp_flag       INTEGER NOT NULL DEFAULT 0,
            recorded_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id          TEXT
        );
    """)
    conn.commit()
    return conn
```

- [ ] **Step 4: Create tests/conftest.py**

```python
import pytest
from backend.db import init_db

@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    yield conn
    conn.close()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_db.py -v
```

Expected: 2 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/db.py backend/config.py tests/conftest.py tests/test_db.py
git commit -m "feat: database layer — SQLite schema with all four tables"
```

---

### Task 3: Distribution Model Service

**Files:**
- Create: `backend/services/model.py`
- Create: `tests/test_model.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_model.py
import pytest
from backend.services.model import (
    get_distribution,
    calc_probability,
    calc_ev,
)

def test_get_distribution_poisson_for_counting_stats():
    assert get_distribution("points") == "poisson"
    assert get_distribution("rebounds") == "poisson"
    assert get_distribution("assists") == "poisson"
    assert get_distribution("steals") == "poisson"
    assert get_distribution("blocks") == "poisson"

def test_get_distribution_normal_for_minutes():
    assert get_distribution("minutes") == "normal"

def test_calc_probability_poisson_over_line():
    # Player averaged 25 pts over 10 games, line is 22.5
    values = [25, 28, 22, 30, 24, 26, 20, 29, 25, 27]
    prob = calc_probability(values, 22.5, "points")
    assert 0.5 < prob < 1.0  # high probability, line is below average

def test_calc_probability_poisson_under_line():
    values = [10, 12, 8, 11, 9, 13, 10, 11, 9, 10]
    prob = calc_probability(values, 20.5, "points")
    assert 0.0 < prob < 0.1  # very low probability, line is far above average

def test_calc_probability_normal_minutes():
    values = [32.0, 34.0, 30.0, 33.0, 31.0, 35.0, 32.0, 33.0, 31.0, 34.0]
    prob = calc_probability(values, 28.5, "minutes")
    assert prob > 0.9  # nearly certain to exceed 28.5

def test_calc_probability_raises_on_empty_values():
    with pytest.raises(ValueError, match="values must not be empty"):
        calc_probability([], 20.5, "points")

def test_calc_ev_positive_odds():
    # +110 odds, 60% modeled probability
    result = calc_ev(0.60, 110)
    assert result["implied_prob"] == pytest.approx(100 / 210, abs=0.001)
    assert result["potential_win"] == pytest.approx(1.10, abs=0.001)
    assert result["ev"] > 0  # should be positive EV
    assert result["kelly_fraction"] > 0

def test_calc_ev_negative_odds():
    # -120 odds, 55% modeled probability
    result = calc_ev(0.55, -120)
    assert result["implied_prob"] == pytest.approx(120 / 220, abs=0.001)
    assert result["potential_win"] == pytest.approx(100 / 120, abs=0.001)

def test_calc_ev_kelly_never_negative():
    # Low probability vs high negative odds → kelly should be 0, not negative
    result = calc_ev(0.30, -200)
    assert result["kelly_fraction"] == 0.0

def test_calc_ev_edge_pct():
    result = calc_ev(0.60, 110)
    implied = 100 / 210
    assert result["edge_pct"] == pytest.approx((0.60 - implied) * 100, abs=0.01)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_model.py -v
```

Expected: `ImportError` — `backend.services.model` doesn't exist.

- [ ] **Step 3: Create backend/services/model.py**

```python
import numpy as np
from scipy.stats import poisson, norm

POISSON_STATS = {"points", "rebounds", "assists", "steals", "blocks"}


def get_distribution(stat_category: str) -> str:
    return "poisson" if stat_category.lower() in POISSON_STATS else "normal"


def calc_probability(values: list[float], line: float, stat_category: str) -> float:
    if not values:
        raise ValueError("values must not be empty")
    dist = get_distribution(stat_category)
    if dist == "poisson":
        lam = float(np.mean(values))
        return float(1 - poisson.cdf(int(line), lam))
    else:
        mu = float(np.mean(values))
        sigma = float(np.std(values))
        if sigma == 0:
            return 1.0 if mu > line else 0.0
        return float(1 - norm.cdf(line, mu, sigma))


def calc_ev(your_prob: float, odds: int) -> dict:
    if odds > 0:
        implied_prob = 100 / (odds + 100)
        potential_win = odds / 100
    else:
        implied_prob = abs(odds) / (abs(odds) + 100)
        potential_win = 100 / abs(odds)

    ev = (your_prob * potential_win) - ((1 - your_prob) * 1)
    kelly_raw = (your_prob * (potential_win + 1) - 1) / potential_win
    kelly = max(0.0, kelly_raw)

    return {
        "your_prob": round(your_prob, 4),
        "implied_prob": round(implied_prob, 4),
        "ev": round(ev, 4),
        "edge_pct": round((your_prob - implied_prob) * 100, 2),
        "kelly_fraction": round(kelly, 4),
        "potential_win": round(potential_win, 4),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_model.py -v
```

Expected: 9 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/services/model.py tests/test_model.py
git commit -m "feat: distribution model — Poisson/normal fitting and EV/Kelly calculation"
```

---

### Task 4: BallDontLie Service

**Files:**
- Create: `backend/services/balldontlie.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_balldontlie.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.services.balldontlie import search_players, get_game_logs

MOCK_SEARCH_RESPONSE = {
    "data": [
        {"id": 1, "first_name": "LeBron", "last_name": "James",
         "team": {"full_name": "Los Angeles Lakers"}}
    ]
}

MOCK_STATS_RESPONSE = {
    "data": [
        {"date": "2024-01-10", "pts": 28, "reb": 7, "ast": 8,
         "stl": 1, "blk": 0, "min": "35:00",
         "team": {"abbreviation": "LAL"}, "game": {"home_team_id": 14}},
        {"date": "2024-01-08", "pts": 32, "reb": 9, "ast": 5,
         "stl": 2, "blk": 1, "min": "38:00",
         "team": {"abbreviation": "LAL"}, "game": {"home_team_id": 14}},
    ]
}

@pytest.mark.asyncio
async def test_search_players_returns_list():
    with patch("backend.services.balldontlie.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=MOCK_SEARCH_RESPONSE)
        )
        results = await search_players("LeBron")
    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["name"] == "LeBron James"
    assert results[0]["team"] == "Los Angeles Lakers"

@pytest.mark.asyncio
async def test_get_game_logs_extracts_stat():
    with patch("backend.services.balldontlie.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=MOCK_STATS_RESPONSE)
        )
        logs = await get_game_logs(player_id=1, stat_category="points", window=10)
    assert len(logs) == 2
    assert logs[0]["value"] == 28
    assert logs[0]["game_date"] == "2024-01-10"

@pytest.mark.asyncio
async def test_get_game_logs_respects_window():
    many_games = {"data": [
        {"date": f"2024-01-{i:02d}", "pts": 20, "reb": 5, "ast": 5,
         "stl": 1, "blk": 0, "min": "32:00",
         "team": {"abbreviation": "LAL"}, "game": {"home_team_id": 14}}
        for i in range(1, 21)  # 20 games
    ]}
    with patch("backend.services.balldontlie.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=many_games)
        )
        logs = await get_game_logs(player_id=1, stat_category="points", window=10)
    assert len(logs) == 10  # only last 10
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_balldontlie.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create backend/services/balldontlie.py**

```python
import httpx
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
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/players",
            params={"search": name, "per_page": 10},
            headers=HEADERS,
        )
        r.raise_for_status()
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

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/stats",
            params={
                "player_ids[]": player_id,
                "per_page": per_page,
                "seasons[]": 2024,
            },
            headers=HEADERS,
        )
        r.raise_for_status()

    games = sorted(r.json()["data"], key=lambda g: g["date"], reverse=True)
    if window > 0:
        games = games[:window]

    return [
        {
            "game_date": g["date"],
            "value": _parse_minutes(g[field]) if field == "min" else (g[field] or 0),
            "opponent": g.get("team", {}).get("abbreviation", ""),
            "home_away": "home" if g.get("game", {}).get("home_team_id") == player_id else "away",
        }
        for g in games
    ]


def _parse_minutes(min_str: str) -> float:
    """Convert '35:30' → 35.5"""
    if not min_str or ":" not in min_str:
        return 0.0
    parts = min_str.split(":")
    return int(parts[0]) + int(parts[1]) / 60
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_balldontlie.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/services/balldontlie.py tests/test_balldontlie.py
git commit -m "feat: BallDontLie service — player search and game log fetching"
```

---

### Task 5: PropOdds + Odds API Services

**Files:**
- Create: `backend/services/propodds.py`
- Create: `backend/services/odds_api.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_odds_services.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.services.propodds import get_player_props, get_historical_lines
from backend.services.odds_api import get_player_props as odds_api_get_props

MOCK_PROPODDS_GAMES = {
    "games": [
        {"game_id": "game_abc123", "away_team": "BOS", "home_team": "LAL",
         "start_timestamp": "2024-01-12T00:00:00Z"}
    ]
}

MOCK_PROPODDS_PROPS = {
    "props": [
        {
            "player_name": "LeBron James",
            "handicap": 25.5,
            "over_price": -110,
            "under_price": -110,
            "book_name": "DraftKings",
            "timestamp": "2024-01-12T18:00:00Z",
        }
    ]
}

@pytest.mark.asyncio
async def test_get_player_props_returns_snapshot():
    with patch("backend.services.propodds.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(side_effect=[
            httpx.Response(200, json=MOCK_PROPODDS_GAMES),
            httpx.Response(200, json=MOCK_PROPODDS_PROPS),
        ])
        mock_client.return_value.__aenter__.return_value.get = mock_get
        result = await get_player_props("LeBron James", "points")

    assert result is not None
    assert result["line"] == 25.5
    assert result["over_odds"] == -110
    assert result["source"] == "propodds"

@pytest.mark.asyncio
async def test_get_player_props_returns_none_when_not_found():
    empty = {"games": []}
    with patch("backend.services.propodds.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=empty)
        )
        result = await get_player_props("Unknown Player", "points")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_odds_services.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create backend/services/propodds.py**

```python
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

    async with httpx.AsyncClient() as client:
        games_r = await client.get(
            f"{BASE_URL}/games/basketball_nba",
            params={"date": today, "tz": "America/New_York", "apiKey": PROPODDS_API_KEY},
        )
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
                if prop["player_name"].lower() == player_name.lower():
                    return {
                        "game_id": game["game_id"],
                        "player_name": prop["player_name"],
                        "stat_category": stat_category,
                        "line": prop["handicap"],
                        "over_odds": prop["over_price"],
                        "under_odds": prop["under_price"],
                        "book": prop.get("book_name", "consensus"),
                        "source": "propodds",
                    }
    return None


async def get_historical_lines(player_name: str, stat_category: str) -> list[dict]:
    """Fetch historical odds snapshots for line movement chart."""
    market = MARKET_MAP.get(stat_category.lower(), "player_points")

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/historical/basketball_nba/{market}",
            params={"player_name": player_name, "apiKey": PROPODDS_API_KEY},
        )
        if r.status_code != 200:
            return []

    return [
        {
            "line": snap["handicap"],
            "over_odds": snap["over_price"],
            "under_odds": snap["under_price"],
            "book": snap.get("book_name", "consensus"),
            "source": "propodds",
            "snapshot_time": snap.get("timestamp"),
        }
        for snap in r.json().get("props", [])
        if snap["player_name"].lower() == player_name.lower()
    ]
```

- [ ] **Step 4: Create backend/services/odds_api.py**

```python
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

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/sports/basketball_nba/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": market,
                "oddsFormat": "american",
            },
        )
        r.raise_for_status()

    for event in r.json():
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
                            -110,
                        )
                        return {
                            "game_id": event["id"],
                            "player_name": player_name,
                            "stat_category": stat_category,
                            "line": outcome["point"],
                            "over_odds": over_price,
                            "under_odds": under_price,
                            "book": bookmaker["title"],
                            "source": "odds_api",
                        }
    return None
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_odds_services.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/services/propodds.py backend/services/odds_api.py tests/test_odds_services.py
git commit -m "feat: PropOdds and Odds API service clients"
```

---

### Task 6: Props Route

**Files:**
- Create: `backend/routes/props.py`
- Create: `tests/test_props_route.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_props_route.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

MOCK_PLAYERS = [{"id": 1, "name": "LeBron James", "team": "Los Angeles Lakers"}]
MOCK_LOGS = [{"game_date": "2024-01-10", "value": 28, "opponent": "BOS", "home_away": "away"}]
MOCK_PROP = {
    "game_id": "abc", "player_name": "LeBron James", "stat_category": "points",
    "line": 25.5, "over_odds": -110, "under_odds": -110,
    "book": "DraftKings", "source": "propodds",
}

def test_search_players_returns_200():
    with patch("backend.routes.props.search_players", new_callable=AsyncMock,
               return_value=MOCK_PLAYERS):
        r = client.get("/props/search?q=LeBron")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "LeBron James"

def test_get_prop_returns_200_with_ev():
    with patch("backend.routes.props.get_game_logs", new_callable=AsyncMock,
               return_value=MOCK_LOGS * 10), \
         patch("backend.routes.props.get_player_props", new_callable=AsyncMock,
               return_value=MOCK_PROP):
        r = client.get("/props/1/points?window=10")
    assert r.status_code == 200
    data = r.json()
    assert "line" in data
    assert "ev" in data
    assert "your_prob" in data

def test_get_prop_returns_404_when_no_odds():
    with patch("backend.routes.props.get_game_logs", new_callable=AsyncMock,
               return_value=MOCK_LOGS * 10), \
         patch("backend.routes.props.get_player_props", new_callable=AsyncMock,
               return_value=None):
        r = client.get("/props/1/points?window=10")
    assert r.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_props_route.py -v
```

Expected: `ImportError` — `backend.main` doesn't exist yet.

- [ ] **Step 3: Create backend/main.py (minimal, enough to support tests)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EdgeIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routes import props, ev, chat, bets  # noqa: E402
app.include_router(props.router)
app.include_router(ev.router)
app.include_router(chat.router)
app.include_router(bets.router)
```

- [ ] **Step 4: Create backend/routes/props.py**

```python
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
    logs, prop = await _fetch_logs_and_prop(player_id, stat_category, window, player_name)
    if prop is None:
        raise HTTPException(status_code=404, detail="No odds found for this prop")

    values = [g["value"] for g in logs]
    your_prob = calc_probability(values, prop["line"], stat_category)
    ev_data = calc_ev(your_prob, prop["over_odds"])
    historical = await get_historical_lines(player_name, stat_category)

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
    import asyncio
    return await asyncio.gather(
        get_game_logs(player_id, stat_category, window),
        get_player_props(player_name, stat_category),
    )
```

- [ ] **Step 5: Create stub files for other routes (so main.py imports succeed)**

```python
# backend/routes/ev.py
from fastapi import APIRouter
router = APIRouter(prefix="/ev", tags=["ev"])

# backend/routes/chat.py
from fastapi import APIRouter
router = APIRouter(prefix="/chat", tags=["chat"])

# backend/routes/bets.py
from fastapi import APIRouter
router = APIRouter(prefix="/bets", tags=["bets"])
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_props_route.py -v
```

Expected: 3 PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/routes/ tests/test_props_route.py
git commit -m "feat: props route — player search and prop lookup with EV pre-computed"
```

---

### Task 7: Frontend Shell + API Client

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/pages/Analyze.jsx` (stub)
- Create: `frontend/src/pages/Tracker.jsx` (stub)

- [ ] **Step 1: Create frontend/src/api/client.js**

```js
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL })

export const searchPlayers = (q) =>
  api.get('/props/search', { params: { q } }).then((r) => r.data)

export const getProp = (playerId, statCategory, { window = 10, playerName }) =>
  api
    .get(`/props/${playerId}/${statCategory}`, {
      params: { window, player_name: playerName },
    })
    .then((r) => r.data)

export const logBet = (bet) => api.post('/bets', bet).then((r) => r.data)

export const getBets = () => api.get('/bets').then((r) => r.data)

export const updateBet = (id, data) =>
  api.patch(`/bets/${id}`, data).then((r) => r.data)

export const streamChat = (payload, onChunk, onDone) => {
  const url = `${BASE_URL}/chat`
  const ctrl = new AbortController()
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: ctrl.signal,
  }).then(async (res) => {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone(); break }
      const text = decoder.decode(value)
      text.split('\n').forEach((line) => {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6)
          if (chunk !== '[DONE]') onChunk(chunk)
        }
      })
    }
  })
  return () => ctrl.abort()
}
```

- [ ] **Step 2: Create frontend/src/App.jsx**

```jsx
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Analyze from './pages/Analyze'
import Tracker from './pages/Tracker'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 px-6 py-3 flex gap-6 text-sm">
          <span className="font-bold text-green-400 mr-4">EdgeIQ</span>
          <NavLink to="/" className={({ isActive }) =>
            isActive ? 'text-green-400' : 'text-gray-400 hover:text-gray-200'}>
            Analyze
          </NavLink>
          <NavLink to="/tracker" className={({ isActive }) =>
            isActive ? 'text-green-400' : 'text-gray-400 hover:text-gray-200'}>
            Tracker
          </NavLink>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<Analyze />} />
            <Route path="/tracker" element={<Tracker />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
```

- [ ] **Step 3: Create stub pages**

```jsx
// frontend/src/pages/Analyze.jsx
export default function Analyze() {
  return <div className="text-gray-400">Analyze — coming soon</div>
}

// frontend/src/pages/Tracker.jsx
export default function Tracker() {
  return <div className="text-gray-400">Tracker — coming soon</div>
}
```

- [ ] **Step 4: Verify the frontend compiles and routes work**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 — nav with "Analyze" and "Tracker" links renders. Both pages show placeholder text.

- [ ] **Step 5: Create vite.config.js with proxy for local dev**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/props': 'http://localhost:8000',
      '/ev': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/bets': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: React shell — routing, nav, API client with all endpoints"
```

---

## Phase 2 — Core Analytics

### Task 8: EV Route

**Files:**
- Modify: `backend/routes/ev.py`
- Create: `tests/test_ev_route.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ev_route.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ev_endpoint_returns_all_fields():
    payload = {
        "game_log_values": [25, 28, 22, 30, 24, 26, 20, 29, 25, 27],
        "line": 22.5,
        "odds": -110,
        "stat_category": "points",
    }
    r = client.post("/ev", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "your_prob" in data
    assert "implied_prob" in data
    assert "ev" in data
    assert "edge_pct" in data
    assert "kelly_fraction" in data
    assert "distribution" in data

def test_ev_endpoint_positive_odds():
    payload = {
        "game_log_values": [10] * 10,
        "line": 8.5,
        "odds": 120,
        "stat_category": "points",
    }
    r = client.post("/ev", json=payload)
    assert r.status_code == 200
    assert r.json()["ev"] > 0

def test_ev_endpoint_validates_empty_log():
    payload = {
        "game_log_values": [],
        "line": 22.5,
        "odds": -110,
        "stat_category": "points",
    }
    r = client.post("/ev", json=payload)
    assert r.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ev_route.py -v
```

Expected: All 3 FAIL (404 or validation error — route is a stub)

- [ ] **Step 3: Replace backend/routes/ev.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ev_route.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/routes/ev.py tests/test_ev_route.py
git commit -m "feat: /ev route — distribution fitting and EV/Kelly calculation endpoint"
```

---

### Task 9: DistChart Component

**Files:**
- Modify: `frontend/src/components/DistChart.jsx`

- [ ] **Step 1: Create frontend/src/components/DistChart.jsx**

```jsx
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell
} from 'recharts'

const WINDOWS = [5, 10, 20, 0]
const WINDOW_LABELS = { 5: 'L5', 10: 'L10', 20: 'L20', 0: 'Season' }

export default function DistChart({ gameLogs = [], line, statCategory, window, onWindowChange }) {
  if (!gameLogs.length) return null

  // Build histogram buckets
  const values = gameLogs.map((g) => g.value)
  const min = Math.floor(Math.min(...values))
  const max = Math.ceil(Math.max(...values))
  const buckets = {}
  for (let i = min; i <= max; i++) buckets[i] = 0
  values.forEach((v) => {
    const bucket = Math.floor(v)
    if (buckets[bucket] !== undefined) buckets[bucket]++
  })

  const data = Object.entries(buckets).map(([val, count]) => ({
    val: Number(val),
    count,
  }))

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-300">
          Distribution — {statCategory}
        </h3>
        <div className="flex gap-1">
          {WINDOWS.map((w) => (
            <button
              key={w}
              onClick={() => onWindowChange(w)}
              className={`px-2 py-1 rounded text-xs font-mono ${
                window === w
                  ? 'bg-green-400 text-gray-900'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {WINDOW_LABELS[w]}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="val" tick={{ fontSize: 11, fill: '#6b7280' }} />
          <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6 }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <ReferenceLine x={Math.floor(line)} stroke="#f59e0b" strokeDasharray="4 2"
            label={{ value: `${line}`, fill: '#f59e0b', fontSize: 11 }} />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.val}
                fill={entry.val > line ? '#4ade80' : '#374151'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-500 mt-2">
        Green bars = would clear the line · Dashed line = prop threshold ({line})
      </p>
    </div>
  )
}
```

- [ ] **Step 2: Verify component renders in Storybook or by importing in Analyze.jsx temporarily**

Add to `Analyze.jsx`:
```jsx
import DistChart from '../components/DistChart'
// inside return:
<DistChart
  gameLogs={[{value:25},{value:28},{value:22},{value:30}]}
  line={24.5}
  statCategory="points"
  window={10}
  onWindowChange={console.log}
/>
```

Run `npm run dev` and confirm chart renders without console errors.

- [ ] **Step 3: Remove the test import from Analyze.jsx**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DistChart.jsx
git commit -m "feat: DistChart — histogram with prop threshold line and window toggle"
```

---

### Task 10: EVCard Component

**Files:**
- Create: `frontend/src/components/EVCard.jsx`

- [ ] **Step 1: Create frontend/src/components/EVCard.jsx**

```jsx
export default function EVCard({ propData, onLogBet }) {
  if (!propData) return null

  const { your_prob, implied_prob, ev, edge_pct, kelly_fraction,
          line, over_odds, stat_category, low_confidence, sample_size } = propData

  const isPositive = ev > 0
  const formatOdds = (o) => o > 0 ? `+${o}` : `${o}`
  const formatPct = (p) => `${(p * 100).toFixed(1)}%`

  return (
    <div className={`bg-gray-900 rounded-xl p-4 border ${
      isPositive ? 'border-green-500/40' : 'border-red-500/30'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">
          Over {line} {stat_category} · {formatOdds(over_odds)}
        </h3>
        <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${
          isPositive
            ? 'bg-green-500/20 text-green-400'
            : 'bg-red-500/20 text-red-400'
        }`}>
          {isPositive ? '+' : ''}{(ev * 100).toFixed(1)}% EV
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <Stat label="Your Prob" value={formatPct(your_prob)} accent={isPositive} />
        <Stat label="Implied Prob" value={formatPct(implied_prob)} />
        <Stat label="Edge" value={`${edge_pct > 0 ? '+' : ''}${edge_pct.toFixed(1)}%`} accent={edge_pct > 0} />
        <Stat label="Kelly" value={`${(kelly_fraction * 100).toFixed(1)}%`} />
      </div>

      {low_confidence && (
        <p className="text-xs text-amber-400 mb-3 flex items-center gap-1">
          ⚠ Small sample (N={sample_size}) — model confidence low
        </p>
      )}

      <button
        onClick={() => onLogBet(propData)}
        className="w-full py-2 rounded-lg bg-gray-800 text-gray-300 text-sm
                   hover:bg-gray-700 transition-colors border border-gray-700"
      >
        Log Bet
      </button>
    </div>
  )
}

function Stat({ label, value, accent = false }) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-2">
      <div className="text-xs text-gray-500 mb-0.5">{label}</div>
      <div className={`text-sm font-mono font-medium ${
        accent ? 'text-green-400' : 'text-gray-200'
      }`}>{value}</div>
    </div>
  )
}
```

- [ ] **Step 2: Visual check — add to Analyze.jsx temporarily**

```jsx
import EVCard from '../components/EVCard'
// test data:
const mockProp = {
  your_prob: 0.62, implied_prob: 0.524, ev: 0.08, edge_pct: 9.6,
  kelly_fraction: 0.18, line: 24.5, over_odds: -110,
  stat_category: "points", low_confidence: false, sample_size: 10
}
<EVCard propData={mockProp} onLogBet={console.log} />
```

Confirm card renders with correct colors and formatting.

- [ ] **Step 3: Remove test import**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/EVCard.jsx
git commit -m "feat: EVCard — EV verdict with color coding and Log Bet button"
```

---

### Task 11: LineMove Component

**Files:**
- Create: `frontend/src/components/LineMove.jsx`

- [ ] **Step 1: Create frontend/src/components/LineMove.jsx**

```jsx
import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts'

export default function LineMove({ historicalLines = [], currentLine, openLine }) {
  if (!historicalLines.length) return null

  const data = historicalLines.map((snap, i) => ({
    i,
    line: snap.line,
    time: snap.snapshot_time
      ? new Date(snap.snapshot_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : `T${i}`,
    sharp: Math.abs(snap.line - (historicalLines[i - 1]?.line ?? snap.line)) > 0.5,
  }))

  const delta = currentLine - openLine
  const sharpPoints = data.filter((d) => d.sharp)

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <h3 className="text-sm font-medium text-gray-300 mb-3">Line Movement</h3>

      <div className="flex gap-4 mb-3 text-xs font-mono">
        <div>
          <span className="text-gray-500">Open </span>
          <span className="text-gray-200">{openLine}</span>
        </div>
        <div>
          <span className="text-gray-500">Current </span>
          <span className="text-gray-200">{currentLine}</span>
        </div>
        <div>
          <span className="text-gray-500">Move </span>
          <span className={Math.abs(delta) > 0.5 ? 'text-amber-400' : 'text-gray-400'}>
            {delta > 0 ? '+' : ''}{delta.toFixed(1)}
            {Math.abs(delta) > 0.5 && ' ⚡'}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={data}>
          <XAxis dataKey="time" hide />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6, fontSize: 11 }}
            formatter={(v) => [v, 'line']}
          />
          <Line type="monotone" dataKey="line" stroke="#4ade80"
            strokeWidth={2} dot={false} />
          {sharpPoints.map((p) => (
            <ReferenceDot key={p.i} x={p.time} y={p.line} r={4} fill="#f59e0b" stroke="none" />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {sharpPoints.length > 0 && (
        <p className="text-xs text-amber-400 mt-1">⚡ Sharp move detected (line shifted &gt;0.5)</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Visual check in Analyze.jsx**

```jsx
import LineMove from '../components/LineMove'
const mockLines = [
  { line: 24.5, snapshot_time: new Date().toISOString() },
  { line: 24.5, snapshot_time: new Date().toISOString() },
  { line: 25.0, snapshot_time: new Date().toISOString() },
  { line: 25.0, snapshot_time: new Date().toISOString() },
]
<LineMove historicalLines={mockLines} currentLine={25.0} openLine={24.5} />
```

Confirm sparkline renders with amber ⚡ indicator for the 0.5 move.

- [ ] **Step 3: Remove test import**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/LineMove.jsx
git commit -m "feat: LineMove — odds sparkline with sharp action detection"
```

---

### Task 12: Analyze Page (wiring everything together)

**Files:**
- Modify: `frontend/src/pages/Analyze.jsx`

- [ ] **Step 1: Replace Analyze.jsx with the full layout**

```jsx
import { useState, useCallback } from 'react'
import { searchPlayers, getProp } from '../api/client'
import DistChart from '../components/DistChart'
import EVCard from '../components/EVCard'
import LineMove from '../components/LineMove'
import ChatSidebar from '../components/ChatSidebar'
import BetForm from '../components/BetForm'

const STAT_OPTIONS = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'minutes']

export default function Analyze() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [statCategory, setStatCategory] = useState('points')
  const [window, setWindow] = useState(10)
  const [propData, setPropData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [betFormOpen, setBetFormOpen] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (query.length < 2) return
    const r = await searchPlayers(query)
    setResults(r)
  }

  const handleSelectPlayer = (player) => {
    setSelectedPlayer(player)
    setResults([])
    setQuery(player.name)
  }

  const loadProp = useCallback(async (win = window) => {
    if (!selectedPlayer) return
    setLoading(true)
    setError(null)
    try {
      const data = await getProp(selectedPlayer.id, statCategory, {
        window: win,
        playerName: selectedPlayer.name,
      })
      setPropData(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load prop data')
    } finally {
      setLoading(false)
    }
  }, [selectedPlayer, statCategory, window])

  const handleWindowChange = (w) => {
    setWindow(w)
    loadProp(w)
  }

  return (
    <div className="flex gap-6">
      <div className="flex-1 min-w-0">
        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2 mb-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search player..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2
                       text-sm text-gray-100 placeholder-gray-500 focus:outline-none
                       focus:border-green-500"
          />
          <select
            value={statCategory}
            onChange={(e) => setStatCategory(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                       text-sm text-gray-200 focus:outline-none"
          >
            {STAT_OPTIONS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button type="submit"
            className="px-4 py-2 bg-green-500 text-gray-900 rounded-lg text-sm font-medium
                       hover:bg-green-400 transition-colors">
            Search
          </button>
        </form>

        {/* Player results dropdown */}
        {results.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg mb-4 overflow-hidden">
            {results.map((p) => (
              <button key={p.id} onClick={() => handleSelectPlayer(p)}
                className="w-full text-left px-4 py-2 hover:bg-gray-700 text-sm text-gray-200">
                <span className="font-medium">{p.name}</span>
                <span className="text-gray-500 ml-2">{p.team}</span>
              </button>
            ))}
          </div>
        )}

        {/* Analyze button */}
        {selectedPlayer && (
          <button onClick={() => loadProp(window)}
            className="mb-6 px-4 py-2 bg-gray-700 text-gray-200 rounded-lg text-sm
                       hover:bg-gray-600 transition-colors">
            {loading ? 'Loading...' : `Analyze ${selectedPlayer.name} — ${statCategory}`}
          </button>
        )}

        {error && (
          <p className="text-red-400 text-sm mb-4">{error}</p>
        )}

        {/* Analytics grid */}
        {propData && (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <DistChart
                gameLogs={propData.game_log}
                line={propData.line}
                statCategory={propData.stat_category}
                window={window}
                onWindowChange={handleWindowChange}
              />
            </div>
            <EVCard
              propData={propData}
              onLogBet={() => setBetFormOpen(true)}
            />
            <div className="col-span-3">
              <LineMove
                historicalLines={propData.historical_lines}
                currentLine={propData.line}
                openLine={propData.historical_lines?.[0]?.line ?? propData.line}
              />
            </div>
          </div>
        )}
      </div>

      {/* Chat toggle */}
      <div className="relative">
        <button
          onClick={() => setChatOpen((o) => !o)}
          className="fixed right-6 bottom-6 bg-green-500 text-gray-900 rounded-full
                     w-12 h-12 text-xl shadow-lg hover:bg-green-400 transition-colors z-20">
          💬
        </button>
        {chatOpen && (
          <ChatSidebar propData={propData} onClose={() => setChatOpen(false)} />
        )}
      </div>

      {betFormOpen && (
        <BetForm
          propData={propData}
          onClose={() => setBetFormOpen(false)}
          onSaved={() => setBetFormOpen(false)}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create stub ChatSidebar and BetForm so app compiles**

```jsx
// frontend/src/components/ChatSidebar.jsx (stub)
export default function ChatSidebar({ propData, onClose }) {
  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-gray-900 border-l
                    border-gray-800 p-4 z-10">
      <button onClick={onClose} className="text-gray-500 hover:text-gray-300 mb-4">✕</button>
      <p className="text-gray-400 text-sm">Chat — coming in Phase 3</p>
    </div>
  )
}

// frontend/src/components/BetForm.jsx (stub)
export default function BetForm({ propData, onClose, onSaved }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-30">
      <div className="bg-gray-900 rounded-xl p-6 w-96 border border-gray-700">
        <p className="text-gray-400 text-sm">Bet form — coming in Phase 4</p>
        <button onClick={onClose} className="mt-4 text-gray-500">Close</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Start both backend and frontend, test the full flow**

```bash
# Terminal 1
source .venv/bin/activate && uvicorn backend.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Search a player (e.g. "LeBron"), select them, choose a stat, click Analyze. Confirm chart + EV card + line movement render with real data.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Analyze.jsx frontend/src/components/ChatSidebar.jsx frontend/src/components/BetForm.jsx
git commit -m "feat: Analyze page — full prop analysis layout wired to live API"
```

---

## Phase 3 — AI Integration

### Task 13: Prompt Builder + Chat Route

**Files:**
- Create: `backend/ai/prompt.py`
- Modify: `backend/routes/chat.py`

- [ ] **Step 1: Create backend/ai/prompt.py**

```python
def build_system_prompt(ctx: dict) -> str:
    game_log = ", ".join(str(v) for v in ctx.get("game_log_values", []))
    open_line = ctx.get("open_line", ctx.get("line", "?"))
    current_line = ctx.get("line", "?")
    delta = round(float(current_line) - float(open_line), 1) if open_line != "?" else 0

    return f"""You are EdgeIQ's betting analyst. You have access to the following data for the current prop being analyzed:

Player: {ctx.get('player_name', '?')} | Opponent: {ctx.get('opponent', '?')} | {ctx.get('home_away', '?')}
Stat: {ctx.get('stat_category', '?')} | Line: {ctx.get('line', '?')} | Odds: {ctx.get('over_odds', '?')}
Window: last {ctx.get('window', '?')} games | Distribution: {ctx.get('distribution', '?')}

Your model:  prob={round(ctx.get('your_prob', 0) * 100, 1)}% | EV={ctx.get('ev', '?')} | edge={ctx.get('edge_pct', '?')}%
Book implied: {round(ctx.get('implied_prob', 0) * 100, 1)}%
Line movement: opened {open_line} → now {current_line} ({delta:+.1f})
Last {ctx.get('sample_size', '?')} values: {game_log}

Answer questions concisely and factually using the data above.
Do not recommend bets — explain what the data shows and let the user decide.
{"⚠ Note: small sample size (N=" + str(ctx.get('sample_size', '?')) + ") — flag uncertainty in your answers." if ctx.get('low_confidence') else ""}"""


def build_suggested_chips(ctx: dict) -> list[str]:
    chips = [f"How has {ctx.get('player_name', 'he')} performed vs {ctx.get('opponent', 'this opponent')} historically?"]
    if abs(float(ctx.get("line", 0)) - float(ctx.get("open_line", ctx.get("line", 0)))) > 0.5:
        chips.append("Why might this line have moved?")
    if ctx.get("ev", 0) > 0:
        chips.append("What could invalidate this edge?")
    else:
        chips.append("Is there a case for taking this despite negative EV?")
    return chips[:3]
```

- [ ] **Step 2: Write failing test for prompt builder**

```python
# tests/test_prompt.py
from backend.ai.prompt import build_system_prompt, build_suggested_chips

CTX = {
    "player_name": "LeBron James", "opponent": "BOS", "home_away": "away",
    "stat_category": "points", "line": 25.0, "over_odds": -110,
    "window": 10, "distribution": "poisson",
    "your_prob": 0.62, "implied_prob": 0.524, "ev": 0.08, "edge_pct": 9.6,
    "game_log_values": [25, 28, 22, 30, 24, 26, 20, 29, 25, 27],
    "open_line": 24.5, "sample_size": 10, "low_confidence": False,
}

def test_system_prompt_contains_player_name():
    prompt = build_system_prompt(CTX)
    assert "LeBron James" in prompt

def test_system_prompt_contains_ev():
    prompt = build_system_prompt(CTX)
    assert "0.08" in prompt

def test_suggested_chips_returns_3():
    chips = build_suggested_chips(CTX)
    assert len(chips) == 3

def test_suggested_chips_line_move_when_large_delta():
    ctx = {**CTX, "line": 25.0, "open_line": 24.0}
    chips = build_suggested_chips(ctx)
    assert any("moved" in c for c in chips)

def test_low_confidence_flag_in_prompt():
    ctx = {**CTX, "low_confidence": True, "sample_size": 5}
    prompt = build_system_prompt(ctx)
    assert "small sample" in prompt.lower()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_prompt.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Run tests after creating prompt.py to verify they pass**

```bash
pytest tests/test_prompt.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Replace backend/routes/chat.py**

```python
import json
import anthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.config import ANTHROPIC_API_KEY
from backend.ai.prompt import build_system_prompt, build_suggested_chips

router = APIRouter(prefix="/chat", tags=["chat"])
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ChatRequest(BaseModel):
    message: str
    prop_context: dict
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


class ChipsRequest(BaseModel):
    prop_context: dict


@router.post("/chips")
def get_chips(payload: ChipsRequest):
    return {"chips": build_suggested_chips(payload.prop_context)}


@router.post("")
def stream_chat(payload: ChatRequest):
    system = build_system_prompt(payload.prop_context)
    messages = [*payload.history, {"role": "user", "content": payload.message}]

    def generate():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

- [ ] **Step 6: Commit**

```bash
git add backend/ai/prompt.py backend/routes/chat.py tests/test_prompt.py
git commit -m "feat: chat route — SSE streaming with dynamic prop context injection"
```

---

### Task 14: ChatSidebar Component (full)

**Files:**
- Modify: `frontend/src/components/ChatSidebar.jsx`

- [ ] **Step 1: Replace ChatSidebar stub with full implementation**

```jsx
import { useState, useEffect, useRef } from 'react'
import { streamChat } from '../api/client'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ChatSidebar({ propData, onClose }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [chips, setChips] = useState([])
  const bottomRef = useRef(null)
  const cancelRef = useRef(null)

  useEffect(() => {
    if (!propData) return
    axios.post(`${BASE_URL}/chat/chips`, { prop_context: buildContext(propData) })
      .then((r) => setChips(r.data.chips))
  }, [propData])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = (text) => {
    if (!text.trim() || streaming) return
    const userMsg = { role: 'user', content: text }
    setMessages((m) => [...m, userMsg, { role: 'assistant', content: '' }])
    setInput('')
    setStreaming(true)
    setChips([])

    cancelRef.current = streamChat(
      { message: text, prop_context: buildContext(propData), history: messages },
      (chunk) => {
        setMessages((m) => {
          const updated = [...m]
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + chunk,
          }
          return updated
        })
      },
      () => setStreaming(false),
    )
  }

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-gray-900 border-l
                    border-gray-800 flex flex-col z-10 shadow-2xl">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <span className="text-sm font-medium text-gray-200">AI Analyst</span>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-lg">✕</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm text-center mt-8">
            {propData ? 'Ask anything about this prop.' : 'Select a prop to start.'}
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
              m.role === 'user'
                ? 'bg-green-500/20 text-green-100'
                : 'bg-gray-800 text-gray-200'
            }`}>
              {m.content || (streaming && i === messages.length - 1 ? '▋' : '')}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {chips.length > 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {chips.map((c, i) => (
            <button key={i} onClick={() => sendMessage(c)}
              className="text-xs bg-gray-800 text-gray-300 border border-gray-700
                         rounded-full px-3 py-1 hover:bg-gray-700 transition-colors">
              {c}
            </button>
          ))}
        </div>
      )}

      <div className="p-4 border-t border-gray-800 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
          placeholder="Ask about this prop..."
          disabled={!propData || streaming}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                     text-sm text-gray-100 placeholder-gray-500 focus:outline-none
                     focus:border-green-500 disabled:opacity-50"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!propData || streaming || !input.trim()}
          className="px-3 py-2 bg-green-500 text-gray-900 rounded-lg text-sm font-medium
                     hover:bg-green-400 disabled:opacity-40 transition-colors"
        >
          →
        </button>
      </div>
    </div>
  )
}

function buildContext(p) {
  if (!p) return {}
  return {
    player_name: p.player_name,
    stat_category: p.stat_category,
    line: p.line,
    over_odds: p.over_odds,
    window: p.window,
    distribution: p.distribution,
    your_prob: p.your_prob,
    implied_prob: p.implied_prob,
    ev: p.ev,
    edge_pct: p.edge_pct,
    game_log_values: p.game_log?.map((g) => g.value) ?? [],
    open_line: p.historical_lines?.[0]?.line ?? p.line,
    sample_size: p.sample_size,
    low_confidence: p.low_confidence,
    opponent: p.game_log?.[0]?.opponent ?? '?',
    home_away: p.game_log?.[0]?.home_away ?? '?',
  }
}
```

- [ ] **Step 2: End-to-end test**

With backend running, open the Analyze page, load a prop, open the chat sidebar. Type a question. Confirm streaming response renders incrementally. Confirm suggested chips appear and clicking one sends the message.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatSidebar.jsx
git commit -m "feat: ChatSidebar — SSE streaming with suggested chips and message history"
```

---

## Phase 4 — Bet Tracker + Deploy

### Task 15: Bets Route

**Files:**
- Modify: `backend/routes/bets.py`
- Create: `tests/test_bets_route.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_bets_route.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import init_db

client = TestClient(app)

BET_PAYLOAD = {
    "player_name": "LeBron James",
    "stat_category": "points",
    "line": 25.5,
    "direction": "over",
    "odds": -110,
    "stake": 50.0,
    "ev_at_bet": 0.08,
}

def test_post_bet_returns_201():
    r = client.post("/bets", json=BET_PAYLOAD)
    assert r.status_code == 201
    data = r.json()
    assert data["player_name"] == "LeBron James"
    assert data["result"] == "pending"
    assert "id" in data

def test_get_bets_returns_list():
    client.post("/bets", json=BET_PAYLOAD)
    r = client.get("/bets")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1

def test_patch_bet_result():
    post_r = client.post("/bets", json=BET_PAYLOAD)
    bet_id = post_r.json()["id"]
    r = client.patch(f"/bets/{bet_id}", json={"result": "win", "profit_loss": 45.45})
    assert r.status_code == 200
    assert r.json()["result"] == "win"
    assert r.json()["profit_loss"] == 45.45

def test_patch_bet_invalid_result():
    post_r = client.post("/bets", json=BET_PAYLOAD)
    bet_id = post_r.json()["id"]
    r = client.patch(f"/bets/{bet_id}", json={"result": "maybe"})
    assert r.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_bets_route.py -v
```

Expected: All FAIL (stub route returns 404)

- [ ] **Step 3: Replace backend/routes/bets.py**

```python
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
```

- [ ] **Step 4: Initialize the DB on app startup — add to backend/main.py**

```python
# Add after imports, before route includes:
from backend.db import init_db
init_db()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_bets_route.py -v
```

Expected: 4 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/routes/bets.py backend/main.py tests/test_bets_route.py
git commit -m "feat: bets route — create, list, and update bets with result tracking"
```

---

### Task 16: BetForm Component

**Files:**
- Modify: `frontend/src/components/BetForm.jsx`

- [ ] **Step 1: Replace BetForm stub with full implementation**

```jsx
import { useState } from 'react'
import { logBet } from '../api/client'

export default function BetForm({ propData, onClose, onSaved }) {
  const [stake, setStake] = useState('')
  const [direction, setDirection] = useState('over')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  if (!propData) return null

  const { player_name, stat_category, line, over_odds, under_odds, ev } = propData
  const odds = direction === 'over' ? over_odds : under_odds
  const formatOdds = (o) => o > 0 ? `+${o}` : `${o}`

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!stake || parseFloat(stake) <= 0) {
      setError('Enter a valid stake amount')
      return
    }
    setSaving(true)
    try {
      await logBet({
        player_name,
        stat_category,
        line,
        direction,
        odds,
        stake: parseFloat(stake),
        ev_at_bet: ev,
      })
      onSaved()
    } catch {
      setError('Failed to save bet')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-30"
         onClick={onClose}>
      <div className="bg-gray-900 rounded-xl p-6 w-96 border border-gray-700 shadow-2xl"
           onClick={(e) => e.stopPropagation()}>
        <h2 className="text-base font-medium text-gray-100 mb-4">Log Bet</h2>

        <div className="bg-gray-800 rounded-lg p-3 mb-4 text-sm">
          <div className="text-gray-400">{player_name}</div>
          <div className="text-gray-200 font-medium">{direction} {line} {stat_category}</div>
          <div className="text-gray-400 font-mono">{formatOdds(odds)}</div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-2">
            {['over', 'under'].map((d) => (
              <button key={d} type="button"
                onClick={() => setDirection(d)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  direction === d
                    ? 'bg-green-500 text-gray-900'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}>
                {d.charAt(0).toUpperCase() + d.slice(1)} {formatOdds(d === 'over' ? over_odds : under_odds)}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Stake ($)</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="50.00"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                         text-sm text-gray-100 focus:outline-none focus:border-green-500"
            />
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 bg-gray-800 text-gray-400 rounded-lg text-sm hover:bg-gray-700">
              Cancel
            </button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2 bg-green-500 text-gray-900 rounded-lg text-sm
                         font-medium hover:bg-green-400 disabled:opacity-50">
              {saving ? 'Saving...' : 'Log Bet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: End-to-end test**

Load a prop, click "Log Bet" on the EVCard. Confirm the modal pre-fills player/stat/line/odds. Set a stake, click "Log Bet". Confirm the modal closes without error. Check the `/bets` API endpoint returns the saved bet.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BetForm.jsx
git commit -m "feat: BetForm — bet logging modal with over/under toggle and stake input"
```

---

### Task 17: Tracker Page

**Files:**
- Modify: `frontend/src/pages/Tracker.jsx`

- [ ] **Step 1: Replace Tracker stub with full implementation**

```jsx
import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid
} from 'recharts'
import { getBets, updateBet, streamChat } from '../api/client'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Tracker() {
  const [bets, setBets] = useState([])
  const [analysisText, setAnalysisText] = useState('')
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => { getBets().then(setBets) }, [])

  const totalPL = bets.reduce((sum, b) => sum + (b.profit_loss || 0), 0)
  const settled = bets.filter((b) => b.result !== 'pending')
  const wins = settled.filter((b) => b.result === 'win').length
  const hitRate = settled.length ? ((wins / settled.length) * 100).toFixed(1) : '--'

  // Running P&L for chart
  let running = 0
  const chartData = settled.map((b) => {
    running += b.profit_loss || 0
    return { label: b.player_name.split(' ')[1], pl: parseFloat(running.toFixed(2)) }
  })

  const handleSetResult = async (bet, result) => {
    const stake = bet.stake
    const profitLoss = result === 'win'
      ? bet.odds > 0 ? (bet.odds / 100) * stake : (100 / Math.abs(bet.odds)) * stake
      : result === 'push' ? 0 : -stake
    const updated = await updateBet(bet.id, { result, profit_loss: profitLoss })
    setBets((prev) => prev.map((b) => b.id === updated.id ? updated : b))
  }

  const handleAnalyze = () => {
    setAnalyzing(true)
    setAnalysisText('')
    const last30 = JSON.stringify(settled.slice(-30))
    const cancelFn = streamChat(
      {
        message: `Analyze my last ${Math.min(30, settled.length)} bets for patterns, win rate, and leaks. Here is my bet history: ${last30}`,
        prop_context: {},
        history: [],
      },
      (chunk) => setAnalysisText((t) => t + chunk),
      () => setAnalyzing(false),
    )
  }

  const formatOdds = (o) => o > 0 ? `+${o}` : `${o}`

  return (
    <div className="max-w-4xl">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatBox label="Total P&L" value={`$${totalPL.toFixed(2)}`} accent={totalPL >= 0} />
        <StatBox label="Hit Rate" value={`${hitRate}%`} />
        <StatBox label="Bets" value={`${settled.length} / ${bets.length}`} />
      </div>

      {/* P&L chart */}
      {chartData.length > 1 && (
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-8">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Running P&L</h3>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6 }}
                formatter={(v) => [`$${v}`, 'P&L']}
              />
              <Line type="monotone" dataKey="pl" stroke="#4ade80" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* AI Analysis */}
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-300">Bet Analysis</h3>
          <button onClick={handleAnalyze} disabled={analyzing || settled.length === 0}
            className="text-xs px-3 py-1.5 bg-green-500/20 text-green-400 border
                       border-green-500/30 rounded-lg hover:bg-green-500/30 disabled:opacity-40">
            {analyzing ? 'Analyzing...' : 'Analyze my bets'}
          </button>
        </div>
        {analysisText ? (
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{analysisText}</p>
        ) : (
          <p className="text-sm text-gray-500">
            {settled.length === 0
              ? 'No settled bets to analyze yet.'
              : 'Click "Analyze my bets" to get an AI breakdown of your patterns and leaks.'}
          </p>
        )}
      </div>

      {/* Bet history */}
      <div className="space-y-2">
        {bets.map((bet) => (
          <div key={bet.id}
            className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center gap-4">
            <div className="flex-1 min-w-0">
              <div className="text-sm text-gray-200 font-medium">
                {bet.player_name} · {bet.direction} {bet.line} {bet.stat_category}
              </div>
              <div className="text-xs text-gray-500 font-mono">
                {formatOdds(bet.odds)} · ${bet.stake} stake
                {bet.ev_at_bet != null && ` · EV was ${(bet.ev_at_bet * 100).toFixed(1)}%`}
              </div>
            </div>
            {bet.result === 'pending' ? (
              <div className="flex gap-1">
                {['win', 'loss', 'push'].map((r) => (
                  <button key={r} onClick={() => handleSetResult(bet, r)}
                    className="text-xs px-2 py-1 bg-gray-800 text-gray-400 rounded
                               hover:bg-gray-700 capitalize">
                    {r}
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-right">
                <span className={`text-xs font-medium capitalize ${
                  bet.result === 'win' ? 'text-green-400'
                  : bet.result === 'loss' ? 'text-red-400'
                  : 'text-gray-400'
                }`}>{bet.result}</span>
                {bet.profit_loss != null && (
                  <div className={`text-xs font-mono ${
                    bet.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {bet.profit_loss >= 0 ? '+' : ''}${bet.profit_loss.toFixed(2)}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {bets.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-8">
            No bets logged yet. Analyze a prop and click "Log Bet".
          </p>
        )}
      </div>
    </div>
  )
}

function StatBox({ label, value, accent = false }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-mono font-medium ${
        accent ? 'text-green-400' : 'text-gray-200'
      }`}>{value}</div>
    </div>
  )
}
```

- [ ] **Step 2: End-to-end test**

Navigate to /tracker. If you have logged bets, confirm they appear with Win/Loss/Push buttons. Click a result — confirm P&L updates and chart renders. Click "Analyze my bets" — confirm streaming analysis appears.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Tracker.jsx
git commit -m "feat: Tracker page — P&L chart, bet history, and AI bet analysis"
```

---

### Task 18: Deploy

**Files:**
- Create: `render.yaml`
- Create: `frontend/.env.production`

- [ ] **Step 1: Run full test suite — all tests must pass before deploying**

```bash
pytest tests/ -v
```

Expected: All tests PASS. Fix any failures before proceeding.

- [ ] **Step 2: Create render.yaml**

```yaml
services:
  - type: web
    name: edgeiq-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: BDL_API_KEY
        sync: false
      - key: PROPODDS_API_KEY
        sync: false
      - key: ODDS_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: DATABASE_URL
        value: /var/data/edgeiq.db
    disk:
      name: edgeiq-data
      mountPath: /var/data
      sizeGB: 1
```

- [ ] **Step 3: Push backend to Render**

1. Push repo to GitHub
2. Go to render.com → New Web Service → connect repo
3. Add all four env vars in the Render dashboard (from your `.env` file)
4. Deploy — confirm health check at `https://your-app.onrender.com/docs`

- [ ] **Step 4: Set frontend production env**

```bash
# frontend/.env.production
VITE_API_URL=https://your-edgeiq-api.onrender.com
```

Replace `your-edgeiq-api.onrender.com` with your actual Render URL.

- [ ] **Step 5: Deploy frontend to Vercel**

```bash
cd frontend
npx vercel --prod
```

Follow prompts. Set `VITE_API_URL` in Vercel dashboard under Project → Settings → Environment Variables.

- [ ] **Step 6: Smoke test production**

- Search a player → results appear
- Load a prop → chart + EV card + line movement render
- Open chat → send a message → response streams
- Log a bet → appears in Tracker
- Set result → P&L updates

- [ ] **Step 7: Final commit**

```bash
git add render.yaml frontend/.env.production
git commit -m "chore: add Render and Vercel deployment config"
```

---

## Self-Review

**Spec coverage:**
- ✅ F-01 Player Prop Lookup — Task 4, 6
- ✅ F-02 Distribution Visualizer — Task 3, 9
- ✅ F-03 EV Calculator — Task 3, 8
- ✅ F-04 Line Movement Panel — Task 5, 11
- ✅ F-05 AI Chat Sidebar — Task 13, 14
- ✅ F-06 Bet Tracker — Task 15, 16, 17
- ✅ PropOdds primary / Odds API fallback — Task 5
- ✅ Window toggle (5/10/20/Season) — Task 9 (onWindowChange)
- ✅ user_id nullable on all tables — Task 2
- ✅ Sample size warning — Task 3 (low_confidence flag), Task 10 (EVCard)
- ✅ Deploy — Task 18
