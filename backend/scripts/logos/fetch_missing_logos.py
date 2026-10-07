"""Fetch missing team logos dari TheSportsDB API."""
import json
import time
import requests

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/
from data_paths import TEAM_LOGOS

MISSING = {
    "Borussia M.Gladbach": "Borussia Monchengladbach",
    "FC Cologne": "FC Koln",
    "Monza": "Monza",
    "Parma Calcio 1913": "Parma",
    "RasenBallsport Leipzig": "RB Leipzig",
    "Venezia": "Venezia FC",
}

ALIAS_FIX = {
    "Borussia M.Gladbach": "Borussia M'gladbach",
    "FC Cologne": "FC Koln",
    "RasenBallsport Leipzig": "RB Leipzig",
    "Parma Calcio 1913": "Parma Calcio 1913",
}

def search_team_badge(query, retries=3):
    url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={query}"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                teams = data.get("teams")
                if teams:
                    team = teams[0]
                    badge = team.get("strBadge") or team.get("strTeamBadge")
                    name = team.get("strTeam")
                    return name, badge
            return None, None
        except Exception as e:
            print(f"  retry {attempt+1} ({query}): {e}")
            time.sleep(2)
    return None, None

def main():
    with open(TEAM_LOGOS, "r", encoding="utf-8") as f:
        logos = json.load(f)

    print("=== FETCH MISSING LOGOS ===")
    for data_name, search_name in MISSING.items():
        found_name, badge = search_team_badge(search_name)
        if badge:
            print(f"OK {data_name} -> {found_name}: {badge}")
            league = logos.get(ALIAS_FIX.get(data_name, data_name), {}).get("league", "Unknown")
            logos[data_name] = {"league": league, "logo_url": badge}
            # Juga update alias target bila berbeda
            alias_target = ALIAS_FIX.get(data_name)
            if alias_target and alias_target not in logos:
                logos[alias_target] = {"league": league, "logo_url": badge}
        else:
            print(f"MISS {data_name} (query: {search_name})")
        time.sleep(1.5)

    with open(TEAM_LOGOS, "w", encoding="utf-8") as f:
        json.dump(logos, f, indent=4, ensure_ascii=False)
    print(f"\nSaved. Total teams: {len(logos)}")

if __name__ == "__main__":
    main()
