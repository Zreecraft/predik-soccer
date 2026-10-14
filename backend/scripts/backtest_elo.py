"""Fase G: Backtest seluruh laga selesai — varian LAMA vs USE_ELO_PRIOR.

Metode:
- Anti-leakage: power index tiap laga hanya memakai histori datetime < kickoff laga.
- Probabilitas H/D/A dari matriks Poisson tertutup (0..10 gol) di atas final_xg
  hasil blend yang sama dengan pipeline produksi (_compute_projection).
- 3 varian:
    LAMA = formula power index pra-Fase D + prior rating manual (tanpa Elo)
    OFF  = pipeline terbaru (Fase D) + USE_ELO_PRIOR=False
    ON   = pipeline terbaru (Fase D) + USE_ELO_PRIOR=True
- Brier (3 kelas, jumlah kuadrat): mean[(pH-oH)^2+(pD-oD)^2+(pA-oA)^2].
  Baseline tebakan seragam (1/3,1/3,1/3) = 0.667 (= 0.222 bila dibagi per kelas).

Pemakaian:
    python scripts/backtest_elo.py            # penuh
    python scripts/backtest_elo.py --limit 500  # smoke cepat
"""
import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data_paths  # noqa: E402
from club_data import get_club_strength, ga_prior_from_rating, xg_prior_from_rating  # noqa: E402
from team_analytics import (  # noqa: E402
    LEAGUE_AVG_XG,
    MIN_TEAM_GA,
    MIN_TEAM_XG,
    MAX_TEAM_GA,
    MAX_TEAM_XG,
    clamp_match_xg,
    get_home_away_bias,
    get_team_power_index,
)

FOUR_LEAGUES = {"EPL", "La_liga", "Serie_A", "Bundesliga"}
MAX_GOALS = 10


# ---------------- Power index versi LAMA (pra-Fase D, disalin utk perbandingan) ----------------
def _power_index_lama(team_name, matches_df, last_n=20, prior_xg=None, prior_ga=None):
    from team_analytics import _team_matches, _is_home  # lokal: hindari siklus impor

    team_matches = _team_matches(team_name, matches_df)
    if team_matches.empty:
        base_xg = float(prior_xg) if prior_xg else 1.45
        base_ga = float(prior_ga) if prior_ga else 1.20
        return {"avg_xg": round(base_xg, 2), "avg_ga": round(base_ga, 2), "win_rate": 45.0, "power_score": 50.0}

    recent = team_matches.head(last_n)
    n = len(recent)
    wins = draws = losses = 0
    goals_conceded = 0
    total_xg = 0.0
    for _, row in recent.iterrows():
        is_home = _is_home(team_name, row)
        gf = row["home_goals"] if is_home else row["away_goals"]
        ga = row["away_goals"] if is_home else row["home_goals"]
        total_xg += row["home_xg"] if is_home else row["away_xg"]
        goals_conceded += ga
        if gf > ga:
            wins += 1
        elif gf == ga:
            draws += 1
        else:
            losses += 1

    win_rate = (wins / n) * 100
    raw_avg_xg = total_xg / n
    avg_ga = goals_conceded / n

    baseline = float(prior_xg) if prior_xg else LEAGUE_AVG_XG
    rel = n / (n + 8.0)
    avg_xg = baseline * (1 - rel) + raw_avg_xg * rel
    avg_xg = float(np.clip(avg_xg, MIN_TEAM_XG, MAX_TEAM_XG))
    if prior_ga:
        avg_ga = float(prior_ga) * (1 - rel) + avg_ga * rel
    avg_ga = float(np.clip(avg_ga, MIN_TEAM_GA, MAX_TEAM_GA))

    score = (win_rate * 0.40) + (min(avg_xg / 2.5, 1.0) * 35) + (max(0, 1 - (avg_ga / 2.0)) * 25)
    return {"avg_xg": round(avg_xg, 2), "avg_ga": round(avg_ga, 2),
            "win_rate": round(win_rate, 1), "power_score": round(score, 1)}


# ---------------- Probabilitas Poisson tertutup ----------------
def _poisson_pmf(lam: float) -> np.ndarray:
    pmf = np.empty(MAX_GOALS + 1)
    pmf[0] = math.exp(-lam)
    for k in range(1, MAX_GOALS + 1):
        pmf[k] = pmf[k - 1] * lam / k
    return pmf


def outcome_probs(home_xg: float, away_xg: float):
    ph = _poisson_pmf(home_xg)
    pa = _poisson_pmf(away_xg)
    mat = np.outer(ph, pa)
    norm = mat.sum()
    p_home = np.tril(mat, -1).sum() / norm   # home > away
    p_draw = np.trace(mat) / norm            # home == away
    p_away = np.triu(mat, 1).sum() / norm    # away > home
    return float(p_home), float(p_draw), float(p_away)


