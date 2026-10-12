"""Klasemen akhir per musim (2020 -> sekarang) dari historical_matches — cache per mtime."""
import pandas as pd

from data_paths import HISTORICAL_MATCHES, calendar_season

_CACHE = {"mtime": None, "tables": None}


def get_season_tables() -> dict:
    """{(league, season): {team: {pos, P, W, D, L, GF, GA, GD, PTS, ppg,
    xg_for_avg, xg_ga_avg, relegated, in_progress}}} — dihitung ulang bila CSV berubah."""
    try:
        mtime = HISTORICAL_MATCHES.stat().st_mtime
    except FileNotFoundError:
        return {}
    if _CACHE["tables"] is not None and _CACHE["mtime"] == mtime:
        return _CACHE["tables"]

    hist = pd.read_csv(HISTORICAL_MATCHES)
    cs = calendar_season()
    tables: dict = {}

    for (lg, season), g in hist.groupby(["league", "season"]):
        season = int(season)
        in_progress = season == cs
        stat: dict = {}
        for t in set(g["home_team"]) | set(g["away_team"]):
            stat[t] = {
                "P": 0, "W": 0, "D": 0, "L": 0,
                "GF": 0, "GA": 0, "GD": 0, "PTS": 0,
                "_xg_for": 0.0, "_xg_ga": 0.0,
            }
        for row in g.itertuples():
            h, a = row.home_team, row.away_team
            hg, ag = int(row.home_goals), int(row.away_goals)
            sh, sa = stat[h], stat[a]
            sh["P"] += 1
            sa["P"] += 1
            sh["GF"] += hg
            sh["GA"] += ag
            sa["GF"] += ag
            sa["GA"] += hg
            sh["_xg_for"] += float(row.home_xg)
            sh["_xg_ga"] += float(row.away_xg)
            sa["_xg_for"] += float(row.away_xg)
            sa["_xg_ga"] += float(row.home_xg)
            if hg > ag:
                sh["PTS"] += 3
                sh["W"] += 1
                sa["L"] += 1
            elif ag > hg:
                sa["PTS"] += 3
                sa["W"] += 1
                sh["L"] += 1
            else:
                sh["PTS"] += 1
                sa["PTS"] += 1
                sh["D"] += 1
                sa["D"] += 1

        for t in stat:
            s = stat[t]
            s["GD"] = s["GF"] - s["GA"]
            s["ppg"] = round(s["PTS"] / s["P"], 2) if s["P"] else 0.0
            s["xg_for_avg"] = round(s.pop("_xg_for") / s["P"], 2) if s["P"] else 0.0
            s["xg_ga_avg"] = round(s.pop("_xg_ga") / s["P"], 2) if s["P"] else 0.0
            s["in_progress"] = in_progress

        order = sorted(stat, key=lambda t: (-stat[t]["PTS"], -stat[t]["GD"], -stat[t]["GF"], t))
        n_rel = 3 if len(stat) >= 18 else 2
        for i, t in enumerate(order):
            stat[t]["pos"] = i + 1
            stat[t]["relegated"] = (i >= len(order) - n_rel) and not in_progress
        tables[(lg, season)] = stat

    _CACHE.update(mtime=mtime, tables=tables)
    return tables


def get_position_history(league_code: str) -> dict:
    """Riwayat posisi akhir per klub per musim untuk sparkline.

    Return: {"seasons": [2020, ...], "teams": {klub: [pos|null, ...]}}
    """
    tables = get_season_tables()
    seasons = sorted({s for (lg, s) in tables if lg == league_code})
    idx = {s: i for i, s in enumerate(seasons)}
    out: dict = {}
    for s in seasons:
        for t, row in tables.get((league_code, s), {}).items():
            arr = out.setdefault(t, [None] * len(seasons))
            arr[idx[s]] = row["pos"]
    return {"seasons": seasons, "teams": dict(sorted(out.items()))}


def relegated_last_label(league_code: str, team: str, before_season: int) -> str | None:
    """Label 'TURUN {yy/yy}' bila kehadiran terakhir klub di liga ini berakhir degradasi."""
    tables = get_season_tables()
    tl = team.lower()
    for s in sorted((s for (lg, s) in tables if lg == league_code and s < before_season), reverse=True):
        stat = tables[(league_code, s)]
        match = next((t for t in stat if t.lower() == tl), None)
        if match is None:
            continue
        if stat[match]["relegated"]:
            return f"TURUN {s}/{str(s + 1)[2:]}"
        return None
    return None
