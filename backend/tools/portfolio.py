"""
Portfolio Intelligence Tool – Analyzes a portfolio of multiple stocks.

Runs the existing multi-agent pipeline on each stock, then computes
portfolio-level metrics: correlation matrix, diversification score,
risk heatmap, sector breakdown, and AI-generated summary.

This is a NEW extension module. It does NOT modify any existing agent logic.
"""

import logging
import math
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def analyze_portfolio(symbols: List[str]) -> Dict[str, Any]:
    """
    Run full multi-agent analysis on a portfolio of stocks.

    Args:
        symbols: List of stock ticker symbols (max 10)

    Returns:
        Dictionary with per-stock analysis and portfolio-level intelligence
    """
    from orchestrator import Orchestrator

    orchestrator = Orchestrator()
    symbols = [s.strip().upper() for s in symbols if s.strip()]

    # Cap at 10 to avoid rate limiting
    if len(symbols) > 10:
        symbols = symbols[:10]

    if len(symbols) < 2:
        raise ValueError("Portfolio analysis requires at least 2 symbols.")

    logger.info(f"Portfolio analysis started for {len(symbols)} stocks: {symbols}")

    # ── Step 1: Run multi-agent analysis on each stock ──
    holdings = []
    failed_symbols = []

    for symbol in symbols:
        try:
            logger.info(f"  Analyzing {symbol}...")
            result = orchestrator.analyze(symbol)

            holding = {
                "symbol": result.symbol,
                "company_name": result.stock_data.company_name if result.stock_data else symbol,
                "decision": result.decision,
                "confidence": round(result.confidence, 1),
                "risk_level": result.risk.risk_level if result.risk else "Unknown",
                "volatility": round(result.risk.volatility, 1) if result.risk else 0,
                "max_drawdown": round(result.risk.max_drawdown, 1) if result.risk else 0,
                "sharpe": round(result.risk.sharpe_estimate, 2) if result.risk else 0,
                "sentiment": result.sentiment.label if result.sentiment else "Neutral",
                "sentiment_score": round(result.sentiment.score, 3) if result.sentiment else 0,
                "price": round(result.stock_data.current_price, 2) if result.stock_data else 0,
                "change_pct": round(result.stock_data.change_percent, 2) if result.stock_data else 0,
                "prices": result.stock_data.prices if result.stock_data else [],
                "market_cap": result.stock_data.market_cap if result.stock_data else "N/A",
                "pe_ratio": result.stock_data.pe_ratio if result.stock_data else None,
                "conflict": result.conflict,
                "signals": [
                    {
                        "agent": s.agent,
                        "signal": s.signal,
                        "strength": round(s.strength, 2),
                    }
                    for s in (result.signal_details or [])
                ],
            }
            holdings.append(holding)

        except Exception as e:
            logger.warning(f"  Failed to analyze {symbol}: {e}")
            failed_symbols.append({"symbol": symbol, "error": str(e)})

    if len(holdings) < 2:
        raise ValueError("Could not analyze enough stocks. Need at least 2 successful analyses.")

    # ── Step 2: Compute portfolio-level metrics ──
    correlation_matrix = _compute_correlation_matrix(holdings)
    diversification = _compute_diversification(holdings, correlation_matrix)
    risk_heatmap = _build_risk_heatmap(holdings)
    sectors = _detect_sectors(holdings)
    conflicts = _scan_conflicts(holdings)
    portfolio_stats = _compute_portfolio_stats(holdings)
    summary = _generate_portfolio_summary(holdings, diversification, portfolio_stats, conflicts)

    return {
        "portfolio_size": len(holdings),
        "symbols": [h["symbol"] for h in holdings],
        "holdings": holdings,
        "failed": failed_symbols,

        # Portfolio-level intelligence
        "diversification_score": diversification["score"],
        "diversification_grade": diversification["grade"],
        "overall_risk": portfolio_stats["overall_risk"],
        "avg_confidence": portfolio_stats["avg_confidence"],
        "buy_count": portfolio_stats["buy_count"],
        "sell_count": portfolio_stats["sell_count"],
        "hold_count": portfolio_stats["hold_count"],

        # Correlation matrix
        "correlation_matrix": correlation_matrix,

        # Sector breakdown
        "sectors": sectors,

        # Risk heatmap
        "risk_heatmap": risk_heatmap,

        # Conflicts found
        "conflicts": conflicts,

        # AI summary
        "summary": summary,
    }


