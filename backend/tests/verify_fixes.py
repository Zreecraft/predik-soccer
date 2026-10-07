"""Verifikasi khusus: abbr, alias, logo coverage, dan ticker format."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

import pandas as pd

from data_paths import TEAM_LOGOS, UPCOMING_FIXTURES
from team_aliases import TEAM_ALIASES, TEAM_ABBR, canonical_team, team_abbr

# 1. Test abbr untuk tim yang dikeluhkan user
test_cases = [
    ("Leeds", "LEE"),
    ("Arsenal", "ARS"),
    ("Manchester United", "MUN"),
    ("Manchester City", "MCI"),
    ("Chelsea", "CHE"),
    ("Liverpool", "LIV"),
    ("Tottenham", "TOT"),
    ("Real Madrid", "RMA"),
    ("Barcelona", "BAR"),
    ("Bayern Munich", "BAY"),
    ("Borussia Dortmund", "BVB"),
    ("Inter", "INT"),
    ("Inter Milan", "INT"),
    ("AC Milan", "MIL"),
    ("Como", "COM"),
    ("Como 1907", "COM"),
    ("PSG", "PSG"),
    ("Paris Saint-Germain", "PSG"),
    ("Lens", "RCL"),
    ("RC Lens", "RCL"),
    ("Lille", "LIL"),
    ("PSV", "PSV"),
    ("PSV Eindhoven", "PSV"),
    ("Feyenoord", "FEY"),
    ("Porto", "POR"),
    ("FC Porto", "POR"),
    ("Sporting CP", "SCP"),
    ("Galatasaray", "GAL"),
    ("Fenerbahce", "FEN"),
    ("Shakhtar Donetsk", "SHK"),
    ("Slavia Prague", "SLA"),
    ("Club Brugge", "CLU"),
    ("AEK Athens", "AEK"),
    ("LASK", "ASK"),
    ("Slovan Bratislava", "SLO"),
    ("Sabah FK", "SAB"),
    ("Stuttgart", "VFB"),
    ("VfB Stuttgart", "VFB"),
]

fails = 0
print("=== ABBR TEST ===")
for name, expected in test_cases:
    got = team_abbr(name)
    status = "OK " if got == expected else "FAIL"
    if got != expected:
        fails += 1
        print(f"{status} {name!r}: expected {expected}, got {got}")
print(f"{len(test_cases) - fails}/{len(test_cases)} abbr passed")

# 2. Alias canonical
print("\n=== ALIAS TEST ===")
alias_cases = [
    ("Leeds United", "Leeds"),
    ("Como 1907", "Como"),
    ("AS Roma", "Roma"),
    ("Inter Milan", "Inter"),
    ("Paris Saint-Germain", "PSG"),
    ("VfB Stuttgart", "Stuttgart"),
]
alias_fails = 0
for name, expected in alias_cases:
    got = canonical_team(name)
    status = "OK " if got == expected else "FAIL"
    if got != expected:
        alias_fails += 1
        print(f"{status} {name!r}: expected {expected}, got {got}")
print(f"{len(alias_cases) - alias_fails}/{len(alias_cases)} alias passed")

# 3. Logo coverage untuk semua tim di fixtures
print("\n=== LOGO COVERAGE ===")

fixtures = pd.read_csv(UPCOMING_FIXTURES)
teams_in_fixtures = sorted(
    set(fixtures["home_team"]).union(set(fixtures["away_team"]))
)
with open(TEAM_LOGOS, "r", encoding="utf-8") as f:
    logos = json.load(f)

missing = []
for t in teams_in_fixtures:
    canonical = canonical_team(t)
    if canonical not in logos and t not in logos:
        missing.append(t)

print(f"Teams in fixtures: {len(teams_in_fixtures)}")
print(f"Missing logos: {len(missing)}")
if missing:
    print("Missing list:", missing)

# 4. Ticker sample
print("\n=== TICKER SAMPLE ===")
from app import get_ticker
tick = get_ticker(limit=6)
for item in tick["items"]:
    print(f"  {item['home_short']} × {item['away_short']}  {item['date'][:16]}")

if fails == 0 and alias_fails == 0 and not missing:
    print("\nALL VERIFICATION PASSED")
else:
    print(f"\nIssues: {fails} abbr, {alias_fails} alias, {len(missing)} missing logos")
