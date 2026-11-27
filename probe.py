from tableauscraper import TableauScraper as TS
url = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/SummaryDashboard"
ts = TS(); ts.loads(url)
wb = ts.getWorkbook()
print("SHEETS:", [w.name for w in wb.worksheets])
for w in wb.worksheets:
    df = w.data
    print("\n=== SHEET:", repr(w.name), "rows", len(df), "cols", list(df.columns)[:12])
    print(df.head(8).to_string()[:1500])
