"""Resolver path absolut berdasarkan lokasi modul (aman dari CWD berbeda)."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

HISTORICAL_MATCHES = BASE_DIR / "historical_matches.csv"
UPCOMING_FIXTURES = BASE_DIR / "upcoming_fixtures.csv"
REAL_SHOTS_DATA = BASE_DIR / "real_shots_data.csv"
TEAM_LOGOS = BASE_DIR / "team_logos.json"
KEY_PLAYERS = BASE_DIR / "key_players.json"
XG_MODEL = BASE_DIR / "xg_model.pkl"
