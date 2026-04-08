"""
FinSynapse – Pydantic Models
All structured data models for the multi-agent financial decision engine.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─── Agent Input/Output Models ──────────────────────────────────────

class StockData(BaseModel):
    """Structured stock data returned by the Data Agent."""
    symbol: str = Field(..., description="Ticker symbol")
    current_price: float = Field(..., description="Current/latest price")
    previous_close: float = Field(0.0, description="Previous closing price")
    change_percent: float = Field(0.0, description="Percent change from previous close")
    prices: List[float] = Field(default_factory=list, description="Historical closing prices")
    volume: int = Field(0, description="Current volume")
    market_cap: str = Field("N/A", description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    company_name: str = Field("", description="Company name")
    currency: str = Field("USD", description="Currency")


class NewsItem(BaseModel):
    """A single news headline with metadata."""
    title: str
    source: str = ""
    url: str = ""
    published: str = ""
    sentiment_score: float = 0.0


class NewsData(BaseModel):
    """Structured news data returned by the News Agent."""
    symbol: str
    headlines: List[str] = Field(default_factory=list)
    items: List[NewsItem] = Field(default_factory=list)


class SentimentResult(BaseModel):
    """Structured sentiment analysis returned by the Sentiment Agent."""
    score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 (bearish) to 1 (bullish)")
    label: str = Field(..., description="Sentiment label: Bullish, Bearish, or Neutral")
    headline_scores: List[dict] = Field(default_factory=list, description="Individual headline scores")


class RiskResult(BaseModel):
    """Structured risk assessment returned by the Risk Agent."""
    volatility: float = Field(..., description="Annualized volatility")
    risk_level: str = Field(..., description="Risk level: Low, Medium, High, Very High")
    max_drawdown: float = Field(0.0, description="Maximum drawdown percentage")
    sharpe_estimate: float = Field(0.0, description="Estimated Sharpe ratio")
    beta_estimate: float = Field(0.0, description="Estimated beta")


# ─── Decision Engine Models ─────────────────────────────────────────

class SignalDetail(BaseModel):
    """Detail for a single signal source."""
    agent: str
    signal: str  # BUY, SELL, HOLD
    strength: float  # 0.0 to 1.0
    reasoning: str


class DecisionResult(BaseModel):
    """Final structured decision from the Decision Engine."""
    symbol: str
    decision: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    conflict: bool = Field(False, description="Whether signals conflict")
    explanation: str = Field("", description="Human-readable reasoning")
    signals: List[str] = Field(default_factory=list, description="Summary signal list")
    signal_details: List[SignalDetail] = Field(default_factory=list, description="Detailed signal breakdown")
    stock_data: Optional[StockData] = None
    sentiment: Optional[SentimentResult] = None
    risk: Optional[RiskResult] = None
    news: Optional[NewsData] = None


# ─── Memory / History Models ────────────────────────────────────────

class HistoryEntry(BaseModel):
    """A stored record of a past decision."""
    id: Optional[int] = None
    symbol: str
    decision: str
    confidence: float
    conflict: bool = False
    explanation: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── API Response Models ────────────────────────────────────────────

class ComparisonResult(BaseModel):
    """Side-by-side comparison of two stocks."""
    stock1: DecisionResult
    stock2: DecisionResult
    summary: str = ""
    recommendation: str = ""


class SimulationResult(BaseModel):
    """Result of a what-if simulation."""
    original: DecisionResult
    simulated: DecisionResult
    price_change_percent: float
    impact_summary: str = ""


class HistoryResponse(BaseModel):
    """Response for history endpoint."""
    symbol: str
    entries: List[HistoryEntry] = Field(default_factory=list)
    total: int = 0
