# EdgeIQ — Design Spec
**Date:** 2026-04-12
**Status:** Approved

---

## Overview

EdgeIQ is a data-driven NBA player prop analysis tool. The core loop: search a player, pull their last N game logs, fit a probability distribution to the stat line in question, calculate expected value against the available odds, track line movement, and interrogate the bet via an AI assistant with full context on the data in view.

It is not a picks service. It is an edge-finding tool for bettors who want to understand whether a bet has value before placing it.

**Scope for v1:** NBA only. Single user (personal tool). Multi-user support is a future phase — the schema is designed to accommodate it without a destructive migration.

---

## Architecture

Two deployments, one monorepo:

```
Browser (React/Vite → Vercel)
    │
    ├── REST calls ──────────→ FastAPI (Render)
    │                              │
    └── SSE stream ──────────→     ├── PropOdds API  (primary odds + historical)
                                   ├── The Odds API  (manual refresh fallback)
                                   ├── BallDontLie   (NBA game logs)
                                   ├── SQLite        (cache + snapshots + bets)
                                   └── Claude API    (streaming chat)
```

**Key flows:**
- User searches a player → backend fetches game logs from BallDontLie, caches in SQLite (24hr TTL), returns stats
- User opens a prop → backend fetches current line from PropOdds (30min TTL), stores timestamped snapshot, runs EV calculation
- User hits "Refresh odds" → on-demand Odds API call, stores new snapshot, line movement updates
- User sends chat message → FastAPI streams Claude response via SSE with prop context injected into system prompt
- User logs a bet → written to `bets` table with EV at time of bet captured

---

## Data Sources

| Source | Purpose | Trigger | Cache TTL |
|---|---|---|---|
| PropOdds API | Live props + historical odds snapshots | On prop open | 30 min |
| The Odds API | Manual refresh cross-check | User hits "Refresh" | No cache |
| BallDontLie | NBA player game logs | On player search | 24 hours |

**Odds strategy rationale:** The Odds API free tier is 500 requests/month — insufficient for background polling. PropOdds is purpose-built for player props with a more generous free tier and includes historical odds snapshots, giving populated line movement charts from the first open. The Odds API is kept as a fallback for manual cross-checks only.

---

## Data Layer

### Caching
- BallDontLie game logs cached per `(player_id, window)` — switching the window toggle does not re-fetch from the API
- PropOdds snapshots stored with `snapshot_time` timestamp — line movement is built from these
- PropOdds historical odds pre-populate the sparkline on first open (no cold-start problem)

### Database Schema (SQLite)

All tables include a nullable `user_id TEXT` column for future multi-user support. When migrating to Postgres for multi-user, this column becomes non-nullable with a foreign key — additive, not destructive.

**`player_stats`**
```
id             INTEGER PK
player_id      TEXT
player_name    TEXT
sport          TEXT
game_date      DATE
stat_category  TEXT
value          REAL
opponent       TEXT
home_away      TEXT
window         INTEGER        -- 5, 10, 20, or 0 (current season, all games)
fetched_at     DATETIME
user_id        TEXT           -- nullable, future use
```

**`odds_snapshots`**
```
id             INTEGER PK
game_id        TEXT
player_name    TEXT
stat_category  TEXT
line           REAL
over_odds      INTEGER
under_odds     INTEGER
book           TEXT
source         TEXT           -- 'propodds' or 'odds_api'
snapshot_time  DATETIME
user_id        TEXT
```

**`bets`**
```
id             INTEGER PK
player_name    TEXT
stat_category  TEXT
line           REAL
direction      TEXT           -- 'over' or 'under'
odds           INTEGER
stake          REAL
ev_at_bet      REAL
result         TEXT           -- 'win', 'loss', 'push', 'pending'
profit_loss    REAL
placed_at      DATETIME
user_id        TEXT
```

**`line_movements`**
```
id                 INTEGER PK
odds_snapshot_id   INTEGER FK
open_line          REAL
current_line       REAL
delta              REAL
sharp_flag         BOOLEAN    -- true if |delta| > 0.5
recorded_at        DATETIME
user_id            TEXT
```

---

## Core Analytics

### Distribution Model

Stat category determines the distribution automatically — no user selection required:

| Stat | Distribution | Rationale |
|---|---|---|
| Points, Rebounds, Assists, Steals, Blocks | Poisson | Discrete counting stats |
| Minutes | Normal | Continuous, coach-controlled |

**Game window:** Default is last 10 games. User can toggle between 5 / 10 / 20 / Season. Changing the window re-fits the distribution and recalculates EV in real time.

**Sample size warning:** When the active window returns fewer than 10 games (early season, injury return, or window set to 5), the EV card surfaces a flag: *"Small sample (N=X) — model confidence low."*

### Probability Formulas

```python
# Poisson — counting stats (e.g. "over 24.5 points")
λ = mean(last_N_games)
P(X > line) = 1 − poisson.cdf(floor(line), λ)

# Normal — continuous stats (e.g. "over 27.5 minutes")
μ, σ = mean(last_N), std(last_N)
P(X > line) = 1 − norm.cdf(line, μ, σ)
```

### EV Calculation

```python
# Convert American odds to implied probability
implied_prob = 100 / (odds + 100)          # positive odds
implied_prob = abs(odds) / (abs(odds) + 100)  # negative odds

# EV per $1 staked
potential_win = odds / 100                 # positive odds (e.g. +110 → 1.1)
potential_win = 100 / abs(odds)            # negative odds (e.g. -120 → 0.833)
EV = (your_prob × potential_win) − ((1 − your_prob) × 1)

# Kelly Criterion (fraction of bankroll)
kelly_f = max(0, (your_prob × (potential_win + 1) − 1) / potential_win)
```

---

## Frontend Components

