"""Metrik tim: power index, bias home/away, dan form N laga terakhir."""
import numpy as np
import pandas as pd

# Baseline rata-rata xG/gol per tim per laga di liga-liga besar
LEAGUE_AVG_XG = 1.40
# Rentang xG tim yang masuk akal untuk 1 laga (di luar ini di-clip)
MIN_TEAM_XG, MAX_TEAM_XG = 0.55, 2.60
MIN_TEAM_GA, MAX_TEAM_GA = 0.35, 3.00


def clamp_match_xg(xg, low=0.3, high=3.5):
    """Menormalkan xG per laga ke rentang wajar (gol per pertandingan)."""
    return round(float(np.clip(xg, low, high)), 2)


def _team_matches(team_name: str, matches_df: pd.DataFrame) -> pd.DataFrame:
    """Semua laga yang melibatkan `team_name`, terbaru di urutan atas."""
    mask = (
        matches_df["home_team"].str.contains(team_name, case=False, na=False)
        | matches_df["away_team"].str.contains(team_name, case=False, na=False)
    )
    return matches_df[mask].sort_values(by="datetime", ascending=False)


def _is_home(team_name: str, row) -> bool:
    return team_name.lower() in str(row["home_team"]).lower()


def get_team_power_index(team_name, matches_df, last_n=20):
    """Menghitung Rating Kekuatan Tim berdasarkan N Pertandingan Terakhir."""
    team_matches = _team_matches(team_name, matches_df)

    if team_matches.empty:
        return {"avg_xg": 1.45, "avg_ga": 1.20, "win_rate": 45.0, "power_score": 50.0}

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

    # Regresi ke rata-rata liga: sampel kecil (4-7 laga) tidak boleh meledak
    # jadi xG ekstrem (mis. 5+). Makin sedikit laga, makin dekat ke baseline.
    reliability = total_games / (total_games + 8.0)
    avg_xg = LEAGUE_AVG_XG * (1 - reliability) + raw_avg_xg * reliability
    avg_xg = float(np.clip(avg_xg, MIN_TEAM_XG, MAX_TEAM_XG))
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
        matches_df[side_col].str.contains(team_name, case=False, na=False)
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
        form.append({
            "result": "W" if gf > ga else ("D" if gf == ga else "L"),
            "score": f"{gf}-{ga}",
            "opponent": row["away_team"] if is_home else row["home_team"],
            "is_home": is_home,
            "date": str(row["datetime"]),
        })
    return form
