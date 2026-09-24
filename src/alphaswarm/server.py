"""Interactive Web Dashboard server for AlphaSwarm."""

import http.server
import json
import socketserver
import sys
import urllib.parse
from pathlib import Path
from alphaswarm.graph import AlphaSwarmGraph
from alphaswarm.market_data import get_market_data
from alphaswarm.reporters import generate_html_report, generate_markdown_report


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AlphaSwarm ⚡ Autonomous Multi-Agent Consensus Hub</title>
<style>
    :root {
        --bg-main: #090d16;
        --bg-card: #111827;
        --border-color: #1f2937;
        --text-primary: #f8fafc;
        --text-muted: #94a3b8;
        --cyan: #38bdf8;
        --green: #10b981;
        --red: #ef4444;
        --yellow: #eab308;
        --purple: #c084fc;
    }
    * { box-sizing: border-box; }
    body {
        background: var(--bg-main);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin: 0;
        padding: 0;
    }
    header {
        background: rgba(17, 24, 39, 0.85);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-color);
        padding: 18px 32px;
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
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    .brand-title { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
    .brand-tag { font-size: 11px; background: rgba(56, 189, 248, 0.15); color: var(--cyan); padding: 3px 8px; border-radius: 4px; font-weight: 700; }
    
    .container {
        max-width: 1200px;
        margin: 32px auto;
        padding: 0 24px;
    }
    .control-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 28px;
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        align-items: center;
    }
    .input-group {
        display: flex;
        gap: 8px;
        flex: 1;
        min-width: 280px;
    }
    input[type="text"] {
        flex: 1;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 16px;
        color: #fff;
        font-size: 16px;
        font-weight: 600;
        text-transform: uppercase;
        outline: none;
    }
    input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2); }
    select {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        color: #fff;
        font-size: 14px;
        outline: none;
    }
    button.btn-primary {
        background: linear-gradient(135deg, #0284c7, #0ea5e9);
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 12px 28px;
        font-size: 15px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    button.btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
    button.btn-primary:active { transform: translateY(0); }
    
    .quick-picks {
        display: flex;
        gap: 8px;
        align-items: center;
        width: 100%;
    }
    .quick-pick-btn {
        background: #1e293b;
        border: 1px solid #334155;
        color: var(--text-muted);
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
    }
    .quick-pick-btn:hover { color: #fff; border-color: var(--cyan); }
    
    .grid-layout {
        display: grid;
        grid-template-columns: 340px 1fr;
        gap: 24px;
    }
    @media (max-width: 900px) {
        .grid-layout { grid-template-columns: 1fr; }
    }
    
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .card-title {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-muted);
        font-weight: 700;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #1e293b;
        font-size: 14px;
    }
    .stat-row:last-child { border-bottom: none; }
    .stat-val { font-weight: 700; color: #fff; }
    
    .consensus-banner {
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #334155;
        background: #1e293b;
    }
    .consensus-stance { font-size: 26px; font-weight: 900; margin-bottom: 8px; }
    .consensus-thesis { font-size: 15px; color: #cbd5e1; line-height: 1.6; }
    
    .debate-stream {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .agent-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        transition: transform 0.2s ease;
    }
    .agent-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .agent-avatar { font-size: 26px; }
    .agent-name { font-weight: 800; font-size: 16px; }
    .agent-role { font-size: 12px; color: var(--text-muted); }
    .agent-badge {
        margin-left: auto;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 800;
    }
    .agent-thesis { font-size: 14px; color: #e2e8f0; line-height: 1.5; margin-bottom: 12px; font-style: italic; }
    .bullet-list { margin: 0; padding-left: 20px; font-size: 13px; color: #94a3b8; line-height: 1.6; }
    .bullet-risk { color: #f87171; }
    
    .loading-spinner {
        display: none;
        text-align: center;
        padding: 48px;
        color: var(--cyan);
        font-size: 18px;
        font-weight: 700;
    }
    .actions-bar {
        display: flex;
        gap: 12px;
        margin-top: 20px;
    }
</style>
</head>
<body>

<header>
    <div class="brand">
        <div class="brand-icon">⚡</div>
        <div>
            <div class="brand-title">ALPHASWARM</div>
            <div style="color: var(--text-muted); font-size: 11px;">Autonomous Multi-Agent Consensus Hub</div>
        </div>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
        <span class="brand-tag">v0.1.0 CANLI</span>
        <a href="https://github.com/umutgungorr/alphaswarm" target="_blank" style="color: var(--text-muted); font-size: 13px; text-decoration: none;">GitHub Repo ↗</a>
    </div>
</header>

<div class="container">
    <div class="control-panel">
        <div class="input-group">
            <input type="text" id="symbolInput" value="BTC" placeholder="Sembol (BTC, ETH, NVDA, SOL)">
            <select id="roundsSelect">
                <option value="1">1 Münazara Turu</option>
                <option value="2" selected>2 Münazara Turu (Derin)</option>
                <option value="3">3 Münazara Turu (Ultra)</option>
            </select>
            <button class="btn-primary" id="launchBtn" onclick="runAnalysis()">
                <span>🚀 Analizi Başlat</span>
            </button>
        </div>
        <div class="quick-picks">
            <span style="font-size: 12px; color: var(--text-muted);">Hızlı Seçim:</span>
            <button class="quick-pick-btn" onclick="selectSymbol('BTC')">BTC</button>
            <button class="quick-pick-btn" onclick="selectSymbol('ETH')">ETH</button>
            <button class="quick-pick-btn" onclick="selectSymbol('SOL')">SOL</button>
            <button class="quick-pick-btn" onclick="selectSymbol('NVDA')">NVDA</button>
            <button class="quick-pick-btn" onclick="selectSymbol('AAPL')">AAPL</button>
        </div>
    </div>

    <div id="loading" class="loading-spinner">
        ⚡ Ajan Swarm'ı toplanıyor ve piyasa telemetrisi hesaplanıyor...
    </div>

    <div id="resultsArea">
        <div id="consensusBanner" class="consensus-banner">
            <div class="consensus-stance" id="verdictStance">CONSENSUS YÜKLENİYOR...</div>
            <div class="consensus-thesis" id="verdictThesis">Analiz başlatmak için yukarıdaki butona tıklayın.</div>
            <div class="actions-bar" id="actionsBar" style="display: none;">
                <button class="quick-pick-btn" style="color: var(--cyan); border-color: var(--cyan);" onclick="downloadReport('html')">📥 HTML Raporu İndir</button>
                <button class="quick-pick-btn" onclick="downloadReport('md')">📄 Markdown Olarak Al</button>
            </div>
        </div>

        <div class="grid-layout">
            <div>
                <div class="card">
                    <div class="card-title">Piyasa Telemetrisi</div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">Son Fiyat</span>
                        <span class="stat-val" id="statPrice">$0.00</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">24 Saat Değişim</span>
                        <span class="stat-val" id="statChange">0.00%</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">RSI (14-Gün)</span>
                        <span class="stat-val" id="statRSI">50.0</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">50 / 200 SMA</span>
                        <span class="stat-val" id="statSMA">NEUTRAL</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">Bollinger Bandı</span>
                        <span class="stat-val" id="statBB">$0 - $0</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">Stop Invalidation</span>
                        <span class="stat-val" id="statInval" style="color: var(--red);">$0.00</span>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">Swarm Ajanları</div>
                    <div style="font-size: 13px; line-height: 1.8; color: var(--text-muted);">
                        <div>📐 <strong>Aria Vance</strong> &bull; Quant / Momentum</div>
                        <div>📰 <strong>Marcus Cole</strong> &bull; Macro & Sentiment</div>
                        <div>🛡️ <strong>Vesper Sterling</strong> &bull; Devil's Advocate</div>
                        <div>⚖️ <strong>Sovereign AI</strong> &bull; Arbitrator Node</div>
                    </div>
                </div>
            </div>

            <div>
                <div class="card">
                    <div class="card-title">Canlı Ajan Münazara Arenası</div>
                    <div class="debate-stream" id="debateStream">
                        <!-- Agent bubbles injected here -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
let currentSymbol = "BTC";

function selectSymbol(sym) {
    document.getElementById("symbolInput").value = sym;
    runAnalysis();
}

async function runAnalysis() {
    const symbol = document.getElementById("symbolInput").value.trim().toUpperCase() || "BTC";
    currentSymbol = symbol;
    const rounds = document.getElementById("roundsSelect").value;

    document.getElementById("loading").style.display = "block";
    document.getElementById("resultsArea").style.opacity = "0.3";

    try {
        const resp = await fetch(`/api/analyze?symbol=${symbol}&rounds=${rounds}`);
        const data = await resp.json();
        renderResults(data);
    } catch (err) {
        alert("Analiz hatası: " + err);
    } finally {
        document.getElementById("loading").style.display = "none";
        document.getElementById("resultsArea").style.opacity = "1.0";
    }
}

function renderResults(data) {
    const v = data.verdict;
    const m = data.market_data;
    const ind = m.indicators;

    const isBull = v.final_stance.includes("BULL");
    const isBear = v.final_stance.includes("BEAR");
    const color = isBull ? "var(--green)" : (isBear ? "var(--red)" : "var(--yellow)");

    const banner = document.getElementById("consensusBanner");
    banner.style.borderLeft = `6px solid ${color}`;
    document.getElementById("verdictStance").textContent = `${v.final_stance} (%${v.confidence_score} Güven)`;
    document.getElementById("verdictStance").style.color = color;
    document.getElementById("verdictThesis").textContent = v.primary_thesis;
    document.getElementById("actionsBar").style.display = "flex";

    // Stats
    document.getElementById("statPrice").textContent = `$${m.current_price.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    const chgEl = document.getElementById("statChange");
    chgEl.textContent = `${m.change_24h_pct >= 0 ? '+' : ''}${m.change_24h_pct.toFixed(2)}%`;
    chgEl.style.color = m.change_24h_pct >= 0 ? "var(--green)" : "var(--red)";
    
    document.getElementById("statRSI").textContent = ind.rsi_14.toFixed(1);
    document.getElementById("statSMA").textContent = ind.trend_50_200;
    document.getElementById("statBB").textContent = `$${ind.bollinger_lower.toLocaleString()} - $${ind.bollinger_upper.toLocaleString()}`;
    document.getElementById("statInval").textContent = `$${v.key_invalidation_level.toLocaleString(undefined, {minimumFractionDigits: 2})}`;

    // Debate Arena
    const stream = document.getElementById("debateStream");
    stream.innerHTML = "";

    v.debate_rounds.forEach(r => {
        const roundTitle = document.createElement("div");
        roundTitle.style.cssText = "font-size: 12px; color: var(--cyan); text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin: 12px 0 6px 0;";
        roundTitle.textContent = `▶ Münazara Turu #${r.round_number} (${r.consensus_shift_notes})`;
        stream.appendChild(roundTitle);

        r.thoughts.forEach(t => {
            const isTBull = t.stance.includes("BULL");
            const isTBear = t.stance.includes("BEAR");
            const tColor = isTBull ? "var(--green)" : (isTBear ? "var(--red)" : "var(--yellow)");
            const icon = t.role === "TECHNICAL" ? "📐" : (t.role === "SENTIMENT" ? "📰" : "🛡️");

            const card = document.createElement("div");
            card.className = "agent-card";
            card.innerHTML = `
                <div class="agent-header">
                    <span class="agent-avatar">${icon}</span>
                    <div>
                        <div class="agent-name">${t.agent_name}</div>
                        <div class="agent-role">[${t.callsign}] &bull; ${t.role}</div>
                    </div>
                    <span class="agent-badge" style="background: ${tColor}22; color: ${tColor}; border: 1px solid ${tColor}66;">
                        ${t.stance} (%${Math.round(t.confidence * 100)})
                    </span>
                </div>
                <div class="agent-thesis">"${t.thesis}"</div>
                <ul class="bullet-list">
                    ${t.key_points.map(p => `<li>${p}</li>`).join("")}
                    ${t.identified_risks.map(rk => `<li class="bullet-risk">⚠️ ${rk}</li>`).join("")}
                </ul>
            `;
            stream.appendChild(card);
        });
    });
}

function downloadReport(fmt) {
    window.open(`/api/report/${fmt}?symbol=${currentSymbol}`, '_blank');
}

// Auto run on load
window.addEventListener("DOMContentLoaded", () => {
    runAnalysis();
});
</script>

</body>
</html>
"""


class AlphaSwarmHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        elif parsed.path == "/api/analyze":
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            rounds = int(qs.get("rounds", [1])[0])
            rounds = max(1, min(rounds, 3))

            market_data = get_market_data(symbol)
            graph = AlphaSwarmGraph(max_rounds=rounds)
            verdict = graph.propagate(market_data)

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

        elif parsed.path.startswith("/api/report/"):
            fmt = parsed.path.split("/")[-1]
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            market_data = get_market_data(symbol)
            graph = AlphaSwarmGraph(max_rounds=2)
            verdict = graph.propagate(market_data)

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
        # Silence default request spam in logs
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
