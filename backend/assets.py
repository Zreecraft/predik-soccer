"""Aset statis: logo tim & pemain kunci (di-cache satu kali)."""
import json

from data_paths import KEY_PLAYERS, TEAM_LOGOS
from team_aliases import canonical_team

_LOGOS_CACHE = None
_PLAYERS_CACHE = None

PLACEHOLDER_LOGO = "https://via.placeholder.com/150?text=No+Logo"


def _load_logos() -> dict:
    global _LOGOS_CACHE
    if _LOGOS_CACHE is None:
        try:
            with open(TEAM_LOGOS, "r", encoding="utf-8") as f:
                _LOGOS_CACHE = json.load(f)
        except Exception:
            _LOGOS_CACHE = {}
    return _LOGOS_CACHE


def _load_players() -> dict:
    global _PLAYERS_CACHE
    if _PLAYERS_CACHE is None:
        try:
            with open(KEY_PLAYERS, "r", encoding="utf-8") as f:
                _PLAYERS_CACHE = json.load(f)
        except Exception:
            _PLAYERS_CACHE = {}
    return _PLAYERS_CACHE


def get_team_logo(team_name: str) -> str:
    logos = _load_logos()
    entry = logos.get(team_name) or logos.get(canonical_team(team_name))
    return (entry or {}).get("logo_url") or PLACEHOLDER_LOGO


def get_key_player(team_name: str) -> dict:
    players = _load_players()
    entry = players.get(team_name) or players.get(canonical_team(team_name))
    return entry or {"player_name": "Key Player", "position": "N/A", "image": None}
