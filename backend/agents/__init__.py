"""
FinSynapse Agents Package
Modular agent components for the multi-agent financial decision engine.
"""

from .data_agent import get_stock_data
from .news_agent import get_news
from .sentiment_agent import analyze_sentiment
from .risk_agent import calculate_risk
from .simulation_agent import simulate_price_change

__all__ = [
    "get_stock_data",
    "get_news",
    "analyze_sentiment",
    "calculate_risk",
    "simulate_price_change",
]
