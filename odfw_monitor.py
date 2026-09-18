import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

URL = "https://myodfw.com/reserve-your-hunt?feedback_url=https%3A%2F%2Fmyodfw.com%2Freserve-your-hunt&ppp_mode=resource_list"
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASS = os.environ.get('GMAIL_APP_PASS')
TO_SMS_EMAIL = os.environ.get('TO_SMS_EMAIL')
STATE_FILE = "last_state.txt"

def send_sms(body):
    msg = MIMEText(body)
    msg["Subject"] = "ODFW Alert"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_SMS_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.send_message(msg)

def get_last_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""

def save_current_state(state_str):
    with open(STATE_FILE, "w") as f:
        f.write(state_str)

def check_calendar():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Use domcontentloaded to prevent hanging on slow background elements
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(7000) 

            found_slots = []

            for frame in page.frames:
                try:
                    slots = frame.locator("td.available").all()
                    for slot in slots:
                        identifier = slot.get_attribute("onclick") or slot.get_attribute("title") or "available"
                        found_slots.append(identifier)
                except Exception:
                    continue

            found_slots.sort()
            current_state_str = ",".join(found_slots)
            last_state_str = get_last_state()

            if current_state_str != last_state_str:
                if len(found_slots) > 0:
                    print(f"Change detected! Found {len(found_slots)} slot(s). Sending alert...")
                    send_sms(f"ODFW ALERT: Permit spot available ({len(found_slots)} spot(s))! Book now: {URL}")
                else:
                    print("All slots taken. State reset to 0.")
                
                save_current_state(current_state_str)
            else:
                print("No changes detected since last check. Skipping text alert.")

        except Exception as e:
            print(f"Temporary page load error: {e}")
            # Ensure last_state.txt exists even if page fails to load
            if not os.path.exists(STATE_FILE):
                save_current_state("")
        finally:
            browser.close()

if __name__ == "__main__":
    check_calendar()
