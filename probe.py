import re, json
from playwright.sync_api import sync_playwright
URL = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/SummaryDashboard?:embed=y&:isGuestRedirectFromVizportal=y"
bodies = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 1200})
    def on_resp(r):
        if "bootstrapSession" in r.url or "/sessions/" in r.url:
            try: bodies.append((r.url, r.text()))
            except Exception as e: bodies.append((r.url, "ERR " + str(e)))
    pg.on("response", on_resp)
    pg.goto(URL, wait_until="networkidle", timeout=120000)
    pg.wait_for_timeout(8000)
    txt = pg.inner_text("body")
    print("=== PAGE TEXT (first 3000 chars) ===")
    print(txt[:3000])
    print("\n=== has 'Domestic Cases' in text:", "Domestic Cases" in txt)
    for u, t in bodies:
        print("\n=== RESPONSE", u[:160], "len", len(t))
        for kw in ["Domestic Cases", "Total Animal Cases", "in domestic animals", "SummaryDashboard"]:
            i = t.find(kw); print(f"  {kw!r}: {i}", (t[max(0,i-150):i+250].replace("\n"," ") if i >= 0 else ""))
        names = sorted(set(re.findall(r'"worksheet"\s*:\s*"([^"]+)"', t)))
        print("  worksheet names:", names[:40])
    b.close()
