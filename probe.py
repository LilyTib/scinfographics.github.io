import json, re, requests
WB = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/"
print("=== A: per-sheet CSV")
for name in ["Summary", "Summary2", "Summary(2)", "Summary-TotalCases", "SummaryTotalCases", "ExportToCSV", "Table", "Textdescription", "TextDescription", "Header"]:
    try:
        r = requests.get(WB + name + ".csv", timeout=60)
        print(f"  {name}.csv -> {r.status_code} {r.headers.get('content-type','')[:30]} | {r.text[:220]!r}")
    except Exception as e:
        print(f"  {name}.csv -> ERR {e}")

print("\n=== B: client-side render")
from playwright.sync_api import sync_playwright
boot = None
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    def on_resp(r):
        global boot
        if "bootstrapSession" in r.url:
            try: boot = r.text()
            except Exception: pass
    pg.on("response", on_resp)
    pg.goto(WB + "SummaryDashboard?:embed=y&:isGuestRedirectFromVizportal=y&:render=true", wait_until="load", timeout=120000)
    pg.wait_for_timeout(15000); b.close()
print("renderMode:", re.findall(r'"renderMode":\s*"([^"]+)"', boot or "")[:2], "has dataSegments:", "dataSegments" in (boot or ""), "len", len(boot or ""))
for kw in ["178", "\"Domestic Cases\""]:
    print(kw, [m.start() for m in re.finditer(re.escape(kw), boot or "")][:5])
