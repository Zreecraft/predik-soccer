"""Kompres cutout pemain: resize ke sisi terpanjang 320px + simpan sebagai WebP.

Konteks: cutout di `frontend/public/assets/players/` berukuran 500-800px (rata-rata
229 KB, total ~18 MB) padahal tampil di UI maksimal 160px (PlayerCutout h-40) —
resolusi 2x (320px) sudah cukup tajam termasuk layar Retina.

- PNG asli TIDAK dihapus (hanya dibuat file baru `*.webp` di folder yang sama).
- Idempoten: file yang sudah ada & lebih baru dari PNG-nya dilewati.
- Alpha/transparansi dipertahankan (WebP lossy quality=82 menyimpan alpha).

Pemakaian (dari folder backend/):
    python scripts/optimize_player_images.py
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from PIL import Image
except ImportError:
    print("Pillow belum terpasang: pip install Pillow")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1].parent
PLAYERS_DIR = ROOT / "frontend" / "public" / "assets" / "players"

MAX_SIDE = 320          # 2x ukuran tampilan maksimal (h-40 = 160px)
QUALITY = 82            # kualitas WebP — di bawah ini tepi cutout mulai terlihat
METHOD = 4              # keseimbangan ukuran/kecepatan (6 = paling lambat, beda tipis)


def main() -> int:
    if not PLAYERS_DIR.is_dir():
        print(f"Folder tidak ditemukan: {PLAYERS_DIR}")
        return 1

    pngs = sorted(PLAYERS_DIR.glob("*.png"))
    if not pngs:
        print(f"Tidak ada PNG di {PLAYERS_DIR}")
        return 1

    total_before = total_after = 0
    converted = skipped = 0

    for png in pngs:
        out = png.with_suffix(".webp")
        src_bytes = png.stat().st_size

        if out.exists() and out.stat().st_mtime >= png.stat().st_mtime:
            total_before += src_bytes
            total_after += out.stat().st_size
            skipped += 1
            continue

        with Image.open(png) as im:
            im = im.convert("RGBA")  # pastikan alpha utk WebP
            w, h = im.size
            if max(w, h) > MAX_SIDE:
                scale = MAX_SIDE / max(w, h)
                im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                               Image.LANCZOS)
            im.save(out, "WEBP", quality=QUALITY, method=METHOD)

        total_before += src_bytes
        total_after += out.stat().st_size
        converted += 1
        print(f"  [{converted}] {png.name} -> {out.stat().st_size // 1024} KB",
              flush=True)

    pct = (total_after / total_before * 100) if total_before else 0
    print(f"Selesai: {converted} dibuat, {skipped} dilewati (sudah ada), "
          f"{len(pngs)} PNG total")
    print(f"  sebelum : {total_before / 1024 / 1024:.1f} MB (PNG)")
    print(f"  sesudah : {total_after / 1024 / 1024:.2f} MB (WebP) = {pct:.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
