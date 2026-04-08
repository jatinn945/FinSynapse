"""
Simulation Agent – Creates hypothetical price scenarios for what-if analysis.
Returns: StockData (Pydantic model with modified prices)
"""

from models import StockData
import logging

logger = logging.getLogger(__name__)


def simulate_price_change(stock: StockData, percent_change: float) -> StockData:
    """
    Simulate a price change by adjusting all prices by a percentage.
    
    This creates a hypothetical scenario where the stock moves by the
    given percentage, allowing the decision engine to re-evaluate.
    
    Args:
        stock: Original StockData
        percent_change: Percentage to adjust prices (e.g., 5.0 for +5%, -10.0 for -10%)
    
    Returns:
        StockData: New StockData with adjusted prices
    """
    try:
        factor = 1 + (percent_change / 100.0)
        
        # Adjust all prices
        simulated_prices = [round(p * factor, 2) for p in stock.prices]
        simulated_current = round(stock.current_price * factor, 2)
        
        # Recalculate change percentage
        new_change = stock.change_percent + percent_change
        
        return StockData(
            symbol=stock.symbol,
            current_price=simulated_current,
            previous_close=stock.previous_close,
            change_percent=round(new_change, 2),
            prices=simulated_prices,
            volume=stock.volume,
            market_cap=stock.market_cap,
            pe_ratio=stock.pe_ratio,
            company_name=stock.company_name + f" (Simulated {percent_change:+.1f}%)",
            currency=stock.currency,
        )
    
    except Exception as e:
        logger.error(f"Simulation Agent error: {e}")
        return stock
