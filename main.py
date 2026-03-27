import time
import logging
import random
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv('NAUKRI_EMAIL')
PASSWORD = os.getenv('NAUKRI_PASSWORD')
print(EMAIL, PASSWORD)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def human_delay(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))


def login_if_needed(page):
    logging.info("Checking login state...")
    page.goto("https://www.naukri.com", timeout=60000)
    page.wait_for_load_state("domcontentloaded")
    human_delay(2, 4)

    if page.locator("text=Sai Rahul Patha").count() > 0 or page.locator(".nI-gNb-logged-in-user").count() > 0:
        logging.info("Already logged in ✅")
        return

    logging.info("Not logged in. Opening login page...")
    login_link = page.locator("a:has-text('Login'), button:has-text('Login')").first
    if login_link.count() > 0:
        login_link.click()
        human_delay(2, 3)

    try:
        email_input = page.locator('input#usernameField, input[type="email"], input[placeholder*="email" i]').first
        email_input.wait_for(timeout=20000)
        email_input.fill(EMAIL)
        human_delay(1, 2)
        page.locator('input#passwordField, input[type="password"]').first.fill(PASSWORD)
        human_delay(1, 2)
        page.locator('button[type="submit"], button:has-text("Login")').first.click()
        logging.info("Waiting for login to complete...")
        time.sleep(10)
    except Exception as e:
        logging.error(f"Login failed: {e}")
        raise


def update_profile(page):
    logging.info("Navigating to profile page...")
    page.goto("https://www.naukri.com/mnjuser/profile", timeout=60000)
    page.wait_for_load_state("domcontentloaded")
    human_delay(3, 5)

    if "profile" not in page.url.lower():
        raise Exception("Failed to navigate to profile page")

    logging.info("Clicking pencil icon next to name...")
    clicked = False
    for selector in ["span.edit.icon", "h1:has-text('Sai Rahul Patha') + span", ".nameSection svg"]:
        try:
            loc = page.locator(selector).first
            if loc.count() > 0:
                loc.scroll_into_view_if_needed()
                loc.click()
                logging.info(f"Clicked pencil: {selector}")
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        page.evaluate("""
            () => {
                const nameEl = Array.from(document.querySelectorAll('h1,h2,.name'))
                    .find(el => el.innerText.includes('Sai Rahul Patha'));
                const parent = nameEl.closest('div,section') || nameEl.parentElement;
                parent.querySelector('svg,[class*="edit"],[class*="pencil"]').click();
            }
        """)
        logging.info("Clicked pencil via JS")

    logging.info("Waiting for resume headline form...")
    human_delay(2, 3)

    save_btn = page.locator('form[name="resumeHeadlineForm"] button[type="submit"]')
    save_btn.wait_for(state="visible", timeout=15000)
    logging.info("Save button found!")

    try:
        textarea = page.locator('textarea#resumeHeadlineTxt')
        if textarea.is_visible():
            current = textarea.input_value()
            textarea.fill(current + " ")
            human_delay(0.5, 1)
            textarea.fill(current)
            logging.info("Touched textarea to register change")
    except Exception:
        pass

    save_btn.click()
    human_delay(2, 3)
    page.screenshot(path="debug_after_save.png")
    logging.info("Profile updated successfully!")


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="user_data",
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        try:
            page.set_extra_http_headers({"accept-language": "en-US,en;q=0.9"})
            login_if_needed(page)
            update_profile(page)
        except Exception as e:
            logging.error(f"Error: {e}")
            try:
                page.screenshot(path="fatal.png")
            except:
                pass
            raise e
        finally:
            browser.close()


if __name__ == "__main__":
    run()