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
