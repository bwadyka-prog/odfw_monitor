import os
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText

# Pull configurations from GitHub Secrets
URL = "https://myodfw.com/reserve-your-hunt?feedback_url=https%3A%2F%2Fmyodfw.com%2Freserve-your-hunt&ppp_mode=resource_list"
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASS = os.environ.get('GMAIL_APP_PASS')
TO_SMS_EMAIL = os.environ.get('TO_SMS_EMAIL')

def send_sms(body):
    msg = MIMEText(body)
    msg["Subject"] = "ODFW Alert"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_SMS_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.send_message(msg)

def check_calendar():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(3000) 

        # Using a broad selector for anything with a green background or 'available' class
        available_slots = page.locator("td.available, .calendar-day-green, [style*='background-color: green']").all()

        if len(available_slots) > 0:
            print(f"Found {len(available_slots)} available slot(s)!")
            send_sms(f"ODFW ALERT: Permit spot available! Book now: {URL}")
        else:
            print("No green slots found.")
            
        browser.close()

if __name__ == "__main__":
    check_calendar()
