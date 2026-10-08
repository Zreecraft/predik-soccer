"""Unduh foto bintang klub ke frontend/public/assets/players/ + perbaiki id TheSportsDB 4 klub.

Aman dijalankan berulang (resumable): file valid tidak diunduh ulang.

Pemakaian (dari folder backend/):
    python scripts/fetch_player_photos.py
"""
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Konsol Windows (cp1252) tidak bisa encode karakter khusus nama pemain
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
PLAYERS_DIR = ROOT / "frontend" / "public" / "assets" / "players"
KEY_PLAYERS = BACKEND / "data" / "key_players.json"
CLUB_PROFILES = BACKEND / "data" / "club_profiles.json"
FIXTURES = BACKEND / "data" / "upcoming_fixtures.csv"

API = "https://www.thesportsdb.com/api/v1/json/3"
UA = {"User-Agent": "Mozilla/5.0"}
SLEEP = 2.4

# id TheSportsDB yang salah (women/II/reserve/netball) -> id klub utama Soccer
FIX_TEAM_IDS = {
    "Alaves": "134221",
    "Borussia M.Gladbach": "134779",
    "Deportivo La Coruna": "133816",
    "Nottingham Forest": "133720",
    "Brighton": "133619",
}

MAGIC = (
    (b"\x89PNG", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF8", "gif"),
    (b"RIFF", "webp"),
)


def api_get(path: str, params: dict, tries: int = 3):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                wait = 10 * (attempt + 1)
                print(f"    429 rate-limit, tunggu {wait}s ...")
                time.sleep(wait)
                continue
            raise
    return {}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())


def valid_file(path: Path) -> bool:
    try:
        head = path.read_bytes()[:12]
    except OSError:
        return False
    return any(head.startswith(m) for m, _ in MAGIC)


def download(url: str, dest: Path) -> bool:
    """Unduh ke dest. True bila file valid sesudahnya."""
    if valid_file(dest):
        return False  # sudah ada (resume)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            break
        except Exception as e:
            if attempt == 2:
                print(f"    gagal unduh: {e}")
                return False
            time.sleep(4 * (attempt + 1))
    if not any(data.startswith(m) for m, _ in MAGIC) or len(data) < 1500:
        print(f"    konten bukan gambar valid ({len(data)} bytes): {url[:80]}")
        return False
    dest.write_bytes(data)
    time.sleep(0.3)
    return True


def search_player(name: str) -> dict | None:
    """Cari pemain di TheSportsDB; kandidat terbaik (nama persis diutamakan)."""
    time.sleep(SLEEP)
    d = api_get("searchplayers.php", {"p": name})
    cands = d.get("player") or []
    if not cands:
        return None
    target = norm(name)

    def score(p):
        n = norm(p.get("strPlayer"))
        if n == target:
            base = 100
        elif target in n or n in target:
            base = 70
        else:
            # toleransi satu-dua karakter beda (Mbappe/Mbappé dll sudah dinormalkan)
            base = 40 if abs(len(n) - len(target)) <= 2 and n[:4] == target[:4] else 0
        has_img = 2 if p.get("strCutout") else (1 if p.get("strThumb") else 0)
        return (base, has_img)

    best = max(cands, key=score)
    if score(best)[0] == 0:
        return None
    return best


def photo_url(p: dict) -> str | None:
    return p.get("strCutout") or p.get("strThumb") or None


def slugify(name: str) -> str:
    out = "".join(c if c.isalnum() else "_" for c in name.lower())
    return "_".join(filter(None, out.split("_")))[:40]


def squad_image(profile: dict, player_name: str) -> dict | None:
    target = norm(player_name)
    for p in profile.get("players") or []:
        n = norm(p.get("name"))
        if n == target or target in n or n in target:
            if p.get("image"):
                return p
    return None


def star_with_photo(profile: dict) -> dict | None:
    """Pemain skuad terbaik yang punya foto (prioritas posisi menyerang)."""
    players = [p for p in (profile.get("players") or []) if p.get("image")]
    if not players:
        return None

    def rank(p):
        pos = str(p.get("position") or "")
        if "Striker" in pos or "Centre-Forward" in pos:
            band = 0
        elif any(k in pos for k in ("Forward", "Winger", "Attacking Midfield")):
            band = 1
        elif "Midfield" in pos:
            band = 2
        else:
            band = 3
        return band

    return min(players, key=rank)


def fix_club_squads(profiles: dict) -> list:
    fixed = []
    for club, tid in FIX_TEAM_IDS.items():
        entry = profiles.get(club)
        if not entry:
            continue
        if entry.get("tsdb_id") == tid and any(p.get("image") for p in entry.get("players") or []):
            continue
        time.sleep(SLEEP)
        d = api_get("lookup_all_players.php", {"id": tid})
        squad = [
            {
                "name": p.get("strPlayer"),
                "position": p.get("strPosition") or "",
                "image": photo_url(p),
                "number": p.get("strNumber"),
            }
            for p in (d.get("player") or [])
            if p.get("strPlayer")
        ]
        if not squad:
            print(f"  !! {club}: skuad kosong dari id {tid}, data lama dipertahankan")
            continue
        entry["tsdb_id"] = tid
        entry["players"] = squad
        fixed.append(f"{club} (id={tid}, {len(squad)} pemain, {sum(1 for p in squad if p['image'])} foto)")
    return fixed


