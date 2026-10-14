"""Profil klub live dari club_profiles.json (coach, formasi, rating, pemain, stadion)."""
import csv
import json

import data_paths
from data_paths import CLUB_ELO, CLUB_PROFILES, ELO_NAME_MAP
from team_aliases import canonical_team

_DEFAULT = {
    "coach": "Staff Analitik",
    "formation": "4-3-3",
    "style": "balanced",
    "stadium": "Stadion Klub",
    "rating": 65,
    "coach_rating": 65,
    "players": [],
}

_CACHE = None
_BY_CANON = None
_MTIME = None

_ELO_CACHE: dict | None = None
_ELO_MTIMES: tuple | None = None
_ELO_NAME_MAP_CACHE: dict | None = None


def load_club_profiles() -> dict:
    global _CACHE, _BY_CANON, _MTIME
    try:
        mtime = CLUB_PROFILES.stat().st_mtime
    except OSError:
        mtime = None
    if _CACHE is None or mtime != _MTIME:
        try:
            with open(CLUB_PROFILES, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
        except Exception:
            _CACHE = {}
        _BY_CANON = {canonical_team(k): v for k, v in _CACHE.items()}
        _MTIME = mtime
    return _CACHE


def get_club_profile(team: str) -> dict:
    """Profil klub (fallback default bila nama tak dikenal)."""
    profiles = load_club_profiles()
    entry = profiles.get(team) or profiles.get(canonical_team(team))
    if entry is None and _BY_CANON:
        entry = _BY_CANON.get(canonical_team(team))
    return {**_DEFAULT, **(entry or {})}


# ===================== Elo Prior (ClubElo) =====================
def _load_elo_name_map() -> dict:
    """Peta nama ClubElo -> nama kanonik (cache; reload bila file berubah)."""
    global _ELO_NAME_MAP_CACHE, _ELO_MTIMES
    try:
        mtimes = (CLUB_ELO.stat().st_mtime, ELO_NAME_MAP.stat().st_mtime)
    except OSError as e:
        mtimes = (None, None)
        if _ELO_NAME_MAP_CACHE is None:
            print(f"[PERINGATAN] File Elo tidak bisa dibaca: {e}")
    if _ELO_NAME_MAP_CACHE is None or mtimes != _ELO_MTIMES:
        name_map = {}
        try:
            raw = json.loads(ELO_NAME_MAP.read_text(encoding="utf-8"))
            name_map = {k: v for k, v in raw.items() if not str(k).startswith("_")}
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            print(f"[PERINGATAN] elo_name_map.json tidak terbaca ({e}) - pakai nama apa adanya.")
        elo = {}
        try:
            with open(CLUB_ELO, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    club = (row.get("Club") or "").strip()
                    if not club:
                        continue
                    try:
                        elo_val = float(row.get("Elo") or "")
                    except ValueError:
                        continue
                    elo[canonical_team(name_map.get(club, club))] = elo_val
        except FileNotFoundError:
            print(f"[PERINGATAN] {CLUB_ELO.name} belum ada - jalankan scripts/fetch_elo.py.")
        except OSError as e:
            print(f"[PERINGATAN] club_elo.csv tidak terbaca: {e}")
        _ELO_NAME_MAP_CACHE = elo  # peta nama & elo digabung jadi satu dict kanonik->elo
        _ELO_MTIMES = mtimes
    return _ELO_NAME_MAP_CACHE


def get_club_elo(team: str) -> float | None:
    """Rating Elo ClubElo utk `team` (kanonik), atau None bila tak tersedia."""
    return _load_elo_name_map().get(canonical_team(team))


def elo_to_overall(elo: float) -> float:
    """Elo ClubElo -> skala overall (netral 1700 = 65; clamp 40..95)."""
    cfg = data_paths
    raw = cfg.ELO_NEUTRAL_OVERALL + (float(elo) - cfg.ELO_NEUTRAL_ELO) * cfg.ELO_SCALE
    lo, hi = cfg.ELO_OVERALL_CLIP
    return round(float(max(lo, min(hi, raw))), 1)


def _has_manual_profile(team: str) -> bool:
    """True bila klub punya entri profil manual (rating bukan default 65)."""
    profiles = load_club_profiles()
    entry = profiles.get(team) or profiles.get(canonical_team(team))
    if entry is None and _BY_CANON:
        entry = _BY_CANON.get(canonical_team(team))
    return bool(entry)


def get_club_strength(team: str) -> dict:
    """Kekuatan klub: rating skuad + kualitas pelatih (bobot 80/20).

    Dengan USE_ELO_PRIOR=True: blend overall = 0.65*elo + 0.15*rating + 0.20*coach.
    `data_source`: xg+elo -> elo -> manual -> default (xg dicek pemanggil via stats).
    """
    profile = get_club_profile(team)
    rating = float(profile.get("rating") or 65)
    coach_rating = float(profile.get("coach_rating") or 65)
    manual_overall = round(rating * 0.8 + coach_rating * 0.2, 1)

    elo = get_club_elo(team)
    overall = manual_overall
    overall_elo = None
    data_source = "manual" if _has_manual_profile(team) else "default"

    if data_paths.USE_ELO_PRIOR and elo is not None:
        overall_elo = elo_to_overall(elo)
        overall = round(
            data_paths.ELO_BLEND_ELO * overall_elo
            + data_paths.ELO_BLEND_RATING * rating
            + data_paths.ELO_BLEND_COACH * coach_rating,
            1,
        )
        # Elo tersedia -> sumber utama prior (di-upgrade ke 'xg+elo' bila ada data historis)
        data_source = "elo"

    return {
        "rating": rating,
        "coach_rating": coach_rating,
        "overall": overall,
        "manual_overall": manual_overall,
        "elo": elo,
        "overall_elo": overall_elo,
        "data_source": data_source,
        "coach": profile.get("coach"),
        "formation": profile.get("formation"),
        "style": profile.get("style"),
    }


def xg_prior_from_rating(overall: float) -> float:
    """xG ekspektasi dari rating kekuatan (netral di 70 = rata-rata klub)."""
    return round(float(max(0.75, min(2.30, 1.40 + (overall - 70.0) * 0.025))), 2)


def ga_prior_from_rating(overall: float) -> float:
    """Gol kebobolan ekspektasi dari rating kekuatan (makin kuat makin sedikit)."""
    return round(float(max(0.70, min(1.75, 1.30 - (overall - 70.0) * 0.018))), 2)


def star_player(team: str) -> dict | None:
    """Pemain terbaik dari profil klub (wajib berfoto; prioritas posisi menyerang)."""
    players = get_club_profile(team).get("players") or []
    photoed = [p for p in players if p.get("image")]
    pool = photoed or players
    if not pool:
        return None

    def _pref(p):
        pos = str(p.get("position") or "")
        attack = any(k in pos for k in ("Forward", "Winger", "Attacking Midfield"))
        striker = "Striker" in pos or "Centre-Forward" in pos
        has_img = 1 if p.get("image") else 0
        return (-has_img, 0 if striker else 1 if attack else 2)

    best = min(pool, key=_pref)
    return {
        "player_name": best.get("name"),
        "position": best.get("position"),
        "image": best.get("image"),
    }
