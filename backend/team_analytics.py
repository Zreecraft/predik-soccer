"""Metrik tim: power index, bias home/away, dan form N laga terakhir."""
import numpy as np
import pandas as pd

from team_aliases import alias_variants, name_pattern

# Baseline rata-rata xG/gol per tim per laga di liga-liga besar
LEAGUE_AVG_XG = 1.40
# Rentang xG tim yang masuk akal untuk 1 laga (di luar ini di-clip)
MIN_TEAM_XG, MAX_TEAM_XG = 0.55, 2.60
MIN_TEAM_GA, MAX_TEAM_GA = 0.35, 3.00


def clamp_match_xg(xg, low=0.3, high=3.5):
    """Menormalkan xG per laga ke rentang wajar (gol per pertandingan)."""
    return round(float(np.clip(xg, low, high)), 2)


def _team_matches(team_name: str, matches_df: pd.DataFrame) -> pd.DataFrame:
    """Semua laga yang melibatkan `team_name` (semua varian alias), terbaru di urutan atas."""
    pattern = name_pattern(team_name)
    mask = (
        matches_df["home_team"].str.contains(pattern, case=False, na=False, regex=True)
        | matches_df["away_team"].str.contains(pattern, case=False, na=False, regex=True)
    )
    return matches_df[mask].sort_values(by="datetime", ascending=False)


def _is_home(team_name: str, row) -> bool:
    home = str(row["home_team"]).lower()
    return any(v.lower() in home for v in alias_variants(team_name))


def _league_avg_xg(matches_df: pd.DataFrame, league: str | None = None) -> float:
    """Rata-rata xG per liga (fallback: seluruh df / konstanta baseline)."""
    try:
        sub = matches_df
        if league and "league" in matches_df.columns:
            sub = matches_df[matches_df["league"] == league]
            if sub.empty:
                sub = matches_df
        h = float(sub["home_xg"].mean())
        a = float(sub["away_xg"].mean())
        avg = (h + a) / 2.0
        if not np.isfinite(avg) or avg <= 0:
            return LEAGUE_AVG_XG
        return avg
    except Exception:
        return LEAGUE_AVG_XG


