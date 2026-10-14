"""Fetch rating Elo klub dari ClubElo API -> backend/data/club_elo.csv.

Sumber utama : http://api.clubelo.com/YYYY-MM-DD
               (CSV: Rank,Club,Country,Level,Elo,From,To)
Fallback      : Wayback Machine (bila API down) -> file lama tetap dipakai + peringatan log.
Cache         : 24 jam via club_elo_meta.json (timestamp fetch terakhir).

Output:
  - data/club_elo.csv       (snapshot Elo; TIDAK dihapus bila fetch gagal)
  - data/club_elo_meta.json (fetched_at ISO, source: "live"|"wayback"|"cache", url asli)

Pakai:
  python scripts/fetch_elo.py               # refresh bila cache > 24 jam
  python scripts/fetch_elo.py --force       # paksa fetch ulang
  python scripts/fetch_elo.py --unmapped    # cetak klub yang belum terpetakan di elo_name_map.json

Rate limit: 1 request per hari normalnya (cache 24 jam); fallback Wayback maks 2 request.
"""
import csv
import io
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from data_paths import CLUB_ELO, CLUB_ELO_META, ELO_NAME_MAP

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
TIMEOUT = 30  # detik per request
CACHE_HOURS = 24
REQUIRED_COLS = ["Rank", "Club", "Country", "Level", "Elo", "From", "To"]
MIN_ROWS = 100  # validasi minimal: snapshot ClubElo biasanya 600+ klub


