"""
Sentiment Agent – Analyzes sentiment of news headlines using TextBlob.
Returns: SentimentResult (Pydantic model)
"""

from textblob import TextBlob
from models import NewsData, SentimentResult
import logging

logger = logging.getLogger(__name__)


def analyze_sentiment(news: NewsData) -> SentimentResult:
    """
    Analyze overall sentiment from news headlines.
    
    Args:
        news: NewsData containing headlines to analyze
    
    Returns:
        SentimentResult: Structured sentiment with score, label, and breakdown
    """
    if not news.headlines:
        return SentimentResult(
            score=0.0,
            label="Neutral",
            headline_scores=[],
        )
    
    headline_scores = []
    total_score = 0.0
    
    for headline in news.headlines:
        try:
            blob = TextBlob(headline)
            polarity = blob.sentiment.polarity  # -1.0 to 1.0
            subjectivity = blob.sentiment.subjectivity  # 0.0 to 1.0
            
            # Determine individual headline sentiment
            if polarity > 0.1:
                h_label = "Bullish"
            elif polarity < -0.1:
                h_label = "Bearish"
            else:
                h_label = "Neutral"
            
            headline_scores.append({
                "headline": headline,
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
                "label": h_label,
            })
            
            total_score += polarity
        
        except Exception as e:
            logger.warning(f"Sentiment analysis failed for headline: {e}")
            headline_scores.append({
                "headline": headline,
                "polarity": 0.0,
                "subjectivity": 0.0,
                "label": "Neutral",
            })
    
    # Calculate overall score
    avg_score = total_score / len(news.headlines)
    avg_score = max(-1.0, min(1.0, avg_score))  # Clamp
    
    # Determine overall label
    if avg_score > 0.15:
        label = "Bullish"
    elif avg_score > 0.05:
        label = "Slightly Bullish"
    elif avg_score < -0.15:
        label = "Bearish"
    elif avg_score < -0.05:
        label = "Slightly Bearish"
    else:
        label = "Neutral"
    
    # Sort headlines by impact (absolute polarity)
    headline_scores.sort(key=lambda x: abs(x["polarity"]), reverse=True)
    
    return SentimentResult(
        score=round(avg_score, 3),
        label=label,
        headline_scores=headline_scores,
    )