def main() -> None:
    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
    profiles = json.loads(CLUB_PROFILES.read_text(encoding="utf-8"))
    key_players = json.loads(KEY_PLAYERS.read_text(encoding="utf-8"))

    print("=== 1) Perbaiki id TheSportsDB klub bermasalah ===")
    for line in fix_club_squads(profiles):
        print("  fixed:", line)

    # Daftar target: klub fixtures yang star player-nya belum punya foto
    import csv

    teams = set()
    with open(FIXTURES, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            teams.add(row["home_team"])
            teams.add(row["away_team"])

    print("\n=== 2) Kumpulkan target tanpa foto ===")
    targets = []  # (club, want_name, dest_name, source_desc)
    for club in sorted(teams):
        entry = key_players.get(club)
        profile = profiles.get(club) or {}
        if entry and entry.get("image"):
            dest_name = Path(entry["image"]).name
            if valid_file(PLAYERS_DIR / dest_name):
                continue  # sudah ada
            targets.append((club, entry["player_name"], dest_name, "key_players"))
        else:
            # klub tanpa foto: pakai bintang skuad yang berfoto
            star = star_with_photo(profile)
            if not star:
                # skuad tak berfoto -> cari via API pakai nama pemain pertama
                any_p = (profile.get("players") or [{}])[0]
                star = {"name": any_p.get("name"), "position": any_p.get("position"), "image": None}
            if not star or not star.get("name"):
                print(f"  !! {club}: tidak ada kandidat nama pemain")
                continue
            dest_name = f"{slugify(star['name'])}.png"
            if valid_file(PLAYERS_DIR / dest_name):
                # file sudah ada, pastikan entry key_players menunjuk ke sana
                key_players[club] = {
                    "player_name": star["name"],
                    "position": (star.get("position") or "").split(" ")[0] or "N/A",
                    "image": f"/assets/players/{dest_name}",
                }
                continue
            targets.append((club, star["name"], dest_name, "squad"))
            key_players[club] = {
                "player_name": star["name"],
                "position": (star.get("position") or "").split(" ")[0] or "N/A",
                "image": f"/assets/players/{dest_name}",
            }

    print(f"  target: {len(targets)} klub")

    print("\n=== 3) Unduh foto ===")
    ok, fail = [], []
    for i, (club, want, dest_name, source) in enumerate(targets, 1):
        dest = PLAYERS_DIR / dest_name
        url = None
        used = want

        # a) foto dari skuad club_profiles
        sq = squad_image(profiles.get(club) or {}, want)
        if sq:
            url = sq.get("image")
            used = sq.get("name")
        # b) cari di TheSportsDB
        if not url:
            print(f"  [{i}/{len(targets)}] {club}: '{want}' -> search API ...")
            p = search_player(want)
            if p:
                url = photo_url(p)
                used = p.get("strPlayer") or want

        if not url:
            # c) fallback: pemain skuad lain yang berfoto
            star = star_with_photo(profiles.get(club) or {})
            if star:
                url = star.get("image")
                used = star.get("name")
                dest = PLAYERS_DIR / f"{slugify(used)}.png"
                dest_name = dest.name
                key_players[club] = {
                    "player_name": used,
                    "position": (star.get("position") or "").split(" ")[0] or "N/A",
                    "image": f"/assets/players/{dest_name}",
                }

        if not url:
            print(f"  FAIL {club}: '{want}' tidak menemukan foto")
            fail.append(club)
            continue

        if download(url, dest):
            print(f"  OK   {club}: {used} -> {dest_name} ({dest.stat().st_size // 1024} KB)")
        else:
            if valid_file(dest):
                print(f"  OK   {club}: {dest_name} (sudah ada)")
            else:
                print(f"  FAIL {club}: unduhan tidak valid")
                fail.append(club)
                continue
        # pastikan entry key_players konsisten dengan file yang diunduh
        if key_players.get(club, {}).get("image") != f"/assets/players/{dest_name}":
            prev = key_players.get(club) or {}
            key_players[club] = {
                "player_name": used,
                "position": prev.get("position") or "N/A",
                "image": f"/assets/players/{dest_name}",
            }
        ok.append(club)

    CLUB_PROFILES.write_text(json.dumps(profiles, ensure_ascii=False, indent=4), encoding="utf-8")
    KEY_PLAYERS.write_text(json.dumps(key_players, ensure_ascii=False, indent=4), encoding="utf-8")

    print(f"\n=== Ringkasan: {len(ok)} unduhan OK, {len(fail)} gagal ===")
    if fail:
        print("GAGAL:", ", ".join(fail))
        sys.exit(1)
    print("SELESAI — semua klub punya foto pemain.")


if __name__ == "__main__":
    main()
