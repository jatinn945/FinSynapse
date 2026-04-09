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

// ═══════════════════════════════════════════════════════════════
// EXTENSIONS – Stock Dropdown Picker
// ═══════════════════════════════════════════════════════════════

(function initStockDropdown() {
    const toggleBtn = document.getElementById('stock-dropdown-toggle');
    const menu = document.getElementById('stock-dropdown-menu');
    const search = document.getElementById('stock-dropdown-search');
    const list = document.getElementById('stock-dropdown-list');

    if (!toggleBtn || !menu) return;

    let stockData = null;

    // Fetch stock list from API
    async function loadStockList() {
        try {
            const res = await fetch(`${API_BASE}/stocks`);
            if (!res.ok) return;
            stockData = await res.json();
            renderStockList('');
        } catch (e) {
            console.warn('Stock list fetch failed, using fallback');
            stockData = {
                stocks: {
                    "US Stocks": [
                        { symbol: "AAPL", name: "Apple Inc.", category: "US" },
                        { symbol: "TSLA", name: "Tesla Inc.", category: "US" },
                        { symbol: "MSFT", name: "Microsoft Corp.", category: "US" },
                        { symbol: "NVDA", name: "NVIDIA Corp.", category: "US" },
                        { symbol: "AMZN", name: "Amazon.com Inc.", category: "US" },
                        { symbol: "META", name: "Meta Platforms Inc.", category: "US" },
                        { symbol: "GOOGL", name: "Alphabet Inc.", category: "US" },
                        { symbol: "AMD", name: "Advanced Micro Devices", category: "US" },
                        { symbol: "NFLX", name: "Netflix Inc.", category: "US" },
                        { symbol: "JPM", name: "JPMorgan Chase & Co.", category: "US" },
                    ],
                    "Indian Stocks": [
                        { symbol: "RELIANCE.NS", name: "Reliance Industries", category: "India" },
                        { symbol: "TCS.NS", name: "Tata Consultancy Services", category: "India" },
                        { symbol: "HDFCBANK.NS", name: "HDFC Bank", category: "India" },
                        { symbol: "INFY.NS", name: "Infosys", category: "India" },
                        { symbol: "ICICIBANK.NS", name: "ICICI Bank", category: "India" },
                        { symbol: "SBIN.NS", name: "State Bank of India", category: "India" },
                        { symbol: "LT.NS", name: "Larsen & Toubro", category: "India" },
                        { symbol: "ITC.NS", name: "ITC Ltd.", category: "India" },
                    ],
                    "Indices": [
                        { symbol: "^NSEI", name: "Nifty 50", category: "Index" },
                        { symbol: "^NSEBANK", name: "Nifty Bank", category: "Index" },
                        { symbol: "^GSPC", name: "S&P 500", category: "Index" },
                        { symbol: "^IXIC", name: "NASDAQ Composite", category: "Index" },
                    ],
                }
            };
            renderStockList('');
        }
    }

    function renderStockList(filter) {
        if (!stockData || !stockData.stocks) return;
        list.innerHTML = '';

        const f = filter.toLowerCase();

        Object.entries(stockData.stocks).forEach(([category, stocks]) => {
            const filtered = stocks.filter(s =>
                s.symbol.toLowerCase().includes(f) || s.name.toLowerCase().includes(f)
            );
            if (filtered.length === 0) return;

            const catEl = document.createElement('div');
            catEl.className = 'stock-dropdown-category';
            catEl.textContent = category;
            list.appendChild(catEl);

            filtered.forEach(stock => {
                const item = document.createElement('div');
                item.className = 'stock-dropdown-item';
                const badgeCls = stock.category === 'US' ? 'us' : stock.category === 'India' ? 'india' : 'index';
                item.innerHTML = `
                    <div>
                        <span class="stock-dropdown-item-symbol">${escapeHtml(stock.symbol)}</span>
                        <span class="stock-dropdown-item-badge ${badgeCls}">${stock.category.toUpperCase()}</span>
                    </div>
                    <span class="stock-dropdown-item-name">${escapeHtml(stock.name)}</span>
                `;
                item.addEventListener('click', () => {
                    symbolInput.value = stock.symbol;
                    closeDropdown();
                    runAnalysis();
                });
                list.appendChild(item);
            });
        });
    }

    function openDropdown() {
        menu.classList.remove('hidden');
        toggleBtn.classList.add('open');
        search.value = '';
        search.focus();
        renderStockList('');
    }

    function closeDropdown() {
        menu.classList.add('hidden');
        toggleBtn.classList.remove('open');
    }

    toggleBtn.addEventListener('click', () => {
        if (menu.classList.contains('hidden')) {
            openDropdown();
        } else {
            closeDropdown();
        }
    });

    search.addEventListener('input', () => {
        renderStockList(search.value.trim());
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        const container = document.getElementById('stock-dropdown-container');
        if (container && !container.contains(e.target)) {
            closeDropdown();
        }
    });

    loadStockList();
})();


