"""Analitik klub: profil taktis, heatmap teritorial, bullet metrics, jadwal mendatang."""
import hashlib
import numpy as np
import pandas as pd

from assets import get_team_logo
from club_data import ga_prior_from_rating, get_club_strength, xg_prior_from_rating
from data_paths import HISTORICAL_MATCHES, REAL_SHOTS_DATA, UPCOMING_FIXTURES
from team_analytics import clamp_match_xg, get_home_away_bias, get_team_form, get_team_power_index

DEFAULT_PROFILE = {
    "coach": "Staff Analitik",
    "formation": "4-3-3",
    "stadium": "Stadion Klub",
    "style": "possession",
    "overload_side": "Kanan",
    "set_piece_rating": 55,
}

# Metadata statis 2026 (dapat diperbarui tanpa menyentuh engine)
CLUB_PROFILES = {
    "Arsenal": {"coach": "Mikel Arteta", "formation": "4-3-3 / 3-2-4-1", "stadium": "Emirates Stadium", "style": "possession", "overload_side": "Kanan", "set_piece_rating": 78},
    "Manchester City": {"coach": "Pep Guardiola", "formation": "4-2-3-1 / 3-2-4-1", "stadium": "Etihad Stadium", "style": "possession", "overload_side": "Kiri", "set_piece_rating": 72},
    "Liverpool": {"coach": "Arne Slot", "formation": "4-2-3-1", "stadium": "Anfield", "style": "gegenpress", "overload_side": "Kanan", "set_piece_rating": 70},
    "Chelsea": {"coach": "Enzo Maresca", "formation": "4-2-3-1 / 3-4-2-1", "stadium": "Stamford Bridge", "style": "possession", "overload_side": "Kanan", "set_piece_rating": 64},
    "Tottenham": {"coach": "Thomas Frank", "formation": "4-2-3-1", "stadium": "Tottenham Hotspur Stadium", "style": "vertical", "overload_side": "Kiri", "set_piece_rating": 61},
    "Manchester United": {"coach": "Ruben Amorim", "formation": "3-4-2-1", "stadium": "Old Trafford", "style": "vertical", "overload_side": "Kanan", "set_piece_rating": 58},
    "Aston Villa": {"coach": "Unai Emery", "formation": "4-2-3-1", "stadium": "Villa Park", "style": "transition", "overload_side": "Kiri", "set_piece_rating": 74},
    "Newcastle": {"coach": "Eddie Howe", "formation": "4-3-3", "stadium": "St James' Park", "style": "high_press", "overload_side": "Kanan", "set_piece_rating": 71},
    "Brighton": {"coach": "Fabian Hurzeler", "formation": "4-2-3-1", "stadium": "Amex Stadium", "style": "possession", "overload_side": "Kiri", "set_piece_rating": 59},
    "West Ham": {"coach": "Graham Potter", "formation": "4-2-3-1", "stadium": "London Stadium", "style": "transition", "overload_side": "Kanan", "set_piece_rating": 66},
    "Real Madrid": {"coach": "Xabi Alonso", "formation": "4-3-3 / 4-2-3-1", "stadium": "Santiago Bernabéu", "style": "transition", "overload_side": "Kanan", "set_piece_rating": 68},
    "Barcelona": {"coach": "Hansi Flick", "formation": "4-3-3", "stadium": "Spotify Camp Nou", "style": "possession", "overload_side": "Kanan", "set_piece_rating": 65},
    "Atletico Madrid": {"coach": "Diego Simeone", "formation": "4-4-2 / 3-5-2", "stadium": "Metropolitano", "style": "defensive_block", "overload_side": "Kiri", "set_piece_rating": 80},
    "Inter": {"coach": "Cristian Chivu", "formation": "3-5-2", "stadium": "San Siro", "style": "possession", "overload_side": "Kiri", "set_piece_rating": 76},
    "AC Milan": {"coach": "Massimiliano Allegri", "formation": "3-5-2 / 4-2-3-1", "stadium": "San Siro", "style": "transition", "overload_side": "Kiri", "set_piece_rating": 67},
    "Juventus": {"coach": "Igor Tudor", "formation": "3-4-2-1", "stadium": "Allianz Stadium", "style": "balanced", "overload_side": "Kanan", "set_piece_rating": 70},
    "Napoli": {"coach": "Antonio Conte", "formation": "4-3-3", "stadium": "Diego Armando Maradona", "style": "high_press", "overload_side": "Kanan", "set_piece_rating": 73},
    "Bayern Munich": {"coach": "Vincent Kompany", "formation": "4-2-3-1", "stadium": "Allianz Arena", "style": "high_press", "overload_side": "Kiri", "set_piece_rating": 75},
    "Bayer Leverkusen": {"coach": "Kasper Hjulmand", "formation": "3-4-2-1", "stadium": "BayArena", "style": "possession", "overload_side": "Kanan", "set_piece_rating": 69},
    "Borussia Dortmund": {"coach": "Niko Kovac", "formation": "4-2-3-1", "stadium": "Signal Iduna Park", "style": "transition", "overload_side": "Kanan", "set_piece_rating": 64},
    "RB Leipzig": {"coach": "Ole Werner", "formation": "4-2-3-1", "stadium": "Red Bull Arena", "style": "high_press", "overload_side": "Kiri", "set_piece_rating": 62},
    "PSG": {"coach": "Luis Enrique", "formation": "4-3-3", "stadium": "Parc des Princes", "style": "possession", "overload_side": "Kiri", "set_piece_rating": 66},
    "Sporting CP": {"coach": "Rui Borges", "formation": "3-4-3", "stadium": "Estádio José Alvalade", "style": "high_press", "overload_side": "Kanan", "set_piece_rating": 71},
    "Benfica": {"coach": "Jose Mourinho", "formation": "4-2-3-1", "stadium": "Estádio da Luz", "style": "possession", "overload_side": "Kanan", "set_piece_rating": 72},
}

