import asyncio
import aiohttp
import pandas as pd
from understat import Understat

async def fetch_comprehensive_data(league="EPL", seasons=[2025, 2026]):
    all_shots = []
    all_matches = []
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        
        for season in seasons:
            print(f"🔄 Mengambil data {league} Musim {season}...")
            results = await understat.get_league_results(league, season)
            
            for match in results:
                all_matches.append({
                    'match_id': match['id'],
                    'season': season,
                    'datetime': match['datetime'],
                    'home_team': match['h']['title'],
                    'away_team': match['a']['title'],
                    'home_goals': int(match['goals']['h']),
                    'away_goals': int(match['goals']['a']),
                    'home_xg': float(match['xG']['h']),
                    'away_xg': float(match['xG']['a'])
                })
                
                # Ambil detail tembakan untuk 30 match terbaru
                if len(all_shots) < 1500:
                    shots = await understat.get_match_shots(match['id'])
                    for s in shots['h']:
                        s['team_name'] = match['h']['title']
                        s['opponent'] = match['a']['title']
                        s['is_home'] = 1
                        all_shots.append(s)
                    for s in shots['a']:
                        s['team_name'] = match['a']['title']
                        s['opponent'] = match['h']['title']
                        s['is_home'] = 0
                        all_shots.append(s)

        # Save Matches Data
        df_matches = pd.DataFrame(all_matches)
        df_matches.to_csv("historical_matches.csv", index=False)
        
        # Save Shots Data
        df_shots = pd.DataFrame(all_shots)
        cols = ['id', 'team_name', 'opponent', 'is_home', 'minute', 'player', 'X', 'Y', 'xG', 'shotType', 'situation', 'result']
        df_shots = df_shots[[c for c in cols if c in df_shots.columns]]
        df_shots.to_csv("real_shots_data.csv", index=False)
        
        print(f"✅ Data Selesai! {len(df_matches)} Matches & {len(df_shots)} Shots Tersimpan.")

if __name__ == "__main__":
    asyncio.run(fetch_comprehensive_data())