import pandas as pd
import numpy as np
import time
from team_analytics import get_team_power_index, get_home_away_bias
from data_paths import HISTORICAL_MATCHES, UPCOMING_FIXTURES

SUPPORTED_LEAGUES = {
    "1": ("English Premier League", "EPL"),
    "2": ("La Liga (Spanyol)", "La_liga"),
    "3": ("Serie A (Italia)", "Serie_A"),
    "4": ("Bundesliga (Jerman)", "Bundesliga")
}

def simulate_10k_matches_minute_by_minute(home_xg, away_xg, iterations=10000, verbose=True):
    np.random.seed(42)
    if verbose:
        print(f"\n🎮 Memulai Simulation Engine ({iterations:,} Uji Coba Pertandingan Menit 1-90)...")
    start_time = time.time()

    home_prob_per_min = home_xg / 90.0
    away_prob_per_min = away_xg / 90.0

    home_randoms = np.random.rand(iterations, 90)
    away_randoms = np.random.rand(iterations, 90)

    home_goals_per_min = (home_randoms < home_prob_per_min).astype(int)
    away_goals_per_min = (away_randoms < away_prob_per_min).astype(int)

    home_sim_goals = np.sum(home_goals_per_min, axis=1)
    away_sim_goals = np.sum(away_goals_per_min, axis=1)

    home_ht_goals = np.sum(home_goals_per_min[:, :45], axis=1)
    away_ht_goals = np.sum(away_goals_per_min[:, :45], axis=1)

    ht_over_0_5 = np.sum((home_ht_goals + away_ht_goals) > 0)
    prob_ht_goal = round((ht_over_0_5 / iterations) * 100, 1)

    if verbose:
        exec_time = round(time.time() - start_time, 2)
        print(f"⚡ Selesai! {iterations:,} Pertandingan disimulasikan dalam {exec_time} detik.")

    return home_sim_goals, away_sim_goals, prob_ht_goal

def calculate_smart_projected_score(home_sim_goals, away_sim_goals, prob_home, prob_away, home_xg, away_xg):
    base_home = int(np.round(np.mean(home_sim_goals)))
    base_away = int(np.round(np.mean(away_sim_goals)))
    
    margin_prob = abs(prob_home - prob_away)
    xg_diff = abs(home_xg - away_xg)

    if margin_prob >= 35.0 or xg_diff >= 1.0:
        if prob_home > prob_away:
            base_home = max(int(np.ceil(home_xg)), base_away + 2)
            if away_xg < 1.0:
                base_away = 0
        else:
            base_away = max(int(np.ceil(away_xg)), base_home + 2)
            if home_xg < 1.0:
                base_home = 0
                
    elif margin_prob >= 10.0:
        if prob_home > prob_away and base_home <= base_away:
            base_home = base_away + 1
        elif prob_away > prob_home and base_away <= base_home:
            base_away = base_home + 1
            
    else:
        if abs(base_home - base_away) > 1:
            avg_g = int(np.round((base_home + base_away) / 2))
            base_home, base_away = avg_g, avg_g

    scores = list(zip(home_sim_goals, away_sim_goals))
    target_count = scores.count((base_home, base_away))
    confidence_pct = round((target_count / len(home_sim_goals)) * 100, 1)

    return base_home, base_away, confidence_pct

