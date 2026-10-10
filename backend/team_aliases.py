"""Mapping alias nama tim untuk normalisasi antar sumber data (Understat, TheSportsDB, UI)."""

# Alias -> canonical name (sesuai team_logos.json)
TEAM_ALIASES = {
    "Leeds United": "Leeds",
    "Leeds Utd": "Leeds",
    "Como 1907": "Como",
    "Como Calcio": "Como",
    "AS Roma": "Roma",
    "Roma Calcio": "Roma",
    "Inter Milan": "Inter",
    "Internazionale": "Inter",
    "Paris Saint-Germain": "PSG",
    "Paris SG": "PSG",
    "PSG": "PSG",
    "PSV Eindhoven": "PSV",
    "PSV": "PSV",
    "VfB Stuttgart": "Stuttgart",
    "Stuttgart": "Stuttgart",
    "RC Lens": "Lens",
    "Lens": "Lens",
    "LOSC Lille": "Lille",
    "Lille": "Lille",
    "FC Porto": "Porto",
    "Porto": "Porto",
    "Sporting CP": "Sporting CP",
    "Sporting Lisbon": "Sporting CP",
    "Fenerbahçe": "Fenerbahce",
    "Fenerbahce": "Fenerbahce",
    "Galatasaray": "Galatasaray",
    "Bodo/Glimt": "Bodo Glimt",
    "Bodø/Glimt": "Bodo Glimt",
    "Bodo Glimt": "Bodo Glimt",
    "Viking FK": "Viking",
    "Viking": "Viking",
    "Slavia Prague": "Slavia Praha",
    "Slavia Praha": "Slavia Praha",
    "AEK Athens": "AEK Athens",
    "LASK": "LASK",
    "LASK Linz": "LASK",
    "Sabah FK": "Sabah FK",
    "Sabah": "Sabah FK",
    "Manchester City FC": "Manchester City",
    "Manchester United FC": "Manchester United",
    "Newcastle United": "Newcastle",
    "Newcastle": "Newcastle",
    "West Ham United": "West Ham",
    "West Ham": "West Ham",
    "Tottenham Hotspur": "Tottenham",
    "Tottenham": "Tottenham",
    "Borussia M.Gladbach": "Borussia M'gladbach",
    "Borussia Monchengladbach": "Borussia M'gladbach",
    "FC Cologne": "FC Koln",
    "1. FC Koln": "FC Koln",
    "RasenBallsport Leipzig": "RB Leipzig",
    "Venezia FC": "Venezia",
    "Parma": "Parma Calcio 1913",
    # nama dari ESPN / sumber live
    "AFC Bournemouth": "Bournemouth",
    "Brighton & Hove Albion": "Brighton",
    "Ipswich Town": "Ipswich",
    "Hamburg SV": "Hamburger SV",
    "1. FC Union Berlin": "Union Berlin",
    "SV Elversberg": "Elversberg",
    "SC Paderborn 07": "Paderborn",
    "FC Augsburg": "Augsburg",
    "TSG Hoffenheim": "Hoffenheim",
    "Feyenoord Rotterdam": "Feyenoord",
    "Vitesse Arnhem": "Vitesse",
    "AZ Alkmaar": "AZ Alkmaar",
    "Go Ahead Eagles": "Go Ahead Eagles",
    # singkatan umum (prediksi / ESPN)
    "Man Utd": "Manchester United",
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Spurs": "Tottenham",
    "Wolves": "Wolverhampton",
    "Wolverhampton Wanderers": "Wolverhampton",
    "Nottm Forest": "Nottingham Forest",
    "Sheff Utd": "Sheffield United",
    "Athletic Bilbao": "Athletic Club",
    "Atletico de Madrid": "Atletico Madrid",
}

