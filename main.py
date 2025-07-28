import json
import base64
import email
import datetime
import requests
import logging
import os
from dotenv import load_dotenv
from gmail_utils import get_gmail_service, get_or_create_label, move_email_to_label, get_all_labels, get_emails_for_label
from ai_classify import classify_email
from utils import get_email_body, extract_list_unsubscribe, abmelden_via_list_unsubscribe, log_unsubscribe_link, logge_neue_kategorie
from rules_utils import lade_regeln, speichere_regeln

# ==== Einstellungen ====
load_dotenv()
REGELN_DATEI = os.getenv("REGELN_DATEI", "regeln.json")
LOG_DATEI = os.getenv("LOG_DATEI", "mail_log.txt")
MAX_EMAILS = int(os.getenv("MAX_EMAILS", 50))
UNSUBSCRIBE_LOG = os.getenv("UNSUBSCRIBE_LOG", "unsubscribe_log.txt")


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def hole_gmail_labels(service):
    """Holt alle Gmail-Labels als Liste (kleingeschrieben)."""
    label_response = service.users().labels().list(userId='me').execute()
    return [label['name'].lower() for label in label_response.get('labels', [])]


def hole_ungelesene_emails(service):
    """Holt ungelesene E-Mails aus der INBOX (max. MAX_EMAILS)."""
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        q="is:unread"
    ).execute()
    return results.get('messages', [])[:MAX_EMAILS]


def verarbeite_email(msg, service, regeln, gmail_labels, trainingsdaten=None):
    """Verarbeitet eine einzelne E-Mail: Klassifizierung, Label, ggf. neue Regel, Verschieben, Abmelden."""
    msg_id = msg['id']
    full_msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = full_msg['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Kein Betreff)')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    body = get_email_body(full_msg)

    # ==== KI-Kategorisierung & Newsletter-Check ====
    result = classify_email(subject, sender, body, regeln, gmail_labels, trainingsdaten)
    kategorie = result.get("kategorie")
    ist_newsletter = result.get("ist_newsletter", False)
    ist_unbezahlt = result.get("ist_unbezahlt", False)
    unsubscribe_url = result.get("unsubscribe_url")

    # Dynamische Kategorien aus Regeln
    kategorien_regeln = list(regeln.keys())
    kategorien_normalisiert = [k.lower().strip() for k in kategorien_regeln]
    if not kategorie:
        logging.warning(f"Keine Kategorie erkannt für: {subject}")
        return
    if kategorie.lower().strip() not in kategorien_normalisiert:
        # Neue Kategorie automatisch als Regel anlegen
        labelname = kategorie.capitalize()
        regeln[kategorie] = {
            "keywords": [],
            "label": labelname
        }
        speichere_regeln(regeln, REGELN_DATEI)
        logge_neue_kategorie(kategorie, labelname, LOG_DATEI)
        logging.info(f"Neue Kategorie '{kategorie}' wurde zu den Regeln hinzugefügt.")

    # ==== Regel prüfen oder neu anlegen ====
    if kategorie not in regeln:
        labelname = kategorie.capitalize()
        regeln[kategorie] = {
            "keywords": [],
            "label": labelname
        }
        speichere_regeln(regeln, REGELN_DATEI)
        logge_neue_kategorie(kategorie, labelname, LOG_DATEI)

    # ==== Gmail Label ID holen oder erstellen ====
    label_id = get_or_create_label(service, regeln[kategorie]["label"])

    # ==== E-Mail verschieben ====
    move_email_to_label(service, msg_id, label_id)
    logging.info(f"E-Mail '{subject}' wurde als '{kategorie}' klassifiziert und verschoben.")

    # ==== Automatische Newsletter-Abmeldung über List-Unsubscribe-Header ====
    list_unsubscribe = extract_list_unsubscribe(headers)
    if ist_newsletter and ist_unbezahlt and list_unsubscribe:
        abmelden_via_list_unsubscribe(list_unsubscribe, subject, lambda s, u: log_unsubscribe_link(s, u, UNSUBSCRIBE_LOG))


def sammle_label_trainingsdaten(service, max_emails_per_label=50):
    """Durchsucht alle Labels und sammelt Betreff, Absender, Body der enthaltenen E-Mails als Trainingsdaten."""
    label_dict = get_all_labels(service)
    trainingsdaten = []
    for label_id, label_name in label_dict.items():
        if label_name.lower() in ["inbox", "spam", "papierkorb", "trash", "sent", "gesendet"]:
            continue  # Systemordner überspringen
        messages = get_emails_for_label(service, label_id, max_results=max_emails_per_label)
        for msg in messages:
            msg_id = msg['id']
            try:
                full_msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                headers = full_msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Kein Betreff)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                body = get_email_body(full_msg)
                trainingsdaten.append({
                    "label": label_name,
                    "subject": subject,
                    "sender": sender,
                    "body": body
                })
            except Exception as e:
                logging.warning(f"Fehler beim Einlesen einer E-Mail aus Label '{label_name}': {e}")
    logging.info(f"Trainingsdaten aus {len(label_dict)} Labels gesammelt. Gesamt: {len(trainingsdaten)} E-Mails.")
    return trainingsdaten


def main():
    """Hauptfunktion: Lerne aus bestehenden Label-Inhalten, dann verarbeite neue ungelesene E-Mails."""
    regeln = lade_regeln(REGELN_DATEI)
    service = get_gmail_service()
    gmail_labels = hole_gmail_labels(service)
    # Schritt 1: Bestehende Label-Inhalte einlesen und als Trainingsdaten sammeln
    trainingsdaten = sammle_label_trainingsdaten(service, max_emails_per_label=50)
    # Schritt 2: Neue ungelesene E-Mails wie bisher verarbeiten
    messages = hole_ungelesene_emails(service)
    logging.info(f"📬 {len(messages)} neue ungelesene E-Mails gefunden.")
    for msg in messages:
        verarbeite_email(msg, service, regeln, gmail_labels, trainingsdaten)


if __name__ == "__main__":
    main()