def execute_prediction():
    try:
        fixtures_df = pd.read_csv(UPCOMING_FIXTURES)
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        print("❌ Error: File 'upcoming_fixtures.csv' / 'historical_matches.csv' belum ada!")
        return False

    # LANGKAH 1: PILIH LIGA
    print("\n" + "="*65)
    print("                 🌍 PILIH LIGA SEPAK BOLA                 ")
    print("="*65)
    for key, (name, _) in SUPPORTED_LEAGUES.items():
        print(f" [{key}] {name}")
    print("="*65)

    league_choice = input("Pilih nomor liga (1-4) atau 'q' untuk keluar: ").strip()
    if league_choice.lower() == 'q':
        return False

    if league_choice not in SUPPORTED_LEAGUES:
        print("⚠️ Pilihan liga tidak valid!")
        return True

    league_name, league_code = SUPPORTED_LEAGUES[league_choice]

    # Filter Jadwal Berdasarkan Liga
    league_fixtures = fixtures_df[fixtures_df['league'] == league_code].reset_index(drop=True)
    if league_fixtures.empty:
        print(f"⚠️ Tidak ada data jadwal untuk {league_name}.")
        return True

    # Ambil Daftar Klub Unik dari Liga Tersebut
    teams = sorted(list(set(league_fixtures['home_team'].unique()).union(set(league_fixtures['away_team'].unique()))))

    # LANGKAH 2: PILIH KLUB
    print("\n" + "="*65)
    print(f"            🏆 PILIH TIM ({league_name.upper()})            ")
    print("="*65)
    for i in range(0, len(teams), 2):
        t1 = f"[{i+1}] {teams[i]}"
        t2 = f"[{i+2}] {teams[i+1]}" if i+1 < len(teams) else ""
        print(f" {t1:<30} {t2:<30}")
    print("="*65)

    team_choice = input(f"Pilih nomor tim (1-{len(teams)}): ").strip()
    if not team_choice.isdigit() or not (1 <= int(team_choice) <= len(teams)):
        print("⚠️ Pilihan tim tidak valid!")
        return True

    selected_team = teams[int(team_choice) - 1]

    # LANGKAH 3: PILIH PERTANDINGAN
    matched_fixtures = league_fixtures[
        (league_fixtures['home_team'] == selected_team) |
        (league_fixtures['away_team'] == selected_team)
    ].reset_index(drop=True)

    print(f"\n📋 Daftar Pertandingan Mendatang untuk '{selected_team.upper()}':")
    print("-" * 65)
    for idx, row in matched_fixtures.iterrows():
        print(f" [{idx + 1}] {row['home_team']:<18} vs  {row['away_team']:<18} ({row['date']})")
    print("-" * 65)

    match_choice = input(f"\nPilih nomor pertandingan (1-{len(matched_fixtures)}): ").strip()
    if not match_choice.isdigit() or not (1 <= int(match_choice) <= len(matched_fixtures)):
        print("⚠️ Pilihan pertandingan tidak valid!")
        return True

    selected_match = matched_fixtures.iloc[int(match_choice) - 1]

    home_team = selected_match['home_team']
    away_team = selected_match['away_team']
    match_date = selected_match['date']

    # Analisis Performa
    home_stats = get_team_power_index(home_team, matches_df, last_n=20)
    away_stats = get_team_power_index(away_team, matches_df, last_n=20)

    home_bias = get_home_away_bias(home_team, is_home=True, matches_df=matches_df)
    away_bias = get_home_away_bias(away_team, is_home=False, matches_df=matches_df)

    home_xg = home_stats['avg_xg'] * home_bias
    away_xg = away_stats['avg_xg'] * away_bias

    if home_stats['avg_ga'] < 1.0: away_xg *= 0.80
    if away_stats['avg_ga'] < 1.0: home_xg *= 0.80

    final_home_xg = round(max(0.3, home_xg), 2)
    final_away_xg = round(max(0.3, away_xg), 2)

    # Simulasi 10.000 Match
    home_sim_goals, away_sim_goals, prob_ht_goal = simulate_10k_matches_minute_by_minute(
        final_home_xg, final_away_xg, iterations=10000
    )

    home_wins = np.sum(home_sim_goals > away_sim_goals)
    draws = np.sum(home_sim_goals == away_sim_goals)
    away_wins = np.sum(home_sim_goals < away_sim_goals)

    prob_home = round((home_wins / 10000) * 100, 1)
    prob_draw = round((draws / 10000) * 100, 1)
    prob_away = round((away_wins / 10000) * 100, 1)

    smart_home_score, smart_away_score, confidence = calculate_smart_projected_score(
        home_sim_goals, away_sim_goals, prob_home, prob_away, final_home_xg, final_away_xg
    )

    print("\n" + "="*65)
    print(f"   📊 HASIL ANALISIS ENGINE ANALYTICA [{league_name.upper()}]   ")
    print("="*65)
    print(f"PERTANDINGAN          : {home_team.upper()} vs {away_team.upper()}")
    print(f"JADWAL LAGA           : {match_date}")
    print(f"PROYEKSI SKOR UTAMA   : {smart_home_score} - {smart_away_score} (Kepercayaan: {confidence}%)")
    print("-" * 65)
    print(f"PROBABILITAS HASIL (10.000 UJI COBA MENIT 1-90):")
    print(f" • {home_team:<18} : {prob_home}%")
    print(f" • Seri                 : {prob_draw}%")
    print(f" • {away_team:<18} : {prob_away}%")
    print("-" * 65)
    print(f"STATISTIK SIMULASI PERTANDINGAN:")
    print(f" • Peluang Ada Gol di Babak Pertama : {prob_ht_goal}%")
    print(f" • Proyeksi xG {home_team:<12}       : {final_home_xg} Goals")
    print(f" • Proyeksi xG {away_team:<12}       : {final_away_xg} Goals")
    print("="*65 + "\n")

    return True

if __name__ == "__main__":
    while True:
        continue_running = execute_prediction()
        if not continue_running:
            print("\n👋 Terima kasih telah menggunakan Analytica Soccer Engine!")
            break
        
        again = input("Cek prediksi pertandingan lain? (y/n): ").strip().lower()
        if again != 'y':
            print("\n👋 Terima kasih telah menggunakan Analytica Soccer Engine!")
            break