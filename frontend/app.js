/**
 * FinSynapse – Frontend Application
 * Multi-Agent Financial Decision Engine
 * 
 * Handles all UI interactions, API calls, chart rendering,
 * and page navigation.
 */

// ═══════════════════════════════════════════════════════════════
// CONFIG & STATE
// ═══════════════════════════════════════════════════════════════

const API_BASE = window.location.origin + '/api';

const state = {
    currentPage: 'dashboard',
    lastAnalysis: null,
    priceChart: null,
    simChart: null,
};

// ═══════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════

function navigateTo(page) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const activeLink = document.querySelector(`[data-page="${page}"]`);
    if (activeLink) activeLink.classList.add('active');

    // Update pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const activePage = document.getElementById(`page-${page}`);
    if (activePage) activePage.classList.add('active');

    state.currentPage = page;

    // Auto-load timeline data when navigating to timeline
    if (page === 'timeline') {
        loadTimeline();
    }
}

// Navigation event listeners
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(link.dataset.page);
    });
});

// ═══════════════════════════════════════════════════════════════
// DASHBOARD – STOCK ANALYSIS
// ═══════════════════════════════════════════════════════════════

const analyzeBtn = document.getElementById('analyze-btn');
const symbolInput = document.getElementById('stock-symbol-input');
const loadingState = document.getElementById('loading-state');
const dashboardResults = document.getElementById('dashboard-results');
const headerBtn = document.getElementById('analyze-header-btn');

// Quick picks
document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        symbolInput.value = btn.dataset.symbol;
        runAnalysis();
    });
});

// Analyze button
analyzeBtn.addEventListener('click', runAnalysis);

// Header analyze button
headerBtn.addEventListener('click', () => {
    navigateTo('dashboard');
    symbolInput.focus();
});

// Enter key on input
symbolInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') runAnalysis();
});

// Global search
document.getElementById('global-search').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const val = e.target.value.trim().toUpperCase();
        if (val) {
            symbolInput.value = val;
            navigateTo('dashboard');
            runAnalysis();
            e.target.value = '';
        }
    }
});