# ═══════════════════════════════════════════════════════════════
# CORRELATION MATRIX
# ═══════════════════════════════════════════════════════════════

def _compute_correlation_matrix(holdings: List[dict]) -> Dict[str, Any]:
    """
    Compute pairwise correlation between stocks using their price histories.
    Uses Pearson correlation on daily returns.
    """
    labels = [h["symbol"] for h in holdings]
    n = len(labels)

    # Compute daily returns for each stock
    returns_map = {}
    for h in holdings:
        prices = h.get("prices", [])
        if len(prices) >= 2:
            returns = []
            for i in range(1, len(prices)):
                if prices[i - 1] != 0:
                    returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
                else:
                    returns.append(0)
            returns_map[h["symbol"]] = returns
        else:
            returns_map[h["symbol"]] = []

    # Build correlation matrix
    values = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                corr = _pearson_correlation(
                    returns_map.get(labels[i], []),
                    returns_map.get(labels[j], [])
                )
                row.append(round(corr, 2))
        values.append(row)

    return {"labels": labels, "values": values}


def _pearson_correlation(x: list, y: list) -> float:
    """Compute Pearson correlation coefficient between two series."""
    # Use overlapping length
    min_len = min(len(x), len(y))
    if min_len < 3:
        return 0.0

    x = x[:min_len]
    y = y[:min_len]

    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if denom_x == 0 or denom_y == 0:
        return 0.0

    return numerator / (denom_x * denom_y)


# ═══════════════════════════════════════════════════════════════
# DIVERSIFICATION SCORE
# ═══════════════════════════════════════════════════════════════

def _compute_diversification(holdings: List[dict], corr_matrix: dict) -> dict:
    """
    Compute a diversification score (0–100) based on:
    1. Average pairwise correlation (lower = more diversified)
    2. Number of distinct sectors
    3. Risk level spread
    """
    n = len(holdings)

    # Average off-diagonal correlation
    values = corr_matrix.get("values", [])
    correlations = []
    for i in range(n):
        for j in range(i + 1, n):
            if i < len(values) and j < len(values[i]):
                correlations.append(abs(values[i][j]))

    avg_corr = sum(correlations) / len(correlations) if correlations else 0.5

    # Correlation score: low correlation = good (0 to 40 points)
    corr_score = max(0, (1 - avg_corr)) * 40

    # Sector diversity (0 to 30 points)
    risk_levels = set(h.get("risk_level", "Unknown") for h in holdings)
    sentiments = set(h.get("sentiment", "Neutral") for h in holdings)
    decisions = set(h.get("decision", "HOLD") for h in holdings)

    variety_score = (
        min(15, len(risk_levels) * 5) +
        min(10, len(sentiments) * 3.33) +
        min(5, len(decisions) * 2.5)
    )

    # Size bonus (0 to 30 points) — more stocks = more diversified
    size_score = min(30, n * 6)

    total = round(corr_score + variety_score + size_score, 1)
    total = min(100, max(0, total))

    # Grade
    if total >= 85:
        grade = "A+"
    elif total >= 75:
        grade = "A"
    elif total >= 65:
        grade = "B+"
    elif total >= 55:
        grade = "B"
    elif total >= 45:
        grade = "C+"
    elif total >= 35:
        grade = "C"
    else:
        grade = "D"

    return {"score": total, "grade": grade, "avg_correlation": round(avg_corr, 2)}


