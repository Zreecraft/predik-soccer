"""Fix wrong TheSportsDB team ids in club_profiles.json.

The first collector filtered on strSport == "football" while the API uses
"Soccer", so several clubs ended up with the wrong team (PSG -> PSG Talon
esports, Inter -> Intercity, Lille -> field hockey, ...). This pass re-searches
every club, scores candidates by name similarity with hard filters, and
refreshes tsdb_id / stadium / players when the id changes.

Usage: python scripts/reid_club_profiles.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data_paths import CLUB_PROFILES  # noqa: E402

BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SLEEP = 2.4

# klub yang query default-nya ambigu
ALT_QUERY = {
    "PSG": ["Paris Saint-Germain", "Paris SG"],
    "Hull": ["Hull City"],
    "Inter": ["Inter Milan", "Internazionale"],
    "Mainz 05": ["Mainz"],
    "Lille": ["Lille OSC"],
    "Hamburger SV": ["Hamburg"],
    "RB Salzburg": ["Red Bull Salzburg"],
    "Nottingham Forest": ["Nottingham"],
    "PSV": ["PSV Eindhoven"],
    "RB Leipzig": ["RasenBallsport"],
    "Ipswich": ["Ipswich Town"],
    "Leeds": ["Leeds United"],
    "Athletic Club": ["Athletic Bilbao"],
    "Atletico Madrid": ["Atletico de Madrid"],
    "RasenBallsport Leipzig": ["RB Leipzig"],
    "Schalke 04": ["Schalke"],
    "Union Berlin": ["Union Berlin"],
    "Elversberg": ["SV Elversberg"],
}
BAD_TOKEN = re.compile(
    r"\b(women|w\.f\.c|youth|u1[589]|u2[13]|reserve|esports|talon|netball|"
    r"hockey|futsal|beach|indoor|legend|hall of fame)\b",
    re.I,
)


def get_json(url: str, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=BROWSER_UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
            else:
                raise
    return None


def norm(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\b(fc|f\.c|cf|c\.f|soccer club|football club|af|a\.f\.c)\b", " ", name)
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


def score(candidate: str, club: str) -> float:
    a, b = norm(candidate), norm(club)
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    if a == b or a.startswith(b) or b.startswith(a):
        ratio += 0.5
    return ratio


def search_teams(query: str) -> list[dict]:
    url = (
        "https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t="
        + urllib.parse.quote(query)
    )
    time.sleep(SLEEP)
    data = get_json(url)
    return data.get("teams") or []


def pick_team(club: str) -> dict | None:
    # evaluasi SEMUA query, ambil skor tertinggi (jangan break awal:
    # query pertama sering kena tim yang salah tapi mirip)
    queries = [club, *ALT_QUERY.get(club, [])]
    best, best_score = None, 0.0
    for query in queries:
        try:
            teams = search_teams(query)
        except Exception as err:
            print(f"[search {query!r} gagal: {err}]", end=" ", flush=True)
            continue
        for team in teams:
            sport = str(team.get("strSport", "")).lower()
            if sport not in ("soccer", "football"):
                continue
            if BAD_TOKEN.search(team.get("strTeam", "") or ""):
                continue
            s = score(team.get("strTeam", ""), club)
            if s > best_score:
                best, best_score = team, s
    return best if best_score >= 0.75 else None


def players_of(team_id: str) -> list[dict]:
    time.sleep(SLEEP)
    data = get_json(
        "https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id="
        + str(team_id)
    )
    return [
        {
            "name": p.get("strPlayer"),
            "position": p.get("strPosition"),
            "image": p.get("strCutout") or p.get("strThumb"),
            "number": p.get("strNumber"),
        }
        for p in (data.get("player") or [])
    ]


def main() -> None:
    only = None
    if "--only" in sys.argv:
        only = {s.strip() for s in sys.argv[sys.argv.index("--only") + 1].split(",")}

    profiles = json.loads(CLUB_PROFILES.read_text(encoding="utf-8"))
    fixed, filled, failed = [], [], []
    clubs = [c for c in sorted(profiles) if not only or c in only]
    for i, club in enumerate(clubs, 1):
        row = profiles[club]
        print(f"[{i}/{len(clubs)}] {club} ...", end=" ", flush=True)
        try:
            team = pick_team(club)
            if team is None:
                print("tidak ada kandidat cocok", flush=True)
                failed.append(club)
                continue
            new_id = team.get("idTeam")
            old_id = row.get("tsdb_id")
            notes = []
            if str(new_id) != str(old_id):
                row["tsdb_id"] = new_id
                notes.append(f"id {old_id}->{new_id} ({team.get('strTeam')})")
                fixed.append(club)
                if team.get("strStadium"):
                    row["stadium"] = team.get("strStadium")
            if notes or not row.get("players"):
                row["players"] = players_of(new_id)
                notes.append(f"pemain={len(row['players'])}")
                if not notes[:-1] and row["players"]:
                    filled.append(club)
        except Exception as err:
            print(f"GAGAL: {err}", flush=True)
            failed.append(club)
            time.sleep(20)
            continue
        CLUB_PROFILES.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=4), encoding="utf-8"
        )
        print("; ".join(notes) or "ok", flush=True)
    print(f"id diperbaiki: {len(fixed)} -> {fixed}", flush=True)
    print(f"pemain diisi: {filled}", flush=True)
    print(f"gagal: {failed}", flush=True)


if __name__ == "__main__":
    main()
