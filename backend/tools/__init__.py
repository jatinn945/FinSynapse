"""
FinSynapse Tools Package
Extended modules for benchmark comparison, simulation, and AI chat.
These are safe extensions that do NOT modify the existing agent pipeline.
"""

from .benchmark import get_benchmark_data
from .chat import chat_with_context
from .portfolio import analyze_portfolio

__all__ = [
    "get_benchmark_data",
    "chat_with_context",
    "analyze_portfolio",
]
