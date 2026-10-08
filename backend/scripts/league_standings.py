"""CLI klasemen akhir liga (interaktif): hasil asli + proyeksi sisa laga.

Jalankan dari folder backend/:  python scripts/league_standings.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

# Konsol Windows (cp1252) tidak bisa encode emoji → paksa UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

from data_paths import HISTORICAL_MATCHES, UPCOMING_FIXTURES
from club_data import ga_prior_from_rating, get_club_strength, xg_prior_from_rating
from run_prediction import calculate_smart_projected_score, simulate_10k_matches_minute_by_minute
from team_analytics import clamp_match_xg, get_home_away_bias, get_team_power_index

SUPPORTED_LEAGUES = {
    "1": ("English Premier League (inggris)"
    , "EPL"),
    "2": ("La Liga (Spanyol)", "La_liga"),
    "3": ("Serie A (Italia)", "Serie_A"),
    "4": ("Bundesliga (Jerman)", "Bundesliga")
}

def run_standings_simulation():
    try:
        fixtures_df = pd.read_csv(UPCOMING_FIXTURES)
        historical_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        print("❌ Error: File 'upcoming_fixtures.csv' / 'historical_matches.csv' belum ada!")
        return False

    print("\n" + "="*65)
    print("          🏆 SIMULATOR KLASEMEN AKHIR & JUARA LIGA          ")
    print("="*65)
    for key, (name, _) in SUPPORTED_LEAGUES.items():
        print(f" [{key}] {name}")
    print("="*65)

    choice = input("Pilih nomor liga (1-4) atau 'q' untuk keluar: ").strip()
    if choice.lower() == 'q': return False
    if choice not in SUPPORTED_LEAGUES: return True

    league_name, league_code = SUPPORTED_LEAGUES[choice]

    # Filter Fixtures & Historical berdasarkan Liga
    league_fixtures = fixtures_df[fixtures_df['league'] == league_code].copy()
    league_history = historical_df[historical_df['league'] == league_code].copy() if 'league' in historical_df.columns else historical_df.copy()

    # Ambil seluruh tim unik di liga tersebut
    teams = sorted(list(set(league_fixtures['home_team'].unique()).union(set(league_fixtures['away_team'].unique()))))
    
    # Inisialisasi statistik untuk 38 pertandingan
    standings = {team: {'P': 0, 'PTS': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'GD': 0} for team in teams}
    all_season_matches = []

    # -------------------------------------------------------------
    # LANGKAH 1: OLAH HASIL PERTANDINGAN NYATA YANG SUDAH TERJADI
    # -------------------------------------------------------------
    for _, row in league_history.iterrows():
        h_team, a_team = row['home_team'], row['away_team']
        h_goals, a_goals = int(row['home_goals']), int(row['away_goals'])
        
        if h_team in standings and a_team in standings:
            standings[h_team]['P'] += 1
            standings[a_team]['P'] += 1
            standings[h_team]['GF'] += h_goals
            standings[h_team]['GA'] += a_goals
            standings[a_team]['GF'] += a_goals
            standings[a_team]['GA'] += h_goals

            if h_goals > a_goals:
                standings[h_team]['PTS'] += 3
                standings[h_team]['W'] += 1
                standings[a_team]['L'] += 1
            elif a_goals > h_goals:
                standings[a_team]['PTS'] += 3
                standings[a_team]['W'] += 1
                standings[h_team]['L'] += 1
            else:
                standings[h_team]['PTS'] += 1
                standings[a_team]['PTS'] += 1
                standings[h_team]['D'] += 1
                standings[a_team]['D'] += 1

            all_season_matches.append({
                'date': row['datetime'],
                'home_team': h_team,
                'away_team': a_team,
                'score': f"{h_goals} - {a_goals}",
                'status': 'SELESAI (HASIL ASLI)'
            })

    # -------------------------------------------------------------
    # LANGKAH 2: SIMULASIKAN SISA PERTANDINGAN MENDATANG
    # -------------------------------------------------------------
    print(f"\n🔄 Menghitung simulasi sisa pertandingan {league_name}...")

    for _, row in league_fixtures.iterrows():
        h_team, a_team, m_date = row['home_team'], row['away_team'], row['date']

        h_str = get_club_strength(h_team)
        a_str = get_club_strength(a_team)
        strength_gap = round(h_str["overall"] - a_str["overall"], 1)

        h_stats = get_team_power_index(
            h_team, historical_df, last_n=20,
            prior_xg=xg_prior_from_rating(h_str["overall"]),
            prior_ga=ga_prior_from_rating(h_str["overall"]),
        )
        a_stats = get_team_power_index(
            a_team, historical_df, last_n=20,
            prior_xg=xg_prior_from_rating(a_str["overall"]),
            prior_ga=ga_prior_from_rating(a_str["overall"]),
        )

        h_bias = get_home_away_bias(h_team, is_home=True, matches_df=historical_df)
        a_bias = get_home_away_bias(a_team, is_home=False, matches_df=historical_df)

        gap_mult_h = 1.0 + (h_str["overall"] - a_str["overall"]) * 0.004
        gap_mult_a = 1.0 + (a_str["overall"] - h_str["overall"]) * 0.004
        h_xg = clamp_match_xg(h_stats['avg_xg'] * h_bias * gap_mult_h)
        a_xg = clamp_match_xg(a_stats['avg_xg'] * a_bias * gap_mult_a)

        h_sim, a_sim, _ = simulate_10k_matches_minute_by_minute(h_xg, a_xg, iterations=4000, verbose=False)
        prob_h = (np.sum(h_sim > a_sim) / len(h_sim)) * 100
        prob_a = (np.sum(a_sim > h_sim) / len(a_sim)) * 100
        p_h_goals, p_a_goals, _ = calculate_smart_projected_score(
            h_sim, a_sim, prob_h, prob_a, h_xg, a_xg, strength_gap=strength_gap
        )

        standings[h_team]['P'] += 1
        standings[a_team]['P'] += 1
        standings[h_team]['GF'] += p_h_goals
        standings[h_team]['GA'] += p_a_goals
        standings[a_team]['GF'] += p_a_goals
        standings[a_team]['GA'] += p_h_goals

        if p_h_goals > p_a_goals:
            standings[h_team]['PTS'] += 3
            standings[h_team]['W'] += 1
            standings[a_team]['L'] += 1
        elif p_a_goals > p_h_goals:
            standings[a_team]['PTS'] += 3
            standings[a_team]['W'] += 1
            standings[h_team]['L'] += 1
        else:
            standings[h_team]['PTS'] += 1
            standings[a_team]['PTS'] += 1
            standings[h_team]['D'] += 1
            standings[a_team]['D'] += 1

        all_season_matches.append({
            'date': m_date,
            'home_team': h_team,
            'away_team': a_team,
            'score': f"{p_h_goals} - {p_a_goals}",
            'status': 'PROYEKSI SIMULASI'
        })

    for t in standings:
        standings[t]['GD'] = standings[t]['GF'] - standings[t]['GA']

    df_standings = pd.DataFrame.from_dict(standings, orient='index').reset_index()
    df_standings.rename(columns={'index': 'Team'}, inplace=True)
    df_standings = df_standings.sort_values(by=['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)

    # TAMPILKAN TABEL KLASEMEN 38 LAGA UTUH
    print("\n" + "="*75)
    print(f"      🏆 PREDIKSI KLASEMEN AKHIR (38 LAGA UTUH) [{league_name.upper()}]      ")
    print("="*75)
    print(f" {'POS':<4} {'TIM':<22} {'P':<3} {'PTS':<5} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD':<5}")
    print("-" * 75)
    for idx, r in df_standings.iterrows():
        pos = idx + 1
        champion_tag = " 👑 (JUARA)" if pos == 1 else ""
        print(f" {pos:<4} {r['Team']:<22} {r['P']:<3} {r['PTS']:<5} {r['W']:<4} {r['D']:<4} {r['L']:<4} {r['GF']:<4} {r['GA']:<4} {r['GD']:<5}{champion_tag}")
    print("="*75 + "\n")

    # OPTIONAL: CEK SELURUH LAGA KLUB (HISTORI + PROYEKSI)
    df_matches = pd.DataFrame(all_season_matches)
    
    while True:
        view_club = input("Apakah ingin melihat seluruh (38) hasil & proyeksi skor klub? (y/n): ").strip().lower()
        if view_club != 'y': break

        ranked_teams = list(df_standings['Team'])
        print("\n" + "="*65)
        print(f"            🏆 PILIH TIM ({league_name.upper()})            ")
        print("="*65)
        for i in range(0, len(ranked_teams), 2):
            t1 = f"[{i+1}] {ranked_teams[i]}"
            t2 = f"[{i+2}] {ranked_teams[i+1]}" if i+1 < len(ranked_teams) else ""
            print(f" {t1:<30} {t2:<30}")
        print("="*65)

        team_choice = input(f"Pilih nomor tim (1-{len(ranked_teams)}): ").strip()
        if team_choice.isdigit() and (1 <= int(team_choice) <= len(ranked_teams)):
            selected_team = ranked_teams[int(team_choice) - 1]

            club_matches = df_matches[
                (df_matches['home_team'] == selected_team) |
                (df_matches['away_team'] == selected_team)
            ].sort_values(by='date').reset_index(drop=True)

            print(f"\n📋 RIWAYAT & PROYEKSI (TOTAL {len(club_matches)} LAGA) UNTUK '{selected_team.upper()}':")
            print("="*80)
            for idx, r in club_matches.iterrows():
                print(f" [{idx + 1:<2}] {r['date']} | {r['home_team']:<18} {r['score']:^7} {r['away_team']:<18} | {r['status']}")
            print("="*80 + "\n")
        else:
            print("⚠️ Nomor pilihan tim tidak valid.")

    return True

if __name__ == "__main__":
    while True:
        if not run_standings_simulation(): break
        if input("Cek klasemen liga lain? (y/n): ").strip().lower() != 'y': break