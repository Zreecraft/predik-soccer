import json

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from assets import get_key_player, get_team_logo
from club_analytics import get_club_analytics, LEAGUE_NAMES
from data_paths import HISTORICAL_MATCHES, REAL_SHOTS_DATA, UPCOMING_FIXTURES
from run_prediction import calculate_smart_projected_score, simulate_10k_matches_minute_by_minute
from season_projection import project_league
from team_aliases import team_abbr
from team_analytics import clamp_match_xg, get_home_away_bias, get_team_form, get_team_power_index
from ucl_simulator import simulate_ucl_tournament

app = FastAPI(title="Analytica FC API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SHOTS_CACHE = None
_UCL_CACHE = None


def _load_shots() -> pd.DataFrame | None:
    global _SHOTS_CACHE
    if _SHOTS_CACHE is None:
        try:
            _SHOTS_CACHE = pd.read_csv(REAL_SHOTS_DATA)
        except FileNotFoundError:
            _SHOTS_CACHE = pd.DataFrame()
    return _SHOTS_CACHE


def _team_shot_summary(team: str, shots_df: pd.DataFrame) -> dict:
    team_shots = shots_df[shots_df["team_name"].str.lower() == team.lower()]
    if team_shots.empty:
        return {
            "shots": 0, "goals": 0, "xg": 0.0, "conversion_pct": 0.0,
            "zone14_shots": 0, "zone14_pct": 0.0, "on_target_pct": 0.0,
            "points": [],
        }
    shots = len(team_shots)
    goals = int((team_shots["result"] == "Goal").sum())
    xg = float(team_shots["xG"].sum())
    z14 = int(((team_shots["X"] >= 0.72) & (team_shots["X"] < 0.88) & (team_shots["Y"] >= 0.35) & (team_shots["Y"] <= 0.65)).sum())
    on_target = int(team_shots["result"].isin(["Goal", "SavedShot"]).sum())
    points = []
    for _, s in team_shots.iterrows():
        points.append({
            "x": round(float(s["X"]), 4),
            "y": round(float(s["Y"]), 4),
            "xg": round(float(s["xG"]), 4),
            "result": str(s["result"]),
            "minute": int(s["minute"]) if pd.notna(s.get("minute")) else None,
            "player": str(s.get("player", "")),
        })
    return {
        "shots": shots,
        "goals": goals,
        "xg": round(xg, 2),
        "conversion_pct": round(goals / shots * 100, 1) if shots else 0.0,
        "zone14_shots": z14,
        "zone14_pct": round(z14 / shots * 100, 1) if shots else 0.0,
        "on_target_pct": round(on_target / shots * 100, 1) if shots else 0.0,
        "points": points,
    }


def _tactical_metrics(team: str, power: dict, shots_summary: dict, shots_against_xg: float) -> dict:
    """Metrik taktis model (turunan data + heuristik berlabel model)."""
    avg_xg = power.get("avg_xg", 1.2)
    avg_ga = power.get("avg_ga", 1.2)
    win_rate = power.get("win_rate", 45.0)
    conversion = shots_summary.get("conversion_pct", 10.0)
    # PPDA proxy: makin banyak gol kebobolan vs xG for, makin longgar press
    ppda = round(float(np.clip(12.0 - (avg_xg - avg_ga) * 2.5 - (win_rate - 45) * 0.04, 6.5, 17.5)), 1)
    # Duel / ball recovery proxy
    duels = round(float(np.clip(48 + (avg_xg - 1.2) * 8 + (50 - avg_ga) * 3, 40, 62)), 1)
    possession = round(float(np.clip(46 + (avg_xg - 1.2) * 10 + (win_rate - 45) * 0.15, 35, 64)), 1)
    return {
        "xg": round(avg_xg, 2),
        "conversion_pct": conversion,
        "ppda": ppda,
        "duels_pct": duels,
        "possession_pct": possession,
        "win_rate": win_rate,
        "avg_ga": avg_ga,
        "shots_against_xg": round(shots_against_xg, 2),
    }


def _differential_summary(home_team: str, away_team: str, home_t: dict, away_t: dict, home_xg: float, away_xg: float) -> str:
    xg_diff = home_xg - away_xg
    ppda_diff = home_t["ppda"] - away_t["ppda"]
    parts = []
    if abs(xg_diff) >= 0.35:
        leader = home_team if xg_diff > 0 else away_team
        parts.append(f"{leader} unggul proyeksi xG ({max(home_xg, away_xg):.2f} vs {min(home_xg, away_xg):.2f}).")
    else:
        parts.append("Proyeksi xG kedua tim relatif seimbang.")
    if abs(ppda_diff) >= 1.2:
        press_team = home_team if ppda_diff < 0 else away_team
        parts.append(f"{press_team} menekan lebih agresif (PPDA {min(home_t['ppda'], away_t['ppda']):.1f}).")
    else:
        parts.append("Intensitas press kedua tim setara.")
    conv_leader = home_team if home_t["conversion_pct"] >= away_t["conversion_pct"] else away_team
    parts.append(f"{conv_leader} lebih efisien mengubah peluang ({max(home_t['conversion_pct'], away_t['conversion_pct']):.1f}% conversion).")
    if xg_diff > 0.2:
        parts.append(f"Kendali territorial condong ke {home_team} di sepertiga akhir.")
    elif xg_diff < -0.2:
        parts.append(f"Kendali territorial condong ke {away_team} di sepertiga akhir.")
    else:
        parts.append("Pertarungan zona 14 diprediksi ketat.")
    return " ".join(parts)


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Analytica FC API"}


@app.get("/api/leagues")
def get_leagues():
    return [
        {"id": "EPL", "name": "English Premier League", "country": "England"},
        {"id": "La_liga", "name": "La Liga", "country": "Spain"},
        {"id": "Serie_A", "name": "Serie A", "country": "Italy"},
        {"id": "Bundesliga", "name": "Bundesliga", "country": "Germany"},
    ]


@app.get("/api/fixtures/{league_code}")
def get_fixtures(league_code: str, limit: int = 40):
    try:
        df = pd.read_csv(UPCOMING_FIXTURES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="File upcoming_fixtures.csv belum ditemukan.")

    filtered = df[df["league"] == league_code].head(limit).to_dict(orient="records")
    if not filtered:
        raise HTTPException(status_code=404, detail=f"Tidak ada jadwal untuk liga '{league_code}'.")

    for fix in filtered:
        fix["home_logo"] = get_team_logo(fix["home_team"])
        fix["away_logo"] = get_team_logo(fix["away_team"])
        fix["home_star_player"] = get_key_player(fix["home_team"])
        fix["away_star_player"] = get_key_player(fix["away_team"])
        date_str = str(fix.get("date", ""))
        fix["date_short"] = date_str[:16] if date_str else ""

    return {
        "league": league_code,
        "league_name": LEAGUE_NAMES.get(league_code, league_code),
        "total": len(filtered),
        "fixtures": filtered,
    }


@app.get("/api/ticker")
def get_ticker(limit: int = 16):
    """Ringkasan pekan aktif untuk navbar ticker."""
    try:
        df = pd.read_csv(UPCOMING_FIXTURES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="File upcoming_fixtures.csv belum ditemukan.")

    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date_dt"]).sort_values("date_dt").head(limit)

    items = []
    for _, row in df.iterrows():
        items.append({
            "home": row["home_team"],
            "away": row["away_team"],
            "home_short": team_abbr(row["home_team"]),
            "away_short": team_abbr(row["away_team"]),
            "date": str(row["date"])[:16],
            "league": row["league"],
        })
    return {"items": items, "total": len(items)}


@app.get("/api/predict")
def predict_match(home_team: str, away_team: str):
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    shots_df = _load_shots()

    home_stats = get_team_power_index(home_team, matches_df, last_n=20)
    away_stats = get_team_power_index(away_team, matches_df, last_n=20)

    home_bias = get_home_away_bias(home_team, is_home=True, matches_df=matches_df)
    away_bias = get_home_away_bias(away_team, is_home=False, matches_df=matches_df)

    final_home_xg = clamp_match_xg(home_stats["avg_xg"] * home_bias)
    final_away_xg = clamp_match_xg(away_stats["avg_xg"] * away_bias)

    home_sim, away_sim, prob_ht = simulate_10k_matches_minute_by_minute(
        final_home_xg, final_away_xg, iterations=10000, verbose=False
    )

    prob_home = round((np.sum(home_sim > away_sim) / 10000) * 100, 1)
    prob_draw = round((np.sum(home_sim == away_sim) / 10000) * 100, 1)
    prob_away = round((np.sum(away_sim > home_sim) / 10000) * 100, 1)

    smart_h, smart_a, confidence = calculate_smart_projected_score(
        home_sim, away_sim, prob_home, prob_away, final_home_xg, final_away_xg
    )

    home_form = get_team_form(home_team, matches_df, 5)
    away_form = get_team_form(away_team, matches_df, 5)

    home_shots = _team_shot_summary(home_team, shots_df)
    away_shots = _team_shot_summary(away_team, shots_df)

    home_tactical = _tactical_metrics(home_team, home_stats, home_shots, away_shots["xg"])
    away_tactical = _tactical_metrics(away_team, away_stats, away_shots, home_shots["xg"])

    differential = _differential_summary(
        home_team, away_team, home_tactical, away_tactical, final_home_xg, final_away_xg
    )

    return {
        "match": f"{home_team} vs {away_team}",
        "home_team": {
            "name": home_team,
            "logo": get_team_logo(home_team),
            "star_player": get_key_player(home_team),
            "form": home_form,
        },
        "away_team": {
            "name": away_team,
            "logo": get_team_logo(away_team),
            "star_player": get_key_player(away_team),
            "form": away_form,
        },
        "meta": {
            "stadium": "Stadion pertandingan",
            "referee": "Wasit pertandingan",
            "competition": "Liga",
            "note": "Meta stadion/wasit placeholder — data Understat tidak menyertakan info ini.",
        },
        "projection": {
            "score": f"{smart_h} - {smart_a}",
            "home_score": int(smart_h),
            "away_score": int(smart_a),
            "confidence_pct": confidence,
        },
        "probabilities": {
            "home_win": prob_home,
            "draw": prob_draw,
            "away_win": prob_away,
        },
        "analytics": {
            "home_xg": final_home_xg,
            "away_xg": final_away_xg,
            "first_half_goal_probability": prob_ht,
        },
        "tactical": {
            "home": home_tactical,
            "away": away_tactical,
        },
        "shots": {
            "home": {k: v for k, v in home_shots.items() if k != "points"},
            "away": {k: v for k, v in away_shots.items() if k != "points"},
        },
        "differential_summary": differential,
    }


@app.get("/api/shots")
def get_shot_map(home_team: str, away_team: str):
    shots_df = _load_shots()
    if shots_df is None or shots_df.empty:
        raise HTTPException(status_code=404, detail="Data tembakan belum tersedia.")

    home = _team_shot_summary(home_team, shots_df)
    away = _team_shot_summary(away_team, shots_df)

    def _summary(side_summary, side_name):
        return {
            "team": side_name,
            "shots": side_summary["shots"],
            "goals": side_summary["goals"],
            "xg": side_summary["xg"],
            "conversion_pct": side_summary["conversion_pct"],
            "zone14_shots": side_summary["zone14_shots"],
            "zone14_pct": side_summary["zone14_pct"],
            "on_target_pct": side_summary["on_target_pct"],
            "points": side_summary["points"],
        }

    return {
        "home": _summary(home, home_team),
        "away": _summary(away, away_team),
        "summary": {
            "zone14_home": home["zone14_shots"],
            "zone14_away": away["zone14_shots"],
            "zone14_dominance": home_team if home["zone14_shots"] >= away["zone14_shots"] else away_team,
            "suppression_home": round(
                max(0.0, min(100.0, (1 - away["xg"] / max(home["shots"] * 0.11, 0.2)) * 100)), 1
            ),
            "suppression_away": round(
                max(0.0, min(100.0, (1 - home["xg"] / max(away["shots"] * 0.11, 0.2)) * 100)), 1
            ),
        },
    }


@app.get("/api/standings/{league_code}")
def get_league_standings(league_code: str, n_seasons: int = 350):
    try:
        projection = project_league(league_code, n_seasons=min(max(n_seasons, 100), 800))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    # Enrich logo & star player
    for row in projection["standings"]:
        row["logo"] = get_team_logo(row["team"])
        row["star_player"] = get_key_player(row["team"])
        row["zone"] = _zone_label(row["projected_position"], len(projection["standings"]))

    return projection


def _zone_label(pos: int, total: int) -> str:
    if pos <= 4:
        return "UCL"
    if pos <= 6:
        return "UEL"
    if pos >= total - 2:
        return "REL"
    return "MID"


@app.get("/api/ucl/simulate")
def simulate_ucl():
    global _UCL_CACHE
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    if _UCL_CACHE is None:
        _UCL_CACHE = simulate_ucl_tournament(matches_df)

    result = json.loads(json.dumps(_UCL_CACHE))

    for item in result["league_phase"]:
        item["logo"] = get_team_logo(item["team"])
        item["star_player"] = get_key_player(item["team"])

    for stage in ("playoffs", "round_of_16", "quarter_finals", "semi_finals"):
        for m in result["knockout_stage"][stage]:
            m["logo_home"] = get_team_logo(m["team_home"])
            m["logo_away"] = get_team_logo(m["team_away"])

    final_m = result["knockout_stage"]["final"]
    final_m["logo_home"] = get_team_logo(final_m["team_home"])
    final_m["logo_away"] = get_team_logo(final_m["team_away"])

    champion = result["champion"]
    champion["logo"] = get_team_logo(champion["team"])
    champion["star_player"] = get_key_player(champion["team"])
    return result


@app.get("/api/analytics/{team}")
def analytics_team(team: str):
    try:
        return get_club_analytics(team)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data pendukung analitik belum ada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membangun analitik klub: {e}")


@app.get("/api/teams")
def list_teams(league: str | None = None):
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    df = matches_df
    if league:
        df = df[df["league"] == league]
    teams = sorted(set(df["home_team"]).union(set(df["away_team"])))
    return {
        "league": league,
        "teams": [
            {"name": t, "logo": get_team_logo(t), "star_player": get_key_player(t)}
            for t in teams
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
