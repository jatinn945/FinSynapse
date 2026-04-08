"""
FinSynapse Extensions – New API endpoints added as a safe, modular router.
This file is imported by main.py via a single `app.include_router()` call.

It does NOT modify any existing pipeline logic.

New Endpoints:
  GET  /api/benchmark/{symbol}  — Compare stock vs benchmark index
  POST /api/chat                — Context-aware AI chat
  GET  /api/stocks              — Get expanded stock list
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from tools.benchmark import get_benchmark_data
from tools.chat import chat_with_context

logger = logging.getLogger("FinSynapse.Extensions")

# ── Router ──
router = APIRouter(prefix="/api", tags=["Extensions"])


# ═══════════════════════════════════════════════════════════════
# EXPANDED STOCK LIST
# ═══════════════════════════════════════════════════════════════

STOCK_LIST = {
    "US Stocks": [
        {"symbol": "AAPL", "name": "Apple Inc.", "category": "US"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "category": "US"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "category": "US"},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "category": "US"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "category": "US"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "category": "US"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "category": "US"},
        {"symbol": "AMD", "name": "Advanced Micro Devices", "category": "US"},
        {"symbol": "NFLX", "name": "Netflix Inc.", "category": "US"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "category": "US"},
    ],
    "Indian Stocks": [
        {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "category": "India"},
        {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "category": "India"},
        {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "category": "India"},
        {"symbol": "INFY.NS", "name": "Infosys", "category": "India"},
        {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "category": "India"},
        {"symbol": "SBIN.NS", "name": "State Bank of India", "category": "India"},
        {"symbol": "LT.NS", "name": "Larsen & Toubro", "category": "India"},
        {"symbol": "ITC.NS", "name": "ITC Ltd.", "category": "India"},
    ],
    "Indices": [
        {"symbol": "^NSEI", "name": "Nifty 50", "category": "Index"},
        {"symbol": "^NSEBANK", "name": "Nifty Bank", "category": "Index"},
        {"symbol": "^GSPC", "name": "S&P 500", "category": "Index"},
        {"symbol": "^IXIC", "name": "NASDAQ Composite", "category": "Index"},
    ],
}

BENCHMARK_OPTIONS = [
    {"symbol": "^NSEI", "name": "Nifty 50"},
    {"symbol": "^NSEBANK", "name": "Nifty Bank"},
    {"symbol": "^GSPC", "name": "S&P 500"},
    {"symbol": "^IXIC", "name": "NASDAQ Composite"},
]


# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    question: str
    symbol: Optional[str] = ""
    decision: Optional[str] = ""
    sentiment: Optional[str] = ""
    risk: Optional[str] = ""
    confidence: Optional[float] = 0.0
    stock_price: Optional[float] = 0.0


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/stocks")
async def get_stock_list():
    """Return the expanded list of supported stocks, indices, and benchmarks."""
    return {
        "stocks": STOCK_LIST,
        "benchmarks": BENCHMARK_OPTIONS,
        "total": sum(len(v) for v in STOCK_LIST.values()),
    }


@router.get("/benchmark/{symbol}")
async def benchmark_comparison(
    symbol: str,
    benchmark: str = Query(default="^NSEI", description="Benchmark index symbol"),
    period: str = Query(default="1mo", description="Data period"),
):
    """
    Compare a stock's performance against a benchmark index.

    Returns normalized price series, relative performance, and alpha.
    """
    try:
        logger.info(f"Benchmark: {symbol} vs {benchmark}")
        result = get_benchmark_data(symbol.upper(), benchmark, period)
        return result
    except Exception as e:
        logger.error(f"Benchmark failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Context-aware AI chat powered by Groq LLaMA.

    Uses the latest analysis outputs to provide intelligent answers.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        logger.info(f"Chat: {request.question[:80]}...")
        result = chat_with_context(
            question=request.question,
            decision=request.decision or "",
            sentiment=request.sentiment or "",
            risk=request.risk or "",
            symbol=request.symbol or "",
            confidence=request.confidence or 0.0,
            stock_price=request.stock_price or 0.0,
        )
        return result
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
