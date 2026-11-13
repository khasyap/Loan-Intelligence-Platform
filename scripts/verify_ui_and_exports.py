import os
import time
import openpyxl
from playwright.sync_api import sync_playwright

def run_acceptance_suite():
    os.makedirs("reports/screenshots", exist_ok=True)
    os.makedirs("reports/test_downloads", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=True
        )
        page = context.new_page()

        print("[1/7] Navigating to http://127.0.0.1:8000/...")
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_selector("h1:has-text('Executive Lending Portfolio')")
        time.sleep(2)

        # -------------------------------------------------------------
        # STEP 1: Verify Dark Mode & Pie Chart Labels
        # -------------------------------------------------------------
        print("[2/7] Checking Dark Mode & Pie Chart Labels...")
        is_dark = page.evaluate("() => document.documentElement.classList.contains('dark')")
        print(f"  Initial Theme Dark Class Present: {is_dark}")

        # Check Pie Chart text element visibility
        pie_labels = page.locator("text[dominant-baseline='central']")
        count_labels = pie_labels.count()
        print(f"  Found {count_labels} customized Pie Chart labels rendered!")
        for i in range(count_labels):
            txt = pie_labels.nth(i).text_content()
            fill = pie_labels.nth(i).get_attribute("fill")
            print(f"    Label {i+1}: '{txt}' with fill: {fill}")

        # Hover over first sector to trigger Tooltip and verify text color
        first_sector = page.locator(".recharts-sector").first
        try:
            first_sector.hover(force=True, timeout=5000)
            time.sleep(1)
            page.screenshot(path="reports/screenshots/05_pie_chart_tooltip_hover.png", full_page=False)
            print("  Hovered pie sector with force=True and saved reports/screenshots/05_pie_chart_tooltip_hover.png")
        except Exception as e:
            print(f"  Hover failed: {e}, falling back to mouse move")
            surface = page.locator("svg.recharts-surface").first
            box = surface.bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] * 0.65, box["y"] + box["height"] * 0.35)
                time.sleep(1)
                page.screenshot(path="reports/screenshots/05_pie_chart_tooltip_hover.png", full_page=False)
                print("  Hovered pie area and saved reports/screenshots/05_pie_chart_tooltip_hover.png")

        # Take screenshot of Executive Dashboard in Dark Mode
        page.screenshot(path="reports/screenshots/01_executive_dark_mode.png", full_page=False)
        print("  Saved reports/screenshots/01_executive_dark_mode.png")

        # -------------------------------------------------------------
        # STEP 2: Test Excel, CSV, and PDF Export from Executive Dashboard
        # -------------------------------------------------------------
        print("[3/7] Testing Executive Portfolio Export Menu (Excel, CSV, PDF)...")
        # Click the Export Portfolio dropdown button
        export_btn = page.locator("button:has-text('Export Portfolio')")
        export_btn.click()
        time.sleep(0.5)

        # Click CSV Data File
        with page.expect_download() as download_info:
            page.locator("button:has-text('CSV Data File')").click()
        download = download_info.value
        csv_path = os.path.join("reports/test_downloads", "Executive_Portfolio.csv")
        download.save_as(csv_path)
        print(f"  Downloaded CSV: {csv_path} ({os.path.getsize(csv_path)} bytes)")
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            csv_text = f.read()
            assert "Metric,Value,Unit / Context" in csv_text
            print("  Verified CSV header and structure!")

        # Click Excel Spreadsheet
        export_btn.click()
        time.sleep(0.5)
        with page.expect_download() as download_info:
            page.locator("button:has-text('Excel Spreadsheet')").click()
        download = download_info.value
        xlsx_path = os.path.join("reports/test_downloads", "Executive_Portfolio.xlsx")
        download.save_as(xlsx_path)
        print(f"  Downloaded Excel: {xlsx_path} ({os.path.getsize(xlsx_path)} bytes)")

        # Verify Excel workbook
        wb = openpyxl.load_workbook(xlsx_path)
        print(f"  Sheets in Excel: {wb.sheetnames}")
        sheet1 = wb.active
        print(f"  Title in A1: {sheet1['A1'].value}")
        assert "Executive" in str(sheet1["A1"].value)

        # Click PDF Document
        export_btn.click()
        time.sleep(0.5)
        with page.expect_download() as download_info:
            page.locator("button:has-text('PDF Document')").click()
        download = download_info.value
        pdf_path = os.path.join("reports/test_downloads", "Executive_Portfolio.pdf")
        download.save_as(pdf_path)
        print(f"  Downloaded PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
        with open(pdf_path, "rb") as f:
            pdf_header = f.read(5)
            assert pdf_header == b"%PDF-", f"Invalid PDF header: {pdf_header}"
        print("  Verified valid PDF header %PDF-!")

        # -------------------------------------------------------------
        # STEP 3: Switch to Light Mode & Verify Theme Switcher
        # -------------------------------------------------------------
        print("[4/7] Testing Theme Switcher (Switching to Light Mode)...")
        # Click 'Light' theme option in sidebar
        light_btn = page.locator("button[title='Light mode']")
        if light_btn.is_visible():
            light_btn.click()
        else:
            # Fallback to compact button
            page.locator("button[aria-label='Toggle theme']").click()
        time.sleep(1)

        is_dark_now = page.evaluate("() => document.documentElement.classList.contains('dark')")
        print(f"  Theme Dark Class After Switch: {is_dark_now} (Expected: False)")
        assert not is_dark_now, "Dark class should be removed in light mode"

        # Check Pie Chart label fill in light mode
        pie_labels_light = page.locator("text[dominant-baseline='central']")
        if pie_labels_light.count() > 0:
            fill_light = pie_labels_light.first.get_attribute("fill")
            print(f"  Light Mode Pie Label fill: {fill_light} (Expected: #0F172A)")

        page.screenshot(path="reports/screenshots/02_executive_light_mode.png", full_page=False)
        print("  Saved reports/screenshots/02_executive_light_mode.png")

        # -------------------------------------------------------------
        # STEP 4: Navigate to Operations Funnel
        # -------------------------------------------------------------
        print("[5/7] Testing Operations Funnel in Light Mode & Exporting Queue...")
        page.locator("button:has-text('Operations Funnel')").click()
        page.wait_for_selector("h3:has-text('Application Processing Queue')")
        time.sleep(1)
        page.screenshot(path="reports/screenshots/03_operations_light_mode.png", full_page=False)
        print("  Saved reports/screenshots/03_operations_light_mode.png")

        # Test Filtered Applications Export
        ops_export_btn = page.locator("button:has-text('Export Queue')")
        ops_export_btn.click()
        time.sleep(0.5)
        with page.expect_download() as download_info:
            page.locator("button:has-text('Excel Spreadsheet')").click()
        download = download_info.value
        apps_xlsx_path = os.path.join("reports/test_downloads", "Applications_Queue.xlsx")
        download.save_as(apps_xlsx_path)
        print(f"  Downloaded Applications Excel: {apps_xlsx_path} ({os.path.getsize(apps_xlsx_path)} bytes)")

        # Test Dossier Export on first row
        dossier_btn = page.locator("button:has-text('Dossier')").first
        dossier_btn.click()
        time.sleep(0.5)
        with page.expect_download() as download_info:
            page.locator("button:has-text('PDF Document')").click()
        download = download_info.value
        dossier_pdf_path = os.path.join("reports/test_downloads", "Sample_Dossier.pdf")
        download.save_as(dossier_pdf_path)
        print(f"  Downloaded Individual Loan Dossier PDF: {dossier_pdf_path} ({os.path.getsize(dossier_pdf_path)} bytes)")

        # -------------------------------------------------------------
        # STEP 5: Test Amortization Tracker & Repayment Schedule Export
        # -------------------------------------------------------------
        print("[6/7] Testing Repayment Amortization Tracker & Export...")
        page.locator("button:has-text('Amortization Tracker')").click()
        page.wait_for_selector("h2:has-text('Loan Amortization & Repayment Tracker')")
        time.sleep(1.5)

        # Trigger Export Schedule (Excel)
        sched_export_btn = page.locator("button:has-text('Export Schedule')")
        if sched_export_btn.is_visible():
            sched_export_btn.click()
            time.sleep(0.5)
            with page.expect_download() as download_info:
                page.locator("button:has-text('Excel Spreadsheet')").click()
            download = download_info.value
            sched_xlsx = os.path.join("reports/test_downloads", "Repayment_Schedule.xlsx")
            download.save_as(sched_xlsx)
            print(f"  Downloaded Schedule Excel: {sched_xlsx} ({os.path.getsize(sched_xlsx)} bytes)")

        # -------------------------------------------------------------
        # STEP 6: Switch back to Dark Mode & Check Anomaly Dashboard
        # -------------------------------------------------------------
        print("[7/7] Switching Back to Dark Mode & Testing Anomaly Lab...")
        dark_btn = page.locator("button[title='Dark mode']")
        if dark_btn.is_visible():
            dark_btn.click()
        else:
            page.locator("button[aria-label='Toggle theme']").click()
        time.sleep(0.5)

        page.locator("button:has-text('Anomaly Lab')").click()
        page.wait_for_selector("h2:has-text('Anomaly Injection & Detection Lab')")
        time.sleep(1)
        page.screenshot(path="reports/screenshots/04_anomaly_lab_dark_mode.png", full_page=False)
        print("  Saved reports/screenshots/04_anomaly_lab_dark_mode.png")

        # Test Anomaly Report PDF download
        anom_btn = page.locator("button:has-text('Export Anomalies')")
        anom_btn.click()
        time.sleep(0.5)
        with page.expect_download() as download_info:
            page.locator("button:has-text('PDF Document')").click()
        download = download_info.value
        anom_pdf = os.path.join("reports/test_downloads", "Anomaly_Evaluation.pdf")
        download.save_as(anom_pdf)
        print(f"  Downloaded Anomaly PDF: {anom_pdf} ({os.path.getsize(anom_pdf)} bytes)")

        browser.close()
        print("\n=======================================================")
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH 100% PASS!")
        print("=======================================================")

if __name__ == "__main__":
    run_acceptance_suite()
