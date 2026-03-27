<div align="center">
  <img src="logobg.png" alt="Sherlock Bands" width="300"/>
  <h1>🔔 Sherlock Bands</h1>
</div>

A lightweight GitHub Actions bot that watches a university web page for changes and sends an email notification with a **visual diff** of what changed.

Built to never miss updates on admission rankings at [Sapienza University of Rome](https://www.uniroma1.it/it/node/40540).

---

## How it works

```
Every hour → fetch page → hash content → compare with last run
    ├── no change  → silent, do nothing
    └── changed    → send email with diff → save new content to repo
```

1. **GitHub Actions** runs the script on a cron schedule (default: every hour)
2. **BeautifulSoup** scrapes and extracts the main content of the page
3. The content is **hashed with SHA-256** and compared to the previous run
4. If different, an **HTML email** is sent showing added lines in green and removed lines in red
5. The new hash and content are **committed back to the repo**, so state persists reliably across runs

---

## Stack

| Tool | Role |
|------|------|
| Python 3.12 | Core logic |
| `requests` + `BeautifulSoup4` | Page fetching and parsing |
| `difflib` | Text diff generation |
| `smtplib` + Gmail App Password | Email delivery |
| GitHub Actions | Scheduling and execution |
| Git (via Actions) | Persistent state storage |

---

## Features

- No false positives — state is committed to the repo, not cached
- Rich HTML email with colored diff (green = added, red = removed)
- Fully automated, no server or paid service required
- Runs within GitHub Actions free tier (uses ~30 min/month out of 2000)
- Credentials stored as GitHub Secrets, never in code

---

## Setup

### 1. Fork or clone this repo
```python
git clone https://github.com/poggiodelpapa/sherlock-bands
```

### 2. Configure Gmail

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. **Security** → **2-Step Verification** (must be enabled)
3. Search for **"App passwords"** → create one for "Mail"
4. Copy the 16-character password

### 3. Add GitHub Secrets

In your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | Value |
|--------|-------|
| `EMAIL_MITTENTE` | Gmail address used to send |
| `EMAIL_DESTINATARIO` | Address to receive notifications |
| `GMAIL_APP_PASSWORD` | 16-character app password from step 2 |

### 4. Enable write permissions for Actions

**Settings** → **Actions** → **General** → **Workflow permissions** → select **"Read and write permissions"**

### 5. Run manually once to initialize

**Actions** → **Monitora Pagina Sapienza** → **Run workflow**

The first run saves the initial state. From the second run onward, you'll only be notified when something actually changes.

---

## Customizing the URL

Edit the `URL` variable at the top of `monitor.py`:

```python
URL = "https://your-target-page.com"
```

## Customizing the schedule

Edit the cron expression in `monitor.yml`:

```yaml
- cron: "0 * * * *"    # every hour
- cron: "0 */6 * * *"  # every 6 hours
- cron: "0 9,18 * * *" # at 9am and 6pm daily
```

---

## Repo structure

```
monitor-sapienza/
├── monitor.py          ← main script
├── last_hash.txt       ← SHA-256 of last seen content (auto-updated)
├── last_content.txt    ← plain text of last seen content (auto-updated)
└── .github/
    └── workflows/
        └── monitor.yml ← Actions workflow definition
```

---

## Example notification

> **Subject:** 🔔 Monitor Sapienza - Novità rilevata!
>
> The page content has changed:
> https://www.uniroma1.it/it/node/40540
>
> ```diff
> + 15 new spots available for Computer Engineering
> + Application deadline: November 5th
> - Applications closed
> ```