DIFFICULTY_BANDS = [
    (0.0, 35.0, "MUDAH", "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"),
    (35.0, 55.0, "SEDANG", "bg-sky-500/15 text-sky-400 border-sky-500/30"),
    (55.0, 72.0, "SULIT", "bg-amber-500/15 text-amber-400 border-amber-500/30"),
    (72.0, 101.0, "SANGAT SULIT", "bg-rose-500/15 text-rose-400 border-rose-500/30"),
]


def _team_hash(name: str) -> int:
    return int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)


def _get_profile(team: str) -> dict:
    """Profil tim: statis (overload/set-piece) -> live club_profiles.json (coach/formasi/rating)."""
    profile = {**DEFAULT_PROFILE, **CLUB_PROFILES.get(team, {})}
    live = _get_live_profile(team)
    for key in ("coach", "formation", "stadium", "style", "rating", "coach_rating"):
        if live.get(key) not in (None, ""):
            profile[key] = live[key]
    return profile


def _get_live_profile(team: str) -> dict:
    try:
        from club_data import get_club_profile

        return get_club_profile(team)
    except Exception:
        return {}


def _difficulty_from_win_prob(win_pct: float) -> tuple:
    for lo, hi, label, cls in DIFFICULTY_BANDS:
        if lo <= win_pct < hi:
            return label, cls
    return "SANGAT SULIT", DIFFICULTY_BANDS[-1][3]


