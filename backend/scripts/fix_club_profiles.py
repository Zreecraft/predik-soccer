"""Repair coach/stadium in club_profiles.json using explicit Wikipedia titles.

The blind search pass picked wrong articles for some clubs (Barcelona SC of
Ecuador, Real Madrid Castilla, ...). This pass queries the exact official
article for every club in a few batched requests and rewrites coach/stadium.

Usage: python scripts/fix_club_profiles.py
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

WIKI_UA = {"User-Agent": "PredikSoccer/1.0 (club profile verifier)"}

# club name (di club_profiles.json) -> judul artikel Wikipedia EN
TITLES: dict[str, str] = {
    "AC Milan": "AC Milan",
    "Alaves": "Deportivo Alavés",
    "Arsenal": "Arsenal F.C.",
    "Aston Villa": "Aston Villa F.C.",
    "Atalanta": "Atalanta B.C.",
    "Athletic Club": "Athletic Bilbao",
    "Atletico Madrid": "Atlético Madrid",
    "Augsburg": "FC Augsburg",
    "Barcelona": "FC Barcelona",
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Bayern Munich": "FC Bayern Munich",
    "Benfica": "S.L. Benfica",
    "Bologna": "Bologna F.C. 1909",
    "Borussia Dortmund": "Borussia Dortmund",
    "Borussia M.Gladbach": "Borussia Mönchengladbach",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford F.C.",
    "Brest": "Stade Brestois 29",
    "Brighton": "Brighton & Hove Albion F.C.",
    "Cagliari": "Cagliari Calcio",
    "Celta Vigo": "Celta Vigo",
    "Celtic": "Celtic F.C.",
    "Chelsea": "Chelsea F.C.",
    "Club Brugge": "Club Brugge",
    "Como": "Como 1907",
    "Coventry": "Coventry City F.C.",
    "Crystal Palace": "Crystal Palace F.C.",
    "Deportivo La Coruna": "Deportivo de La Coruña",
    "Dinamo Zagreb": "GNK Dinamo Zagreb",
    "Eintracht Frankfurt": "Eintracht Frankfurt",
    "Elche": "Elche CF",
    "Elversberg": "SV Elversberg",
    "Espanyol": "RCD Espanyol",
    "Everton": "Everton F.C.",
    "FC Cologne": "1. FC Köln",
    "Feyenoord": "Feyenoord",
    "Fiorentina": "ACF Fiorentina",
    "Freiburg": "SC Freiburg",
    "Frosinone": "Frosinone Calcio",
    "Fulham": "Fulham F.C.",
    "Genoa": "Genoa CFC",
    "Getafe": "Getafe CF",
    "Girona": "Girona FC",
    "Hamburger SV": "Hamburger SV",
    "Hoffenheim": "TSG 1899 Hoffenheim",
    "Hull": "Hull City A.F.C.",
    "Inter": "Inter Milan",
    "Ipswich": "Ipswich Town F.C.",
    "Juventus": "Juventus F.C.",
    "Lazio": "SS Lazio",
    "Lecce": "U.S. Lecce",
    "Leeds": "Leeds United F.C.",
    "Levante": "Levante UD",
    "Lille": "LOSC Lille",
    "Liverpool": "Liverpool F.C.",
    "Mainz 05": "1. FSV Mainz 05",
    "Malaga": "Málaga CF",
    "Manchester City": "Manchester City F.C.",
    "Manchester United": "Manchester United F.C.",
    "Monaco": "AS Monaco FC",
    "Monza": "AC Monza",
    "Napoli": "SSC Napoli",
    "Newcastle United": "Newcastle United F.C.",
    "Nottingham Forest": "Nottingham Forest F.C.",
    "Osasuna": "CA Osasuna",
    "PSG": "Paris Saint-Germain F.C.",
    "PSV": "PSV Eindhoven",
    "Paderborn": "SC Paderborn 07",
    "Parma Calcio 1913": "Parma Calcio 1913",
    "RB Leipzig": "RB Leipzig",
    "RB Salzburg": "FC Red Bull Salzburg",
    "Racing Santander": "Racing de Santander",
    "RasenBallsport Leipzig": "RB Leipzig",
    "Rayo Vallecano": "Rayo Vallecano",
    "Real Betis": "Real Betis",
    "Real Madrid": "Real Madrid C.F.",
    "Real Sociedad": "Real Sociedad",
    "Red Star Belgrade": "Red Star Belgrade",
    "Roma": "AS Roma",
    "Sassuolo": "U.S. Sassuolo Calcio",
    "Schalke 04": "FC Schalke 04",
    "Sevilla": "Sevilla FC",
    "Shakhtar Donetsk": "Shakhtar Donetsk",
    "Slovan Bratislava": "ŠK Slovan Bratislava",
    "Sparta Prague": "AC Sparta Prague",
    "Sporting CP": "Sporting CP",
    "Sturm Graz": "SK Sturm Graz",
    "Stuttgart": "VfB Stuttgart",
    "Sunderland": "Sunderland A.F.C.",
    "Torino": "Torino F.C.",
    "Tottenham": "Tottenham Hotspur F.C.",
    "Udinese": "Udinese Calcio",
    "Union Berlin": "1. FC Union Berlin",
    "Valencia": "Valencia CF",
    "Venezia": "Venezia F.C.",
    "VfB Stuttgart": "VfB Stuttgart",
    "Villarreal": "Villarreal CF",
    "Werder Bremen": "SV Werder Bremen",
    "Young Boys": "BSC Young Boys",
}

MANAGER_RE = re.compile(
    r"\|\s*(?:manager|head coach|coach)\s*=\s*(.{0,200})", re.I
)
STADIUM_RE = re.compile(r"\|\s*(?:stadium|ground|arena)\s*=\s*(.{0,160})", re.I)
BAD_RE = re.compile(
    r"[<>=]|\{\{|\buntil\b|caretaker|interim|mgrtitle|league =|\b(19|20)\d{2}\b",
    re.I,
)
ALLOWED_PUNCT = " '-."


def get_json(url: str, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=WIKI_UA)
            with urllib.request.urlopen(req, timeout=40) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            if attempt < retries - 1:
                time.sleep(8 * (attempt + 1))
            else:
                raise
    return None


def clean_markup(raw: str) -> str:
    # komentar/ref dulu (bisa multi-baris), baru batasi ke baris pertama
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    raw = re.split(r"<!--", raw, maxsplit=1)[0]
    raw = re.split(r"<ref", raw, maxsplit=1, flags=re.I)[0]
    raw = raw.split("\n")[0]
    raw = re.sub(r"<br\s*/?>.*", "", raw, flags=re.I)
    raw = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw)
    raw = re.sub(r"\{\{[^}]*\}\}", "", raw)
    raw = re.sub(r"'{2,}", "", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip(" |'\"")


def looks_like_person(name: str) -> bool:
    if not name or len(name) < 4 or len(name) > 45:
        return False
    if BAD_RE.search(name):
        return False
    # huruf Unicode apa pun (Terzić, Højlund, ...) + tanda baca nama
    if not all(c.isalpha() or c in ALLOWED_PUNCT for c in name):
        return False
    words = name.split()
    if not (2 <= len(words) <= 4):
        return False
    return all(len(w) >= 2 or w in ("de", "van", "da", "di", "la") for w in words)


def fetch_wikitexts(titles: list[str]) -> dict[str, str]:
    """Batch action=query (50 judul/request) -> {judul artikel: wikitext}."""
    out: dict[str, str] = {}
    for start in range(0, len(titles), 50):
        batch = titles[start : start + 50]
        url = (
            "https://en.wikipedia.org/w/api.php?action=query&format=json"
            "&prop=revisions&rvprop=content&rvslots=main&redirects=1&titles="
            + urllib.parse.quote("|".join(batch))
        )
        data = get_json(url)
        query = data.get("query", {})
        # mapping judul asli (setelah normalize/redirect) -> judul original
        back: dict[str, str] = {}
        for key in ("normalized", "redirects"):
            for item in query.get(key, []):
                back[item["to"]] = item["from"]
        for page in query.get("pages", {}).values():
            revs = page.get("revisions")
            if not revs:
                continue
            title = page.get("title", "")
            original = back.get(title, title)
            out[original] = revs[0]["slots"]["main"]["*"]
        time.sleep(1.0)
    return out


def extract(wikitext: str) -> tuple[str | None, str | None]:
    """Ambil dari infobox klub (bagian sebelum heading '==' pertama)."""
    head = re.split(r"\n==+\s*\w", wikitext, maxsplit=1)[0]
    coach = stadium = None
    for match in MANAGER_RE.finditer(head):
        name = clean_markup(match.group(1))
        if coach is None and looks_like_person(name):
            coach = name
            break
    for match in STADIUM_RE.finditer(head):
        stad = clean_markup(match.group(1))
        if (
            stadium is None
            and 4 < len(stad) < 60
            and not BAD_RE.search(stad)
            and "capacity" not in stad.lower()
            and "square" not in stad.lower()
            and "hotel" not in stad.lower()
        ):
            stadium = stad
            break
    return coach, stadium


def main() -> None:
    profiles = json.loads(CLUB_PROFILES.read_text(encoding="utf-8"))
    wanted: dict[str, str] = {}  # judul wikipedia -> klub (dedupe utk alias)
    for club, title in TITLES.items():
        if club in profiles:
            wanted.setdefault(title, club)
    print(f"Fetch wikitext {len(wanted)} artikel ...", flush=True)
    pages = fetch_wikitexts(sorted(wanted))
    print(f"Dapat {len(pages)} artikel", flush=True)

    changed = []
    for title, club in sorted(wanted.items(), key=lambda x: x[1]):
        wikitext = pages.get(title)
        if wikitext is None:
            print(f"{club:22} ARTIKEL TIDAK KETEMU ({title})", flush=True)
            continue
        coach, stadium = extract(wikitext)
        row = profiles[club]
        old = (row.get("coach"), row.get("stadium"))
        if coach:
            row["coach"] = coach
        if stadium:
            row["stadium"] = stadium
        if (row.get("coach"), row.get("stadium")) != old:
            changed.append(club)
            print(
                f"{club:22} coach={row.get('coach')!r} stadion={row.get('stadium')!r}",
                flush=True,
            )
        # alias dengan artikel sama ikut disalin
        for alias, alias_title in TITLES.items():
            if alias_title == title and alias in profiles and alias != club:
                profiles[alias]["coach"] = row.get("coach")
                profiles[alias]["stadium"] = row.get("stadium")

    CLUB_PROFILES.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=4), encoding="utf-8"
    )
    print(f"Selesai, {len(changed)} klub diubah")


if __name__ == "__main__":
    main()
