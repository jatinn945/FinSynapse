"""
Memory Layer – SQLite-backed persistent storage for decision history.
Stores and retrieves HistoryEntry records.
"""

import sqlite3
import os
from typing import List
from models import HistoryEntry
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "finsynapse.db")


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                decision TEXT NOT NULL,
                confidence REAL NOT NULL,
                conflict INTEGER DEFAULT 0,
                explanation TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol ON decision_history(symbol)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON decision_history(timestamp DESC)
        """)
        conn.commit()
        logger.info("Database initialized successfully")
    finally:
        conn.close()


def save_decision(entry: HistoryEntry) -> HistoryEntry:
    """
    Save a decision to the history database.
    
    Args:
        entry: HistoryEntry to save
    
    Returns:
        HistoryEntry with assigned ID
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO decision_history (symbol, decision, confidence, conflict, explanation, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.symbol.upper(),
                entry.decision,
                entry.confidence,
                1 if entry.conflict else 0,
                entry.explanation,
                entry.timestamp or datetime.now().isoformat(),
            )
        )
        conn.commit()
        entry.id = cursor.lastrowid
        return entry
    finally:
        conn.close()


def get_history(symbol: str, limit: int = 50) -> List[HistoryEntry]:
    """
    Retrieve decision history for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        limit: Maximum entries to return
    
    Returns:
        List of HistoryEntry records, newest first
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, symbol, decision, confidence, conflict, explanation, timestamp
            FROM decision_history
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (symbol.upper(), limit)
        ).fetchall()
        
        return [
            HistoryEntry(
                id=row["id"],
                symbol=row["symbol"],
                decision=row["decision"],
                confidence=row["confidence"],
                conflict=bool(row["conflict"]),
                explanation=row["explanation"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
    finally:
        conn.close()


def get_all_history(limit: int = 100) -> List[HistoryEntry]:
    """Retrieve all decision history across all symbols."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, symbol, decision, confidence, conflict, explanation, timestamp
            FROM decision_history
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        
        return [
            HistoryEntry(
                id=row["id"],
                symbol=row["symbol"],
                decision=row["decision"],
                confidence=row["confidence"],
                conflict=bool(row["conflict"]),
                explanation=row["explanation"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
    finally:
        conn.close()