// ═══════════════════════════════════════════════════════════════
// EXTENSIONS – Benchmark Comparison
// ═══════════════════════════════════════════════════════════════

(function initBenchmark() {
    const runBtn = document.getElementById('bench-run-btn');
    if (!runBtn) return;

    let benchChart = null;

    runBtn.addEventListener('click', runBenchmark);

    async function runBenchmark() {
        const symbol = document.getElementById('bench-symbol').value.trim().toUpperCase();
        const benchmark = document.getElementById('bench-index').value;

        if (!symbol) return;

        document.getElementById('bench-results').classList.add('hidden');
        document.getElementById('bench-loading').classList.remove('hidden');
        runBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/benchmark/${symbol}?benchmark=${encodeURIComponent(benchmark)}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            await sleep(400);

            document.getElementById('bench-loading').classList.add('hidden');
            document.getElementById('bench-results').classList.remove('hidden');

            renderBenchmark(data);

        } catch (err) {
            console.error('Benchmark failed:', err);
            document.getElementById('bench-loading').classList.add('hidden');
            alert('Benchmark comparison failed. Please check the symbols and try again.');
        } finally {
            runBtn.disabled = false;
        }
    }

    function renderBenchmark(data) {
        // Stock return
        const stockReturnEl = document.getElementById('bench-stock-return');
        stockReturnEl.textContent = `${data.stock_return_pct >= 0 ? '+' : ''}${data.stock_return_pct.toFixed(2)}%`;
        stockReturnEl.className = `bench-hero-value ${data.stock_return_pct >= 0 ? 'positive' : 'negative'}`;
        document.getElementById('bench-stock-name').textContent = data.stock_name || data.symbol;

        // Benchmark return
        const benchReturnEl = document.getElementById('bench-index-return');
        benchReturnEl.textContent = `${data.benchmark_return_pct >= 0 ? '+' : ''}${data.benchmark_return_pct.toFixed(2)}%`;
        benchReturnEl.className = `bench-hero-value ${data.benchmark_return_pct >= 0 ? 'positive' : 'negative'}`;
        document.getElementById('bench-index-name').textContent = data.benchmark_name || data.benchmark;

        // Alpha
        const alphaEl = document.getElementById('bench-alpha');
        alphaEl.textContent = `${data.alpha >= 0 ? '+' : ''}${data.alpha.toFixed(2)}%`;
        alphaEl.className = `bench-hero-value ${data.alpha >= 0 ? 'positive' : 'negative'}`;
        document.getElementById('bench-alpha-verdict').textContent =
            data.outperforming ? '🟢 Outperforming Benchmark' : '🔴 Underperforming Benchmark';

        // Chart
        renderBenchChart(data);

        // Summary
        document.getElementById('bench-summary-text').textContent = data.summary || '';
    }

    function renderBenchChart(data) {
        const ctx = document.getElementById('bench-chart');
        if (!ctx) return;

        if (benchChart) benchChart.destroy();

        const labels = (data.dates || []).map(d => {
            const date = new Date(d);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        benchChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: data.stock_name || data.symbol,
                        data: data.stock_normalized || [],
                        borderColor: '#2563EB',
                        borderWidth: 2.5,
                        tension: 0.35,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        fill: false,
                    },
                    {
                        label: data.benchmark_name || data.benchmark,
                        data: data.benchmark_normalized || [],
                        borderColor: '#94A3B8',
                        borderWidth: 2,
                        borderDash: [6, 4],
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
                            label: (c) => `${c.dataset.label}: ${c.parsed.y.toFixed(2)}`
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
                            callback: (v) => v.toFixed(1),
                        },
                        border: { display: false },
                    }
                }
            }
        });
    }
})();


// ═══════════════════════════════════════════════════════════════
// EXTENSIONS – AI Chat
// ═══════════════════════════════════════════════════════════════