def get_team_power_index(team_name, matches_df, last_n=20, prior_xg=None, prior_ga=None, overall=None):
    """Menghitung Rating Kekuatan Tim berdasarkan N Pertandingan Terakhir.

    prior_xg/prior_ga: baseline ekspektasi dari rating kekuatan klub (club_data).
    overall: rating kekuatan klub — dipakai utk turunkan win_rate/power_score
    bila tim belum punya laga (bila None, di-inverse dari prior_xg).
    """
    team_matches = _team_matches(team_name, matches_df)

    if team_matches.empty:
        base_xg = float(prior_xg) if prior_xg else 1.45
        base_ga = float(prior_ga) if prior_ga else 1.20
        # Turunan dari overall (bukan lagi 45% / 50 statis)
        ov = overall
        if ov is None and prior_xg:
            ov = (float(prior_xg) - 1.40) / 0.025 + 70.0  # invers xg_prior_from_rating
        if ov is None:
            ov = 65.0
        win_rate = float(np.clip(45.0 + (ov - 65.0) * 0.9, 15.0, 80.0))
        power_score = (
            (win_rate * 0.40)
            + (min(base_xg / 2.5, 1.0) * 35)
            + (max(0, 1 - (base_ga / 2.0)) * 25)
        )
        return {
            "avg_xg": round(base_xg, 2),
            "avg_ga": round(base_ga, 2),
            "win_rate": round(win_rate, 1),
            "power_score": round(power_score, 1),
        }

    recent_matches = team_matches.head(last_n)
    total_games = len(recent_matches)

    wins, draws, losses = 0, 0, 0
    goals_scored, goals_conceded = 0, 0
    total_xg = 0.0

    for _, row in recent_matches.iterrows():
        is_home = _is_home(team_name, row)

        gf = row["home_goals"] if is_home else row["away_goals"]
        ga = row["away_goals"] if is_home else row["home_goals"]
        xg = row["home_xg"] if is_home else row["away_xg"]

        goals_scored += gf
        goals_conceded += ga
        total_xg += xg

        if gf > ga:
            wins += 1
        elif gf == ga:
            draws += 1
        else:
            losses += 1

    win_rate = (wins / total_games) * 100
    raw_avg_xg = total_xg / total_games
    avg_ga = goals_conceded / total_games

    # ==== Fase D: normalisasi xG lintas liga ====
    # form_ratio = xG tim / rata-rata xG liganya -> klub dominan di liga lemah
    # tidak otomatis dihargai lebih tinggi dari klub rata-rata di liga kuat.
    league = None
    if "league" in recent_matches.columns:
        modes = recent_matches["league"].mode()
        league = modes.iloc[0] if not modes.empty else None
    league_avg = _league_avg_xg(matches_df, league)
    form_ratio = raw_avg_xg / league_avg if league_avg else 1.0

    # reliability = n/(n+8); klub baru/promosi (<20 laga) lebih banyak ditarik ke prior
    n = float(total_games)
    reliability = n / (n + (12.0 if n < 20 else 8.0))

    baseline = float(prior_xg) if prior_xg else LEAGUE_AVG_XG
    avg_xg = baseline * float(np.clip(1.0 + (form_ratio - 1.0) * reliability, 0.80, 1.20))
    avg_xg = float(np.clip(avg_xg, MIN_TEAM_XG, MAX_TEAM_XG))
    if prior_ga:
        avg_ga = float(prior_ga) * (1 - reliability) + avg_ga * reliability
    avg_ga = float(np.clip(avg_ga, MIN_TEAM_GA, MAX_TEAM_GA))

    # Formula Power Rating (Bobot: Win Rate 40%, Offense 35%, Defense 25%)
    form_score = (win_rate * 0.40) + (min(avg_xg / 2.5, 1.0) * 35) + (max(0, 1 - (avg_ga / 2.0)) * 25)

    return {
        "games_analyzed": total_games,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "avg_xg": round(avg_xg, 2),
        "avg_ga": round(avg_ga, 2),
        "power_score": round(form_score, 1),
    }


def get_home_away_bias(team_name, is_home, matches_df):
    """Menghitung multiplier performa spesifik laga Home/Away."""
    side_col = "home_team" if is_home else "away_team"
    team_matches = matches_df[
        matches_df[side_col].str.contains(name_pattern(team_name), case=False, na=False, regex=True)
    ].sort_values(by="datetime", ascending=False).head(10)

    if team_matches.empty:
        return 1.10 if is_home else 0.90

    xg_col = "home_xg" if is_home else "away_xg"
    avg_xg = float(np.clip(team_matches[xg_col].mean(), 0.3, 3.5))
    multiplier = 1.0 + ((avg_xg - 1.35) * 0.12)
    return round(float(np.clip(multiplier, 0.85, 1.25)), 2)


def get_team_form(team: str, historical_df: pd.DataFrame, n: int = 5) -> list:
    """N laga terakhir sebuah tim: hasil, skor, lawan, dan status kandang."""
    team_matches = _team_matches(team, historical_df).head(n)
    form = []
    for _, row in team_matches.iterrows():
        is_home = _is_home(team, row)
        gf = int(row["home_goals"]) if is_home else int(row["away_goals"])
        ga = int(row["away_goals"]) if is_home else int(row["home_goals"])
        xg_for = float(row.get("home_xg", 0) or 0) if is_home else float(row.get("away_xg", 0) or 0)
        xg_against = float(row.get("away_xg", 0) or 0) if is_home else float(row.get("home_xg", 0) or 0)
        form.append({
            "result": "W" if gf > ga else ("D" if gf == ga else "L"),
            "score": f"{gf}-{ga}",
            "opponent": row["away_team"] if is_home else row["home_team"],
            "is_home": is_home,
            "date": str(row["datetime"]),
            "xg_for": round(xg_for, 2),
            "xg_against": round(xg_against, 2),
        })
    return form
