# Tugas: Redesign UI Analytica FC (website prediksi bola ML)

Kerjakan BERTAHAP. Selesaikan satu fase, jalankan app, pastikan tidak error, baru lanjut. Jangan ubah logika model, API, atau data. Ubah hanya tampilan (CSS/komponen). Sebelum mulai, baca struktur folder dan sebutkan file mana yang mengatur styling global.

## Masalah yang harus diperbaiki
1. Semua teks kecil (10-11px) dan label HURUF KAPITAL ber-letter-spacing lebar. Sulit dibaca.
2. Semua blok berbentuk kartu dengan border cyan/neon yang sama. Tidak ada hierarki, mata tidak tahu harus lihat apa dulu.
3. Hasil prediksi (angka utama) tersembunyi di tengah, kecil, dikelilingi badge dan chip.
4. Terlalu banyak label eyebrow ("// MATCH PREDICTION ENGINE", "DATA ASLI", "POP-UP", dll). Hapus yang tidak memberi informasi.
5. Satu halaman berisi terlalu banyak hal. Pindahkan detail ke tab/accordion.
6. Warna: navy gelap + neon cyan/merah/hijau di mana-mana. Terlihat seperti template AI.
7. Tabel Proyeksi Liga terlalu padat (15+ kolom). Peta tembakan titiknya menumpuk.

## Design tokens (pakai persis ini, simpan sebagai CSS variables)
Light (default):
- --bg: #eef2ef; --card: #fbfcfb; --ink: #12231b; --mute: #5d6f65; --line: #d3ddd6
- --home: #1b5fd0; --away: #d4452b; --draw: #9aa8a0; --ok: #1f7a4d; --bad: #b3341f
Dark (prefers-color-scheme + toggle data-theme="dark"):
- --bg: #0f1a15; --card: #16241d; --ink: #e9f1ec; --mute: #93a79b; --line: #27392f
- --home: #6aa0ff; --away: #ff7d63; --draw: #5d6f65; --ok: #52c58a; --bad: #ff8a73

Font (Google Fonts): `Bricolage Grotesque` (700/800) untuk judul dan angka besar, `Figtree` (400/500/600) untuk teks. Body minimal 15px, label minimal 13px. Gunakan `font-variant-numeric: tabular-nums` untuk angka.

Aturan visual:
- Warna home = --home, away = --away, di SEMUA halaman. Jangan pakai warna lain untuk tim.
- Hijau/merah (--ok/--bad) hanya untuk benar/salah prediksi.
- Border radius: 16px untuk blok utama, 6-10px untuk elemen kecil, jangan semua sama.
- Tanpa glow, tanpa gradient dekoratif, tanpa animasi masuk di tiap section. Animasi hanya untuk respons klik (buka/tutup).
- Label: sentence case, bukan KAPITAL. Hapus tanda "//" dan em dash dekoratif.
- Satu blok hero per halaman, sisanya polos (garis pemisah tipis, bukan kartu bertumpuk).

## Fase 1: Halaman Prediksi Laga (paling penting)
Referensi visual: file `contoh-ui-prediksi.html` (buka di browser, tiru struktur dan nuansanya).
Urutan konten dari atas:
1. Hero: info laga (liga, stadion, tanggal) satu baris kecil. Nama tim kiri/kanan. Skor BESAR di tengah (clamp 52px-96px).
2. Satu baris verdict: badge "Tepat skor" / "Tepat hasil" / "Meleset" + satu kalimat penjelasan.
3. Bar probabilitas 3 segmen (menang tim A / seri / menang tim B) dengan persentase di bawahnya. Hapus bar form yang terpisah.
4. Section "Kenapa model memprediksi ini?": hanya 3 statistik paling berpengaruh dengan bar berpasangan (kiri home, kanan away). Statistik lain pindah ke accordion "Statistik lengkap".
5. Peta tembakan: titik lebih sedikit dan transparan, gol diberi warna khusus (kuning) dengan outline. Legenda satu baris.
6. Link ke Match Centre sebagai teks biasa, bukan banner hijau.
Hapus: badge "9.15 keyakinan model" di pojok (pindahkan jadi teks kecil di bawah bar probabilitas), kartu "Rangkuman diferensial taktis" (gabungkan jadi satu kalimat di bawah statistik), chip "POP-UP".
Match picker (modal cari laga): tampilkan tiap laga sebagai satu baris: tanggal | tim A skor tim B | ikon hasil. Badge "Prediksi/Aktual" jadi teks abu kecil.

## Fase 2: Navigasi dan layout global
- Header: logo + 5 menu saja, aktif ditandai garis bawah 2px, bukan kotak biru.
- Ticker "PEKAN" di bawah header: hapus atau ubah jadi satu baris yang bisa di-scroll horizontal, font 13px.
- Lebar konten maksimal 960px, dipusatkan. Spasi antar section 32px.
- Responsif: semua grid 2 kolom jadi 1 kolom di bawah 640px. Tidak boleh ada scroll horizontal di body.

## Fase 3: Proyeksi Liga
- Tabel: default tampilkan hanya Pos, Klub, Main, Poin, Proyeksi, Juara%, Top 4%, Degradasi%. Kolom lain di tombol "Kolom lainnya".
- Grafik 20 garis klub: sorot klub yang dipilih/dicari, sisanya abu tipis.
- Grid "Jalur setiap klub" 20 kartu: ganti jadi daftar kompak atau sembunyikan di accordion.

## Fase 4: Bagan UCL dan Analitik Klub
- Bagan UCL: beri judul tahap yang jelas, ukuran tim minimal 13px, jangan paksa semua muat dalam satu layar, boleh scroll horizontal di dalam kontainer sendiri.
- Analitik Klub: letakkan Rating dan Power di hero, sisanya di tab (Musim, Form, Jadwal).

## Aturan kualitas (cek di setiap fase)
- Kontras teks minimal 4.5:1 di light dan dark.
- Fokus keyboard terlihat (outline 2px --home).
- Hormati prefers-reduced-motion.
- Jalankan build/lint, perbaiki error sebelum lanjut.
- Setelah tiap fase, tulis ringkasan 3 baris: file yang diubah, apa yang berubah, apa yang belum.

Mulai dari Fase 1 saja. Berhenti setelah selesai dan tunggu konfirmasi sebelum Fase 2.
