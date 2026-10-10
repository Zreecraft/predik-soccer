"""Live score service — skor ASLI via ESPN (tanpa key) / football-data.org, mock fallback.

Prioritas sumber:
  1. football-data.org v4  — jika FOOTBALL_DATA_API_KEY diset (env / backend/.env)
  2. ESPN public scoreboard — tanpa API key, endpoint /soccer/all (H-2..H)
  3. Mock lokal — simulasi deterministik, dilabeli source="mock"

- Server-side cache TTL 55 detik.
- Konfigurasi key: env FOOTBALL_DATA_API_KEY atau file backend/.env
"""
from __future__ import annotations

import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from assets import get_key_player, get_team_logo
from data_paths import HISTORICAL_MATCHES, UPCOMING_FIXTURES
from season_projection import _compute_actual_table
from team_aliases import canonical_team, team_abbr

API_BASE = "https://api.football-data.org/v4"
CACHE_TTL = 55  # detik — aman di bawah limit 10 req/menit

COMP_TO_LEAGUE = {"PL": "EPL", "PD": "La_liga", "SA": "Serie_A", "BL": "Bundesliga"}
LEAGUE_TO_COMP = {v: k for k, v in COMP_TO_LEAGUE.items()}

LEAGUE_DISPLAY = {
    "EPL": "Premier League",
    "La_liga": "La Liga",
    "Serie_A": "Serie A",
    "Bundesliga": "Bundesliga",
    "UCL": "Champions League",
}

LIVE_STATUSES = {"IN_PLAY", "PAUSED", "LIVE"}


def _load_dotenv() -> None:
    p = Path(__file__).with_name(".env")
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()

_CACHE: dict = {"ts": 0.0, "payload": None}


# ==========================================
# API football-data.org
# ==========================================

def _parse_api_match(m: dict) -> dict:
    comp = (m.get("competition") or {}).get("code") or ""
    status = m.get("status") or ""
    score = (m.get("score") or {}).get("fullTime") or {}
    home = m.get("homeTeam") or {}
    away = m.get("awayTeam") or {}
    h_name = home.get("name") or home.get("shortName") or "?"
    a_name = away.get("name") or away.get("shortName") or "?"
    live = status in LIVE_STATUSES
    return {
        "id": m.get("id"),
        "league": COMP_TO_LEAGUE.get(comp, "UCL" if comp == "CL" else comp),
        "competition": comp,
        "competition_name": LEAGUE_DISPLAY.get(comp_to_league(comp), comp),
        "status": status,
        "live": live,
        "minute": m.get("minute") if status in ("IN_PLAY", "PAUSED") else None,
        "home": h_name,
        "away": a_name,
        "home_short": home.get("tla") or team_abbr(h_name),
        "away_short": away.get("tla") or team_abbr(a_name),
        "home_score": score.get("home"),
        "away_score": score.get("away"),
        "kickoff": m.get("utcDate"),
        "kickoff_wib": _wib_str(m.get("utcDate")),
        "crest_home": home.get("crest"),
        "crest_away": away.get("crest"),
    }


def comp_to_league(comp: str) -> str:
    return COMP_TO_LEAGUE.get(comp, "UCL" if comp == "CL" else comp)


def _wib_str(dt) -> str:
    """Format datetime UTC -> 'Sab, 10 Okt 2026 • 18:30 WIB'."""
    if not dt:
        return None
    try:
        t = pd.Timestamp(dt)
    except Exception:
        return None
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    t = t.tz_convert("Asia/Jakarta")
    days = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    return f"{days[t.dayofweek]}, {t.day} {months[t.month - 1]} {t.year} • {t.hour:02d}:{t.minute:02d} WIB"


def _fetch_api() -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/matches",
        headers={"X-Auth-Token": API_KEY},
        params={"status": "IN_PLAY,PAUSED,TIMED,FINISHED"},
        timeout=10,
    )
    resp.raise_for_status()
    return [_parse_api_match(m) for m in resp.json().get("matches", [])]


# ==========================================
# ESPN public scoreboard (skor ASLI, tanpa API key)
# ==========================================

