# FinSynapse – Multi-Agent Financial Decision Engine

A production-grade, multi-agent AI system for intelligent financial decision-making with structured reasoning, conflict detection, and explainable AI.

## Architecture

```
User Input → Orchestrator → Agents → Structured Outputs → Decision Engine → Response
```

### Agents
1. **Data Agent** – Fetches real stock data via yfinance
2. **News Agent** – Pulls financial headlines from free RSS feeds
3. **Sentiment Agent** – Analyzes sentiment using TextBlob
4. **Risk Agent** – Calculates volatility and risk metrics using numpy
5. **Simulation Agent** – Models hypothetical price scenarios

### Decision Engine
- Converts agent outputs into directional signals (BUY/SELL/HOLD)
- Detects conflicts between signals
- Computes weighted confidence scores
- Generates structured, explainable reasoning

### Memory Layer
- SQLite-backed persistent storage for decision history

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
python -m textblob.download_corpora
```

### 2. Run the Server
```bash
cd backend
python main.py
```

### 3. Open the App
Navigate to **http://localhost:8000** in your browser.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/analyze/{symbol}` | Full multi-agent analysis |
| `GET /api/simulate/{symbol}?change=5` | What-if simulation |
| `GET /api/compare?stock1=AAPL&stock2=TSLA` | Side-by-side comparison |
| `GET /api/history/{symbol}` | Decision history for a symbol |
| `GET /api/history` | All decision history |
| `GET /api/health` | Health check |

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic, yfinance, TextBlob, numpy
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Database**: SQLite
- **All free** – No paid APIs required
