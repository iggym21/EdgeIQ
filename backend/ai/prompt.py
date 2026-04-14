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
    if abs(float(ctx.get("line", 0)) - float(ctx.get("open_line", ctx.get("line", 0)))) >= 0.5:
        chips.append("Why might this line have moved?")
    if ctx.get("ev", 0) > 0:
        chips.append("What could invalidate this edge?")
    else:
        chips.append("Is there a case for taking this despite negative EV?")
    return chips[:3]
