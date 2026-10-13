export const LEAGUE_LABELS = {
  EPL: 'Premier League',
  La_liga: 'La Liga',
  Serie_A: 'Serie A',
  Bundesliga: 'Bundesliga',
}

// Aksen warna per liga — kartu jadwal & pil laga tidak lagi abu-abu polos
export const LEAGUE_ACCENTS = {
  EPL: {
    text: 'text-sky-400',
    border: 'border-sky-500/40',
    bg: 'bg-sky-500/10',
    bar: 'bg-sky-500',
    chip: 'border-sky-500/40 bg-sky-500/10 text-sky-400',
  },
  La_liga: {
    text: 'text-amber-400',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/10',
    bar: 'bg-amber-500',
    chip: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
  },
  Serie_A: {
    text: 'text-emerald-400',
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-500/10',
    bar: 'bg-emerald-500',
    chip: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
  },
  Bundesliga: {
    text: 'text-violet-400',
    border: 'border-violet-500/40',
    bg: 'bg-violet-500/10',
    bar: 'bg-violet-500',
    chip: 'border-violet-500/40 bg-violet-500/10 text-violet-400',
  },
}

export function leagueAccent(league) {
  return LEAGUE_ACCENTS[league] || LEAGUE_ACCENTS.EPL
}

// Kickoff UTC -> "Sen, 12 Okt 2026 • 20:00 WIB"
export function formatWib(dateStr) {
  if (!dateStr) return ''
  const d = new Date(String(dateStr).replace(' ', 'T') + 'Z')
  if (isNaN(d.getTime())) return ''
  const wib = new Date(d.getTime() + 7 * 3600 * 1000)
  const days = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
  const pad = (n) => String(n).padStart(2, '0')
  return `${days[wib.getUTCDay()]}, ${wib.getUTCDate()} ${months[wib.getUTCMonth()]} ${wib.getUTCFullYear()} • ${pad(wib.getUTCHours())}:${pad(wib.getUTCMinutes())} WIB`
}

// Jam saja: "20:00 WIB"
export function formatWibTime(dateStr) {
  const full = formatWib(dateStr)
  const m = full.match(/(\d{2}:\d{2}) WIB$/)
  return m ? `${m[1]} WIB` : full
}

