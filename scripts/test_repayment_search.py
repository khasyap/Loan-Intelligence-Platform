import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
    time.sleep(1)

    # Navigate to Amortization Tracker
    page.locator("button:has-text('Amortization Tracker')").click()
    time.sleep(1)

    # Verify initial schedule for LOAN-2026-005999
    input_box = page.locator("input[placeholder='e.g. LOAN-2026-000004']")
    input_box.fill("LOAN-2026-005999")
    page.locator("button:has-text('Search')").click()
    time.sleep(1.5)
    page.screenshot(path="reports/screenshots/06_repayment_005999_valid.png")
    print("1. Saved LOAN-2026-005999 valid schedule screenshot!")

    # Now search LOAN-2026-006000 (the rejected loan)
    input_box.fill("LOAN-2026-006000")
    page.locator("button:has-text('Search')").click()
    time.sleep(1.5)
    page.screenshot(path="reports/screenshots/07_repayment_006000_rejected_notice.png")
    print("2. Saved LOAN-2026-006000 rejected notice screenshot!")

    # Verify the notice text is visible
    notice_text = page.locator("text=REJECT").first.text_content()
    print(f"  Notice rendered: {notice_text}")

    # Now click the recovery button 'Load LOAN-2026-005999 (Approved)'
    page.locator("button:has-text('Load LOAN-2026-005999')").click()
    time.sleep(1.5)
    page.screenshot(path="reports/screenshots/08_repayment_recovered.png")
    print("3. Clicked recovery button and restored schedule!")