async function runAnalysis() {
    const symbol = symbolInput.value.trim().toUpperCase();
    if (!symbol) {
        symbolInput.focus();
        return;
    }

    // Show loading
    dashboardResults.classList.add('hidden');
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;

    // Animate agent statuses
    animateAgents();

    try {
        const res = await fetch(`${API_BASE}/analyze/${symbol}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        state.lastAnalysis = data;

        // Small delay so the user sees the agent animation complete
        await sleep(600);

        // Hide loading, show results
        loadingState.classList.add('hidden');
        dashboardResults.classList.remove('hidden');

        renderDashboard(data);
        updateAnalysisPage(data);

    } catch (err) {
        console.error('Analysis failed:', err);
        loadingState.classList.add('hidden');
        alert(`Analysis failed for "${symbol}". Please check the symbol and try again.`);
    } finally {
        analyzeBtn.disabled = false;
        resetAgentStatus();
    }
}

function animateAgents() {
    const agents = ['agent-data', 'agent-news', 'agent-sentiment', 'agent-risk', 'agent-engine'];
    agents.forEach((id, i) => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) el.classList.add('active');
        }, i * 400);
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.remove('active');
                el.classList.add('done');
            }
        }, (i + 1) * 400 + 200);
    });
}

function resetAgentStatus() {
    ['agent-data', 'agent-news', 'agent-sentiment', 'agent-risk', 'agent-engine'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('active', 'done');
        }
    });
}

// ═══════════════════════════════════════════════════════════════
// RENDER DASHBOARD
// ═══════════════════════════════════════════════════════════════

function renderDashboard(data) {
    // Title
    document.getElementById('dashboard-title').textContent =
        `${data.stock_data?.symbol || ''} ${data.stock_data?.company_name || ''}`;

    // Hero card
    const price = data.stock_data?.current_price || 0;
    const change = data.stock_data?.change_percent || 0;

    document.getElementById('hero-price').textContent = `$${price.toFixed(2)}`;

    const changeEl = document.getElementById('hero-change');
    changeEl.className = `hero-change ${change >= 0 ? 'positive' : 'negative'}`;
    changeEl.querySelector('.change-arrow').textContent = change >= 0 ? '↑' : '↓';
    document.getElementById('hero-change-value').textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;

    // Decision badge
    const badge = document.getElementById('decision-badge');
    badge.textContent = data.decision;
    badge.className = `decision-badge ${data.decision.toLowerCase()}`;

    // Confidence
    const confEl = document.getElementById('confidence-value');
    animateNumber(confEl, 0, data.confidence, '%');

    // Metric cards
    renderMetrics(data);

    // Chart
    renderPriceChart(data.stock_data?.prices || []);

    // Signals
    renderSignals(data.signal_details || []);

    // AI Summary
    renderAISummary(data);

    // News
    renderNews(data.news);

    // Explanation
    document.getElementById('explanation-text').textContent = data.explanation || '';
}

function renderMetrics(data) {
    // Sentiment
    const sentiment = data.sentiment;
    if (sentiment) {
        document.getElementById('sentiment-value').textContent = sentiment.label;
        document.getElementById('sentiment-score').textContent = `Score: ${sentiment.score.toFixed(3)}`;

        const bar = document.getElementById('sentiment-bar');
        const pct = ((sentiment.score + 1) / 2) * 100; // -1..1 → 0..100
        bar.style.width = `${pct}%`;

        if (sentiment.score > 0.05) {
            bar.style.background = 'var(--buy)';
        } else if (sentiment.score < -0.05) {
            bar.style.background = 'var(--sell)';
        } else {
            bar.style.background = 'var(--hold)';
        }
    }

    // Risk
    const risk = data.risk;
    if (risk) {
        document.getElementById('risk-value').textContent = risk.risk_level;
        document.getElementById('risk-volatility').textContent = `Volatility: ${risk.volatility.toFixed(1)}%`;
        document.getElementById('risk-drawdown').textContent = `Max Drawdown: ${risk.max_drawdown.toFixed(1)}%`;
    }

    // Market data
    const stock = data.stock_data;
    if (stock) {
        document.getElementById('market-cap-value').textContent = stock.market_cap || 'N/A';
        document.getElementById('pe-ratio').textContent = `P/E Ratio: ${stock.pe_ratio ? stock.pe_ratio.toFixed(1) + 'x' : 'N/A'}`;
        document.getElementById('volume-value').textContent = `Volume: ${formatNumber(stock.volume)}`;
    }
}

function renderPriceChart(prices) {
    const ctx = document.getElementById('price-chart');
    if (!ctx) return;

    if (state.priceChart) {
        state.priceChart.destroy();
    }

    const labels = prices.map((_, i) => `Day ${i + 1}`);
    const gradient = ctx.getContext('2d');
    const bg = gradient.createLinearGradient(0, 0, 0, 250);
    bg.addColorStop(0, 'rgba(37, 99, 235, 0.12)');
    bg.addColorStop(1, 'rgba(37, 99, 235, 0.0)');

    state.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Price',
                data: prices,
                borderColor: '#2563EB',
                backgroundColor: bg,
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: '#2563EB',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0F172A',
                    titleFont: { family: "'Inter', sans-serif", weight: '600', size: 12 },
                    bodyFont: { family: "'Inter', sans-serif", size: 12 },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => `$${ctx.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: { display: false },
                    ticks: {
                        font: { family: "'Inter', sans-serif", size: 11 },
                        color: '#94A3B8',
                        maxTicksLimit: 8,
                    },
                    border: { display: false },
                },
                y: {
                    display: true,
                    grid: {
                        color: '#F1F5F9',
                        drawBorder: false,
                    },
                    ticks: {
                        font: { family: "'Inter', sans-serif", size: 11 },
                        color: '#94A3B8',
                        callback: (v) => `$${v.toFixed(0)}`,
                    },
                    border: { display: false },
                }
            }
        }
    });
}

function renderSignals(signals) {
    const list = document.getElementById('signals-list');
    list.innerHTML = '';

    signals.forEach(signal => {
        const type = signal.signal.toLowerCase();
        const item = document.createElement('div');
        item.className = 'signal-item';
        item.innerHTML = `
            <div class="signal-dot ${type}"></div>
            <div class="signal-agent">${escapeHtml(signal.agent)}</div>
            <span class="signal-tag ${type}">${signal.signal}</span>
            <span class="signal-strength">${Math.round(signal.strength * 100)}%</span>
        `;
        list.appendChild(item);
    });
}

