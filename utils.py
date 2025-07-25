import base64
import datetime
import requests
import re
from typing import Any, Dict, List, Optional

def get_email_body(full_msg: dict) -> str:
    """Extrahiert den Body einer E-Mail (text/plain bevorzugt, sonst text/html)."""
    body_data = ""
    if 'parts' in full_msg['payload']:
        for part in full_msg['payload']['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body_data = part['body']['data']
                break
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

def extract_list_unsubscribe(headers: List[Dict[str, Any]]) -> Optional[str]:
    """Extrahiert den List-Unsubscribe-Header, falls vorhanden."""
    for h in headers:
        if h['name'].lower() == 'list-unsubscribe':
            return h['value']
    return None

def abmelden_via_list_unsubscribe(header_value: str, subject: str, log_unsubscribe_link_func) -> bool:
    """Versucht, sich über den List-Unsubscribe-Header abzumelden (HTTP oder mailto)."""
    urls = re.findall(r'<(http[^>]+)>', header_value)
    if urls:
        unsubscribe_url = urls[0]
        print(f"Automatische Abmeldung über List-Unsubscribe-URL: {unsubscribe_url}")
        log_unsubscribe_link_func(subject, unsubscribe_url)
        try:
            response = requests.get(unsubscribe_url, timeout=10)
            print("Abmeldung durchgeführt, Status:", response.status_code)
        except Exception as e:
            print("Fehler bei der Abmeldung:", e)
        return True
    mailtos = re.findall(r'<mailto:([^>]+)>', header_value)
    if mailtos:
        print(f"Abmeldung per E-Mail an: {mailtos[0]}")
        log_unsubscribe_link_func(subject, f"mailto:{mailtos[0]}")
        return True
    return False

def log_unsubscribe_link(subject: str, url: str, unsubscribe_log: str) -> None:
    """Loggt einen Abmelde-Link in die Logdatei."""
    with open(unsubscribe_log, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} | {subject} | {url}\n")

def logge_neue_kategorie(kategorie: str, labelname: str, log_datei: str) -> None:
    """Loggt das Anlegen einer neuen Kategorie in die Logdatei."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logtext = (
        f"\n[{timestamp}] Neue Kategorie von Gemini AI erkannt:\n"
        f"  - Kategorie: {kategorie}\n"
        f"  - Label: {labelname}\n"
        f"  - Quelle: Gemini-Antwort + Gmail-Labels\n"
    )
    with open(log_datei, "a", encoding="utf-8") as f:
        f.write(logtext) 