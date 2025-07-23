import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import logging
from collections import namedtuple
import difflib

load_dotenv()

# Modellkapselung
class GeminiClassifier:
    def __init__(self):
        self._model = None
        self._api_key = os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise ValueError("❌ Gemini API Key fehlt. Bitte .env Datei erstellen oder setzen.")
        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel("models/gemini-1.5-pro")

    def classify(self, subject, sender, body, regeln, gmail_labels=None, trainingsdaten=None):
        """
        Klassifiziert eine E-Mail mithilfe von Gemini AI, optional mit Trainingsdaten.
        :return: Dict mit Schlüsseln: kategorie, ist_newsletter, ist_unbezahlt, unsubscribe_url
        """
        kategorien = list(regeln.keys())
        if gmail_labels:
            gmail_labels_clean = [lbl.lower().strip() for lbl in gmail_labels if lbl.lower().strip() not in kategorien]
            kategorien += gmail_labels_clean
        # Normalisiere Kategorien (Kleinschreibung, Whitespace)
        kategorien_normalisiert = [k.lower().strip() for k in kategorien]

        prompt_examples = ""
        if trainingsdaten:
            for item in trainingsdaten:
                prompt_examples += f"""
--- Beispiel ---
Label: {item['label']}
Betreff: {item['subject']}
Absender: {item['sender']}
Inhalt: {item['body'][:200]}
"""

        prompt = f"""
Du bist ein intelligenter E-Mail-Classifier. Hier sind Beispiele, wie E-Mails bisher klassifiziert wurden:
{prompt_examples}

--- Neue E-Mail zur Klassifizierung ---
Betreff: {subject}
Absender: {sender}
Inhalt (ggf. gekürzt): {body[:2000]}

Basierend auf den obigen Beispielen, weise die E-Mail einer der folgenden Kategorien zu:
{json.dumps(kategorien, ensure_ascii=False)}

Gib nur eine Rückgabe aus: den exakten Namen der Kategorie (z. B. "rechnung", "newsletter", ...).
Wenn keine passende Kategorie vorhanden ist, gib "unbekannt" zurück.
"""
        try:
            response = self._model.generate_content(prompt)
            antwort = response.text.strip().lower()
            logging.info(f"🔎 Gemini-Modellantwort: '{antwort}' für Betreff: '{subject}'")
            result = {
                "kategorie": None,
                "ist_newsletter": False,
                "ist_unbezahlt": False,
                "unsubscribe_url": None
            }
            # Robustere Prüfung: exakte Übereinstimmung oder Fuzzy-Match
            antwort_norm = antwort.strip().lower()
            if antwort_norm in kategorien_normalisiert:
                idx = kategorien_normalisiert.index(antwort_norm)
                result["kategorie"] = kategorien[idx]  # Originalname
                if antwort_norm == "newsletter":
                    result["ist_newsletter"] = True
            elif antwort_norm == "unbekannt":
                result["kategorie"] = None
            else:
                # Fuzzy-Matching (z. B. Tippfehler abfangen)
                matches = difflib.get_close_matches(antwort_norm, kategorien_normalisiert, n=1, cutoff=0.8)
                if matches:
                    idx = kategorien_normalisiert.index(matches[0])
                    result["kategorie"] = kategorien[idx]
                    if matches[0] == "newsletter":
                        result["ist_newsletter"] = True
                    logging.warning(f"⚠️ Fuzzy-Match: '{antwort}' wurde als '{kategorien[idx]}' interpretiert.")
                else:
                    logging.warning(f"⚠️ Unerwartete Gemini-Antwort: {antwort}")
                    result["kategorie"] = None
            return result
        except Exception as e:
            logging.error(f"❌ Gemini-Fehler: {e}")
            return {
                "kategorie": None,
                "ist_newsletter": False,
                "ist_unbezahlt": False,
                "unsubscribe_url": None
            }

# Singleton-Instanz für Modulgebrauch
_classifier_instance = None

def classify_email(subject, sender, body, regeln, gmail_labels=None, trainingsdaten=None):
    """Wrapper für die GeminiClassifier-Klasse, um Kompatibilität zu wahren."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = GeminiClassifier()
    return _classifier_instance.classify(subject, sender, body, regeln, gmail_labels, trainingsdaten)
