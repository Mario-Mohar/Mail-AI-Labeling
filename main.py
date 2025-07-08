import json
import base64
import email
import datetime
from gmail_utils import get_gmail_service, get_or_create_label, move_email_to_label
from ai_classify import classify_email

# ==== Einstellungen ====
REGELN_DATEI = "regeln.json"
LOG_DATEI = "mail_log.txt"
MAX_EMAILS = 10  # Begrenzung zur Sicherheit

# ==== Regeln laden ====
try:
    with open(REGELN_DATEI, "r", encoding="utf-8") as f:
        regeln = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    regeln = {}

# ==== Gmail verbinden ====
service = get_gmail_service()

# ==== E-Mails aus INBOX abrufen ====
results = service.users().messages().list(
    userId='me',
    labelIds=['INBOX'],
    q="is:unread"
).execute()

messages = results.get('messages', [])[:MAX_EMAILS]

print(f"📬 {len(messages)} neue ungelesene E-Mails gefunden.")

# ==== Verarbeiten ====
for msg in messages:
    msg_id = msg['id']
    full_msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = full_msg['payload']['headers']

    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Kein Betreff)')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    
    # Body auslesen (text/plain)
    body_data = ""
    if 'parts' in full_msg['payload']:
        for part in full_msg['payload']['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body_data = part['body']['data']
                break
    elif 'body' in full_msg['payload'] and 'data' in full_msg['payload']['body']:
        body_data = full_msg['payload']['body']['data']

    try:
        body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
    except:
        body = ""

    # ==== KI-Kategorisierung ====
    kategorie = classify_email(subject, sender, body, regeln)

    if not kategorie:
        print(f"⚠️  Keine Kategorie erkannt für: {subject}")
        continue

    # ==== Regel prüfen oder neu anlegen ====
    if kategorie not in regeln:
        labelname = kategorie.capitalize()

        # Neue Regel lokal speichern
        regeln[kategorie] = {
            "keywords": [],
            "label": labelname
        }

        with open(REGELN_DATEI, "w", encoding="utf-8") as f:
            json.dump(regeln, f, indent=2, ensure_ascii=False)

        # Loggen
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logtext = (
            f"\n[{timestamp}] Neue Kategorie von Gemini AI erkannt:\n"
            f"  - Kategorie: {kategorie}\n"
            f"  - Label: {labelname}\n"
            f"  - Quelle: Gemini-Antwort\n"
        )
        with open(LOG_DATEI, "a", encoding="utf-8") as f:
            f.write(logtext)

        print(logtext.strip())

    # ==== Gmail Label ID holen oder erstellen ====
    label_id = get_or_create_label(service, regeln[kategorie]["label"])

    # ==== E-Mail verschieben ====
    move_email_to_label(service, msg_id, label_id)

    print(f"✅ E-Mail '{subject}' wurde als '{kategorie}' klassifiziert und verschoben.\n")