import urllib.request, json

def test_chat(question, symbol="", decision="", sentiment="", risk="", confidence=0, stock_price=0):
    req = urllib.request.Request(
        "http://localhost:8000/api/chat",
        data=json.dumps({
            "question": question,
            "symbol": symbol,
            "decision": decision,
            "sentiment": sentiment,
            "risk": risk,
            "confidence": confidence,
            "stock_price": stock_price,
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    r = urllib.request.urlopen(req, timeout=30)
    d = json.loads(r.read())
    print(f"Success: {d['success']} | Model: {d['model']}")
    print(f"Answer:\n{d['answer'][:400]}\n")
    return d

print("=" * 50)
print("Test 1: No context — greeting")
print("=" * 50)
test_chat("Hello!")

print("=" * 50)
print("Test 2: With context — should I buy?")
print("=" * 50)
test_chat("Should I buy this stock?", symbol="AAPL", decision="BUY", sentiment="Positive", risk="Moderate", confidence=72.5, stock_price=195.50)

print("=" * 50)
print("Test 3: Risk question with context")
print("=" * 50)
test_chat("How risky is this?", symbol="TSLA", decision="HOLD", sentiment="Neutral", risk="High", confidence=55.0, stock_price=180.25)
