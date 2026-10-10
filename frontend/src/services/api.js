import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 120000,
  headers: {
    Accept: 'application/json',
  },
})

export function extractError(err) {
  const msg = err?.response?.data?.detail || err?.message || 'Terjadi kesalahan'
  return String(msg)
}

export const fetchLeagues = () => api.get('/leagues').then((r) => r.data)
export const fetchFixtures = (league, limit = 40) =>
  api.get(`/fixtures/${league}`, { params: { limit } }).then((r) => r.data)
export const fetchTicker = (limit = 16) =>
  api.get('/ticker', { params: { limit } }).then((r) => r.data)
export const fetchTeams = (league) => api.get('/teams', { params: { league } }).then((r) => r.data)
export const fetchPredict = (home, away) =>
  api.get('/predict', { params: { home_team: home, away_team: away } }).then((r) => r.data)
export const fetchShots = (home, away) =>
  api.get('/shots', { params: { home_team: home, away_team: away } }).then((r) => r.data)
export const fetchStandings = (league, nSeasons = 350) =>
  api.get(`/standings/${league}`, { params: { n_seasons: nSeasons } }).then((r) => r.data)
export const fetchUcl = () => api.get('/ucl/simulate').then((r) => r.data)
export const postUclWhatIf = (overrides) =>
  api.post('/ucl/whatif', { overrides }).then((r) => r.data)
export const fetchModelStats = () => api.get('/model/stats').then((r) => r.data)
export const fetchAnalytics = (team) => api.get(`/analytics/${encodeURIComponent(team)}`).then((r) => r.data)
export const fetchLiveMatches = () => api.get('/live/matches').then((r) => r.data)
export const fetchLiveStandings = (league) => api.get(`/live/standings/${league}`).then((r) => r.data)
export const fetchLiveUcl = () => api.get('/live/ucl').then((r) => r.data)
export const fetchMatchDetail = (matchId, refresh = false, teams = null) =>
  api
    .get(`/live/match/${matchId}/detail`, {
      params: {
        ...(refresh ? { refresh: true } : {}),
        ...(teams?.home ? { home: teams.home } : {}),
        ...(teams?.away ? { away: teams.away } : {}),
        ...(teams?.league ? { league: teams.league } : {}),
      },
    })
    .then((r) => r.data)
export const fetchMatchDetailByTeams = (home, away, league, refresh = false) =>
  api
    .get('/live/match/detail', {
      params: { home, away, ...(league ? { league } : {}), ...(refresh ? { refresh: true } : {}) },
    })
    .then((r) => r.data)