// Tanggal saja: "Sen, 12 Okt"
export function formatWibDay(dateStr) {
  const full = formatWib(dateStr)
  return full.split(' • ')[0] || full
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
    // EPL
    'Manchester City': 'MCI',
    'Manchester United': 'MUN',
    'Aston Villa': 'AVL',
    'West Ham': 'WHU',
    'Brighton': 'BHA',
    'Newcastle': 'NEW',
    'Newcastle United': 'NEW',
    'Nottingham Forest': 'NFO',
    'Crystal Palace': 'CRY',
    'Sheffield United': 'SHU',
    'Southampton': 'SOU',
    'Burnley': 'BUR',
    'Wolverhampton': 'WOL',
    'Tottenham': 'TOT',
    'Leeds': 'LEE',
    'Leicester': 'LEI',
    // La Liga
    'Real Madrid': 'RMA',
    'Atletico Madrid': 'ATM',
    'Athletic Club': 'ATH',
    'Real Betis': 'BET',
    'Real Sociedad': 'RSO',
    'Celta Vigo': 'CEL',
    'Rayo Vallecano': 'RAY',
    'Deportivo La Coruna': 'DEP',
    'Racing Santander': 'RAC',
    // Serie A
    'AC Milan': 'MIL',
    'Inter': 'INT',
    'Inter Milan': 'INT',
    'Roma': 'ROM',
    'AS Roma': 'ROM',
    'Napoli': 'NAP',
    'Juventus': 'JUV',
    'Atalanta': 'ATA',
    'Como': 'COM',
    'Como 1907': 'COM',
    'Fiorentina': 'FIO',
    'Lazio': 'LAZ',
    'Torino': 'TOR',
    'Udinese': 'UDI',
    'Venezia': 'VEN',
    'Cagliari': 'CAG',
    'Parma Calcio 1913': 'PAR',
    // Bundesliga
    'Borussia Dortmund': 'BVB',
    'Bayern Munich': 'BAY',
    'Bayer Leverkusen': 'B04',
    'RB Leipzig': 'RBL',
    'Stuttgart': 'VFB',
    'VfB Stuttgart': 'VFB',
    "Borussia M'gladbach": 'BMG',
    'Eintracht Frankfurt': 'SGE',
    'Union Berlin': 'FCU',
    'Werder Bremen': 'SVW',
    'Mainz 05': 'M05',
    'FC Koln': 'KOE',
    'Schalke 04': 'S04',
    'Hamburger SV': 'HSV',
    // Ligue 1
    'PSG': 'PSG',
    'Paris Saint-Germain': 'PSG',
    'Lens': 'RCL',
    'RC Lens': 'RCL',
    'Lille': 'LIL',
    'LOSC Lille': 'LIL',
    'Lyon': 'OL',
    'Marseille': 'OM',
    'Monaco': 'ASM',
    'Nice': 'OGC',
    'Rennes': 'SRFC',
    'Brest': 'BRE',
    'Le Havre': 'HAC',
    // Eredivisie
    'PSV': 'PSV',
    'PSV Eindhoven': 'PSV',
    'Feyenoord': 'FEY',
    'Ajax': 'AJA',
    'AZ Alkmaar': 'AZ',
    'FC Twente': 'TWE',
    'Utrecht': 'UTR',
    // Primeira Liga
    'Porto': 'POR',
    'FC Porto': 'POR',
    'Benfica': 'BEN',
    'Sporting CP': 'SCP',
    'Braga': 'SCB',
    // Super Lig
    'Galatasaray': 'GAL',
    'Fenerbahce': 'FEN',
    'Fenerbahçe': 'FEN',
    'Besiktas': 'BJK',
    'Trabzonspor': 'TS',
    // Other
    'Shakhtar Donetsk': 'SHK',
    'Slavia Praha': 'SLA',
    'Slavia Prague': 'SLA',
    'Sparta Praha': 'SPP',
    'Sparta Prague': 'SPP',
    'Club Brugge': 'CLU',
    'Anderlecht': 'AND',
    'AEK Athens': 'AEK',
    'Olympiacos': 'OLY',
    'Panathinaikos': 'PAN',
    'PAOK': 'PAOK',
    'LASK': 'ASK',
    'RB Salzburg': 'RBS',
    'Red Bull Salzburg': 'RBS',
    'Sturm Graz': 'STU',
    'Rapid Wien': 'RAP',
    'Austria Wien': 'AUW',
    'Slovan Bratislava': 'SLO',
    'Sabah FK': 'SAB',
    'Qarabag': 'QAR',
    'Qarabag FK': 'QAR',
    'Bodo Glimt': 'BOD',
    'Bodø/Glimt': 'BOD',
    'Viking': 'VIK',
    'Viking FK': 'VIK',
    'Molde': 'MOL',
    'Rosenborg': 'ROS',
    'Young Boys': 'YB',
    'Basel': 'BAS',
    'Celtic': 'CEL',
    'Rangers': 'RAN',
    'Red Star Belgrade': 'CZV',
    'Dinamo Zagreb': 'DZG',
    'Ferencvaros': 'FER',
    'Sturm': 'STU',
  }

  if (map[team]) return map[team]

  // Fallback: hilangkan prefix umum, ambil 3 huruf pertama
  const skip = /^(FC|AS|AC|RC|RB|SC|VfB|SV|FK|SK|CF|UD|CD|LOSC|OGC|TSG)\s+/i
  const cleaned = team.replace(skip, '')
  return cleaned.slice(0, 3).toUpperCase()
}

export function playerImageSrc(image) {
  if (!image) return null
  if (image.startsWith('http')) return image
  // key_players.json: /assets/players/xxx.png
  const file = image.split('/').pop()
  return `${import.meta.env.BASE_URL}assets/players/${file}`
}

// Warna garis trajektori berdasarkan posisi proyeksi — konsisten
// antara grafik besar (TrajectoryChart) dan small multiples (TeamTrajectoryGrid).
const ZONE_TRAJECTORY_COLORS = {
  UCL: '#38BDF8', // sky
  UEL: '#A78BFA', // violet
  REL: '#FB7185', // rose
  MID: '#94A3B8', // slate
}

export function trajectoryColor(row = {}) {
  if (row.projected_position === 1) return '#F59E0B' // amber — juara
  return ZONE_TRAJECTORY_COLORS[row.zone] || ZONE_TRAJECTORY_COLORS.MID
}
