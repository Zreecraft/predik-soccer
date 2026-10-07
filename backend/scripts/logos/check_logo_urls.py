"""Validasi URL logo (HEAD request) untuk semua tim, khususnya yang baru ditambahkan."""
import json
import time
import requests

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/
from data_paths import TEAM_LOGOS

NEW_TEAMS = [
    "Paris Saint-Germain", "RC Lens", "Lille", "PSV Eindhoven", "Feyenoord",
    "FC Porto", "Sporting CP", "Galatasaray", "Fenerbahce", "Shakhtar Donetsk",
    "Slavia Prague", "Club Brugge", "AEK Athens", "LASK", "Slovan Bratislava",
    "Sabah FK", "Southampton", "Burnley", "Sheffield United", "Como 1907",
    "VfB Stuttgart", "AS Roma", "Inter Milan", "Leeds",
    "Borussia M.Gladbach", "FC Cologne", "Monza", "Parma Calcio 1913",
    "RasenBallsport Leipzig", "Venezia",
]

def check_url(url, timeout=10):
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return "OK", r.headers.get("content-type", "?")
        # beberapa CDN tolak HEAD; coba GET stream
        r2 = requests.get(url, timeout=timeout, stream=True)
        ct = r2.headers.get("content-type", "?")
        r2.close()
        return ("OK" if r2.status_code == 200 else f"HTTP {r2.status_code}"), ct
    except Exception as e:
        return f"ERR {type(e).__name__}", str(e)[:60]

def main():
    with open(TEAM_LOGOS, "r", encoding="utf-8") as f:
        logos = json.load(f)

    broken = []
    print(f"{'TEAM':<28} {'STATUS':<12} CONTENT-TYPE")
    print("-" * 80)
    for team in NEW_TEAMS:
        entry = logos.get(team) or {}
        url = entry.get("logo_url", "")
        status, ct = check_url(url)
        flag = "" if status == "OK" and ("image" in ct or "png" in ct or "octet" in ct) else "  <-- CHECK"
        print(f"{team:<28} {status:<12} {ct[:40]}{flag}")
        if flag:
            broken.append((team, url, status, ct))
        time.sleep(0.3)

    print("-" * 80)
    print(f"Total checked: {len(NEW_TEAMS)}, issues: {len(broken)}")
    if broken:
        print("\nBROKEN URLS:")
        for t, u, s, c in broken:
            print(f"  {t}: {u} ({s}; {c})")

if __name__ == "__main__":
    main()
