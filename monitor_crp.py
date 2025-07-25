import csv
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

# url to scrape, csv to save old (non-seen) projects
CRP_URL = "https://crp.the-examples-book.com/"
CSV_FILE = "seen_projects.csv"

# email credentials
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")


# load project names already seen
def load_seen_names():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline="", encoding="utf-8") as file:
        return {row["project_name"] for row in csv.DictReader(file)}


# save new projects to csv (overwrite with current list)
def save_all_rows(rows):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        fieldnames = ["partnership", "project_name", "semester", "location"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "partnership": row["partnership"],
                "project_name": row["project_name"],
                "semester": row["semester"],
                "location": row["location"],
            })


# function to send email
def send_email(new_rows):
    count = len(new_rows)
    subject = f"{count} new tdm crp projs"

    lines = [
        "new data mine corporate partners projs for 2025-26",
        ""
    ]
    for row in new_rows:
        lines.append(
            f"{row['partnership']}: {row['project_name']} "
            f"({row['semester']}; {row['location']}) -- {row['url']}"
        )

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


# check if any new projects (main)
def check_for_new_projects():
    # fetch & parse
    response = requests.get(CRP_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table", id="projects-table")

    # use only "2025-2026" rows
    all_rows = []
    for tr in table.tbody.find_all("tr"):
        cells = tr.find_all("td")
        year = cells[0].get_text(strip=True)
        if year != "2025-2026":
            continue

        location = cells[1].get_text(strip=True)
        if location != "West Lafayette, IN":
            continue
        partnership = cells[2].get_text(strip=True)
        semester = cells[4].get_text(strip=True)
        link = cells[3].find("a")
        project_name= link.get_text(strip=True)
        url = link["href"]

        all_rows.append({
            "partnership": partnership,
            "project_name": project_name,
            "semester": semester,
            "location": location,
            "url": url,
        })

    # compare against current csv
    seen = load_seen_names()
    new_rows = [row for row in all_rows if row["project_name"] not in seen]

    # always update csv to current list (silent delete)
    save_all_rows(all_rows)

    # email if new rows
    if new_rows:
        send_email(new_rows)
        print(f"Found {len(new_rows)} new 2025-2026 project(s), email sent")
    else:
        print("No new 2025-2026 projects")




if __name__ == "__main__":
    check_for_new_projects()
