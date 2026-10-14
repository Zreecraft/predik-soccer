"""Fase 2: isi aset yang hilang — logo tim (team_logos.json) & cutout pemain (club_profiles.json).

- Logo : cari badge TheSportsDB untuk tim yang belum ada / belum punya logo_url.
- Pemain: per klub (lookup_all_players by tsdb_id) → upgrade gambar ke strCutout
  (remove-bg) bila tersedia; pemain tanpa gambar diisi cutout bila ketemu.

Resumable & aman diulang: entri yang sudah lengkap dilewati, data lama tidak dihapus.
Rate-limit 2.4s (hormati TheSportsDB free tier).

Pemakaian (dari folder backend/):
    python scripts/fetch_missing_assets.py            # logo + pemain
    python scripts/fetch_missing_assets.py --logos    # logo saja
    python scripts/fetch_missing_assets.py --players  # pemain saja
    python scripts/fetch_missing_assets.py --dry-run  # laporan tanpa menulis
"""
import argparse
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_paths import CLUB_PROFILES, TEAM_LOGOS  # noqa: E402
from team_aliases import alias_variants, canonical_team  # noqa: E402
from ucl_simulator import UCL_TEAMS  # noqa: E402
import pandas as pd  # noqa: E402

API = "https://www.thesportsdb.com/api/v1/json/3"
UA = {"User-Agent": "Mozilla/5.0"}
SLEEP = 2.4

PLACEHOLDER_TAILS = ("placeholder.png", "badge.png")


def api_get(path: str, params: dict, tries: int = 3) -> dict:
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                wait = 15 * (attempt + 1)
                print(f"    429 rate-limit, tunggu {wait}s ...")
                time.sleep(wait)
                continue
            print(f"    HTTP {e.code} ({path}), retry ...")
        except Exception as e:
            print(f"    {type(e).__name__} ({path}), retry ...")
        time.sleep(4 * (attempt + 1))
    return {}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())


