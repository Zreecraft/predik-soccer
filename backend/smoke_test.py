from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

checks = []

def ok(name, cond, extra=""):
    checks.append((name, bool(cond), extra))
    print(("OK " if cond else "FAIL "), name, extra)

r = client.get("/api/health")
ok("health", r.status_code == 200 and r.json()["status"] == "ok")

r = client.get("/api/leagues")
ok("leagues", r.status_code == 200 and len(r.json()) == 4)

r = client.get("/api/ticker?limit=8")
ok("ticker", r.status_code == 200 and r.json()["total"] > 0)

r = client.get("/api/fixtures/EPL?limit=8")
ok("fixtures", r.status_code == 200 and r.json()["total"] > 0 and "home_logo" in r.json()["fixtures"][0])

r = client.get("/api/predict?home_team=Arsenal&away_team=Chelsea")
j = r.json()
ok(
    "predict",
    r.status_code == 200
    and "projection" in j
    and "probabilities" in j
    and "tactical" in j
    and "differential_summary" in j
    and j["home_team"]["form"] is not None,
    f"{j.get('projection')} {j.get('probabilities')}",
)

r = client.get("/api/shots?home_team=Arsenal&away_team=Chelsea")
j = r.json()
ok(
    "shots",
    r.status_code == 200
    and j["home"]["shots"] > 0
    and len(j["home"]["points"]) > 0
    and "zone14_dominance" in j["summary"],
    f"home_shots={j['home']['shots']} points={len(j['home']['points'])}",
)

r = client.get("/api/standings/EPL?n_seasons=120")
j = r.json()
ok(
    "standings",
    r.status_code == 200
    and all(k in j["kpi"] for k in ("title_threshold", "ucl_threshold", "relegation_line", "rmse_pct"))
    and len(j["standings"]) > 0
    and "projected_points" in j["standings"][0]
    and "title_pct" in j["standings"][0],
    str(j["kpi"]),
)

r = client.get("/api/ucl/simulate")
j = r.json()
ok(
    "ucl",
    r.status_code == 200
    and "pots" in j
    and "Pot 1" in j["pots"]
    and j["knockout_stage"]["final"]["winner"]
    and j["champion"]["team"],
    f"champion={j['champion']['team']}",
)

r = client.get("/api/analytics/Arsenal")
j = r.json()
ok(
    "analytics",
    r.status_code == 200
    and j["profile"]["coach"] == "Mikel Arteta"
    and len(j["territorial"]) == 30
    and len(j["upcoming"]) > 0
    and "tactical_bullets" in j,
    f"ppda={j['ppda']} upcoming={len(j['upcoming'])}",
)

r = client.get("/api/teams?league=La_liga")
ok("teams", r.status_code == 200 and len(r.json()["teams"]) > 5)

failed = [c for c in checks if not c[1]]
print(f"\n{len(checks) - len(failed)}/{len(checks)} passed")
if failed:
    raise SystemExit(1)
print("ALL CHECKS PASSED")