def _build_territorial_grid(team: str, profile: dict, shots_df: pd.DataFrame | None) -> list:
    """Grid 6x5 intensitas dominasi serangan (0-100)."""
    rows, cols = 5, 6
    base = {
        "possession": [40, 55, 70, 75, 65, 50, 30, 45, 62, 78, 70, 48, 22, 35, 55, 72, 68, 42, 15, 28, 48, 60, 55, 35, 10, 18, 35, 48, 45, 28],
        "high_press": [55, 68, 78, 80, 72, 58, 42, 58, 72, 76, 68, 50, 30, 45, 60, 65, 58, 40, 20, 32, 48, 52, 48, 32, 12, 22, 35, 40, 35, 22],
        "transition": [30, 48, 62, 72, 68, 52, 25, 40, 58, 70, 65, 48, 20, 32, 50, 64, 60, 42, 14, 25, 42, 55, 50, 35, 8, 18, 32, 42, 38, 25],
        "gegenpress": [50, 65, 75, 78, 70, 55, 38, 52, 68, 74, 66, 48, 28, 42, 58, 64, 58, 40, 18, 30, 46, 52, 46, 30, 10, 20, 34, 40, 34, 22],
        "defensive_block": [25, 38, 50, 58, 52, 40, 20, 32, 45, 55, 50, 38, 15, 25, 40, 48, 44, 32, 10, 20, 34, 40, 36, 25, 6, 14, 25, 30, 28, 18],
        "vertical": [35, 50, 65, 74, 70, 55, 28, 42, 58, 70, 66, 50, 22, 35, 52, 66, 62, 45, 12, 24, 40, 54, 50, 35, 8, 16, 30, 42, 40, 28],
        "balanced": [38, 52, 64, 70, 64, 50, 28, 42, 56, 66, 62, 46, 22, 34, 48, 60, 56, 40, 12, 24, 40, 50, 46, 32, 8, 16, 30, 38, 34, 22],
    }
    template = base.get(profile.get("style", "balanced"), base["balanced"]).copy()

    # Bias sisi overload
    side = profile.get("overload_side", "Kanan")
    rng = np.random.default_rng(_team_hash(team) % (2**32))
    jitter = rng.integers(-6, 7, size=len(template))
    grid = np.clip(np.array(template) + jitter, 5, 95)

    # Jika ada data shots, boost zona dengan tembakan nyata
    if shots_df is not None and not shots_df.empty:
        for _, s in shots_df.iterrows():
            x = float(s.get("X", 0.5))
            y = float(s.get("Y", 0.5))
            col = min(cols - 1, max(0, int(x * cols)))
            row_from_bottom = min(rows - 1, max(0, int(y * rows)))
            idx = (rows - 1 - row_from_bottom) * cols + col
            xg = float(s.get("xG", 0.05))
            grid[idx] = min(95, grid[idx] + xg * 40)

    if side == "Kanan":
        # kolom kanan grid (indeks 2,5,8,...) dinaikkan ringan
        for r in range(rows):
            grid[r * cols + 2] = min(95, grid[r * cols + 2] + 6)
            grid[r * cols + 3] = min(95, grid[r * cols + 3] + 4)
    else:
        for r in range(rows):
            grid[r * cols + 0] = min(95, grid[r * cols + 0] + 6)
            grid[r * cols + 1] = min(95, grid[r * cols + 1] + 4)

    return [{"row": i // cols, "col": i % cols, "value": int(v)} for i, v in enumerate(grid)]


def _shot_metrics(team: str, shots_df: pd.DataFrame | None) -> dict:
    empty = {
        "shots": 0, "goals": 0, "xg_total": 0.0, "conversion_pct": 0.0,
        "zone14_shots": 0, "zone14_pct": 0.0, "on_target_pct": 0.0,
        "shots_against": 0, "xg_against": 0.0, "suppress_pct": 0.0,
    }
    if shots_df is None or shots_df.empty:
        return empty

    team_shots = shots_df[shots_df["team_name"].str.lower() == team.lower()]
    opp_shots = shots_df[shots_df["opponent"].str.lower() == team.lower()]

    def _summarize(df):
        if df.empty:
            return {"shots": 0, "goals": 0, "xg_total": 0.0, "conversion_pct": 0.0, "zone14_shots": 0, "zone14_pct": 0.0, "on_target_pct": 0.0}
        shots = len(df)
        goals = int((df["result"] == "Goal").sum())
        xg_total = float(df["xG"].sum())
        # Understat: X makin dekat 1 = makin dekat gawang; zone 14 = area di luar kotak penalti tengah
        z14 = int(((df["X"] >= 0.72) & (df["X"] < 0.88) & (df["Y"] >= 0.35) & (df["Y"] <= 0.65)).sum())
        on_target = int(df["result"].isin(["Goal", "SavedShot"]).sum())
        return {
            "shots": shots,
            "goals": goals,
            "xg_total": round(xg_total, 2),
            "conversion_pct": round(goals / shots * 100, 1) if shots else 0.0,
            "zone14_shots": z14,
            "zone14_pct": round(z14 / shots * 100, 1) if shots else 0.0,
            "on_target_pct": round(on_target / shots * 100, 1) if shots else 0.0,
        }

    home = _summarize(team_shots)
    away = _summarize(opp_shots)
    return {
        **home,
        "shots_against": away["shots"],
        "xg_against": away["xg_total"],
        "suppress_pct": round((1 - away["xg_total"] / max(home["shots"] * 0.12, 0.1)) * 100, 1) if away["shots"] else 0.0,
    }


def _ppda_estimate(team: str, shots_df: pd.DataFrame | None, profile: dict) -> float:
    """Estimasi PPDA dari rasio tekanan proxy (shots against per shot for) + profil."""
    base = {"high_press": 8.5, "gegenpress": 9.2, "possession": 11.0, "transition": 12.5, "vertical": 12.0, "balanced": 11.5, "defensive_block": 14.5}
    val = base.get(profile.get("style", "balanced"), 11.5)
    if shots_df is not None and not shots_df.empty:
        team_shots = shots_df[shots_df["team_name"].str.lower() == team.lower()]
        opp_shots = shots_df[shots_df["opponent"].str.lower() == team.lower()]
        if len(team_shots) > 0 and len(opp_shots) > 0:
            ratio = len(opp_shots) / len(team_shots)
            val = val * 0.5 + (ratio * 12) * 0.5
    return round(float(np.clip(val, 6.0, 18.0)), 1)


def _xg_trend(team: str, historical_df: pd.DataFrame, n: int = 10) -> list:
    mask = (historical_df["home_team"].str.contains(team, case=False, na=False)) | (
        historical_df["away_team"].str.contains(team, case=False, na=False)
    )
    team_matches = historical_df[mask].sort_values(by="datetime", ascending=False).head(n).iloc[::-1]
    series = []
    for _, row in team_matches.iterrows():
        is_home = team.lower() in str(row["home_team"]).lower()
        xg_for = float(row["home_xg"]) if is_home else float(row["away_xg"])
        xg_against = float(row["away_xg"]) if is_home else float(row["home_xg"])
        series.append({
            "date": str(row["datetime"])[:10],
            "xg_for": round(xg_for, 2),
            "xg_against": round(xg_against, 2),
            "opponent": row["away_team"] if is_home else row["home_team"],
        })
    return series


def get_club_analytics(team: str) -> dict:
    historical_df = pd.read_csv(HISTORICAL_MATCHES)
    fixtures_df = pd.read_csv(UPCOMING_FIXTURES)
    try:
        shots_df = pd.read_csv(REAL_SHOTS_DATA)
    except FileNotFoundError:
        shots_df = None

    profile = _get_profile(team)
    team_strength = get_club_strength(team)
    power = get_team_power_index(
        team, historical_df, last_n=20,
        prior_xg=xg_prior_from_rating(team_strength["overall"]),
        prior_ga=ga_prior_from_rating(team_strength["overall"]),
    )

    # Posisi liga saat ini
    league_code = None
    league_mask = (historical_df["home_team"].str.contains(team, case=False, na=False)) | (
        historical_df["away_team"].str.contains(team, case=False, na=False)
    )
    if league_mask.any():
        league_code = historical_df.loc[league_mask, "league"].mode().iloc[0]

    league_position = None
    league_name = league_code
    if league_code:
        league_hist = historical_df[historical_df["league"] == league_code]
        teams = set(league_hist["home_team"]).union(set(league_hist["away_team"]))
        table = {}
        for t in teams:
            tmask = (league_hist["home_team"].str.contains(t, case=False, na=False)) | (
                league_hist["away_team"].str.contains(t, case=False, na=False)
            )
            tdf = league_hist[tmask]
            pts = 0
            for _, row in tdf.iterrows():
                is_home = t.lower() in str(row["home_team"]).lower()
                gf = int(row["home_goals"]) if is_home else int(row["away_goals"])
                ga = int(row["away_goals"]) if is_home else int(row["home_goals"])
                if gf > ga:
                    pts += 3
                elif gf == ga:
                    pts += 1
            table[t] = pts
        ranked = sorted(table.items(), key=lambda kv: -kv[1])
        for i, (t, _) in enumerate(ranked):
            if t.lower() == team.lower():
                league_position = i + 1
                break
        league_name = LEAGUE_NAMES.get(league_code, league_code)

    shot_metrics = _shot_metrics(team, shots_df)
    ppda = _ppda_estimate(team, shots_df, profile)
    form = get_team_form(team, historical_df, n=5)
    xg_trend = _xg_trend(team, historical_df, n=10)
    territorial = _build_territorial_grid(team, profile, shots_df)

    # Jadwal mendatang + proyeksi
    team_fixtures = fixtures_df[
        (fixtures_df["home_team"].str.contains(team, case=False, na=False))
        | (fixtures_df["away_team"].str.contains(team, case=False, na=False))
    ].head(6)

    upcoming = []
    for _, row in team_fixtures.iterrows():
        h, a = row["home_team"], row["away_team"]
        is_home = h.lower() == team.lower()
        opponent = a if is_home else h
        h_str = get_club_strength(h)
        a_str = get_club_strength(a)
        h_stats = get_team_power_index(
            h, historical_df, last_n=20,
            prior_xg=xg_prior_from_rating(h_str["overall"]),
            prior_ga=ga_prior_from_rating(h_str["overall"]),
        )
        a_stats = get_team_power_index(
            a, historical_df, last_n=20,
            prior_xg=xg_prior_from_rating(a_str["overall"]),
            prior_ga=ga_prior_from_rating(a_str["overall"]),
        )
        h_bias = get_home_away_bias(h, is_home=True, matches_df=historical_df)
        a_bias = get_home_away_bias(a, is_home=False, matches_df=historical_df)
        gap_mult_h = 1.0 + (h_str["overall"] - a_str["overall"]) * 0.004
        gap_mult_a = 1.0 + (a_str["overall"] - h_str["overall"]) * 0.004
        h_xg = clamp_match_xg(h_stats["avg_xg"] * h_bias * gap_mult_h)
        a_xg = clamp_match_xg(a_stats["avg_xg"] * a_bias * gap_mult_a)

        rng = np.random.default_rng(abs(_team_hash(str(row.get("match_id", opponent)))) % (2**32))
        sims = 400
        hg = rng.poisson(h_xg, sims)
        ag = rng.poisson(a_xg, sims)
        pw = float(np.mean(hg > ag)) * 100
        pd_ = float(np.mean(hg == ag)) * 100
        pl = float(np.mean(hg < ag)) * 100
        team_win = pw if is_home else pl
        difficulty, difficulty_cls = _difficulty_from_win_prob(team_win)
        upcoming.append({
            "match_id": row.get("match_id"),
            "league": row.get("league"),
            "date": str(row.get("date")),
            "home_team": h,
            "away_team": a,
            "opponent": opponent,
            "is_home": is_home,
            "prob_home": round(pw, 1),
            "prob_draw": round(pd_, 1),
            "prob_away": round(pl, 1),
            "team_win_pct": round(team_win, 1),
            "difficulty": difficulty,
            "difficulty_cls": difficulty_cls,
        })

    # Bullet tactical cards
    overload_pct = min(95, 45 + (shot_metrics.get("zone14_pct", 0) * 0.4) + (12 if profile["overload_side"] == "Kanan" else 8))
    set_piece = profile["set_piece_rating"]
    ppda_score = max(5, min(95, int((18 - ppda) * 8)))

    return {
        "team": team,
        "league": league_code,
        "league_name": league_name,
        "league_position": league_position,
        "logo": get_team_logo(team),
        "profile": {
            "coach": profile["coach"],
            "formation": profile["formation"],
            "stadium": profile["stadium"],
            "style": profile["style"],
            "overload_side": profile["overload_side"],
            "rating": profile.get("rating"),
            "coach_rating": profile.get("coach_rating"),
        },
        "power": power,
        "form": form,
        "xg_trend": xg_trend,
        "shot_metrics": shot_metrics,
        "ppda": ppda,
        "territorial": territorial,
        "tactical_bullets": [
            {
                "key": "overload",
                "title": f"Overload Sayap {profile['overload_side']}",
                "value": f"{round(overload_pct)}%",
                "detail": f"Dominasi build-up sisi {profile['overload_side'].lower()} dengan densitas half-space aktif.",
                "tone": "sky",
            },
            {
                "key": "set_piece",
                "title": "Efisiensi Set-Piece",
                "value": f"{set_piece}/100",
                "detail": "Indeks ancaman bola mati berdasarkan profil taktis & rekam jejak.",
                "tone": "amber",
            },
            {
                "key": "ppda",
                "title": "Indeks PPDA",
                "value": f"{ppda}",
                "detail": f"Skor tekanan {ppda_score}/100 — makin rendah PPDA makin agresif press.",
                "tone": "emerald",
            },
        ],
        "upcoming": upcoming,
    }


LEAGUE_NAMES = {
    "EPL": "English Premier League",
    "La_liga": "La Liga",
    "Serie_A": "Serie A",
    "Bundesliga": "Bundesliga",
}