function renderAISummary(data) {
    const stock = data.stock_data;
    const sentiment = data.sentiment;
    const risk = data.risk;

    // Generate a clean summary text
    let summaryParts = [];

    if (stock) {
        summaryParts.push(`${stock.company_name} is currently trading at $${stock.current_price.toFixed(2)} (${stock.change_percent >= 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%).`);
    }

    if (sentiment) {
        summaryParts.push(`Market sentiment is ${sentiment.label.toLowerCase()} with a score of ${sentiment.score.toFixed(3)}.`);
    }

    if (risk) {
        summaryParts.push(`Risk assessment indicates ${risk.risk_level.toLowerCase()} risk with ${risk.volatility.toFixed(1)}% volatility.`);
    }

    if (data.conflict) {
        summaryParts.push(`⚠ Conflict detected between agent signals — exercise caution.`);
    }

    summaryParts.push(`The decision engine recommends ${data.decision} with ${data.confidence.toFixed(1)}% confidence.`);

    document.getElementById('ai-summary-text').textContent = summaryParts.join(' ');

    // AI Metrics
    const metricsEl = document.getElementById('ai-metrics');
    metricsEl.innerHTML = '';

    if (risk) {
        addAIMetric(metricsEl, 'VOLATILITY', `${risk.volatility.toFixed(1)}%`);
        if (risk.sharpe_estimate) addAIMetric(metricsEl, 'SHARPE', risk.sharpe_estimate.toFixed(2));
        addAIMetric(metricsEl, 'DRAWDOWN', `${risk.max_drawdown.toFixed(1)}%`);
    }
}

function addAIMetric(container, label, value) {
    const div = document.createElement('div');
    div.className = 'ai-metric';
    div.innerHTML = `
        <span class="ai-metric-label">${label}</span>
        <span class="ai-metric-value">${value}</span>
    `;
    container.appendChild(div);
}

function renderNews(news) {
    const list = document.getElementById('news-list');
    list.innerHTML = '';

    if (!news || !news.items || news.items.length === 0) {
        list.innerHTML = '<div class="news-item">No news found for this symbol.</div>';
        return;
    }

    // Use headline_scores from sentiment if available
    const sentimentData = state.lastAnalysis?.sentiment?.headline_scores || [];

    news.items.forEach((item, idx) => {
        const scoreData = sentimentData[idx] || {};
        const polarity = scoreData.polarity || item.sentiment_score || 0;
        const sentLabel = polarity > 0.05 ? 'positive' : polarity < -0.05 ? 'negative' : 'neutral';
        const sentText = polarity > 0.05 ? 'Bullish' : polarity < -0.05 ? 'Bearish' : 'Neutral';

        const el = document.createElement('div');
        el.className = `news-item ${idx === 0 ? 'top-impact' : ''}`;
        el.innerHTML = `
            <div class="news-source">${escapeHtml(item.source || 'Market News')}${idx === 0 ? ' · TOP IMPACT' : ''}</div>
            <div class="news-title">${escapeHtml(item.title)}</div>
            <span class="news-sentiment ${sentLabel}">● ${sentText} (${polarity.toFixed(3)})</span>
        `;
        list.appendChild(el);
    });
}

// ═══════════════════════════════════════════════════════════════
// ANALYSIS PAGE
// ═══════════════════════════════════════════════════════════════