(function initChat() {
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const contextValue = document.getElementById('chat-context-value');

    if (!chatInput || !chatSendBtn) return;

    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Update chat context whenever analysis is run
    const _origRunAnalysis = window.runAnalysis || null;

    // We rely on state.lastAnalysis which is set by the existing runAnalysis function
    function getChatContext() {
        const analysis = state.lastAnalysis;
        if (!analysis) return null;
        return {
            symbol: analysis.symbol || analysis.stock_data?.symbol || '',
            decision: analysis.decision || '',
            sentiment: analysis.sentiment?.label || '',
            risk: analysis.risk?.risk_level || '',
            confidence: analysis.confidence || 0,
            stock_price: analysis.stock_data?.current_price || 0,
        };
    }

    // Periodically check and update context bar
    setInterval(() => {
        const ctx = getChatContext();
        if (ctx && contextValue) {
            contextValue.textContent = `${ctx.symbol} | ${ctx.decision} (${ctx.confidence.toFixed(1)}%) | Sentiment: ${ctx.sentiment} | Risk: ${ctx.risk}`;
        }
    }, 2000);

    async function sendChatMessage() {
        const question = chatInput.value.trim();
        if (!question) return;

        // Add user message
        addMessage('user', question);
        chatInput.value = '';
        chatSendBtn.disabled = true;

        // Show typing indicator
        const typingEl = addTypingIndicator();

        try {
            const ctx = getChatContext() || {};
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    symbol: ctx.symbol || '',
                    decision: ctx.decision || '',
                    sentiment: ctx.sentiment || '',
                    risk: ctx.risk || '',
                    confidence: ctx.confidence || 0,
                    stock_price: ctx.stock_price || 0,
                }),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            // Remove typing indicator
            typingEl.remove();

            // Add bot response
            addMessage('bot', data.answer || 'Sorry, I couldn\'t generate a response.');

        } catch (err) {
            console.error('Chat failed:', err);
            typingEl.remove();
            addMessage('bot', 'I\'m having trouble reaching the AI service right now. Please try again in a moment.');
        } finally {
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    }

    function addMessage(role, text) {
        const msg = document.createElement('div');
        msg.className = `chat-message ${role}`;

        const avatarHtml = role === 'bot'
            ? `<div class="chat-avatar bot-avatar"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect width="20" height="20" rx="6" fill="#2563EB"/><path d="M6 14V10L10 8L14 10V14" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="10" cy="10" r="1.5" fill="white"/></svg></div>`
            : `<div class="chat-avatar user-avatar-chat">YOU</div>`;

        const senderText = role === 'bot' ? 'FinSynapse AI' : 'You';

        msg.innerHTML = `
            ${avatarHtml}
            <div class="chat-bubble">
                <div class="chat-sender">${senderText}</div>
                <div class="chat-text">${escapeHtml(text)}</div>
            </div>
        `;

        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addTypingIndicator() {
        const msg = document.createElement('div');
        msg.className = 'chat-message bot';
        msg.innerHTML = `
            <div class="chat-avatar bot-avatar"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect width="20" height="20" rx="6" fill="#2563EB"/><path d="M6 14V10L10 8L14 10V14" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="10" cy="10" r="1.5" fill="white"/></svg></div>
            <div class="chat-bubble">
                <div class="chat-sender">FinSynapse AI</div>
                <div class="chat-typing-indicator"><span></span><span></span><span></span></div>
            </div>
        `;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msg;
    }
})();

console.log('FinSynapse Extensions loaded: Benchmark, AI Chat, Stock Picker');


// ═══════════════════════════════════════════════════════════════
// EXTENSIONS – Portfolio Intelligence Hub
// ═══════════════════════════════════════════════════════════════

