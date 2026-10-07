import requests
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/

from data_paths import TEAM_LOGOS

ALL_LEAGUE_CLUBS = {
    "EPL": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Chelsea", "Coventry", "Crystal Palace", "Everton", "Fulham",
        "Hull", "Ipswich", "Leeds", "Liverpool", "Manchester City",
        "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland", "Tottenham"
    ],
    "La_liga": [
        "Athletic Club", "Atletico Madrid", "Osasuna", "Celta Vigo", "Alaves",
        "Deportivo La Coruna", "Elche", "Barcelona", "Getafe", "Levante",
        "Malaga", "Racing Santander", "Rayo Vallecano", "Real Betis", "Real Madrid",
        "Real Sociedad", "Espanyol", "Sevilla", "Valencia", "Villarreal"
    ],
    "Serie_A": [
        "AC Milan", "Fiorentina", "Roma", "Atalanta", "Bologna",
        "Cagliari", "Como", "Frosinone", "Genoa", "Inter",
        "Juventus", "Parma", "Pisa", "Lazio", "Napoli",
        "Torino", "Udinese", "Cremonese", "Lecce", "Sassuolo"
    ],
    "Bundesliga": [
        "FC Koln", "Mainz 05", "Bayer Leverkusen", "Borussia Dortmund", "Borussia M'gladbach",
        "Eintracht Frankfurt", "Augsburg", "Bayern Munich", "Schalke 04", "Hamburger SV",
        "RB Leipzig", "Freiburg", "Paderborn", "Elversberg", "Hoffenheim",
        "Union Berlin", "Stuttgart", "Werder Bremen"
    ]
}

# Mapping Nama Tim Presisi untuk Query TheSportsDB API
SEARCH_MAPPING = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Chelsea": "Chelsea",
    "Coventry": "Coventry",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull": "Hull",
    "Ipswich": "Ipswich",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester City": "Manchester City",
    "Manchester United": "Manchester United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nottingham Forest",
    "Sunderland": "Sunderland",
    "Tottenham": "Tottenham",
    "Alaves": "Alaves",
    "Osasuna": "Osasuna",
    "Celta Vigo": "Celta Vigo",
    "Deportivo La Coruna": "Deportivo La Coruna",
    "Barcelona": "Barcelona",
    "Real Madrid": "Real Madrid",
    "Atletico Madrid": "Atletico Madrid",
    "Bayer Leverkusen": "Bayer Leverkusen",
    "Borussia Dortmund": "Borussia Dortmund",
    "Bayern Munich": "Bayern Munich",
    "Schalke 04": "Schalke 04",
    "Hamburger SV": "Hamburger SV",
    "RB Leipzig": "RB Leipzig",
    "Freiburg": "Freiburg",
    "Hoffenheim": "Hoffenheim",
    "Union Berlin": "Union Berlin",
    "Stuttgart": "Stuttgart",
    "Werder Bremen": "Werder Bremen"
}

def fetch_single_logo(team_name):
    query_name = SEARCH_MAPPING.get(team_name, team_name)
    url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={requests.utils.quote(query_name)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # Mekanisme Retry hingga 3x jika terkena Rate-Limit
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data and data.get('teams'):
                    return data['teams'][0].get('strBadge')
        except Exception:
            pass
        time.sleep(2.0)  # Istirahat 2 detik sebelum retry
    
    return None

def fetch_and_save_all_logos():
    output_filename = str(TEAM_LOGOS)
    
    # Muat data lama jika sudah ada agar tidak perlu download ulang yang sudah OK
    logos_database = {}
    try:
        with open(output_filename, "r", encoding="utf-8") as f:
            logos_database = json.load(f)
    except FileNotFoundError:
        logos_database = {}

    print("🔄 Memulai Eksekusi Scraping Logo (Mode Cerdas & Auto-Retry)...\n" + "="*70)

    total_processed = 0
    total_teams = sum(len(clubs) for clubs in ALL_LEAGUE_CLUBS.values())

    for league_code, clubs in ALL_LEAGUE_CLUBS.items():
        print(f"\n🏆 MENGAMBIL LOGO LIGA: [{league_code}] ({len(clubs)} Tim)")
        print("-" * 70)

        for team_name in clubs:
            total_processed += 1
            
            # Cek jika logo sudah pernah berhasil di-download sebelumnya
            existing_data = logos_database.get(team_name, {})
            existing_url = existing_data.get("logo_url", "")
            
            if existing_url and "placeholder" not in existing_url:
                print(f" [{total_processed}/{total_teams}] {team_name:<25} -> ⏩ SKIP (SUDAH ADA)")
                continue

            # Jika belum ada / masih fallback, lakukan fetching
            badge_url = fetch_single_logo(team_name)
            final_url = badge_url or "https://via.placeholder.com/150?text=No+Logo"

            logos_database[team_name] = {
                "league": league_code,
                "logo_url": final_url
            }

            status = "✅ OK" if badge_url else "⚠️️ FALLBACK"
            print(f" [{total_processed}/{total_teams}] {team_name:<25} -> {status}")

            # Simpan bertahap setiap dapat logo baru
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(logos_database, f, indent=4, ensure_ascii=False)

            time.sleep(1.2)  # Delay aman anti-block

    print("\n" + "="*70)
    print(f"🎉 SELESAI! Hasil akhir tersimpan di '{output_filename}'")
    print("="*70 + "\n")

if __name__ == "__main__":
    fetch_and_save_all_logos()