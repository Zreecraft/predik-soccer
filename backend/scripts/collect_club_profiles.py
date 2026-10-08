"""Collect coach, stadium and player data for all clubs.

Writes backend/data/club_profiles.json. Resumable: clubs already present
are skipped, so the script can be re-run after rate-limit interruptions.

Usage: python scripts/collect_club_profiles.py [--only "Arsenal,Chelsea"]
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data_paths import DATA_DIR  # noqa: E402

OUT = DATA_DIR / "club_profiles.json"
WIKI_UA = {"User-Agent": "PredikSoccer/1.0 (club profile collector)"}
BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SLEEP = 1.6
MANAGER_RE = re.compile(r"\|\s*(?:manager|head coach)\s*=\s*(.{0,150})", re.I)


def get_json(url: str, headers: dict, timeout: int = 30, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code in (429, 503, 1015) and attempt < retries - 1:
                wait = 15 * (attempt + 1)
                print(f"    HTTP {err.code}, tunggu {wait}s ...", flush=True)
                time.sleep(wait)
            else:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt < retries - 1:
                time.sleep(6)
            else:
                raise
    return None


def wiki_coach(team: str) -> str | None:
    q = urllib.parse.quote(f"{team} football club")
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&format=json"
        f"&generator=search&gsrsearch={q}&gsrlimit=5"
        "&prop=revisions&rvprop=content&rvslots=main"
    )
    data = get_json(url, WIKI_UA)
    pages = (data or {}).get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions")
        if not revs:
            continue
        wikitext = revs[0]["slots"]["main"]["*"]
        match = MANAGER_RE.search(wikitext)
        if match:
            raw = match.group(1).split("\n")[0]
            raw = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw)
            raw = re.sub(r"\{\{[^}]*\}\}", "", raw)
            name = re.sub(r"\s+", " ", raw).strip(" |'\"")
            if name and len(name) > 2:
                return name
    return None


def tsdb_team(team: str) -> dict | None:
    url = (
        "https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t="
        + urllib.parse.quote(team)
    )
    data = get_json(url, BROWSER_UA)
    teams = (data or {}).get("teams") or []
    for row in teams:
        if str(row.get("strSport", "")).lower() == "football":
            return row
    return teams[0] if teams else None


def tsdb_players(team_id: str) -> list:
    url = (
        "https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id="
        + team_id
    )
    data = get_json(url, BROWSER_UA)
    players = (data or {}).get("player") or []
    out = []
    for p in players:
        out.append(
            {
                "name": p.get("strPlayer"),
                "position": p.get("strPosition"),
                "image": p.get("strCutout") or p.get("strThumb"),
                "number": p.get("strNumber"),
            }
        )
    return out


def load() -> dict:
    if OUT.exists():
        return json.loads(OUT.read_text(encoding="utf-8"))
    return {}


def save(profiles: dict) -> None:
    OUT.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=4), encoding="utf-8"
    )


def all_clubs() -> list[str]:
    from ucl_simulator import UCL_TEAMS

    import pandas as pd

    fx = pd.read_csv(DATA_DIR / "upcoming_fixtures.csv")
    return sorted(set(fx["home_team"]) | set(fx["away_team"]) | set(UCL_TEAMS))


def main() -> None:
    only = None
    if "--only" in sys.argv:
        only = {s.strip() for s in sys.argv[sys.argv.index("--only") + 1].split(",")}

    profiles = load()
    clubs = [c for c in all_clubs() if not only or c in only]
    todo = [c for c in clubs if c not in profiles]
    print(f"{len(clubs)} klub, {len(todo)} belum terkumpul", flush=True)

    for i, club in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {club} ...", end=" ", flush=True)
        row = profiles.get(club, {})
        try:
            if "coach" not in row:
                row["coach"] = wiki_coach(club)
                time.sleep(SLEEP)
            team = tsdb_team(club)
            time.sleep(SLEEP)
            if team:
                row["stadium"] = team.get("strStadium")
                row["tsdb_id"] = team.get("idTeam")
                row["logo"] = team.get("strBadge") or row.get("logo")
            if "players" not in row and row.get("tsdb_id"):
                row["players"] = tsdb_players(str(row["tsdb_id"]))
                time.sleep(SLEEP)
            row.setdefault("players", [])
            profiles[club] = row
            save(profiles)
            print(
                f"pelatih={row.get('coach')!r} pemain={len(row.get('players') or [])}",
                flush=True,
            )
        except Exception as err:  # lanjut ke klub berikutnya
            profiles[club] = row
            save(profiles)
            print(f"GAGAL: {err}", flush=True)

    done = sum(1 for v in profiles.values() if v.get("coach"))
    print(f"Selesai: {done}/{len(profiles)} klub punya pelatih", flush=True)


if __name__ == "__main__":
    main()
