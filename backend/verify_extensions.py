"""FinSynapse Extension Verification Script"""
import urllib.request
import json

def test(name, fn):
    try:
        result = fn()
        print(f"  [PASS] {name}: {result}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return False

print("=" * 55)
print("FinSynapse Extension Verification")
print("=" * 55)
passed = 0
total = 0

# Test 1: Stocks endpoint (NEW)
print("\n--- NEW Endpoints ---")
total += 1
if test("/api/stocks", lambda: (
    json.loads(urllib.request.urlopen("http://localhost:8000/api/stocks").read()),
    "OK"
)[-1]):
    r = json.loads(urllib.request.urlopen("http://localhost:8000/api/stocks").read())
    print(f"         Total stocks: {r['total']}")
    for k, v in r["stocks"].items():
        print(f"         {k}: {len(v)} items")
    passed += 1

# Test 2: Chat endpoint (NEW)
total += 1
req = urllib.request.Request(
    "http://localhost:8000/api/chat",
    data=json.dumps({"question": "What is a stock?", "symbol": "", "decision": "", "sentiment": "", "risk": ""}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    r = urllib.request.urlopen(req, timeout=30)
    d = json.loads(r.read())
    print(f"  [PASS] /api/chat: success={d.get('success')}, model={d.get('model')}")
    print(f"         Answer preview: {d.get('answer', '')[:80]}...")
    passed += 1
except Exception as e:
    print(f"  [FAIL] /api/chat: {e}")

# Test 3: Health (EXISTING - must still work)
print("\n--- EXISTING Endpoints ---")
total += 1
if test("/api/health", lambda: json.loads(urllib.request.urlopen("http://localhost:8000/api/health").read())["status"]):
    passed += 1

# Test 4: Frontend HTML checks
print("\n--- Frontend HTML Checks ---")
html = urllib.request.urlopen("http://localhost:8000/").read().decode()
checks = [
    ("Benchmark nav link", 'data-page="benchmark"'),
    ("AI Chat nav link", 'data-page="chat"'),
    ("Stock dropdown button", "stock-dropdown-toggle"),
    ("Benchmark page section", "page-benchmark"),
    ("Chat page section", "page-chat"),
    ("RELIANCE quick pick", "RELIANCE.NS"),
    ("TCS quick pick", "TCS.NS"),
    ("Dashboard (existing)", "page-dashboard"),
    ("Simulation (existing)", "page-simulation"),
    ("Comparison (existing)", "page-comparison"),
    ("Timeline (existing)", "page-timeline"),
]
for name, pattern in checks:
    total += 1
    if pattern in html:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name} — pattern not found")

print(f"\n{'=' * 55}")
print(f"Results: {passed}/{total} tests passed")
if passed == total:
    print("ALL TESTS PASSED — Extensions are safe and working!")
else:
    print(f"WARNING: {total - passed} test(s) failed")
print("=" * 55)
