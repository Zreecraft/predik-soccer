import pandas as pd
import numpy as np
from team_analytics import get_team_power_index, get_home_away_bias
from data_paths import HISTORICAL_MATCHES, UPCOMING_FIXTURES

SUPPORTED_LEAGUES = {
    "1": ("English Premier League", "EPL"),
    "2": ("La Liga (Spanyol)", "La_liga"),
    "3": ("Serie A (Italia)", "Serie_A"),
    "4": ("Bundesliga (Jerman)", "Bundesliga")
}

def simulate_match(home_xg, away_xg):
    np.random.seed(42)
    h_sim = np.random.poisson(home_xg, 1000)
    a_sim = np.random.poisson(away_xg, 1000)
    return h_sim, a_sim

def calculate_score(h_sim, a_sim, h_xg, a_xg):
    prob_h = (np.sum(h_sim > a_sim) / 1000) * 100
    prob_a = (np.sum(a_sim > h_sim) / 1000) * 100
    
    base_h = int(np.round(np.mean(h_sim)))
    base_a = int(np.round(np.mean(a_sim)))
    
    margin = abs(prob_h - prob_a)
    if margin >= 35.0 or abs(h_xg - a_xg) >= 1.0:
        if prob_h > prob_a:
            base_h = max(int(np.ceil(h_xg)), base_a + 2)
            if a_xg < 1.0: base_a = 0
        else:
            base_a = max(int(np.ceil(a_xg)), base_h + 2)
            if h_xg < 1.0: base_h = 0
    elif margin >= 10.0:
        if prob_h > prob_a and base_h <= base_a: base_h = base_a + 1
        elif prob_a > prob_h and base_a <= base_h: base_a = base_h + 1
        
    return base_h, base_a

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

        h_stats = get_team_power_index(h_team, historical_df, last_n=20)
        a_stats = get_team_power_index(a_team, historical_df, last_n=20)

        h_bias = get_home_away_bias(h_team, is_home=True, matches_df=historical_df)
        a_bias = get_home_away_bias(a_team, is_home=False, matches_df=historical_df)

        h_xg = round(max(0.3, h_stats['avg_xg'] * h_bias), 2)
        a_xg = round(max(0.3, a_stats['avg_xg'] * a_bias), 2)

        h_sim, a_sim = simulate_match(h_xg, a_xg)
        p_h_goals, p_a_goals = calculate_score(h_sim, a_sim, h_xg, a_xg)

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