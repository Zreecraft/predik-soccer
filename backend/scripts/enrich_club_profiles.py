"""Enrich club_profiles.json: formation, style, rating, coach_rating (kurasi 2026-27).

Aman dijalankan berulang (resumable): hanya menambah/memperbarui field kurasi,
data coach/stadium/pemain hasil scraping tidak disentuh.

Pemakaian:
    python scripts/enrich_club_profiles.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_paths import CLUB_PROFILES

# club -> (formation, style, rating, coach_rating)
# style harus cocok dengan kunci grid club_analytics:
# possession | high_press | transition | gegenpress | defensive_block | vertical | balanced
CURATED = {
    # ---------------- English Premier League ----------------
    "Arsenal": ("4-3-3", "possession", 90, 88),
    "Aston Villa": ("4-2-3-1", "transition", 79, 84),
    "Bournemouth": ("4-2-3-1", "high_press", 69, 72),
    "Brentford": ("4-3-3", "transition", 69, 71),
    "Brighton": ("4-2-3-1", "possession", 76, 78),
    "Chelsea": ("4-2-3-1", "possession", 84, 87),
    "Coventry": ("4-4-2", "balanced", 62, 66),
    "Crystal Palace": ("3-4-2-1", "transition", 75, 76),
    "Everton": ("4-2-3-1", "defensive_block", 71, 70),
    "Fulham": ("4-2-3-1", "balanced", 70, 72),
    "Hull": ("4-2-3-1", "transition", 61, 63),
    "Ipswich": ("4-2-3-1", "possession", 63, 64),
    "Leeds": ("4-2-3-1", "transition", 66, 68),
    "Liverpool": ("4-2-3-1", "high_press", 88, 84),
    "Manchester City": ("4-3-3", "possession", 91, 84),
    "Manchester United": ("3-4-2-1", "transition", 78, 74),
    "Newcastle United": ("4-3-3", "high_press", 82, 80),
    "Nottingham Forest": ("4-2-3-1", "transition", 73, 72),
    "Sunderland": ("4-2-3-1", "balanced", 65, 70),
    "Tottenham": ("4-2-3-1", "possession", 81, 82),
    # ---------------- La Liga ----------------
    "Alaves": ("4-4-2", "defensive_block", 63, 65),
    "Athletic Club": ("4-2-3-1", "high_press", 78, 77),
    "Atletico Madrid": ("4-4-2", "defensive_block", 86, 90),
    "Barcelona": ("4-3-3", "possession", 91, 87),
    "Celta Vigo": ("4-3-3", "possession", 69, 72),
    "Deportivo La Coruna": ("4-2-3-1", "possession", 62, 63),
    "Elche": ("4-4-2", "balanced", 61, 62),
    "Espanyol": ("4-2-3-1", "defensive_block", 64, 65),
    "Getafe": ("4-4-2", "defensive_block", 65, 74),
    "Girona": ("4-3-3", "possession", 70, 72),
    "Levante": ("4-4-2", "transition", 60, 61),
    "Malaga": ("4-2-3-1", "balanced", 58, 60),
    "Osasuna": ("4-4-2", "defensive_block", 66, 70),
    "Racing Santander": ("4-4-2", "defensive_block", 59, 62),
    "Rayo Vallecano": ("4-2-3-1", "high_press", 65, 68),
    "Real Betis": ("4-2-3-1", "possession", 75, 82),
    "Real Madrid": ("4-3-3", "transition", 92, 92),
    "Real Sociedad": ("4-3-3", "possession", 74, 73),
    "Sevilla": ("4-3-3", "balanced", 70, 68),
    "Valencia": ("4-4-2", "balanced", 68, 70),
    "Villarreal": ("4-3-3", "possession", 77, 78),
    # ---------------- Serie A ----------------
    "Atalanta": ("3-4-2-1", "high_press", 80, 79),
    "Bologna": ("4-2-3-1", "high_press", 73, 75),
    "Cagliari": ("4-2-3-1", "defensive_block", 63, 62),
    "Como": ("4-3-3", "possession", 70, 74),
    "Fiorentina": ("4-2-3-1", "possession", 74, 73),
    "Frosinone": ("4-3-3", "balanced", 57, 58),
    "Genoa": ("4-2-3-1", "defensive_block", 64, 63),
    "Inter": ("3-5-2", "possession", 87, 80),
    "Juventus": ("3-4-2-1", "balanced", 83, 76),
    "Lazio": ("4-2-3-1", "possession", 77, 76),
    "Lecce": ("4-4-2", "defensive_block", 60, 60),
    "AC Milan": ("4-2-3-1", "transition", 82, 75),
    "Monza": ("4-3-3", "balanced", 59, 59),
    "Napoli": ("4-3-3", "high_press", 85, 88),
    "Parma Calcio 1913": ("4-3-3", "balanced", 62, 61),
    "Roma": ("4-2-3-1", "transition", 79, 78),
    "Sassuolo": ("4-3-3", "possession", 61, 64),
    "Torino": ("3-5-2", "defensive_block", 67, 70),
    "Udinese": ("3-5-2", "transition", 66, 67),
    "Venezia": ("4-3-3", "possession", 58, 59),
    # ---------------- Bundesliga ----------------
    "Augsburg": ("4-4-2", "defensive_block", 64, 66),
    "Bayer Leverkusen": ("3-4-2-1", "possession", 83, 79),
    "Bayern Munich": ("4-2-3-1", "high_press", 93, 86),
    "Borussia Dortmund": ("4-2-3-1", "transition", 84, 78),
    "Borussia M.Gladbach": ("4-2-3-1", "transition", 68, 66),
    "Eintracht Frankfurt": ("4-2-3-1", "transition", 75, 74),
    "Elversberg": ("4-2-3-1", "transition", 56, 58),
    "FC Cologne": ("4-3-3", "high_press", 65, 64),
    "Freiburg": ("3-4-2-1", "balanced", 72, 76),
    "Hamburger SV": ("4-4-2", "balanced", 63, 65),
    "Hoffenheim": ("3-4-2-1", "possession", 67, 64),
    "Mainz 05": ("3-4-2-1", "high_press", 71, 75),
    "Paderborn": ("4-3-3", "balanced", 58, 62),
    "RB Leipzig": ("4-2-3-1", "high_press", 81, 77),
    "Schalke 04": ("4-2-3-1", "high_press", 64, 63),
    "Stuttgart": ("4-2-3-1", "transition", 77, 74),
    "Union Berlin": ("3-5-2", "defensive_block", 65, 69),
    "VfB Stuttgart": ("4-2-3-1", "transition", 77, 74),
    "Werder Bremen": ("4-2-3-1", "balanced", 68, 67),
    # ---------------- Ligue 1 ----------------
    "Brest": ("4-2-3-1", "transition", 68, 67),
    "Lille": ("4-2-3-1", "balanced", 76, 73),
    "Monaco": ("4-2-3-1", "transition", 79, 74),
    "PSG": ("4-3-3", "possession", 91, 89),
    # ---------------- UCL / liga lainnya ----------------
    "Benfica": ("4-2-3-1", "possession", 81, 80),
    "Celtic": ("4-3-3", "high_press", 73, 74),
    "Club Brugge": ("4-3-3", "possession", 72, 71),
    "Dinamo Zagreb": ("4-3-3", "possession", 69, 68),
    "Feyenoord": ("4-2-3-1", "possession", 74, 73),
    "PSV": ("4-3-3", "high_press", 76, 77),
    "RB Salzburg": ("4-2-3-1", "high_press", 71, 70),
    "RasenBallsport Leipzig": ("4-2-3-1", "high_press", 81, 77),
    "Red Star Belgrade": ("4-4-2", "transition", 65, 64),
    "Shakhtar Donetsk": ("4-3-3", "possession", 72, 71),
    "Slovan Bratislava": ("4-4-2", "defensive_block", 62, 61),
    "Sparta Prague": ("4-2-3-1", "balanced", 68, 67),
    "Sporting CP": ("3-4-3", "high_press", 80, 78),
    "Sturm Graz": ("4-2-3-1", "high_press", 66, 67),
    "Young Boys": ("4-2-3-1", "possession", 67, 66),
}


def main() -> None:
    with open(CLUB_PROFILES, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    enriched, missing = 0, []
    for club, entry in profiles.items():
        cur = CURATED.get(club)
        if cur is None:
            missing.append(club)
            continue
        formation, style, rating, coach_rating = cur
        if entry.get("formation") == formation and entry.get("style") == style and entry.get("rating") == rating and entry.get("coach_rating") == coach_rating:
            continue
        entry["formation"] = formation
        entry["style"] = style
        entry["rating"] = rating
        entry["coach_rating"] = coach_rating
        enriched += 1

    with open(CLUB_PROFILES, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=4)

    print(f"enriched: {enriched}/{len(profiles)} klub")
    if missing:
        print("TANPA kurasi (perlu ditambahkan):", ", ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
