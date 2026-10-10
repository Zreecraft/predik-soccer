"""Detail laga live: timeline gol/kartu/offside, line-up, statistik tim.

Sumber (mengikuti sumber laga di livescore):
  - espn → ESPN summary (gratis, tanpa API key): keyEvents + boxscore + rosters
  - api  → football-data.org v4: /matches/{id} (+ /lineups) — butuh API key
  - mock / tak dikenal → available=False (tidak disimulasikan)

Cache server-side TTL 60 detik per laga.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone

import requests

from livescore import API_BASE, API_KEY, ESPN_UID_TO_LEAGUE, get_live_matches
from team_aliases import canonical_team, team_key

CACHE_TTL = 60  # detik

# kode liga kita -> path liga ESPN
LEAGUE_TO_ESPN_PATH = {
    "EPL": "eng.1",
    "La_liga": "esp.1",
    "Serie_A": "ita.1",
    "Bundesliga": "ger.1",
    "UCL": "uefa.champions",
}

_ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/soccer/{path}/summary"
_ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

# pencarian laga berdasar nama tim (untuk laga yang sudah lewat dari jendela livescore)
SCAN_DAYS = 8  # H-7 .. H
_DAY_TTL = 600  # detik — scoreboard per hari jarang berubah setelah lewat
_RESOLVED_TTL = 24 * 3600  # id laga final tidak berubah

_DAY_CACHE: dict[str, tuple[float, list]] = {}
_RESOLVED: dict[str, tuple[float, dict]] = {}

# teks event ESPN -> tipe ternormalisasi
_TYPE_MAP = {
    "goal": "goal",
    "penalty-goal": "goal",
    "penalty": "goal",
    "own-goal": "own_goal",
    "yellow-card": "yellow",
    "second-yellow-card": "second_yellow",
    "yellow-red-card": "second_yellow",
    "red-card": "red",
    "substitution": "sub",
}

# nama statistik ESPN -> kunci kita
_STAT_MAP = {
    "yellowCards": "yellow_cards",
    "redCards": "red_cards",
    "offsides": "offsides",
    "foulsCommitted": "fouls",
    "possessionPct": "possession",
    "totalShots": "shots",
    "shotsOnTarget": "shots_on_target",
    "wonCorners": "corners",
    "saves": "saves",
}

_EMPTY_STATS = {
    "yellow_cards": 0,
    "red_cards": 0,
    "offsides": 0,
    "fouls": 0,
    "possession": 50,
    "shots": 0,
    "shots_on_target": 0,
    "corners": 0,
    "saves": 0,
}

# "James Justin (Leeds United) right footed shot …"
_PLAYER_RE = re.compile(
    r"([A-Z][A-Za-zÀ-ÿ'\-\.]+(?: [A-Z][A-Za-zÀ-ÿ'\-\.]+){0,3})\s*\(([^)]{2,40})\)"
)
_ASSIST_RE = re.compile(r"Assisted by\s+([^.]+?)(?:\s+with\b|\.|$)", re.IGNORECASE)
_SUB_RE = re.compile(
    r"Substitution,\s*[^.]+\.\s*([^.]+?)\s+replaces\s+([^.]+?)(?:\.|$)", re.IGNORECASE
)

_CACHE: dict[str, tuple[float, dict]] = {}


# ==========================================
# Util
# ==========================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _find_match(match_id) -> tuple[dict | None, str]:
    """Cari entri laga di cache livescore → (match, source)."""
    try:
        live = get_live_matches()
    except Exception:
        return None, "mock"
    src = live.get("source") or "mock"
    sid = str(match_id)
    for m in live.get("matches", []):
        if str(m.get("id")) == sid:
            return m, m.get("source") or src
    return None, src


def _first_player_team(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    m = _PLAYER_RE.search(text)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


def _side_of(team_name: str | None, home: str, away: str) -> str | None:
    if not team_name:
        return None
    from team_aliases import team_key

    tk = team_key(team_name)
    if tk == team_key(home):
        return "home"
    if tk == team_key(away):
        return "away"
    low = team_name.lower()
    if home.lower() in low or low in home.lower():
        return "home"
    if away.lower() in low or low in away.lower():
        return "away"
    return None


def _clean_stats(raw: dict | None) -> dict:
    out = dict(_EMPTY_STATS)
    for src, dst in _STAT_MAP.items():
        if not raw or src not in raw:
            continue
        val = raw[src]
        try:
            out[dst] = int(float(val))
        except (TypeError, ValueError):
            pass
    return out


def _espn_stat_map(statistics: list | None) -> dict:
    """ESPN boxscore statistics: [{name, displayValue}] → {name: value}."""
    out = {}
    for s in statistics or []:
        name = s.get("name")
        if not name:
            continue
        val = s.get("value")
        if val is None:
            val = s.get("displayValue")
        out[name] = val
    return out


# ==========================================
# ESPN summary
# ==========================================

def _parse_espn_summary(data: dict, match: dict) -> dict:
    home = match.get("home") or ""
    away = match.get("away") or ""
    hs, as_ = match.get("home_score"), match.get("away_score")

    # --- statistik tim (boxscore) ---
    stats = {"home": dict(_EMPTY_STATS), "away": dict(_EMPTY_STATS)}
    for t in (data.get("boxscore") or {}).get("teams") or []:
        side = t.get("homeAway")
        if side in ("home", "away"):
            stats[side] = _clean_stats(_espn_stat_map(t.get("statistics")))

    # skor: boxscore tidak selalu punya "score" → fallback ke header.competitions
    if hs is None or as_ is None:
        comp = ((data.get("header") or {}).get("competitions") or [{}])[0]
        for c in comp.get("competitors") or []:
            side = c.get("homeAway")
            raw = c.get("score")
            try:
                val = int(raw) if raw is not None and str(raw).strip() != "" else None
            except (TypeError, ValueError):
                val = None
            if side == "home" and hs is None:
                hs = val
            elif side == "away" and as_ is None:
                as_ = val
    if match.get("swapped"):
        hs, as_ = as_, hs
        stats["home"], stats["away"] = stats["away"], stats["home"]

    # --- timeline (keyEvents) ---
    timeline: list[dict] = []
    for ev in data.get("keyEvents") or []:
        t = (ev.get("type") or {})
        etype = _TYPE_MAP.get((t.get("type") or "").lower())
        if not etype:
            continue
        text = ev.get("text") or ""
        clock = ev.get("clock") or {}
        minute_str = clock.get("displayValue") or None
        try:
            minute_num = int(clock.get("value") // 60) if clock.get("value") is not None else None
        except TypeError:
            minute_num = None
        period = (ev.get("period") or {}).get("number")

        player, team_name = _first_player_team(text)
        entry = {
            "type": etype,
            "minute": minute_str or (f"{minute_num}'" if minute_num is not None else None),
            "minute_num": minute_num,
            "period": period,
            "team": team_name,
            "side": _side_of(team_name, home, away),
            "player": player,
            "assist": None,
            "detail": text or None,
        }
        if etype == "goal":
            am = _ASSIST_RE.search(text)
            if am:
                entry["assist"] = am.group(1).strip().rstrip(".")
            if t.get("type") == "own-goal" or "own goal" in text.lower():
                entry["type"] = "own_goal"
        elif etype == "sub":
            sm = _SUB_RE.search(text)
            if sm:
                entry["player"] = sm.group(1).strip()   # pemain masuk
                entry["player_out"] = sm.group(2).strip()
                # tim dari "Substitution, Arsenal."
                tm = re.match(r"Substitution,\s*([^.]+)\.", text)
                if tm:
                    entry["team"] = tm.group(1).strip()
                    entry["side"] = _side_of(entry["team"], home, away)
        timeline.append(entry)

    timeline.sort(key=lambda e: (e.get("period") or 0, e.get("minute_num") or 0))

    # --- line-up (rosters) ---
    lineups: dict[str, dict] = {}
    for r in data.get("rosters") or []:
        side = r.get("homeAway")
        if side not in ("home", "away"):
            continue
        starters, subs = [], []
        for p in r.get("roster") or []:
            ath = p.get("athlete") or {}
            pos = (ath.get("position") or {}).get("name") or (p.get("position") or {}).get("name")
            item = {
                "name": ath.get("displayName") or ath.get("shortName"),
                "number": p.get("jersey") or ath.get("jersey"),
                "position": pos,
                "headshot": ath.get("headshot"),
            }
            if p.get("starter"):
                starters.append(item)
            elif p.get("active") is not False or p.get("subbedIn") is not None:
                subs.append(item)
        lineups[side] = {
            "formation": r.get("formation"),
            "coach": None,
            "starters": starters,
            "substitutes": subs,
        }

    if match.get("swapped") and ("home" in lineups or "away" in lineups):
        lineups["home"], lineups["away"] = lineups.get("away"), lineups.get("home")

    return {
        "home_score": hs,
        "away_score": as_,
        "timeline": timeline,
        "stats": stats,
        "lineups": lineups,
    }


def _fetch_espn_summary(event_id: str, league: str) -> dict:
    path = LEAGUE_TO_ESPN_PATH.get(league)
    if not path:
        raise ValueError(f"Liga '{league}' tidak didukung ESPN summary.")
    resp = requests.get(_ESPN_SUMMARY.format(path=path), params={"event": event_id}, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ==========================================
# football-data.org v4
# ==========================================

def _fd_minute(m: dict):
    st = m.get("status") or ""
    if st in ("IN_PLAY", "PAUSED"):
        return m.get("minute")
    if st == "FINISHED":
        return 90
    return None


def _fetch_fd_detail(match_id: str) -> dict:
    if not API_KEY:
        raise RuntimeError("FOOTBALL_DATA_API_KEY belum diset.")
    headers = {"X-Auth-Token": API_KEY}

    resp = requests.get(f"{API_BASE}/matches/{match_id}", headers=headers, timeout=12)
    resp.raise_for_status()
    m = resp.json()

    home = ((m.get("homeTeam") or {}).get("name")
            or (m.get("homeTeam") or {}).get("shortName") or "")
    away = ((m.get("awayTeam") or {}).get("name")
            or (m.get("awayTeam") or {}).get("shortName") or "")
    ft = (m.get("score") or {}).get("fullTime") or {}

    timeline: list[dict] = []
    for g in m.get("goals") or []:
        gtype = (g.get("type") or "REGULAR").upper()
        tname = (g.get("team") or {}).get("name")
        timeline.append({
            "type": "own_goal" if gtype == "OWN_GOAL" else "goal",
            "minute": f"{g.get('minute')}'" if g.get("minute") is not None else None,
            "minute_num": g.get("minute"),
            "period": None,
            "team": tname,
            "side": _side_of(tname, home, away),
            "player": g.get("player"),
            "assist": None,
            "detail": "Gol penalti" if gtype == "PENALTY" else None,
        })
    for b in m.get("bookings") or []:
        card = (b.get("card") or "").upper()
        if card == "YELLOW_CARD":
            etype = "yellow"
        elif card == "YELLOW_RED":
            etype = "second_yellow"
        elif card == "RED_CARD":
            etype = "red"
        else:
            continue
        tname = (b.get("team") or {}).get("name")
        timeline.append({
            "type": etype,
            "minute": f"{b.get('minute')}'" if b.get("minute") is not None else None,
            "minute_num": b.get("minute"),
            "period": None,
            "team": tname,
            "side": _side_of(tname, home, away),
            "player": b.get("player"),
            "assist": None,
            "detail": None,
        })
    for s in m.get("substitutions") or []:
        tname = (s.get("team") or {}).get("name")
        timeline.append({
            "type": "sub",
            "minute": f"{s.get('minute')}'" if s.get("minute") is not None else None,
            "minute_num": s.get("minute"),
            "period": None,
            "team": tname,
            "side": _side_of(tname, home, away),
            "player": (s.get("playerIn") or {}).get("name"),
            "player_out": (s.get("playerOut") or {}).get("name"),
            "assist": None,
            "detail": None,
        })
    timeline.sort(key=lambda e: e.get("minute_num") or 0)

    # agregat statistik dari timeline (football-data tidak selalu memberi boxscore)
    def _count(side: str | None, *types: str) -> int:
        return sum(1 for e in timeline if e.get("side") == side and e["type"] in types)

    stats = {"home": dict(_EMPTY_STATS), "away": dict(_EMPTY_STATS)}
    for side in ("home", "away"):
        stats[side]["yellow_cards"] = _count(side, "yellow", "second_yellow")
        stats[side]["red_cards"] = _count(side, "red", "second_yellow")
        stats[side]["possession"] = 50

    # line-up
    lineups: dict[str, dict] = {}
    try:
        lr = requests.get(f"{API_BASE}/matches/{match_id}/lineups", headers=headers, timeout=12)
        lr.raise_for_status()
        for block in lr.json().get("lineups") or []:
            # football-data tidak menandai home/away eksplisit — cocokkan nama tim
            tname = (block.get("team") or {}).get("name") or ""
            side = _side_of(tname, home, away)
            if side not in ("home", "away"):
                continue

            def _pl(p: dict) -> dict:
                return {
                    "name": p.get("name"),
                    "number": p.get("shirtNumber"),
                    "position": p.get("position"),
                    "headshot": None,
                }

            lineups[side] = {
                "formation": block.get("formation"),
                "coach": (block.get("coach") or {}).get("name"),
                "starters": [_pl(x.get("player") or {}) for x in block.get("startXI") or []],
                "substitutes": [_pl(x.get("player") or {}) for x in block.get("substitutes") or []],
            }
    except Exception:
        lineups = {}

    return {
        "home": home,
        "away": away,
        "home_score": ft.get("home"),
        "away_score": ft.get("away"),
        "minute": _fd_minute(m),
        "timeline": timeline,
        "stats": stats,
        "lineups": lineups,
    }


# ==========================================
# Resolusi laga dari nama tim (jendela livescore terlalu sempit)
# ==========================================

def _same_team(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    ka, kb = team_key(a), team_key(b)
    if ka == kb:
        return True
    # toleransi singkatan: "leeds" vs "leeds united", "manchester" vs ...
    ta, tb = set(ka.split()), set(kb.split())
    if len(ta) == 1 and next(iter(ta)) in kb:
        return True
    if len(tb) == 1 and next(iter(tb)) in ka:
        return True
    return False


def _scan_events_day(day: str) -> list[dict]:
    """Daftar laga ESPN (semua liga kita) untuk satu tanggal YYYYMMDD."""
    hit = _DAY_CACHE.get(day)
    if hit and time.time() - hit[0] < _DAY_TTL:
        return hit[1]
    resp = requests.get(_ESPN_SCOREBOARD, params={"dates": day, "limit": 1000}, timeout=15)
    resp.raise_for_status()
    out: list[dict] = []
    for ev in resp.json().get("events") or []:
        comps = ev.get("competitions") or []
        competitors = (comps[0].get("competitors") or []) if comps else []
        home_c = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away_c = next((c for c in competitors if c.get("homeAway") == "away"), {})
        ht = home_c.get("team") or {}
        at = away_c.get("team") or {}
        m = re.search(r"l:(\d+)", ev.get("uid") or "")
        league = ESPN_UID_TO_LEAGUE.get(m.group(1)) if m else None
        if not league:
            continue
        st = (ev.get("status") or {}).get("type") or {}
        state = st.get("state") or "pre"
        status = "FINISHED" if state == "post" else "IN_PLAY" if state == "in" else "TIMED"
        out.append({
            "id": ev.get("id"),
            "league": league,
            "competition_name": {
                "EPL": "Premier League", "La_liga": "La Liga", "Serie_A": "Serie A",
                "Bundesliga": "Bundesliga", "UCL": "Champions League",
            }.get(league, league),
            "status": status,
            "live": status in ("IN_PLAY", "PAUSED"),
            "minute": None,
            "home": ht.get("displayName") or ht.get("shortDisplayName") or "",
            "away": at.get("displayName") or at.get("shortDisplayName") or "",
            "home_short": ht.get("abbreviation"),
            "away_short": at.get("abbreviation"),
            "home_score": None,
            "away_score": None,
            "crest_home": ht.get("logo"),
            "crest_away": at.get("logo"),
        })
    _DAY_CACHE[day] = (time.time(), out)
    return out


def _resolve_by_name(home: str, away: str, league: str | None = None) -> dict | None:
    """Cari id laga ESPN dari pasangan nama tim (scan 8 hari terakhir, terbaru dulu)."""
    pair = f"{team_key(home)}|{team_key(away)}|{league or ''}"
    hit = _RESOLVED.get(pair)
    if hit and time.time() - hit[0] < _RESOLVED_TTL:
        return hit[1]

    now = datetime.now(timezone.utc)
    for offset in range(0, -SCAN_DAYS, -1):
        day = (now + timedelta(days=offset)).strftime("%Y%m%d")
        try:
            events = _scan_events_day(day)
        except Exception:
            continue
        for ev in events:
            if league and ev["league"] != league:
                continue
            if _same_team(ev["home"], home) and _same_team(ev["away"], away):
                _RESOLVED[pair] = (time.time(), ev)
                return ev
        # urutan terbalik (kandang/tandang dijadwalkan berbeda) → balikkan label
        for ev in events:
            if league and ev["league"] != league:
                continue
            if _same_team(ev["home"], away) and _same_team(ev["away"], home):
                swapped = {
                    **ev,
                    "swapped": True,
                    "home": away, "away": home,
                    "home_short": ev.get("away_short"), "away_short": ev.get("home_short"),
                    "crest_home": ev.get("crest_away"), "crest_away": ev.get("crest_home"),
                }
                _RESOLVED[pair] = (time.time(), swapped)
                return swapped
    return None


# ==========================================
# Public API
# ==========================================

def get_match_detail(match_id=None, home: str | None = None, away: str | None = None,
                     league: str | None = None, force: bool = False) -> dict:
    """Detail laga (timeline + statistik + line-up).

    Lookup:
      1. id laga di cache livescore (H-2..H)
      2. fallback: resolve id ESPN dari nama tim (scan scoreboard 7 hari terakhir)
    """
    key = str(match_id) if match_id else f"pair:{team_key(home or '')}|{team_key(away or '')}"
    now = time.time()
    if not force and key in _CACHE and now - _CACHE[key][0] < CACHE_TTL:
        return _CACHE[key][1]

    match, live_source = (None, None)
    if match_id:
        match, live_source = _find_match(match_id)
    if match is None and home and away:
        resolved = _resolve_by_name(home, away, league)
        if resolved:
            match, live_source = resolved, "espn"
            match_id = resolved["id"]
    # key bisa berubah setelah resolusi nama → id ESPN
    key = str(match_id) if match_id else key

    base = {
        "available": False,
        "source": None,
        "reason": None,
        "match_id": match_id,
        "home": match.get("home") if match else None,
        "away": match.get("away") if match else None,
        "home_short": match.get("home_short") if match else None,
        "away_short": match.get("away_short") if match else None,
        "home_score": match.get("home_score") if match else None,
        "away_score": match.get("away_score") if match else None,
        "status": match.get("status") if match else None,
        "minute": match.get("minute") if match else None,
        "competition_name": match.get("competition_name") if match else None,
        "crest_home": match.get("crest_home") if match else None,
        "crest_away": match.get("crest_away") if match else None,
        "timeline": [],
        "scorers": {"home": [], "away": []},
        "stats": None,
        "lineups": None,
        "fetched_at": _now_iso(),
    }

    if match is None:
        base["reason"] = "not_found"
        return base

    base["source"] = live_source
    src = match.get("source") or live_source or "mock"
    if src == "mock":
        # sesuai kebijakan: jangan tampilkan event simulasi
        base["reason"] = "mock"
        return base

    try:
        if src == "api":
            detail = _fetch_fd_detail(key)
            base.update({
                "available": True,
                "source": "api",
                "timeline": detail["timeline"],
                "stats": detail["stats"],
                "lineups": detail["lineups"] or None,
                "home_score": detail["home_score"] if detail["home_score"] is not None else base["home_score"],
                "away_score": detail["away_score"] if detail["away_score"] is not None else base["away_score"],
                "minute": detail.get("minute") or base["minute"],
            })
        else:  # espn
            data = _fetch_espn_summary(key, match.get("league") or "")
            parsed = _parse_espn_summary(data, match)
            base.update({
                "available": True,
                "source": "espn",
                "timeline": parsed["timeline"],
                "stats": parsed["stats"],
                "lineups": parsed["lineups"] or None,
                "home_score": parsed["home_score"],
                "away_score": parsed["away_score"],
            })
    except Exception as e:
        base["reason"] = f"fetch_error: {e}"
        _CACHE[key] = (now, base)
        return base

    # agregat pencetak gol
    for ev in base["timeline"]:
        if ev["type"] in ("goal", "own_goal") and ev.get("side") in ("home", "away"):
            base["scorers"][ev["side"]].append({
                "player": ev.get("player"),
                "minute": ev.get("minute"),
                "own_goal": ev["type"] == "own_goal",
            })

    base["fetched_at"] = _now_iso()
    _CACHE[key] = (now, base)
    return base
