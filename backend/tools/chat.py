"""
Context-Aware AI Chat Tool – Uses Groq LLaMA to answer financial questions
based on the latest analysis outputs (decision, sentiment, risk).

This is a NEW extension module. It does NOT modify any existing agent logic.
"""

import json
import urllib.request
import urllib.error
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def chat_with_context(
    question: str,
    decision: str = "",
    sentiment: str = "",
    risk: str = "",
    symbol: str = "",
    confidence: float = 0.0,
    stock_price: float = 0.0,
    extra_context: str = "",
) -> Dict[str, Any]:
    """
    Answer a financial question using Groq LLaMA with analysis context.
    Falls back to a built-in intelligent response engine if the API fails.

    Args:
        question: User's question
        decision: Latest decision (BUY/SELL/HOLD)
        sentiment: Sentiment label
        risk: Risk level
        symbol: Stock symbol
        confidence: Confidence percentage
        stock_price: Current stock price
        extra_context: Any additional context

    Returns:
        Dictionary with answer and metadata
    """
    # Build context-aware system prompt
    system_prompt = _build_system_prompt(
        decision, sentiment, risk, symbol,
        confidence, stock_price, extra_context
    )

    # Try Groq API first
    result = _try_groq(system_prompt, question, symbol, decision, sentiment, risk, confidence)
    if result:
        return result

    # Fallback: built-in intelligent response
    logger.info("Using built-in response engine (Groq unavailable)")
    return _generate_builtin_response(
        question, symbol, decision, sentiment, risk,
        confidence, stock_price
    )


def _try_groq(system_prompt, question, symbol, decision, sentiment, risk, confidence):
    """Attempt to call Groq API. Returns None if it fails."""
    try:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 0.9,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            GROQ_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result["choices"][0]["message"]["content"]

        return {
            "answer": answer,
            "model": GROQ_MODEL,
            "symbol": symbol,
            "context_used": {
                "decision": decision,
                "sentiment": sentiment,
                "risk": risk,
                "confidence": confidence,
            },
            "success": True,
        }

    except Exception as e:
        logger.warning(f"Groq API failed: {e}")
        return None


