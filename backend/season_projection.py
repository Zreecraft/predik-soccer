"""Proyeksi klasemen akhir musim via Monte Carlo sisa pertandingan."""
import numpy as np
import pandas as pd
from functools import lru_cache

from data_paths import HISTORICAL_MATCHES, UPCOMING_FIXTURES
from team_analytics import get_team_power_index, get_home_away_bias

LEAGUE_META = {
    "EPL": {"name": "English Premier League", "country": "England", "teams_per_league": 20},
    "La_liga": {"name": "La Liga", "country": "Spain", "teams_per_league": 20},
    "Serie_A": {"name": "Serie A", "country": "Italy", "teams_per_league": 20},
    "Bundesliga": {"name": "Bundesliga", "country": "Germany", "teams_per_league": 18},
}


def _compute_actual_table(league_matches: pd.DataFrame) -> dict:
    teams = set(league_matches["home_team"]).union(set(league_matches["away_team"]))
    table = {t: {"P": 0, "PTS": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0} for t in teams}
    for _, row in league_matches.iterrows():
        h, a = row["home_team"], row["away_team"]
        hg, ag = int(row["home_goals"]), int(row["away_goals"])
        table[h]["P"] += 1
        table[a]["P"] += 1
        table[h]["GF"] += hg
        table[h]["GA"] += ag
        table[a]["GF"] += ag
        table[a]["GA"] += hg
        if hg > ag:
            table[h]["PTS"] += 3
            table[h]["W"] += 1
            table[a]["L"] += 1
        elif ag > hg:
            table[a]["PTS"] += 3
            table[a]["W"] += 1
            table[h]["L"] += 1
        else:
            table[h]["PTS"] += 1
            table[a]["PTS"] += 1
            table[h]["D"] += 1
            table[a]["D"] += 1
    for t in table:
        table[t]["GD"] = table[t]["GF"] - table[t]["GA"]
    return table


def _simulate_remaining_fixtures(league_fixtures: pd.DataFrame, historical_df: pd.DataFrame, rng: np.random.Generator):
    """Simulasi satu musim penuh sisa pertandingan -> dict skor per fixture."""
    results = []
    for _, row in league_fixtures.iterrows():
        h_team, a_team = row["home_team"], row["away_team"]
        h_stats = get_team_power_index(h_team, historical_df, last_n=20)
        a_stats = get_team_power_index(a_team, historical_df, last_n=20)
        h_bias = get_home_away_bias(h_team, is_home=True, matches_df=historical_df)
        a_bias = get_home_away_bias(a_team, is_home=False, matches_df=historical_df)
        h_xg = max(0.3, h_stats["avg_xg"] * h_bias)
        a_xg = max(0.3, a_stats["avg_xg"] * a_bias)
        hg = int(rng.poisson(h_xg))
        ag = int(rng.poisson(a_xg))
        results.append((h_team, a_team, hg, ag, h_xg, a_xg))
    return results