ESPN_LEAGUES = {
    "eng.1": "EPL",
    "esp.1": "La_liga",
    "ita.1": "Serie_A",
    "ger.1": "Bundesliga",
    "uefa.champions": "UCL",
}

# id liga di uid ESPN (s:40~l:XXX~e:...) -> kode liga kita
ESPN_UID_TO_LEAGUE = {
    "700": "EPL",
    "740": "La_liga",
    "730": "Serie_A",
    "720": "Bundesliga",
    "775": "UCL",
}


def _parse_espn_event(ev: dict, league: str) -> dict | None:
    comps = ev.get("competitions") or []
    if not comps:
        return None
    comp = comps[0]
    competitors = comp.get("competitors") or []
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    st = ev.get("status") or {}
    stype = st.get("type") or {}
    state = stype.get("state") or "pre"
    detail = (stype.get("detail") or "").lower()
    tname = (stype.get("name") or "").lower()

    if "postpon" in detail or "susp" in detail or "abandon" in detail:
        status = "TIMED"  # ditunda / dibatalkan — jangan tampil sebagai hasil
    elif state == "post":
        status = "FINISHED"
    elif state == "in":
        status = "PAUSED" if ("halftime" in tname or "half-time" in detail or detail == "ht") else "IN_PLAY"
    else:
        status = "TIMED"

    minute = None
    if status in ("IN_PLAY", "PAUSED"):
        cstat = (comp.get("status") or {})
        clock = cstat.get("clock") or st.get("clock")
        if isinstance(clock, dict):
            minute = clock.get("value")
            if minute is None:
                digits = re.findall(r"\d+", str(clock.get("displayValue") or ""))
                minute = int(digits[0]) if digits else None
        elif isinstance(clock, (int, float)) and clock:
            minute = int(clock // 60)
        if minute is None:
            dc = st.get("displayClock") or cstat.get("displayClock")
            digits = re.findall(r"\d+", str(dc or ""))
            minute = int(digits[0]) if digits else None

    def _score(c: dict):
        raw = c.get("score")
        try:
            return int(raw) if raw is not None and str(raw).strip() != "" else None
        except (TypeError, ValueError):
            return None

    ht = home.get("team") or {}
    at = away.get("team") or {}
    h_name = ht.get("displayName") or ht.get("shortDisplayName") or "?"
    a_name = at.get("displayName") or at.get("shortDisplayName") or "?"
    kickoff = ev.get("date")
    return {
        "id": ev.get("id"),
        "league": league,
        "competition": LEAGUE_TO_COMP.get(league, "CL"),
        "competition_name": LEAGUE_DISPLAY.get(league, league),
        "status": status,
        "live": status in LIVE_STATUSES,
        "minute": minute,
        "home": h_name,
        "away": a_name,
        "home_short": ht.get("abbreviation") or team_abbr(h_name),
        "away_short": at.get("abbreviation") or team_abbr(a_name),
        "home_score": None if status == "TIMED" else _score(home),
        "away_score": None if status == "TIMED" else _score(away),
        "kickoff": kickoff,
        "kickoff_wib": _wib_str(kickoff),
        "crest_home": ht.get("logo"),
        "crest_away": at.get("logo"),
    }


def _fetch_espn() -> list[dict]:
    """ESPN public scoreboard (endpoint /all) — skor ASLI, tanpa API key.

    Satu request per hari (H-2, H-1, H) dengan limit=1000, filter liga kita
    via id di uid event. Menangkap laga FINISHED, LIVE, dan TIMED terdekat.
    """
    today = datetime.now(timezone.utc)
    out: list[dict] = []
    seen: set[str] = set()
    for offset in (-2, -1, 0):
        day = (today + timedelta(days=offset)).strftime("%Y%m%d")
        resp = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard",
            params={"dates": day, "limit": 1000},
            timeout=15,
        )
        resp.raise_for_status()
        for ev in resp.json().get("events") or []:
            uid = ev.get("uid") or ""
            m = re.search(r"l:(\d+)", uid)
            if not m:
                continue
            league = ESPN_UID_TO_LEAGUE.get(m.group(1))
            if not league:
                continue
            if ev.get("id") in seen:
                continue
            seen.add(ev.get("id"))
            parsed = _parse_espn_event(ev, league)
            if parsed:
                out.append(parsed)
    return out


