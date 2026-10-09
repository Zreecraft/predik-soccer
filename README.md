# Analytica FC

Platform **Sports Analytics & Match Prediction** berbasis Monte Carlo, Poisson, dan model xG.

## Struktur

```text
predik-soccer/
├── backend/                # FastAPI + engine prediksi (Python)
│   ├── app.py              # Entrypoint API
│   ├── assets.py           # Loader logo tim & pemain kunci
│   ├── data_paths.py       # Resolver path ke backend/data/
│   ├── run_prediction.py   # Engine simulasi 10k + skor proyeksi
│   ├── team_analytics.py   # Power index, bias home/away, form
│   ├── team_aliases.py     # Nama & abbr tim
│   ├── club_analytics.py   # Endpoint analitik klub
│   ├── database.py         # SQLite: prediction_logs + model_metrics
│   ├── model_retrainer.py  # Self-learning: Brier/Log-Loss + retrain XGBoost
│   ├── season_projection.py# Proyeksi klasemen (Monte Carlo)
│   ├── ucl_simulator.py    # Simulasi UCL
│   ├── data/               # Data hasil fetch (csv/json/pkl)
│   ├── scripts/            # CLI & tools sekali jalan
│   │   ├── predict_cli.py  # Prediksi laga di terminal
│   │   ├── league_standings.py
│   │   ├── fetch_data.py   # Fetch data Understat
│   │   ├── fetch_fixtures.py
│   │   ├── train_xg_model.py
│   │   └── logos/          # Tooling logo tim
│   └── tests/              # smoke_test.py, verify_fixes.py
└── frontend/               # Vue 3 + Vite + Tailwind CSS
```

## Menjalankan Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8001
```

API docs: http://127.0.0.1:8001/docs

### Endpoint utama

| Endpoint | Fungsi |
|----------|--------|
| `GET /api/leagues` | Daftar liga |
| `GET /api/fixtures/{league}` | Jadwal mendatang |
| `GET /api/predict?home_team=&away_team=` | Prediksi skor 10k Monte Carlo (otomatis di-log ke SQLite) |
| `GET /api/shots?home_team=&away_team=` | Peta tembakan xG |
| `GET /api/standings/{league}` | Proyeksi klasemen + probabilitas |
| `GET /api/ucl/simulate` | Simulasi UCL (pots + bracket + 144 fixture fase liga) |
| `POST /api/ucl/whatif` | **What-If Simulator** — re-simulasi dengan skor manual |
| `GET /api/analytics/{team}` | Analitik klub taktis (form 5 laga + xG) |
| `GET /api/teams` | Daftar tim (opsional `?league=`) |
| `GET /api/model/stats` | Statistik log prediksi & metrik Brier/accuracy |
| `POST /api/model/evaluate` | Sinkron hasil riil → hitung Brier/Log-Loss |
| `POST /api/model/retrain` | Retrain XGBoost (feedback loop) |

### Self-Learning Engine

Setiap `GET /api/predict` dicatat ke `backend/predictions.db` (SQLite).
Loop pembelajaran mandiri:

```bash
cd backend
python model_retrainer.py   # evaluasi Brier/Log-Loss + retrain XGBoost sekaligus
```

Atau via API: `POST /api/model/evaluate` lalu `POST /api/model/retrain`.

### Tools & Tests (dari folder `backend/`)

```bash
python scripts/fetch_data.py        # refresh data historis Understat
python scripts/fetch_fixtures.py    # refresh jadwal mendatang
python scripts/train_xg_model.py    # latih model xG
python scripts/predict_cli.py       # prediksi laga di terminal
python scripts/league_standings.py  # klasemen akhir (CLI interaktif)
python ucl_simulator.py             # simulasi UCL (CLI)

python tests/smoke_test.py          # cek seluruh endpoint API
python tests/verify_fixes.py        # cek abbr, alias, dan coverage logo
```

## Menjalankan Frontend

```bash
cd frontend
npm install
npm run dev
```

Buka http://127.0.0.1:5174

Vite proxy `/api` → backend `http://127.0.0.1:8001`.

### Fitur UI

- **Klasemen interaktif:** setiap baris klub di `/standings` dapat diklik → menuju Analitik Klub.
- **Analitik Klub:** filter dua tingkat (Liga → Klub), section **Hasil 5 Laga Terakhir** (skor riil, xG for/against, badge W/D/L), dan proyeksi 5 laga mendatang (Win/Draw/Loss % + kesulitan).
- **UCL What-If Simulator:** tombol `What-If Simulator` di `/ucl` — ubah skor agregat pada kartu bagan & skor 144 laga fase liga; klasemen, seeding, bracket, dan peluang juara dihitung ulang otomatis (debounce 500ms).

## Design System

- Canvas `#090D16`, panel slate gelap, border tipis
- Font: **Plus Jakarta Sans** (UI) + **JetBrains Mono** (angka/telemetri)
- Aksen fungsional: sky (home/metric), rose (away), amber (caution), emerald (success)

## Foto Pemain (Cutout PNG)

- **Auto-download:** jalankan dari folder `backend/` → `python scripts/fetch_player_photos.py`.
  Script mengunduh cutout PNG dari TheSportsDB ke `frontend/public/assets/players/` (resumable — file valid tidak diunduh ulang).
- **Fallback elegan:** bila file PNG tidak ditemukan/gagal dimuat, `PlayerCutout.vue` otomatis menampilkan siluet avatar inisial nama klub.
- **Kontras dark mode (`#090D16`):** foto diberi *ambient rim light*
  (`drop-shadow(0 0 14px rgba(56,189,248,0.3))`) + *radial glow backdrop* di belakang kontur,
  sehingga pemain berkulit gelap tetap terpisah jelas dari kanvas.
- File pendamping: `backend/data/key_players.json` (pemain bintang per klub).
