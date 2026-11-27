import requests, re
from tableauscraper import TableauScraper as TS
base = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/SummaryDashboard"
variants = [base + "?:embed=y&:isGuestRedirectFromVizportal=y",
            base + "?:embed=y&:showVizHome=no&:isGuestRedirectFromVizportal=y",
            base + "?:showVizHome=no"]
for url in variants:
    r = requests.get(url, timeout=60)
    m = re.search(r'id="tsConfigContainer">(.{0,200})', r.text, re.S)
    print("\nURL:", url, "status", r.status_code, "len", len(r.text), "tsConfig:", (m.group(1)[:120] if m else None))
    try:
        ts = TS(); ts.loads(url)
        wb = ts.getWorkbook()
        print("SHEETS:", [w.name for w in wb.worksheets])
        for w in wb.worksheets:
            df = w.data
            print("\n=== SHEET:", repr(w.name), "rows", len(df), "cols", list(df.columns)[:12])
            print(df.head(6).to_string()[:1200])
        break
    except Exception as e:
        print("FAILED:", type(e).__name__, str(e)[:200])
