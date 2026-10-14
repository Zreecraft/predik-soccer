"""SQLite database helper untuk prediction logs dan feedback loop self-learning."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "predictions.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            projected_home_goals INTEGER,
            projected_away_goals INTEGER,
            prob_home REAL,
            prob_draw REAL,
            prob_away REAL,
            actual_home_goals INTEGER DEFAULT NULL,
            actual_away_goals INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            brier_score REAL,
            accuracy REAL,
            n_samples INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calibration_factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            method TEXT NOT NULL,
            temp REAL,
            bias_home REAL,
            bias_draw REAL,
            bias_away REAL,
            n_samples INTEGER,
            brier_before REAL,
            brier_after REAL,
            active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def get_active_calibration() -> dict | None:
    """Faktor kalibrasi aktif terakhir (atau None bila belum ada / belum cukup data)."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM calibration_factors WHERE active=1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return dict(row)


init_db()
