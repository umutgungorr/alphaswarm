"""Interactive High-Performance Web Dashboard server for AlphaSwarm."""

import http.server
import json
import socketserver
import urllib.parse
from alphaswarm.agents import answer_user_scenario
from alphaswarm.graph import AlphaSwarmGraph
from alphaswarm.market_data import (
    COIN_CATALOGUE,
    STOCK_CATALOGUE,
    get_market_data,
    get_top_assets,
)
from alphaswarm.models import Stance
from alphaswarm.reporters import generate_html_report, generate_markdown_report


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AlphaSwarm ⚡ Otonom Çoklu Ajan Piyasa İstihbarat & Konsensüs Hub</title>
<style>
    :root {
        --bg-main: #070b12;
        --bg-card: #0f172a;
        --bg-card-sub: #1e293b;
        --border-color: #1e293b;
        --border-highlight: #334155;
        --text-primary: #f8fafc;
        --text-muted: #94a3b8;
        --cyan: #38bdf8;
        --green: #10b981;
        --red: #ef4444;
        --yellow: #f59e0b;
        --purple: #a855f7;
    }
    * { box-sizing: border-box; }
    body {
        background: var(--bg-main);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    header {
        background: rgba(15, 23, 42, 0.94);
        backdrop-filter: blur(14px);
        border-bottom: 1px solid var(--border-color);
        padding: 12px 28px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-icon {
        background: linear-gradient(135deg, #0284c7, #38bdf8);
        width: 38px;
        height: 38px;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.35);
    }
    .brand-title { font-size: 20px; font-weight: 900; letter-spacing: -0.5px; }
    
    .nav-actions { display: flex; gap: 12px; align-items: center; }

    /* Live auto refresh toggle */
    .live-stream-btn {
        background: #090d16;
        border: 1px solid var(--border-highlight);
        color: var(--text-muted);
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
    }
    .live-stream-btn.active {
        border-color: var(--green);
        color: var(--green);
        background: rgba(16, 185, 129, 0.1);
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #64748b;
    }
    .live-stream-btn.active .pulse-dot {
        background: var(--green);
        box-shadow: 0 0 8px var(--green);
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.7; }
        50% { transform: scale(1.25); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.7; }
    }

    .lang-toggle {
        display: flex;
        background: #090d16;
        border: 1px solid var(--border-highlight);
        border-radius: 8px;
        overflow: hidden;
    }
    .lang-btn {
        background: transparent;
        border: none;
        color: var(--text-muted);
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s;
    }
    .lang-btn.active { background: var(--cyan); color: #090d16; }

    .container {
        max-width: 1320px;
        margin: 20px auto;
        padding: 0 20px;
    }

    /* Watchlist Quick Bar */
    .watchlist-bar {
        display: flex;
        align-items: center;
        gap: 10px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 8px 16px;
        margin-bottom: 16px;
        overflow-x: auto;
    }
    .watchlist-title {
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: var(--text-muted);
        white-space: nowrap;
    }
    .watchlist-items {
        display: flex;
        gap: 8px;
        flex-wrap: nowrap;
    }

    /* Category Switcher Tabs */
    .segment-tabs {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 16px;
    }
    .segment-tab {
        padding: 12px 18px;
        background: var(--bg-card);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-muted);
        font-size: 14px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.2s ease;
    }
    .segment-tab:hover { border-color: #38bdf855; color: #fff; }
    .segment-tab.active {
        background: rgba(56, 189, 248, 0.08);
        border-color: var(--cyan);
        color: var(--cyan);
        box-shadow: 0 0 20px -5px rgba(56, 189, 248, 0.25);
    }

    /* Control Box */
    .control-box {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 18px;
        position: relative;
    }
    .input-bar {
        display: flex;
        gap: 10px;
        margin-bottom: 12px;
        flex-wrap: wrap;
        position: relative;
    }
    .search-input-wrap {
        position: relative;
        flex: 2;
        min-width: 240px;
    }
    input[type="text"] {
        width: 100%;
        background: #070b12;
        border: 1px solid var(--border-highlight);
        border-radius: 8px;
        padding: 12px 16px;
        color: #fff;
        font-size: 15px;
        font-weight: 800;
        text-transform: uppercase;
        outline: none;
    }
    input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25); }

    /* Autocomplete dropdown */
    .search-suggestions {
        position: absolute;
        top: 105%;
        left: 0;
        right: 0;
        background: #0d1527;
        border: 1px solid var(--border-highlight);
        border-radius: 8px;
        max-height: 240px;
        overflow-y: auto;
        z-index: 50;
        display: none;
        box-shadow: 0 10px 25px rgba(0,0,0,0.6);
    }
    .suggestion-item {
        padding: 10px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e293b;
        cursor: pointer;
        font-size: 13px;
        transition: background 0.15s;
    }
    .suggestion-item:hover { background: #1e293b; }

    select {
        background: #070b12;
        border: 1px solid var(--border-highlight);
        border-radius: 8px;
        padding: 12px 16px;
        color: #fff;
        font-size: 14px;
        font-weight: 600;
        outline: none;
    }
    button.btn-launch {
        background: linear-gradient(135deg, #0284c7, #0ea5e9);
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: transform 0.15s ease;
    }
    button.btn-launch:hover { opacity: 0.95; transform: translateY(-1px); }
    button.btn-launch:active { transform: translateY(0); }

    .pills-container {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
    }
    .pill {
        background: #1e293b;
        border: 1px solid #334155;
        color: var(--text-muted);
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .pill:hover { color: #fff; border-color: var(--cyan); background: #334155; }
    .pill.active { background: var(--cyan); color: #090d16; border-color: var(--cyan); }

    /* Alert Banner */
    .error-alert {
        display: none;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid var(--red);
        color: #fca5a5;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 18px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Toast Notification */
    .toast-msg {
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #10b981;
        color: #070b12;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 13px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
        display: none;
        z-index: 200;
        animation: fadeIn 0.3s ease;
    }

    /* Consensus Hero Card */
    .consensus-hero {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 6px solid var(--cyan);
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 20px;
        transition: border-color 0.3s;
    }
    .hero-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 12px;
    }
    .hero-stance { font-size: 22px; font-weight: 900; }
    .hero-thesis { font-size: 14px; color: #cbd5e1; line-height: 1.6; }

    /* Telemetry 8-Card Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 14px;
        text-align: center;
        position: relative;
    }
    .metric-val { font-size: 17px; font-weight: 900; color: #fff; margin: 4px 0; }
    .metric-lbl { font-size: 10px; text-transform: uppercase; color: var(--text-muted); font-weight: 800; letter-spacing: 0.5px; }
    .metric-sub { font-size: 10px; font-weight: 700; margin-top: 2px; }

    /* Progress bar gauge */
    .gauge-bar-wrap {
        height: 5px;
        background: #1e293b;
        border-radius: 3px;
        margin-top: 5px;
        overflow: hidden;
    }
    .gauge-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.4s ease;
    }

    /* Main Grid: Chart + Debates */
    .dashboard-grid {
        display: grid;
        grid-template-columns: 1fr 480px;
        gap: 20px;
        margin-bottom: 24px;
    }
    @media (max-width: 1100px) {
        .dashboard-grid { grid-template-columns: 1fr; }
    }

    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 20px;
    }
    .card-hdr {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .card-title {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-muted);
        font-weight: 800;
    }

    /* Interactive HUD & Candlestick Canvas */
    .chart-hud {
        background: #070b12;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 11px;
        font-family: monospace;
        color: #94a3b8;
        margin-bottom: 10px;
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }
    .chart-container {
        position: relative;
        width: 100%;
        height: 420px;
        background: #070b12;
        border: 1px solid #1e293b;
        border-radius: 10px;
        overflow: hidden;
        cursor: crosshair;
    }
    canvas {
        display: block;
        width: 100%;
        height: 100%;
    }
    .chart-legend {
        display: flex;
        gap: 16px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 10px;
        flex-wrap: wrap;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-color { width: 12px; height: 3px; border-radius: 2px; }

    /* Live Debate Arena */
    .debate-arena {
        display: flex;
        flex-direction: column;
        gap: 12px;
        max-height: 520px;
        overflow-y: auto;
        padding-right: 4px;
    }
    .agent-card {
        background: #070b12;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 14px;
        transition: transform 0.2s, border-color 0.2s;
        animation: fadeIn 0.3s ease forwards;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .agent-top {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
    }
    .agent-avatar { font-size: 22px; }
    .agent-name { font-weight: 800; font-size: 13px; }
    .agent-callsign { font-size: 10px; color: var(--text-muted); font-weight: 700; }
    .agent-badge {
        margin-left: auto;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 10px;
        font-weight: 800;
    }
    .agent-speech { font-size: 12px; color: #cbd5e1; line-height: 1.5; font-style: italic; margin-bottom: 8px; }
    .agent-ul { margin: 0; padding-left: 16px; font-size: 11px; color: var(--text-muted); line-height: 1.5; }
    .risk-li { color: #f87171; }

    /* Stepping status ticker */
    .swarm-status-bar {
        background: rgba(56, 189, 248, 0.08);
        border: 1px dashed var(--cyan);
        color: var(--cyan);
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        display: none;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
    }

    /* Ask the Swarm Interactive Scenario Box */
    .ask-swarm-box {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 24px;
    }
    .quick-chips {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 10px 0 14px 0;
    }
    .quick-chip {
        background: #090d16;
        border: 1px solid #334155;
        color: #94a3b8;
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s;
    }
    .quick-chip:hover { color: #fff; border-color: var(--cyan); background: #1e293b; }

    .scenario-response {
        display: none;
        background: #070b12;
        border: 1px solid var(--border-highlight);
        border-radius: 12px;
        padding: 18px;
        margin-top: 16px;
        animation: fadeIn 0.3s ease;
    }
    .scenario-resp-row {
        margin-bottom: 12px;
        padding-bottom: 10px;
        border-bottom: 1px solid #1e293b;
        font-size: 13px;
        line-height: 1.5;
    }
    .scenario-resp-row:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

    /* Market Radar Table */
    .radar-table-wrap { overflow-x: auto; }
    table.radar-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        text-align: left;
    }
    table.radar-table th {
        background: #070b12;
        color: var(--text-muted);
        padding: 10px 14px;
        border-bottom: 1px solid var(--border-color);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    table.radar-table td {
        padding: 12px 14px;
        border-bottom: 1px solid #1e293b;
        color: #f1f5f9;
    }
    table.radar-table tr:hover td {
        background: rgba(56, 189, 248, 0.04);
        cursor: pointer;
    }
</style>
</head>
<body>

<header>
    <div class="brand">
        <div class="brand-icon">⚡</div>
        <div>
            <div class="brand-title">ALPHASWARM</div>
            <div id="hdrSubtitle" style="color: var(--text-muted); font-size: 11px;">Otonom Çoklu Ajan Konsensüs & Piyasa İstihbarat Platformu</div>
        </div>
    </div>
    <div class="nav-actions">
        <button class="live-stream-btn" id="btnLiveStream" onclick="toggleLiveStream()">
            <span class="pulse-dot"></span>
            <span id="lblLiveStream">Canlı Akış (15s)</span>
        </button>
        <div class="lang-toggle">
            <button class="lang-btn active" id="btnLangTR" onclick="setLanguage('tr')">🇹🇷 TR</button>
            <button class="lang-btn" id="btnLangEN" onclick="setLanguage('en')">🇬🇧 EN</button>
        </div>
        <a href="https://github.com/umutgungorr/alphaswarm" target="_blank" style="color: var(--text-muted); font-size: 13px; text-decoration: none; font-weight: 600;">GitHub Repo ↗</a>
    </div>
</header>

<div class="container">
    <!-- Watchlist Quick Bar -->
    <div class="watchlist-bar">
        <span class="watchlist-title">⭐️ <span id="lblWatchlist">Takip Listem:</span></span>
        <div class="watchlist-items" id="watchlistItems"></div>
    </div>

    <!-- Category Tabs -->
    <div class="segment-tabs">
        <button class="segment-tab active" id="tabCrypto" onclick="switchCategory('CRYPTO')">
            <span style="font-size: 24px;">🪙</span>
            <div>
                <div id="lblTabCrypto">Kripto Varlıklar (Coins)</div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">BTC, ETH, SOL, AVAX, BNB, XRP, SUI, TON, LINK...</div>
            </div>
        </button>
        <button class="segment-tab" id="tabStock" onclick="switchCategory('EQUITY')">
            <span style="font-size: 24px;">📈</span>
            <div>
                <div id="lblTabStock">Hisse Senetleri & BIST (Stocks)</div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">THYAO, ASELS, EREGL, GARAN, NVDA, AAPL, TSLA...</div>
            </div>
        </button>
    </div>

    <!-- Error Alert Box -->
    <div id="errorAlert" class="error-alert"></div>

    <!-- Control Box -->
    <div class="control-box">
        <div class="input-bar">
            <div class="search-input-wrap">
                <input type="text" id="symbolInput" value="BTC" placeholder="Sembol (BTC, NVDA, THYAO...)" autocomplete="off">
                <div class="search-suggestions" id="searchSuggestions"></div>
            </div>
            <select id="roundsSelect">
                <option value="1">1 Münazara Turu (Hızlı)</option>
                <option value="2" selected>2 Münazara Turu (Derin)</option>
                <option value="3">3 Münazara Turu (Ultra)</option>
            </select>
            <button class="btn-launch" id="launchBtn" onclick="runAnalysis()">
                <span>🚀 Analizi Başlat</span>
            </button>
        </div>
        <div class="pills-container">
            <div id="pillsContainer" style="display: flex; gap: 8px; flex-wrap: wrap;"></div>
            <button class="pill" id="btnToggleWatchlist" style="margin-left: auto; border-color: var(--yellow); color: var(--yellow);" onclick="toggleWatchlistCurrent()">
                ⭐️ Takibe Ekle
            </button>
        </div>
    </div>

    <!-- Live Agent Thinking Status Bar -->
    <div id="swarmStatusBar" class="swarm-status-bar">
        <span class="spinner" style="font-size: 18px;">⏳</span>
        <span id="swarmStatusMsg">Ajan Swarm'ı toplanıyor...</span>
    </div>

    <!-- Consensus Hero Card -->
    <div id="consensusHero" class="consensus-hero">
        <div class="hero-top">
            <div class="hero-stance" id="verdictStance">KONSENSÜS BEKLENİYOR...</div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button class="pill" style="color: var(--green); border-color: var(--green);" onclick="copySignalCard()">📋 Sinyali Kopyala</button>
                <button class="pill" style="color: var(--cyan); border-color: var(--cyan);" onclick="downloadReport('html')">📥 HTML Rapor</button>
                <button class="pill" onclick="downloadReport('md')">📄 Markdown</button>
            </div>
        </div>
        <div class="hero-thesis" id="verdictThesis">Analiz başlatmak için yukarıdaki 'Analizi Başlat' butonuna tıklayın.</div>
    </div>

    <!-- 8 Execution Telemetry Cards Grid -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-lbl">RSI (14-GÜN)</div>
            <div class="metric-val" id="valRSI">50.0</div>
            <div class="gauge-bar-wrap">
                <div class="gauge-bar-fill" id="barRSI" style="width: 50%; background: var(--cyan);"></div>
            </div>
            <div class="metric-sub" id="subRSI" style="color: var(--cyan);">NÖTR</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl" id="lblFgTitle">KORKU & AÇGÖZLÜLÜK</div>
            <div class="metric-val" id="valFG">50</div>
            <div class="gauge-bar-wrap">
                <div class="gauge-bar-fill" id="barFG" style="width: 50%; background: var(--yellow);"></div>
            </div>
            <div class="metric-sub" id="subFG" style="color: var(--yellow);">DENGELİ</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl">50/200 TREND</div>
            <div class="metric-val" id="valSMA" style="font-size: 13px;">BEKLEMEDE</div>
            <div class="metric-sub" id="subSMA" style="color: var(--text-muted);">Ortalama Kesişimi</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl" id="lblTp1Title">🎯 HEDEF 1 (TP1)</div>
            <div class="metric-val" id="valTP1" style="color: var(--green);">$0.00</div>
            <div class="metric-sub" id="subTP1" style="color: var(--green);">+0.00% Potansiyel</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl" id="lblTp2Title">🎯 HEDEF 2 (TP2)</div>
            <div class="metric-val" id="valTP2" style="color: var(--green);">$0.00</div>
            <div class="metric-sub" id="subTP2" style="color: var(--green);">+0.00% Genişleme</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl" id="lblStopTitle">🛑 ZARAR KES (STOP)</div>
            <div class="metric-val" id="valInval" style="color: var(--red);">$0.00</div>
            <div class="metric-sub" id="subInval" style="color: var(--red);">-0.00% Risk Sınırı</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl">⚖️ RİSK / ÖDÜL (R:R)</div>
            <div class="metric-val" id="valRR" style="color: var(--cyan);">1 : 2.0</div>
            <div class="metric-sub" id="subRR" style="color: var(--cyan);">Asimetrik Oran</div>
        </div>
        <div class="metric-card">
            <div class="metric-lbl" id="lblSrTitle">🛡️ DESTEK / DİRENÇ</div>
            <div class="metric-val" id="valSR" style="font-size: 12px; margin-top: 6px;">S: $0 | R: $0</div>
            <div class="metric-sub" style="color: var(--text-muted);">Kritik Sınırlar</div>
        </div>
    </div>

    <!-- Main Dashboard Grid -->
    <div class="dashboard-grid">
        <!-- Left: Real Price Action Chart & Telemetry -->
        <div>
            <div class="card" style="margin-bottom: 20px;">
                <div class="card-hdr">
                    <div>
                        <span class="card-title" id="lblChartTitle">Canlı Fiyat Grafiği, Hacim & Teknik Bantlar</span>
                        <div id="chartAssetHeader" style="font-size: 18px; font-weight: 900; color: #fff; margin-top: 4px;">BTC / USD</div>
                    </div>
                    <div style="text-align: right;">
                        <div id="chartPrice" style="font-size: 20px; font-weight: 800; color: var(--cyan);">$0.00</div>
                        <div id="chartChange" style="font-size: 12px; font-weight: 700;">+0.00%</div>
                    </div>
                </div>

                <!-- Live Hover HUD Tooltip Bar -->
                <div class="chart-hud" id="chartHud">
                    <span>İmleci mumların üzerine getirerek anlık Açılış, Yüksek, Düşük, Kapanış ve Hacim verilerini inceleyin.</span>
                </div>

                <div class="chart-container" id="chartWrap">
                    <canvas id="candleCanvas"></canvas>
                </div>

                <div class="chart-legend">
                    <div class="legend-item"><div class="legend-color" style="background: #10b981;"></div><span id="lblLgBull">Boğa Mumu</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #ef4444;"></div><span id="lblLgBear">Ayı Mumu</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #38bdf8;"></div><span>SMA 50</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #a855f7;"></div><span>SMA 200</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #10b981; border-top: 1px dashed #10b981;"></div><span>TP1 / TP2 Hedef</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #f87171; border-top: 1px dashed #f87171;"></div><span id="lblLgStop">Stop Invalidation</span></div>
                </div>
            </div>

            <!-- Screener Radar Table -->
            <div class="card">
                <div class="card-title" id="lblRadarTitle">⚡ Çoklu Varlık Radarı & Hızlı Tarama</div>
                <div class="radar-table-wrap">
                    <table class="radar-table">
                        <thead>
                            <tr>
                                <th>Sembol</th>
                                <th>Varlık Adı</th>
                                <th>Son Fiyat</th>
                                <th>24h %</th>
                                <th>RSI</th>
                                <th>İşlem</th>
                            </tr>
                        </thead>
                        <tbody id="radarTbody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Right: Live Debate Arena -->
        <div>
            <div class="card" style="margin-bottom: 20px;">
                <div class="card-hdr">
                    <span class="card-title" id="lblArenaTitle">Canlı Ajan Münazara Arenası</span>
                    <span style="font-size: 11px; color: var(--cyan); font-weight: 700;">4 OTONOM AJAN</span>
                </div>
                <div class="debate-arena" id="debateArena"></div>
            </div>

            <!-- Interactive Ask the Swarm & Scenario Simulator -->
            <div class="ask-swarm-box">
                <div class="card-title" id="lblAskTitle">💬 Ajan Swarm'ına Danış & Özel Senaryo Simülasyonu</div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
                    Mevcut varlık için swarm ajanlarına özel soru sorun veya senaryo simülasyonu çalıştırın:
                </div>
                
                <div class="quick-chips">
                    <div class="quick-chip" onclick="setScenarioQuestion(this)">Bu fiyattan kademeli alım yapılır mı?</div>
                    <div class="quick-chip" onclick="setScenarioQuestion(this)">Düşüş derinleşirse en güçlü ilk destek neresi?</div>
                    <div class="quick-chip" onclick="setScenarioQuestion(this)">Kısa ve orta vadeli kar realizasyonu seviyeleri?</div>
                    <div class="quick-chip" onclick="setScenarioQuestion(this)">Kaldıraçlı işlem açmak mantıklı mı?</div>
                    <div class="quick-chip" onclick="setScenarioQuestion(this)">Piyasa çökerse en savunmacı strateji ne olur?</div>
                </div>

                <div style="display: flex; gap: 8px;">
                    <input type="text" id="scenarioInput" placeholder="Ajanlara bir soru veya senaryo yazın..." style="font-size: 13px; text-transform: none;">
                    <button class="btn-launch" id="btnAskSwarm" onclick="askSwarmScenario()" style="padding: 10px 16px; white-space: nowrap;">
                        <span>Danış ⚡</span>
                    </button>
                </div>

                <div class="scenario-response" id="scenarioResponseBox">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-weight: 800; color: var(--cyan); font-size: 13px;">🧠 Swarm Danışmanlık Yanıtı</span>
                        <button class="pill" style="font-size: 10px;" onclick="closeScenarioBox()">Kapat ✕</button>
                    </div>
                    <div class="scenario-resp-row" id="respAria"></div>
                    <div class="scenario-resp-row" id="respMarcus"></div>
                    <div class="scenario-resp-row" id="respVesper"></div>
                    <div class="scenario-resp-row" id="respSovereign" style="font-weight: 800; color: var(--green);"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="toast-msg" id="toastMsg">✅ Panoya Kopyalandı!</div>

<script>
let currentCategory = "CRYPTO";
let currentLang = "tr";
let currentSymbol = "BTC";
let currentCandles = [];
let currentVerdict = null;
let currentMarketData = null;
let isLiveStreaming = false;
let liveStreamTimer = null;
let hoveredCandleIndex = null;

let watchlist = JSON.parse(localStorage.getItem("alphaswarm_watchlist") || '["BTC", "ETH", "SOL", "NVDA", "THYAO"]');

const COIN_LIST = [
    { s: "BTC", n: "Bitcoin", p: 84500, c: 2.45, r: 61.2 },
    { s: "ETH", n: "Ethereum", p: 3450, c: -1.15, r: 48.5 },
    { s: "SOL", n: "Solana", p: 148, c: 4.80, r: 66.4 },
    { s: "AVAX", n: "Avalanche", p: 28.5, c: 3.20, r: 58.1 },
    { s: "BNB", n: "BNB", p: 585, c: 0.90, r: 52.0 },
    { s: "XRP", n: "XRP", p: 0.58, c: -0.40, r: 47.0 },
    { s: "SUI", n: "Sui", p: 1.65, c: 7.40, r: 69.5 },
    { s: "TON", n: "Toncoin", p: 5.60, c: 1.20, r: 53.0 },
    { s: "LINK", n: "Chainlink", p: 11.8, c: 1.80, r: 54.0 },
    { s: "RENDER", n: "Render", p: 6.20, c: 3.50, r: 60.5 },
    { s: "INJ", n: "Injective", p: 21.5, c: -0.80, r: 49.0 },
    { s: "DOT", n: "Polkadot", p: 4.60, c: 0.50, r: 51.0 },
];

const STOCK_LIST = [
    { s: "NVDA", n: "NVIDIA Corp.", p: 225.5, c: 2.10, r: 63.5 },
    { s: "AAPL", n: "Apple Inc.", p: 337.0, c: 0.85, r: 58.0 },
    { s: "MSFT", n: "Microsoft Corp.", p: 430.0, c: -0.60, r: 49.2 },
    { s: "TSLA", n: "Tesla Inc.", p: 380.1, c: 3.80, r: 65.0 },
    { s: "THYAO", n: "Türk Hava Yolları", p: 298.5, c: 1.75, r: 56.4 },
    { s: "ASELS", n: "Aselsan", p: 62.5, c: 0.80, r: 53.0 },
    { s: "EREGL", n: "Ereğli Demir Çelik", p: 52.0, c: -1.10, r: 46.0 },
    { s: "GARAN", n: "Garanti BBVA", p: 120.0, c: 2.30, r: 61.0 },
    { s: "TUPRS", n: "Tüpraş", p: 175.0, c: 0.40, r: 52.5 },
    { s: "BIMAS", n: "BİM Mağazalar", p: 520.0, c: 1.10, r: 57.0 },
    { s: "SPY", n: "S&P 500 ETF", p: 560.0, c: 0.45, r: 54.0 },
    { s: "QQQ", n: "Invesco QQQ", p: 480.0, c: 0.65, r: 56.0 },
];

const I18N = {
    tr: {
        subtitle: "Otonom Çoklu Ajan Konsensüs & Piyasa İstihbarat Platformu",
        watchlist: "Takip Listem:",
        tabCrypto: "Kripto Varlıklar (Coins)",
        tabStock: "Hisse Senetleri & BIST (Stocks)",
        btnLaunch: "🚀 Analizi Başlat",
        chartTitle: "Canlı Fiyat Grafiği, Hacim & Teknik Bantlar",
        radarTitle: "⚡ Çoklu Varlık Radarı & Hızlı Tarama",
        arenaTitle: "Canlı Ajan Münazara Arenası",
        askTitle: "💬 Ajan Swarm'ına Danış & Özel Senaryo Simülasyonu",
        lgBull: "Boğa Mumu",
        lgBear: "Ayı Mumu",
        lgStop: "Stop İptal Seviyesi",
        lblFg: "KORKU & AÇGÖZLÜLÜK",
        lblStop: "🛑 ZARAR KES (STOP)",
        lblTp1: "🎯 HEDEF 1 (TP1)",
        lblTp2: "🎯 HEDEF 2 (TP2)",
        lblSr: "🛡️ DESTEK / DİRENÇ",
        waitingThesis: "Analiz başlatmak için yukarıdaki 'Analizi Başlat' butonuna tıklayın.",
        steps: [
            "Aria Vance (Quant) mum grafiklerini, Bollinger bantlarını ve RSI/MACD göstergelerini hesaplıyor...",
            "Marcus Cole (Makro/Haber) kurumsal fon akışlarını ve duyarlılığı değerlendiriyor...",
            "Vesper Sterling (Risk) tersine riskleri ve stop patlatma tuzaklarını inceliyor...",
            "Sovereign AI (Konsensüs) tüm argümanları tartıp nihai kararı oluşturuyor..."
        ]
    },
    en: {
        subtitle: "Autonomous Multi-Agent Consensus & Market Intelligence Platform",
        watchlist: "My Watchlist:",
        tabCrypto: "Cryptocurrencies (Coins)",
        tabStock: "Equities & BIST Stocks",
        btnLaunch: "🚀 Launch Swarm",
        chartTitle: "Live Candlestick Chart, Volume & Technical Bands",
        radarTitle: "⚡ Multi-Asset Radar & Screener",
        arenaTitle: "Live Multi-Agent Debate Arena",
        askTitle: "💬 Ask The Swarm & Custom Scenario Simulator",
        lgBull: "Bull Candle",
        lgBear: "Bear Candle",
        lgStop: "Stop Invalidation Level",
        lblFg: "FEAR & GREED",
        lblStop: "🛑 STOP LOSS",
        lblTp1: "🎯 TARGET 1 (TP1)",
        lblTp2: "🎯 TARGET 2 (TP2)",
        lblSr: "🛡️ SUPPORT / RESISTANCE",
        waitingThesis: "Click 'Launch Swarm' to begin multi-agent consensus analysis.",
        steps: [
            "Aria Vance (Quant Lead) computing candle indicators, Bollinger bands & momentum...",
            "Marcus Cole (Macro Lead) evaluating institutional flows & sentiment...",
            "Vesper Sterling (Risk Lead) interrogating downside traps & stops...",
            "Sovereign AI (Consensus Node) resolving arguments & issuing final dossier..."
        ]
    }
};

function setLanguage(lang) {
    currentLang = lang;
    document.getElementById("btnLangTR").className = "lang-btn" + (lang === "tr" ? " active" : "");
    document.getElementById("btnLangEN").className = "lang-btn" + (lang === "en" ? " active" : "");

    const t = I18N[lang];
    document.getElementById("hdrSubtitle").textContent = t.subtitle;
    document.getElementById("lblWatchlist").textContent = t.watchlist;
    document.getElementById("lblTabCrypto").textContent = t.tabCrypto;
    document.getElementById("lblTabStock").textContent = t.tabStock;
    document.getElementById("launchBtn").innerHTML = `<span>${t.btnLaunch}</span>`;
    document.getElementById("lblChartTitle").textContent = t.chartTitle;
    document.getElementById("lblRadarTitle").textContent = t.radarTitle;
    document.getElementById("lblArenaTitle").textContent = t.arenaTitle;
    document.getElementById("lblAskTitle").textContent = t.askTitle;
    document.getElementById("lblLgBull").textContent = t.lgBull;
    document.getElementById("lblLgBear").textContent = t.lgBear;
    document.getElementById("lblLgStop").textContent = t.lgStop;
    document.getElementById("lblFgTitle").textContent = t.lblFg;
    document.getElementById("lblStopTitle").textContent = t.lblStop;
    document.getElementById("lblTp1Title").textContent = t.lblTp1;
    document.getElementById("lblTp2Title").textContent = t.lblTp2;
    document.getElementById("lblSrTitle").textContent = t.lblSr;

    renderRadarTable();
    runAnalysis();
}

function switchCategory(cat) {
    currentCategory = cat;
    document.getElementById("tabCrypto").className = "segment-tab" + (cat === "CRYPTO" ? " active" : "");
    document.getElementById("tabStock").className = "segment-tab" + (cat === "EQUITY" ? " active" : "");
    
    renderPills();
    renderRadarTable();

    document.getElementById("symbolInput").value = cat === "CRYPTO" ? "BTC" : "THYAO";
    runAnalysis();
}

function renderPills() {
    const container = document.getElementById("pillsContainer");
    container.innerHTML = "";
    const list = currentCategory === "CRYPTO" ? COIN_LIST : STOCK_LIST;
    list.slice(0, 8).forEach(item => {
        const btn = document.createElement("button");
        btn.className = "pill" + (item.s === currentSymbol ? " active" : "");
        btn.textContent = item.s;
        btn.onclick = () => {
            document.getElementById("symbolInput").value = item.s;
            runAnalysis();
        };
        container.appendChild(btn);
    });
    updateWatchlistBtn();
}

function renderWatchlist() {
    const bar = document.getElementById("watchlistItems");
    bar.innerHTML = "";
    watchlist.forEach(sym => {
        const btn = document.createElement("button");
        btn.className = "pill" + (sym === currentSymbol ? " active" : "");
        btn.innerHTML = `${sym} <span style="font-size: 9px; color: #94a3b8;" onclick="event.stopPropagation(); removeWatchlist('${sym}')">✕</span>`;
        btn.onclick = () => {
            document.getElementById("symbolInput").value = sym;
            runAnalysis();
        };
        bar.appendChild(btn);
    });
}

function toggleWatchlistCurrent() {
    const sym = currentSymbol;
    if (watchlist.includes(sym)) {
        watchlist = watchlist.filter(x => x !== sym);
    } else {
        watchlist.push(sym);
    }
    localStorage.setItem("alphaswarm_watchlist", JSON.stringify(watchlist));
    renderWatchlist();
    updateWatchlistBtn();
    showToast(watchlist.includes(sym) ? `⭐️ ${sym} Takip Listesine Eklendi!` : `❌ ${sym} Takip Listesinden Çıkarıldı.`);
}

function removeWatchlist(sym) {
    watchlist = watchlist.filter(x => x !== sym);
    localStorage.setItem("alphaswarm_watchlist", JSON.stringify(watchlist));
    renderWatchlist();
    updateWatchlistBtn();
}

function updateWatchlistBtn() {
    const btn = document.getElementById("btnToggleWatchlist");
    if (!btn) return;
    if (watchlist.includes(currentSymbol)) {
        btn.innerHTML = "⭐️ Takipte ✓";
        btn.style.borderColor = "var(--green)";
        btn.style.color = "var(--green)";
    } else {
        btn.innerHTML = "⭐️ Takibe Ekle";
        btn.style.borderColor = "var(--yellow)";
        btn.style.color = "var(--yellow)";
    }
}

function renderRadarTable() {
    const tbody = document.getElementById("radarTbody");
    tbody.innerHTML = "";
    const list = currentCategory === "CRYPTO" ? COIN_LIST : STOCK_LIST;
    list.forEach(item => {
        const tr = document.createElement("tr");
        const isBist = item.s.includes("THYAO") || item.s.includes("ASELS") || item.s.includes("EREGL") || item.s.includes("GARAN") || item.s.includes("TUPRS") || item.s.includes("BIMAS");
        const cur = isBist ? "₺" : "$";
        const chgColor = item.c >= 0 ? "var(--green)" : "var(--red)";
        tr.innerHTML = `
            <td><strong>${item.s}</strong></td>
            <td style="color: var(--text-muted);">${item.n}</td>
            <td><strong>${cur}${item.p.toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></td>
            <td style="color: ${chgColor}; font-weight: 700;">${item.c >= 0 ? '+' : ''}${item.c.toFixed(2)}%</td>
            <td>${item.r}</td>
            <td><button class="pill" style="font-size: 11px;">Analiz ↗</button></td>
        `;
        tr.onclick = () => {
            document.getElementById("symbolInput").value = item.s;
            window.scrollTo({ top: 0, behavior: 'smooth' });
            runAnalysis();
        };
        tbody.appendChild(tr);
    });
}

function toggleLiveStream() {
    isLiveStreaming = !isLiveStreaming;
    const btn = document.getElementById("btnLiveStream");
    btn.className = "live-stream-btn" + (isLiveStreaming ? " active" : "");
    if (isLiveStreaming) {
        showToast("🟢 Canlı Akış Başlatıldı (15s döngü)");
        liveStreamTimer = setInterval(() => {
            runAnalysis(true);
        }, 15000);
    } else {
        showToast("⏸️ Canlı Akış Duraklatıldı");
        if (liveStreamTimer) clearInterval(liveStreamTimer);
    }
}

async function runAnalysis(silent = false) {
    const symInput = document.getElementById("symbolInput").value.trim().toUpperCase();
    if (!symInput) return;

    currentSymbol = symInput;
    renderPills();
    updateWatchlistBtn();

    const rounds = document.getElementById("roundsSelect").value;
    const errAlert = document.getElementById("errorAlert");
    errAlert.style.display = "none";

    const sBar = document.getElementById("swarmStatusBar");
    const sMsg = document.getElementById("swarmStatusMsg");
    if (!silent) sBar.style.display = "flex";

    const t = I18N[currentLang];
    sMsg.textContent = t.steps[0];

    try {
        const url = `/api/analyze?symbol=${encodeURIComponent(symInput)}&asset_type=${currentCategory}&rounds=${rounds}&lang=${currentLang}`;
        const resp = await fetch(url);
        const data = await resp.json();

        if (!resp.ok) {
            errAlert.textContent = data.error || "Geçersiz sembol!";
            errAlert.style.display = "block";
            sBar.style.display = "none";
            return;
        }

        if (!silent) {
            sMsg.textContent = t.steps[1];
            await new Promise(r => setTimeout(r, 180));
            sMsg.textContent = t.steps[2];
            await new Promise(r => setTimeout(r, 180));
            sMsg.textContent = t.steps[3];
            await new Promise(r => setTimeout(r, 180));
        }

        renderData(data);
    } catch (err) {
        errAlert.textContent = "Bağlantı hatası: " + err;
        errAlert.style.display = "block";
    } finally {
        sBar.style.display = "none";
    }
}

function renderData(data) {
    const v = data.verdict;
    const m = data.market_data;
    const ind = m.indicators;
    currentVerdict = v;
    currentMarketData = m;
    currentCandles = m.candles || [];

    const isBull = v.final_stance.includes("BULL");
    const isBear = v.final_stance.includes("BEAR");
    const color = isBull ? "var(--green)" : (isBear ? "var(--red)" : "var(--yellow)");

    // Hero consensus banner
    const hero = document.getElementById("consensusHero");
    hero.style.borderLeftColor = color;
    
    let stanceDisplay = v.final_stance;
    if (currentLang === "tr") {
        if (v.final_stance === "STRONG_BULL") stanceDisplay = "GÜÇLÜ YÜKSELİŞ (STRONG BULL)";
        else if (v.final_stance === "BULLISH") stanceDisplay = "YÜKSELİŞ (BULLISH)";
        else if (v.final_stance === "NEUTRAL") stanceDisplay = "NÖTR / BEKLE (NEUTRAL)";
        else if (v.final_stance === "BEARISH") stanceDisplay = "DÜŞÜŞ (BEARISH)";
        else if (v.final_stance === "STRONG_BEAR") stanceDisplay = "GÜÇLÜ DÜŞÜŞ (STRONG BEAR)";
    }

    document.getElementById("verdictStance").textContent = `${stanceDisplay} &bull; %${v.confidence_score} Güven`;
    document.getElementById("verdictStance").style.color = color;
    document.getElementById("verdictThesis").textContent = v.primary_thesis;

    // Header values
    const cur = m.currency === "TRY" ? "₺" : "$";
    document.getElementById("chartAssetHeader").textContent = `${m.symbol} / ${m.currency}`;
    document.getElementById("chartPrice").textContent = `${cur}${m.current_price.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    const chgEl = document.getElementById("chartChange");
    chgEl.textContent = `${m.change_24h_pct >= 0 ? '+' : ''}${m.change_24h_pct.toFixed(2)}%`;
    chgEl.style.color = m.change_24h_pct >= 0 ? "var(--green)" : "var(--red)";

    // 8 Telemetry Cards
    document.getElementById("valRSI").textContent = ind.rsi_14.toFixed(1);
    const rsiBar = document.getElementById("barRSI");
    rsiBar.style.width = `${Math.min(100, Math.max(0, ind.rsi_14))}%`;
    rsiBar.style.background = ind.rsi_14 > 70 ? "var(--red)" : (ind.rsi_14 < 30 ? "var(--green)" : "var(--cyan)");
    document.getElementById("subRSI").textContent = ind.rsi_14 > 70 ? "AŞIRI ALIM" : (ind.rsi_14 < 30 ? "AŞIRI SATIM" : "DENGELİ");

    document.getElementById("valFG").textContent = m.fear_greed_score;
    const fgBar = document.getElementById("barFG");
    fgBar.style.width = `${m.fear_greed_score}%`;
    fgBar.style.background = m.fear_greed_score > 60 ? "var(--green)" : (m.fear_greed_score < 40 ? "var(--red)" : "var(--yellow)");
    document.getElementById("subFG").textContent = m.fear_greed_label;

    document.getElementById("valSMA").textContent = ind.trend_50_200;
    
    // TP1, TP2, Stop, RR, SR
    const tp1Pct = ((v.take_profit_1 - m.current_price) / m.current_price * 100).toFixed(1);
    const tp2Pct = ((v.take_profit_2 - m.current_price) / m.current_price * 100).toFixed(1);
    const stopPct = ((v.key_invalidation_level - m.current_price) / m.current_price * 100).toFixed(1);

    document.getElementById("valTP1").textContent = `${cur}${v.take_profit_1.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    document.getElementById("subTP1").textContent = `${tp1Pct >= 0 ? '+' : ''}${tp1Pct}% Potansiyel`;

    document.getElementById("valTP2").textContent = `${cur}${v.take_profit_2.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    document.getElementById("subTP2").textContent = `${tp2Pct >= 0 ? '+' : ''}${tp2Pct}% Genişleme`;

    document.getElementById("valInval").textContent = `${cur}${v.key_invalidation_level.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    document.getElementById("subInval").textContent = `${stopPct}% Risk Sınırı`;

    document.getElementById("valRR").textContent = `1 : ${v.risk_reward_ratio || 2.0}`;
    document.getElementById("valSR").textContent = `S: ${cur}${v.support_level} | R: ${cur}${v.resistance_level}`;

    // Render Canvas Chart
    drawCanvasChart(currentCandles, ind, v, cur);

    // Render Debates with lively animated bubbles
    const arena = document.getElementById("debateArena");
    arena.innerHTML = "";

    v.debate_rounds.forEach(r => {
        const roundTitle = document.createElement("div");
        roundTitle.style.cssText = "font-size: 11px; color: var(--cyan); text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin: 8px 0 4px 0;";
        roundTitle.textContent = currentLang === 'tr' 
            ? `▶ Münazara Turu #${r.round_number} (${r.consensus_shift_notes})` 
            : `▶ Debate Round #${r.round_number} (${r.consensus_shift_notes})`;
        arena.appendChild(roundTitle);

        r.thoughts.forEach(t => {
            const isTBull = t.stance.includes("BULL");
            const isTBear = t.stance.includes("BEAR");
            const tColor = isTBull ? "var(--green)" : (isTBear ? "var(--red)" : "var(--yellow)");
            const icon = t.role === "TECHNICAL" ? "📐" : (t.role === "SENTIMENT" ? "📰" : "🛡️");

            const card = document.createElement("div");
            card.className = "agent-card";
            card.innerHTML = `
                <div class="agent-top">
                    <span class="agent-avatar">${icon}</span>
                    <div>
                        <div class="agent-name">${t.agent_name}</div>
                        <div class="agent-callsign">[${t.callsign}] &bull; ${t.role}</div>
                    </div>
                    <span class="agent-badge" style="background: ${tColor}22; color: ${tColor}; border: 1px solid ${tColor}55;">
                        ${t.stance} (%${Math.round(t.confidence * 100)})
                    </span>
                </div>
                <div class="agent-speech">"${t.thesis}"</div>
                <ul class="agent-ul">
                    ${t.key_points.map(p => `<li>${p}</li>`).join("")}
                    ${t.identified_risks.map(rk => `<li class="risk-li">⚠️ ${rk}</li>`).join("")}
                </ul>
            `;
            arena.appendChild(card);
        });
    });
}

function drawCanvasChart(candles, ind, verdict, curSym) {
    const canvas = document.getElementById("candleCanvas");
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;

    const width = canvas.parentElement.clientWidth;
    const height = canvas.parentElement.clientHeight;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    if (!candles || candles.length === 0) return;

    ctx.clearRect(0, 0, width, height);

    // Panes: Price pane (top 72%), Volume pane (bottom 24%)
    const pricePaneHeight = height * 0.72;
    const volPaneTop = height * 0.76;
    const volPaneHeight = height - volPaneTop - 12;

    // Price Bounds
    const allPrices = candles.flatMap(c => [c.high, c.low]);
    if (verdict) {
        if (verdict.key_invalidation_level) allPrices.push(verdict.key_invalidation_level);
        if (verdict.take_profit_1) allPrices.push(verdict.take_profit_1);
        if (verdict.take_profit_2) allPrices.push(verdict.take_profit_2);
    }
    if (ind && ind.bollinger_upper) allPrices.push(ind.bollinger_upper, ind.bollinger_lower);

    const minPrice = Math.min(...allPrices) * 0.985;
    const maxPrice = Math.max(...allPrices) * 1.015;
    const priceRange = maxPrice - minPrice;

    const getY = p => 15 + ((maxPrice - p) / priceRange) * (pricePaneHeight - 30);

    // Max Volume
    const maxVol = Math.max(...candles.map(c => c.volume || 1));

    // 1. Grid Lines on Price Pane
    ctx.strokeStyle = "#162032";
    ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
        const y = (pricePaneHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();

        const gridP = maxPrice - (i / 5) * priceRange;
        ctx.fillStyle = "#475569";
        ctx.font = "10px sans-serif";
        ctx.fillText(`${curSym}${gridP.toLocaleString(undefined, {maximumFractionDigits: 1})}`, width - 65, y - 4);
    }

    // 2. Volume Separator & Label
    ctx.strokeStyle = "#1e293b";
    ctx.beginPath();
    ctx.moveTo(0, volPaneTop - 4);
    ctx.lineTo(width, volPaneTop - 4);
    ctx.stroke();

    ctx.fillStyle = "#475569";
    ctx.font = "9px sans-serif";
    ctx.fillText("HACİM (VOL)", 8, volPaneTop + 8);

    // 3. Candle X Geometry
    const n = candles.length;
    const gap = width / n;
    const candleWidth = Math.max(4, gap * 0.65);

    // 4. Draw Bollinger Band Channel Fill (if available)
    if (ind && ind.bollinger_upper && ind.bollinger_lower) {
        const yUpper = getY(ind.bollinger_upper);
        const yLower = getY(ind.bollinger_lower);
        ctx.fillStyle = "rgba(168, 85, 247, 0.05)";
        ctx.fillRect(0, yUpper, width, yLower - yUpper);

        ctx.strokeStyle = "rgba(168, 85, 247, 0.35)";
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(0, yUpper);
        ctx.lineTo(width, yUpper);
        ctx.moveTo(0, yLower);
        ctx.lineTo(width, yLower);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // 5. Draw SMA 50 and SMA 200 Curves across candles
    function drawMovingAverage(period, color) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        let started = false;

        for (let i = 0; i < n; i++) {
            const startIdx = Math.max(0, i - period + 1);
            const slice = candles.slice(startIdx, i + 1);
            const avg = slice.reduce((acc, c) => acc + c.close, 0) / slice.length;
            const x = i * gap + gap / 2;
            const y = getY(avg);

            if (!started) {
                ctx.moveTo(x, y);
                started = true;
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }

    drawMovingAverage(10, "#38bdf8"); // Fast MA (SMA 50 proxy)
    drawMovingAverage(20, "#a855f7"); // Slow MA (SMA 200 proxy)

    // 6. Draw Targets & Stop Lines
    if (verdict) {
        // TP1
        if (verdict.take_profit_1) {
            const tp1Y = getY(verdict.take_profit_1);
            ctx.save();
            ctx.strokeStyle = "#10b981";
            ctx.lineWidth = 1.4;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.moveTo(0, tp1Y);
            ctx.lineTo(width, tp1Y);
            ctx.stroke();
            ctx.fillStyle = "#10b981";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(`🎯 TP1: ${curSym}${verdict.take_profit_1.toLocaleString(undefined, {maximumFractionDigits: 1})}`, 8, tp1Y - 4);
            ctx.restore();
        }

        // TP2
        if (verdict.take_profit_2) {
            const tp2Y = getY(verdict.take_profit_2);
            ctx.save();
            ctx.strokeStyle = "#059669";
            ctx.lineWidth = 1.4;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.moveTo(0, tp2Y);
            ctx.lineTo(width, tp2Y);
            ctx.stroke();
            ctx.fillStyle = "#059669";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(`🎯 TP2: ${curSym}${verdict.take_profit_2.toLocaleString(undefined, {maximumFractionDigits: 1})}`, 8, tp2Y - 4);
            ctx.restore();
        }

        // STOP
        if (verdict.key_invalidation_level) {
            const stopY = getY(verdict.key_invalidation_level);
            ctx.save();
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 1.4;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.moveTo(0, stopY);
            ctx.lineTo(width, stopY);
            ctx.stroke();
            ctx.fillStyle = "#ef4444";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(`🛑 STOP: ${curSym}${verdict.key_invalidation_level.toLocaleString(undefined, {maximumFractionDigits: 1})}`, width - 130, stopY - 4);
            ctx.restore();
        }
    }

    // 7. Draw Candles & Volume Bars
    candles.forEach((c, i) => {
        const x = i * gap + gap / 2;
        const openY = getY(c.open);
        const closeY = getY(c.close);
        const highY = getY(c.high);
        const lowY = getY(c.low);

        const isBull = c.close >= c.open;
        const color = isBull ? "#10b981" : "#ef4444";

        // Highlight hovered candle
        if (i === hoveredCandleIndex) {
            ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
            ctx.fillRect(x - gap / 2, 0, gap, height);
        }

        // Wick
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, highY);
        ctx.lineTo(x, lowY);
        ctx.stroke();

        // Body
        ctx.fillStyle = color;
        const bodyTop = Math.min(openY, closeY);
        const bodyHeight = Math.max(2, Math.abs(closeY - openY));
        ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);

        // Volume Bar
        const vBarHeight = Math.max(2, (c.volume / maxVol) * volPaneHeight);
        ctx.fillStyle = isBull ? "rgba(16, 185, 129, 0.35)" : "rgba(239, 68, 68, 0.35)";
        ctx.fillRect(x - candleWidth / 2, height - 8 - vBarHeight, candleWidth, vBarHeight);
    });

    // 8. Crosshair overlay if hovered
    if (hoveredCandleIndex !== null && candles[hoveredCandleIndex]) {
        const hc = candles[hoveredCandleIndex];
        const hx = hoveredCandleIndex * gap + gap / 2;
        const hy = getY(hc.close);

        ctx.save();
        ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);

        // Vertical line
        ctx.beginPath();
        ctx.moveTo(hx, 0);
        ctx.lineTo(hx, height);
        ctx.stroke();

        // Horizontal line
        ctx.beginPath();
        ctx.moveTo(0, hy);
        ctx.lineTo(width, hy);
        ctx.stroke();

        // Price badge on right
        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(width - 65, hy - 9, 65, 18);
        ctx.fillStyle = "#070b12";
        ctx.font = "bold 10px monospace";
        ctx.fillText(`${curSym}${hc.close.toFixed(1)}`, width - 60, hy + 3);

        ctx.restore();
    }
}

// Chart Mouse Hover Listener for Crosshair
const chartWrap = document.getElementById("chartWrap");
chartWrap.addEventListener("mousemove", (e) => {
    if (!currentCandles || currentCandles.length === 0) return;
    const rect = chartWrap.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const gap = rect.width / currentCandles.length;
    const idx = Math.min(currentCandles.length - 1, Math.max(0, Math.floor(x / gap)));

    hoveredCandleIndex = idx;
    const c = currentCandles[idx];
    const cur = currentMarketData ? (currentMarketData.currency === "TRY" ? "₺" : "$") : "$";
    const chg = ((c.close - c.open) / c.open * 100).toFixed(2);
    const chgColor = chg >= 0 ? "#10b981" : "#ef4444";

    const hud = document.getElementById("chartHud");
    hud.innerHTML = `
        <span>📅 ${c.timestamp}</span>
        <span>🟢 O: <strong>${cur}${c.open}</strong></span>
        <span>🔺 H: <strong>${cur}${c.high}</strong></span>
        <span>🔻 L: <strong>${cur}${c.low}</strong></span>
        <span>🏁 C: <strong>${cur}${c.close}</strong></span>
        <span>📊 Vol: <strong>${c.volume.toLocaleString()}</strong></span>
        <span style="color: ${chgColor};">📈 ${chg >= 0 ? '+' : ''}${chg}%</span>
    `;

    if (currentVerdict) {
        drawCanvasChart(currentCandles, currentMarketData ? currentMarketData.indicators : null, currentVerdict, cur);
    }
});

chartWrap.addEventListener("mouseleave", () => {
    hoveredCandleIndex = null;
    const cur = currentMarketData ? (currentMarketData.currency === "TRY" ? "₺" : "$") : "$";
    if (currentCandles.length > 0 && currentVerdict) {
        drawCanvasChart(currentCandles, currentMarketData ? currentMarketData.indicators : null, currentVerdict, cur);
    }
    document.getElementById("chartHud").innerHTML = `
        <span>İmleci mumların üzerine getirerek anlık Açılış, Yüksek, Düşük, Kapanış ve Hacim verilerini inceleyin.</span>
    `;
});

// Autocomplete Logic
const symbolInput = document.getElementById("symbolInput");
const searchSuggestions = document.getElementById("searchSuggestions");

symbolInput.addEventListener("input", () => {
    const val = symbolInput.value.trim().toUpperCase();
    if (!val) {
        searchSuggestions.style.display = "none";
        return;
    }

    const all = [...COIN_LIST.map(x => ({...x, type: "COIN"})), ...STOCK_LIST.map(x => ({...x, type: "STOCK"}))];
    const matches = all.filter(x => x.s.includes(val) || x.n.toUpperCase().includes(val));

    if (matches.length === 0) {
        searchSuggestions.style.display = "none";
        return;
    }

    searchSuggestions.innerHTML = "";
    matches.slice(0, 6).forEach(m => {
        const item = document.createElement("div");
        item.className = "suggestion-item";
        item.innerHTML = `
            <div>
                <strong>${m.s}</strong> &bull; <span style="color: var(--text-muted);">${m.n}</span>
            </div>
            <span class="pill" style="font-size: 10px;">${m.type}</span>
        `;
        item.onclick = () => {
            symbolInput.value = m.s;
            searchSuggestions.style.display = "none";
            runAnalysis();
        };
        searchSuggestions.appendChild(item);
    });
    searchSuggestions.style.display = "block";
});

document.addEventListener("click", (e) => {
    if (!searchSuggestions.contains(e.target) && e.target !== symbolInput) {
        searchSuggestions.style.display = "none";
    }
});

// Ask the Swarm & Interactive Scenario Simulator
function setScenarioQuestion(el) {
    document.getElementById("scenarioInput").value = el.textContent;
    askSwarmScenario();
}

async function askSwarmScenario() {
    const q = document.getElementById("scenarioInput").value.trim();
    if (!q) return;

    const btn = document.getElementById("btnAskSwarm");
    btn.innerHTML = "<span>⏳ Düşünülüyor...</span>";

    try {
        const url = `/api/ask?symbol=${encodeURIComponent(currentSymbol)}&question=${encodeURIComponent(q)}&lang=${currentLang}&asset_type=${currentCategory}`;
        const resp = await fetch(url);
        const data = await resp.json();

        document.getElementById("respAria").innerHTML = `📐 <strong>Aria Vance (Teknik):</strong> ${data.aria}`;
        document.getElementById("respMarcus").innerHTML = `📰 <strong>Marcus Cole (Makro):</strong> ${data.marcus}`;
        document.getElementById("respVesper").innerHTML = `🛡️ <strong>Vesper Sterling (Risk):</strong> ${data.vesper}`;
        document.getElementById("respSovereign").innerHTML = `⚖️ <strong>Sovereign AI (Konsensüs):</strong> ${data.sovereign}`;

        document.getElementById("scenarioResponseBox").style.display = "block";
    } catch (err) {
        showToast("Hata: " + err);
    } finally {
        btn.innerHTML = "<span>Danış ⚡</span>";
    }
}

function closeScenarioBox() {
    document.getElementById("scenarioResponseBox").style.display = "none";
}

// Copy Signal Card to Clipboard
function copySignalCard() {
    if (!currentVerdict || !currentMarketData) return;
    const v = currentVerdict;
    const m = currentMarketData;
    const cur = m.currency === "TRY" ? "₺" : "$";

    const text = `⚡ ALPHASWARM İSTİHBARAT KONSENSÜSÜ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Varlık: ${v.symbol} / ${m.currency}
📊 Duruş: ${v.final_stance} (%${v.confidence_score} Güven)
💵 Fiyat: ${cur}${m.current_price.toLocaleString(undefined, {minimumFractionDigits: 2})}
🎯 Hedef 1 (TP1): ${cur}${v.take_profit_1.toLocaleString(undefined, {minimumFractionDigits: 2})}
🎯 Hedef 2 (TP2): ${cur}${v.take_profit_2.toLocaleString(undefined, {minimumFractionDigits: 2})}
🛑 Zarar Kes (Stop): ${cur}${v.key_invalidation_level.toLocaleString(undefined, {minimumFractionDigits: 2})}
⚖️ Risk / Ödül: 1 : ${v.risk_reward_ratio}
🛡️ Destek / Direnç: S: ${cur}${v.support_level} | R: ${cur}${v.resistance_level}
📌 Konsensüs Özeti: ${v.primary_thesis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 AlphaSwarm Platformu (umutgungorr/alphaswarm)`;

    navigator.clipboard.writeText(text).then(() => {
        showToast("📋 Sinyal Kartı Panoya Kopyalandı!");
    }).catch(() => {
        showToast("Kopyalama başarısız oldu.");
    });
}

function showToast(msg) {
    const toast = document.getElementById("toastMsg");
    toast.textContent = msg;
    toast.style.display = "block";
    setTimeout(() => { toast.style.display = "none"; }, 2800);
}

function downloadReport(fmt) {
    window.open(`/api/report/${fmt}?symbol=${encodeURIComponent(currentSymbol)}&asset_type=${currentCategory}&lang=${currentLang}`, '_blank');
}

window.addEventListener("DOMContentLoaded", () => {
    renderWatchlist();
    renderPills();
    renderRadarTable();
    runAnalysis();
});

window.addEventListener("resize", () => {
    if (currentCandles.length > 0 && currentVerdict) {
        const cur = currentCategory === "CRYPTO" ? "$" : (currentMarketData && currentMarketData.currency === "TRY" ? "₺" : "$");
        drawCanvasChart(currentCandles, currentMarketData ? currentMarketData.indicators : null, currentVerdict, cur);
    }
});
</script>

</body>
</html>
"""


class AlphaSwarmHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        elif parsed.path == "/api/analyze":
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            asset_type = qs.get("asset_type", [None])[0]
            rounds = int(qs.get("rounds", [2])[0])
            lang = qs.get("lang", ["tr"])[0].lower()

            try:
                market_data = get_market_data(symbol, asset_type=asset_type)
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"))
                return

            graph = AlphaSwarmGraph(max_rounds=rounds)
            verdict = graph.propagate(market_data, lang=lang)

            res = {
                "market_data": market_data.to_dict(),
                "verdict": verdict.to_dict(),
            }
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        elif parsed.path == "/api/ask":
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            question = qs.get("question", ["Bu fiyattan alım yapılır mı?"])[0].strip()
            asset_type = qs.get("asset_type", [None])[0]
            lang = qs.get("lang", ["tr"])[0].lower()

            try:
                market_data = get_market_data(symbol, asset_type=asset_type)
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"))
                return

            consultation = answer_user_scenario(market_data, question=question, lang=lang)
            body = json.dumps(consultation, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        elif parsed.path.startswith("/api/report/"):
            fmt = parsed.path.split("/")[-1]
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            asset_type = qs.get("asset_type", [None])[0]
            lang = qs.get("lang", ["tr"])[0].lower()

            try:
                market_data = get_market_data(symbol, asset_type=asset_type)
            except ValueError as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
                return

            graph = AlphaSwarmGraph(max_rounds=2)
            verdict = graph.propagate(market_data, lang=lang)

            if fmt == "html":
                content = generate_html_report(verdict, market_data)
                mime = "text/html; charset=utf-8"
            else:
                content = generate_markdown_report(verdict, market_data)
                mime = "text/markdown; charset=utf-8"

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        return


def start_server(port: int = 5050):
    server_address = ("", port)
    with socketserver.TCPServer(server_address, AlphaSwarmHandler) as httpd:
        print(f"\033[1m\033[36m⚡ AlphaSwarm Interactive Dashboard is live at:\033[0m")
        print(f"   \033[32mhttp://localhost:{port}\033[0m (or http://127.0.0.1:{port})")
        print("   Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down AlphaSwarm server.")
