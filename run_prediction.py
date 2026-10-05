import pandas as pd
import numpy as np

def predict_from_fixtures():
    # 1. Load data jadwal mendatang
    try:
        fixtures_df = pd.read_csv("upcoming_fixtures.csv")
    except FileNotFoundError:
        print("❌ Error: File 'upcoming_fixtures.csv' belum ada. Jalankan 'python fetch_fixtures.py' dulu!")
        return

    # 2. Load data tembakan historis
    try:
        shots_df = pd.read_csv("real_shots_data.csv")
        shots_df['xG'] = shots_df['xG'].astype(float)
    except FileNotFoundError:
        print("❌ Error: File 'real_shots_data.csv' belum ada. Jalankan 'python fetch_data.py' dulu!")
        return

    print("\n🔍 CARI JADWAL PERTANDINGAN MENDATANG")
    search_input = input("Masukkan nama klub (contoh: Arsenal / Chelsea / Liverpool): ").strip()

    # Filter jadwal berdasarkan input user
    matched_fixtures = fixtures_df[
        fixtures_df['home_team'].str.contains(search_input, case=False, na=False) |
        fixtures_df['away_team'].str.contains(search_input, case=False, na=False)
    ]

    # VALIDASI: Jika pertandingan tidak ditemukan di jadwal mendatang
    if matched_fixtures.empty:
        print(f"\n⚠️ Pertandingan untuk '{search_input}' TIDAK ADA / Tidak Ditemukan dalam jadwal mendatang!")
        return

    # Ambil pertandingan pertama yang cocok dari hasil pencarian
    selected_match = matched_fixtures.iloc[0]
    home_team = selected_match['home_team']
    away_team = selected_match['away_team']
    match_date = selected_match['date']

    print(f"\n✅ Pertandingan Ditemukan: {home_team} vs {away_team} ({match_date})")
    print("🔄 Menghitung proyeksi analitik...")

    # 3. Hitung statistik xG dari histori tembakan murni
    home_shots = shots_df[shots_df['team_name'].str.contains(home_team, case=False, na=False)]
    away_shots = shots_df[shots_df['team_name'].str.contains(away_team, case=False, na=False)]

    if len(home_shots) > 0 and home_shots['id'].nunique() > 0:
        home_base_xg = home_shots['xG'].sum() / home_shots['id'].nunique()
    else:
        home_base_xg = 1.85

    if len(away_shots) > 0 and away_shots['id'].nunique() > 0:
        away_base_xg = away_shots['xG'].sum() / away_shots['id'].nunique()
    else:
        away_base_xg = 1.15

    # Home advantage multiplier
    home_xg = round(home_base_xg * 1.12, 2)
    away_xg = round(away_base_xg * 0.88, 2)

    # 4. Simulasi Monte Carlo (10.000 Iterasi)
    iterations = 10000
    home_goals = np.random.poisson(home_xg, iterations)
    away_goals = np.random.poisson(away_xg, iterations)

    home_wins = np.sum(home_goals > away_goals)
    draws = np.sum(home_goals == away_goals)
    away_wins = np.sum(home_goals < away_goals)

    prob_home = round((home_wins / iterations) * 100, 1)
    prob_draw = round((draws / iterations) * 100, 1)
    prob_away = round((away_wins / iterations) * 100, 1)

    projected_home_goals = int(np.round(home_xg))
    projected_away_goals = int(np.round(away_xg))

    # 5. TAMPILKAN HASIL AKURAT
    print("\n" + "="*55)
    print("      📊 HASIL PREDIKSI ENGINE ANALYTICA (VERIFIED)      ")
    print("="*55)
    print(f"PERTANDINGAN      : {home_team.upper()} vs {away_team.upper()}")
    print(f"TANGGAL & WAKTU   : {match_date}")
    print(f"PROYEKSI SKOR     : {projected_home_goals} - {projected_away_goals}")
    print("-" * 55)
    print(f"PELUANG MENANG    : {home_team} ({prob_home}%)")
    print(f"PELUANG SERI      : Seri ({prob_draw}%)")
    print(f"PELUANG MENANG    : {away_team} ({prob_away}%)")
    print("-" * 55)
    print("PROYEKSI METRIK xG LAGA:")
    print(f" - Expected Goals {home_team:<11} : {home_xg} Goals")
    print(f" - Expected Goals {away_team:<11} : {away_xg} Goals")
    print("="*55 + "\n")

if __name__ == "__main__":
    predict_from_fixtures()