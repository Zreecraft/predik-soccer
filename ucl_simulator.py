import pandas as pd
import numpy as np
import random
from team_analytics import get_team_power_index, get_home_away_bias

# 36 Tim Peserta UCL
UCL_TEAMS = [
    "Real Madrid", "Manchester City", "Bayern Munich", "PSG", "Liverpool",
    "Inter", "Borussia Dortmund", "RB Leipzig", "Barcelona", "Bayer Leverkusen",
    "Atletico Madrid", "Atalanta", "Juventus", "Benfica", "Arsenal",
    "Club Brugge", "Shakhtar Donetsk", "AC Milan", "Feyenoord", "Sporting CP",
    "PSV", "Dinamo Zagreb", "RB Salzburg", "Lille", "Red Star Belgrade",
    "Young Boys", "Celtic", "Slovan Bratislava", "Monaco", "Sparta Prague",
    "Aston Villa", "Bologna", "Girona", "Stuttgart", "Sturm Graz", "Brest"
]

# European DNA / UCL Prestige Rating (Multiplier Mentalitas Liga Champions)
UCL_DNA_TIERS = {
    # Tier 1: Penguasa / Kolektor Trofi Eropa (Bonus +20% xG Efficiency)
    "Real Madrid": 1.20, "Bayern Munich": 1.18, "Liverpool": 1.15, "Barcelona": 1.15, "Manchester City": 1.15,
    # Tier 2: Langganan Finalis / Semifinalis (Bonus +10% xG Efficiency)
    "PSG": 1.10, "Inter": 1.10, "Borussia Dortmund": 1.10, "Atletico Madrid": 1.10, "Juventus": 1.10, "Arsenal": 1.08, "AC Milan": 1.08,
    # Tier 3: Tim Kuda Hitam / Regular Participant (Normal 1.0)
    "Bayer Leverkusen": 1.02, "RB Leipzig": 1.02, "Atalanta": 1.00, "Benfica": 1.00, "Sporting CP": 1.00, "PSV": 1.00,
    # Tier 4: Tim Non-Top 5 Liga / Debutan (Penalti Pengalaman European Competition)
    "Club Brugge": 0.95, "Shakhtar Donetsk": 0.95, "Celtic": 0.92, "Monaco": 0.95, "Aston Villa": 0.95,
    "Stuttgart": 0.92, "Girona": 0.90, "Bologna": 0.90, "Brest": 0.88, "Slovan Bratislava": 0.85
}

def calculate_weighted_ucl_xg(team_name, is_home, matches_df):
    """
    Menghitung xG Gabungan: Performa Domestik (60%) + UCL DNA/Prestige Multiplier (40%)
    """
    # 1. Performa Liga Domestik 20 Match Terakhir
    stats = get_team_power_index(team_name, matches_df, last_n=20)
    bias = get_home_away_bias(team_name, is_home=is_home, matches_df=matches_df)
    
    base_xg = stats['avg_xg'] * bias

    # 2. Ambil Multiplier DNA UCL (Default 1.0 jika tidak terdaftar)
    dna_multiplier = UCL_DNA_TIERS.get(team_name, 1.0)

    # 3. Formulasi xG Akhir Berbobot
    final_xg = (base_xg * 0.60) + (base_xg * dna_multiplier * 0.40)
    
    return round(max(0.4, final_xg), 2)

def simulate_match_xg(home_team, away_team, matches_df):
    """Simulasi 1 Pertandingan dengan xG Berbobot"""
    h_xg = calculate_weighted_ucl_xg(home_team, is_home=True, matches_df=matches_df)
    a_xg = calculate_weighted_ucl_xg(away_team, is_home=False, matches_df=matches_df)

    # Poisson Distribution berdasarkan Weighted xG
    np.random.seed(42 + random.randint(1, 1000))
    h_goals = np.random.poisson(h_xg)
    a_goals = np.random.poisson(a_xg)

    return h_goals, a_goals

def simulate_knockout_match(team1, team2, matches_df):
    """Simulasi 2 Leg (Kandang & Tandang) Babak Gugur"""
    g1_h, g1_a = simulate_match_xg(team1, team2, matches_df)  # Leg 1
    g2_h, g2_a = simulate_match_xg(team2, team1, matches_df)  # Leg 2

    agg1 = g1_h + g2_a
    agg2 = g1_a + g2_h

    if agg1 > agg2:
        winner = team1
    elif agg2 > agg1:
        winner = team2
    else:
        # Poin Penentu jika Agregat Imbang (Adu Penalti)
        winner = team1 if random.random() > 0.5 else team2

    return winner, f"{team1} {agg1} - {agg2} {team2}"

