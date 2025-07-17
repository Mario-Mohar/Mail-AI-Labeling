import json
import base64
import email
import datetime
import requests
from gmail_utils import get_gmail_service, get_or_create_label, move_email_to_label
from ai_classify import classify_email

# ==== Einstellungen ====
REGELN_DATEI = "regeln.json"
LOG_DATEI = "mail_log.txt"
MAX_EMAILS = 50  # Begrenzung zur Sicherheit
UNSUBSCRIBE_LOG = "unsubscribe_log.txt"

KATEGORIEN = ["rechnung", "fußball", "newsletter", "spam", "privat", "arbeit", "werbung", "sonstiges"]


def log_unsubscribe_link(subject, url):
    with open(UNSUBSCRIBE_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} | {subject} | {url}\n")


def is_valid_url(url):
    return isinstance(url, str) and url.startswith("http")


def get_email_body(full_msg):
    body_data = ""
    # Suche zuerst nach text/plain
    if 'parts' in full_msg['payload']:
        for part in full_msg['payload']['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body_data = part['body']['data']
                break
        # Wenn kein text/plain gefunden, nimm text/html
        if not body_data:
            for part in full_msg['payload']['parts']:
                if part['mimeType'] == 'text/html' and 'data' in part['body']:
                    body_data = part['body']['data']
                    break
    elif 'body' in full_msg['payload'] and 'data' in full_msg['payload']['body']:
        body_data = full_msg['payload']['body']['data']
    try:
        return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
    except Exception:
        return ""


def extract_list_unsubscribe(headers):
    for h in headers:
        if h['name'].lower() == 'list-unsubscribe':
            return h['value']
    return None


def abmelden_via_list_unsubscribe(header_value, subject):
    import re
    # Suche nach URL im Header
    urls = re.findall(r'<(http[^>]+)>', header_value)
    if urls:
        unsubscribe_url = urls[0]
        print(f"Automatische Abmeldung über List-Unsubscribe-URL: {unsubscribe_url}")
        log_unsubscribe_link(subject, unsubscribe_url)
        try:
            response = requests.get(unsubscribe_url, timeout=10)
            print("Abmeldung durchgeführt, Status:", response.status_code)
        except Exception as e:
            print("Fehler bei der Abmeldung:", e)
        return True
    # Optional: Mailto-Adresse extrahieren und E-Mail senden
    mailtos = re.findall(r'<mailto:([^>]+)>', header_value)
    if mailtos:
        print(f"Abmeldung per E-Mail an: {mailtos[0]}")
        log_unsubscribe_link(subject, f"mailto:{mailtos[0]}")
        # Hier könntest du automatisiert eine E-Mail senden (z.B. mit smtplib)
        return True
    return False


def main():
    # ==== Regeln laden ====
    try:
        with open(REGELN_DATEI, "r", encoding="utf-8") as f:
            regeln = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        regeln = {}

    # ==== Gmail verbinden ====
    service = get_gmail_service()

    # ==== Gmail Labels abrufen (für Gemini-Erkennung) ====
    label_response = service.users().labels().list(userId='me').execute()
    gmail_labels = [label['name'].lower() for label in label_response.get('labels', [])]

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

        body = get_email_body(full_msg)

        # ==== KI-Kategorisierung & Newsletter-Check ====
        result = classify_email(subject, sender, body, regeln, gmail_labels)
        if not result:
            kategorie = None
            ist_newsletter = False
            ist_unbezahlt = False
            unsubscribe_url = None
        else:
            kategorie = result[0]
            ist_newsletter = result[1]
            ist_unbezahlt = result[2]
            unsubscribe_url = result[3]

        # Kategorientest
        if kategorie not in KATEGORIEN:
            kategorie = "sonstiges"

        if not kategorie:
            print(f"⚠️  Keine Kategorie erkannt für: {subject}")
            continue

        # ==== Regel prüfen oder neu anlegen ====
        if kategorie not in regeln:
            labelname = kategorie.capitalize()
            regeln[kategorie] = {
                "keywords": [],
                "label": labelname
            }
            with open(REGELN_DATEI, "w", encoding="utf-8") as f:
                json.dump(regeln, f, indent=2, ensure_ascii=False)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logtext = (
                f"\n[{timestamp}] Neue Kategorie von Gemini AI erkannt:\n"
                f"  - Kategorie: {kategorie}\n"
                f"  - Label: {labelname}\n"
                f"  - Quelle: Gemini-Antwort + Gmail-Labels\n"
            )
            with open(LOG_DATEI, "a", encoding="utf-8") as f:
                f.write(logtext)
            print(logtext.strip())

        # ==== Gmail Label ID holen oder erstellen ====
        label_id = get_or_create_label(service, regeln[kategorie]["label"])

        # ==== E-Mail verschieben ====
        move_email_to_label(service, msg_id, label_id)
        print(f"✅ E-Mail '{subject}' wurde als '{kategorie}' klassifiziert und verschoben.\n")

        # ==== Automatische Newsletter-Abmeldung über List-Unsubscribe-Header ====
        list_unsubscribe = extract_list_unsubscribe(headers)
        if ist_newsletter and ist_unbezahlt and list_unsubscribe:
            abmelden_via_list_unsubscribe(list_unsubscribe, subject)


if __name__ == "__main__":
    main()
