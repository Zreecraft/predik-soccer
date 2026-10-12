"""Resolver path absolut berdasarkan lokasi modul (aman dari CWD berbeda)."""
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

HISTORICAL_MATCHES = DATA_DIR / "historical_matches.csv"
UPCOMING_FIXTURES = DATA_DIR / "upcoming_fixtures.csv"
REAL_SHOTS_DATA = DATA_DIR / "real_shots_data.csv"
TEAM_LOGOS = DATA_DIR / "team_logos.json"
KEY_PLAYERS = DATA_DIR / "key_players.json"
CLUB_PROFILES = DATA_DIR / "club_profiles.json"
XG_MODEL = DATA_DIR / "xg_model.pkl"


def calendar_season() -> int:
    """Tahun mulai musim sepakbola Eropa berjalan (Agustus-Mei)."""
    now = datetime.now()
    return now.year if now.month >= 7 else now.year - 1


def filter_current_season(df):
    """Filter baris musim berjalan; fallback ke musim terbaru dalam df bila CSV belum refresh."""
    if df is None or df.empty or "season" not in df.columns:
        return df
    cs = calendar_season()
    seasons = set(df["season"].dropna().unique())
    if cs not in seasons:
        cs = max(seasons)
    return df[df["season"] == cs]
