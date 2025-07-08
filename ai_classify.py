import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ Gemini API Key fehlt. Bitte .env Datei erstellen.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("models/gemini-2.5-flash")

def classify_email(subject, sender, body, regeln):
    prompt = f"""
Du bist ein E-Mail-Classifier. Weise die E-Mail einer dieser Kategorien zu: {list(regeln.keys())}.
E-Mail-Betreff: {subject}
Absender: {sender}
Inhalt: {body[:2000]}
Nur eine Rückgabe: Der Label-Name (z. B. \"rechnung\", \"newsletter\", ...).
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower()
    except Exception as e:
        print(f"❌ Gemini-Fehler: {e}")
        return None