def _get(url: str, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _get_rate_limited(url: str, timeout: int = TIMEOUT) -> bytes:
    """_get dengan satu retry bila kena 429 (jeda 45 dtk - hormati rate limit)."""
    try:
        return _get(url, timeout)
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        print(f"  [rate limit 429] jeda 45 detik lalu coba ulang: {url}")
        time.sleep(45)
        return _get(url, timeout)


def _validate_csv(text: str) -> list[dict]:
    """Parse & validasi CSV ClubElo; raise ValueError bila format tidak sesuai."""
    rows = list(csv.DictReader(io.StringIO(text)))
    if len(rows) < MIN_ROWS:
        raise ValueError(f"baris terlalu sedikit ({len(rows)} < {MIN_ROWS})")
    missing = [c for c in REQUIRED_COLS if c not in rows[0]]
    if missing:
        raise ValueError(f"kolom hilang: {missing}")
    return rows


def fetch_live(date_str: str) -> tuple[str, str]:
    """Fetch langsung dari API ClubElo. -> (csv_text, url)."""
    url = f"http://api.clubelo.com/{date_str}"
    text = _get(url).decode("utf-8", errors="replace")
    _validate_csv(text)
    return text, url


def fetch_wayback(date_str: str) -> tuple[str, str]:
    """Fallback: snapshot Wayback Machine untuk tanggal yang sama / terdekat sebelumnya."""
    avail = json.loads(
        _get_rate_limited(
            f"https://archive.org/wayback/available?url=api.clubelo.com/{date_str}"
        ).decode()
    )
    snap = (avail.get("archived_snapshots") or {}).get("closest")
    if not snap or not snap.get("url"):
        # Cari snapshot terbaru apa pun (prefix /20*) via CDX, lalu pakai yang paling akhir.
        # fl=timestamp,original -> rows = [timestamp, original] (baris ke-0 = header utk output=json)
        cdx = _get_rate_limited(
            "http://web.archive.org/cdx/search/cdx"
            "?url=api.clubelo.com/20*&output=json"
            "&fl=timestamp,original&filter=statuscode:200&limit=-1"
        ).decode()
        rows = json.loads(cdx) if cdx.strip() else []
        if len(rows) < 2:
            raise RuntimeError("tidak ada snapshot Wayback utk ClubElo API")
        snap = {"timestamp": rows[-1][0], "url": rows[-1][1]}
    ts = snap.get("timestamp", "")
    raw_url = f"https://web.archive.org/web/{ts}id_/{snap['url']}"
    text = _get_rate_limited(raw_url).decode("utf-8", errors="replace")
    _validate_csv(text)
    return text, raw_url


def _read_meta() -> dict:
    try:
        return json.loads(CLUB_ELO_META.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _write(text: str, source: str, url: str) -> None:
    CLUB_ELO.write_text(text, encoding="utf-8", newline="\n")
    CLUB_ELO_META.write_text(
        json.dumps(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source": source,
                "url": url,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def refresh(force: bool = False) -> bool:
    """Refresh club_elo.csv. True = ada data valid (baru/lama), False = tidak ada data sama sekali."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    meta = _read_meta()
    fetched_at = meta.get("fetched_at")
    if not force and CLUB_ELO.exists() and fetched_at:
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)
            if age < timedelta(hours=CACHE_HOURS):
                print(f"Cache masih segar ({age.total_seconds()/3600:.1f} jam) - skip fetch.")
                return True
        except ValueError:
            pass

    try:
        text, url = fetch_live(date_str)
        _write(text, "live", url)
        print(f"OK live: club_elo.csv <- {url}")
        return True
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
        print(f"[PERINGATAN] API ClubElo gagal ({e}) - coba Wayback Machine...")

    try:
        text, url = fetch_wayback(date_str)
        _write(text, "wayback", url)
        print(f"OK wayback: club_elo.csv <- {url}")
        return True
    except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError, OSError) as e:
        print(f"[PERINGATAN] Wayback juga gagal ({e}).")

    if CLUB_ELO.exists():
        print(f"[PERINGATAN] Pakai file LAMA apa adanya: {CLUB_ELO} (meta: {meta or 'tanpa meta'}).")
        return True

    print(f"[ERROR] Tidak ada data Elo sama sekali ({CLUB_ELO} belum pernah terisi).")
    return False


def report_unmapped() -> None:
    """Cetak klub di club_elo.csv yang belum punya pasangan di elo_name_map.json."""
    if not CLUB_ELO.exists():
        print("club_elo.csv belum ada - jalankan fetch dulu.")
        return
    name_map = {}
    if ELO_NAME_MAP.exists():
        try:
            data = json.loads(ELO_NAME_MAP.read_text(encoding="utf-8"))
            name_map = {k: v for k, v in data.items() if not k.startswith("_")}
        except json.JSONDecodeError as e:
            print(f"[PERINGATAN] elo_name_map.json rusak ({e}) - anggap kosong.")

    from team_aliases import canonical_team

    rows = list(csv.DictReader(io.StringIO(CLUB_ELO.read_text(encoding="utf-8"))))
    unmapped = []
    elo_keys = set()
    for r in rows:
        club = (r.get("Club") or "").strip()
        if not club:
            continue
        resolved = name_map.get(club)
        elo_keys.add(canonical_team(resolved or club))
        canon = canonical_team(resolved or club)
        # terpetakan = ada di elo_name_map ATAU nama kanonik sudah dikenali alias/profil
        if resolved is None and canon == club and club not in _known_canonicals():
            unmapped.append(club)
    print(f"Total klub Elo: {len(rows)}; belum terpetakan: {len(unmapped)}")
    for c in unmapped:
        print(f"  - {c}")

    # Bagian 2: klub target (UCL_TEAMS + club_profiles) yang TIDAK punya Elo
    targets: set = set()
    try:
        from ucl_simulator import UCL_TEAMS

        targets |= {canonical_team(t) for t in UCL_TEAMS}
    except Exception as e:  # pragma: no cover - diagnostik saja
        print(f"[PERINGATAN] UCL_TEAMS gagal dimuat ({e}) - cek profil saja.")
    try:
        profiles = json.loads(
            (Path(__file__).resolve().parents[1] / "data" / "club_profiles.json").read_text(
                encoding="utf-8"
            )
        )
        targets |= {canonical_team(k) for k in profiles}
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        print(f"[PERINGATAN] club_profiles.json gagal dimuat ({e}).")

    missing = sorted(t for t in targets if t not in elo_keys)
    print(f"\nTarget tanpa Elo ({len(missing)}/{len(targets)}):")
    for t in missing:
        print(f"  - {t}")


_KNOWN_CACHE: set | None = None


def _known_canonicals() -> set:
    global _KNOWN_CACHE
    if _KNOWN_CACHE is None:
        from team_aliases import TEAM_ALIASES

        known = set(TEAM_ALIASES.values()) | set(TEAM_ALIASES.keys())
        try:
            profiles = json.loads(
                (Path(__file__).resolve().parents[1] / "data" / "club_profiles.json").read_text(encoding="utf-8")
            )
            known |= set(profiles.keys())
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        _KNOWN_CACHE = known
    return _KNOWN_CACHE


if __name__ == "__main__":
    t0 = time.time()
    argv = [a.lower() for a in sys.argv[1:]]
    if "--unmapped" in argv:
        report_unmapped()
    else:
        ok = refresh(force="--force" in argv)
        print(f"Selesai dalam {time.time() - t0:.0f} detik")
        sys.exit(0 if ok else 1)
