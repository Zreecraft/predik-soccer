import pandas as pd
import numpy as np

def get_team_power_index(team_name, matches_df, last_n=20):
    """Menghitung Rating Kekuatan Tim berdasarkan 20 Pertandingan Terakhir."""
    team_matches = matches_df[
        (matches_df['home_team'].str.contains(team_name, case=False, na=False)) |
        (matches_df['away_team'].str.contains(team_name, case=False, na=False))
    ].sort_values(by='datetime', ascending=False)
    
    if team_matches.empty:
        return {"avg_xg": 1.45, "avg_ga": 1.20, "win_rate": 45.0, "power_score": 50.0}

    recent_matches = team_matches.head(last_n)
    total_games = len(recent_matches)
    
    wins, draws, losses = 0, 0, 0
    goals_scored, goals_conceded = 0, 0
    total_xg = 0.0

    for _, row in recent_matches.iterrows():
        is_home = team_name.lower() in row['home_team'].lower()
        
        gf = row['home_goals'] if is_home else row['away_goals']
        ga = row['away_goals'] if is_home else row['home_goals']
        xg = row['home_xg'] if is_home else row['away_xg']
        
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
    avg_xg = total_xg / total_games
    avg_ga = goals_conceded / total_games
    
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
        "power_score": round(form_score, 1)
    }

def get_home_away_bias(team_name, is_home, matches_df):
    """Menghitung multiplier performa spesifik laga Home/Away."""
    team_matches = matches_df[
        (matches_df['home_team'].str.contains(team_name, case=False, na=False)) if is_home else
        (matches_df['away_team'].str.contains(team_name, case=False, na=False))
    ].head(10)
    
    if team_matches.empty:
        return 1.10 if is_home else 0.90
        
    total_xg = sum(row['home_xg'] if is_home else row['away_xg'] for _, row in team_matches.iterrows())
    avg_xg = total_xg / len(team_matches)
    multiplier = 1.0 + ((avg_xg - 1.3) * 0.15)
    return round(max(0.75, min(1.35, multiplier)), 2)