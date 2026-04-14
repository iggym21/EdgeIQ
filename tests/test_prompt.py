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
