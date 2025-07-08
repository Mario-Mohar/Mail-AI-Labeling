# Mail-AI-Labeling – Automatisiertes Gmail-Labeling mit Gemini AI

Dieses Projekt scannt deine Gmail-Inbox via IMAP, klassifiziert E-Mails mithilfe von Gemini AI, verschiebt sie in passende Labels und protokolliert alle Aktionen.

---

## 🔧 Voraussetzungen

### 📦 Python & Pip

Installiere Python 3.12 oder höher: [https://www.python.org/downloads/](https://www.python.org/downloads/)

Dann:

```bash
pip install -r requirements.txt
```

### 🔐 API-Zugänge einrichten

#### 1. Google Gmail API

- Aktiviere die Gmail API: [https://console.developers.google.com/](https://console.developers.google.com/)
- Erstelle ein OAuth2-Client (Desktop-App)
- Lade `credentials.json` herunter und speichere es im Projektordner
- Beim ersten Lauf wirst du zur Authentifizierung im Browser weitergeleitet → es wird eine `token.json` erzeugt

#### 2. Gemini API

- [https://ai.google.dev](https://ai.google.dev) → API-Schlüssel generieren
- Erstelle eine Datei `.env` im Projektverzeichnis:

```
GEMINI_API_KEY=dein_schlüssel_hier
```

---

## 🚀 Projektstruktur

```text
mail_ai_labeling/
├── ai_classify.py           # Klassifizierung von E-Mails mit Gemini AI
├── gmail_utils.py           # Gmail API Zugriff & Label-Handling
├── main.py                  # Hauptprogramm zur Ausführung
├── rules.json               # Regeln für Label-Zuordnung
├── .env                     # Gemini API Key (nicht ins Repo einchecken)
├── credentials.json         # Gmail OAuth Datei (nicht ins Repo einchecken)
├── token.json               # Wird nach OAuth automatisch erzeugt
├── logs/
│   └── mail_log.txt         # Status- und Logeinträge
├── tests/
│   └── test_import.py       # Pytest-Modulimport-Test
└── .github/
    └── workflows/
        ├── lint.yml         # Linting & Modulprüfung (GitHub Actions)
        └── test.yml         # Pytest Workflow (GitHub Actions)
```

---

## 📄 Beispiel `rules.json`

```json
{
  "rechnung": {
    "keywords": ["Rechnung", "Zahlungserinnerung"],
    "label": "Rechnungen"
  },
  "newsletter": {
    "keywords": ["Abonnieren", "Newsletter", "Jetzt lesen"],
    "label": "Newsletter"
  }
}
```

Die Regeln werden bei Bedarf automatisch durch Gemini AI erweitert. Jede Erweiterung wird geloggt.

---

## 📋 `.gitignore`

Füge folgende Datei hinzu, um sensible Daten nicht zu veröffentlichen:

```gitignore
.env
credentials.json
token.json
logs/
__pycache__/
*.pyc
```

---

## ✅ GitHub Actions: Automatische Tests

### 1. Lint & Modulprüfung: `.github/workflows/lint.yml`

```yaml
name: Python Lint & Import Check

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install flake8

    - name: Run Linter
      run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

    - name: Add project root to PYTHONPATH
      run: echo "PYTHONPATH=$PWD" >> $GITHUB_ENV

    - name: Test Import Modules
      run: pytest tests/
```

### 2. Pytest: `.github/workflows/test.yml`

```yaml
name: Run Pytest Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest

    - name: Create fake .env for tests
      run: echo "GEMINI_API_KEY=placeholder_for_ci" > .env

    - name: Create dummy credentials.json
      run: echo '{ "installed": { "client_id": "dummy", "client_secret": "dummy", "redirect_uris": ["http://localhost"] } }' > credentials.json

    - name: Add project root to PYTHONPATH
      run: echo "PYTHONPATH=$PWD" >> $GITHUB_ENV

    - name: Run Pytest
      run: pytest tests/
```

---

## ⏰ Automatisiert lokal ausführen (Windows)

Plane über die Windows Aufgabenplanung die Ausführung von `main.py`, z. B.:

```bat
cd C:\Pfad\zum\Projekt
python main.py
```

Geplante Uhrzeit: 09:00 und 20:00 Uhr täglich.

---

## ☁️ Deployment auf Server

In Vorbereitung – empfohlen: Cronjob auf Linux-Server oder Docker mit `schedule`

---

## ☁️ Nächste Schritte (optional)

- Unit-Tests für KI-Klassifikation mit Mock-Daten
- Webhook/URL für Newsletter-Abmeldungen
- Deployment als selbstlaufender Dienst (Docker + VPS)

---

## 🧠 Autor & Idee

Mario Mohar – zur intelligenten E-Mail-Automatisierung im Alltag & Business 😊

