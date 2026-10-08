"""Fill players[] for clubs TheSportsDB has no squad data for.

Parses the "First team" wikitable of each club's Wikipedia season article.

Usage: python scripts/fill_players_from_wiki.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data_paths import CLUB_PROFILES  # noqa: E402

WIKI_UA = {"User-Agent": "PredikSoccer/1.0 (squad parser)"}

# klub -> kueri pencarian artikel season
SEASON_QUERY = {
    "Hamburger SV": "Hamburger SV 2026-27 season",
    "Leeds": "Leeds United 2026-27 season",
    "Lille": "Lille OSC 2026-27 season",
    "Mainz 05": "1. FSV Mainz 05 2026-27 season",
    "Nottingham Forest": "Nottingham Forest 2026-27 season",
    "PSG": "Paris Saint-Germain 2026-27 season",
    "RB Salzburg": "FC Red Bull Salzburg 2026-27 season",
}

ROW_RE = re.compile(
    r"^\|\s*(\d{1,2})\s*\|\|\s*\[\[(?:[^|\]]*\|)?([^\]]+)\]\]"
    r"\s*\|\|\s*(?:\[\[(?:[^|\]]*\|)?([^\]]+)\]\]|(\S+))",
    re.M,
)


def get_json(url: str, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=WIKI_UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            if attempt < retries - 1:
                time.sleep(8 * (attempt + 1))
            else:
                raise
    return None


def find_season_article(query: str) -> str | None:
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&format=json"
        "&list=search&srnamespace=0&srlimit=5&srsearch=" + urllib.parse.quote(query)
    )
    data = get_json(url)
    for row in data.get("query", {}).get("search", []):
        title = row["title"]
        if re.search(r"20(2[5-9])", title) and "season" in title.lower():
            return title
    return None


def wikitext(title: str) -> str:
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&format=json"
        "&prop=revisions&rvprop=content&rvslots=main&redirects=1&titles="
        + urllib.parse.quote(title)
    )
    data = get_json(url)
    for page in data.get("query", {}).get("pages", {}).values():
        if "revisions" in page:
            return page["revisions"][0]["slots"]["main"]["*"]
    return ""


def squad_section(w: str) -> str:
    """Ambil isi section 'First team'/'Players'/dst. sampai heading berikutnya."""
    headings = list(re.finditer(r"\n(={2,})\s*([^\n=]+?)\s*\1", w))
    for pref in ("First team", "Players", "Squad", "Current squad"):
        for m in headings:
            if m.group(2).strip().lower() != pref.lower():
                continue
            level = len(m.group(1))
            end = len(w)
            for n in headings:
                if n.start() > m.start() and len(n.group(1)) <= level:
                    end = n.start()
                    break
            section = w[m.end() : end]
            if section.strip():
                return section
    return ""


def parse_squad(section: str) -> list[dict]:
    players = []
    seen = set()
    for m in ROW_RE.finditer(section):
        number, name, pos_link, pos_plain = m.groups()
        position = (pos_link or pos_plain or "").strip()
        position = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", position)
        if name in seen:
            continue
        seen.add(name)
        players.append(
            {
                "name": name,
                "position": position or None,
                "image": None,
                "number": number,
            }
        )
        if len(players) >= 25:
            break
    return players


def main() -> None:
    profiles = json.loads(CLUB_PROFILES.read_text(encoding="utf-8"))
    todo = [c for c in SEASON_QUERY if not profiles.get(c, {}).get("players")]
    print("klub kosong:", todo, flush=True)
    for club in todo:
        print(f"{club} ...", end=" ", flush=True)
        title = find_season_article(SEASON_QUERY[club])
        time.sleep(1.2)
        if not title:
            print("artikel season tidak ketemu", flush=True)
            continue
        section = squad_section(wikitext(title))
        time.sleep(1.2)
        players = parse_squad(section)
        if players:
            profiles[club]["players"] = players
            print(f"{len(players)} pemain dari {title!r}", flush=True)
        else:
            print(f"tabel gagal diparse dari {title!r} (section={len(section)})", flush=True)
    CLUB_PROFILES.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=4), encoding="utf-8"
    )
    still = [c for c, v in profiles.items() if not v.get("players")]
    print("sisa tanpa pemain:", still, flush=True)


if __name__ == "__main__":
    main()
