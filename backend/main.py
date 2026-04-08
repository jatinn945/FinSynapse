"""
FinSynapse – FastAPI Application
Multi-Agent Financial Decision Engine API
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging

from models import DecisionResult, SimulationResult, ComparisonResult, HistoryResponse
from orchestrator import Orchestrator
from memory import init_db, get_history, get_all_history

# ── Logging Setup ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinSynapse")

# ── Initialize Database ──
init_db()

# ── FastAPI App ──
app = FastAPI(
    title="FinSynapse",
    description="Multi-Agent Financial Decision Engine with structured reasoning",
    version="1.0.0",
)

# ── CORS Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount frontend static files ──
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ── Orchestrator Instance ──
orchestrator = Orchestrator()


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "FinSynapse API is running. Frontend not found."}


@app.get("/api/analyze/{symbol}", response_model=DecisionResult)
async def analyze_stock(symbol: str):
    """
    Run the full multi-agent analysis pipeline for a stock.
    
    Returns a structured DecisionResult with:
    - BUY/SELL/HOLD decision
    - Confidence score
    - Conflict detection
    - Signal breakdown
    - Full explanation
    """
    try:
        logger.info(f"API: /analyze/{symbol}")
        result = orchestrator.analyze(symbol.upper())
        return result
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/simulate/{symbol}", response_model=SimulationResult)
async def simulate_stock(
    symbol: str,
    change: float = Query(default=5.0, description="Price change percentage"),
):
    """
    Run a what-if simulation with a hypothetical price change.
    
    Returns comparison of original vs simulated analysis.
    """
    try:
        logger.info(f"API: /simulate/{symbol}?change={change}")
        result = orchestrator.simulate(symbol.upper(), change)
        return result
    except Exception as e:
        logger.error(f"Simulation failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare", response_model=ComparisonResult)
async def compare_stocks(
    stock1: str = Query(..., description="First stock symbol"),
    stock2: str = Query(..., description="Second stock symbol"),
):
    """
    Compare two stocks side by side.
    
    Returns analysis for both stocks with summary and recommendation.
    """
    try:
        logger.info(f"API: /compare?stock1={stock1}&stock2={stock2}")
        result = orchestrator.compare(stock1.upper(), stock2.upper())
        return result
    except Exception as e:
        logger.error(f"Comparison failed for {stock1} vs {stock2}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{symbol}", response_model=HistoryResponse)
async def get_stock_history(symbol: str):
    """
    Retrieve decision history for a specific stock.
    """
    try:
        entries = get_history(symbol.upper())
        return HistoryResponse(
            symbol=symbol.upper(),
            entries=entries,
            total=len(entries),
        )
    except Exception as e:
        logger.error(f"History retrieval failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history", response_model=HistoryResponse)
async def get_all_stock_history():
    """
    Retrieve all decision history across all stocks.
    """
    try:
        entries = get_all_history()
        return HistoryResponse(
            symbol="ALL",
            entries=entries,
            total=len(entries),
        )
    except Exception as e:
        logger.error(f"History retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "FinSynapse",
        "version": "1.0.0",
        "agents": [
            "Data Agent (yfinance)",
            "News Agent (RSS)",
            "Sentiment Agent (TextBlob)",
            "Risk Agent (numpy)",
            "Simulation Agent",
        ],
    }


# ── Extensions Router (safe addition – does not modify existing endpoints) ──
from extensions import router as extensions_router
app.include_router(extensions_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
