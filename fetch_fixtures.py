import asyncio
import aiohttp
import pandas as pd
from understat import Understat

LEAGUES = ["EPL", "La_liga", "Serie_A", "Bundesliga"]

async def fetch_all_upcoming_fixtures(season=2026):
    all_upcoming = []
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        for league in LEAGUES:
            print(f"🔄 Mengambil jadwal mendatang {league} Musim {season}...")
            try:
                fixtures = await understat.get_league_fixtures(league, season)
                for f in fixtures:
                    if not f.get('isResult', False):
                        all_upcoming.append({
                            'match_id': f['id'],
                            'league': league,
                            'date': f['datetime'],
                            'home_team': f['h']['title'],
                            'away_team': f['a']['title']
                        })
            except Exception as e:
                print(f"❌ Error jadwal {league}: {e}")
        
        df = pd.DataFrame(all_upcoming)
        df.to_csv("upcoming_fixtures.csv", index=False)
        print(f"✅ Total {len(df)} jadwal mendatang dari 4 liga disimpan ke 'upcoming_fixtures.csv'")

if __name__ == "__main__":
    asyncio.run(fetch_all_upcoming_fixtures(season=2026))