@lru_cache(maxsize=8)
def project_league(league_code: str, n_seasons: int = 350) -> dict:
    historical_df = pd.read_csv(HISTORICAL_MATCHES)
    fixtures_df = pd.read_csv(UPCOMING_FIXTURES)

    league_history = historical_df[historical_df["league"] == league_code].copy()
    league_fixtures = fixtures_df[fixtures_df["league"] == league_code].copy()
    if league_history.empty and league_fixtures.empty:
        raise ValueError(f"Tidak ada data untuk liga '{league_code}'")

    teams = sorted(
        set(league_history["home_team"]).union(set(league_history["away_team"]))
        .union(set(league_fixtures["home_team"]))
        .union(set(league_fixtures["away_team"]))
    )
    actual = _compute_actual_table(league_history) if not league_history.empty else {
        t: {"P": 0, "PTS": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0} for t in teams
    }

    # Cache xG power per tim (dihitung sekali, bukan per iterasi)
    power_cache = {}
    for t in teams:
        stats = get_team_power_index(t, historical_df, last_n=20)
        h_bias = get_home_away_bias(t, is_home=True, matches_df=historical_df)
        a_bias = get_home_away_bias(t, is_home=False, matches_df=historical_df)
        power_cache[t] = {
            "h_xg": max(0.3, stats["avg_xg"] * h_bias),
            "a_xg": max(0.3, stats["avg_xg"] * a_bias),
        }

    remaining = []
    for _, row in league_fixtures.iterrows():
        h, a = row["home_team"], row["away_team"]
        if h not in power_cache or a not in power_cache:
            continue
        remaining.append((h, a, power_cache[h]["h_xg"], power_cache[a]["a_xg"]))

    rng = np.random.default_rng(42)
    title_counts = {t: 0 for t in teams}
    top4_counts = {t: 0 for t in teams}
    releg_counts = {t: 0 for t in teams}
    points_samples = {t: [] for t in teams}
    # Trajectory: rata-rata poin kumulatif per "pekan proxy" untuk top 3 saat ini
    trajectory_samples = []

    for _ in range(n_seasons):
        pts = {t: actual.get(t, {}).get("PTS", 0) for t in teams}
        played = {t: actual.get(t, {}).get("P", 0) for t in teams}
        gd = {t: actual.get(t, {}).get("GD", 0) for t in teams}
        gf = {t: actual.get(t, {}).get("GF", 0) for t in teams}

        # Simulasi sisa laga
        sim_path = {t: [pts[t]] for t in teams}
        batch_size = max(1, len(remaining) // 38) if remaining else 1
        if remaining:
            for idx, (h, a, h_xg, a_xg) in enumerate(remaining):
                hg = int(rng.poisson(h_xg))
                ag = int(rng.poisson(a_xg))
                pts[h] += 3 if hg > ag else (1 if hg == ag else 0)
                pts[a] += 3 if ag > hg else (1 if hg == ag else 0)
                played[h] += 1
                played[a] += 1
                gd[h] += hg - ag
                gd[a] += ag - hg
                gf[h] += hg
                gf[a] += ag
                # sampling trajectory tiap batch
                if (idx + 1) % batch_size == 0 or idx == len(remaining) - 1:
                    for t in teams:
                        sim_path[t].append(pts[t])

        order = sorted(teams, key=lambda t: (-pts[t], -gd[t], -gf[t]))
        title_counts[order[0]] += 1
        for t in order[:4]:
            top4_counts[t] += 1
        n_teams = len(teams)
        n_rel = 3 if n_teams >= 18 else 2
        for t in order[-n_rel:]:
            releg_counts[t] += 1
        for t in teams:
            points_samples[t].append(pts[t])

        if len(trajectory_samples) == 0:
            # snapshot path untuk tim teratas saat ini (dari actual + simulasi berjalan)
            pass
        trajectory_samples.append({t: sim_path[t] for t in teams})

    # Ambil path rata-rata untuk 3 besar berdasarkan proyeksi rata-rata poin
    avg_pts = {t: float(np.mean(points_samples[t])) for t in teams}
    top3 = sorted(teams, key=lambda t: -avg_pts[t])[:3]
    # Resample trajectory ke 38 titik
    trajectory = {}
    for t in top3:
        paths = [trajectory_samples[i][t] for i in range(min(len(trajectory_samples), 80))]
        max_len = max(len(p) for p in paths) if paths else 1
        resampled = []
        for step in range(38):
            vals = []
            for p in paths:
                idx = min(len(p) - 1, int(step / 37 * (len(p) - 1)))
                vals.append(p[idx])
            resampled.append(round(float(np.mean(vals)), 2) if vals else 0.0)
        trajectory[t] = resampled

    # KPI ambang batas
    all_final_pts = []
    for t in teams:
        all_final_pts.extend(points_samples[t])
    # approx title threshold = poin juara rerata
    title_winner_pts = []
    for i in range(n_seasons):
        season_pts = [points_samples[t][i] for t in teams]
        title_winner_pts.append(max(season_pts))
    # Top4 line: rerata poin klub di posisi ke-4
    fourth_pts = []
    for i in range(n_seasons):
        season_pts = sorted([points_samples[t][i] for t in teams], reverse=True)
        fourth_pts.append(season_pts[3] if len(season_pts) >= 4 else season_pts[-1])
    releg_survival = []
    n_teams = len(teams)
    n_rel = 3 if n_teams >= 18 else 2
    for i in range(n_seasons):
        season_pts = sorted([points_samples[t][i] for t in teams], reverse=True)
        releg_survival.append(season_pts[-n_rel - 1] if len(season_pts) > n_rel else season_pts[0])

    title_threshold = round(float(np.mean(title_winner_pts)), 1)
    ucl_threshold = round(float(np.mean(fourth_pts)), 1)
    relegation_line = round(float(np.mean(releg_survival)), 1)

    # RMSE / dispersi: std proyeksi poin per tim dibagi rata-rata
    dispersions = []
    for t in teams:
        arr = np.array(points_samples[t], dtype=float)
        if len(arr) > 1:
            dispersions.append(float(np.std(arr)))
    rmse_pct = round(float(np.mean(dispersions)) / max(title_threshold, 1) * 100, 1) if dispersions else 0.0

    rows = []
    for t in teams:
        a = actual.get(t, {"P": 0, "PTS": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0})
        arr = np.array(points_samples[t], dtype=float)
        rows.append({
            "team": t,
            "P": int(a["P"]),
            "W": int(a["W"]),
            "D": int(a["D"]),
            "L": int(a["L"]),
            "GF": int(a["GF"]),
            "GA": int(a["GA"]),
            "GD": int(a["GD"]),
            "PTS": int(a["PTS"]),
            "projected_points": round(float(np.mean(arr)), 1),
            "projected_std": round(float(np.std(arr)), 1) if len(arr) > 1 else 0.0,
            "title_pct": round(title_counts[t] / n_seasons * 100, 1),
            "top4_pct": round(top4_counts[t] / n_seasons * 100, 1),
            "relegation_pct": round(releg_counts[t] / n_seasons * 100, 1),
        })

    rows.sort(key=lambda r: (-r["projected_points"], -r["PTS"], -r["GD"]))
    for i, r in enumerate(rows):
        r["projected_position"] = i + 1

    meta = LEAGUE_META.get(league_code, {"name": league_code, "country": ""})

    return {
        "league": league_code,
        "league_name": meta.get("name", league_code),
        "country": meta.get("country", ""),
        "n_seasons": n_seasons,
        "kpi": {
            "title_threshold": title_threshold,
            "ucl_threshold": ucl_threshold,
            "relegation_line": relegation_line,
            "rmse_pct": rmse_pct,
        },
        "trajectory": trajectory,
        "standings": rows,
    }
