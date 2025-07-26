import json
import logging
from typing import Dict

def lade_regeln(regeln_datei: str) -> Dict:
    """Lädt die Regeln aus der Datei oder gibt ein leeres Dict zurück."""
    try:
        with open(regeln_datei, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning("Regeln konnten nicht geladen werden, leeres Dict wird verwendet.")
        return {}

def speichere_regeln(regeln: Dict, regeln_datei: str) -> None:
    """Speichert die Regeln in die Datei."""
    with open(regeln_datei, "w", encoding="utf-8") as f:
        json.dump(regeln, f, indent=2, ensure_ascii=False) 