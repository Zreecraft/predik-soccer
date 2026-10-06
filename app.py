import json
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

# Import modul internal backend
from team_analytics import get_team_power_index, get_home_away_bias
from run_prediction import simulate_10k_matches_minute_by_minute, calculate_smart_projected_score
from ucl_simulator import simulate_match_xg, simulate_knockout_match, UCL_TEAMS

app = FastAPI(title="Analytica Soccer API", version="1.0.0")

# Mencegah error CORS saat dipanggil dari Frontend (React/Next.js/Vue/Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# HELPER FUNCTIONS (JSON ASSETS LOADERS)
# ==========================================

def get_team_logo(team_name: str) -> str:
    """Helper untuk mengambil URL logo klub dari team_logos.json"""
    try:
        with open("team_logos.json", "r", encoding="utf-8") as f:
            logos = json.load(f)
            return logos.get(team_name, {}).get("logo_url", "https://via.placeholder.com/150?text=No+Logo")
    except Exception:
        return "https://via.placeholder.com/150?text=No+Logo"


def get_key_player(team_name: str) -> dict:
    """Helper untuk memuat data pemain kunci dari key_players.json"""
    try:
        with open("key_players.json", "r", encoding="utf-8") as f:
            players = json.load(f)
            return players.get(team_name, {
                "player_name": "Key Player",
                "position": "N/A",
                "image": None
            })
    except Exception:
        return {
            "player_name": "Key Player",
            "position": "N/A",
            "image": None
        }


# ==========================================
# REST API ENDPOINTS
# ==========================================

# 1. Endpoint: List Liga
@app.get("/api/leagues")
def get_leagues():
    return [
        {"id": "EPL", "name": "English Premier League", "country": "England"},
        {"id": "La_liga", "name": "La Liga", "country": "Spain"},
        {"id": "Serie_A", "name": "Serie A", "country": "Italy"},
        {"id": "Bundesliga", "name": "Bundesliga", "country": "Germany"}
    ]


# 2. Endpoint: Jadwal Mendatang Berdasarkan Liga
@app.get("/api/fixtures/{league_code}")
def get_fixtures(league_code: str):
    try:
        df = pd.read_csv("upcoming_fixtures.csv")
        filtered = df[df['league'] == league_code].to_dict(orient="records")
        
        for fix in filtered:
            fix["home_logo"] = get_team_logo(fix["home_team"])
            fix["away_logo"] = get_team_logo(fix["away_team"])
            fix["home_star_player"] = get_key_player(fix["home_team"])
            fix["away_star_player"] = get_key_player(fix["away_team"])
            
        return {"league": league_code, "total": len(filtered), "fixtures": filtered}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File upcoming_fixtures.csv belum ditemukan.")