# ═══════════════════════════════════════════════════════════════
# RISK HEATMAP
# ═══════════════════════════════════════════════════════════════

def _build_risk_heatmap(holdings: List[dict]) -> List[dict]:
    """Build risk heatmap data for visualization."""
    color_map = {
        "Low": "#059669",       # green
        "Moderate": "#D97706",  # amber
        "High": "#DC2626",      # red
        "Very High": "#991B1B", # dark red
    }

    heatmap = []
    for h in holdings:
        risk_level = h.get("risk_level", "Unknown")
        heatmap.append({
            "symbol": h["symbol"],
            "company_name": h.get("company_name", h["symbol"]),
            "volatility": h.get("volatility", 0),
            "max_drawdown": h.get("max_drawdown", 0),
            "risk_level": risk_level,
            "color": color_map.get(risk_level, "#94A3B8"),
        })

    return heatmap


# ═══════════════════════════════════════════════════════════════
# SECTOR BREAKDOWN
# ═══════════════════════════════════════════════════════════════

def _detect_sectors(holdings: List[dict]) -> List[dict]:
    """
    Auto-detect sectors from yfinance info.
    Falls back to symbol-based heuristics.
    """
    import yfinance as yf

    sector_counts = {}
    for h in holdings:
        sector = "Unknown"
        try:
            info = yf.Ticker(h["symbol"]).info
            sector = info.get("sector", "Unknown")
            if not sector or sector == "":
                sector = info.get("industry", "Unknown")
        except Exception:
            # Heuristic fallback based on known symbols
            sector = _heuristic_sector(h["symbol"])

        if sector not in sector_counts:
            sector_counts[sector] = []
        sector_counts[sector].append(h["symbol"])

    total = len(holdings)
    sectors = []
    for sector, syms in sector_counts.items():
        sectors.append({
            "sector": sector,
            "count": len(syms),
            "symbols": syms,
            "percentage": round((len(syms) / total) * 100, 1),
        })

    # Sort by count descending
    sectors.sort(key=lambda s: s["count"], reverse=True)
    return sectors


