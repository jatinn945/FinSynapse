"""
Orchestrator – Coordinates all agents and the decision engine.
This is the central conductor of the FinSynapse multi-agent system.
"""

from models import (
    StockData,
    NewsData,
    SentimentResult,
    RiskResult,
    DecisionResult,
    HistoryEntry,
    ComparisonResult,
    SimulationResult,
)
from agents import (
    get_stock_data,
    get_news,
    analyze_sentiment,
    calculate_risk,
    simulate_price_change,
)
from engine import make_decision
from memory import save_decision, get_history
import logging

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates the multi-agent pipeline:
    
    User Input → Data Agent → News Agent → Sentiment Agent → Risk Agent
                                                              ↓
                                                     Decision Engine
                                                              ↓
                                                     Memory Layer
                                                              ↓
                                                   DecisionResult
    """
    
    def analyze(self, symbol: str) -> DecisionResult:
        """
        Run the full analysis pipeline for a stock.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            DecisionResult with complete analysis
        """
        logger.info(f"Orchestrator: Starting analysis for {symbol}")
        
        # Step 1: Data Agent — Fetch stock data
        stock_data = get_stock_data(symbol)
        logger.info(f"  ✓ Data Agent: {stock_data.company_name} @ ${stock_data.current_price}")
        
        # Step 2: News Agent — Fetch headlines
        news_data = get_news(symbol)
        logger.info(f"  ✓ News Agent: {len(news_data.headlines)} headlines")
        
        # Step 3: Sentiment Agent — Analyze sentiment
        sentiment = analyze_sentiment(news_data)
        logger.info(f"  ✓ Sentiment Agent: {sentiment.label} ({sentiment.score:+.3f})")
        
        # Step 4: Risk Agent — Calculate risk
        risk = calculate_risk(stock_data)
        logger.info(f"  ✓ Risk Agent: {risk.risk_level} (volatility: {risk.volatility:.1f}%)")
        
        # Step 5: Decision Engine — Make decision
        decision = make_decision(stock_data, sentiment, risk)
        decision.news = news_data
        logger.info(f"  ✓ Decision Engine: {decision.decision} ({decision.confidence:.1f}%)")
        
        # Step 6: Memory Layer — Save to history
        entry = HistoryEntry(
            symbol=symbol.upper(),
            decision=decision.decision,
            confidence=decision.confidence,
            conflict=decision.conflict,
            explanation=decision.explanation,
        )
        save_decision(entry)
        logger.info(f"  ✓ Memory Layer: Decision saved")
        
        return decision
    
    def simulate(self, symbol: str, percent_change: float) -> SimulationResult:
        """
        Run a what-if simulation: analyze with modified prices.
        
        Args:
            symbol: Stock ticker symbol
            percent_change: Hypothetical price change percentage
        
        Returns:
            SimulationResult comparing original vs simulated
        """
        logger.info(f"Orchestrator: Simulation for {symbol} with {percent_change:+.1f}% change")
        
        # Get original analysis
        original = self.analyze(symbol)
        
        # Simulate price change
        simulated_stock = simulate_price_change(original.stock_data, percent_change)
        
        # Re-run sentiment and risk on simulated data
        # (sentiment stays the same — news hasn't changed)
        simulated_risk = calculate_risk(simulated_stock)
        
        # Re-run decision engine with simulated data
        simulated_decision = make_decision(
            simulated_stock,
            original.sentiment,
            simulated_risk,
        )
        simulated_decision.news = original.news
        
        # Generate impact summary
        impact = self._generate_impact_summary(
            original, simulated_decision, percent_change
        )
        
        return SimulationResult(
            original=original,
            simulated=simulated_decision,
            price_change_percent=percent_change,
            impact_summary=impact,
        )
    
    def compare(self, symbol1: str, symbol2: str) -> ComparisonResult:
        """
        Compare analysis of two stocks side by side.
        
        Args:
            symbol1: First stock ticker
            symbol2: Second stock ticker
        
        Returns:
            ComparisonResult with both analyses and summary
        """
        logger.info(f"Orchestrator: Comparing {symbol1} vs {symbol2}")
        
        result1 = self.analyze(symbol1)
        result2 = self.analyze(symbol2)
        
        summary = self._generate_comparison_summary(result1, result2)
        recommendation = self._generate_recommendation(result1, result2)
        
        return ComparisonResult(
            stock1=result1,
            stock2=result2,
            summary=summary,
            recommendation=recommendation,
        )
    
    def get_timeline(self, symbol: str) -> list:
        """Retrieve decision history for a symbol."""
        return get_history(symbol)
    
    # ═══════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════
    
    def _generate_impact_summary(
        self,
        original: DecisionResult,
        simulated: DecisionResult,
        change: float,
    ) -> str:
        """Generate a summary of simulation impact."""
        lines = []
        lines.append(f"Simulation Impact Analysis: {change:+.1f}% price change")
        lines.append(f"{'─'*45}")
        
        if original.decision != simulated.decision:
            lines.append(f"⚡ Decision CHANGED: {original.decision} → {simulated.decision}")
        else:
            lines.append(f"✓ Decision unchanged: {simulated.decision}")
        
        conf_delta = simulated.confidence - original.confidence
        lines.append(f"Confidence: {original.confidence:.1f}% → {simulated.confidence:.1f}% ({conf_delta:+.1f}%)")
        
        if original.risk and simulated.risk:
            lines.append(f"Risk Level: {original.risk.risk_level} → {simulated.risk.risk_level}")
        
        return "\n".join(lines)
    
    def _generate_comparison_summary(
        self,
        r1: DecisionResult,
        r2: DecisionResult,
    ) -> str:
        """Generate comparison summary between two stocks."""
        lines = []
        lines.append(f"Comparison: {r1.symbol} vs {r2.symbol}")
        lines.append(f"{'─'*45}")
        lines.append(f"{r1.symbol}: {r1.decision} ({r1.confidence:.1f}% confidence)")
        lines.append(f"{r2.symbol}: {r2.decision} ({r2.confidence:.1f}% confidence)")
        
        if r1.stock_data and r2.stock_data:
            lines.append(f"\nPrice: ${r1.stock_data.current_price:.2f} vs ${r2.stock_data.current_price:.2f}")
        
        if r1.sentiment and r2.sentiment:
            lines.append(f"Sentiment: {r1.sentiment.label} vs {r2.sentiment.label}")
        
        if r1.risk and r2.risk:
            lines.append(f"Risk: {r1.risk.risk_level} vs {r2.risk.risk_level}")
        
        return "\n".join(lines)
    
    def _generate_recommendation(
        self,
        r1: DecisionResult,
        r2: DecisionResult,
    ) -> str:
        """Generate a recommendation between two stocks."""
        score1 = r1.confidence if r1.decision == "BUY" else -r1.confidence if r1.decision == "SELL" else 0
        score2 = r2.confidence if r2.decision == "BUY" else -r2.confidence if r2.decision == "SELL" else 0
        
        if score1 > score2:
            return f"{r1.symbol} appears more favorable with a {r1.decision} signal at {r1.confidence:.1f}% confidence."
        elif score2 > score1:
            return f"{r2.symbol} appears more favorable with a {r2.decision} signal at {r2.confidence:.1f}% confidence."
        else:
            return f"Both stocks show similar signals. Consider other factors before deciding."
