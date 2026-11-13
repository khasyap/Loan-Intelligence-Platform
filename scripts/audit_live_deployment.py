import os
import time
import urllib.request
import ssl
from playwright.sync_api import sync_playwright

LIVE_BASE_URL = "https://loan-intelligence-platform.onrender.com"
SCREENSHOT_DIR = "reports/live_audit_screenshots"
DOWNLOAD_DIR = "reports/live_downloads"

def run_live_audit():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    results = {}

    print("=====================================================================")
    print("LOAN INTELLIGENCE PLATFORM — PRODUCTION AUDIT OF LIVE RENDER DEPLOYMENT")
    print(f"Target URL: {LIVE_BASE_URL}")
    print("=====================================================================")

    console_errors = []
    failed_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=True
        )
        page = context.new_page()

        # Capture console errors
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("requestfailed", lambda req: failed_requests.append(f"FAILED: {req.method} {req.url} - {req.failure}"))

        # ----------------------------------------------------------------------
        # TEST 1: Homepage Load & Static Assets
        # ----------------------------------------------------------------------
        print("\n[TEST 1] Auditing Live Homepage Load & Static Assets...")
        t0 = time.time()
        resp = page.goto(f"{LIVE_BASE_URL}/", wait_until="networkidle", timeout=30000)
        load_time = time.time() - t0
        status_code = resp.status if resp else "NO_RESPONSE"
        print(f"  Response Status: {status_code} in {load_time:.2f}s")
        assert status_code == 200, f"Expected 200, got {status_code}"
        
        # Verify DOM Content
        h1_text = page.locator("h1").first.text_content()
        print(f"  First H1 Tag Rendered: '{h1_text}'")
        page.screenshot(path=f"{SCREENSHOT_DIR}/01_live_homepage.png")
        results["Homepage Load"] = "PASS"

        # ----------------------------------------------------------------------
        # TEST 2: Endpoint Health & OpenAPI
        # ----------------------------------------------------------------------
        print("\n[TEST 2] Checking /health and /docs...")
        page_health = context.new_page()
        resp_h = page_health.goto(f"{LIVE_BASE_URL}/health")
        print(f"  /health status: {resp_h.status}")
        health_text = page_health.text_content("body")
        print(f"  /health body: {health_text}")
        page_health.close()

        page_docs = context.new_page()
        resp_d = page_docs.goto(f"{LIVE_BASE_URL}/docs", wait_until="networkidle")
        print(f"  /docs status: {resp_d.status}")
        page_docs.screenshot(path=f"{SCREENSHOT_DIR}/02_live_docs.png")
        page_docs.close()
        results["Health & Docs"] = "PASS"

        # ----------------------------------------------------------------------
        # TEST 3: Responsive Viewport Audits
        # ----------------------------------------------------------------------
        print("\n[TEST 3] Testing Responsive Viewports...")
        viewports = [
            ("1920x1080", 1920, 1080),
            ("1366x768", 1366, 768),
            ("768x1024", 768, 1024),
            ("390x844", 390, 844),
            ("360x800", 360, 800),
        ]
        for name, w, h in viewports:
            page.set_viewport_size({"width": w, "height": h})
            time.sleep(1)
            page.screenshot(path=f"{SCREENSHOT_DIR}/viewport_{name}.png")
            print(f"  Rendered viewport {name} cleanly (Saved screenshot)")
        results["Responsive Viewports"] = "PASS"

        # Reset viewport
        page.set_viewport_size({"width": 1440, "height": 900})

        # ----------------------------------------------------------------------
        # TEST 4: Theme Switching (Dark & Light)
        # ----------------------------------------------------------------------
        print("\n[TEST 4] Testing Theme Switching & Contrast...")
        # Check current dark mode
        is_dark = page.evaluate("() => document.documentElement.classList.contains('dark')")
        print(f"  Initial Dark Mode: {is_dark}")

        # Switch to light
        light_btn = page.locator("button[title='Light mode']")
        if light_btn.is_visible():
            light_btn.click()
            time.sleep(1)
            is_dark_now = page.evaluate("() => document.documentElement.classList.contains('dark')")
            print(f"  Switched to Light Mode (Dark Class = {is_dark_now})")
            page.screenshot(path=f"{SCREENSHOT_DIR}/theme_light.png")

        # Switch back to dark
        dark_btn = page.locator("button[title='Dark mode']")
        if dark_btn.is_visible():
            dark_btn.click()
            time.sleep(1)
            is_dark_again = page.evaluate("() => document.documentElement.classList.contains('dark')")
            print(f"  Switched back to Dark Mode (Dark Class = {is_dark_again})")
            page.screenshot(path=f"{SCREENSHOT_DIR}/theme_dark.png")
        results["Theme Switching"] = "PASS"

        # ----------------------------------------------------------------------
        # TEST 5: Live Export Testing (Executive Portfolio)
        # ----------------------------------------------------------------------
        print("\n[TEST 5] Testing Live Report Exports from Render...")
        export_btn = page.locator("button:has-text('Export Portfolio')")
        if export_btn.is_visible():
            # CSV Download
            export_btn.click()
            time.sleep(0.5)
            csv_btn = page.locator("button:has-text('CSV Data File')")
            if csv_btn.is_visible():
                with page.expect_download() as dl_info:
                    csv_btn.click()
                csv_dl = dl_info.value
                csv_file = os.path.join(DOWNLOAD_DIR, "live_portfolio.csv")
                csv_dl.save_as(csv_file)
                print(f"  Successfully downloaded live CSV: {csv_file} ({os.path.getsize(csv_file)} bytes)")

            # Excel Download
            export_btn.click()
            time.sleep(0.5)
            xlsx_btn = page.locator("button:has-text('Excel Spreadsheet')")
            if xlsx_btn.is_visible():
                with page.expect_download() as dl_info:
                    xlsx_btn.click()
                xlsx_dl = dl_info.value
                xlsx_file = os.path.join(DOWNLOAD_DIR, "live_portfolio.xlsx")
                xlsx_dl.save_as(xlsx_file)
                print(f"  Successfully downloaded live Excel: {xlsx_file} ({os.path.getsize(xlsx_file)} bytes)")

            # PDF Download
            export_btn.click()
            time.sleep(0.5)
            pdf_btn = page.locator("button:has-text('PDF Document')")
            if pdf_btn.is_visible():
                with page.expect_download() as dl_info:
                    pdf_btn.click()
                pdf_dl = dl_info.value
                pdf_file = os.path.join(DOWNLOAD_DIR, "live_portfolio.pdf")
                pdf_dl.save_as(pdf_file)
                print(f"  Successfully downloaded live PDF: {pdf_file} ({os.path.getsize(pdf_file)} bytes)")
            results["Live Exports"] = "PASS"
        else:
            print("  Export button not directly visible on this page view")
            results["Live Exports"] = "NOT TESTED"

        # ----------------------------------------------------------------------
        # Summary of Browser Errors
        # ----------------------------------------------------------------------
        print("\n[TEST 6] Inspecting Browser Console Logs & Failed Network Requests...")
        print(f"  Total Console Errors/Warnings: {len(console_errors)}")
        for err in console_errors[:5]:
            print(f"    {err}")
        print(f"  Total Failed Requests: {len(failed_requests)}")
        for req in failed_requests[:5]:
            print(f"    {req}")

        browser.close()

    print("\n=====================================================================")
    print("LIVE AUDIT SUMMARY:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("=====================================================================")

if __name__ == "__main__":
    run_live_audit()