def run_ucl_simulation():
    try:
        matches_df = pd.read_csv("historical_matches.csv")
    except FileNotFoundError:
        print("❌ Error: File 'historical_matches.csv' belum ada!")
        return False

    print("\n" + "="*80)
    print("   🇪🇺 SIMULATOR UCL (COMBINED DOMESTIC FORM + EUROPEAN DNA MULTIPLIER)   ")
    print("="*80)

    # 1. KLASEMEN LEAGUE PHASE (36 TIM)
    standings = {t: {'P': 0, 'PTS': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'GD': 0} for t in UCL_TEAMS}
    
    random.seed(42)
    fixtures = []
    for team in UCL_TEAMS:
        opponents = random.sample([t for t in UCL_TEAMS if t != team], 8)
        for opp in opponents[:4]:
            fixtures.append((team, opp))

    print("🔄 Menghitung simulasi League Phase (144 Pertandingan)...")
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

    df = pd.DataFrame.from_dict(standings, orient='index').reset_index()
    df.rename(columns={'index': 'Team'}, inplace=True)
    df = df.sort_values(by=['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)

    # TAMPILKAN KLASEMEN LEAGUE PHASE
    print("\n" + "="*80)
    print("                  🏆 KLASEMEN AKHIR UCL LEAGUE PHASE (36 TIM)                  ")
    print("="*80)
    print(f" {'POS':<4} {'TIM':<22} {'P':<3} {'PTS':<5} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD':<5} {'STATUS'}")
    print("-" * 80)

    for idx, r in df.iterrows():
        pos = idx + 1
        if pos <= 8: status = "🟢 Lolos Babak 16 Besar"
        elif pos <= 24: status = "🟡 Lolos Play-off Knockout"
        else: status = "🔴 Tereliminasi"
            
        print(f" {pos:<4} {r['Team']:<22} {r['P']:<3} {r['PTS']:<5} {r['W']:<4} {r['D']:<4} {r['L']:<4} {r['GF']:<4} {r['GA']:<4} {r['GD']:<5} {status}")
    print("="*80)

    input("\nTekan Enter untuk melanjutkan ke Simulasi Babak Gugur...")

    # 2. BABAK PLAY-OFF KNOCKOUT
    print("\n" + "="*65)
    print("              🔥 BABAK PLAY-OFF KNOCKOUT (AGREGAT)              ")
    print("="*65)
    playoff_teams = list(df.iloc[8:24]['Team'])
    round_16_qualified = list(df.iloc[0:8]['Team'])
    
    playoff_winners = []
    for i in range(8):
        t1, t2 = playoff_teams[i], playoff_teams[15 - i]
        winner, score_str = simulate_knockout_match(t1, t2, matches_df)
        playoff_winners.append(winner)
        print(f" • Play-off #{i+1}: {score_str} ➡️ [{winner.upper()} LOLOS]")

    round_16_teams = round_16_qualified + playoff_winners

    # 3. BABAK 16 BESAR
    print("\n" + "="*65)
    print("                   ⚽ BABAK 16 BESAR (AGREGAT)                   ")
    print("="*65)
    qf_teams = []
    random.shuffle(round_16_teams)
    for i in range(0, 16, 2):
        winner, score_str = simulate_knockout_match(round_16_teams[i], round_16_teams[i+1], matches_df)
        qf_teams.append(winner)
        print(f" • Match #{i//2 + 1}: {score_str} ➡️ [{winner.upper()} LOLOS]")

    # 4. PEREMPAT FINAL
    print("\n" + "="*65)
    print("                ⚔️ PEREMPAT FINAL / QUARTER-FINALS                ")
    print("="*65)
    sf_teams = []
    for i in range(0, 8, 2):
        winner, score_str = simulate_knockout_match(qf_teams[i], qf_teams[i+1], matches_df)
        sf_teams.append(winner)
        print(f" • QF #{i//2 + 1}: {score_str} ➡️ [{winner.upper()} LOLOS]")

    # 5. SEMIFINAL
    print("\n" + "="*65)
    print("                      🔥 SEMIFINAL (AGREGAT)                      ")
    print("="*65)
    finalists = []
    for i in range(0, 4, 2):
        winner, score_str = simulate_knockout_match(sf_teams[i], sf_teams[i+1], matches_df)
        finalists.append(winner)
        print(f" • SF #{i//2 + 1}: {score_str} ➡️ [{winner.upper()} LOLOS KE FINAL]")

    # 6. GRAND FINAL
    print("\n" + "="*65)
    print("                 🏆 GRAND FINAL UEFA CHAMPIONS LEAGUE             ")
    print("="*65)
    f1, f2 = finalists[0], finalists[1]
    g1, g2 = simulate_match_xg(f1, f2, matches_df)
    
    if g1 == g2:
        winner = f1 if random.random() > 0.5 else f2
        score_final = f"{f1} {g1} - {g2} {f2} (AET/Pen)"
    else:
        winner = f1 if g1 > g2 else f2
        score_final = f"{f1} {g1} - {g2} {f2}"

    print(f" LAGA FINAL : {f1.upper()} vs {f2.upper()}")
    print(f" HASIL LAGA  : {score_final}")
    print("="*65)
    print(f" 👑 JUARA UEFA CHAMPIONS LEAGUE: {winner.upper()}")
    print("="*65 + "\n")

    return True

if __name__ == "__main__":
    while True:
        if not run_ucl_simulation(): break
        if input("Jalankan ulang simulasi UCL? (y/n): ").strip().lower() != 'y': break