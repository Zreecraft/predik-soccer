"""Resolver path absolut berdasarkan lokasi modul (aman dari CWD berbeda)."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

HISTORICAL_MATCHES = DATA_DIR / "historical_matches.csv"
UPCOMING_FIXTURES = DATA_DIR / "upcoming_fixtures.csv"
REAL_SHOTS_DATA = DATA_DIR / "real_shots_data.csv"
TEAM_LOGOS = DATA_DIR / "team_logos.json"
KEY_PLAYERS = DATA_DIR / "key_players.json"
XG_MODEL = DATA_DIR / "xg_model.pkl"
