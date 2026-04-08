"""
Risk Agent – Calculates risk metrics from stock price data using numpy.
Returns: RiskResult (Pydantic model)
"""

import numpy as np
from models import StockData, RiskResult
import logging

logger = logging.getLogger(__name__)


def calculate_risk(stock: StockData) -> RiskResult:
    """
    Calculate risk metrics from historical price data.
    
    Args:
        stock: StockData with historical prices
    
    Returns:
        RiskResult: Structured risk assessment with volatility, drawdown, etc.
    """
    if len(stock.prices) < 3:
        return RiskResult(
            volatility=0.0,
            risk_level="Unknown",
            max_drawdown=0.0,
            sharpe_estimate=0.0,
            beta_estimate=1.0,
        )
    
    try:
        prices = np.array(stock.prices)
        
        # ── Daily Returns ──
        returns = np.diff(prices) / prices[:-1]
        
        # ── Annualized Volatility ──
        daily_vol = np.std(returns)
        annualized_vol = daily_vol * np.sqrt(252)  # 252 trading days
        volatility = round(annualized_vol * 100, 2)  # As percentage
        
        # ── Risk Level Classification ──
        if volatility < 15:
            risk_level = "Low"
        elif volatility < 25:
            risk_level = "Medium"
        elif volatility < 40:
            risk_level = "High"
        else:
            risk_level = "Very High"
        
        # ── Maximum Drawdown ──
        peak = np.maximum.accumulate(prices)
        drawdowns = (prices - peak) / peak
        max_drawdown = round(abs(np.min(drawdowns)) * 100, 2)
        
        # ── Simplified Sharpe Estimate ──
        # Using risk-free rate of ~4.5% (current US T-bill rate approximation)
        risk_free_daily = 0.045 / 252
        mean_return = np.mean(returns)
        sharpe = 0.0
        if daily_vol > 0:
            sharpe = round((mean_return - risk_free_daily) / daily_vol * np.sqrt(252), 2)
        
        # ── Beta Estimate (simplified: relative volatility) ──
        # Without a benchmark, estimate beta from return distribution
        skew = float(np.mean(((returns - np.mean(returns)) / (np.std(returns) + 1e-10)) ** 3))
        beta_estimate = round(1.0 + (volatility - 20) / 40, 2)  # Normalize around 1.0
        beta_estimate = max(0.0, min(3.0, beta_estimate))  # Clamp
        
        return RiskResult(
            volatility=volatility,
            risk_level=risk_level,
            max_drawdown=max_drawdown,
            sharpe_estimate=sharpe,
            beta_estimate=beta_estimate,
        )
    
    except Exception as e:
        logger.error(f"Risk Agent error: {e}")
        return RiskResult(
            volatility=0.0,
            risk_level="Unknown",
            max_drawdown=0.0,
            sharpe_estimate=0.0,
            beta_estimate=1.0,
        )