function updateAnalysisPage(data) {
    const content = document.getElementById('analysis-content');
    const prompt = document.querySelector('.analysis-prompt');

    if (!data) return;

    prompt.classList.add('hidden');
    content.classList.remove('hidden');

    // Sentiment score (scale to 0-100)
    const sentScore = data.sentiment ? Math.round(((data.sentiment.score + 1) / 2) * 100) : 50;
    const sentLabel = data.sentiment?.label || 'Neutral';
    document.getElementById('analysis-sentiment-score').textContent = sentScore;

    const labelEl = document.getElementById('analysis-sentiment-label');
    labelEl.textContent = sentLabel.toUpperCase();

    if (sentScore > 60) {
        labelEl.style.color = 'var(--buy)';
    } else if (sentScore < 40) {
        labelEl.style.color = 'var(--sell)';
    } else {
        labelEl.style.color = 'var(--hold)';
    }

    // Sentiment bar segments
    const fear = Math.max(5, 50 - sentScore);
    const neutral = 20;
    const greed = Math.max(5, sentScore - 30);
    document.querySelector('.bar-segment.fear').style.flex = fear;
    document.querySelector('.bar-segment.neutral').style.flex = neutral;
    document.querySelector('.bar-segment.greed').style.flex = greed;

    // Risk gauge
    const risk = data.risk;
    if (risk) {
        document.getElementById('analysis-risk-label').textContent = risk.risk_level;
        const gauge = document.querySelector('.gauge-fill');
        const riskPct = Math.min(100, risk.volatility * 2.5);
        gauge.style.borderTopColor = riskPct > 60 ? 'var(--sell)' : riskPct > 30 ? 'var(--hold)' : 'var(--buy)';
        gauge.style.transform = `rotate(${riskPct * 1.8}deg)`;
    }

    // Headline ranking
    const ranking = document.getElementById('headline-ranking');
    ranking.innerHTML = '';

    const headlineScores = data.sentiment?.headline_scores || [];
    headlineScores.forEach(hs => {
        const pol = hs.polarity || 0;
        const cls = pol > 0.05 ? 'positive' : pol < -0.05 ? 'negative' : 'neutral';
        const el = document.createElement('div');
        el.className = 'headline-rank-item';
        el.innerHTML = `
            <span class="rank-score ${cls}">${pol >= 0 ? '+' : ''}${pol.toFixed(2)}</span>
            <span class="rank-text">${escapeHtml(hs.headline)}</span>
        `;
        ranking.appendChild(el);
    });
}

// ═══════════════════════════════════════════════════════════════
// SIMULATION
// ═══════════════════════════════════════════════════════════════

const simSlider = document.getElementById('sim-slider');
const simSliderValue = document.getElementById('sim-slider-value');
const simRunBtn = document.getElementById('sim-run-btn');

simSlider.addEventListener('input', () => {
    const val = parseFloat(simSlider.value);
    simSliderValue.textContent = `${val >= 0 ? '+' : ''}${val.toFixed(1)}%`;
    simSliderValue.style.color = val >= 0 ? 'var(--buy)' : 'var(--sell)';
});

simRunBtn.addEventListener('click', runSimulation);

async function runSimulation() {
    const symbol = document.getElementById('sim-symbol').value.trim().toUpperCase();
    const change = parseFloat(simSlider.value);

    if (!symbol) return;

    document.getElementById('sim-results').classList.add('hidden');
    document.getElementById('sim-loading').classList.remove('hidden');
    simRunBtn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/simulate/${symbol}?change=${change}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        await sleep(500);

        document.getElementById('sim-loading').classList.add('hidden');
        document.getElementById('sim-results').classList.remove('hidden');

        renderSimulation(data);

    } catch (err) {
        console.error('Simulation failed:', err);
        document.getElementById('sim-loading').classList.add('hidden');
        alert('Simulation failed. Please try again.');
    } finally {
        simRunBtn.disabled = false;
    }
}

function renderSimulation(data) {
    // Verdict
    const decEl = document.getElementById('sim-decision');
    decEl.textContent = data.simulated.decision;
    decEl.className = `verdict-decision ${data.simulated.decision.toLowerCase()}`;

    document.getElementById('sim-confidence').textContent =
        `Confidence: ${data.simulated.confidence.toFixed(1)}% | Original: ${data.original.decision} (${data.original.confidence.toFixed(1)}%)`;

    // Chart
    renderSimChart(data);

    // Metrics
    const metricsRow = document.getElementById('sim-metrics-row');
    metricsRow.innerHTML = '';

    const origRisk = data.original.risk;
    const simRisk = data.simulated.risk;

    addSimMetric(metricsRow, 'PRICE CHANGE', `${data.price_change_percent >= 0 ? '+' : ''}${data.price_change_percent.toFixed(1)}%`);
    addSimMetric(metricsRow, 'RISK SHIFT', origRisk && simRisk ? `${origRisk.risk_level} → ${simRisk.risk_level}` : 'N/A');
    addSimMetric(metricsRow, 'CONFIDENCE DELTA',
        `${(data.simulated.confidence - data.original.confidence) >= 0 ? '+' : ''}${(data.simulated.confidence - data.original.confidence).toFixed(1)}%`);

    // Impact text
    document.getElementById('sim-impact-text').textContent = data.impact_summary || '';
}