**`DistChart.jsx`**
Histogram of last N games with fitted Poisson/normal curve overlaid. Prop line renders as a vertical threshold. Clicking over/under zones highlights the win region. Window toggle (5/10/20/Season) sits directly above — changing it re-renders in place.

**`EVCard.jsx`**
Verdict card: modeled probability, implied probability, EV%, edge%, Kelly fraction. Color-coded green (positive EV) / red (negative EV). Sample size warning flag when N < 10. One-click "Log Bet" button pre-fills the bet form.

**`LineMove.jsx`**
Sparkline of line from PropOdds historical open to present, plus any manual refresh snapshots. Sharp action flag (delta > 0.5) renders as an amber dot on the sparkline. Open, current, and consensus line shown as labeled values below.

**`ChatSidebar.jsx`**
Sliding right-side drawer. Streams Claude responses via SSE. Suggested question chips pre-populated from prop context (see AI Integration). Message history persists for the session.

**`BetForm.jsx`**
Modal triggered from EVCard. Pre-fills player, stat, line, odds, and EV from current context. User adds stake and confirms direction (over/under). Writes to `bets` table on submit.

**Page layout:**
- `/analyze` — search bar at top, `DistChart` + `EVCard` + `LineMove` in three-column grid, `ChatSidebar` as right drawer
- `/tracker` — P&L chart over time, ROI breakdown by market, bet history list, "Analyze my bets" button

---

## AI Integration

### Streaming
FastAPI `/chat` endpoint uses SSE (`text/event-stream`). Claude streams token-by-token. React sidebar renders incrementally.

### System Prompt (dynamic per prop)
```
Player: {player_name} | Game: {opponent} | {home_away}
Stat: {stat_category} | Line: {line} | Odds: {odds}
Window: last {n} games | Distribution: {poisson|normal}

Your model:  prob={your_prob}% | EV={ev} | edge={edge_pct}%
Book implied: {implied_prob}%
Line movement: opened {open_line} → now {current_line} ({delta:+.1f})
Last {n} values: {game_log_values}

Policy: explain what the data shows, do not recommend bets.
Flag low confidence when N < 10.
```

### Suggested Question Chips
Three chips pre-generated per prop from context templates:
- If line moved > 0.5: *"Why might this line have moved?"*
- If EV is positive: *"What could invalidate this edge?"*
- Always: *"How has he performed vs {opponent} historically?"*

Chips disappear after use and do not reappear in the session.

### Bet History Analysis
On the Tracker page, "Analyze my bets" sends the last 30 bets as structured JSON. Claude returns a plain-language breakdown: win rate by market, P&L trend, identifiable patterns or leaks.

---

## Project Structure

```
edgeiq/
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── db.py                   # SQLite setup, table creation
│   ├── routes/
│   │   ├── props.py            # /props — player search, prop lookup
│   │   ├── ev.py               # /ev — distribution fit + EV calculation
│   │   ├── chat.py             # /chat — SSE streaming to Claude
│   │   └── bets.py             # /bets — CRUD for bet tracker
│   ├── services/
│   │   ├── propodds.py         # PropOdds API client
│   │   ├── odds_api.py         # The Odds API client (manual refresh)
│   │   ├── balldontlie.py      # BallDontLie game log fetcher
│   │   └── model.py            # Distribution fitting (scipy)
│   └── ai/
│       └── prompt.py           # System prompt templates
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Analyze.jsx     # Main analysis view
│   │   │   └── Tracker.jsx     # Bet history + P&L
│   │   ├── components/
│   │   │   ├── DistChart.jsx
│   │   │   ├── EVCard.jsx
│   │   │   ├── LineMove.jsx
│   │   │   ├── ChatSidebar.jsx
│   │   │   └── BetForm.jsx
│   │   └── api/
│   │       └── client.js       # Axios wrapper
│   └── package.json
├── .env                        # PROPODDS_API_KEY, ODDS_API_KEY, ANTHROPIC_API_KEY
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-12-edgeiq-design.md
```

---

## Build Phases

**Phase 1 — Foundation (~3 days)**
- Scaffold FastAPI + SQLite, create all tables with nullable `user_id`
- Integrate BallDontLie — player search, game log fetch, 24hr cache
- Integrate PropOdds — pull NBA player props, store timestamped snapshots
- React/Vite shell with routing (`/analyze`, `/tracker`)
- Player search → prop lookup UI rendering real data

**Phase 2 — Core Analytics (~3 days)**
- Poisson/normal distribution fitting via scipy
- `/ev` endpoint — probability, EV, edge%, Kelly output
- `DistChart` — histogram + fitted curve + threshold line
- Window toggle (5/10/20/Season) wired to live recalculation
- `EVCard` — verdict badge, sample size warning flag
- `LineMove` — sparkline from PropOdds historical + manual refresh snapshots
- On-demand Odds API refresh button

**Phase 3 — AI Integration (~2 days)**
- `/chat` SSE endpoint with dynamic system prompt
- `ChatSidebar` with streaming responses
- Suggested question chips from context templates
- "Analyze my bets" endpoint for Tracker page

**Phase 4 — Bet Tracker + Deploy (~2 days)**
- `BetForm` modal + `bets` table writes
- P&L chart + ROI breakdown on Tracker page
- Deploy backend to Render, frontend to Vercel
- `.env` wiring for all API keys

---

## Future Work (post-v1)

- **Multi-user:** Add auth (Clerk or Auth.js), make `user_id` non-nullable, migrate SQLite → Postgres
- **Additional sports:** MLB (Pybaseball), NFL (nfl-data-py) — data layer is sport-agnostic by design
- **SportsRadar upgrade:** Situational splits, opponent defense rankings, injury feeds
- **Correlated parlays:** Model joint probability of two props for the same player
