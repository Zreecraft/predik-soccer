import asyncio
import aiohttp
import pandas as pd
from understat import Understat

async def fetch_upcoming_fixtures(league="EPL", season=2026):
    print(f"🔄 Mengambil jadwal pertandingan mendatang {league} Musim {season}...")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        # Ambil seluruh daftar jadwal/fixtures musim 2026
        fixtures = await understat.get_league_fixtures(league, season)
        
        upcoming_matches = []
        for f in fixtures:
            # Filter hanya pertandingan yang BELUM dimainkan (isResult == False)
            if not f['isResult']:
                upcoming_matches.append({
                    'match_id': f['id'],
                    'date': f['datetime'],
                    'home_team': f['h']['title'],
                    'away_team': f['a']['title']
                })
        
        df = pd.DataFrame(upcoming_matches)
        
        # Simpan ke CSV
        df.to_csv("upcoming_fixtures.csv", index=False)
        
        print("\n" + "="*50)
        print("    JADWAL PERTANDINGAN MENDATANG (MURNI TANPA PREDIKSI)    ")
        print("="*50)
        # Tampilkan 10 pertandingan mendatang pertama
        print(df.head(50).to_string(index=False))
        print("="*50)
        print(f"\n✅ Total {len(df)} laga mendatang disimpan ke 'upcoming_fixtures.csv'")

if __name__ == "__main__":
    asyncio.run(fetch_upcoming_fixtures(league="EPL", season=2026))