def _generate_builtin_response(
    question, symbol, decision, sentiment, risk, confidence, stock_price
):
    """
    Generate an intelligent context-aware response using the analysis data.
    This is the fallback when the Groq API is unavailable.
    """
    q = question.lower().strip()
    has_context = bool(symbol and decision)

    # Build context string for answers
    ctx_parts = []
    if symbol:
        ctx_parts.append(f"**{symbol}**")
    if stock_price > 0:
        ctx_parts.append(f"currently trading at **${stock_price:.2f}**")
    if decision:
        ctx_parts.append(f"with a **{decision}** recommendation")
    if confidence > 0:
        ctx_parts.append(f"at **{confidence:.1f}%** confidence")
    if sentiment:
        ctx_parts.append(f"Market sentiment is **{sentiment}**")
    if risk:
        ctx_parts.append(f"Risk level: **{risk}**")

    context_summary = ". ".join(ctx_parts) + "." if ctx_parts else ""

    # Pattern-match user questions for intelligent responses
    if any(w in q for w in ["should i buy", "should i invest", "buy or sell", "what should i do"]):
        if has_context:
            answer = (
                f"Based on the FinSynapse multi-agent analysis for {symbol}:\n\n"
                f"• Decision: **{decision}** with {confidence:.1f}% confidence\n"
                f"• Sentiment: {sentiment}\n"
                f"• Risk Level: {risk}\n"
                f"• Price: ${stock_price:.2f}\n\n"
            )
            if decision == "BUY":
                answer += "The agents lean bullish, but remember — this is algorithmic analysis, not financial advice. Consider your portfolio allocation, risk tolerance, and investment horizon before acting."
            elif decision == "SELL":
                answer += "The signals suggest caution. Multiple agents have flagged concerns. Review the detailed reasoning and consider your cost basis and tax implications."
            else:
                answer += "The signals are mixed, suggesting a HOLD. This often means waiting for clearer directional signals. Consider setting price alerts at key support/resistance levels."
        else:
            answer = "I'd love to help, but I need analysis data first! Run an analysis on the Dashboard by entering a stock symbol, then come back and ask me. I'll use the real-time data from all 5 agents to give you contextual insights."

    elif any(w in q for w in ["risk", "risky", "dangerous", "safe"]):
        if has_context and risk:
            risk_detail = {
                "Low": "The risk metrics look favorable — low volatility and contained drawdowns. However, low historical risk doesn't guarantee future safety.",
                "Moderate": "Risk is at moderate levels. The stock shows average volatility for its sector. Position sizing and stop-losses are recommended.",
                "High": "⚠️ Risk is elevated. High volatility and significant drawdown potential detected. Consider reducing position size or using protective options strategies.",
            }
            answer = f"Risk analysis for {symbol}:\n\n• Risk Level: **{risk}**\n\n{risk_detail.get(risk, 'Risk data is being processed.')}\n\nAlways align your position size with your overall portfolio risk tolerance."
        else:
            answer = "Run a stock analysis first, and I'll break down the risk metrics including volatility, max drawdown, Sharpe ratio, and more."

    elif any(w in q for w in ["sentiment", "market feel", "bullish", "bearish"]):
        if has_context and sentiment:
            answer = f"Market sentiment for {symbol} is currently **{sentiment}**.\n\nThis is derived from analyzing recent news headlines using NLP. The sentiment agent scores each headline and aggregates them into an overall market mood indicator.\n\n"
            if "Positive" in sentiment or "Bullish" in sentiment:
                answer += "The news flow is favorable, which historically correlates with short-term price momentum."
            elif "Negative" in sentiment or "Bearish" in sentiment:
                answer += "Negative news sentiment can create selling pressure. However, contrarian opportunities sometimes arise from excessive pessimism."
            else:
                answer += "Neutral sentiment suggests the market is in a wait-and-see mode. Watch for catalyst events that could shift the narrative."
        else:
            answer = "I need analysis data to discuss sentiment. Run an analysis on the Dashboard and I'll have full sentiment breakdown for you!"

    elif any(w in q for w in ["explain", "how does", "what is", "tell me about"]):
        if "finsynapse" in q or "system" in q or "work" in q:
            answer = ("FinSynapse is a **multi-agent financial decision engine** with 5 specialized AI agents:\n\n"
                     "1. 📊 **Data Agent** — Fetches real-time price data via yfinance\n"
                     "2. 📰 **News Agent** — Scrapes financial news from RSS feeds\n"
                     "3. 💭 **Sentiment Agent** — NLP analysis of headlines (TextBlob)\n"
                     "4. ⚠️ **Risk Agent** — Calculates volatility, drawdown, Sharpe ratio\n"
                     "5. 🧪 **Simulation Agent** — What-if scenario modeling\n\n"
                     "The **Decision Engine** aggregates all signals, detects conflicts, and produces a confidence-weighted BUY/SELL/HOLD recommendation.")
        elif "benchmark" in q:
            answer = "The **Benchmark Comparison** tool lets you compare any stock's performance against a market index (S&P 500, Nifty 50, etc.). It normalizes both to a base of 100 and calculates **alpha** — the excess return of the stock vs. the index."
        elif "confidence" in q:
            answer = f"Confidence score represents how strongly the agents agree on the decision. {'Currently at ' + str(round(confidence, 1)) + '% for ' + symbol + '.' if has_context else ''}\n\n• **80%+**: Strong consensus across agents\n• **60-80%**: Moderate agreement, some mixed signals\n• **Below 60%**: Conflicting signals — exercise extra caution"
        else:
            answer = "That's a great question! I can help with stock analysis, sentiment, risk assessment, and market insights. Try asking about a specific stock after running an analysis."

    elif any(w in q for w in ["compare", "vs", "versus", "better"]):
        answer = "For comparing two stocks head-to-head, use the **Comparison** page in the sidebar! It runs full multi-agent analysis on both stocks and gives you a side-by-side breakdown with an AI recommendation."

    elif any(w in q for w in ["simulate", "what if", "scenario", "hypothetical"]):
        answer = "Check out the **Simulation** page! You can model hypothetical price changes (-50% crash to +50% surge) and see how the decision engine's recommendation would change. Great for stress-testing your thesis."

    elif any(w in q for w in ["hello", "hi", "hey", "help"]):
        if has_context:
            answer = f"Hello! I'm your FinSynapse AI analyst. I currently have analysis data loaded for **{symbol}** ({decision} @ {confidence:.1f}% confidence). Ask me anything about the analysis — risk, sentiment, or whether the signals support a trade!"
        else:
            answer = "Hello! I'm your FinSynapse AI assistant. To get started:\n\n1. Go to the **Dashboard**\n2. Enter a stock symbol (e.g., AAPL, TSLA, RELIANCE.NS)\n3. Click **Analyze**\n4. Come back here and ask me about the results!\n\nI'll use all the agent data to give you contextual insights."

    elif has_context:
        # Generic response with context
        answer = (
            f"Here's what I know about {symbol} from the latest analysis:\n\n"
            f"• **Decision**: {decision}\n"
            f"• **Confidence**: {confidence:.1f}%\n"
            f"• **Sentiment**: {sentiment}\n"
            f"• **Risk**: {risk}\n"
            f"• **Price**: ${stock_price:.2f}\n\n"
            f"Could you rephrase your question? I can help with risk analysis, sentiment breakdown, buy/sell reasoning, or general market concepts."
        )
    else:
        answer = "I'm here to help! Run a stock analysis first on the Dashboard, then ask me anything — I'll use the real-time agent data to give you intelligent, context-aware answers."

    # Disclaimer
    answer += "\n\n---\n*FinSynapse provides analysis and educational information, not financial advice. Always do your own research and consult a financial advisor before making investment decisions.*"

    return {
        "answer": answer,
        "model": "finsynapse-builtin-v1",
        "symbol": symbol,
        "context_used": {
            "decision": decision,
            "sentiment": sentiment,
            "risk": risk,
            "confidence": confidence,
        },
        "success": True,
    }


