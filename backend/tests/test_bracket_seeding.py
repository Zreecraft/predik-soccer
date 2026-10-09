import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from ucl_simulator import simulate_ucl_tournament

df = pd.read_csv("data/historical_matches.csv")
r = simulate_ucl_tournament(df)

lp = r["league_phase"]
print("=== Status League Phase ===")
for pos in (1, 8, 9, 16, 17, 24, 25, 36):
    t = lp[pos - 1]
    print(
        f'  P{pos:>2} {t["team"]:<20} status={t["status"]:<8} '
        f'seeded={t["is_seeded"]} detail={t["status_detail"]}'
    )

print("\n=== Play-off Pairs ===")
for m in r["knockout_stage"]["playoffs"]:
    print(f'  {m["match_id"]}: {m["team_home"]:<22} vs {m["team_away"]:<22} agg={m["aggregate"]}')

print("\n=== R16 Locked Bracket ===")
for m in r["knockout_stage"]["round_of_16"]:
    print(
        f'  {m["match_id"]} [{m["bracket_slot"]:<20}] '
        f'{m["seeded_team"]:<22} vs {m["team_away"]:<22} -> {m["winner"]}'
    )

side_p1 = side_p2 = None
for m in r["knockout_stage"]["round_of_16"]:
    if m["seeded_team"] == lp[0]["team"]:
        side_p1 = m["side"]
    if m["seeded_team"] == lp[1]["team"]:
        side_p2 = m["side"]
print(f'\nP1({lp[0]["team"]}) side={side_p1} | P2({lp[1]["team"]}) side={side_p2} -> beda sisi: {side_p1 != side_p2}')

# Cek QF / SF / Final ada
qf = r["knockout_stage"]["quarter_finals"]
sf = r["knockout_stage"]["semi_finals"]
fin = r["knockout_stage"]["final"]
print(f"\nQF matches: {len(qf)} | SF matches: {len(sf)} | Final: {fin['team_home']} vs {fin['team_away']}")
print("OK")
