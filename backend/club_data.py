"""Profil klub live dari club_profiles.json (coach, formasi, rating, pemain, stadion)."""
import json

from data_paths import CLUB_PROFILES
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


def get_club_strength(team: str) -> dict:
    """Kekuatan klub: rating skuad + kualitas pelatih (bobot 80/20)."""
    profile = get_club_profile(team)
    rating = float(profile.get("rating") or 65)
    coach_rating = float(profile.get("coach_rating") or 65)
    overall = round(rating * 0.8 + coach_rating * 0.2, 1)
    return {
        "rating": rating,
        "coach_rating": coach_rating,
        "overall": overall,
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