function renderSimChart(data) {
    const ctx = document.getElementById('sim-chart');
    if (!ctx) return;

    if (state.simChart) state.simChart.destroy();

    const origPrices = data.original.stock_data?.prices || [];
    const simPrices = data.simulated.stock_data?.prices || [];
    const labels = origPrices.map((_, i) => `Day ${i + 1}`);

    state.simChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Baseline',
                    data: origPrices,
                    borderColor: '#94A3B8',
                    borderWidth: 2,
                    borderDash: [6, 4],
                    tension: 0.35,
                    pointRadius: 0,
                    fill: false,
                },
                {
                    label: 'Scenario',
                    data: simPrices,
                    borderColor: '#2563EB',
                    borderWidth: 2.5,
                    tension: 0.35,
                    pointRadius: 0,
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        font: { family: "'Inter', sans-serif", size: 12 },
                        usePointStyle: true,
                        pointStyle: 'circle',
                    }
                },
                tooltip: {
                    backgroundColor: '#0F172A',
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, color: '#94A3B8', maxTicksLimit: 8 },
                    border: { display: false },
                },
                y: {
                    grid: { color: '#F1F5F9' },
                    ticks: {
                        font: { size: 11 },
                        color: '#94A3B8',
                        callback: (v) => `$${v.toFixed(0)}`,
                    },
                    border: { display: false },
                }
            }
        }
    });
}

function addSimMetric(container, label, value) {
    const el = document.createElement('div');
    el.className = 'sim-metric';
    el.innerHTML = `
        <div class="sim-metric-label">${label}</div>
        <div class="sim-metric-value">${value}</div>
    `;
    container.appendChild(el);
}

// ═══════════════════════════════════════════════════════════════
// COMPARISON
// ═══════════════════════════════════════════════════════════════

document.getElementById('compare-btn').addEventListener('click', runComparison);

async function runComparison() {
    const stock1 = document.getElementById('compare-stock1').value.trim().toUpperCase();
    const stock2 = document.getElementById('compare-stock2').value.trim().toUpperCase();

    if (!stock1 || !stock2) return;

    document.getElementById('compare-results').classList.add('hidden');
    document.getElementById('compare-loading').classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/compare?stock1=${stock1}&stock2=${stock2}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        await sleep(500);

        document.getElementById('compare-loading').classList.add('hidden');
        document.getElementById('compare-results').classList.remove('hidden');

        renderComparison(data);

    } catch (err) {
        console.error('Comparison failed:', err);
        document.getElementById('compare-loading').classList.add('hidden');
        alert('Comparison failed. Please try again.');
    }
}

