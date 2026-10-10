import json

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from assets import get_key_player, get_team_logo
from club_analytics import get_club_analytics, LEAGUE_NAMES
from club_data import ga_prior_from_rating, get_club_profile, get_club_strength, xg_prior_from_rating
from data_paths import HISTORICAL_MATCHES, REAL_SHOTS_DATA, UPCOMING_FIXTURES
import livescore
import match_detail
from run_prediction import calculate_smart_projected_score, simulate_10k_matches_minute_by_minute
from season_projection import project_league
from team_aliases import team_abbr
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
    team_shots = shots_df[shots_df["team_name"].str.lower() == team.lower()]
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
    refresh: bool = False,
):
    """Detail laga: timeline gol/kartu, offside, line-up, statistik tim.

    Jika id tidak ada di daftar livescore (laga lama), backend resolve id ESPN
    dari query home/away bila diberikan. Laga mock → available=false.
    """
    try:
        return match_detail.get_match_detail(
            match_id, home=home, away=away, league=league, force=refresh
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detail laga gagal diambil: {e}")


@app.get("/api/live/match/detail")
def live_match_detail_by_teams(home: str, away: str, league: str | None = None, refresh: bool = False):
    """Detail laga berdasar nama tim — resolve id ESPN otomatis (scan 7 hari)."""
    try:
        return match_detail.get_match_detail(home=home, away=away, league=league, force=refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detail laga gagal diambil: {e}")


@app.get("/api/predict")
def predict_match(home_team: str, away_team: str):
    try:
        matches_df = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Data histori pertandingan belum ada.")

    shots_df = _load_shots()

    home_profile = get_club_profile(home_team)
    away_profile = get_club_profile(away_team)
    home_strength = get_club_strength(home_team)
    away_strength = get_club_strength(away_team)
    strength_gap = round(home_strength["overall"] - away_strength["overall"], 1)

    home_stats = get_team_power_index(
        home_team, matches_df, last_n=20,
        prior_xg=xg_prior_from_rating(home_strength["overall"]),
        prior_ga=ga_prior_from_rating(home_strength["overall"]),
    )
    away_stats = get_team_power_index(
        away_team, matches_df, last_n=20,
        prior_xg=xg_prior_from_rating(away_strength["overall"]),
        prior_ga=ga_prior_from_rating(away_strength["overall"]),
    )

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

    smart_h, smart_a, confidence = calculate_smart_projected_score(
        home_sim, away_sim, prob_home, prob_away, final_home_xg, final_away_xg,
        strength_gap=strength_gap,
    )

    home_form = get_team_form(home_team, matches_df, 5)
    away_form = get_team_form(away_team, matches_df, 5)

    # Self-learning: catat prediksi ke SQLite (evaluasi Brier/Log-Loss nanti)
    try:
        from database import get_db
        _db = get_db()
        _db.execute(
            "INSERT INTO prediction_logs (home_team, away_team, projected_home_goals, "
            "projected_away_goals, prob_home, prob_draw, prob_away) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (home_team, away_team, int(smart_h), int(smart_a), prob_home, prob_draw, prob_away),
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
        },
        "away_team": {
            "name": away_team,
            "logo": get_team_logo(away_team),
            "star_player": get_key_player(away_team),
            "form": away_form,
            "coach": away_profile.get("coach"),
            "formation": away_profile.get("formation"),
            "strength": away_strength,
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
    """Lengkapi hasil simulasi UCL dengan logo & star player."""
    for item in result["league_phase"]:
        item["logo"] = get_team_logo(item["team"])
        item["star_player"] = get_key_player(item["team"])

    for stage in ("playoffs", "round_of_16", "quarter_finals", "semi_finals"):
        for m in result["knockout_stage"][stage]:
            m["logo_home"] = get_team_logo(m["team_home"])
            m["logo_away"] = get_team_logo(m["team_away"])
            m["star_player_home"] = get_key_player(m["team_home"])
            m["star_player_away"] = get_key_player(m["team_away"])

    final_m = result["knockout_stage"]["final"]
    final_m["logo_home"] = get_team_logo(final_m["team_home"])
    final_m["logo_away"] = get_team_logo(final_m["team_away"])
    final_m["star_player_home"] = get_key_player(final_m["team_home"])
    final_m["star_player_away"] = get_key_player(final_m["team_away"])

    champion = result["champion"]
    champion["logo"] = get_team_logo(champion["team"])
    champion["star_player"] = get_key_player(champion["team"])
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

    df = matches_df
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True)
