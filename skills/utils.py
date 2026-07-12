import re
import dateparser
from datetime import datetime


def format_for_whatsapp(text: str, max_length: int = 1500) -> str:
    """Adapte une réponse au format WhatsApp : pas de blocs de code Markdown,
    gras WhatsApp (*mot*) au lieu du gras Markdown (**mot**), longueur raisonnable."""
    if not text:
        return text

    formatted = text.replace("```", "").strip()
    formatted = re.sub(r"\*\*(.+?)\*\*", r"*\1*", formatted)

    if len(formatted) > max_length:
        truncated = formatted[:max_length].rsplit(" ", 1)[0]
        formatted = f"{truncated}…"

    return formatted


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
