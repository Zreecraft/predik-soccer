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
# Elo Club (ClubElo) — dipakai Fase Elo Prior (bisa dimatikan lewat USE_ELO_PRIOR)
CLUB_ELO = DATA_DIR / "club_elo.csv"
CLUB_ELO_META = DATA_DIR / "club_elo_meta.json"
ELO_NAME_MAP = DATA_DIR / "elo_name_map.json"

# ==== Konfigurasi Elo Prior (Fase C) — satu saklar: False = perilaku lama persis ====
USE_ELO_PRIOR = True
ELO_BLEND_ELO = 0.65       # bobot overall dari Elo
ELO_BLEND_RATING = 0.15    # bobot rating manual
ELO_BLEND_COACH = 0.20     # bobot coach_rating manual
ELO_NEUTRAL_ELO = 1700.0   # Elo "netral"
ELO_NEUTRAL_OVERALL = 65.0  # overall di Elo netral
ELO_SCALE = 0.08           # poin overall per poin Elo
ELO_OVERALL_CLIP = (40.0, 95.0)

# ==== Self-learning loop (Fase 5) — satu saklar: False = prob mentah tanpa kalibrasi ====
USE_PROB_CALIBRATION = True   # koreksi probabilitas 3-kelas dari log EVALUATED
AUTO_LEARN = True             # auto-eval periodik + auto-retrain terjadwal
AUTO_EVAL_INTERVAL_H = 6      # evaluasi prediksi + refit kalibrasi tiap N jam
AUTO_RETRAIN_INTERVAL_H = 24  # retrain XGBoost tiap N jam
CALIB_MIN_SAMPLES_FIT = 60    # minimal log EVALUATED sebelum kalibrasi dipasang
CALIB_MIN_SAMPLES_BIAS = 200  # minimal log sebelum boleh fit bias per-kelas


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
