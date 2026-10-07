"""Engine prediksi: simulasi Monte Carlo minute-by-minute + pemilihan skor proyeksi."""
import time
from collections import Counter

import numpy as np

# Batas wajar skor proyeksi (sepak bola nyata jarang > 5 gol per tim)
MAX_PROJECTED_GOALS = 5
MAX_PROJECTED_MARGIN = 4


def simulate_10k_matches_minute_by_minute(home_xg, away_xg, iterations=10000, verbose=True):
    np.random.seed(42)
    # Clamp xG per laga ke rentang wajar agar probabilitas menit tetap valid
    home_xg = float(np.clip(home_xg, 0.1, 4.0))
    away_xg = float(np.clip(away_xg, 0.1, 4.0))
    if verbose:
        print(f"\n🎮 Memulai Simulation Engine ({iterations:,} Uji Coba Pertandingan Menit 1-90)...")
    start_time = time.time()

    home_prob_per_min = home_xg / 90.0
    away_prob_per_min = away_xg / 90.0

    home_randoms = np.random.rand(iterations, 90)
    away_randoms = np.random.rand(iterations, 90)

    home_goals_per_min = (home_randoms < home_prob_per_min).astype(int)
    away_goals_per_min = (away_randoms < away_prob_per_min).astype(int)

    home_sim_goals = np.sum(home_goals_per_min, axis=1)
    away_sim_goals = np.sum(away_goals_per_min, axis=1)

    home_ht_goals = np.sum(home_goals_per_min[:, :45], axis=1)
    away_ht_goals = np.sum(away_goals_per_min[:, :45], axis=1)

    ht_over_0_5 = np.sum((home_ht_goals + away_ht_goals) > 0)
    prob_ht_goal = round((ht_over_0_5 / iterations) * 100, 1)

    if verbose:
        exec_time = round(time.time() - start_time, 2)
        print(f"⚡ Selesai! {iterations:,} Pertandingan disimulasikan dalam {exec_time} detik.")

    return home_sim_goals, away_sim_goals, prob_ht_goal


def calculate_smart_projected_score(home_sim_goals, away_sim_goals, prob_home, prob_away, home_xg, away_xg):
    """Skor proyeksi = skor paling sering muncul dari simulasi (modus),
    dibatasi wajar (maks 5 gol/tim, selisih maks 4) dan disesuaikan hasil favorit model."""
    home_sim_goals = np.asarray(home_sim_goals)
    away_sim_goals = np.asarray(away_sim_goals)
    counts = Counter(zip(home_sim_goals.tolist(), away_sim_goals.tolist()))
    total = max(1, len(home_sim_goals))

    margin = prob_home - prob_away
    xg_diff = home_xg - away_xg

    if margin >= 20.0 or xg_diff >= 0.8:
        outcome = "home"
    elif margin <= -20.0 or xg_diff <= -0.8:
        outcome = "away"
    else:
        outcome = "close"

    def acceptable(score):
        h, a = score
        if h > MAX_PROJECTED_GOALS or a > MAX_PROJECTED_GOALS:
            return False
        if abs(h - a) > MAX_PROJECTED_MARGIN:
            return False
        if outcome == "home":
            return h > a
        if outcome == "away":
            return a > h
        return abs(h - a) <= 1

    candidates = [s for s in counts if acceptable(s)]
    if not candidates:
        candidates = [s for s in counts if s[0] <= MAX_PROJECTED_GOALS and s[1] <= MAX_PROJECTED_GOALS]
    if not candidates:
        return (
            int(min(round(home_xg), MAX_PROJECTED_GOALS)),
            int(min(round(away_xg), MAX_PROJECTED_GOALS)),
            0.0,
        )

    # Paling sering muncul; tie-break: paling dekat dengan ekspektasi xG
    def rank(score):
        h, a = score
        return (-counts[score], abs(h - home_xg) + abs(a - away_xg))

    best = min(candidates, key=rank)
    confidence = round(counts[best] / total * 100, 1)
    return int(best[0]), int(best[1]), confidence
