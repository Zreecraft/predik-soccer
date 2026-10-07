"""Aset statis: logo tim & pemain kunci (di-cache per mtime file)."""
import json

from data_paths import KEY_PLAYERS, TEAM_LOGOS
from team_aliases import canonical_team

_LOGOS_CACHE = None
_PLAYERS_CACHE = None
_LOGOS_BY_CANON = None
_PLAYERS_BY_CANON = None
_LOGOS_MTIME = None
_PLAYERS_MTIME = None

PLACEHOLDER_LOGO = "https://via.placeholder.com/150?text=No+Logo"


def _load_logos() -> dict:
    global _LOGOS_CACHE, _LOGOS_BY_CANON, _LOGOS_MTIME
    try:
        mtime = TEAM_LOGOS.stat().st_mtime
    except OSError:
        mtime = None
    if _LOGOS_CACHE is None or mtime != _LOGOS_MTIME:
        try:
            with open(TEAM_LOGOS, "r", encoding="utf-8") as f:
                _LOGOS_CACHE = json.load(f)
        except Exception:
            _LOGOS_CACHE = {}
        _LOGOS_BY_CANON = {canonical_team(k): v for k, v in _LOGOS_CACHE.items()}
        _LOGOS_MTIME = mtime
    return _LOGOS_CACHE


def _load_players() -> dict:
    global _PLAYERS_CACHE, _PLAYERS_BY_CANON, _PLAYERS_MTIME
    try:
        mtime = KEY_PLAYERS.stat().st_mtime
    except OSError:
        mtime = None
    if _PLAYERS_CACHE is None or mtime != _PLAYERS_MTIME:
        try:
            with open(KEY_PLAYERS, "r", encoding="utf-8") as f:
                _PLAYERS_CACHE = json.load(f)
        except Exception:
            _PLAYERS_CACHE = {}
        _PLAYERS_BY_CANON = {canonical_team(k): v for k, v in _PLAYERS_CACHE.items()}
        _PLAYERS_MTIME = mtime
    return _PLAYERS_CACHE


def _find(mapping: dict, by_canon: dict, team_name: str):
    """Cocokkan nama apa pun: persis -> kanonik -> lewat kanonik tiap key."""
    if not team_name:
        return None
    entry = mapping.get(team_name) or mapping.get(canonical_team(team_name))
    if entry is None and by_canon:
        entry = by_canon.get(canonical_team(team_name))
    return entry


def get_team_logo(team_name: str) -> str:
    entry = _find(_load_logos(), _LOGOS_BY_CANON, team_name)
    return (entry or {}).get("logo_url") or PLACEHOLDER_LOGO


def get_key_player(team_name: str) -> dict:
    entry = _find(_load_players(), _PLAYERS_BY_CANON, team_name)
    return entry or {"player_name": "Key Player", "position": "N/A", "image": None}