def _heuristic_sector(symbol: str) -> str:
    """Fallback sector detection based on known symbols."""
    tech = ["AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "NFLX", "TCS.NS", "INFY.NS"]
    auto = ["TSLA"]
    finance = ["JPM", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]
    energy = ["RELIANCE.NS"]
    consumer = ["AMZN", "ITC.NS"]
    industrial = ["LT.NS"]

    s = symbol.upper()
    if s in tech:
        return "Technology"
    elif s in auto:
        return "Consumer Cyclical"
    elif s in finance:
        return "Financial Services"
    elif s in energy:
        return "Energy"
    elif s in consumer:
        return "Consumer"
    elif s in industrial:
        return "Industrials"
    return "Other"


# ═══════════════════════════════════════════════════════════════
# CONFLICT SCANNER
# ═══════════════════════════════════════════════════════════════

def _scan_conflicts(holdings: List[dict]) -> List[dict]:
    """Find stocks where agents have conflicting signals."""
    conflicts = []
    for h in holdings:
        if h.get("conflict"):
            signals = h.get("signals", [])
            buy_agents = [s["agent"] for s in signals if s["signal"] == "BUY"]
            sell_agents = [s["agent"] for s in signals if s["signal"] == "SELL"]

            detail = ""
            if buy_agents and sell_agents:
                detail = f"{', '.join(buy_agents)} say BUY but {', '.join(sell_agents)} say SELL"
            else:
                detail = "Mixed signals detected across agents"

            conflicts.append({
                "symbol": h["symbol"],
                "decision": h["decision"],
                "confidence": h["confidence"],
                "details": detail,
            })

    return conflicts


# ═══════════════════════════════════════════════════════════════
# PORTFOLIO STATS
# ═══════════════════════════════════════════════════════════════

def _compute_portfolio_stats(holdings: List[dict]) -> dict:
    """Compute aggregate portfolio statistics."""
    buy_count = sum(1 for h in holdings if h["decision"] == "BUY")
    sell_count = sum(1 for h in holdings if h["decision"] == "SELL")
    hold_count = sum(1 for h in holdings if h["decision"] == "HOLD")

    avg_confidence = round(
        sum(h["confidence"] for h in holdings) / len(holdings), 1
    ) if holdings else 0

    avg_volatility = round(
        sum(h.get("volatility", 0) for h in holdings) / len(holdings), 1
    ) if holdings else 0

    # Overall risk from average volatility
    if avg_volatility > 40:
        overall_risk = "Very High"
    elif avg_volatility > 25:
        overall_risk = "High"
    elif avg_volatility > 15:
        overall_risk = "Moderate"
    else:
        overall_risk = "Low"

    return {
        "buy_count": buy_count,
        "sell_count": sell_count,
        "hold_count": hold_count,
        "avg_confidence": avg_confidence,
        "avg_volatility": avg_volatility,
        "overall_risk": overall_risk,
    }


# ═══════════════════════════════════════════════════════════════
# AI SUMMARY GENERATION
# ═══════════════════════════════════════════════════════════════

def _generate_portfolio_summary(
    holdings: List[dict],
    diversification: dict,
    stats: dict,
    conflicts: List[dict],
) -> str:
    """Generate a human-readable portfolio health summary."""
    n = len(holdings)
    lines = []

    # Opening
    lines.append(f"📊 Portfolio Health Report ({n} Holdings)")
    lines.append("=" * 50)

    # Decision breakdown
    lines.append(
        f"\n🎯 Signal Breakdown: {stats['buy_count']} BUY, "
        f"{stats['sell_count']} SELL, {stats['hold_count']} HOLD"
    )
    lines.append(f"📈 Average Confidence: {stats['avg_confidence']}%")
    lines.append(f"⚡ Average Volatility: {stats['avg_volatility']}%")
    lines.append(f"🛡️ Overall Risk: {stats['overall_risk']}")

    # Diversification
    lines.append(f"\n🎯 Diversification Score: {diversification['score']}/100 ({diversification['grade']})")
    avg_corr = diversification.get("avg_correlation", 0)
    if avg_corr > 0.7:
        lines.append("⚠️  High correlation detected — your holdings move together. Consider adding uncorrelated assets.")
    elif avg_corr > 0.4:
        lines.append("📊 Moderate correlation — reasonable diversification, but room for improvement.")
    else:
        lines.append("✅ Low correlation — well-diversified portfolio with independent movers.")

    # Conflicts
    if conflicts:
        lines.append(f"\n⚠️  Agent Conflicts Detected in {len(conflicts)} stock(s):")
        for c in conflicts:
            lines.append(f"   • {c['symbol']}: {c['details']}")

    # Top picks
    buy_holdings = sorted(
        [h for h in holdings if h["decision"] == "BUY"],
        key=lambda x: x["confidence"],
        reverse=True,
    )
    if buy_holdings:
        top = buy_holdings[0]
        lines.append(f"\n🏆 Strongest BUY Signal: {top['symbol']} at {top['confidence']}% confidence")

    sell_holdings = [h for h in holdings if h["decision"] == "SELL"]
    if sell_holdings:
        worst = max(sell_holdings, key=lambda x: x["confidence"])
        lines.append(f"🔴 Strongest SELL Signal: {worst['symbol']} at {worst['confidence']}% confidence")

    # Risk warnings
    high_risk = [h for h in holdings if h.get("risk_level") in ("High", "Very High")]
    if high_risk:
        names = ", ".join(h["symbol"] for h in high_risk)
        lines.append(f"\n⚠️  High-risk holdings: {names}")

    return "\n".join(lines)