def words(s: str) -> list:
    """Kata-kata ternormalisasi (spasi dipertahankan) — untuk pisah nama depan/belakang."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return ["".join(c for c in w if c.isalnum()) for w in s.lower().split() if w]


# ---------------- LOGO ----------------
def _team_candidates() -> dict:
    """nama apa pun (kunci team_logos / historis / UCL / profil) -> daftar varian query."""
    logos = json.loads(TEAM_LOGOS.read_text(encoding="utf-8"))
    all_names: set[str] = set(logos.keys())

    try:
        hist = pd.read_csv("data/historical_matches.csv", usecols=["home_team", "away_team"])
        all_names |= set(hist["home_team"]) | set(hist["away_team"])
    except Exception:
        pass
    try:
        fx = pd.read_csv("data/upcoming_fixtures.csv", usecols=["home_team", "away_team"])
        all_names |= set(fx["home_team"]) | set(fx["away_team"])
    except Exception:
        pass
    profiles = json.loads(CLUB_PROFILES.read_text(encoding="utf-8"))
    all_names |= set(profiles.keys())
    all_names |= set(UCL_TEAMS)

    by_canon = {}
    for name in all_names:
        by_canon.setdefault(canonical_team(name), set()).add(name)

    need = {}
    for canon, variants in by_canon.items():
        entry = None
        for v in variants:
            e = logos.get(v) or logos.get(canon)
            if e:
                entry = e
                break
        url = (entry or {}).get("logo_url") or ""
        if url and not url.endswith(PLACEHOLDER_TAILS):
            continue  # sudah ada logo asli
        queries = list(dict.fromkeys(SPECIAL_QUERIES.get(canon, []) + [canon, *sorted(alias_variants(canon))]))
        # varian tambahan umum: hubung & spasi
        extra = set()
        for q in list(queries):
            if "-" in q:
                extra.add(q.replace("-", " "))
            if " " in q:
                extra.add(q.replace(" ", "-"))
        need[canon] = list(dict.fromkeys(queries + sorted(extra)))
    return need


# Query ekstra untuk tim yang namanya berbeda di TheSportsDB
SPECIAL_QUERIES = {
    "Hertha Berlin": ["Hertha BSC"],
    "Greuther Fuerth": ["SpVgg Greuther Furth", "1. FC Greuther Furth", "Furth"],
    "Reims": ["Stade de Reims"],
    "Wolverhampton": ["Wolverhampton Wanderers"],
    "Leicester": ["Leicester City"],
    "Norwich": ["Norwich City"],
    "Verona": ["Hellas Verona"],
    "West Ham": ["West Ham United"],
}


def search_badge(query: str) -> tuple[str, str] | None:
    """Cari badge. Tolak tim wanita/umur muda & tim dengan nama jauh berbeda."""
    d = api_get("searchteams.php", {"t": query})
    qn = norm(query)
    best = None
    best_score = 0
    for t in d.get("teams") or []:
        sport = (t.get("strSport") or "").lower()
        badge = t.get("strBadge") or t.get("strTeamBadge")
        if sport != "soccer" or not badge:
            continue
        name = norm(t.get("strTeam") or "")
        if not name:
            continue
        # Tolak tim wanita / reservi / akademi (bukan tim utama yang dicari)
        raw_lower = (t.get("strTeam") or "").lower()
        if any(bad in raw_lower for bad in ("women", "u21", "u23", "u19", "u18", "youth", "reserves")):
            continue
        if name == qn:
            score = 100
        elif name.startswith(qn) or qn.startswith(name):
            score = 80  # prefix (mis. "heidenheim" vs "fc heidenheim")
        elif qn in name or name in qn:
            score = 50
        else:
            continue
        if score > best_score:
            best, best_score = (t.get("strTeam") or query, badge), score
    return best if best_score >= 50 else None


def fetch_logos(dry: bool) -> tuple[int, list[str]]:
    logos = json.loads(TEAM_LOGOS.read_text(encoding="utf-8"))
    need = _team_candidates()
    print(f"=== LOGO: {len(need)} tim perlu logo ===")
    ok, missing = 0, []
    for canon in sorted(need):
        found = None
        for q in need[canon]:
            time.sleep(SLEEP)
            found = search_badge(q)
            if found:
                break
        if found:
            name, badge = found
            print(f"OK  {canon:<26} <- {name}: {badge[:70]}")
            if not dry:
                old = logos.get(canon) or {}
                logos[canon] = {"league": old.get("league", "Unknown"), "logo_url": badge}
            ok += 1
        else:
            missing.append(canon)
            print(f"MISS {canon}")
    if not dry:
        TEAM_LOGOS.write_text(json.dumps(logos, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"team_logos.json disimpan (+{ok})")
    return ok, missing


# ---------------- PEMAIN (cutout / remove-bg) ----------------
def _pick_player(name: str, team: str, players: list[dict]) -> dict | None:
    """Kandidat terbaik: nama depan+belakang wajib nyambung, wajib punya strCutout.

    Kecocokan parsial longgar (hanya nama depan) sering salah sasaran —
    ditolak di sini: minimal kata belakang (surname) harus identik.
    """
    target = norm(name)
    tteam = norm(team)
    if not target:
        return None
    t_parts = words(name)
    # kata belakang (surname) target — syarat wajib kecocokan
    t_last = t_parts[-1] if t_parts else ""
    t_first = t_parts[0] if len(t_parts) > 1 else ""
    best, best_score = None, 0
    for p in players:
        p_full = norm(p.get("strPlayer") or "")
        if not p.get("strCutout") or not p_full:
            continue
        p_parts = words(p.get("strPlayer") or "")
        p_last = p_parts[-1] if p_parts else ""
        p_first = p_parts[0] if len(p_parts) > 1 else ""
        # syarat ketat: nama persis, atau surname identik + nama depan mirip
        if p_full == target:
            base = 100
        elif t_last and p_last == t_last and len(t_last) >= 4:
            if t_first and p_first and (t_first == p_first or t_first[:5] == p_first[:5]):
                base = 85
            elif t_first and p_first and t_first[:4] == p_first[:4]:
                base = 70
            else:
                continue  # depan beda → kemungkinan orang berbeda
        else:
            continue
        pteam = norm(p.get("strTeam") or "")
        team_bonus = 15 if pteam and (pteam == tteam or pteam in tteam or tteam in pteam) else 0
        score = base + team_bonus
        if score > best_score:
            best, best_score = p, score
    return best


def fetch_cutouts(dry: bool) -> tuple[int, int]:
    profiles = json.loads(CLUB_PROFILES.read_text(encoding="utf-8"))

    # kelompokkan target per klub (punya tsdb_id -> lookup bulk)
    targets: dict[str, list[dict]] = {}
    for club, entry in profiles.items():
        for pl in entry.get("players") or []:
            im = pl.get("image") or ""
            if im and "cutout" in im:
                continue  # sudah remove-bg
            if not entry.get("tsdb_id"):
                continue
            targets.setdefault(club, []).append(pl)

    total_players = sum(len(v) for v in targets.values())
    print(f"=== CUTOUT: {total_players} pemain di {len(targets)} klub ===")
    upgraded, no_cutout = 0, 0
    for club in sorted(targets):
        tid = profiles[club]["tsdb_id"]
        time.sleep(SLEEP)
        d = api_get("lookup_all_players.php", {"id": tid})
        pool = d.get("player") or []
        if not pool:
            print(f"  !! {club}: lookup kosong (id {tid}), dilewati")
            no_cutout += len(targets[club])
            continue
        for pl in targets[club]:
            cand = _pick_player(pl.get("name") or "", club, pool)
            if cand:
                url = cand["strCutout"]
                print(f"  OK  {club}: {pl.get('name')} <- {cand.get('strPlayer')}")
                if not dry:
                    pl["image"] = url
                upgraded += 1
            else:
                no_cutout += 1
        if dry:
            continue
    if not dry:
        CLUB_PROFILES.write_text(json.dumps(profiles, indent=4, ensure_ascii=False), encoding="utf-8")
        print(f"club_profiles.json disimpan (+{upgraded} cutout)")
    print(f"cutout ditemukan: {upgraded} | tidak tersedia: {no_cutout}")
    return upgraded, no_cutout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logos", action="store_true")
    ap.add_argument("--players", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    do_all = not (args.logos or args.players)

    if do_all or args.logos:
        ok, missing = fetch_logos(args.dry_run)
        print(f"\nLogo: +{ok}, miss {len(missing)}")
        if missing:
            print("  Masih miss:", ", ".join(missing))
    if do_all or args.players:
        fetch_cutouts(args.dry_run)


if __name__ == "__main__":
    main()
