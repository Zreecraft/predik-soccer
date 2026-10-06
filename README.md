# Analytica FC

Platform **Sports Analytics & Match Prediction** berbasis Monte Carlo, Poisson, dan model xG.

## Struktur

```text
predik-soccer/
├── backend/     # FastAPI + engine prediksi (Python)
└── frontend/    # Vue 3 + Vite + Tailwind CSS
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
