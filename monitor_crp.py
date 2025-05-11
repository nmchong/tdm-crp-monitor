import time
import csv
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

# ─── Configuration ──────────────────────────────────────────────────────────────

CRP_URL        = "https://crp.the-examples-book.com/"
CSV_FILE       = "seen_projects.csv"
CHECK_INTERVAL = 60 * 60   # seconds (1 hour)

# These will be provided via env vars in GitHub Actions:
SMTP_SERVER    = os.getenv("SMTP_SERVER")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS  = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO       = os.getenv("EMAIL_TO")

# ─── Helpers ────────────────────────────────────────────────────────────────────

def load_seen_urls():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return {row["url"] for row in csv.DictReader(f)}

def save_new_rows(rows):
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url","location","partnership","project_name"])
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

def send_email(new_rows):
    body_lines = []
    for r in new_rows:
        body_lines.append(f"- {r['project_name']} ({r['location']}, {r['partnership']})\n  {r['url']}")
    body = "New CRP projects detected:\n\n" + "\n\n".join(body_lines)
    msg = MIMEText(body)
    msg["Subject"] = f"[CRP] {len(new_rows)} new project(s) added"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ─── Core Scraping & Detection ─────────────────────────────────────────────────

def check_for_new_projects():
    resp = requests.get(CRP_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find("table", id="projects-table")
    rows = []
    for tr in table.tbody.find_all("tr"):
        link = tr.find("td", {"data-label":"Project Name"}).a
        url = link["href"]
        project_name = link.get_text(strip=True)
        location = tr.find("td", {"data-label":"Location"}).get_text(strip=True)
        partnership = tr.find("td", {"data-label":"Partnership"}).get_text(strip=True)
        rows.append({
            "url": url,
            "project_name": project_name,
            "location": location,
            "partnership": partnership
        })

    seen = load_seen_urls()
    new_rows = [r for r in rows if r["url"] not in seen]
    if new_rows:
        save_new_rows(new_rows)
        send_email(new_rows)
        print(f"Found {len(new_rows)} new project(s); email sent.")
    else:
        print("No new projects.")

# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    check_for_new_projects()