# ==========================================
# Mock fallback (tanpa API key)
# ==========================================

def _mock_score(match_id: int, minute: int) -> tuple[int, int]:
    """Skor deterministik per laga: menit gol di-seed dari id laga."""
    rng = random.Random(f"mock-{match_id}")
    h_count = rng.randint(0, 4)
    a_count = rng.randint(0, 3)
    h_mins = sorted(rng.randint(1, 90) for _ in range(h_count))
    a_mins = sorted(rng.randint(1, 90) for _ in range(a_count))
    return (
        sum(1 for x in h_mins if x <= minute),
        sum(1 for x in a_mins if x <= minute),
    )


def _mock_matches() -> list[dict]:
    """Berdasarkan jadwal asli upcoming_fixtures.csv.

    LIVE HANYA jika kickoff benar-benar sudah lewat hari ini (<= 130 menit).
    FINISHED jika kickoff sudah lewat > 130 menit — skor deterministik dari _mock_score(id, 90).
    Selain itu status TIMED + jam kickoff WIB — tanpa skor palsu.
    """
    try:
        fx = pd.read_csv(UPCOMING_FIXTURES)
    except FileNotFoundError:
        return []
    if fx.empty or "date" not in fx.columns:
        return []

    fx = fx.copy()
    fx["dt"] = pd.to_datetime(fx["date"], errors="coerce", utc=True)
    fx = fx.dropna(subset=["dt"]).sort_values("dt")

    now = pd.Timestamp.now(tz="UTC")
    window = pd.Timedelta(minutes=130)  # 90' + HT + injury time
    fx["is_live"] = (fx["dt"] <= now) & (now < fx["dt"] + window)
    fx["is_finished"] = now >= fx["dt"] + window

    # Ambil: semua live + semua finished (max 50) + 5 upcoming terdekat
    live_rows = fx[fx["is_live"]]
    finished_rows = fx[fx["is_finished"]].tail(50)
    upcoming_rows = fx[~fx["is_live"] & ~fx["is_finished"]].head(5)
    picks = pd.concat([live_rows, finished_rows, upcoming_rows]).head(60)

    out = []
    for r in picks.itertuples():
        minute, status, hs, as_ = None, "TIMED", None, None
        if r.is_finished:
            minute = 90
            status = "FINISHED"
            hs, as_ = _mock_score(int(r.match_id), 90)
        elif r.is_live:
            minute = min(max(1, int((now - r.dt).total_seconds() // 60)), 90)
            status = "PAUSED" if 45 <= minute <= 60 else "IN_PLAY"
            hs, as_ = _mock_score(int(r.match_id), minute)
        out.append(
            {
                "id": int(r.match_id),
                "league": r.league,
                "competition": LEAGUE_TO_COMP.get(r.league, "CL"),
                "competition_name": LEAGUE_DISPLAY.get(r.league, r.league),
                "status": status,
                "live": status in LIVE_STATUSES,
                "minute": minute,
                "home": r.home_team,
                "away": r.away_team,
                "home_short": team_abbr(r.home_team),
                "away_short": team_abbr(r.away_team),
                "home_score": hs,
                "away_score": as_,
                "kickoff": r.dt.isoformat(),
                "kickoff_wib": _wib_str(r.dt),
                "crest_home": get_team_logo(r.home_team),
                "crest_away": get_team_logo(r.away_team),
            }
        )
    return out


# ==========================================
# Public API
# ==========================================

def get_live_matches(force: bool = False) -> dict:
    now = time.time()
    if not force and _CACHE["payload"] is not None and now - _CACHE["ts"] < CACHE_TTL:
        return _CACHE["payload"]

    source = "mock"
    error = None
    matches: list[dict] = []
    if API_KEY:
        try:
            matches = _fetch_api()
            source = "api"
        except Exception as e:  # rate limit / offline / salah key -> espn
            error = str(e)
            matches = []
    if source == "mock":
        try:
            matches = _fetch_espn()
            source = "espn"
        except Exception as e:
            error = f"{error or ''} | espn: {e}".strip(" |")
            matches = []
    if source == "mock":
        matches = _mock_matches()

    matches.sort(key=lambda m: (not m["live"], str(m.get("kickoff") or ""), str(m["id"])))
    payload = {
        "source": source,
        "error": error,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(matches),
        "live_count": sum(1 for m in matches if m["live"]),
        "matches": matches,
    }
    _CACHE["ts"] = now
    _CACHE["payload"] = payload
    return payload


def _resolve_team(name: str, table: dict) -> str:
    if name in table:
        return name
    folded = {k.casefold(): k for k in table}
    if name.casefold() in folded:
        return folded[name.casefold()]
    canon = canonical_team(name)
    if canon in table:
        return canon
    if canon.casefold() in folded:
        return folded[canon.casefold()]
    return name  # tim baru (promosi) — buat entri baru


def _zone(pos: int, total: int) -> str:
    if pos <= 4:
        return "UCL"
    if pos <= 6:
        return "UEL"
    if pos >= total - 2:
        return "REL"
    return "MID"


def get_live_standings(league_code: str) -> dict:
    if league_code not in LEAGUE_TO_COMP:
        raise ValueError(f"Liga '{league_code}' tidak dikenal.")

    live = get_live_matches()
    try:
        hist = pd.read_csv(HISTORICAL_MATCHES)
        league_hist = hist[hist["league"] == league_code]
    except FileNotFoundError:
        league_hist = pd.DataFrame(columns=["home_team", "away_team", "home_goals", "away_goals"])

    table = (
        _compute_actual_table(league_hist)
        if not league_hist.empty
        else {}
    )

    # Overlay skor live yang sedang berjalan (provisional, belum masuk histori)
    live_teams: set[str] = set()
    for m in live["matches"]:
        if m["league"] != league_code or not m["live"]:
            continue
        if m.get("home_score") is None or m.get("away_score") is None:
            continue
        h = _resolve_team(m["home"], table)
        a = _resolve_team(m["away"], table)
        for t, nm in ((h, m["home"]), (a, m["away"])):
            if t not in table:
                table[t] = {"P": 0, "PTS": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0}
        hg, ag = int(m["home_score"]), int(m["away_score"])
        hb, ab = table[h], table[a]
        hb["P"] += 1
        ab["P"] += 1
        hb["GF"] += hg
        hb["GA"] += ag
        ab["GF"] += ag
        ab["GA"] += hg
        if hg > ag:
            hb["PTS"] += 3
            hb["W"] += 1
            ab["L"] += 1
        elif ag > hg:
            ab["PTS"] += 3
            ab["W"] += 1
            hb["L"] += 1
        else:
            hb["PTS"] += 1
            ab["PTS"] += 1
            hb["D"] += 1
            ab["D"] += 1
        live_teams.update({h, a})

    for t in table:
        table[t]["GD"] = table[t]["GF"] - table[t]["GA"]

    rows = sorted(
        table.items(),
        key=lambda kv: (-kv[1]["PTS"], -kv[1]["GD"], -kv[1]["GF"], kv[0]),
    )
    total = len(rows)
    out = []
    for pos, (team, s) in enumerate(rows, 1):
        out.append(
            {
                "position": pos,
                "team": team,
                "abbr": team_abbr(team),
                "P": s["P"],
                "W": s["W"],
                "D": s["D"],
                "L": s["L"],
                "GF": s["GF"],
                "GA": s["GA"],
                "GD": s["GD"],
                "PTS": s["PTS"],
                "live": team in live_teams,
                "zone": _zone(pos, total),
                "logo": get_team_logo(team),
                "star_player": get_key_player(team),
            }
        )

    return {
        "league": league_code,
        "source": live["source"],
        "updated_at": live["fetched_at"],
        "table": out,
    }


def get_live_ucl() -> dict:
    live = get_live_matches()
    matches = [m for m in live["matches"] if m["league"] == "UCL"]
    return {
        "source": live["source"],
        "fetched_at": live["fetched_at"],
        "count": len(matches),
        "matches": matches,
    }
