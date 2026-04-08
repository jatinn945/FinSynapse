"""
Data Agent – Fetches stock market data using yfinance.
Returns: StockData (Pydantic model)
"""

import yfinance as yf
from models import StockData
import logging

logger = logging.getLogger(__name__)


def get_stock_data(symbol: str) -> StockData:
    """
    Fetch real-time stock data for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        StockData: Structured stock data with prices and metadata
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        
        # Get historical data (1 month of daily prices)
        hist = ticker.history(period="1mo")
        
        if hist.empty:
            raise ValueError(f"No data found for symbol: {symbol}")
        
        # Extract info
        info = ticker.info
        
        prices = hist["Close"].tolist()
        current_price = prices[-1] if prices else 0.0
        previous_close = info.get("previousClose", prices[-2] if len(prices) > 1 else current_price)
        
        change_percent = 0.0
        if previous_close and previous_close > 0:
            change_percent = round(((current_price - previous_close) / previous_close) * 100, 2)
        
        # Format market cap
        raw_cap = info.get("marketCap", 0)
        if raw_cap >= 1_000_000_000_000:
            market_cap = f"${raw_cap / 1_000_000_000_000:.2f}T"
        elif raw_cap >= 1_000_000_000:
            market_cap = f"${raw_cap / 1_000_000_000:.2f}B"
        elif raw_cap >= 1_000_000:
            market_cap = f"${raw_cap / 1_000_000:.2f}M"
        else:
            market_cap = "N/A"
        
        return StockData(
            symbol=symbol.upper(),
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            change_percent=change_percent,
            prices=[round(p, 2) for p in prices],
            volume=info.get("volume", 0) or 0,
            market_cap=market_cap,
            pe_ratio=info.get("trailingPE"),
            company_name=info.get("shortName", symbol.upper()),
            currency=info.get("currency", "USD"),
        )
    
    except Exception as e:
        logger.error(f"Data Agent error for {symbol}: {e}")
        # Return a minimal StockData with error indication
        return StockData(
            symbol=symbol.upper(),
            current_price=0.0,
            prices=[],
            company_name=f"{symbol.upper()} (data unavailable)",
        )
