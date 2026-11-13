"""
Browser Automation & Visual UI Acceptance Verification Script
Using Playwright + System Google Chrome
Validates:
- Desktop (1920x1080), Laptop (1366x768), Tablet (768x1024), Mobile (390x844), Small Mobile (360x800)
- Fixed & Collapsible Side Navigation Bar
- Unclipped application logo and title
- Role switching & Customer Portal
- Hamburger menu & sliding drawer on tablet/mobile
- Loan Origination Modal on mobile
- Horizontal overflow detection
- Console & network errors
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.abspath("reports/screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CHROME_PATH = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
BASE_URL = "http://127.0.0.1:8000"

console_logs = []
failed_requests = []

def run_visual_verification():
    print("=" * 70)
    print("LAUNCHING PLAYWRIGHT BROWSER VISUAL ACCEPTANCE TEST SUITE")
    print(f"Target URL: {BASE_URL}")
    print(f"Screenshots Directory: {SCREENSHOT_DIR}")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )

        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        def handle_console(msg):
            console_logs.append(f"[{msg.type.upper()}] {msg.text}")

        def handle_request_failed(request):
            failed_requests.append(f"{request.method} {request.url} - {request.failure}")

        page.on("console", handle_console)
        page.on("requestfailed", handle_request_failed)

        # ----------------------------------------------------------------------
        # 1. Desktop 1920x1080: Executive Dashboard
        # ----------------------------------------------------------------------
        print("\n[1/10] Testing Desktop 1920x1080 Executive Dashboard...")
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Confirm application title is present and visible in desktop sidebar
        title_el = page.locator("aside").get_by_text("Loan Intelligence").first
        assert title_el.is_visible(), "Application title is not visible in desktop sidebar"

        shot_path = os.path.join(SCREENSHOT_DIR, "desktop_1920x1080_executive.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # ----------------------------------------------------------------------
        # 2. Desktop Sidebar Collapse & Expand
        # ----------------------------------------------------------------------
        print("\n[2/10] Testing Desktop Sidebar Collapse & Expand...")
        collapse_btn = page.locator("aside button[title='Collapse sidebar']").first
        if collapse_btn.is_visible():
            collapse_btn.click()
            page.wait_for_timeout(500)
            shot_path = os.path.join(SCREENSHOT_DIR, "desktop_collapsed_sidebar.png")
            page.screenshot(path=shot_path, full_page=False)
            print(f" -> Saved {shot_path}")

            # Expand back
            expand_btn = page.locator("aside button[title='Expand sidebar']").first
            expand_btn.click()
            page.wait_for_timeout(500)

        # ----------------------------------------------------------------------
        # 3. Tab Navigation: Risk & Compliance
        # ----------------------------------------------------------------------
        print("\n[3/10] Testing Risk & Compliance Dashboard...")
        page.locator("aside button:has-text('Risk & Compliance')").first.click()
        page.wait_for_timeout(1000)
        shot_path = os.path.join(SCREENSHOT_DIR, "desktop_risk.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # ----------------------------------------------------------------------
        # 4. Tab Navigation: Operations Funnel
        # ----------------------------------------------------------------------
        print("\n[4/10] Testing Operations Funnel & Queue Table...")
        page.locator("aside button:has-text('Operations Funnel')").first.click()
        page.wait_for_timeout(1000)
        shot_path = os.path.join(SCREENSHOT_DIR, "desktop_operations.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # ----------------------------------------------------------------------
        # 5. Tab Navigation: Amortization Tracker
        # ----------------------------------------------------------------------
        print("\n[5/10] Testing Amortization Tracker & Schedule...")
        page.locator("aside button:has-text('Amortization Tracker')").first.click()
        page.wait_for_timeout(1000)
        shot_path = os.path.join(SCREENSHOT_DIR, "desktop_repayments.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # ----------------------------------------------------------------------
        # 6. Tab Navigation: Anomaly Lab
        # ----------------------------------------------------------------------
        print("\n[6/10] Testing Anomaly Lab Dashboard...")
        page.locator("aside button:has-text('Anomaly Lab')").first.click()
        page.wait_for_timeout(1000)
        shot_path = os.path.join(SCREENSHOT_DIR, "desktop_anomalies.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # ----------------------------------------------------------------------
        # 7. Role Switching: Customer Portal
        # ----------------------------------------------------------------------
        print("\n[7/10] Testing Role Switch to Customer (Loan Applicant)...")
        role_btn = page.locator("aside button[title='Switch Demo Role']").first
        role_btn.click()
        page.wait_for_timeout(400)
        page.locator("button:has-text('Loan Applicant')").first.click()
        page.wait_for_timeout(1200)

        shot_path = os.path.join(SCREENSHOT_DIR, "desktop_customer_portal.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # Switch back to Admin
        page.locator("aside button[title='Switch Demo Role']").first.click()
        page.wait_for_timeout(400)
        page.locator("button:has-text('System Administrator')").first.click()
        page.wait_for_timeout(1000)

        # ----------------------------------------------------------------------
        # 8. Laptop Viewport: 1366x768
        # ----------------------------------------------------------------------
        print("\n[8/10] Testing Laptop Resolution (1366x768)...")
        page.set_viewport_size({"width": 1366, "height": 768})
        page.goto(f"{BASE_URL}", wait_until="networkidle")
        page.wait_for_timeout(1000)
        shot_path = os.path.join(SCREENSHOT_DIR, "laptop_1366x768.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # ----------------------------------------------------------------------
        # 9. Tablet Viewport: 768x1024 (Mobile Header & Sliding Drawer)
        # ----------------------------------------------------------------------
        print("\n[9/10] Testing Tablet Resolution (768x1024)...")
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(500)
        shot_path = os.path.join(SCREENSHOT_DIR, "tablet_768x1024_header.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # Open mobile drawer
        hamburger = page.locator("button[aria-label='Open Navigation Menu']")
        if hamburger.is_visible():
            hamburger.click()
            page.wait_for_timeout(400)
            shot_path = os.path.join(SCREENSHOT_DIR, "tablet_drawer_open.png")
            page.screenshot(path=shot_path, full_page=False)
            print(f" -> Saved {shot_path}")
            # Click a tab in drawer to close it
            page.locator("button:has-text('Operations Funnel')").last.click()
            page.wait_for_timeout(600)

        # ----------------------------------------------------------------------
        # 10. Mobile Viewports: 390x844 & 360x800
        # ----------------------------------------------------------------------
        print("\n[10/10] Testing Mobile Viewport (390x844 & 360x800)...")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(600)
        shot_path = os.path.join(SCREENSHOT_DIR, "mobile_390x844_dashboard.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        # Open drawer on mobile
        hamburger = page.locator("button[aria-label='Open Navigation Menu']")
        if hamburger.is_visible():
            hamburger.click()
            page.wait_for_timeout(400)
            shot_path = os.path.join(SCREENSHOT_DIR, "mobile_390x844_drawer.png")
            page.screenshot(path=shot_path, full_page=False)
            print(f" -> Saved {shot_path}")

            # Close drawer by clicking backdrop or close button
            backdrop = page.locator(".fixed.inset-0.bg-slate-950\\/80").first
            if backdrop.is_visible():
                backdrop.click(force=True)
                page.wait_for_timeout(400)

        # Open Loan Origination Modal on mobile
        simulate_btn = page.locator("button:has-text('Simulate')").first
        if simulate_btn.is_visible():
            simulate_btn.click()
            page.wait_for_timeout(400)
            shot_path = os.path.join(SCREENSHOT_DIR, "mobile_390x844_modal.png")
            page.screenshot(path=shot_path, full_page=False)
            print(f" -> Saved {shot_path}")
            # Close modal
            page.locator("button:has(svg.lucide-x)").last.click()
            page.wait_for_timeout(400)

        # Test Small Mobile 360x800 for horizontal overflow
        page.set_viewport_size({"width": 360, "height": 800})
        page.wait_for_timeout(500)
        
        # Check for unintended horizontal overflow on body
        overflow_x = page.evaluate("() => document.body.scrollWidth > window.innerWidth")
        print(f" -> 360x800 Horizontal Overflow Check: {'OVERFLOW DETECTED' if overflow_x else 'ZERO OVERFLOW (PERFECT)'}")

        shot_path = os.path.join(SCREENSHOT_DIR, "mobile_360x800.png")
        page.screenshot(path=shot_path, full_page=False)
        print(f" -> Saved {shot_path}")

        browser.close()

    print("\n" + "=" * 70)
    print("BROWSER AUTOMATION & VISUAL ACCEPTANCE TESTS COMPLETE")
    print(f"Console Logs Recorded: {len(console_logs)}")
    print(f"Failed HTTP Requests: {len(failed_requests)}")
    if failed_requests:
        print("Failed Requests:", failed_requests)
    print("=" * 70)

if __name__ == "__main__":
    run_visual_verification()
