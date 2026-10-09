"""Fetch data Understat (musim 2026) untuk semua liga yang didukung.

Understat kini memakai JSON API (bukan embedded script lagi):
  GET /getLeagueData/{league}/{season}  -> {teams, players, dates}
  GET /getMatchData/{match_id}          -> {rosters, shots:{h,a}}

Output:
  - historical_matches.csv (laga yang sudah selesai)
  - real_shots_data.csv    (level tembakan, semua liga termasuk Bundesliga)
"""
import asyncio
import sys
import time
from pathlib import Path

import aiohttp
import pandas as pd

# Konsol Windows (cp1252) tidak bisa encode emoji log
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from data_paths import HISTORICAL_MATCHES, REAL_SHOTS_DATA

LEAGUES = ["EPL", "La_liga", "Serie_A", "Bundesliga"]
SEASON = 2026
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
XHR = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
DELAY = 0.12  # jeda antar request agar tidak diblokir


async def get_json(session, url, referer):
    async with session.get(url, headers=dict(XHR, Referer=referer)) as r:
        r.raise_for_status()
        return await r.json(content_type=None)


async def fetch_all_leagues_data():
    all_shots = []
    all_matches = []

    async with aiohttp.ClientSession(
        headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    ) as session:
        for league in LEAGUES:
            print(f"🔄 Mengambil data {league} Musim {SEASON}...")
            referer = f"https://understat.com/league/{league}/{SEASON}"
            try:
                data = await get_json(
                    session,
                    f"https://understat.com/getLeagueData/{league}/{SEASON}",
                    referer,
                )
            except Exception as e:
                print(f"⚠️ Gagal mengambil data {league} {SEASON}: {e}")
                continue

            dates = data.get("dates", [])
            results = [d for d in dates if d.get("isResult")]
            print(f"   {len(results)} laga selesai dari {len(dates)} jadwal")

            for match in results:
                all_matches.append(
                    {
                        "match_id": match["id"],
                        "league": league,
                        "season": SEASON,
                        "datetime": match["datetime"],
                        "home_team": match["h"]["title"],
                        "away_team": match["a"]["title"],
                        "home_goals": int(match["goals"]["h"]),
                        "away_goals": int(match["goals"]["a"]),
                        "home_xg": float(match["xG"]["h"]),
                        "away_xg": float(match["xG"]["a"]),
                    }
                )

                try:
                    md = await get_json(
                        session,
                        f"https://understat.com/getMatchData/{match['id']}",
                        f"https://understat.com/match/{match['id']}",
                    )
                    shots = md.get("shots", {})
                    for side, is_home in (("h", 1), ("a", 0)):
                        for s in shots.get(side, []):
                            all_shots.append(
                                {
                                    "id": s["id"],
                                    "league": league,
                                    "team_name": s["h_team"] if is_home else s["a_team"],
                                    "opponent": s["a_team"] if is_home else s["h_team"],
                                    "is_home": is_home,
                                    "minute": int(s["minute"]),
                                    "player": s["player"],
                                    "X": float(s["X"]),
                                    "Y": float(s["Y"]),
                                    "xG": float(s["xG"]),
                                    "shotType": s["shotType"],
                                    "situation": s["situation"],
                                    "result": s["result"],
                                }
                            )
                except Exception as e:
                    print(f"   ⚠️ Shots laga {match['id']} gagal: {e}")
                    continue
                await asyncio.sleep(DELAY)

            print(f"   -> kumulatif: {len(all_matches)} laga, {len(all_shots)} shots")

    df_matches = pd.DataFrame(all_matches)
    df_matches.to_csv(HISTORICAL_MATCHES, index=False)

    df_shots = pd.DataFrame(all_shots)
    if not df_shots.empty:
        cols = [
            "id",
            "league",
            "team_name",
            "opponent",
            "is_home",
            "minute",
            "player",
            "X",
            "Y",
            "xG",
            "shotType",
            "situation",
            "result",
        ]
        df_shots = df_shots[[c for c in cols if c in df_shots.columns]]
        df_shots.to_csv(REAL_SHOTS_DATA, index=False)

    print(f"\n✅ BERHASIL! Total {len(df_matches)} Matches & {len(df_shots)} Shots tersimpan.")


if __name__ == "__main__":
    t0 = time.time()
    asyncio.run(fetch_all_leagues_data())
    print(f"Selesai dalam {time.time() - t0:.0f} detik")
