import csv
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

CRP_URL   = "https://crp.the-examples-book.com/"
CSV_FILE  = "seen_projects.csv"

SMTP_SERVER    = os.getenv("SMTP_SERVER")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS  = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO       = os.getenv("EMAIL_TO")

def load_seen_names():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return {row["project_name"] for row in csv.DictReader(f)}

def save_new_rows(rows):
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["partnership", "project_name", "semester", "location"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for r in rows:
            writer.writerow({
                "partnership":   r["partnership"],
                "project_name":  r["project_name"],
                "semester":      r["semester"],
                "location":      r["location"],
            })

def send_email(new_rows):
    count = len(new_rows)
    subject = f"{count} new tdm crp projs"

    lines = [
        "new crp projs, 2025-26",
        ""
    ]
    for r in new_rows:
        lines.append(
            f"{r['partnership']}: {r['project_name']} "
            f"({r['semester']}; {r['location']}) -- {r['url']}"
        )

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def check_for_new_projects():
    # 1) Fetch & parse
    resp = requests.get(CRP_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", id="projects-table")

    # 2) Extract only 2025-2026 rows
    all_rows = []
    for tr in table.tbody.find_all("tr"):
        cells = tr.find_all("td")
        year = cells[0].get_text(strip=True)
        if year != "2025-2026":
            continue

        location    = cells[1].get_text(strip=True)
        partnership = cells[2].get_text(strip=True)
        semester    = cells[4].get_text(strip=True)
        link        = cells[3].find("a")
        project_name= link.get_text(strip=True)
        url         = link["href"]

        all_rows.append({
            "partnership":  partnership,
            "project_name": project_name,
            "semester":     semester,
            "location":     location,
            "url":          url,
        })

    # 3) Diff against our CSV
    seen = load_seen_names()
    new_rows = [r for r in all_rows if r["project_name"] not in seen]

    # 4) If there are any, save & email
    if new_rows:
        save_new_rows(new_rows)
        send_email(new_rows)
        print(f"Found {len(new_rows)} new 2025-2026 project(s); email sent.")
    else:
        print("No new 2025-2026 projects.")

if __name__ == "__main__":
    check_for_new_projects()
