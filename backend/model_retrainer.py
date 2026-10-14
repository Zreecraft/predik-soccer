"""Self-learning engine: eval Brier/Log-Loss dari prediksi vs hasil riil, incremental XGBoost retrain."""
import sys
import numpy as np
from pathlib import Path

# Konsol Windows (cp1252) tidak bisa encode emoji log training
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from database import get_db, get_active_calibration
from train_xg_model import train_xgboost_model as train_model
from data_paths import (
    HISTORICAL_MATCHES,
    USE_PROB_CALIBRATION,
    CALIB_MIN_SAMPLES_FIT,
    CALIB_MIN_SAMPLES_BIAS,
)

MODEL_PATH = Path(__file__).resolve().parent / "data" / "xg_model.pkl"

# ---- Cache faktor kalibrasi (hindari query DB tiap prediksi) ----
_CALIB_CACHE = {"ts": 0.0, "data": None}
_CALIB_TTL_SEC = 300.0


def _calibration() -> dict | None:
    """Faktor kalibrasi aktif (cache 5 menit). None bila dimatikan / belum ada / belum cukup data."""
    if not USE_PROB_CALIBRATION:
        return None
    import time as _t

    now = _t.time()
    if now - _CALIB_CACHE["ts"] < _CALIB_TTL_SEC:
        return _CALIB_CACHE["data"]
    row = get_active_calibration()
    data = None
    if row and (row.get("n_samples") or 0) >= CALIB_MIN_SAMPLES_FIT:
        data = {
            "temp": float(row.get("temp") or 1.0),
            "bias": np.array(
                [row.get("bias_home") or 0.0, row.get("bias_draw") or 0.0, row.get("bias_away") or 0.0],
                dtype=float,
            ),
        }
    _CALIB_CACHE["ts"] = now
    _CALIB_CACHE["data"] = data
    return data


def apply_probability_calibration(probs) -> list:
    """Koreksi probabilitas 3-kelas (pakai faktor aktif bila ada).

    probs: [home, draw, away] dalam skala apa pun (rasio atau persen) —
    dikalibrasi lalu diskalakan ulang ke total yang sama.
    """
    cal = _calibration()
    if cal is None:
        return [float(x) for x in probs]
    p = np.asarray(probs, dtype=float)
    total = float(p.sum())
    if total <= 0 or not np.isfinite(total):
        return [float(x) for x in probs]
    p = np.clip(p / total, 1e-9, 1.0)
    logits = np.log(p) / max(cal["temp"], 1e-3) + cal["bias"]
    e = np.exp(logits - logits.max())
    out = e / e.sum()
    return (out * total).tolist()


def _softmax_rows(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def _log_loss(P: np.ndarray, y: np.ndarray) -> float:
    idx = np.arange(len(y))
    return float(-np.log(np.clip(P[idx, y], 1e-12, 1.0)).mean())


def _brier(P: np.ndarray, y: np.ndarray) -> float:
    onehot = np.zeros_like(P)
    onehot[np.arange(len(y)), y] = 1.0
    return float(np.sum((P - onehot) ** 2, axis=1).mean())


def fit_probability_calibration() -> dict:
    """Fit temperature + prior-bias per kelas dari log EVALUATED; aktifkan faktor baru.

    Mengoreksi prediksi BERIKUTNYA: probabilitas model diluruskan agar
    kecenderungannya (over/under-confident, bias kandang) cocok dengan riil.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT prob_home, prob_draw, prob_away, actual_home_goals, actual_away_goals "
        "FROM prediction_logs WHERE status='EVALUATED' "
        "AND actual_home_goals IS NOT NULL AND actual_away_goals IS NOT NULL"
    ).fetchall()
    conn.close()

    n = len(rows)
    if n < CALIB_MIN_SAMPLES_FIT:
        return {"fitted": False, "n_samples": n,
                "reason": f"butuh >={CALIB_MIN_SAMPLES_FIT} log EVALUATED (ada {n})"}

    P = np.array([[r["prob_home"], r["prob_draw"], r["prob_away"]] for r in rows], dtype=float)
    P = P / np.clip(P.sum(axis=1, keepdims=True), 1e-9, None)
    y = np.array([_outcome_class(r["actual_home_goals"], r["actual_away_goals"]) for r in rows])

    # 1) Temperature scaling — grid search minimalkan log-loss
    logp = np.log(np.clip(P, 1e-9, 1.0))
    best_t, best_ll = 1.0, _log_loss(P, y)
    for t in np.arange(0.2, 3.01, 0.05):
        ll = _log_loss(_softmax_rows(logp / t), y)
        if ll < best_ll - 1e-6:
            best_ll, best_t = ll, float(t)

    # 2) Prior-bias per kelas (hanya bila cukup data) — koreksi frekuensi empiris
    bias = np.zeros(3)
    method = "temperature"
    if n >= CALIB_MIN_SAMPLES_BIAS:
        P_t = _softmax_rows(logp / best_t)
        emp = np.bincount(y, minlength=3) / n
        mod = P_t.mean(axis=0)
        bias = np.log(np.clip(emp, 1e-6, None)) - np.log(np.clip(mod, 1e-6, None))
        method = "temperature+prior"

    P_cal = _softmax_rows(logp / best_t + bias)
    brier_before, brier_after = _brier(P, y), _brier(P_cal, y)
    acc_before = float((P.argmax(1) == y).mean())
    acc_after = float((P_cal.argmax(1) == y).mean())

    conn = get_db()
    conn.execute("UPDATE calibration_factors SET active=0 WHERE active=1")
    conn.execute(
        "INSERT INTO calibration_factors "
        "(method, temp, bias_home, bias_draw, bias_away, n_samples, brier_before, brier_after, active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
        (method, best_t, float(bias[0]), float(bias[1]), float(bias[2]),
         n, round(brier_before, 4), round(brier_after, 4)),
    )
    conn.commit()
    conn.close()
    _CALIB_CACHE["ts"] = 0.0  # reset cache

    return {
        "fitted": True, "method": method, "n_samples": n,
        "temperature": round(best_t, 3),
        "bias": [round(float(b), 4) for b in bias],
        "brier_before": round(brier_before, 4), "brier_after": round(brier_after, 4),
        "accuracy_before": round(acc_before * 100, 1), "accuracy_after": round(acc_after * 100, 1),
    }


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
        # Anti-bocor: hanya hasil yang terjadi SETELAH prediksi dicatat
        # (laga musim lalu / laga yang sudah selesai sebelum prediksi = bukan evaluasi valid)
        ts = pd.to_datetime(row["timestamp"], errors="coerce")
        if pd.isna(ts):
            continue
        match = match[match["datetime"] > ts]
        if match.empty:
            continue
        first = match.sort_values("datetime").iloc[0]
        conn.execute(
            "UPDATE prediction_logs SET actual_home_goals=?, actual_away_goals=? WHERE id=?",
            (int(first["home_goals"]), int(first["away_goals"]), row["id"]),
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
    cal = get_active_calibration()
    return {
        "total_predictions": total,
        "pending": pending,
        "evaluated": evaluated,
        "recent_metrics": [dict(m) for m in metrics],
        "model_file": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
        "calibration": dict(cal) if cal else None,
    }


if __name__ == "__main__":
    print("=== Evaluasi prediksi pending ===")
    print(evaluate_pending_predictions())
    print("\n=== Retrain model ===")
    print(retrain_model())
    print("\n=== Statistik model ===")
    print(get_model_stats())
