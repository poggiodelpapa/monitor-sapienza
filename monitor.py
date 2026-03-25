import hashlib
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from bs4 import BeautifulSoup

URL = "https://www.uniroma1.it/it/node/40540"
HASH_FILE = "last_hash.txt"

# Configurazione email
EMAIL_MITTENTE = os.environ.get("EMAIL_MITTENTE")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# Leggiamo la forzatura: se "true", consideriamo il flag attivo
FORCE_EMAIL = os.environ.get("FORCE_EMAIL", "false").lower() == "true"


def get_page_content(url: str) -> str:
    """Scarica la pagina e restituisce il testo rilevante."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    main = soup.find("main") or soup.find("article") or soup.find("body")
    return main.get_text(separator="\n", strip=True) if main else response.text


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_last_hash() -> str | None:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return None


def save_hash(hash_value: str):
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)


def send_email(url: str, is_forced: bool = False):
    subject = "⚠️ Cambiamento rilevato nella pagina Sapienza"
    
    # Rinominiamo l'oggetto se è un test forzato
    if is_forced:
        subject = "🧪 TEST (FORCE_EMAIL): Monitoraggio Sapienza"

    body_intro = "Questo è un test forzato dell'email." if is_forced else "È stato rilevato un cambiamento nella pagina monitorata:"

    body = f"""Ciao,

{body_intro}

🔗 {url}

Visita il link per vedere le novità.

---
Bot di monitoraggio GitHub Actions
"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_MITTENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_MITTENTE, GMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_MITTENTE, EMAIL_DESTINATARIO, msg.as_string())
    print("✅ Email inviata!")


def main():
    print(f"Controllo: {URL}")
    content = get_page_content(URL)
    current_hash = compute_hash(content)
    last_hash = load_last_hash()

    print(f"Hash attuale:   {current_hash}")
    print(f"Hash precedente: {last_hash}")

    # Logica per l'email di test
    if FORCE_EMAIL:
        print("FORZATURA ATTIVA: Invio email di test a prescindere dall'hash.")
        send_email(URL, is_forced=True)

    # Logica di monitoraggio standard
    if last_hash is None:
        print("Prima esecuzione: salvo hash iniziale.")
        save_hash(current_hash)
    elif current_hash != last_hash:
        print("⚠️ Cambiamento rilevato!")
        if not FORCE_EMAIL:  # Evita di inviare l'email due volte se l'avevi già forzata sopra
            send_email(URL)
        save_hash(current_hash)
    else:
        print("✅ Nessun cambiamento.")


if __name__ == "__main__":
    main()
