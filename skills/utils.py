import dateparser
from datetime import datetime

def parse_date_to_iso(date_str: str) -> str:
    """Convertit une chaîne de date en langage naturel vers un format ISO 8601 pour PostgreSQL."""
    if not date_str:
        return None
        
    try:
        # On utilise dateparser pour comprendre le français ("demain à 10h")
        parsed_date = dateparser.parse(date_str, languages=['fr', 'en'])
        if parsed_date:
            return parsed_date.isoformat()
        return None
    except Exception as e:
        print(f"Erreur lors du parsing de la date '{date_str}': {e}")
        return None
