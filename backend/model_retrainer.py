"""Self-learning engine: eval Brier/Log-Loss dari prediksi vs hasil riil, incremental XGBoost retrain."""
import sys
import numpy as np
from pathlib import Path

# Konsol Windows (cp1252) tidak bisa encode emoji log training
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from database import get_db
from train_xg_model import train_xgboost_model as train_model
from data_paths import HISTORICAL_MATCHES

MODEL_PATH = Path(__file__).resolve().parent / "data" / "xg_model.pkl"


def _outcome_class(hg: int, ag: int) -> int:
    """0=home win, 1=draw, 2=away win."""
    if hg > ag:
        return 0
    if hg == ag:
        return 1
    return 2


def sync_actuals_from_history() -> int:
    """Isi actual_home_goals/actual_away_goals dari historical_matches.csv untuk log PENDING."""
    import pandas as pd

    try:
        hist = pd.read_csv(HISTORICAL_MATCHES)
    except FileNotFoundError:
        return 0

    hist["datetime"] = pd.to_datetime(hist["datetime"], errors="coerce")
    now = pd.Timestamp.now()
    hist = hist[hist["datetime"] <= now]

    conn = get_db()
    pending = conn.execute(
        "SELECT id, home_team, away_team, timestamp FROM prediction_logs WHERE status='PENDING'"
    ).fetchall()
    updated = 0
    for row in pending:
        match = hist[
            (hist["home_team"].str.lower() == row["home_team"].lower())
            & (hist["away_team"].str.lower() == row["away_team"].lower())
        ]
        if match.empty:
            continue
        latest = match.sort_values("datetime").iloc[-1]
        conn.execute(
            "UPDATE prediction_logs SET actual_home_goals=?, actual_away_goals=? WHERE id=?",
            (int(latest["home_goals"]), int(latest["away_goals"]), row["id"]),
        )
        updated += 1
    conn.commit()
    conn.close()
    return updated


def evaluate_pending_predictions() -> dict:
    """Sinkron hasil riil + hitung Brier Score & Log-Loss, tandai EVALUATED."""
    synced = sync_actuals_from_history()

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM prediction_logs WHERE status='PENDING' "
        "AND actual_home_goals IS NOT NULL AND actual_away_goals IS NOT NULL"
    ).fetchall()

    if not rows:
        conn.close()
        return {"evaluated": 0, "synced": synced, "brier": None, "log_loss": None, "accuracy": None}

    briers, log_losses, correct = [], [], 0
    for r in rows:
        actual = _outcome_class(r["actual_home_goals"], r["actual_away_goals"])
        probs = np.array([r["prob_home"], r["prob_draw"], r["prob_away"]], dtype=float)
        probs = probs / probs.sum()  # normalisasi

        onehot = np.zeros(3)
        onehot[actual] = 1

        briers.append(float(np.sum((probs - onehot) ** 2)))
        log_losses.append(float(-np.log(max(probs[actual], 1e-10))))
        if int(np.argmax(probs)) == actual:
            correct += 1

        conn.execute("UPDATE prediction_logs SET status='EVALUATED' WHERE id=?", (r["id"],))

    brier = float(np.mean(briers))
    log_loss = float(np.mean(log_losses))
    accuracy = correct / len(rows)

    conn.execute(
        "INSERT INTO model_metrics (brier_score, accuracy, n_samples) VALUES (?, ?, ?)",
        (brier, accuracy, len(rows)),
    )
    conn.commit()
    conn.close()
    return {"evaluated": len(rows), "synced": synced, "brier": round(brier, 4), "log_loss": round(log_loss, 4), "accuracy": round(accuracy * 100, 1)}


def retrain_model() -> dict:
    """Incremental retrain XGBoost dari seluruh shot data (termasuk hasil terbaru)."""
    try:
        result = train_model()
        if not result:
            return {"retrained": False, "error": "Training dibatalkan (data tembakan tidak ada)."}
        return {"retrained": True, **result}
    except Exception as e:
        return {"retrained": False, "error": str(e)}


def get_model_stats() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) c FROM prediction_logs").fetchone()["c"]
    pending = conn.execute(
        "SELECT COUNT(*) c FROM prediction_logs WHERE status='PENDING'"
    ).fetchone()["c"]
    evaluated = conn.execute(
        "SELECT COUNT(*) c FROM prediction_logs WHERE status='EVALUATED'"
    ).fetchone()["c"]
    metrics = conn.execute(
        "SELECT * FROM model_metrics ORDER BY timestamp DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return {
        "total_predictions": total,
        "pending": pending,
        "evaluated": evaluated,
        "recent_metrics": [dict(m) for m in metrics],
        "model_file": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
    }


if __name__ == "__main__":
    print("=== Evaluasi prediksi pending ===")
    print(evaluate_pending_predictions())
    print("\n=== Retrain model ===")
    print(retrain_model())
    print("\n=== Statistik model ===")
    print(get_model_stats())
