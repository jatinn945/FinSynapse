"""
Decision Engine – Core intelligence of FinSynapse.
Combines signals from multiple agents, detects conflicts,
calculates confidence, and produces explainable BUY/SELL/HOLD decisions.
"""

from models import (
    StockData,
    SentimentResult,
    RiskResult,
    DecisionResult,
    SignalDetail,
)
import logging

logger = logging.getLogger(__name__)


def make_decision(
    stock: StockData,
    sentiment: SentimentResult,
    risk: RiskResult,
) -> DecisionResult:
    """
    Core decision engine that combines all agent signals into a final decision.
    
    Process:
    1. Convert each agent's output into a directional signal (BUY/SELL/HOLD)
    2. Assign strength to each signal
    3. Detect conflicts between signals
    4. Compute weighted confidence
    5. Generate structured explanation
    
    Args:
        stock: Stock price data from Data Agent
        sentiment: Sentiment analysis from Sentiment Agent
        risk: Risk metrics from Risk Agent
    
    Returns:
        DecisionResult: Final structured decision with full reasoning
    """
    
    signal_details = []
    
    # ──────────────────────────────────────────────────────────
    # SIGNAL 1: Price Momentum (from StockData)
    # ──────────────────────────────────────────────────────────
    momentum_signal, momentum_strength, momentum_reason = _analyze_momentum(stock)
    signal_details.append(SignalDetail(
        agent="Price Momentum",
        signal=momentum_signal,
        strength=momentum_strength,
        reasoning=momentum_reason,
    ))
    
    # ──────────────────────────────────────────────────────────
    # SIGNAL 2: Sentiment (from SentimentResult)
    # ──────────────────────────────────────────────────────────
    sentiment_signal, sentiment_strength, sentiment_reason = _analyze_sentiment_signal(sentiment)
    signal_details.append(SignalDetail(
        agent="Sentiment Analysis",
        signal=sentiment_signal,
        strength=sentiment_strength,
        reasoning=sentiment_reason,
    ))
    
    # ──────────────────────────────────────────────────────────
    # SIGNAL 3: Risk Assessment (from RiskResult)
    # ──────────────────────────────────────────────────────────
    risk_signal, risk_strength, risk_reason = _analyze_risk_signal(risk)
    signal_details.append(SignalDetail(
        agent="Risk Assessment",
        signal=risk_signal,
        strength=risk_strength,
        reasoning=risk_reason,
    ))
    
    # ──────────────────────────────────────────────────────────
    # SIGNAL 4: Trend Analysis (price trend from history)
    # ──────────────────────────────────────────────────────────
    trend_signal, trend_strength, trend_reason = _analyze_trend(stock)
    signal_details.append(SignalDetail(
        agent="Trend Analysis",
        signal=trend_signal,
        strength=trend_strength,
        reasoning=trend_reason,
    ))
    
    # ──────────────────────────────────────────────────────────
    # CONFLICT DETECTION
    # ──────────────────────────────────────────────────────────
    signals = [s.signal for s in signal_details if s.signal != "HOLD"]
    buy_signals = [s for s in signal_details if s.signal == "BUY"]
    sell_signals = [s for s in signal_details if s.signal == "SELL"]
    
    conflict = len(buy_signals) > 0 and len(sell_signals) > 0
    
    # ──────────────────────────────────────────────────────────
    # FINAL DECISION LOGIC
    # ──────────────────────────────────────────────────────────
    if conflict:
        # Conflict detected – check if one side is significantly stronger
        buy_total = sum(s.strength for s in buy_signals)
        sell_total = sum(s.strength for s in sell_signals)
        
        if buy_total > sell_total * 1.5:
            decision = "BUY"
            confidence = _compute_confidence(buy_signals, signal_details)
        elif sell_total > buy_total * 1.5:
            decision = "SELL"
            confidence = _compute_confidence(sell_signals, signal_details)
        else:
            decision = "HOLD"
            confidence = max(30.0, min(55.0, 50.0 - abs(buy_total - sell_total) * 10))
    else:
        if len(buy_signals) > len(sell_signals):
            decision = "BUY"
            confidence = _compute_confidence(buy_signals, signal_details)
        elif len(sell_signals) > len(buy_signals):
            decision = "SELL"
            confidence = _compute_confidence(sell_signals, signal_details)
        else:
            decision = "HOLD"
            confidence = 50.0
    
    # ──────────────────────────────────────────────────────────
    # EXPLANATION GENERATION
    # ──────────────────────────────────────────────────────────
    explanation = _generate_explanation(
        decision, confidence, conflict, signal_details, stock, sentiment, risk
    )
    
    # Summary signals list
    summary_signals = [f"{s.agent}: {s.signal} ({s.strength:.0%})" for s in signal_details]
    
    return DecisionResult(
        symbol=stock.symbol,
        decision=decision,
        confidence=round(confidence, 1),
        conflict=conflict,
        explanation=explanation,
        signals=summary_signals,
        signal_details=signal_details,
        stock_data=stock,
        sentiment=sentiment,
        risk=risk,
    )


# ═══════════════════════════════════════════════════════════════
# SIGNAL ANALYZERS
# ═══════════════════════════════════════════════════════════════

def _analyze_momentum(stock: StockData) -> tuple:
    """Analyze price momentum from change percentage."""
    change = stock.change_percent
    
    if change > 3.0:
        return "BUY", min(0.9, 0.5 + change / 20), f"Strong upward momentum at {change:+.2f}%"
    elif change > 1.0:
        return "BUY", 0.4 + change / 20, f"Positive momentum at {change:+.2f}%"
    elif change < -3.0:
        return "SELL", min(0.9, 0.5 + abs(change) / 20), f"Strong downward pressure at {change:+.2f}%"
    elif change < -1.0:
        return "SELL", 0.4 + abs(change) / 20, f"Negative momentum at {change:+.2f}%"
    else:
        return "HOLD", 0.3, f"Flat momentum at {change:+.2f}%, no strong directional bias"


