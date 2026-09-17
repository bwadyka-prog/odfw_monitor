import os
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText

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
        
        # Load page and wait for iframe network activity to finish
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(5000) 

        total_available = 0

        # Scan the main page AND all embedded iframes for green squares
        for frame in page.frames:
            try:
                slots = frame.locator("td.available").all()
                total_available += len(slots)
            except Exception:
                continue

        if total_available > 0:
            print(f"Found {total_available} available slot(s)!")
            send_sms(f"ODFW ALERT: Permit spot available! Book now: {URL}")
        else:
            print("No green slots found.")
            
        browser.close()

if __name__ == "__main__":
    check_calendar()
