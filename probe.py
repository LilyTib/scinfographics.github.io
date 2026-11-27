import json, re
from playwright.sync_api import sync_playwright
URL = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/SummaryDashboard?:embed=y&:isGuestRedirectFromVizportal=y"
boot = None
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    def on_resp(r):
        global boot
        if "bootstrapSession" in r.url:
            try: boot = r.text()
            except Exception: pass
    pg.on("response", on_resp)
    pg.goto(URL, wait_until="load", timeout=120000); pg.wait_for_timeout(15000); b.close()

# response = "<len>;<json><len>;<json>"
parts, i = [], 0
while i < len(boot):
    m = re.match(r"(\d+);", boot[i:]); n = int(m.group(1)); s = i + len(m.group(0))
    parts.append(json.loads(boot[s:s+n])); i = s + n
sec = parts[-1]["secondaryInfo"]["presModelMap"]
cols = sec["dataDictionary"]["presModelHolder"]["genDataDictionaryPresModel"]["dataSegments"]["0"]["dataColumns"]
dd = {c["dataType"]: c["dataValues"] for c in cols}
viz = sec["vizData"]["presModelHolder"]["genPresModelMapPresModel"]["presModelMap"]
def val(dtype, idx):
    if idx >= 0: return dd.get(dtype, [None]*(idx+1))[idx]
    return dd["cstring"][-idx-1]
for name, pm in viz.items():
    try:
        pcd = pm["presModelHolder"]["genVizDataPresModel"]["paneColumnsData"]
    except KeyError:
        continue
    print(f"\n=== {name}")
    for vc in pcd["vizDataColumns"]:
        cap = vc.get("fieldCaption")
        if not cap: continue
        for pi, ci in zip(vc["paneIndices"], vc["columnIndices"]):
            pc = pcd["paneColumnsList"][pi]["vizPaneColumns"][ci]
            idxs = pc.get("aliasIndices") or pc.get("valueIndices") or []
            vals = [val(vc["dataType"], k) for k in idxs[:12]]
            print(f"   {cap!r} [{vc['dataType']}] -> {vals}{' ...' if len(idxs) > 12 else ''}")
