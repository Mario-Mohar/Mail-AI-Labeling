import os
import google.generativeai as genai
from dotenv import load_dotenv
import json


load_dotenv()

_model = None

def classify_email(subject, sender, body, regeln, gmail_labels=None):
    """
    Klassifiziert eine E-Mail mithilfe von Gemini AI basierend auf Regeln
    und optional bekannten Gmail-Labels.

    :param subject: E-Mail-Betreff
    :param sender: Absender-Adresse
    :param body: Textinhalt der E-Mail
    :param regeln: Dict mit bekannten Kategorien/Labels
    :param gmail_labels: (Optional) Liste vorhandener Gmail-Labels
    :return: erkannte Kategorie (str) oder None
    """
    global _model

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ Gemini API Key fehlt. Bitte .env Datei erstellen oder setzen.")

    if _model is None:
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("models/gemini-2.5-flash")

    kategorien = list(regeln.keys())
    if gmail_labels:
        # Labels aus Gmail ergänzen (die nicht schon in Regeln stehen)
        gmail_labels_clean = [lbl.lower() for lbl in gmail_labels if lbl.lower() not in kategorien]
        kategorien += gmail_labels_clean

    prompt = f"""
Du bist ein intelligenter E-Mail-Classifier. Weise die E-Mail einer der folgenden Kategorien zu:
{json.dumps(kategorien, ensure_ascii=False)}

E-Mail-Betreff: {subject}
Absender: {sender}
Inhalt (ggf. gekürzt): {body[:2000]}

Gib nur eine Rückgabe aus: den exakten Namen der Kategorie (z. B. "rechnung", "newsletter", ...).
Wenn keine passende Kategorie vorhanden ist, gib "unbekannt" zurück.
"""

    try:
        response = _model.generate_content(prompt)
        antwort = response.text.strip().lower()

        if antwort in kategorien:
            return antwort
        if antwort == "unbekannt":
            return None

        print(f"⚠️ Unerwartete Gemini-Antwort: {antwort}")
        return None
    except Exception as e:
        print(f"❌ Gemini-Fehler: {e}")
        return None