# Short abbreviation untuk ticker & UI (uppercase 2-4 char)
TEAM_ABBR = {
    "Arsenal": "ARS", "Aston Villa": "AVL", "Bournemouth": "BOU", "Brentford": "BRE",
    "Brighton": "BHA", "Burnley": "BUR", "Chelsea": "CHE", "Coventry": "COV",
    "Crystal Palace": "CRY", "Everton": "EVE", "Fulham": "FUL", "Hull": "HUL",
    "Ipswich": "IPS", "Leeds": "LEE", "Leicester": "LEI", "Liverpool": "LIV",
    "Manchester City": "MCI", "Manchester United": "MUN", "Newcastle": "NEW",
    "Newcastle United": "NEW", "Nottingham Forest": "NFO", "Sheffield United": "SHU",
    "Southampton": "SOU", "Sunderland": "SUN", "Tottenham": "TOT", "West Ham": "WHU",
    "Wolverhampton": "WOL", "Luton": "LUT", "Stoke": "STK", "Norwich": "NOR",
    "Watford": "WAT", "Bristol City": "BRC", "Middlesbrough": "MID", "Preston": "PRE",
    "QPR": "QPR", "Reading": "REA", "Rotherham": "ROT", "Huddersfield": "HUD",
    "Swansea": "SWA", "Cardiff": "CAR", "Millwall": "MIL", "Blackburn": "BLB",
    # La Liga
    "Alaves": "ALA", "Athletic Club": "ATH", "Atletico Madrid": "ATM",
    "Barcelona": "BAR", "Celta Vigo": "CEL", "Elche": "ELC", "Espanyol": "ESP",
    "Getafe": "GET", "Girona": "GIR", "Levante": "LEV", "Malaga": "MAL",
    "Osasuna": "OSA", "Racing Santander": "RAC", "Rayo Vallecano": "RAY",
    "Real Betis": "BET", "Real Madrid": "RMA", "Real Sociedad": "RSO",
    "Sevilla": "SEV", "Valencia": "VAL", "Villarreal": "VIL", "Deportivo La Coruna": "DEP",
    # Serie A
    "AC Milan": "MIL", "Atalanta": "ATA", "Bologna": "BOL", "Cagliari": "CAG",
    "Como": "COM", "Cremonese": "CRE", "Empoli": "EMP", "Fiorentina": "FIO",
    "Frosinone": "FRO", "Genoa": "GEN", "Inter": "INT", "Juventus": "JUV",
    "Lazio": "LAZ", "Lecce": "LEC", "Monza": "MON", "Napoli": "NAP",
    "Parma Calcio 1913": "PAR", "Parma": "PAR", "Pisa": "PIS", "Roma": "ROM",
    "Sassuolo": "SAS", "Torino": "TOR", "Udinese": "UDI", "Venezia": "VEN", "Verona": "VER",
    # Bundesliga
    "Augsburg": "AUG", "Bayer Leverkusen": "B04", "Bayern Munich": "BAY",
    "Borussia Dortmund": "BVB", "Borussia M'gladbach": "BMG", "Borussia M.Gladbach": "BMG",
    "Borussia Monchengladbach": "BMG", "Eintracht Frankfurt": "SGE",
    "Freiburg": "SCF", "Hamburger SV": "HSV", "Hoffenheim": "TSG", "Mainz 05": "M05",
    "FC Koln": "KOE", "FC Cologne": "KOE", "1. FC Koln": "KOE",
    "Paderborn": "SCP", "RB Leipzig": "RBL", "RasenBallsport Leipzig": "RBL",
    "Schalke 04": "S04", "Stuttgart": "VFB", "VfB Stuttgart": "VFB",
    "Union Berlin": "FCU", "Werder Bremen": "SVW", "Elversberg": "ELV",
    # Ligue 1
    "PSG": "PSG", "Paris Saint-Germain": "PSG", "Lens": "RCL", "Lille": "LIL",
    "Lyon": "OL", "Marseille": "OM", "Monaco": "ASM", "Nice": "OGC",
    "Rennes": "SRFC", "Strasbourg": "RCSA", "Toulouse": "TFC", "Nantes": "FCN",
    "Montpellier": "MHSC", "Brest": "BRE", "Le Havre": "HAC", "Auxerre": "AJA",
    "Angers": "SCO", "Reims": "SDR", "Saint-Etienne": "ASSE",
    # Eredivisie
    "PSV": "PSV", "Feyenoord": "FEY", "Ajax": "AJA", "AZ Alkmaar": "AZ",
    "FC Twente": "TWE", "Utrecht": "UTR", "Vitesse": "VIT", "Go Ahead Eagles": "GAE",
    "Heerenveen": "HEE", "Sparta Rotterdam": "SPA", "NAC Breda": "NAC",
    "Fortuna Sittard": "FOR", "Heracles": "HER", "PEC Zwolle": "PEC",
    "Willem II": "WIL", "Almere City": "ALM", "RKC Waalwijk": "RKC", "NEC Nijmegen": "NEC",
    # Primeira Liga
    "Porto": "POR", "FC Porto": "POR", "Benfica": "BEN", "Sporting CP": "SCP",
    "Braga": "SCB", "Vitoria Guimaraes": "VSC", "Famalicao": "FAM", "Moreirense": "MORE",
    "Rio Ave": "RIO", "Vitoria SC": "VSC", "Santa Clara": "CDS", "Estoril": "EST",
    "Farense": "FAR", "Boavista": "BOA", "Gil Vicente": "GIL", "Nacional": "NAC",
    # Super Lig
    "Galatasaray": "GAL", "Fenerbahce": "FEN", "Besiktas": "BJK", "Trabzonspor": "TS",
    "Basaksehir": "IBFK", "Adana Demirspor": "ADS", "Konyaspor": "KON",
    "Antalyaspor": "ANT", "Alanyaspor": "ALA", "Kasimpasa": "KSM", "Rizespor": "RIZ",
    "Sivasspor": "SIV", "Gaziantep FK": "GFK", "Samsunspor": "SAM", "Eyupspor": "EYP",
    "Goztepe": "GOZ", "Bodrum FK": "BDM", "Hatayspor": "HAT",
    # Other leagues
    "Shakhtar Donetsk": "SHK", "Dynamo Kyiv": "DKY", "Slavia Praha": "SLA",
    "Slavia Prague": "SLA", "Sparta Praha": "SPP", "Sparta Prague": "SPP",
    "Victoria Plzen": "PLZ", "Club Brugge": "CLU", "Anderlecht": "AND",
    "Genk": "GNK", "Gent": "GNT", "Union SG": "USG", "Antwerp": "ANT",
    "AEK Athens": "AEK", "Olympiacos": "OLY", "Panathinaikos": "PAN", "PAOK": "PAOK",
    "LASK": "ASK", "Red Bull Salzburg": "RBS", "RB Salzburg": "RBS", "Sturm Graz": "STU",
    "Rapid Wien": "RAP", "Austria Wien": "AUW", "Wolfsberger AC": "WAC",
    "Slovan Bratislava": "SLO", "Spartak Trnava": "SPT", "Sabah FK": "SAB",
    "Qarabag": "QAR", "Qarabag FK": "QAR", "Bodo Glimt": "BOD", "Viking": "VIK",
    "Molde": "MOL", "Rosenborg": "ROS", "Young Boys": "YB", "Basel": "BAS",
    "Celtic": "CEL", "Rangers": "RAN", "Red Star Belgrade": "CZV",
    "Dinamo Zagreb": "DZG", "Ferencvaros": "FER", "Dinamo Bucuresti": "DBU",
}