def _build_system_prompt(
    decision: str,
    sentiment: str,
    risk: str,
    symbol: str,
    confidence: float,
    stock_price: float,
    extra_context: str,
) -> str:
    """Build a context-aware system prompt for the LLM."""
    context_parts = []

    if symbol:
        context_parts.append(f"Stock being analyzed: {symbol}")
    if stock_price > 0:
        context_parts.append(f"Current price: ${stock_price:.2f}")
    if decision:
        context_parts.append(f"Latest AI decision: {decision}")
    if confidence > 0:
        context_parts.append(f"Confidence: {confidence:.1f}%")
    if sentiment:
        context_parts.append(f"Market sentiment: {sentiment}")
    if risk:
        context_parts.append(f"Risk level: {risk}")
    if extra_context:
        context_parts.append(f"Additional context: {extra_context}")

    context_str = "\n".join(context_parts) if context_parts else "No analysis data available yet."

    return f"""You are FinSynapse AI — a premium financial analysis assistant powered by a multi-agent decision engine.

Based on the latest analysis data:
{context_str}

Answer the user's question using this context. Be:
- Concise but insightful
- Data-driven, referencing the analysis above
- Professional but approachable
- Honest about limitations

Important: You provide analysis and educational information, NOT financial advice. Always remind users to do their own research and consult a financial advisor before making investment decisions.

If no analysis data is provided, still answer helpfully based on your general knowledge, but note that the user should run an analysis first for personalized insights."""
