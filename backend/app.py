import functools
import json
import re
import threading
import time
import unicodedata
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from assets import get_key_player, get_team_logo
from club_analytics import get_club_analytics, LEAGUE_NAMES
from club_data import ga_prior_from_rating, get_club_profile, get_club_strength, xg_prior_from_rating
from data_paths import (
    HISTORICAL_MATCHES,
    REAL_SHOTS_DATA,
    UPCOMING_FIXTURES,
    filter_current_season,
    AUTO_LEARN,
    AUTO_EVAL_INTERVAL_H,
    AUTO_RETRAIN_INTERVAL_H,
)
import livescore
import match_detail
from run_prediction import calculate_smart_projected_score, simulate_10k_matches_minute_by_minute
from season_projection import project_league
from team_aliases import team_abbr, team_key
from team_analytics import clamp_match_xg, get_home_away_bias, get_team_form, get_team_power_index
from ucl_simulator import simulate_ucl_tournament

app = FastAPI(title="Analytica FC API", version="2.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SHOTS_CACHE = None
_SHOTS_CACHE_MTIME = None
_UCL_CACHE = None


def _load_shots() -> pd.DataFrame | None:
    global _SHOTS_CACHE, _SHOTS_CACHE_MTIME
    try:
        mtime = REAL_SHOTS_DATA.stat().st_mtime
    except OSError:
        mtime = None
    if _SHOTS_CACHE is None or mtime != _SHOTS_CACHE_MTIME:
        try:
            _SHOTS_CACHE = pd.read_csv(REAL_SHOTS_DATA)
        except FileNotFoundError:
            _SHOTS_CACHE = pd.DataFrame()
        _SHOTS_CACHE_MTIME = mtime
    return _SHOTS_CACHE


def _outcome(hg: int, ag: int) -> str:
    if hg > ag: return "home"
    if hg == ag: return "draw"
    return "away"

def _finished_verdict(actual_h: int, actual_a: int, source: str,
                      pred_h: int, pred_a: int, home_team: str, away_team: str) -> dict:
    """Bangun verdict akhir. `correct` = skor TEPAT (bukan cuma outcome)."""
    pred_outcome = _outcome(pred_h, pred_a)
    actual_outcome = _outcome(actual_h, actual_a)
    exact = pred_h == actual_h and pred_a == actual_a
    if source in ("espn", "api", "understat"):  # data asli -> evaluasi model
        try:
            from database import get_db
            db = get_db()
            db.execute(
                "UPDATE prediction_logs SET actual_home_goals=?, actual_away_goals=?, status='EVALUATED' "
                "WHERE home_team=? AND away_team=? AND status='PENDING'",
                (actual_h, actual_a, home_team, away_team),
            )
            db.commit()
            db.close()
        except Exception:
            pass
    return {
        "status": "finished",
        "actual_home": actual_h,
        "actual_away": actual_a,
        "actual_outcome": actual_outcome,
        "predicted_outcome": pred_outcome,
        "exact": exact,
        "outcome_correct": pred_outcome == actual_outcome,
        "correct": exact,
        "predicted_score": f"{pred_h}-{pred_a}",
        "actual_score": f"{actual_h}-{actual_a}",
        "source": source,
    }

def _match_result(home_team: str, away_team: str,
                  pred_h: int, pred_a: int,
                  prob_h: float, prob_d: float, prob_a: float) -> dict:
    """Cek hasil laga. Prioritas: data ASLI (ESPN/football-data) -> historical
    Understat (guard tanggal) -> jendela kickoff (live/mock fallback)."""
    from team_aliases import team_key
    hk, ak = team_key(home_team), team_key(away_team)

    def _same(m_home, m_away):
        return team_key(m_home) == hk and team_key(m_away) == ak

    # 1. Data ASLI dari live API (ESPN tanpa key / football-data.org dengan key)
    try:
        live = livescore.get_live_matches()
        src = live.get("source", "mock")
        for m in live.get("matches", []):
            if not _same(m.get("home") or "", m.get("away") or ""):
                continue
            if m.get("live") and m.get("home_score") is not None:
                return {
                    "status": "live",
                    "actual_home": m.get("home_score"),
                    "actual_away": m.get("away_score"),
                    "minute": m.get("minute"),
                    "predicted_score": f"{pred_h}-{pred_a}",
                    "source": src,
                }
            if m.get("status") == "FINISHED" and m.get("home_score") is not None:
                return _finished_verdict(int(m["home_score"]), int(m["away_score"]),
                                         src, pred_h, pred_a, home_team, away_team)
    except Exception:
        pass

    # 2. Historical Understat (skor asli) — wajib satu laga dengan fixture (±1 hari)
    try:
        hist = pd.read_csv(HISTORICAL_MATCHES)
        hmask = [_same(r.home_team, r.away_team) for r in hist.itertuples()]
        matches = hist[hmask]
        if not matches.empty:
            fx_date = None
            try:
                fx = pd.read_csv(UPCOMING_FIXTURES)
                fmask = [_same(r.home_team, r.away_team) for r in fx.itertuples()]
                frows = fx[fmask]
                if not frows.empty:
                    fx_date = pd.Timestamp(frows.sort_values("date").iloc[-1]["date"])
                    if fx_date.tzinfo is None:
                        fx_date = fx_date.tz_localize("UTC")
            except Exception:
                pass
            cand = matches.sort_values("datetime")
            if fx_date is not None:
                dts = pd.to_datetime(cand["datetime"], errors="coerce", utc=True)
                near = cand[(dts - fx_date).abs() <= pd.Timedelta(days=1)]
                cand = near
            if not cand.empty:
                latest = cand.iloc[-1]
                return _finished_verdict(int(latest["home_goals"]), int(latest["away_goals"]),
                                         "understat", pred_h, pred_a, home_team, away_team)
    except FileNotFoundError:
        pass

    # 3. Jendela kickoff (fallback: live/mock dari fixtures lokal)
    try:
        fx = pd.read_csv(UPCOMING_FIXTURES)
        fmask = [_same(r.home_team, r.away_team) for r in fx.itertuples()]
        row = fx[fmask]
        if not row.empty:
            latest = row.sort_values("date").iloc[-1]
            kickoff = pd.Timestamp(latest["date"])
            if kickoff.tzinfo is None:
                kickoff = kickoff.tz_localize("UTC")
            now = pd.Timestamp.now(tz="UTC")
            elapsed = (now - kickoff).total_seconds() / 60

            if elapsed < 0:
                return {"status": "upcoming"}  # belum kickoff

            src = "mock"
            try:
                src = livescore.get_live_matches().get("source", "mock")
            except Exception:
                pass

            if elapsed <= 130:
                # sedang live — skor dari livescore bila ada, tanpa skor jika tidak
                out = {"status": "live", "predicted_score": f"{pred_h}-{pred_a}", "source": src}
                try:
                    live = livescore.get_live_matches()
                    for m in live.get("matches", []):
                        if _same(m.get("home") or "", m.get("away") or "") and m.get("live"):
                            out.update({
                                "actual_home": m.get("home_score"),
                                "actual_away": m.get("away_score"),
                                "minute": m.get("minute"),
                            })
                            break
                except Exception:
                    pass
                if "actual_home" not in out and src == "mock":
                    from livescore import _mock_score
                    hs, as_ = _mock_score(int(latest["match_id"]),
                                          min(max(1, int(elapsed)), 90))
                    out.update({"actual_home": hs, "actual_away": as_})
                return out

            # finished — coba skor livescore (mock terakhir), verdict tetap dilabeli sumbernya
            try:
                live = livescore.get_live_matches()
                for m in live.get("matches", []):
                    if (_same(m.get("home") or "", m.get("away") or "")
                            and m.get("status") == "FINISHED"
                            and m.get("home_score") is not None):
                        return _finished_verdict(int(m["home_score"]), int(m["away_score"]),
                                                 live.get("source", "mock"),
                                                 pred_h, pred_a, home_team, away_team)
            except Exception:
                pass
            try:
                from livescore import _mock_score
                ah, aa = _mock_score(int(latest["match_id"]), 90)
                return _finished_verdict(ah, aa, "mock", pred_h, pred_a, home_team, away_team)
            except Exception:
                pass
    except FileNotFoundError:
        pass

    return {"status": "upcoming"}


def _team_shot_summary(team: str, shots_df: pd.DataFrame) -> dict:
    from team_aliases import alias_variants

    variants = {v.lower() for v in alias_variants(team)}
    team_shots = shots_df[shots_df["team_name"].astype(str).str.lower().isin(variants)]
    if team_shots.empty:
        return {
            "shots": 0, "goals": 0, "xg": 0.0, "conversion_pct": 0.0,
            "zone14_shots": 0, "zone14_pct": 0.0, "on_target_pct": 0.0,
            "points": [],
        }
    shots = len(team_shots)
    goals = int((team_shots["result"] == "Goal").sum())
    xg = float(team_shots["xG"].sum())
    z14 = int(((team_shots["X"] >= 0.72) & (team_shots["X"] < 0.88) & (team_shots["Y"] >= 0.35) & (team_shots["Y"] <= 0.65)).sum())
    on_target = int(team_shots["result"].isin(["Goal", "SavedShot"]).sum())
    points = []
    for _, s in team_shots.iterrows():
        points.append({
            "x": round(float(s["X"]), 4),
            "y": round(float(s["Y"]), 4),
            "xg": round(float(s["xG"]), 4),
            "result": str(s["result"]),
            "minute": int(s["minute"]) if pd.notna(s.get("minute")) else None,
            "player": str(s.get("player", "")),
        })
    return {
        "shots": shots,
        "goals": goals,
        "xg": round(xg, 2),
        "conversion_pct": round(goals / shots * 100, 1) if shots else 0.0,
        "zone14_shots": z14,
        "zone14_pct": round(z14 / shots * 100, 1) if shots else 0.0,
        "on_target_pct": round(on_target / shots * 100, 1) if shots else 0.0,
        "points": points,
    }


def _tactical_metrics(team: str, power: dict, shots_summary: dict, shots_against_xg: float) -> dict:
    """Metrik taktis model (turunan data + heuristik berlabel model)."""
    avg_xg = power.get("avg_xg", 1.2)
    avg_ga = power.get("avg_ga", 1.2)
    win_rate = power.get("win_rate", 45.0)
    conversion = shots_summary.get("conversion_pct", 10.0)
    # PPDA proxy: makin banyak gol kebobolan vs xG for, makin longgar press
    ppda = round(float(np.clip(12.0 - (avg_xg - avg_ga) * 2.5 - (win_rate - 45) * 0.04, 6.5, 17.5)), 1)
    # Duel / ball recovery proxy
    duels = round(float(np.clip(48 + (avg_xg - 1.2) * 8 + (50 - avg_ga) * 3, 40, 62)), 1)
    possession = round(float(np.clip(46 + (avg_xg - 1.2) * 10 + (win_rate - 45) * 0.15, 35, 64)), 1)
    return {
        "xg": round(avg_xg, 2),
        "conversion_pct": conversion,
        "ppda": ppda,
        "duels_pct": duels,
        "possession_pct": possession,
        "win_rate": win_rate,
        "avg_ga": avg_ga,
        "shots_against_xg": round(shots_against_xg, 2),
    }


def _differential_summary(home_team: str, away_team: str, home_t: dict, away_t: dict, home_xg: float, away_xg: float) -> str:
    xg_diff = home_xg - away_xg
    ppda_diff = home_t["ppda"] - away_t["ppda"]
    parts = []
    if abs(xg_diff) >= 0.35:
        leader = home_team if xg_diff > 0 else away_team
        parts.append(f"{leader} unggul proyeksi xG ({max(home_xg, away_xg):.2f} vs {min(home_xg, away_xg):.2f}).")
    else:
        parts.append("Proyeksi xG kedua tim relatif seimbang.")
    if abs(ppda_diff) >= 1.2:
        press_team = home_team if ppda_diff < 0 else away_team
        parts.append(f"{press_team} menekan lebih agresif (PPDA {min(home_t['ppda'], away_t['ppda']):.1f}).")
    else:
        parts.append("Intensitas press kedua tim setara.")
    conv_leader = home_team if home_t["conversion_pct"] >= away_t["conversion_pct"] else away_team
    parts.append(f"{conv_leader} lebih efisien mengubah peluang ({max(home_t['conversion_pct'], away_t['conversion_pct']):.1f}% conversion).")
    if xg_diff > 0.2:
        parts.append(f"Kendali territorial condong ke {home_team} di sepertiga akhir.")
    elif xg_diff < -0.2:
        parts.append(f"Kendali territorial condong ke {away_team} di sepertiga akhir.")
    else:
        parts.append("Pertarungan zona 14 diprediksi ketat.")
    return " ".join(parts)


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Analytica FC API"}


@app.get("/api/leagues")
def get_leagues():
    return [
        {"id": "EPL", "name": "English Premier League", "country": "England"},
        {"id": "La_liga", "name": "La Liga", "country": "Spain"},
        {"id": "Serie_A", "name": "Serie A", "country": "Italy"},
        {"id": "Bundesliga", "name": "Bundesliga", "country": "Germany"},
    ]


@app.get("/api/fixtures/{league_code}")
def get_fixtures(league_code: str, limit: int = 40):
    try:
        df = pd.read_csv(UPCOMING_FIXTURES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="File upcoming_fixtures.csv belum ditemukan.")

    filtered = df[df["league"] == league_code].head(limit).to_dict(orient="records")
    if not filtered:
        raise HTTPException(status_code=404, detail=f"Tidak ada jadwal untuk liga '{league_code}'.")

    for fix in filtered:
        fix["home_logo"] = get_team_logo(fix["home_team"])
        fix["away_logo"] = get_team_logo(fix["away_team"])
        fix["home_star_player"] = get_key_player(fix["home_team"])
        fix["away_star_player"] = get_key_player(fix["away_team"])
        date_str = str(fix.get("date", ""))
        fix["date_short"] = date_str[:16] if date_str else ""

    return {
        "league": league_code,
        "league_name": LEAGUE_NAMES.get(league_code, league_code),
        "total": len(filtered),
        "fixtures": filtered,
    }


@app.get("/api/ticker")
def get_ticker(limit: int = 16):
    """Ringkasan pekan aktif untuk navbar ticker."""
    try:
        df = pd.read_csv(UPCOMING_FIXTURES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="File upcoming_fixtures.csv belum ditemukan.")

    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date_dt"]).sort_values("date_dt").head(limit)

    items = []
    for _, row in df.iterrows():
        items.append({
            "home": row["home_team"],
            "away": row["away_team"],
            "home_short": team_abbr(row["home_team"]),
            "away_short": team_abbr(row["away_team"]),
            "date": str(row["date"])[:16],
            "league": row["league"],
        })
    return {"items": items, "total": len(items)}


# ==========================================
# SCHEDULE: jadwal terpadu (live/hari ini, mendatang, hasil selesai)
# ==========================================

SCHEDULE_WINDOW_MIN = 130  # 90' + HT + injury time

_DT_FMTS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S")


def _wib_dt(val):
    """Parse date string laga → datetime naive (UTC+7) utk cek "hari ini".

    Strptime dgn format umum (~µs) menggantikan pd.to_datetime yang menebak format
    (per baris ≈ 8 ms — total ~85% waktu get_schedule). Format tak dikenal →
    fallback pd.to_datetime (jarang; hasil identik). None/NaT → None.
    """
    if val is None:
        return None
    if isinstance(val, str):
        for fmt in _DT_FMTS:
            try:
                return datetime.strptime(val, fmt) + timedelta(hours=7)
            except ValueError:
                continue
    try:
        d = pd.to_datetime(val, errors="coerce", utc=True)
    except Exception:
        return None
    if pd.isna(d):
        return None
    return (d + pd.Timedelta(hours=7)).to_pydatetime()


@functools.lru_cache(maxsize=4096)
def _fuzzy_key(name) -> str:
    """Kunci normalisasi nama tim untuk join antar sumber data (buang aksen).

    Memoized: fungsi murni, dipanggil ribuan kali per request (nama tim berulang).
    """
    s = unicodedata.normalize("NFD", str(name or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", team_key(s).lower())


_ACTUAL_HIST_CACHE: dict | None = None
_ACTUAL_HIST_MTIME = None


def _historical_actual_scores() -> dict:
    """Skor asli dari historical_matches.csv, di-cache per mtime file.

    File ~11.007 baris; tanpa cache + to_datetime per baris, fungsi ini memakan
    ~20 detik PER REQUEST (biang lambatnya /api/schedule).
    """
    global _ACTUAL_HIST_CACHE, _ACTUAL_HIST_MTIME
    try:
        mtime = HISTORICAL_MATCHES.stat().st_mtime
    except OSError:
        mtime = None
    if _ACTUAL_HIST_CACHE is not None and mtime == _ACTUAL_HIST_MTIME:
        return _ACTUAL_HIST_CACHE

    out: dict = {}
    try:
        hist = pd.read_csv(HISTORICAL_MATCHES)
        hg = pd.to_numeric(hist["home_goals"], errors="coerce")
        ag = pd.to_numeric(hist["away_goals"], errors="coerce")
        # Vektorisasi: SATU panggilan to_datetime utk seluruh kolom (~7 ms),
        # bukan per baris (~4 dtk) — anti-pattern pandas paling mahal di endpoint ini.
        dts = pd.to_datetime(hist["datetime"], errors="coerce", utc=True)
        keep = hg.notna() & ag.notna() & dts.notna()
        for h, a, ts, g_h, g_a in zip(hist.loc[keep, "home_team"],
                                      hist.loc[keep, "away_team"],
                                      dts[keep], hg[keep], ag[keep]):
            out.setdefault((_fuzzy_key(h), _fuzzy_key(a)), []).append(
                (ts, int(g_h), int(g_a), "understat"))
    except Exception:
        pass
    for v in out.values():
        v.sort(key=lambda e: (pd.isna(e[0]), e[0]))
    _ACTUAL_HIST_CACHE = out
    _ACTUAL_HIST_MTIME = mtime
    return out


def _schedule_actual_scores() -> dict:
    """Skor asli per pasangan tim → list entri bertanggal [(dt, hg, ag, source)].

    Dipakai _resolve_schedule_actual() yang memilih entri paling dekat dengan
    kickoff laga — penting karena satu pasangan bisa main banyak kali lintas musim.

    Bagian historical dari cache mtime; entri live di-merge per request
    (list milik cache TIDAK pernah dimutasi → selalu di-salin dulu).
    """
    out: dict = dict(_historical_actual_scores())
    try:
        live = livescore.get_live_matches()
        if live.get("source") in ("espn", "api"):
            for m in live.get("matches", []):
                if m.get("status") == "FINISHED" and m.get("home_score") is not None:
                    pair = (_fuzzy_key(m.get("home")), _fuzzy_key(m.get("away")))
                    try:
                        ts = pd.to_datetime(m.get("kickoff"), errors="coerce", utc=True)
                    except Exception:
                        ts = pd.NaT
                    try:
                        entry = (ts, int(m["home_score"]), int(m["away_score"]),
                                 live["source"])
                    except (TypeError, ValueError):
                        continue
                    cached = out.get(pair)
                    if cached is None:
                        out[pair] = [entry]
                    else:
                        merged = list(cached) + [entry]
                        merged.sort(key=lambda e: (pd.isna(e[0]), e[0]))
                        out[pair] = merged
    except Exception:
        pass
    return out


def _as_utc_ts(val) -> pd.Timestamp:
    """Ke Timestamp UTC tanpa menebak format (strptime utk format umum ~µs).

    pd.to_datetime dgn format-guessing per string ≈ 0,8 ms — dipanggil per laga
    di dua resolver bawah. String dianggap UTC (sama dgn pd.to_datetime utc=True).
    """
    if isinstance(val, pd.Timestamp):
        return val if val.tz is not None else val.tz_localize("UTC")
    if isinstance(val, str):
        for fmt in _DT_FMTS:
            try:
                return pd.Timestamp(datetime.strptime(val, fmt)).tz_localize("UTC")
            except ValueError:
                continue
    try:
        return pd.to_datetime(val, errors="coerce", utc=True)
    except Exception:
        return pd.NaT


def _resolve_schedule_actual(actual_map: dict, pair, kickoff_dt, tol_hours: float = 96.0):
    """Pilih skor asli untuk SATU laga: entri dengan tanggal paling dekat kickoff.

    - tol_hours (default 4 hari): di luar ambang ini dianggap bukan laga yang sama
      (mis. historical lintas musim) → None, jangan tampilkan skor asli yang salah.
    - Sumber asli (ESPN/api) menang bila berbagi tanggal yang sama dengan understat.
    - kickoff tidak valid → pakai entri terakhir (understat terbaru).
    """
    entries = actual_map.get(pair)
    if not entries:
        return None

    def _fallback():
        ts, hg, ag, src = entries[-1]
        return None if pd.isna(ts) else (hg, ag, src)

    if kickoff_dt is None or pd.isna(kickoff_dt):
        return _fallback()
    kd = _as_utc_ts(kickoff_dt)
    if pd.isna(kd):
        return _fallback()

    best = None  # (prioritas_sumber, selisih_detik, (hg, ag, src))
    for ts, hg, ag, src in entries:
        if pd.isna(ts):
            continue
        diff = abs((ts - kd).total_seconds())
        if diff > tol_hours * 3600:
            continue
        prio = 0 if src in ("espn", "api") else 1  # data asli lebih dipercaya
        cand = (prio, diff, (hg, ag, src))
        if best is None or cand < best:
            best = cand
    return best[2] if best else None


def _schedule_predictions() -> dict:
    """Prediksi per pasangan tim → list entri bertanggal [(ts_log, pred_dict)] terurut.

    Dipakai _resolve_schedule_prediction() yang memilih prediksi paling dekat dengan
    kickoff laga ini (bukan sekadar "id terbesar menang", yang bisa salah ambil
    prediksi laga berikutnya antar tim yang sama).
    """
    out: dict = {}
    try:
        from database import get_db
        conn = get_db()
        rows = conn.execute(
            "SELECT home_team, away_team, projected_home_goals, projected_away_goals, "
            "prob_home, prob_draw, prob_away, status, timestamp "
            "FROM prediction_logs ORDER BY id"
        ).fetchall()
        conn.close()
        # Vektorisasi: SATU panggilan to_datetime utk seluruh kolom timestamp
        # (per baris = ~2,6 dtk utk ribuan log — format guessing ulang tiap baris).
        ts_raw = pd.Series([r["timestamp"] for r in rows], dtype="object")
        ts_list = pd.to_datetime(ts_raw, errors="coerce", utc=True) if len(rows) else []
        for r, ts in zip(rows, ts_list):
            d = dict(r)
            d.pop("timestamp", None)
            out.setdefault((_fuzzy_key(r["home_team"]), _fuzzy_key(r["away_team"])), []) \
                .append((ts, d))
    except Exception:
        pass
    for v in out.values():
        v.sort(key=lambda e: (pd.isna(e[0]), e[0]))
    return out


def _resolve_schedule_prediction(pred_map: dict, pair, kickoff_dt):
    """Pilih prediksi untuk SATU laga: yang timestamp-nya paling dekat & sebelum kickoff.

    - Utamakan prediksi yang di-log sebelum/near kickoff (log prediksi = saat model
      dipanggil, umumnya sebelum laga). Fallback: yang paling dekat secara absolut.
    """
    entries = pred_map.get(pair)
    if not entries:
        return None

    if kickoff_dt is None or pd.isna(kickoff_dt):
        return entries[-1][1]
    kd = _as_utc_ts(kickoff_dt)
    if pd.isna(kd):
        return entries[-1][1]

    best_before = None  # (selisih_detik, pred) untuk ts <= kickoff
    best_any = None     # (selisih_detik, pred) untuk ts apa pun
    for ts, pred in entries:
        if pd.isna(ts):
            continue
        diff = abs((ts - kd).total_seconds())
        if best_any is None or diff < best_any[0]:
            best_any = (diff, pred)
        if ts <= kd and (best_before is None or diff < best_before[0]):
            best_before = (diff, pred)
    if best_before:
        return best_before[1]
    return best_any[1] if best_any else None


def _resolve_actual_espn(home: str, away: str, league: str | None):
    """Skor asli laga SELESAI via ESPN scoreboard — resolver yg SAMA dgn Match Centre.

    Dipakai sebagai fallback saat historical/livescore tidak punya skor laga ini
    (laga 1-3 hari terakhir biasanya belum masuk historical_matches.csv, dan
    key nama pasangan bisa beda sumber). Karena memakai match_detail._resolve_by_name,
    hasilnya dijamin identik dengan halaman Match Centre.

    Mengembalikan (hg, ag, 'espn') dalam urutan kandang/tandang fixture, atau None.
    """
    try:
        ev = match_detail._resolve_by_name(home, away, league)
    except Exception:
        return None
    if not ev or ev.get("status") != "FINISHED":
        return None
    hs, as_ = ev.get("home_score"), ev.get("away_score")
    if hs is None or as_ is None:
        return None
    if ev.get("swapped"):
        # ESPN menampilkan tim terbalik vs fixture → samakan urutan dgn Match Centre
        hs, as_ = as_, hs
    try:
        return (int(hs), int(as_), "espn")
    except (TypeError, ValueError):
        return None


def _schedule_item(row_id, league_code, date_str, home, away,
                   status, minute, home_score, away_score, score_source,
                   pred, actual) -> dict:
    verdict = None
    pred_out = None
    if pred:
        pred_out = {
            "home": pred.get("projected_home_goals"),
            "away": pred.get("projected_away_goals"),
            "prob_home": pred.get("prob_home"),
            "prob_draw": pred.get("prob_draw"),
            "prob_away": pred.get("prob_away"),
            "status": pred.get("status"),
        }
    if pred and actual:
        ph, pa = int(pred.get("projected_home_goals") or 0), int(pred.get("projected_away_goals") or 0)
        ah, aa = int(actual[0]), int(actual[1])
        exact = ph == ah and pa == aa
        outcome_ok = _outcome(ph, pa) == _outcome(ah, aa)
        verdict = {
            "exact": exact,
            "outcome_correct": outcome_ok,
            "label": "exact" if exact else ("outcome" if outcome_ok else "miss"),
        }
    return {
        "id": str(row_id),
        "league": league_code,
        "league_name": LEAGUE_NAMES.get(league_code, league_code),
        "date": date_str,
        "home": home,
        "away": away,
        "home_logo": get_team_logo(home),
        "away_logo": get_team_logo(away),
        "status": status,
        "minute": minute,
        "home_score": home_score,
        "away_score": away_score,
        "score_source": score_source,
        "prediction": pred_out,
        "verdict": verdict,
    }


@app.get("/api/schedule")
def get_schedule(tab: str = "live", league: str | None = None,
                 q: str | None = None, limit: int = 80):
    """Jadwal terpadu untuk picker laga.

    tab: live (live + hari ini WIB) | upcoming (mendatang) | finished (hasil selesai).
    Laga selesai TETAP disimpan untuk perbandingan prediksi vs aktual & pembelajaran model.
    """
    if tab not in ("upcoming", "live", "finished"):
        raise HTTPException(status_code=400, detail="tab harus upcoming|live|finished")
    limit = max(1, min(limit, 300))

    try:
        fx = pd.read_csv(UPCOMING_FIXTURES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="File upcoming_fixtures.csv belum ditemukan.")

    now = pd.Timestamp.now(tz="UTC")
    now_wib = now + pd.Timedelta(hours=7)
    fx["dt"] = pd.to_datetime(fx["date"], errors="coerce", utc=True)
    fx = fx.dropna(subset=["dt"])

    actual_map = _schedule_actual_scores()
    pred_map = _schedule_predictions()

    # Status live asli dari livescore (hanya sumber asli yang dipercaya)
    live_map: dict = {}
    live_source = None
    try:
        live = livescore.get_live_matches()
        live_source = live.get("source")
        if live_source in ("espn", "api"):
            for m in live.get("matches", []):
                live_map[(_fuzzy_key(m.get("home")), _fuzzy_key(m.get("away")))] = m
    except Exception:
        pass

    items: list[dict] = []
    fixture_pairs: set = set()

    for r in fx.itertuples():
        if league and r.league != league:
            continue
        home, away = str(r.home_team), str(r.away_team)
        if q:
            nq = q.strip().lower()
            if nq and nq not in home.lower() and nq not in away.lower():
                continue

        pair = (_fuzzy_key(home), _fuzzy_key(away))
        fixture_pairs.add(pair)
        dt = r.dt
        lm = live_map.get(pair)

        # Kickoff: ESPN lebih dipercaya bila punya data laga ini (tanggal CSV bisa meleset)
        if lm is not None and lm.get("kickoff"):
            try:
                espn_dt = pd.to_datetime(lm["kickoff"], errors="raise", utc=True)
                if not pd.isna(espn_dt):
                    dt = espn_dt
            except Exception:
                pass

        elapsed_min = (now - dt).total_seconds() / 60.0
        minute = None
        home_score = away_score = None
        score_source = None

        if lm is not None and lm.get("live"):
            status = "live"
            minute = lm.get("minute")
            home_score = lm.get("home_score")
            away_score = lm.get("away_score")
            if home_score is not None:
                score_source = live_source
        elif lm is not None and lm.get("status") == "FINISHED":
            # Skor live FINISHED hanya dipakai bila kickoff-nya laga yang sama (tanggal cocok)
            status = "finished"
            home_score = lm.get("home_score")
            away_score = lm.get("away_score")
            if home_score is not None:
                score_source = live_source
        elif elapsed_min < 0:
            status = "upcoming"
        elif elapsed_min <= SCHEDULE_WINDOW_MIN:
            status = "live"
            minute = min(90, max(1, int(elapsed_min)))
        else:
            status = "finished"

        actual = None
        if status == "finished":
            # Lookup bertanggal: pilih skor asli terdekat dengan kickoff laga ini
            actual = _resolve_schedule_actual(actual_map, pair, dt)
            if actual:
                home_score, away_score = actual[0], actual[1]
                score_source = actual[2]
            else:
                # Fallback: resolver ESPN yang SAMA dengan Match Centre — untuk laga
                # yang belum masuk historical (1-3 hari terakhir) atau nama tim beda
                # antar sumber. Menjaga popup & Match Centre menampilkan skor identik.
                espn = _resolve_actual_espn(home, away, r.league)
                if espn:
                    actual = espn
                    home_score, away_score = espn[0], espn[1]
                    score_source = espn[2]
                else:
                    # Tidak ada skor asli yang cocok → jangan tampilkan skor
                    # (lebih baik kosong daripada skor laga lain yang menyesatkan)
                    home_score = away_score = None
                    score_source = None

        pred = _resolve_schedule_prediction(pred_map, pair, dt)
        items.append(_schedule_item(
            r.match_id, r.league, dt.strftime("%Y-%m-%d %H:%M:%S"), home, away,
            status, minute, home_score, away_score, score_source,
            pred, actual,
        ))

    # Arsip hasil dari historical yang tidak ada di upcoming_fixtures (laga pra-10 Okt, musim berjalan saja)
    try:
        hist = filter_current_season(pd.read_csv(HISTORICAL_MATCHES))
        for h in hist.itertuples():
            if league and h.league != league:
                continue
            home, away = str(h.home_team), str(h.away_team)
            if q:
                nq = q.strip().lower()
                if nq and nq not in home.lower() and nq not in away.lower():
                    continue
            pair = (_fuzzy_key(home), _fuzzy_key(away))
            if pair in fixture_pairs:
                continue
            actual = (int(h.home_goals), int(h.away_goals), "understat")
            items.append(_schedule_item(
                h.match_id, h.league, str(h.datetime), home, away,
                "finished", 90, actual[0], actual[1], "understat",
                _resolve_schedule_prediction(pred_map, pair, h.datetime), actual,
            ))
    except (FileNotFoundError, Exception):
        pass

    def _is_today(item) -> bool:
        d = _wib_dt(item["date"])
        return d is not None and d.date() == now_wib.date()

    # Flag "hari ini" dihitung SEKALI per item; versi lama memanggil pd.to_datetime
    # (tebak format datetime) di tiap panggilan _in_tab → ~3.600x/request ≈ 85% waktu.
    _today_flags = [_is_today(i) for i in items]

    def _in_tab(idx: int, t) -> bool:
        st = items[idx]["status"]
        if t == "finished":
            return st == "finished"
        if t == "live":
            return st == "live" or _today_flags[idx]
        return st == "upcoming" and not _today_flags[idx]

    counts = {
        t: sum(1 for i in range(len(items)) if _in_tab(i, t))
        for t in ("upcoming", "live", "finished")
    }
    selected = [items[i] for i in range(len(items)) if _in_tab(i, tab)]

    if tab == "finished":
        selected.sort(key=lambda i: str(i["date"]), reverse=True)
    elif tab == "live":
        selected.sort(key=lambda i: (i["status"] != "live", str(i["date"])))
    else:
        selected.sort(key=lambda i: str(i["date"]))

    if tab == "finished":
        missing = sum(
            1 for i in items
            if i["status"] == "finished"
            and i["home_score"] is not None and i["away_score"] is not None
            and not i["prediction"]
        )
        if missing:
            start_backfill_async()

    total = len(selected)
    return {
        "tab": tab,
        "counts": counts,
        "total": total,
        "items": selected[:limit],
        "source": live_source,
        "fetched_at": now.isoformat(timespec="seconds"),
    }


@app.get("/api/live/matches")
def live_matches():
    """Skor live semua laga (polling server 55s, source: api|mock)."""
    return livescore.get_live_matches()


@app.get("/api/live/standings/{league_code}")
def live_standings(league_code: str):
    """Klasemen aktual + overlay skor live yang sedang berjalan."""
    try:
        return livescore.get_live_standings(league_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/live/ucl")
def live_ucl():
    """Laga Champions League yang sedang berlangsung / jadwal hari ini."""
    return livescore.get_live_ucl()


@app.get("/api/live/match/{match_id}/detail")
def live_match_detail(
    match_id: str,
    home: str | None = None,
    away: str | None = None,
    league: str | None = None,
    date: str | None = None,
    refresh: bool = False,
):
    """Detail laga: timeline gol/kartu, offside, line-up, statistik tim.

    Jika id tidak ada di daftar livescore (laga lama), backend resolve id ESPN
    dari query home/away — `date` (YYYY-MM-DD) mempercepat & memperluas resolusi
    ke laga kapan pun. Laga mock → available=false.
    """
    try:
        return match_detail.get_match_detail(
            match_id, home=home, away=away, league=league, date=date, force=refresh
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detail laga gagal diambil: {e}")


@app.get("/api/live/match/detail")
def live_match_detail_by_teams(
    home: str, away: str, league: str | None = None,
    date: str | None = None, refresh: bool = False,
):
    """Detail laga berdasar nama tim — resolve id ESPN otomatis.

    Tanpa `date`: scan 8 hari terakhir lalu fallback historis (historical_matches.csv)
    agar laga SELESAI kapan pun tetap bisa dibuka selama ESPN masih punya arsipnya.
    """
    try:
        return match_detail.get_match_detail(
            home=home, away=away, league=league, date=date, force=refresh
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detail laga gagal diambil: {e}")


_HIST_TEAMS_CACHE: set | None = None
_HIST_TEAMS_MTIME = None


def _teams_with_history() -> set:
    """Set kanonik tim yang punya data historis (cache per mtime CSV)."""
    global _HIST_TEAMS_CACHE, _HIST_TEAMS_MTIME
    try:
        mtime = HISTORICAL_MATCHES.stat().st_mtime
    except OSError:
        return set()
    if _HIST_TEAMS_CACHE is None or mtime != _HIST_TEAMS_MTIME:
        try:
            names = pd.read_csv(HISTORICAL_MATCHES, usecols=["home_team", "away_team"])
            _HIST_TEAMS_CACHE = {team_key(t) for t in set(names["home_team"]) | set(names["away_team"])}
            _HIST_TEAMS_MTIME = mtime
        except Exception:
            _HIST_TEAMS_CACHE = set()
    return _HIST_TEAMS_CACHE


def _team_data_source(team: str, stats: dict | None = None) -> str:
    """Sumber data kekuatan tim: xg+elo -> elo -> manual -> default."""
    src = get_club_strength(team).get("data_source", "manual")
    if src == "elo":
        has_xg = stats.get("games_analyzed") if stats else (team_key(team) in _teams_with_history())
        if has_xg:
            return "xg+elo"
    return src


def _compute_projection(home_team: str, away_team: str, matches_df: pd.DataFrame) -> dict:
    """Inti prediksi: power index → blend xG → simulasi 10k → skor proyeksi + probabilitas."""
    home_strength = get_club_strength(home_team)
    away_strength = get_club_strength(away_team)
    strength_gap = round(home_strength["overall"] - away_strength["overall"], 1)

    home_stats = get_team_power_index(
        home_team, matches_df, last_n=20,
        prior_xg=xg_prior_from_rating(home_strength["overall"]),
        prior_ga=ga_prior_from_rating(home_strength["overall"]),
        overall=home_strength["overall"],
    )
    away_stats = get_team_power_index(
        away_team, matches_df, last_n=20,
        prior_xg=xg_prior_from_rating(away_strength["overall"]),
        prior_ga=ga_prior_from_rating(away_strength["overall"]),
        overall=away_strength["overall"],
    )
    home_strength["data_source"] = _team_data_source(home_team, home_stats)
    away_strength["data_source"] = _team_data_source(away_team, away_stats)

    home_bias = get_home_away_bias(home_team, is_home=True, matches_df=matches_df)
    away_bias = get_home_away_bias(away_team, is_home=False, matches_df=matches_df)

    # Blend rating kekuatan ke xG (power index = data historis; rating = prior jarak kekuatan)
    def _blend_xg(base, bias, overall, opponent_overall):
        gap_mult = 1.0 + (overall - opponent_overall) * 0.004  # +/-20 rating -> +/-8%
        return clamp_match_xg(base * bias * gap_mult)

    final_home_xg = _blend_xg(home_stats["avg_xg"], home_bias, home_strength["overall"], away_strength["overall"])
    final_away_xg = _blend_xg(away_stats["avg_xg"], away_bias, away_strength["overall"], home_strength["overall"])

    home_sim, away_sim, prob_ht = simulate_10k_matches_minute_by_minute(
        final_home_xg, final_away_xg, iterations=10000, verbose=False
    )

    prob_home = round((np.sum(home_sim > away_sim) / 10000) * 100, 1)
    prob_draw = round((np.sum(home_sim == away_sim) / 10000) * 100, 1)
    prob_away = round((np.sum(away_sim > home_sim) / 10000) * 100, 1)

    # Kalibrasi 3-kelas dari log pembelajaran (Fase 5). Raw dipertahankan untuk
    # log prediction_logs (fit kalibrasi selalu pada prob mentah -> riil).
    raw_prob_home, raw_prob_draw, raw_prob_away = prob_home, prob_draw, prob_away
    try:
        from model_retrainer import apply_probability_calibration

        cal = apply_probability_calibration([prob_home, prob_draw, prob_away])
        prob_home, prob_draw, prob_away = (round(float(x), 1) for x in cal)
    except Exception:
        pass  # kalibrasi gagal -> pakai prob mentah

    smart_h, smart_a, confidence = calculate_smart_projected_score(
        home_sim, away_sim, prob_home, prob_away, final_home_xg, final_away_xg,
        strength_gap=strength_gap,
    )

    return {
        "home_strength": home_strength,
        "away_strength": away_strength,
        "strength_gap": strength_gap,
        "home_stats": home_stats,
        "away_stats": away_stats,
        "final_home_xg": final_home_xg,
        "final_away_xg": final_away_xg,
        "prob_home": prob_home,
        "prob_draw": prob_draw,
        "prob_away": prob_away,
        "raw_prob_home": raw_prob_home,
        "raw_prob_draw": raw_prob_draw,
        "raw_prob_away": raw_prob_away,
        "prob_ht": prob_ht,
        "smart_h": smart_h,
        "smart_a": smart_a,
        "confidence": confidence,
    }


@app.get("/api/predict")
def predict_match(home_team: str, away_team: str):
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    shots_df = _load_shots()

    home_profile = get_club_profile(home_team)
    away_profile = get_club_profile(away_team)

    p = _compute_projection(home_team, away_team, matches_df)
    home_strength = p["home_strength"]
    away_strength = p["away_strength"]
    strength_gap = p["strength_gap"]
    home_stats = p["home_stats"]
    away_stats = p["away_stats"]
    final_home_xg = p["final_home_xg"]
    final_away_xg = p["final_away_xg"]
    prob_home = p["prob_home"]
    prob_draw = p["prob_draw"]
    prob_away = p["prob_away"]
    prob_ht = p["prob_ht"]
    smart_h, smart_a, confidence = p["smart_h"], p["smart_a"], p["confidence"]

    home_form = get_team_form(home_team, matches_df, 5)
    away_form = get_team_form(away_team, matches_df, 5)

    # Self-learning: catat prediksi ke SQLite. Pakai prob MENTAH (bukan terkalibrasi)
    # agar fit kalibrasi selalu memetakan prob mentah -> riil (tidak double-correct).
    try:
        from database import get_db
        _db = get_db()
        _db.execute(
            "INSERT INTO prediction_logs (home_team, away_team, projected_home_goals, "
            "projected_away_goals, prob_home, prob_draw, prob_away) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                home_team, away_team, int(smart_h), int(smart_a),
                p.get("raw_prob_home", prob_home),
                p.get("raw_prob_draw", prob_draw),
                p.get("raw_prob_away", prob_away),
            ),
        )
        _db.commit()
        _db.close()
    except Exception:
        pass

    home_shots = _team_shot_summary(home_team, shots_df)
    away_shots = _team_shot_summary(away_team, shots_df)

    home_tactical = _tactical_metrics(home_team, home_stats, home_shots, away_shots["xg"])
    away_tactical = _tactical_metrics(away_team, away_stats, away_shots, home_shots["xg"])

    differential = _differential_summary(
        home_team, away_team, home_tactical, away_tactical, final_home_xg, final_away_xg
    )

    # Cek hasil akhir (historical) / live score
    result = _match_result(home_team, away_team, smart_h, smart_a, prob_home, prob_draw, prob_away)

    return {
        "match": f"{home_team} vs {away_team}",
        "home_team": {
            "name": home_team,
            "logo": get_team_logo(home_team),
            "star_player": get_key_player(home_team),
            "form": home_form,
            "coach": home_profile.get("coach"),
            "formation": home_profile.get("formation"),
            "strength": home_strength,
            "data_source": home_strength.get("data_source", "default"),
        },
        "away_team": {
            "name": away_team,
            "logo": get_team_logo(away_team),
            "star_player": get_key_player(away_team),
            "form": away_form,
            "coach": away_profile.get("coach"),
            "formation": away_profile.get("formation"),
            "strength": away_strength,
            "data_source": away_strength.get("data_source", "default"),
        },
        "strength_gap": {
            "value": abs(strength_gap),
            "home": home_strength["overall"],
            "away": away_strength["overall"],
            "favorite": (
                home_team if strength_gap >= 5
                else away_team if strength_gap <= -5
                else None
            ),
        },
        "meta": {
            "stadium": home_profile.get("stadium") or "Stadion pertandingan",
            "referee": "Wasit pertandingan",
            "competition": "Liga",
            "note": "Stadion dari profil klub tuan rumah; wasit placeholder (data Understat tidak menyertakan info ini).",
        },
        "projection": {
            "score": f"{smart_h} - {smart_a}",
            "home_score": int(smart_h),
            "away_score": int(smart_a),
            "confidence_pct": confidence,
        },
        "probabilities": {
            "home_win": prob_home,
            "draw": prob_draw,
            "away_win": prob_away,
        },
        "analytics": {
            "home_xg": final_home_xg,
            "away_xg": final_away_xg,
            "first_half_goal_probability": prob_ht,
        },
        "tactical": {
            "home": home_tactical,
            "away": away_tactical,
        },
        "shots": {
            "home": {k: v for k, v in home_shots.items() if k != "points"},
            "away": {k: v for k, v in away_shots.items() if k != "points"},
        },
        "differential_summary": differential,
        "result": result,
    }


@app.get("/api/shots")
def get_shot_map(home_team: str, away_team: str):
    shots_df = _load_shots()
    if shots_df is None or shots_df.empty:
        raise HTTPException(status_code=404, detail="Data tembakan belum tersedia.")

    home = _team_shot_summary(home_team, shots_df)
    away = _team_shot_summary(away_team, shots_df)

    def _summary(side_summary, side_name):
        return {
            "team": side_name,
            "shots": side_summary["shots"],
            "goals": side_summary["goals"],
            "xg": side_summary["xg"],
            "conversion_pct": side_summary["conversion_pct"],
            "zone14_shots": side_summary["zone14_shots"],
            "zone14_pct": side_summary["zone14_pct"],
            "on_target_pct": side_summary["on_target_pct"],
            "points": side_summary["points"],
        }

    return {
        "home": _summary(home, home_team),
        "away": _summary(away, away_team),
        "summary": {
            "zone14_home": home["zone14_shots"],
            "zone14_away": away["zone14_shots"],
            "zone14_dominance": home_team if home["zone14_shots"] >= away["zone14_shots"] else away_team,
            "suppression_home": round(
                max(0.0, min(100.0, (1 - away["xg"] / max(home["shots"] * 0.11, 0.2)) * 100)), 1
            ),
            "suppression_away": round(
                max(0.0, min(100.0, (1 - home["xg"] / max(away["shots"] * 0.11, 0.2)) * 100)), 1
            ),
        },
    }


@app.get("/api/standings/{league_code}")
def get_league_standings(league_code: str, n_seasons: int = 350):
    try:
        projection = project_league(league_code, n_seasons=min(max(n_seasons, 100), 800))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    # Enrich logo & star player
    for row in projection["standings"]:
        row["logo"] = get_team_logo(row["team"])
        row["star_player"] = get_key_player(row["team"])
        row["zone"] = _zone_label(row["projected_position"], len(projection["standings"]))

    return projection


def _zone_label(pos: int, total: int) -> str:
    if pos <= 4:
        return "UCL"
    if pos <= 6:
        return "UEL"
    if pos >= total - 2:
        return "REL"
    return "MID"


def _enrich_ucl(result: dict) -> dict:
    """Lengkapi hasil simulasi UCL dengan logo, star player & data_source."""
    for item in result["league_phase"]:
        item["logo"] = get_team_logo(item["team"])
        item["star_player"] = get_key_player(item["team"])
        item["data_source"] = _team_data_source(item["team"])

    for stage in ("playoffs", "round_of_16", "quarter_finals", "semi_finals"):
        for m in result["knockout_stage"][stage]:
            m["logo_home"] = get_team_logo(m["team_home"])
            m["logo_away"] = get_team_logo(m["team_away"])
            m["star_player_home"] = get_key_player(m["team_home"])
            m["star_player_away"] = get_key_player(m["team_away"])
            m["data_source_home"] = _team_data_source(m["team_home"])
            m["data_source_away"] = _team_data_source(m["team_away"])

    final_m = result["knockout_stage"]["final"]
    final_m["logo_home"] = get_team_logo(final_m["team_home"])
    final_m["logo_away"] = get_team_logo(final_m["team_away"])
    final_m["star_player_home"] = get_key_player(final_m["team_home"])
    final_m["star_player_away"] = get_key_player(final_m["team_away"])
    final_m["data_source_home"] = _team_data_source(final_m["team_home"])
    final_m["data_source_away"] = _team_data_source(final_m["team_away"])

    champion = result["champion"]
    champion["logo"] = get_team_logo(champion["team"])
    champion["star_player"] = get_key_player(champion["team"])
    champion["data_source"] = _team_data_source(champion["team"])
    return result


@app.get("/api/ucl/simulate")
def simulate_ucl():
    global _UCL_CACHE
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    if _UCL_CACHE is None:
        _UCL_CACHE = simulate_ucl_tournament(matches_df)

    return _enrich_ucl(json.loads(json.dumps(_UCL_CACHE)))


@app.post("/api/ucl/whatif")
def ucl_whatif(payload: dict | None = None):
    """What-If Interactive Simulator: re-simulasi UCL dengan skor manual pengguna.

    Body: {"overrides": {"league_fixtures": {"lp_m1": {"goals_home": 3, "goals_away": 0}},
                          "knockout": {"playoff_m1": {"agg_home": 2, "agg_away": 1}}}}
    """
    overrides = (payload or {}).get("overrides") or {}
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")
    try:
        result = simulate_ucl_tournament(matches_df, overrides=overrides)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if simulation gagal: {e}")
    return _enrich_ucl(result)


@app.get("/api/analytics/{team}")
def analytics_team(team: str):
    try:
        return get_club_analytics(team)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data pendukung analitik belum ada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membangun analitik klub: {e}")


@app.get("/api/teams")
def list_teams(league: str | None = None):
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    df = filter_current_season(matches_df)
    if league:
        df = df[df["league"] == league]
    teams = sorted(set(df["home_team"]).union(set(df["away_team"])))
    return {
        "league": league,
        "teams": [
            {"name": t, "logo": get_team_logo(t), "star_player": get_key_player(t)}
            for t in teams
        ],
    }


# ==========================================
# SELF-LEARNING: PREDICTION LOGS & RETRAIN
# ==========================================

@app.get("/api/model/stats")
def model_stats():
    """Statistik log prediksi & metrik model (Brier, accuracy)."""
    from model_retrainer import get_model_stats
    return get_model_stats()


@app.post("/api/model/evaluate")
def model_evaluate():
    """Sinkron hasil riil dari historical_matches → hitung Brier/Log-Loss → tandai EVALUATED."""
    from model_retrainer import evaluate_pending_predictions
    try:
        return evaluate_pending_predictions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluasi gagal: {e}")


@app.post("/api/model/retrain")
def model_retrain():
    """Retrain XGBoost dari data tembakan terbaru (feedback loop)."""
    from model_retrainer import retrain_model
    return retrain_model()


BACKFILL_STATE = {"running": False, "last": None}
_BACKFILL_LOCK = threading.Lock()


def backfill_finished_predictions(evaluate: bool = True) -> dict:
    """Hindcast prediksi untuk laga SELESAI yang belum punya log.

    Anti-bocor hasil: hanya memakai laga historis yang berakhir SEBELUM kickoff
    pertandingan, dan mengecualikan pasangan tim itu sendiri. Hasil akhir langsung
    ditulis (status PENDING + aktual) lalu dievaluasi sekali di akhir.
    """
    sched = get_schedule(tab="finished", limit=300)
    items = sched["items"]
    pred_map = _schedule_predictions()

    def _has_pred_for(pair, kickoff_str):
        """True bila sudah ada prediksi yang di-log untuk laga ini (kickoff cocok ±6 jam).

        Sebelumnya memakai `pair in pred_map` sehingga prediksi laga LAIN antar tim
        yang sama (banyak kali bertemu lintas musim) membuat laga ini ter-skip.
        """
        entries = pred_map.get(pair)
        if not entries:
            return False
        try:
            ko = pd.to_datetime(kickoff_str, errors="coerce", utc=True)
        except Exception:
            ko = pd.NaT
        if pd.isna(ko):
            return True  # tanpa tanggal → anggap sudah ada (jangan duplikat)
        for ts, _pred in entries:
            if pd.isna(ts):
                continue
            if abs((ts - ko).total_seconds()) <= 6 * 3600:
                return True
        return False

    hist = None
    try:
        hist = pd.read_csv(HISTORICAL_MATCHES)
        hist["dt"] = pd.to_datetime(hist["datetime"], errors="coerce")
        hist["pk"] = [
            (_fuzzy_key(h), _fuzzy_key(a))
            for h, a in zip(hist["home_team"], hist["away_team"])
        ]
    except (FileNotFoundError, Exception):
        hist = None

    from database import get_db

    inserted = skipped_existing = skipped_no_actual = skipped_error = 0

    for it in items:
        pair = (_fuzzy_key(it["home"]), _fuzzy_key(it["away"]))
        if _has_pred_for(pair, it["date"]):
            skipped_existing += 1
            continue
        if it["home_score"] is None or it["away_score"] is None:
            skipped_no_actual += 1
            continue

        kickoff = pd.to_datetime(it["date"], errors="coerce")
        if hist is None or pd.isna(kickoff):
            skipped_error += 1
            continue
        filtered = hist[(hist["dt"] < kickoff) & (hist["pk"] != pair)]

        try:
            proj = _compute_projection(it["home"], it["away"], filtered)
            conn = get_db()
            conn.execute(
                "INSERT INTO prediction_logs (home_team, away_team, projected_home_goals, "
                "projected_away_goals, prob_home, prob_draw, prob_away, "
                "actual_home_goals, actual_away_goals, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')",
                (
                    it["home"], it["away"],
                    int(proj["smart_h"]), int(proj["smart_a"]),
                    proj.get("raw_prob_home", proj["prob_home"]),
                    proj.get("raw_prob_draw", proj["prob_draw"]),
                    proj.get("raw_prob_away", proj["prob_away"]),
                    int(it["home_score"]), int(it["away_score"]),
                ),
            )
            conn.commit()
            conn.close()
            # Tandai sudah ada prediksi untuk laga ini (pakai kickoff agar
            # _has_pred_for() mendeteksinya di iterasi berikutnya).
            try:
                _ts = pd.to_datetime(it["date"], errors="coerce", utc=True)
            except Exception:
                _ts = pd.NaT
            pred_map.setdefault(pair, []).append((_ts, {"inserted": True}))
            inserted += 1
        except Exception:
            skipped_error += 1

    evaluation = None
    if evaluate and inserted:
        from model_retrainer import evaluate_pending_predictions
        try:
            evaluation = evaluate_pending_predictions()
        except Exception as e:
            evaluation = {"error": str(e)}

    return {
        "scanned": len(items),
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "skipped_no_actual": skipped_no_actual,
        "skipped_error": skipped_error,
        "evaluation": evaluation,
    }


def start_backfill_async(evaluate: bool = True) -> bool:
    """Jalankan backfill di thread latar. Return False bila masih berjalan."""
    with _BACKFILL_LOCK:
        if BACKFILL_STATE["running"]:
            return False
        BACKFILL_STATE["running"] = True

    def _run():
        try:
            BACKFILL_STATE["last"] = backfill_finished_predictions(evaluate=evaluate)
        except Exception as e:
            BACKFILL_STATE["last"] = {"error": str(e)}
        finally:
            with _BACKFILL_LOCK:
                BACKFILL_STATE["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return True


def _warm_schedule():
    """Isi cache schedule saat startup (historical, ESPN scoreboard, livescore).

    Tanpa ini, request PERTAMA user menanggung cold-hit ~10 dtk (scan ESPN utk
    laga tanpa skor + fetch livescore). Beri jeda agar tak berebut dgn backfill.
    """
    time.sleep(3)
    for tab in ("live", "finished", "upcoming"):
        try:
            get_schedule(tab, limit=80)
        except Exception:
            pass


@app.on_event("startup")
def _startup_backfill():
    start_backfill_async()
    threading.Thread(target=_warm_schedule, daemon=True).start()
    if AUTO_LEARN:
        _start_auto_learn()


# ==== Self-learning loop (Fase 5): auto-eval periodik + auto-retrain terjadwal ====
_AUTO_LEARN_STATE = {"last_eval": None, "last_retrain": None, "last_eval_result": None,
                     "last_retrain_result": None, "running": False}


def _auto_learn_cycle():
    """Eval prediksi selesai -> refit kalibrasi -> (tiap N jam) retrain XGBoost."""
    from model_retrainer import evaluate_pending_predictions, fit_probability_calibration, retrain_model

    with threading.Lock():
        if _AUTO_LEARN_STATE["running"]:
            return
        _AUTO_LEARN_STATE["running"] = True
    try:
        # 1) Evaluasi prediksi pending (PENDING -> EVALUATED) + sinkron hasil riil
        try:
            _AUTO_LEARN_STATE["last_eval_result"] = evaluate_pending_predictions()
        except Exception as e:
            _AUTO_LEARN_STATE["last_eval_result"] = {"error": str(e)}
        _AUTO_LEARN_STATE["last_eval"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # 2) Refit kalibrasi probabilitas dari log EVALUATED
        try:
            fit_probability_calibration()
        except Exception:
            pass

        # 3) Retrain XGBoost terjadwal
        last_retrain = _AUTO_LEARN_STATE["last_retrain"]
        due = (
            last_retrain is None
            or (time.time() - last_retrain) >= AUTO_RETRAIN_INTERVAL_H * 3600
        )
        if due:
            _AUTO_LEARN_STATE["last_retrain_result"] = retrain_model()
            _AUTO_LEARN_STATE["last_retrain"] = time.time()
    finally:
        with threading.Lock():
            _AUTO_LEARN_STATE["running"] = False


def _auto_learn_loop():
    # Cycle pertama: beri jeda agar backfill startup tidak berebut CPU
    time.sleep(120)
    while True:
        try:
            _auto_learn_cycle()
        except Exception:
            pass
        time.sleep(AUTO_EVAL_INTERVAL_H * 3600)


def _start_auto_learn():
    threading.Thread(target=_auto_learn_loop, daemon=True).start()


@app.get("/api/model/autolearn")
def model_autolearn():
    """Status self-learning loop (eval & retrain terakhir)."""
    import datetime as _dt

    lr = _AUTO_LEARN_STATE["last_retrain"]
    return {
        **{k: v for k, v in _AUTO_LEARN_STATE.items() if k != "last_retrain"},
        "last_retrain": (
            _dt.datetime.fromtimestamp(lr).strftime("%Y-%m-%d %H:%M:%S") if lr else None
        ),
        "eval_interval_hours": AUTO_EVAL_INTERVAL_H,
        "retrain_interval_hours": AUTO_RETRAIN_INTERVAL_H,
        "auto_learn_enabled": AUTO_LEARN,
    }


@app.post("/api/model/backfill")
def model_backfill():
    """Backfill hindcast laga selesai yang belum punya prediksi + evaluasi sekali."""
    with _BACKFILL_LOCK:
        if BACKFILL_STATE["running"]:
            return {"status": "running", "detail": "Backfill masih berjalan."}
        BACKFILL_STATE["running"] = True
    try:
        stats = backfill_finished_predictions(evaluate=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backfill gagal: {e}")
    finally:
        with _BACKFILL_LOCK:
            BACKFILL_STATE["running"] = False
    return {"status": "ok", **stats}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True)
