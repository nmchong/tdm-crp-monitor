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


# save new projects to csv
def save_new_rows(rows):
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
        fieldnames = ["partnership", "project_name", "semester", "location"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if write_header:
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
    try:
        # fetch & parse
        print(f"Fetching data from {CRP_URL}...")
        response = requests.get(CRP_URL)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response content: {response.text[:500]}...")
            return
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table", id="projects-table")
        
        if not table:
            print("Error: Could not find table with id 'projects-table'")
            print(f"Page content preview: {response.text[:1000]}...")
            return
            
        if not table.tbody:
            print("Error: Could not find tbody in table")
            return
            
        print(f"Found table with {len(table.tbody.find_all('tr'))} rows")
        
        # use only "2025-2026" rows
        all_rows = []
        west_lafayette_rows = []
        available_locations = set()
        
        for tr in table.tbody.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 5:
                print(f"Skipping row with insufficient cells: {len(cells)}")
                continue
                
            year = cells[0].get_text(strip=True)
            if year != "2025-2026":
                continue

            location = cells[1].get_text(strip=True)
            available_locations.add(location)
            
            if "West Lafayette, IN" not in location:
                continue
            partnership = cells[2].get_text(strip=True)
            semester = cells[4].get_text(strip=True)
            link = cells[3].find("a")
            if not link:
                print(f"No link found in row: {cells[3]}")
                continue
            project_name= link.get_text(strip=True)
            url = link["href"]

            west_lafayette_rows.append({
                "partnership": partnership,
                "project_name": project_name,
                "semester": semester,
                "location": location,
                "url": url,
            })
            
        print(f"Available locations for 2025-2026: {sorted(available_locations)}")
        print(f"Found {len(west_lafayette_rows)} West Lafayette projects for 2025-2026")
        
        all_rows = west_lafayette_rows

        # compare against current csv
        seen = load_seen_names()
        new_rows = [row for row in all_rows if row["project_name"] not in seen]

        # save new csv & email if new rows
        if new_rows:
            save_new_rows(new_rows)
            
            # Only send email if credentials are configured
            if all([SMTP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_TO]):
                try:
                    send_email(new_rows)
                    print(f"Found {len(new_rows)} new 2025-2026 project(s), email sent")
                except Exception as e:
                    print(f"Found {len(new_rows)} new 2025-2026 project(s), saved to CSV but email failed: {e}")
            else:
                print(f"Found {len(new_rows)} new 2025-2026 project(s), saved to CSV (email not configured)")
        else:
            print("No new 2025-2026 projects")
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()




if __name__ == "__main__":
    check_for_new_projects()
