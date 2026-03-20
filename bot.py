# !/usr/bin/env python3
"""
Roommatch.nl Selenium Auto-Apply Script
Opens Chrome, logs in, and clicks the React button on a room.

Usage:
    python roommatch_selenium.py <dwelling_id>

Example:
    python roommatch_selenium.py 124885

Requirements:
    pip install selenium webdriver-manager
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ============================================
# CONFIGURATION - SET VIA ENVIRONMENT VARIABLES
# ============================================
USERNAME = os.environ.get("ROOMMATCH_USERNAME", "")
PASSWORD = os.environ.get("ROOMMATCH_PASSWORD", "")


# ============================================


def apply_to_room(dwelling_id):
    """Open Chrome, log in, and apply to a room"""

    print("=" * 60)
    print("Roommatch Selenium Auto-Apply")
    print("=" * 60)
    print(f"\n🎯 Target room: {dwelling_id}")

    # Setup Chrome
    print("\n[1] Starting Chrome...")

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run without visible browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    except Exception as e:
        print(f"    ✗ Failed to start Chrome: {e}")
        print("\n    Make sure you have Chrome installed and run:")
        print("    pip install selenium webdriver-manager")
        return False

    wait = WebDriverWait(driver, 30)

    try:
        # Step 1: Go to login page
        print("\n[2] Going to login page...")
        driver.get("https://www.roommatch.nl/portal/sso/frontend/start")
        time.sleep(1)

        # Step 2: Enter username
        print("\n[3] Entering username...")
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "loginName"))
        )
        username_field.clear()
        username_field.send_keys(USERNAME)
        print(f"    ✓ Entered username: {USERNAME}")

        # Step 3: Click Next button
        print("\n[4] Clicking Next...")
        next_button = wait.until(
            EC.element_to_be_clickable((By.ID, "submit-button"))
        )
        next_button.click()
        time.sleep(1)

        # Step 4: Enter password
        print("\n[5] Entering password...")
        password_field = wait.until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_field.clear()
        password_field.send_keys(PASSWORD)
        print("    ✓ Entered password: ********")

        # Step 5: Click Next button (login)
        print("\n[6] Clicking Next to login...")
        next_button = wait.until(
            EC.element_to_be_clickable((By.ID, "submit-button"))
        )
        next_button.click()

        # Wait for redirect to complete
        print("    → Waiting for login to complete...")
        time.sleep(4)

        # Check if we're logged in
        if "roommatch.nl" in driver.current_url:
            print("    ✓ Login successful!")
        else:
            print(f"    ⚠ Current URL: {driver.current_url}")

        # Step 6: Navigate to room details page
        print(f"\n[7] Going to room {dwelling_id}...")
        room_url = f"https://www.roommatch.nl/aanbod/studentenwoningen/details/{dwelling_id}"
        driver.get(room_url)
        time.sleep(2)

        print(f"    → Current URL: {driver.current_url}")

        # Step 7: Find the React button
        print("\n[8] Looking for React button...")

        react_button = None
        selectors = [
            (By.CSS_SELECTOR, "input.reageer-button[value='Reageer']"),
            (By.CSS_SELECTOR, "input[type='submit'].reageer-button"),
            (By.CSS_SELECTOR, ".reageer-button"),
            (By.XPATH, "//input[@value='Reageer']"),
            (By.XPATH, "//button[contains(text(), 'Reageer')]"),
        ]

        for selector_type, selector in selectors:
            try:
                react_button = wait.until(
                    EC.presence_of_element_located((selector_type, selector))
                )
                print(f"    ✓ Found button with: {selector}")
                break
            except:
                continue

        if not react_button:
            print("    ✗ Could not find React button!")
            driver.save_screenshot("debug_screenshot.png")
            print("    → Saved: debug_screenshot.png")
            return False

        # Step 8: Scroll to the button
        print("\n[9] Scrolling to React button...")

        # Scroll the element into view (centered)
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            react_button
        )
        time.sleep(1)

        # Double-check it's visible
        location = react_button.location
        print(f"    → Button location: x={location['x']}, y={location['y']}")

        # Step 9: Click the React button using JavaScript (more reliable)
        print("\n[10] Clicking React button...")

        # Try JavaScript click first (bypasses overlay issues)
        try:
            driver.execute_script("arguments[0].click();", react_button)
            print("    ✓ Clicked via JavaScript")
        except Exception as js_error:
            print(f"    ⚠ JS click failed: {js_error}")
            # Fallback to regular click
            react_button.click()
            print("    ✓ Clicked via Selenium")

        time.sleep(3)

        print("\n" + "=" * 60)
        print("✅ SUCCESS! Application submitted!")
        print("=" * 60)
        print("\n🎉 Check 'Mijn reacties' on Roommatch to verify")

        # Keep browser open for a moment to see result
        time.sleep(5)

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

        try:
            driver.save_screenshot("error_screenshot.png")
            print("    → Saved error screenshot: error_screenshot.png")
        except:
            pass

        return False

    finally:
        print("\n[11] Closing browser...")
        driver.quit()


def main():
    if len(sys.argv) < 2:
        url_id = input("\nURL ID: ").strip()
    else:
        url_id = sys.argv[1]

    if not USERNAME or not PASSWORD:
        print("=" * 60)
        print("⚠️  SETUP REQUIRED")
        print("=" * 60)
        print("\nPlease set your credentials as environment variables:")
        print("  export ROOMMATCH_USERNAME='your_username'")
        print("  export ROOMMATCH_PASSWORD='your_password'")
        print("\nOr create a .env file (see .env.example)")
        sys.exit(1)

    success = apply_to_room(url_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()