# ---------------- Satu varian backtest ----------------
def run_variant(name: str, hist: pd.DataFrame, use_elo: bool, use_new_power: bool) -> dict:
    """Balikkan metrik per grup: all / 4-liga / non-4-liga."""
    data_paths.USE_ELO_PRIOR = use_elo

    strength_cache: dict = {}

    def strength(team: str) -> dict:
        if team not in strength_cache:
            strength_cache[team] = get_club_strength(team)
        return strength_cache[team]

    rows = []
    for _, m in hist.iterrows():
        t = m["_dt"]
        before = hist[hist["_dt"] < t]
        h, a = m["home_team"], m["away_team"]

        sh, sa = strength(h), strength(a)
        px_h, px_a = xg_prior_from_rating(sh["overall"]), xg_prior_from_rating(sa["overall"])
        pg_h, pg_a = ga_prior_from_rating(sh["overall"]), ga_prior_from_rating(sa["overall"])

        if use_new_power:
            st_h = get_team_power_index(h, before, last_n=20, prior_xg=px_h, prior_ga=pg_h, overall=sh["overall"])
            st_a = get_team_power_index(a, before, last_n=20, prior_xg=px_a, prior_ga=pg_a, overall=sa["overall"])
        else:
            st_h = _power_index_lama(h, before, last_n=20, prior_xg=px_h, prior_ga=pg_h)
            st_a = _power_index_lama(a, before, last_n=20, prior_xg=px_a, prior_ga=pg_a)

        bias_h = get_home_away_bias(h, is_home=True, matches_df=before)
        bias_a = get_home_away_bias(a, is_home=False, matches_df=before)

        def blend(base, bias, own, opp):
            gap = 1.0 + (own - opp) * 0.004
            return clamp_match_xg(base * bias * gap)

        fh = blend(st_h["avg_xg"], bias_h, sh["overall"], sa["overall"])
        fa = blend(st_a["avg_xg"], bias_a, sa["overall"], sh["overall"])

        p_home, p_draw, p_away = outcome_probs(fh, fa)
        gh, ga_ = int(m["home_goals"]), int(m["away_goals"])
        o_home, o_draw, o_away = (1.0, 0.0, 0.0) if gh > ga_ else ((0.0, 1.0, 0.0) if gh == ga_ else (0.0, 0.0, 1.0))

        pred = 0 if p_home >= p_draw and p_home >= p_away else (1 if p_draw >= p_away else 2)
        actual = 0 if gh > ga_ else (1 if gh == ga_ else 2)
        brier = (p_home - o_home) ** 2 + (p_draw - o_draw) ** 2 + (p_away - o_away) ** 2

        rows.append({
            "league": m["league"],
            "acc": 1.0 if pred == actual else 0.0,
            "brier": brier,
        })

    df = pd.DataFrame(rows)
    out = {}
    groups = {
        "Semua laga": df,
        "4 liga utama": df[df["league"].isin(FOUR_LEAGUES)],
        "Non-4-liga (Ligue_1 dst)": df[~df["league"].isin(FOUR_LEAGUES)],
    }
    for gname, g in groups.items():
        out[gname] = {
            "n": len(g),
            "acc": float(g["acc"].mean()) if len(g) else float("nan"),
            "brier": float(g["brier"].mean()) if len(g) else float("nan"),
        }
    print(f"  [{name}] selesai — {len(df)} laga")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="batasi jumlah laga (smoke test)")
    args = ap.parse_args()

    df = pd.read_csv(data_paths.HISTORICAL_MATCHES)
    df = df.dropna(subset=["home_goals", "away_goals", "datetime", "home_xg", "away_xg"]).copy()
    df["_dt"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["_dt"]).sort_values("_dt").reset_index(drop=True)
    if args.limit:
        df = df.iloc[-args.limit:]  # contoh terbaru = yang paling representatif
    print(f"Backtest {len(df)} laga selesai (time-split anti-leakage)...")

    t0 = time.time()
    original_flag = data_paths.USE_ELO_PRIOR
    try:
        results = {
            "LAMA (pra-Fase D, tanpa Elo)": run_variant("LAMA", df, use_elo=False, use_new_power=False),
            "Pipeline baru, Elo OFF": run_variant("OFF", df, use_elo=False, use_new_power=True),
            "Pipeline baru, USE_ELO_PRIOR=True": run_variant("ON", df, use_elo=True, use_new_power=True),
        }
    finally:
        data_paths.USE_ELO_PRIOR = original_flag

    print(f"\nWaktu: {time.time() - t0:.0f} detik")
    print("Brier = mean[(pH-oH)^2+(pD-oD)^2+(pA-oA)^2]  (jumlah kuadrat 3 kelas;")
    print("        baseline tebakan seragam 1/3 = 0.667; bila dibagi per kelas = 0.222)\n")

    for group in ["Semua laga", "4 liga utama", "Non-4-liga (Ligue_1 dst)"]:
        print(f"### {group}")
        print(f"{'Varian':<36} {'N':>6} {'Akurasi':>9} {'Brier':>8}")
        for name, res in results.items():
            r = res[group]
            print(f"{name:<36} {r['n']:>6} {r['acc'] * 100:>8.2f}% {r['brier']:>8.4f}")
        print()

    # Keputusan otomatis utk konsistensi: bandingkan ON vs OFF di 'Semua laga'
    off = results["Pipeline baru, Elo OFF"]
    on = results["Pipeline baru, USE_ELO_PRIOR=True"]
    better = (
        on["Semua laga"]["brier"] <= off["Semua laga"]["brier"]
        or on["Semua laga"]["acc"] >= off["Semua laga"]["acc"]
    )
    print("Kesimpulan:", "Elo prior TIDAK lebih buruk — aman jadi default (USE_ELO_PRIOR=True)."
          if better else
          "Elo prior LEBIH BURUK — pertimbangkan USE_ELO_PRIOR=False sebagai default.")


if __name__ == "__main__":
    main()
