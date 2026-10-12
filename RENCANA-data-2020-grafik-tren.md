# Rencana: Data Liga 2020–2026 + Grafik Tren & Statistik Lengkap

Keputusan user: (1) archive = hasil laga saja (shots opsional via flag nanti), (2) popup tetap musim ini saja, (3) semua ide improve dipasang + **semua grafik memakai GARIS, bukan batang**.

## Fase 1 — Data multi-musim (backend)

### 1.1 `scripts/fetch_data.py`
- `SEASONS = [2020..2026]`; 2026 tetap dengan shots seperti sekarang.
- 2020–2025: `getLeagueData/{league}/{season}` → hanya `isResult` → baris matches (TANPA shots).
- Gabung semua musim, sort datetime, tulis satu `historical_matches.csv` (~8.900 baris).
- Flag CLI `--archive-shots` (default off; fetch shots archive terpisah ~60 menit, di luar eksekusi awal).
- Runtime archive: 24 request ≈ <30 detik.

### 1.2 Guard "musim berjalan" — WAJIB sebelum merge dipakai
Helper `get_current_season()` di `data_paths.py` (max season di historical, cached per mtime). Filter ke musim berjalan di:
1. `season_projection.project_league` → `_compute_actual_table` (klasemen salah total jika semua musim dijumlah)
2. `livescore.get_live_standings` → sebelum `_compute_actual_table`
3. `club_analytics.get_club_analytics` → hitung `league_position`
4. `app.get_schedule` → bagian arsip historical (popup & performa tetap)
5. `app.list_teams` → daftar tim dropdown
6. `scripts/league_standings.py` (CLI)

### 1.3 Koreksi korektif: `model_retrainer.sync_actuals_from_history`
Bug laten jadi kritis setelah merge: sync memasangkan pasangan tim sama persis, ambil hasil terakhir → prediksi laga MENDATANG bisa keisi actual dari musim lalu (metrik korup).
Fix: hanya pakai historis `datetime > timestamp` prediksi, ambil yang paling awal. Baris backfill (timestamp=now) juga terlindungi.

### 1.4 Verifikasi nama tim antar musim; tambah alias di `team_aliases.py` bila beda.

## Fase 2 — Analitik Klub: tren naik/turun 2020→2026 (garis)

### 2.1 Backend `club_analytics.py`
- `_season_tables()` (cache per mtime): klasemen akhir per musim × liga dari historical (pos, P, W/D/L, GF/GA, PPG, avg xG for/against).
- `get_club_analytics` embed:
  - `season_history`: `[{season:"2020/21", position, points, ppg, w,d,l, gf,ga, xg_for_avg, xg_against_avg, relegated, in_progress}, ...]`
  - `trend`: `{delta_position, delta_points, direction:"naik"|"turun"|"stabil"}`
- `relegated` = posisi akhir zona bawah (bottom 3 / 2 sesuai jumlah tim); musim berjalan `in_progress=true`, tidak dihitung relegated.

### 2.2 Frontend `AnalyticsView.vue` + `SeasonTrendChart.vue` (baru)
- **Grafik garis** dual-sumbu: poin per musim + posisi (sumbu kanan, terbalik); titik musim berjalan hollow + label "berlangsung"; vue-chartjs Line (sudah ada dependency).
- Kartu tren: "Naik +7 poin vs musim lalu" / "Turun 3 posisi" (ArrowUpRight/ArrowDownRight, emerald/rose).
- Tabel statistik per musim + chip "DEGRADASI" merah untuk musim terdegradasi.
- **Dropdown pemilih musim** (2020/21…2026/27): highlight titik + filter baris tabel (frontend-only, tanpa API baru).

## Fase 3 — Proyeksi Liga: statistik penuh + garis semua klub + label degradasi

### 3.1 Backend
- `season_projection.py` — per baris standings tambah: `ppg`, `avg_xg_for`, `avg_xg_ga`, `status` ("JUARA"|"UCL"|"UEL"|"DEGRADASI"|"MID"), `promoted` (tidak ada musim lalu), `relegated_last_season` (posisi akhir musim lalu di zona turun → chip konteks).
- Endpoint `/api/standings/{league}` embed `position_history: {klub: [pos2020..pos2026|null]}` (cache mtime) untuk sparkline.

### 3.2 Frontend
- `StandingsTable.vue`: kolom penuh M/S/K, GM/GK, SG, Poin, Proyeksi±, %, **sparkline posisi (SVG mini-line 2020→now)**, chip status: **"DEGRADASI"** (rose, projected zona bawah), "PROMOSI" (sky), "DEGRADASI 25/26" (slate).
- `ProjectedPointsChart.vue` (baru): **grafik garis** semua klub — garis "Poin Aktual" vs "Proyeksi Poin", band rose zona degradasi, tooltip nama+logo.
- `StandingsView.vue`: pasang chart + ekspor CSV kolom baru.

## Fase 4 — Verifikasi
1. Jalankan fetch archive → cek CSV ~8.900 baris, rentang 2020→2026.
2. Restart uvicorn → curl: `/api/standings/EPL` (aktual hanya 2026 + position_history), `/api/analytics/Arsenal` (season_history 7 musim), `/api/schedule?tab=finished` (±234 item, tidak meledak), `/api/teams`.
3. `/api/model/stats` — sync guard: pending tanpa actual tidak keisi actual lama.
4. `npm run build`; respons analitik <1s (cache season tables).

## Risiko & mitigasi
- Klasemen/proyeksi salah karena semua musim dijumlah → guard 1.2.
- Metrik evaluasi korup → timestamp guard 1.3.
- Popup banjir laga lama → filter arsip musim berjalan (permintaan user).
- `lru_cache` project_league basi setelah fetch → restart server.
- Nama tim beda antar musim → verifikasi + alias.

## File yang disentuh
Backend: `scripts/fetch_data.py`, `data_paths.py`, `season_projection.py`, `livescore.py`, `club_analytics.py`, `model_retrainer.py`, `app.py`, (`team_aliases.py` bila perlu).
Frontend: `AnalyticsView.vue`, `SeasonTrendChart.vue` (baru), `StandingsView.vue`, `StandingsTable.vue`, `ProjectedPointsChart.vue` (baru), `services/api.js` (bila perlu).
