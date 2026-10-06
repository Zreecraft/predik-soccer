export const LEAGUE_LABELS = {
  EPL: 'Premier League',
  La_liga: 'La Liga',
  Serie_A: 'Serie A',
  Bundesliga: 'Bundesliga',
}

export function formBadgeClass(result) {
  if (result === 'W') return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40'
  if (result === 'D') return 'bg-slate-500/15 text-slate-300 border-slate-500/40'
  return 'bg-rose-500/15 text-rose-400 border-rose-500/40'
}

export function teamInitial(name = '') {
  const parts = String(name).trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function abbrTeam(team = '') {
  const map = {
    'Manchester City': 'MCI',
    'Manchester United': 'MUN',
    'Aston Villa': 'AVL',
    'West Ham': 'WHU',
    'Brighton': 'BHA',
    'Newcastle': 'NEW',
    'Real Madrid': 'RMA',
    'Atletico Madrid': 'ATM',
    'Borussia Dortmund': 'BVB',
    'Bayern Munich': 'BAY',
    'Bayer Leverkusen': 'B04',
    'RB Leipzig': 'RBL',
    'AC Milan': 'MIL',
    Inter: 'INT',
    Roma: 'ROM',
    Napoli: 'NAP',
    Juventus: 'JUV',
    Atalanta: 'ATA',
    PSG: 'PSG',
    Benfica: 'BEN',
    'Sporting CP': 'SCP',
  }
  return map[team] || team.slice(0, 3).toUpperCase()
}

export function playerImageSrc(image) {
  if (!image) return null
  if (image.startsWith('http')) return image
  // key_players.json: /assets/players/xxx.png
  const file = image.split('/').pop()
  return `${import.meta.env.BASE_URL}assets/players/${file}`
}