def _analyze_sentiment_signal(sentiment: SentimentResult) -> tuple:
    """Convert sentiment into a trading signal."""
    score = sentiment.score
    
    if score > 0.2:
        return "BUY", min(0.9, 0.5 + score), f"Strongly bullish sentiment ({sentiment.label}, score: {score:.3f})"
    elif score > 0.05:
        return "BUY", 0.3 + score, f"Mildly bullish sentiment ({sentiment.label}, score: {score:.3f})"
    elif score < -0.2:
        return "SELL", min(0.9, 0.5 + abs(score)), f"Strongly bearish sentiment ({sentiment.label}, score: {score:.3f})"
    elif score < -0.05:
        return "SELL", 0.3 + abs(score), f"Mildly bearish sentiment ({sentiment.label}, score: {score:.3f})"
    else:
        return "HOLD", 0.3, f"Neutral sentiment ({sentiment.label}, score: {score:.3f})"


def _analyze_risk_signal(risk: RiskResult) -> tuple:
    """Convert risk metrics into a trading signal."""
    vol = risk.volatility
    
    if risk.risk_level == "Very High":
        return "SELL", 0.7, f"Very high risk – volatility at {vol:.1f}%, max drawdown {risk.max_drawdown:.1f}%"
    elif risk.risk_level == "High":
        return "HOLD", 0.5, f"High risk environment – volatility at {vol:.1f}%, caution advised"
    elif risk.risk_level == "Low":
        return "BUY", 0.5, f"Low risk environment – volatility at {vol:.1f}%, favorable conditions"
    else:  # Medium
        return "HOLD", 0.3, f"Moderate risk – volatility at {vol:.1f}%, standard conditions"


def _analyze_trend(stock: StockData) -> tuple:
    """Analyze price trend from historical data."""
    if len(stock.prices) < 5:
        return "HOLD", 0.2, "Insufficient historical data for trend analysis"
    
    prices = stock.prices
    recent = prices[-5:]
    earlier = prices[:5] if len(prices) >= 10 else prices[:len(prices)//2]
    
    recent_avg = sum(recent) / len(recent)
    earlier_avg = sum(earlier) / len(earlier)
    
    if earlier_avg == 0:
        return "HOLD", 0.2, "Cannot compute trend"
    
    trend_pct = ((recent_avg - earlier_avg) / earlier_avg) * 100
    
    # Check for consistent direction in recent prices
    updays = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
    consistency = updays / (len(recent) - 1)
    
    if trend_pct > 3.0 and consistency > 0.6:
        strength = min(0.8, 0.4 + trend_pct / 30)
        return "BUY", strength, f"Uptrend detected: {trend_pct:+.1f}% over period, {consistency:.0%} consistency"
    elif trend_pct < -3.0 and consistency < 0.4:
        strength = min(0.8, 0.4 + abs(trend_pct) / 30)
        return "SELL", strength, f"Downtrend detected: {trend_pct:+.1f}% over period, low consistency"
    else:
        return "HOLD", 0.3, f"No clear trend: {trend_pct:+.1f}% over period"


# ═══════════════════════════════════════════════════════════════
# CONFIDENCE & EXPLANATION
# ═══════════════════════════════════════════════════════════════

def _compute_confidence(aligned_signals: list, all_signals: list) -> float:
    """Compute confidence percentage based on signal agreement and strength."""
    if not aligned_signals:
        return 50.0
    
    # Base confidence from aligned signal strengths
    avg_strength = sum(s.strength for s in aligned_signals) / len(aligned_signals)
    
    # Agreement bonus
    alignment_ratio = len(aligned_signals) / len(all_signals)
    
    confidence = (avg_strength * 60) + (alignment_ratio * 40)
    
    return max(30.0, min(98.0, confidence))


def _generate_explanation(
    decision: str,
    confidence: float,
    conflict: bool,
    signals: list,
    stock: StockData,
    sentiment: SentimentResult,
    risk: RiskResult,
) -> str:
    """Generate a human-readable explanation of the decision."""
    
    lines = []
    
    # Header
    lines.append(f"FinSynapse Decision Engine — {stock.symbol}")
    lines.append(f"{'='*50}")
    
    # Summary
    if conflict:
        lines.append(f"\n⚠ CONFLICT DETECTED: Mixed signals across agents.")
        lines.append(f"Final decision: {decision} with {confidence:.1f}% confidence (reduced due to conflict).")
    else:
        lines.append(f"\nSignals are aligned. Final decision: {decision} with {confidence:.1f}% confidence.")
    
    # Agent breakdown
    lines.append(f"\n--- Agent Signal Breakdown ---")
    for s in signals:
        icon = "🟢" if s.signal == "BUY" else "🔴" if s.signal == "SELL" else "🟡"
        lines.append(f"{icon} {s.agent}: {s.signal} (strength: {s.strength:.0%})")
        lines.append(f"   └─ {s.reasoning}")
    
    # Key metrics
    lines.append(f"\n--- Key Metrics ---")
    lines.append(f"Price: ${stock.current_price:.2f} ({stock.change_percent:+.2f}%)")
    lines.append(f"Sentiment: {sentiment.label} ({sentiment.score:+.3f})")
    lines.append(f"Volatility: {risk.volatility:.1f}% ({risk.risk_level})")
    lines.append(f"Max Drawdown: {risk.max_drawdown:.1f}%")
    
    if risk.sharpe_estimate != 0:
        lines.append(f"Sharpe Ratio: {risk.sharpe_estimate:.2f}")
    
    return "\n".join(lines)
