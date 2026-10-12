"""Fetch data Understat multi-musim (2020 -> sekarang) untuk semua liga yang didukung.

Understat kini memakai JSON API (bukan embedded script lagi):
  GET /getLeagueData/{league}/{season}  -> {teams, players, dates}
  GET /getMatchData/{match_id}          -> {rosters, shots:{h,a}}

Mode:
  (default)       : musim berjalan (2026) + shots, PLUS archive 2020-2025 (hasil laga saja)
  --archive-only  : hanya archive 2020-2025, merge dengan CSV yang ada (cepat, ~30 detik)
  --archive-shots : sertakan shots utk musim archive (lama, ~60 menit sekali jalan)

Output:
  - historical_matches.csv (semua musim, diurutkan datetime)
  - real_shots_data.csv    (level tembakan; di-append aman bila mode merge)
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
CURRENT_SEASON = 2026
ARCHIVE_SEASONS = [2020, 2021, 2022, 2023, 2024, 2025]
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
XHR = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
DELAY = 0.12  # jeda antar request match (shots) agar tidak diblokir
DELAY_LIGHT = 0.1  # jeda ringan antar request liga


async def get_json(session, url, referer):
    async with session.get(url, headers=dict(XHR, Referer=referer)) as r:
        r.raise_for_status()
        return await r.json(content_type=None)


async def fetch_league_season(session, league, season, with_shots, delay=DELAY):
    """Ambil satu musim satu liga -> (rows_laga, rows_shots)."""
    referer = f"https://understat.com/league/{league}/{season}"
    try:
        data = await get_json(
            session,
            f"https://understat.com/getLeagueData/{league}/{season}",
            referer,
        )
    except Exception as e:
        print(f"  Gagal mengambil data {league} {season}: {e}")
        return [], []

    dates = data.get("dates", [])
    results = [d for d in dates if d.get("isResult")]
    print(f"  {league} {season}: {len(results)} laga selesai dari {len(dates)} jadwal")

    matches = []
    shots = []
    for match in results:
        matches.append(
            {
                "match_id": match["id"],
                "league": league,
                "season": season,
                "datetime": match["datetime"],
                "home_team": match["h"]["title"],
                "away_team": match["a"]["title"],
                "home_goals": int(match["goals"]["h"]),
                "away_goals": int(match["goals"]["a"]),
                "home_xg": float(match["xG"]["h"]),
                "away_xg": float(match["xG"]["a"]),
            }
        )

        if not with_shots:
            continue
        try:
            md = await get_json(
                session,
                f"https://understat.com/getMatchData/{match['id']}",
                f"https://understat.com/match/{match['id']}",
            )
            shot_rows = md.get("shots", {})
            for side, is_home in (("h", 1), ("a", 0)):
                for s in shot_rows.get(side, []):
                    shots.append(
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
            print(f"    Shots laga {match['id']} gagal: {e}")
        await asyncio.sleep(delay)

    return matches, shots


def _merge_csv(path: Path, new_df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Gabung new_df dengan CSV lama, dedupe by key, urutkan datetime."""
    try:
        old = pd.read_csv(path)
        merged = pd.concat([old, new_df], ignore_index=True)
    except FileNotFoundError:
        merged = new_df
    merged = merged.drop_duplicates(subset=[key], keep="last")
    if "datetime" in merged.columns:
        merged = merged.sort_values("datetime")
    return merged.reset_index(drop=True)


async def fetch_all_leagues_data():
    argv = [a.lower() for a in sys.argv[1:]]
    archive_only = "--archive-only" in argv
    archive_shots = "--archive-shots" in argv

    all_shots = []
    all_matches = []
    shots_from_archive = False

    async with aiohttp.ClientSession(
        headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    ) as session:
        if not archive_only:
            print(f"Musim berjalan {CURRENT_SEASON} (dengan shots)...")
            for league in LEAGUES:
                m, s = await fetch_league_season(session, league, CURRENT_SEASON, with_shots=True)
                all_matches.extend(m)
                all_shots.extend(s)
                print(f"   kumulatif: {len(all_matches)} laga, {len(all_shots)} shots")
                await asyncio.sleep(DELAY_LIGHT)

        print(f"Archive musim {ARCHIVE_SEASONS[0]}-{ARCHIVE_SEASONS[-1]} "
              f"({'dengan' if archive_shots else 'tanpa'} shots)...")
        for season in ARCHIVE_SEASONS:
            for league in LEAGUES:
                m, s = await fetch_league_season(
                    session, league, season, with_shots=archive_shots
                )
                all_matches.extend(m)
                if s:
                    all_shots.extend(s)
                    shots_from_archive = True
                await asyncio.sleep(DELAY_LIGHT)
            print(f"   kumulatif: {len(all_matches)} laga, {len(all_shots)} shots")

    # --- tulis historical (archive-only = merge dgn CSV; selain itu tulis penuh) ---
    if all_matches:
        df_m = pd.DataFrame(all_matches)
        if archive_only:
            df_m = _merge_csv(HISTORICAL_MATCHES, df_m, key="match_id")
        else:
            df_m = df_m.drop_duplicates(subset=["match_id"], keep="last")
            df_m = df_m.sort_values("datetime").reset_index(drop=True)
        df_m.to_csv(HISTORICAL_MATCHES, index=False)
        print(f"historical_matches.csv: {len(df_m)} baris, "
              f"{df_m['season'].min()}-{df_m['season'].max()}")
    else:
        print("Tidak ada laga berhasil diambil - historical_matches.csv TIDAK diubah.")

    # --- tulis shots ---
    if all_shots and not archive_only and not shots_from_archive:
        df_shots = pd.DataFrame(all_shots)
        cols = [
            "id", "league", "team_name", "opponent", "is_home", "minute",
            "player", "X", "Y", "xG", "shotType", "situation", "result",
        ]
        df_shots = df_shots[[c for c in cols if c in df_shots.columns]]
        df_shots.to_csv(REAL_SHOTS_DATA, index=False)
        print(f"real_shots_data.csv: {len(df_shots)} shots")
    elif all_shots and (archive_only or shots_from_archive):
        df_new = pd.DataFrame(all_shots)
        df_new = _merge_csv(REAL_SHOTS_DATA, df_new, key="id")
        df_new.to_csv(REAL_SHOTS_DATA, index=False)
        print(f"real_shots_data.csv (merge): {len(df_new)} shots")
    else:
        print("real_shots_data.csv TIDAK diubah (tanpa shots pada mode ini).")

    print(f"\nBERHASIL! Total {len(all_matches)} Matches & {len(all_shots)} Shots.")


if __name__ == "__main__":
    t0 = time.time()
    asyncio.run(fetch_all_leagues_data())
    print(f"Selesai dalam {time.time() - t0:.0f} detik")
