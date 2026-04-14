def build_system_prompt(ctx: dict) -> str:
    line = ctx.get("line")
    line_f = float(line) if line not in (None, "?") else None
    open_line = ctx.get("open_line", line)
    current_line = line

    try:
        delta = round(float(current_line) - float(open_line), 1) if open_line not in (None, "?") else 0
    except (TypeError, ValueError):
        delta = 0

    # Full season game log table
    full_log = ctx.get("full_season_log", [])
    game_table_lines = []
    for g in full_log:
        val = g.get("value")
        if line_f is not None and isinstance(val, (int, float)):
            hit = "✅" if val > line_f else "❌"
        else:
            hit = "—"
        game_table_lines.append(
            f"  {g.get('game_date','?')} | {g.get('opponent','?')} | {g.get('home_away','?')} | {val} | {hit}"
        )
    game_table = "\n".join(game_table_lines) if game_table_lines else "  (no data)"

    # Matchup breakdown from full season
    matchup_stats: dict[str, list[float]] = {}
    for g in full_log:
        opp = g.get("opponent", "UNK")
        val = g.get("value")
        if isinstance(val, (int, float)):
            matchup_stats.setdefault(opp, []).append(val)

    matchup_lines = []
    for opp, vals in sorted(matchup_stats.items()):
        avg = sum(vals) / len(vals)
        if line_f is not None:
            hits = sum(1 for v in vals if v > line_f)
            matchup_lines.append(
                f"  {opp}: {len(vals)}G | avg {avg:.1f} | {hits}/{len(vals)} over {line_f}"
            )
        else:
            matchup_lines.append(f"  {opp}: {len(vals)}G | avg {avg:.1f}")
    matchup_section = "\n".join(matchup_lines) if matchup_lines else "  (no data)"

    windowed_values = ", ".join(str(v) for v in ctx.get("game_log_values", []))

    low_conf_note = (
        f"\n⚠ Small sample (N={ctx.get('sample_size','?')}) — flag uncertainty in answers."
        if ctx.get("low_confidence") else ""
    )

    return f"""You are EdgeIQ's betting analyst. Answer questions concisely and factually using the data below.
Do not recommend bets — explain what the data shows and let the user decide.{low_conf_note}

=== CURRENT PROP ===
Player: {ctx.get('player_name', '?')} | Stat: {ctx.get('stat_category', '?')}
Line: {line} | Odds: {ctx.get('over_odds', '?')} | Distribution: {ctx.get('distribution', '?')}
Analysis window: last {ctx.get('window', '?')} games | Sample size: {ctx.get('sample_size', '?')}

Model: prob={round(ctx.get('your_prob', 0) * 100, 1)}% | EV={ctx.get('ev', '?')} | edge={ctx.get('edge_pct', '?')}%
Book implied: {round(ctx.get('implied_prob', 0) * 100, 1)}%
Line movement: opened {open_line} → now {current_line} ({delta:+.1f})
Last {ctx.get('window', '?')} values: {windowed_values}

=== FULL SEASON GAME LOG (date | opponent | home/away | value | over line?) ===
{game_table}

=== MATCHUP SPLITS THIS SEASON (vs each opponent) ===
{matchup_section}"""


def build_suggested_chips(ctx: dict) -> list[str]:
    player = ctx.get("player_name", "this player")
    opponent = ctx.get("opponent", "this opponent")
    chips = [f"How has {player} performed vs {opponent} historically?"]

    try:
        line = float(ctx.get("line", 0))
        open_line = float(ctx.get("open_line", line))
        if abs(line - open_line) >= 0.5:
            chips.append("Why might this line have moved?")
    except (TypeError, ValueError):
        pass

    if ctx.get("ev", 0) > 0:
        chips.append("What could invalidate this edge?")
    else:
        chips.append("Is there a case for taking this despite negative EV?")

    return chips[:3]
