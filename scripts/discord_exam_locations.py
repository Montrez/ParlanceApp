"""State and city picks to narrow exam center search."""
from __future__ import annotations

from discord_exam_data import EXAM_FAMILY

# country value → list of {label, value, note_spanish, note_french}
LOCATIONS: dict[str, list[dict[str, str]]] = {
    "us": [
        {"label": "New York, NY", "value": "nyc", "note_spanish": "Instituto Cervantes New York — check spring/fall session dates early.", "note_french": "Alliance Française NYC and FIAF — DELF/DALF sessions year-round."},
        {"label": "Los Angeles, CA", "value": "la", "note_spanish": "Instituto Cervantes Los Angeles — popular for West Coast DELE.", "note_french": "Alliance Française Los Angeles."},
        {"label": "Chicago, IL", "value": "chi", "note_spanish": "Instituto Cervantes Chicago — Midwest hub.", "note_french": "Alliance Française Chicago."},
        {"label": "Miami, FL", "value": "mia", "note_spanish": "Instituto Cervantes Miami — strong Spanish-speaking community.", "note_french": "Alliance Française Miami."},
        {"label": "Houston, TX", "value": "hou", "note_spanish": "University and Cervantes-affiliated centers in Houston area.", "note_french": "Alliance Française Houston."},
        {"label": "Washington, DC", "value": "dc", "note_spanish": "Instituto Cervantes Washington — convenient for DMV area.", "note_french": "Alliance Française Washington DC."},
        {"label": "Boston, MA", "value": "bos", "note_spanish": "Boston-area universities often host DELE sessions.", "note_french": "Alliance Française Boston."},
        {"label": "San Francisco, CA", "value": "sf", "note_spanish": "Bay Area Cervantes and university partners.", "note_french": "Alliance Française San Francisco."},
        {"label": "Seattle, WA", "value": "sea", "note_spanish": "Pacific Northwest — fewer dates; book early.", "note_french": "Alliance Française Seattle."},
        {"label": "Dallas, TX", "value": "dal", "note_spanish": "North Texas university and language-school partners.", "note_french": "Alliance Française Dallas."},
        {"label": "Atlanta, GA", "value": "atl", "note_spanish": "Southeast hub — check Atlanta and nearby universities.", "note_french": "Alliance Française Atlanta."},
        {"label": "Denver, CO", "value": "den", "note_spanish": "Rocky Mountain region — limited seats per session.", "note_french": "Alliance Française Denver."},
        {"label": "Philadelphia, PA", "value": "phi", "note_spanish": "Mid-Atlantic — university partners in Philly metro.", "note_french": "Alliance Française Philadelphia."},
        {"label": "Phoenix, AZ", "value": "phx", "note_spanish": "Arizona universities — confirm dates on the Cervantes portal.", "note_french": "Check AF network for Arizona offerings."},
        {"label": "Austin, TX", "value": "aus", "note_spanish": "UT-area and Central Texas centers.", "note_french": "Alliance Française Austin when sessions run."},
    ],
    "ca": [
        {"label": "Toronto, ON", "value": "tor", "note_spanish": "Toronto DELE/SIELE — university and Cervantes partners.", "note_french": "Alliance Française Toronto — TCF Canada available."},
        {"label": "Montreal, QC", "value": "mtl", "note_spanish": "Montreal Spanish institutes and universities.", "note_french": "Strong DELF/DALF network in Montreal."},
        {"label": "Vancouver, BC", "value": "van", "note_spanish": "Lower Mainland university partners.", "note_french": "Alliance Française Vancouver."},
        {"label": "Ottawa, ON", "value": "ott", "note_spanish": "National capital region centers.", "note_french": "Alliance Française Ottawa."},
        {"label": "Quebec City, QC", "value": "qc", "note_spanish": "Fewer Spanish exam dates — check portal.", "note_french": "DELF/DALF common in Quebec City."},
        {"label": "Calgary, AB", "value": "cal", "note_spanish": "Alberta university partners.", "note_french": "Alliance Française Calgary."},
    ],
    "mx": [
        {"label": "Mexico City (CDMX)", "value": "cdmx", "note_spanish": "Largest DELE/SIELE network in Mexico.", "note_french": "Alliance Française Mexico City."},
        {"label": "Guadalajara", "value": "gdl", "note_spanish": "Western Mexico hub.", "note_french": "Alliance Française Guadalajara."},
        {"label": "Monterrey", "value": "mty", "note_spanish": "Northern Mexico — industrial hub with regular sessions.", "note_french": "Check AF Monterrey for French exam dates."},
        {"label": "Puebla", "value": "pue", "note_spanish": "Central Mexico university partners.", "note_french": "Smaller French exam calendar."},
        {"label": "Cancún", "value": "cun", "note_spanish": "Southeast — tourist region with seasonal sessions.", "note_french": "Limited French exam dates."},
    ],
    "es": [
        {"label": "Madrid", "value": "mad", "note_spanish": "Instituto Cervantes HQ — widest DELE calendar.", "note_french": "Alliance Française Madrid."},
        {"label": "Barcelona", "value": "bcn", "note_spanish": "Catalonia's main DELE/SIELE hub.", "note_french": "Alliance Française Barcelona."},
        {"label": "Valencia", "value": "vlc", "note_spanish": "Mediterranean coast — regular sessions.", "note_french": "Alliance Française Valencia."},
        {"label": "Seville", "value": "svq", "note_spanish": "Andalusia hub.", "note_french": "Alliance Française Seville."},
        {"label": "Bilbao", "value": "bio", "note_spanish": "Basque Country centers.", "note_french": "Alliance Française Bilbao."},
    ],
    "fr": [
        {"label": "Paris", "value": "par", "note_spanish": "Instituto Cervantes Paris.", "note_french": "Largest DELF/DALF/TCF calendar in France."},
        {"label": "Lyon", "value": "lys", "note_spanish": "Rhône-Alpes Spanish centers.", "note_french": "Major DELF hub outside Paris."},
        {"label": "Marseille", "value": "mrs", "note_spanish": "Provence Spanish institutes.", "note_french": "Alliance Française Marseille."},
        {"label": "Toulouse", "value": "tls", "note_spanish": "Southwest France.", "note_french": "University and AF partners in Toulouse."},
        {"label": "Bordeaux", "value": "bod", "note_spanish": "Atlantic coast Spanish centers.", "note_french": "Alliance Française Bordeaux."},
        {"label": "Lille", "value": "lil", "note_spanish": "Northern France.", "note_french": "Alliance Française Lille."},
    ],
    "co": [
        {"label": "Bogotá", "value": "bog", "note_spanish": "Colombia's main DELE/SIELE hub.", "note_french": "Alliance Française Bogotá."},
        {"label": "Medellín", "value": "med", "note_spanish": "Antioquia university partners.", "note_french": "Alliance Française Medellín."},
        {"label": "Cali", "value": "cal", "note_spanish": "Pacific region centers.", "note_french": "Check AF Cali for French exams."},
    ],
    "ar": [
        {"label": "Buenos Aires", "value": "bue", "note_spanish": "Argentina's largest DELE network.", "note_french": "Alliance Française Buenos Aires."},
        {"label": "Córdoba", "value": "cor", "note_spanish": "Central Argentina university partners.", "note_french": "Alliance Française Córdoba."},
    ],
    "uk": [
        {"label": "London", "value": "lon", "note_spanish": "Instituto Cervantes London.", "note_french": "Alliance Française London."},
        {"label": "Manchester", "value": "man", "note_spanish": "Northwest England partners.", "note_french": "Alliance Française Manchester."},
        {"label": "Edinburgh", "value": "edi", "note_spanish": "Scotland Spanish centers.", "note_french": "Alliance Française Edinburgh."},
    ],
    "de": [
        {"label": "Berlin", "value": "ber", "note_spanish": "Instituto Cervantes Berlin.", "note_french": "Alliance Française Berlin."},
        {"label": "Munich", "value": "mun", "note_spanish": "Bavaria Spanish institutes.", "note_french": "Alliance Française Munich."},
        {"label": "Hamburg", "value": "ham", "note_spanish": "Northern Germany partners.", "note_french": "Alliance Française Hamburg."},
    ],
    "br": [
        {"label": "São Paulo", "value": "sao", "note_spanish": "Brazil's largest DELE network.", "note_french": "Alliance Française São Paulo."},
        {"label": "Rio de Janeiro", "value": "rio", "note_spanish": "Southeast Brazil hub.", "note_french": "Alliance Française Rio."},
    ],
    "ma": [
        {"label": "Casablanca", "value": "cas", "note_spanish": "Limited Spanish exams.", "note_french": "Major DELF hub in Morocco."},
        {"label": "Rabat", "value": "rab", "note_spanish": "Capital region.", "note_french": "Institut français du Maroc — Rabat."},
        {"label": "Marrakech", "value": "mar", "note_spanish": "Southern Morocco.", "note_french": "Alliance Française Marrakech."},
    ],
    "vn": [
        {"label": "Hanoi", "value": "han", "note_spanish": "Northern Vietnam.", "note_french": "Institut français Hanoi — DELF/TCF."},
        {"label": "Ho Chi Minh City", "value": "sgn", "note_spanish": "Southern Vietnam.", "note_french": "Institut français HCMC."},
    ],
}


def locations_for_country(country_value: str) -> list[dict[str, str]]:
    return LOCATIONS.get(country_value, [])


def location_note(exam: str, location: dict[str, str]) -> str:
    family = EXAM_FAMILY.get(exam, "spanish")
    key = "note_french" if family == "french" else "note_spanish"
    return location.get(key, "")
