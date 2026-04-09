"""
Data Agent – Fetches stock market data using yfinance.
Returns: StockData (Pydantic model)

Includes fallback mechanisms for cloud hosting environments
where yfinance Ticker.history() may fail silently.
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
    sym = symbol.upper()

    # ── Method 1: yf.Ticker.history() (works on localhost) ──
    try:
        logger.info(f"Data Agent: Trying Ticker.history() for {sym}")
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="1mo")

        if not hist.empty and len(hist) > 0:
            logger.info(f"Data Agent: Ticker.history() returned {len(hist)} rows for {sym}")
            return _build_stock_data(sym, hist, ticker)
        else:
            logger.warning(f"Data Agent: Ticker.history() returned empty for {sym}, trying fallback")
    except Exception as e:
        logger.warning(f"Data Agent: Ticker.history() failed for {sym}: {e}")

    # ── Method 2: yf.download() (different code path, often works on cloud) ──
    try:
        logger.info(f"Data Agent: Trying yf.download() for {sym}")
        hist = yf.download(sym, period="1mo", progress=False, auto_adjust=True)

        if not hist.empty and len(hist) > 0:
            logger.info(f"Data Agent: yf.download() returned {len(hist)} rows for {sym}")
            ticker = yf.Ticker(sym)
            return _build_stock_data(sym, hist, ticker)
        else:
            logger.warning(f"Data Agent: yf.download() also returned empty for {sym}")
    except Exception as e:
        logger.warning(f"Data Agent: yf.download() failed for {sym}: {e}")

    # ── Method 3: yf.download() with longer period ──
    try:
        logger.info(f"Data Agent: Trying yf.download() with 3mo period for {sym}")
        hist = yf.download(sym, period="3mo", progress=False, auto_adjust=True)

        if not hist.empty and len(hist) > 0:
            logger.info(f"Data Agent: 3mo download returned {len(hist)} rows for {sym}")
            ticker = yf.Ticker(sym)
            return _build_stock_data(sym, hist, ticker)
    except Exception as e:
        logger.warning(f"Data Agent: 3mo download failed for {sym}: {e}")

    # ── All methods failed ──
    logger.error(f"Data Agent: All methods failed for {sym}")
    return StockData(
        symbol=sym,
        current_price=0.0,
        prices=[],
        company_name=f"{sym} (data unavailable)",
    )


def _build_stock_data(symbol: str, hist, ticker) -> StockData:
    """Build a StockData object from history DataFrame and ticker info."""
    try:
        # Handle multi-level columns from yf.download()
        if hasattr(hist.columns, 'nlevels') and hist.columns.nlevels > 1:
            close_col = hist["Close"]
            if hasattr(close_col, 'columns'):
                close_col = close_col.iloc[:, 0]
            prices = close_col.dropna().tolist()
        else:
            prices = hist["Close"].dropna().tolist()

        # Filter out any remaining NaN/None values (yf.download on cloud can leak NaNs)
        import math
        prices = [p for p in prices if p is not None and not math.isnan(p)]

        if not prices:
            raise ValueError("No price data extracted")

        current_price = prices[-1]

        # Get info (safe — may fail on cloud but we already have prices)
        info = {}
        try:
            info = ticker.info or {}
        except Exception as e:
            logger.warning(f"Could not fetch ticker.info for {symbol}: {e}")

        previous_close = info.get("previousClose", prices[-2] if len(prices) > 1 else current_price)

        change_percent = 0.0
        if previous_close and previous_close > 0:
            change_percent = round(((current_price - previous_close) / previous_close) * 100, 2)

        # Format market cap
        raw_cap = info.get("marketCap", 0) or 0
        if raw_cap >= 1_000_000_000_000:
            market_cap = f"${raw_cap / 1_000_000_000_000:.2f}T"
        elif raw_cap >= 1_000_000_000:
            market_cap = f"${raw_cap / 1_000_000_000:.2f}B"
        elif raw_cap >= 1_000_000:
            market_cap = f"${raw_cap / 1_000_000:.2f}M"
        else:
            market_cap = "N/A"

        return StockData(
            symbol=symbol,
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            change_percent=change_percent,
            prices=[round(p, 2) for p in prices],
            volume=info.get("volume", 0) or 0,
            market_cap=market_cap,
            pe_ratio=info.get("trailingPE"),
            company_name=info.get("shortName", symbol),
            currency=info.get("currency", "USD"),
        )

    except Exception as e:
        logger.error(f"_build_stock_data error for {symbol}: {e}")
        return StockData(
            symbol=symbol,
            current_price=0.0,
            prices=[],
            company_name=f"{symbol} (data unavailable)",
        )
