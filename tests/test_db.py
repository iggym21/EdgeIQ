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


def test_bets_direction_check_constraint(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.cursor()
    with pytest.raises(Exception):  # sqlite3.IntegrityError
        cursor.execute(
            "INSERT INTO bets (player_name, stat_category, line, direction, odds, stake) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("LeBron James", "points", 24.5, "sideways", -110, 10.0)
        )
        conn.commit()
    conn.close()


def test_player_stats_row_roundtrip(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO player_stats (player_id, player_name, game_date, stat_category, value) "
        "VALUES (?, ?, ?, ?, ?)",
        ("123", "LeBron James", "2026-04-01", "points", 28.0)
    )
    conn.commit()
    cursor.execute("SELECT * FROM player_stats WHERE player_id = '123'")
    row = cursor.fetchone()
    assert row["player_name"] == "LeBron James"
    assert row["value"] == 28.0
    assert row["user_id"] is None  # nullable, should default to NULL
    conn.close()
