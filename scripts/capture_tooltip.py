import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
    page.wait_for_selector("h1")
    time.sleep(2)

    # Find the sector path and dispatch mouseover
    sector = page.locator("path.recharts-sector").first
    sector.dispatch_event("mouseover")
    sector.dispatch_event("mouseenter")
    time.sleep(1)
    page.screenshot(path="reports/screenshots/05_pie_chart_tooltip_hover.png")
    print("Dispatched mouseover to sector and saved screenshot!")