(function initPortfolio() {
    const runBtn = document.getElementById('portfolio-run-btn');
    const inputEl = document.getElementById('portfolio-input');

    if (!runBtn || !inputEl) return;

    // Run button
    runBtn.addEventListener('click', runPortfolioAnalysis);

    // Enter key
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') runPortfolioAnalysis();
    });

    // Preset buttons
    document.querySelectorAll('.portfolio-preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            inputEl.value = btn.dataset.symbols;
            runPortfolioAnalysis();
        });
    });

    async function runPortfolioAnalysis() {
        const raw = inputEl.value.trim();
        if (!raw) { inputEl.focus(); return; }

        const symbols = raw.split(',').map(s => s.trim().toUpperCase()).filter(Boolean);

        if (symbols.length < 2) {
            alert('Please enter at least 2 stock symbols, separated by commas.');
            return;
        }
        if (symbols.length > 10) {
            alert('Maximum 10 symbols allowed.');
            return;
        }

        // Show loading
        document.getElementById('portfolio-results').classList.add('hidden');
        document.getElementById('portfolio-loading').classList.remove('hidden');
        document.getElementById('portfolio-loading-progress').textContent =
            `Analyzing ${symbols.length} stocks: ${symbols.join(', ')}...`;
        runBtn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/portfolio/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbols }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            await sleep(400);

            document.getElementById('portfolio-loading').classList.add('hidden');
            document.getElementById('portfolio-results').classList.remove('hidden');

            renderPortfolio(data);

        } catch (err) {
            console.error('Portfolio analysis failed:', err);
            document.getElementById('portfolio-loading').classList.add('hidden');
            alert(`Portfolio analysis failed: ${err.message}`);
        } finally {
            runBtn.disabled = false;
        }
    }

    function renderPortfolio(data) {
        // ── Hero Stats ──
        const divScoreEl = document.getElementById('portfolio-div-score');
        animateNumber(divScoreEl, 0, data.diversification_score || 0, '');
        document.getElementById('portfolio-div-grade').textContent = data.diversification_grade || '—';

        // Risk
        const riskEl = document.getElementById('portfolio-risk');
        riskEl.textContent = data.overall_risk || '—';
        riskEl.style.color = getRiskColor(data.overall_risk);

        document.getElementById('portfolio-confidence').textContent =
            `Avg Confidence: ${data.avg_confidence || 0}%`;

        // Signal pills
        document.getElementById('portfolio-signal-pills').innerHTML = `
            <span class="signal-pill buy">${data.buy_count || 0} BUY</span>
            <span class="signal-pill sell">${data.sell_count || 0} SELL</span>
            <span class="signal-pill hold">${data.hold_count || 0} HOLD</span>
        `;

        // ── Risk Heatmap ──
        renderRiskHeatmap(data.risk_heatmap || []);

        // ── Sectors ──
        renderSectors(data.sectors || []);

        // ── Correlation Matrix ──
        renderCorrelationMatrix(data.correlation_matrix || {});

        // ── Holdings Table ──
        renderHoldingsTable(data.holdings || []);

        // ── Conflicts ──
        renderConflicts(data.conflicts || []);

        // ── Summary ──
        document.getElementById('portfolio-summary-text').textContent = data.summary || '';
    }

    function renderRiskHeatmap(heatmap) {
        const container = document.getElementById('portfolio-risk-heatmap');
        container.innerHTML = '';

        heatmap.forEach((item, idx) => {
            const el = document.createElement('div');
            el.className = 'risk-heatmap-item';
            el.style.background = hexToRgba(item.color, 0.1);
            el.style.borderColor = hexToRgba(item.color, 0.3);
            el.style.animationDelay = `${idx * 0.05}s`;

            el.innerHTML = `
                <div class="risk-heatmap-symbol">${escapeHtml(item.symbol)}</div>
                <div class="risk-heatmap-volatility" style="color:${item.color}">${item.volatility.toFixed(1)}%</div>
                <div class="risk-heatmap-level" style="color:${item.color}">${item.risk_level}</div>
                <div class="risk-heatmap-drawdown">Drawdown: ${item.max_drawdown.toFixed(1)}%</div>
            `;
            // The top bar
            el.style.setProperty('--heatmap-color', item.color);
            el.querySelector('.risk-heatmap-volatility').parentElement.insertAdjacentHTML(
                'afterbegin', `<div style="position:absolute;top:0;left:0;right:0;height:4px;background:${item.color};border-radius:12px 12px 0 0;"></div>`
            );

            container.appendChild(el);
        });
    }

    function renderSectors(sectors) {
        const container = document.getElementById('portfolio-sector-list');
        container.innerHTML = '';

        const colors = ['#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#818CF8'];

        sectors.forEach((sector, idx) => {
            const color = colors[idx % colors.length];
            const el = document.createElement('div');
            el.className = 'sector-item';
            el.innerHTML = `
                <div class="sector-bar-container">
                    <div class="sector-bar-header">
                        <span class="sector-name">${escapeHtml(sector.sector)}</span>
                        <span class="sector-pct" style="color:${color}">${sector.percentage.toFixed(0)}%</span>
                    </div>
                    <div class="sector-symbols">${sector.symbols.join(', ')}</div>
                    <div class="sector-bar-track">
                        <div class="sector-bar-fill" style="width:${sector.percentage}%;background:${color}"></div>
                    </div>
                </div>
            `;
            container.appendChild(el);
        });
    }

    function renderCorrelationMatrix(matrix) {
        const container = document.getElementById('portfolio-corr-matrix');
        container.innerHTML = '';

        const labels = matrix.labels || [];
        const values = matrix.values || [];
        const n = labels.length;

        if (n === 0) return;

        // Grid: (n+1) columns — header col + data cols
        container.style.gridTemplateColumns = `repeat(${n + 1}, 1fr)`;

        // Top-left empty cell
        const emptyCell = document.createElement('div');
        emptyCell.className = 'corr-cell header';
        emptyCell.textContent = '';
        container.appendChild(emptyCell);

        // Header row
        labels.forEach(label => {
            const cell = document.createElement('div');
            cell.className = 'corr-cell header';
            cell.textContent = label;
            container.appendChild(cell);
        });

        // Data rows
        for (let i = 0; i < n; i++) {
            // Row header
            const rowHeader = document.createElement('div');
            rowHeader.className = 'corr-cell header';
            rowHeader.textContent = labels[i];
            container.appendChild(rowHeader);

            // Data cells
            for (let j = 0; j < n; j++) {
                const val = values[i] ? values[i][j] : 0;
                const cell = document.createElement('div');

                if (i === j) {
                    cell.className = 'corr-cell diagonal';
                    cell.textContent = '1.00';
                } else {
                    cell.className = 'corr-cell';
                    cell.textContent = val.toFixed(2);
                    const absVal = Math.abs(val);
                    cell.style.background = getCorrColor(absVal);
                    cell.style.color = absVal > 0.5 ? 'white' : 'var(--text-primary)';
                }

                container.appendChild(cell);
            }
        }
    }

    function renderHoldingsTable(holdings) {
        const tbody = document.getElementById('portfolio-table-body');
        tbody.innerHTML = '';

        holdings.forEach(h => {
            const changeCls = h.change_pct >= 0 ? 'positive' : 'negative';
            const decType = h.decision.toLowerCase();

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <strong>${escapeHtml(h.symbol)}</strong>
                    <div style="font-size:0.72rem;color:var(--text-tertiary)">${escapeHtml(h.company_name || '')}</div>
                </td>
                <td>$${h.price.toFixed(2)}</td>
                <td class="table-change ${changeCls}">${h.change_pct >= 0 ? '+' : ''}${h.change_pct.toFixed(2)}%</td>
                <td><span class="table-badge ${decType}">${h.decision}</span></td>
                <td>${h.confidence.toFixed(1)}%</td>
                <td>${escapeHtml(h.sentiment)}</td>
                <td>${escapeHtml(h.risk_level)}</td>
                <td>${h.volatility.toFixed(1)}%</td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderConflicts(conflicts) {
        const wrapper = document.getElementById('portfolio-conflicts');
        const list = document.getElementById('portfolio-conflicts-list');

        if (conflicts.length === 0) {
            wrapper.classList.add('hidden');
            return;
        }

        wrapper.classList.remove('hidden');
        list.innerHTML = '';

        conflicts.forEach(c => {
            const el = document.createElement('div');
            el.className = 'conflict-item';
            el.innerHTML = `
                <span class="conflict-symbol">${escapeHtml(c.symbol)}</span>
                <span class="conflict-detail">${escapeHtml(c.details)} (Decision: ${c.decision} at ${c.confidence}%)</span>
            `;
            list.appendChild(el);
        });
    }

    // ── Utility ──

    function getRiskColor(level) {
        const map = {
            'Low': 'var(--buy)',
            'Moderate': 'var(--hold)',
            'High': 'var(--sell)',
            'Very High': '#991B1B',
        };
        return map[level] || 'var(--text-primary)';
    }

    function getCorrColor(absVal) {
        if (absVal >= 0.7) return 'rgba(220, 38, 38, 0.7)';   // red — high
        if (absVal >= 0.4) return 'rgba(217, 119, 6, 0.5)';    // amber — medium
        if (absVal >= 0.2) return 'rgba(217, 119, 6, 0.2)';    // light amber
        return 'rgba(5, 150, 105, 0.15)';                       // green — low
    }

    function hexToRgba(hex, alpha) {
        if (!hex || hex.charAt(0) !== '#') return `rgba(148,163,184,${alpha})`;
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r},${g},${b},${alpha})`;
    }
})();

console.log('FinSynapse Portfolio Intelligence Hub loaded.');
