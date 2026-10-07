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
python -m uvicorn app:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Endpoint utama

| Endpoint | Fungsi |
|----------|--------|
| `GET /api/leagues` | Daftar liga |
| `GET /api/fixtures/{league}` | Jadwal mendatang |
| `GET /api/predict?home_team=&away_team=` | Prediksi skor 10k Monte Carlo |
| `GET /api/shots?home_team=&away_team=` | Peta tembakan xG |
| `GET /api/standings/{league}` | Proyeksi klasemen + probabilitas |
| `GET /api/ucl/simulate` | Simulasi UCL (pots + bracket) |
| `GET /api/analytics/{team}` | Analitik klub taktis |

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

Buka http://127.0.0.1:5173

Vite proxy `/api` → backend `http://127.0.0.1:8000`.

## Design System

- Canvas `#090D16`, panel slate gelap, border tipis
- Font: **Plus Jakarta Sans** (UI) + **JetBrains Mono** (angka/telemetri)
- Aksen fungsional: sky (home/metric), rose (away), amber (caution), emerald (success)

## Foto Pemain

Letakkan PNG cutout di `frontend/public/assets/players/` dengan nama file yang sama seperti di `backend/key_players.json` (mis. `haaland.png`, `saka.png`). Bila file belum ada, UI otomatis fallback ke avatar inisial.