def canonical_team(name: str) -> str:
    """Normalisasi nama tim ke bentuk kanonik."""
    if not name:
        return name
    name = str(name).strip()
    return TEAM_ALIASES.get(name, name)


# prefix umum yang dipakai sumber data (ESPN dkk.)
_PREFIXES = {
    "fc", "afc", "sc", "sv", "tsg", "vfb", "vfl", "1.", "1", "2.", "3.",
    "rc", "as", "ac", "cd", "ud", "sk", "cf", "us", "sd", "ss", "sp",
}


def team_key(name: str) -> str:
    """Kunci perbandingan nama tim: kanonik + lowercase + buang prefix klub."""
    n = canonical_team(name).lower() if name else ""
    n = n.replace("&", " and ").replace(".", " ").replace("'", "")
    words = [w for w in n.split() if w]
    while words and words[0] in _PREFIXES:
        words.pop(0)
    # buang digit ekor (mis. "union berlin 1892") — kecuali angka bagian nama (mainz 05)
    while words and words[-1].isdigit() and len(words) > 1 and len(words[-1]) > 2:
        words.pop()
    return " ".join(words)


def team_abbr(name: str) -> str:
    """Singkatan 2-4 huruf untuk ticker/UI."""
    if not name:
        return "?"
    name = str(name).strip()
    # coba langsung, lalu alias kanonik
    if name in TEAM_ABBR:
        return TEAM_ABBR[name]
    canonical = canonical_team(name)
    if canonical in TEAM_ABBR:
        return TEAM_ABBR[canonical]
    # fallback: kata pertama (abaikan prefix FC/AS/AC/RC/RB dst)
    skip_words = {"FC", "AS", "AC", "RC", "RB", "SC", "VfB", "SV", "FK", "SK", "CF", "UD", "CD"}
    words = [w for w in name.replace("-", " ").split() if w not in skip_words]
    base = words[0] if words else name
    return base[:3].upper()