# 3. Endpoint Utama: Prediksi Match Tunggal (Lengkap dengan Logo & Star Player)
@app.get("/api/predict")
def predict_match(home_team: str, away_team: str):
    try:
        matches_df = pd.read_csv("historical_matches.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    # Hitung statistik daya serang & home/away bias
    home_stats = get_team_power_index(home_team, matches_df, last_n=20)
    away_stats = get_team_power_index(away_team, matches_df, last_n=20)

    home_bias = get_home_away_bias(home_team, is_home=True, matches_df=matches_df)
    away_bias = get_home_away_bias(away_team, is_home=False, matches_df=matches_df)

    final_home_xg = round(max(0.3, home_stats['avg_xg'] * home_bias), 2)
    final_away_xg = round(max(0.3, away_stats['avg_xg'] * away_bias), 2)

    # Eksekusi Simulasi Monte Carlo 10.000 Iterasi Minute-by-Minute
    home_sim, away_sim, prob_ht = simulate_10k_matches_minute_by_minute(final_home_xg, final_away_xg, iterations=10000)

    prob_home = round((np.sum(home_sim > away_sim) / 10000) * 100, 1)
    prob_draw = round((np.sum(home_sim == away_sim) / 10000) * 100, 1)
    prob_away = round((np.sum(away_sim > home_sim) / 10000) * 100, 1)

    smart_h, smart_a, confidence = calculate_smart_projected_score(
        home_sim, away_sim, prob_home, prob_away, final_home_xg, final_away_xg
    )

    return {
        "match": f"{home_team} vs {away_team}",
        "home_team": {
            "name": home_team,
            "logo": get_team_logo(home_team),
            "star_player": get_key_player(home_team)
        },
        "away_team": {
            "name": away_team,
            "logo": get_team_logo(away_team),
            "star_player": get_key_player(away_team)
        },
        "projection": {
            "score": f"{smart_h} - {smart_a}",
            "home_score": smart_h,
            "away_score": smart_a,
            "confidence_pct": confidence
        },
        "probabilities": {
            "home_win": prob_home,
            "draw": prob_draw,
            "away_win": prob_away
        },
        "analytics": {
            "home_xg": final_home_xg,
            "away_xg": final_away_xg,
            "first_half_goal_probability": prob_ht
        }
    }


# 4. Endpoint: Prediksi Klasemen Liga Domestik
@app.get("/api/standings/{league_code}")
def get_league_standings(league_code: str):
    try:
        matches_df = pd.read_csv("historical_matches.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    league_matches = matches_df[matches_df['league'] == league_code]
    if league_matches.empty:
        raise HTTPException(status_code=404, detail=f"Tidak ada data untuk liga '{league_code}'.")

    teams = set(league_matches['home_team']).union(set(league_matches['away_team']))
    standings = {t: {'P': 0, 'PTS': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'GD': 0} for t in teams}

    for _, row in league_matches.iterrows():
        h, a = row['home_team'], row['away_team']
        hg, ag = int(row['home_score']), int(row['away_score'])

        standings[h]['P'] += 1
        standings[a]['P'] += 1
        standings[h]['GF'] += hg
        standings[h]['GA'] += ag
        standings[a]['GF'] += ag
        standings[a]['GA'] += hg

        if hg > ag:
            standings[h]['PTS'] += 3
            standings[h]['W'] += 1
            standings[a]['L'] += 1
        elif ag > hg:
            standings[a]['PTS'] += 3
            standings[a]['W'] += 1
            standings[h]['L'] += 1
        else:
            standings[h]['PTS'] += 1
            standings[a]['PTS'] += 1
            standings[h]['D'] += 1
            standings[a]['D'] += 1

    for t in standings:
        standings[t]['GD'] = standings[t]['GF'] - standings[t]['GA']

    df_standings = pd.DataFrame.from_dict(standings, orient='index').reset_index()
    df_standings.rename(columns={'index': 'team'}, inplace=True)
    df_standings = df_standings.sort_values(by=['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)

    result = []
    for idx, row in df_standings.iterrows():
        item = row.to_dict()
        item['position'] = idx + 1
        item['logo'] = get_team_logo(row['team'])
        item['star_player'] = get_key_player(row['team'])
        result.append(item)

    return {"league": league_code, "standings": result}


# 5. Endpoint: Simulasi Lengkap UCL
@app.get("/api/ucl/simulate")
def simulate_ucl():
    try:
        matches_df = pd.read_csv("historical_matches.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    # 1. League Phase (36 Tim)
    standings = {t: {'P': 0, 'PTS': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'GD': 0} for t in UCL_TEAMS}
    random.seed(42)
    fixtures = []
    for team in UCL_TEAMS:
        opponents = random.sample([t for t in UCL_TEAMS if t != team], 8)
        for opp in opponents[:4]:
            fixtures.append((team, opp))

    for h_team, a_team in fixtures:
        h_g, a_g = simulate_match_xg(h_team, a_team, matches_df)
        standings[h_team]['P'] += 1
        standings[a_team]['P'] += 1
        standings[h_team]['GF'] += h_g
        standings[h_team]['GA'] += a_g
        standings[a_team]['GF'] += a_g
        standings[a_team]['GA'] += h_g

        if h_g > a_g:
            standings[h_team]['PTS'] += 3
            standings[h_team]['W'] += 1
            standings[a_team]['L'] += 1
        elif a_g > h_g:
            standings[a_team]['PTS'] += 3
            standings[a_team]['W'] += 1
            standings[h_team]['L'] += 1
        else:
            standings[h_team]['PTS'] += 1
            standings[a_team]['PTS'] += 1
            standings[h_team]['D'] += 1
            standings[a_team]['D'] += 1

    for t in standings:
        standings[t]['GD'] = standings[t]['GF'] - standings[t]['GA']

    df_ucl = pd.DataFrame.from_dict(standings, orient='index').reset_index()
    df_ucl.rename(columns={'index': 'team'}, inplace=True)
    df_ucl = df_ucl.sort_values(by=['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)

    league_phase_result = []
    for idx, row in df_ucl.iterrows():
        pos = idx + 1
        status = "Direct 16" if pos <= 8 else ("Play-off" if pos <= 24 else "Eliminated")
        item = row.to_dict()
        item['position'] = pos
        item['status'] = status
        item['logo'] = get_team_logo(row['team'])
        item['star_player'] = get_key_player(row['team'])
        league_phase_result.append(item)

    # 2. Play-off Knockout Stage
    playoff_teams = list(df_ucl.iloc[8:24]['team'])
    round_16_qualified = list(df_ucl.iloc[0:8]['team'])
    
    playoff_results, playoff_winners = [], []
    for i in range(8):
        t1, t2 = playoff_teams[i], playoff_teams[15 - i]
        winner, score_str = simulate_knockout_match(t1, t2, matches_df)
        playoff_winners.append(winner)
        playoff_results.append({"match": score_str, "winner": winner})

    # 3. Babak 16 Besar
    round_16_teams = round_16_qualified + playoff_winners
    random.shuffle(round_16_teams)
    r16_results, qf_teams = [], []
    for i in range(0, 16, 2):
        winner, score_str = simulate_knockout_match(round_16_teams[i], round_16_teams[i+1], matches_df)
        qf_teams.append(winner)
        r16_results.append({"match": score_str, "winner": winner})

    # 4. Quarter-Finals
    qf_results, sf_teams = [], []
    for i in range(0, 8, 2):
        winner, score_str = simulate_knockout_match(qf_teams[i], qf_teams[i+1], matches_df)
        sf_teams.append(winner)
        qf_results.append({"match": score_str, "winner": winner})

    # 5. Semi-Finals
    sf_results, finalists = [], []
    for i in range(0, 4, 2):
        winner, score_str = simulate_knockout_match(sf_teams[i], sf_teams[i+1], matches_df)
        finalists.append(winner)
        sf_results.append({"match": score_str, "winner": winner})

    # 6. Grand Final
    f1, f2 = finalists[0], finalists[1]
    g1, g2 = simulate_match_xg(f1, f2, matches_df)
    champion = f1 if g1 >= g2 else f2
    final_score = f"{f1} {g1} - {g2} {f2}"

    return {
        "league_phase": league_phase_result,
        "knockout_stage": {
            "playoffs": playoff_results,
            "round_of_16": r16_results,
            "quarter_finals": qf_results,
            "semi_finals": sf_results,
            "final": {
                "teams": f"{f1} vs {f2}",
                "result": final_score,
                "champion": champion,
                "champion_logo": get_team_logo(champion),
                "champion_star_player": get_key_player(champion)
            }
        }
    }


# Runner untuk eksekusi server langsung
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)