from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception:
            print("⚠️ Fehler mit token.json – Datei wird neu erstellt.")
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute()
    for label in labels['labels']:
        if label['name'].lower() == label_name.lower():
            return label['id']
    new_label = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    created = service.users().labels().create(userId='me', body=new_label).execute()
    return created['id']

def move_email_to_label(service, message_id, label_id):
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={
            'addLabelIds': [label_id],
            'removeLabelIds': ['INBOX']
        }
    ).execute()

def get_all_labels(service):
    """Gibt alle Labels als Dict (id->name) zurück."""
    labels = service.users().labels().list(userId='me').execute()
    return {label['id']: label['name'] for label in labels['labels']}


def get_emails_for_label(service, label_id, max_results=100):
    """Holt bis zu max_results E-Mails für ein bestimmtes Label."""
    results = service.users().messages().list(
        userId='me',
        labelIds=[label_id],
        maxResults=max_results
    ).execute()
    return results.get('messages', [])
