### Overview
Routinely scrapes Purdue's Data Mine Corporate Partners projects list to check if new projects are added.
- Scrapes [https://crp.the-examples-book.com/](https://crp.the-examples-book.com/) (Purdue's Data Mine corporate partners list) for new projects in West Lafayette campus
- Uses cron jobs to run *monitor_crp.py* (scrapes the website every x amount of time)
- Saves projects to *seen_projects.csv* and emails if any new projects added

### Customization
#### Environment variables
- SMTP_SERVER: hostname of smtp (e.g. smtp.gmail.com for gmail)
- SMTP_PORT: standard is 587
- EMAIL_ADDRESS: email address you are sending from
- EMAIL_PASSWORD: password of above -- this is "app password" from gmail settings, not your login password
- EMAIL_TO: email address you will send to (make sure to check spam folder)
#### Update customization
- Change check_for_new_projects() to change the year to scrape and other info like location
- Edit .github/workflows/monitor.yml to change cron-job frequency