function renderComparison(data) {
    const container = document.getElementById('compare-cards');
    container.innerHTML = '';

    [data.stock1, data.stock2].forEach(result => {
        const stock = result.stock_data;
        const change = stock?.change_percent || 0;
        const changeCls = change >= 0 ? 'positive' : 'negative';
        const decType = result.decision.toLowerCase();

        const card = document.createElement('div');
        card.className = 'compare-card';
        card.innerHTML = `
            <div class="compare-card-header">
                <div>
                    <div class="compare-symbol">${escapeHtml(stock?.symbol || '')}</div>
                    <div style="font-size:0.82rem;color:var(--text-secondary)">${escapeHtml(stock?.company_name || '')}</div>
                </div>
                <div>
                    <div class="compare-price">$${(stock?.current_price || 0).toFixed(2)}</div>
                    <div class="compare-change ${changeCls}">${change >= 0 ? '↑' : '↓'} ${change >= 0 ? '+' : ''}${change.toFixed(2)}%</div>
                </div>
            </div>
            <div class="compare-stats">
                <div class="compare-stat">
                    <span class="compare-stat-label">Market Cap</span>
                    <span class="compare-stat-value">${stock?.market_cap || 'N/A'}</span>
                </div>
                <div class="compare-stat">
                    <span class="compare-stat-label">P/E Ratio</span>
                    <span class="compare-stat-value">${stock?.pe_ratio ? stock.pe_ratio.toFixed(1) + 'x' : 'N/A'}</span>
                </div>
                <div class="compare-stat">
                    <span class="compare-stat-label">Sentiment</span>
                    <span class="compare-stat-value">${result.sentiment?.label || 'N/A'}</span>
                </div>
                <div class="compare-stat">
                    <span class="compare-stat-label">Risk Level</span>
                    <span class="compare-stat-value">${result.risk?.risk_level || 'N/A'}</span>
                </div>
                <div class="compare-stat">
                    <span class="compare-stat-label">Volatility</span>
                    <span class="compare-stat-value">${result.risk?.volatility?.toFixed(1) || '0'}%</span>
                </div>
                <div class="compare-stat">
                    <span class="compare-stat-label">Confidence</span>
                    <span class="compare-stat-value">${result.confidence.toFixed(1)}%</span>
                </div>
            </div>
            <span class="compare-badge ${decType}">${result.decision}</span>
        `;
        container.appendChild(card);
    });

    document.getElementById('compare-summary-text').textContent = data.summary || '';
    document.getElementById('compare-recommendation').textContent = data.recommendation || '';
}

// ═══════════════════════════════════════════════════════════════
// TIMELINE
// ═══════════════════════════════════════════════════════════════

document.getElementById('timeline-load-btn').addEventListener('click', loadTimeline);

async function loadTimeline() {
    const symbol = document.getElementById('timeline-symbol').value.trim().toUpperCase();

    try {
        const url = symbol
            ? `${API_BASE}/history/${symbol}`
            : `${API_BASE}/history`;

        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        renderTimeline(data.entries || []);

    } catch (err) {
        console.error('Timeline load failed:', err);
    }
}

function renderTimeline(entries) {
    const list = document.getElementById('timeline-list');
    list.innerHTML = '';

    if (entries.length === 0) {
        list.innerHTML = `
            <div class="timeline-empty">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="20" stroke="#CBD5E1" stroke-width="2"/><path d="M24 14V26L32 30" stroke="#CBD5E1" stroke-width="2" stroke-linecap="round"/></svg>
                <p>No decisions recorded yet. Analyze a stock to start building your timeline.</p>
            </div>
        `;
        return;
    }

    // Add timeline line
    const line = document.createElement('div');
    line.className = 'timeline-line';
    list.appendChild(line);

    entries.forEach((entry, idx) => {
        const decType = entry.decision.toLowerCase();
        const time = formatTimestamp(entry.timestamp);

        const el = document.createElement('div');
        el.className = 'timeline-entry';
        el.style.animationDelay = `${idx * 0.05}s`;
        el.innerHTML = `
            <div class="timeline-dot ${decType}"></div>
            <div class="timeline-card">
                <div class="timeline-card-header">
                    <div>
                        <span class="timeline-symbol">${escapeHtml(entry.symbol)}</span>
                        <span class="timeline-badge ${decType}">${entry.decision}</span>
                    </div>
                    <span class="timeline-time">${time}</span>
                </div>
                <div class="timeline-confidence">Confidence: ${entry.confidence.toFixed(1)}%</div>
                ${entry.conflict ? '<div class="timeline-conflict">⚠ Conflict Detected</div>' : ''}
            </div>
        `;
        list.appendChild(el);
    });
}

// ═══════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(2)}B`;
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toLocaleString();
}

function formatTimestamp(ts) {
    if (!ts) return '';
    try {
        const date = new Date(ts);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return ts;
    }
}

function animateNumber(element, from, to, suffix = '') {
    const duration = 800;
    const start = performance.now();

    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = from + (to - from) * eased;
        element.textContent = `${current.toFixed(1)}${suffix}`;
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

console.log('FinSynapse – Multi-Agent Financial Decision Engine');
console.log('Ready. Enter a stock symbol to begin analysis.');
