import asyncio
import aiohttp
import pandas as pd
from understat import Understat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from data_paths import HISTORICAL_MATCHES, REAL_SHOTS_DATA

# List Liga yang didukung oleh Understat
LEAGUES = ["EPL", "La_liga", "Serie_A", "Bundesliga"]

async def fetch_all_leagues_data(seasons=[2026]):
    all_shots = []
    all_matches = []
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        
        for league in LEAGUES:
            for season in seasons:
                print(f"🔄 Mengambil data {league} Musim {season}...")
                try:
                    results = await understat.get_league_results(league, season)
                except Exception as e:
                    print(f"⚠️ Gagal mengambil data {league} {season}: {e}")
                    continue
                
                for match in results:
                    all_matches.append({
                        'match_id': match['id'],
                        'league': league,
                        'season': season,
                        'datetime': match['datetime'],
                        'home_team': match['h']['title'],
                        'away_team': match['a']['title'],
                        'home_goals': int(match['goals']['h']),
                        'away_goals': int(match['goals']['a']),
                        'home_xg': float(match['xG']['h']),
                        'away_xg': float(match['xG']['a'])
                    })
                    
                    if len(all_shots) < 4000:
                        try:
                            shots = await understat.get_match_shots(match['id'])
                            for s in shots.get('h', []):
                                s['league'] = league
                                s['team_name'] = match['h']['title']
                                s['opponent'] = match['a']['title']
                                s['is_home'] = 1
                                all_shots.append(s)
                            for s in shots.get('a', []):
                                s['league'] = league
                                s['team_name'] = match['a']['title']
                                s['opponent'] = match['h']['title']
                                s['is_home'] = 0
                                all_shots.append(s)
                        except Exception:
                            continue

        # Simpan ke CSV
        df_matches = pd.DataFrame(all_matches)
        df_matches.to_csv(HISTORICAL_MATCHES, index=False)

        df_shots = pd.DataFrame(all_shots)
        if not df_shots.empty:
            cols = ['id', 'league', 'team_name', 'opponent', 'is_home', 'minute', 'player', 'X', 'Y', 'xG', 'shotType', 'situation', 'result']
            df_shots = df_shots[[c for c in cols if c in df_shots.columns]]
            df_shots.to_csv(REAL_SHOTS_DATA, index=False)
        
        print(f"\n✅ BERHASIL! Total {len(df_matches)} Matches & {len(df_shots)} Shots tersimpan.")

if __name__ == "__main__":
    asyncio.run(fetch_all_leagues_data())