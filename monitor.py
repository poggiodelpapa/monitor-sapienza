import hashlib
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import difflib

URL = "https://www.uniroma1.it/it/node/40540"
HASH_FILE = "last_hash.txt"
CONTENT_FILE = "last_content.txt"

EMAIL_MITTENTE = os.environ["EMAIL_MITTENTE"]
EMAIL_DESTINATARIO = os.environ["EMAIL_DESTINATARIO"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
FORCE_EMAIL = os.environ.get("FORCE_EMAIL", "false").lower() == "true"

SENDER_NAME = "Monitor Sapienza"


def get_clean_text(soup):
    """Estrae il testo pulito del contenuto principale."""
    main_content = soup.find("div", class_="node__content")
    if not main_content:
        return None, None
    # Testo leggibile per il diff
    text = main_content.get_text(separator="\n", strip=True)
    # HTML per l'hash
    html = str(main_content)
    return text, html


def compute_diff(old_text, new_text):
    """Restituisce le righe aggiunte/rimosse tra vecchio e nuovo testo."""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile="Precedente", tofile="Attuale",
        lineterm=""
    ))
    if not diff:
        return "(nessuna differenza testuale rilevata)"
    # Mostriamo solo le righe +/- per leggibilità, max 80 righe
    meaningful = [l for l in diff if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    meaningful = meaningful[:80]
    return "\n".join(meaningful)


def main():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    new_text, new_html = get_clean_text(soup)

    if new_html is None:
        print("⚠️ Contenuto principale non trovato nella pagina.")
        return

    current_hash = hashlib.sha256(new_html.encode("utf-8")).hexdigest()

    # Leggi hash e contenuto precedenti
    last_hash = None
    last_text = None

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()

    if os.path.exists(CONTENT_FILE):
        with open(CONTENT_FILE, "r", encoding="utf-8") as f:
            last_text = f.read()

    if FORCE_EMAIL:
        print("FORZATURA: Invio email di test...")
        diff_text = compute_diff(last_text or "", new_text) if last_text else "(nessun contenuto precedente salvato)"
        send_email(URL, diff_text)

    changed = (last_hash is not None) and (current_hash != last_hash)

    if changed and not FORCE_EMAIL:
        diff_text = compute_diff(last_text or "", new_text)
        send_email(URL, diff_text)
        print("📧 Cambiamento rilevato, email inviata.")
    elif last_hash is None:
        print("📝 Prima esecuzione: hash iniziale salvato, nessuna email inviata.")
    else:
        print("✅ Nessun cambiamento rilevato.")

    # Aggiorna i file solo se c'è stato un cambiamento (o è la prima volta)
    if last_hash is None or changed:
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        with open(CONTENT_FILE, "w", encoding="utf-8") as f:
            f.write(new_text)
        print("✅ Hash e contenuto aggiornati.")


def send_email(url, diff_text):
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SENDER_NAME} <{EMAIL_MITTENTE}>"
    msg["To"] = EMAIL_DESTINATARIO
    msg["Subject"] = "🔔 Monitor Sapienza - Novità rilevata!"

    body_plain = (
        f"È cambiato il contenuto della pagina:\n{url}\n\n"
        f"--- MODIFICHE RILEVATE ---\n"
        f"Le righe con '+' sono state aggiunte, quelle con '-' rimosse:\n\n"
        f"{diff_text}\n\n"
        f"Controlla subito!"
    )

    # Versione HTML con colori per leggibilità
    diff_html_lines = []
    for line in diff_text.splitlines():
        if line.startswith("+"):
            diff_html_lines.append(
                f'<div style="background:#e6ffed;color:#1a7f37;font-family:monospace;padding:2px 6px;">{line}</div>'
            )
        elif line.startswith("-"):
            diff_html_lines.append(
                f'<div style="background:#ffebe9;color:#cf222e;font-family:monospace;padding:2px 6px;">{line}</div>'
            )
        else:
            diff_html_lines.append(
                f'<div style="font-family:monospace;padding:2px 6px;color:#555;">{line}</div>'
            )
    diff_html = "\n".join(diff_html_lines)

    body_html = f"""
    <html><body style="font-family:sans-serif;max-width:700px;margin:auto;">
      <h2>🔔 Monitor Sapienza — Novità rilevata!</h2>
      <p>È cambiato il contenuto della pagina:<br>
         <a href="{url}">{url}</a></p>
      <h3>Modifiche rilevate</h3>
      <p style="color:#555;font-size:0.9em;">
        Righe in <span style="color:#1a7f37">verde (+)</span> = aggiunte &nbsp;|&nbsp;
        Righe in <span style="color:#cf222e">rosso (-)</span> = rimosse
      </p>
      <div style="border:1px solid #ddd;border-radius:6px;padding:10px;background:#fafafa;">
        {diff_html}
      </div>
      <br>
      <a href="{url}" style="background:#0066cc;color:white;padding:10px 20px;
         border-radius:5px;text-decoration:none;display:inline-block;">
        Controlla subito →
      </a>
    </body></html>
    """

    msg.attach(MIMEText(body_plain, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(EMAIL_MITTENTE, GMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_MITTENTE, EMAIL_DESTINATARIO, msg.as_string())

    print("✅ Email inviata!")


if __name__ == "__main__":
    main()
