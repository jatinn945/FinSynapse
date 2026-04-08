"""
Benchmark Tool – Compares a stock's performance against a benchmark index.
Uses yfinance to fetch both stock and benchmark prices.

This is a NEW extension module. It does NOT modify any existing agent logic.
"""

import yfinance as yf
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_benchmark_data(
    symbol: str,
    benchmark: str = "^NSEI",
    period: str = "1mo",
) -> Dict[str, Any]:
    """
    Compare a stock's performance against a benchmark index.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')
        benchmark: Benchmark index symbol (default: ^NSEI — Nifty 50)
        period: Historical data period (default: '1mo')

    Returns:
        Dictionary with stock_prices, benchmark_prices, and relative_performance
    """
    try:
        # Fetch stock data
        stock_ticker = yf.Ticker(symbol.upper())
        stock_hist = stock_ticker.history(period=period)

        if stock_hist.empty:
            raise ValueError(f"No data found for symbol: {symbol}")

        stock_prices = stock_hist["Close"].tolist()
        stock_dates = [d.strftime("%Y-%m-%d") for d in stock_hist.index]

        # Fetch benchmark data
        bench_ticker = yf.Ticker(benchmark)
        bench_hist = bench_ticker.history(period=period)

        if bench_hist.empty:
            raise ValueError(f"No data found for benchmark: {benchmark}")

        bench_prices = bench_hist["Close"].tolist()
        bench_dates = [d.strftime("%Y-%m-%d") for d in bench_hist.index]

        # Calculate relative performance (normalized to starting price = 100)
        stock_normalized = _normalize(stock_prices)
        bench_normalized = _normalize(bench_prices)

        # Calculate returns
        stock_return = _total_return(stock_prices)
        bench_return = _total_return(bench_prices)
        alpha = round(stock_return - bench_return, 2)

        # Use overlapping dates for comparison
        min_len = min(len(stock_normalized), len(bench_normalized))
        relative_performance = [
            round(stock_normalized[i] - bench_normalized[i], 2)
            for i in range(min_len)
        ]

        # Get stock info for display
        stock_info = stock_ticker.info
        stock_name = stock_info.get("shortName", symbol.upper())

        bench_info = bench_ticker.info
        bench_name = bench_info.get("shortName", benchmark)

        return {
            "symbol": symbol.upper(),
            "benchmark": benchmark,
            "stock_name": stock_name,
            "benchmark_name": bench_name,
            "stock_prices": [round(p, 2) for p in stock_prices],
            "benchmark_prices": [round(p, 2) for p in bench_prices],
            "stock_normalized": [round(p, 2) for p in stock_normalized[:min_len]],
            "benchmark_normalized": [round(p, 2) for p in bench_normalized[:min_len]],
            "relative_performance": relative_performance,
            "dates": stock_dates[:min_len],
            "stock_return_pct": round(stock_return, 2),
            "benchmark_return_pct": round(bench_return, 2),
            "alpha": alpha,
            "outperforming": alpha > 0,
            "summary": _generate_summary(
                symbol.upper(), benchmark, stock_name, bench_name,
                stock_return, bench_return, alpha
            ),
        }

    except Exception as e:
        logger.error(f"Benchmark comparison error for {symbol} vs {benchmark}: {e}")
        return {
            "symbol": symbol.upper(),
            "benchmark": benchmark,
            "error": str(e),
            "stock_prices": [],
            "benchmark_prices": [],
            "stock_normalized": [],
            "benchmark_normalized": [],
            "relative_performance": [],
            "dates": [],
            "stock_return_pct": 0,
            "benchmark_return_pct": 0,
            "alpha": 0,
            "outperforming": False,
            "summary": f"Unable to compare {symbol} against {benchmark}: {e}",
        }


def _normalize(prices: List[float]) -> List[float]:
    """Normalize prices to start at 100 for fair comparison."""
    if not prices or prices[0] == 0:
        return [100.0] * len(prices)
    base = prices[0]
    return [(p / base) * 100 for p in prices]


def _total_return(prices: List[float]) -> float:
    """Calculate total return percentage."""
    if len(prices) < 2 or prices[0] == 0:
        return 0.0
    return ((prices[-1] - prices[0]) / prices[0]) * 100


def _generate_summary(
    symbol: str, benchmark: str,
    stock_name: str, bench_name: str,
    stock_return: float, bench_return: float,
    alpha: float,
) -> str:
    """Generate a human-readable benchmark comparison summary."""
    direction = "outperformed" if alpha > 0 else "underperformed"
    return (
        f"{stock_name} ({symbol}) {direction} {bench_name} ({benchmark}) "
        f"by {abs(alpha):.2f}% over the period. "
        f"Stock return: {stock_return:+.2f}%, Benchmark return: {bench_return:+.2f}%."
    )
