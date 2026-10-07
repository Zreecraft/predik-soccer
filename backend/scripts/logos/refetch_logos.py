"""Fetch ulang logo ASLI dari TheSportsDB API untuk semua tim yang URL-nya rusak."""
import json
import time
import requests

from data_paths import TEAM_LOGOS

# Tim yang perlu fetch ulang (URL hardcode tadi 404)
TEAMS_TO_FIX = {
    # nama di team_logos.json -> query pencarian TheSportsDB
    "Paris Saint-Germain": "Paris Saint-Germain",
    "RC Lens": "Lens",
    "Lille": "Lille",
    "PSV Eindhoven": "PSV Eindhoven",
    "Feyenoord": "Feyenoord",
    "FC Porto": "FC Porto",
    "Sporting CP": "Sporting CP",
    "Galatasaray": "Galatasaray",
    "Fenerbahce": "Fenerbahce",
    "Shakhtar Donetsk": "Shakhtar Donetsk",
    "Slavia Prague": "Slavia Prague",
    "Club Brugge": "Club Brugge",
    "AEK Athens": "AEK Athens",
    "LASK": "LASK",
    "Slovan Bratislava": "Slovan Bratislava",
    "Sabah FK": "Sabah FK",
    "Southampton": "Southampton",
    "Burnley": "Burnley",
    "Sheffield United": "Sheffield United",
    "Como 1907": "Como",
    "VfB Stuttgart": "VfB Stuttgart",
    "AS Roma": "AS Roma",
    "Inter Milan": "Inter Milan",
    "Leeds": "Leeds United",
}

API_KEY = "3"  # free tier


def search_team(query, retries=3):
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/searchteams.php?t={query}"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                teams = data.get("teams")
                if teams:
                    # cari match paling mirip (football, bukan e-sport)
                    for t in teams:
                        sport = (t.get("strSport") or "").lower()
                        badge = t.get("strBadge") or t.get("strTeamBadge")
                        if sport == "soccer" and badge:
                            return t.get("strTeam"), badge
                    # fallback team pertama dengan badge
                    t = teams[0]
                    badge = t.get("strBadge") or t.get("strTeamBadge")
                    return t.get("strTeam"), badge
                return None, None
            print(f"  HTTP {r.status_code} ({query}), retry...")
        except Exception as e:
            print(f"  retry {attempt+1} ({query}): {type(e).__name__}")
        time.sleep(2)
    return None, None


def main():
    with open(TEAM_LOGOS, "r", encoding="utf-8") as f:
        logos = json.load(f)

    print("=== REFETCH REAL LOGOS ===")
    fixed, still_missing = 0, []
    for name, query in TEAMS_TO_FIX.items():
        found_name, badge = search_team(query)
        if badge:
            league = logos.get(name, {}).get("league", "Unknown")
            logos[name] = {"league": league, "logo_url": badge}
            print(f"OK  {name:<26} <- {found_name}: {badge}")
            fixed += 1
        else:
            still_missing.append(name)
            print(f"MISS {name} (query: {query})")
        time.sleep(1.2)  # rate limit

    with open(TEAM_LOGOS, "w", encoding="utf-8") as f:
        json.dump(logos, f, indent=4, ensure_ascii=False)

    print(f"\nFixed: {fixed}, Missing: {len(still_missing)}")
    if still_missing:
        print("Still missing:", still_missing)


if __name__ == "__main__":
    main()
