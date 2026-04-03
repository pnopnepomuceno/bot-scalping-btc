"""
Dashboard Web para Bot de Scalping Multi-Par
Acesse: http://localhost:5000
Requisitos: pip install flask
"""
from flask import Flask, jsonify, render_template_string
import os, json, re
from datetime import datetime

app = Flask(__name__)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log")

HTML = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ScalpBot Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --bg:#08080f;--bg2:#0f0f1a;--bg3:#16162a;--bg4:#1e1e35;
  --border:#2a2a45;--green:#00e87a;--red:#ff3d5a;--blue:#4d9fff;
  --amber:#ffaa00;--purple:#a855f7;--text:#e0e0f0;--muted:#6060a0;
  --mono:'Space Mono',monospace;--sans:'DM Sans',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden}

/* Header */
header{background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:52px;position:sticky;top:0;z-index:100}
.logo{font-family:var(--mono);font-size:13px;letter-spacing:.12em;color:var(--green);display:flex;align-items:center;gap:10px}
.logo-dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(0,232,122,.4)}50%{opacity:.6;box-shadow:0 0 0 6px rgba(0,232,122,0)}}
.header-right{display:flex;align-items:center;gap:12px}
.status-chip{font-family:var(--mono);font-size:10px;letter-spacing:.08em;padding:4px 10px;border-radius:99px;border:1px solid var(--border);background:var(--bg3);color:var(--muted)}
.status-chip.on{border-color:var(--green);color:var(--green);background:rgba(0,232,122,.08)}
.status-chip.off{border-color:var(--red);color:var(--red);background:rgba(255,61,90,.08)}
.ts{font-family:var(--mono);font-size:11px;color:var(--muted)}

/* Ticker */
.ticker{background:var(--bg2);border-bottom:1px solid var(--border);display:flex;overflow-x:auto;scrollbar-width:none}
.ticker::-webkit-scrollbar{display:none}
.ticker-item{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px 20px;border-right:1px solid var(--border);min-width:130px;cursor:default;transition:background .15s;flex-shrink:0}
.ticker-item:hover{background:var(--bg3)}
.ticker-item.active-ticker{background:rgba(77,159,255,.08);border-bottom:2px solid var(--blue)}
.ticker-sym{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.1em;margin-bottom:3px}
.ticker-price{font-family:var(--mono);font-size:14px;font-weight:700;color:var(--text)}
.ticker-change{font-family:var(--mono);font-size:10px;margin-top:2px}
.ticker-change.pos{color:var(--green)}
.ticker-change.neg{color:var(--red)}

/* Layout */
main{padding:18px 20px;display:flex;flex-direction:column;gap:14px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:16px}
.card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.card-title{font-family:var(--mono);font-size:10px;letter-spacing:.12em;color:var(--muted)}

/* Par ativo */
.active-pair{background:linear-gradient(135deg,var(--bg2) 0%,var(--bg3) 100%);border:1px solid var(--border);border-radius:12px;padding:14px 20px;display:flex;align-items:center;justify-content:space-between}
.pair-name{font-family:var(--mono);font-size:22px;font-weight:700;color:var(--blue)}
.pair-meta{display:flex;gap:20px}
.pair-stat{text-align:right}
.pair-stat-label{font-size:10px;color:var(--muted);letter-spacing:.1em}
.pair-stat-val{font-family:var(--mono);font-size:16px;font-weight:700}
.pair-scanner{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.pair-badge{font-family:var(--mono);font-size:10px;padding:3px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg4);color:var(--muted);cursor:default}
.pair-badge.active{border-color:var(--blue);color:var(--blue);background:rgba(77,159,255,.1)}
.pair-badge.best{border-color:var(--green);color:var(--green);background:rgba(0,232,122,.08)}

/* Métricas */
.metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
.metric{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.metric-label{font-size:10px;letter-spacing:.1em;color:var(--muted);margin-bottom:6px;font-family:var(--mono)}
.metric-val{font-family:var(--mono);font-size:18px;font-weight:700;color:var(--text)}
.metric-val.g{color:var(--green)}
.metric-val.r{color:var(--red)}
.metric-val.b{color:var(--blue)}
.metric-val.a{color:var(--amber)}
.metric-sub{font-size:11px;color:var(--muted);margin-top:3px;font-family:var(--mono)}

/* Grid layouts */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.grid-60-40{display:grid;grid-template-columns:1fr 360px;gap:14px}

/* Chart */
.chart-wrap{position:relative;height:200px}

/* Tabela de operações */
.ops-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px}
.ops-table th{color:var(--muted);font-size:9px;letter-spacing:.1em;padding:6px 10px;text-align:left;border-bottom:1px solid var(--border)}
.ops-table td{padding:7px 10px;border-bottom:1px solid rgba(42,42,69,.4)}
.ops-table tr:last-child td{border-bottom:none}
.ops-table tr:hover td{background:var(--bg3)}
.ops-scroll{overflow-y:auto;max-height:280px}
.tag{font-size:9px;padding:2px 6px;border-radius:4px;font-weight:700}
.tag-buy{background:rgba(0,232,122,.12);color:var(--green)}
.tag-sell{background:rgba(255,61,90,.12);color:var(--red)}
.tag-sym{background:var(--bg4);color:var(--blue);border:1px solid rgba(77,159,255,.3)}
.tag-tp{background:rgba(0,232,122,.1);color:var(--green)}
.tag-sl{background:rgba(255,61,90,.1);color:var(--red)}
.tag-ia{background:rgba(168,85,247,.1);color:var(--purple)}
.pnl-pos{color:var(--green);font-weight:700}
.pnl-neg{color:var(--red);font-weight:700}

/* Resumo por par */
.pair-stats-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.pair-stat-box{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.psb-name{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--blue);margin-bottom:6px}
.psb-row{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;margin-bottom:3px}
.psb-key{color:var(--muted)}
.psb-val{color:var(--text)}

/* Posição aberta */
.pos-none{color:var(--muted);font-family:var(--mono);font-size:12px;text-align:center;padding:16px 0}
.pos-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(42,42,69,.5)}
.pos-row:last-child{border-bottom:none}
.pos-key{font-size:11px;color:var(--muted);font-family:var(--mono)}
.pos-val{font-size:12px;font-weight:600;font-family:var(--mono)}

/* Scanner */
.scanner-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px}
.scanner-table th{color:var(--muted);font-size:9px;letter-spacing:.1em;padding:4px 8px;text-align:left;border-bottom:1px solid var(--border)}
.scanner-table td{padding:6px 8px;border-bottom:1px solid rgba(42,42,69,.5)}
.scanner-table tr:last-child td{border-bottom:none}
.scanner-table tr.best-row td{color:var(--green)}
.score-bar{height:4px;border-radius:2px;background:var(--bg4);overflow:hidden;margin-top:3px}
.score-fill{height:100%;border-radius:2px;background:var(--blue)}
.score-fill.best{background:var(--green)}

/* Log */
.log-inner{height:150px;overflow-y:auto;font-family:var(--mono);font-size:10px;display:flex;flex-direction:column;gap:2px}
.log-line{color:var(--muted);line-height:1.6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.log-line.buy{color:var(--green)}
.log-line.sell{color:var(--red)}
.log-line.warn{color:var(--amber)}
.log-line.err{color:var(--red);opacity:.8}
.log-line.scan{color:var(--purple)}
.log-line.ia{color:var(--blue)}

/* Tabs */
.tabs{display:flex;gap:6px;margin-bottom:12px}
.tab-btn{font-family:var(--mono);font-size:9px;padding:4px 10px;border-radius:4px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer}
.tab-btn.active{border-color:var(--blue);color:var(--blue);background:rgba(77,159,255,.1)}
.tab-panel{display:none}
.tab-panel.active{display:block}

::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.empty{color:var(--muted);font-family:var(--mono);font-size:11px;text-align:center;padding:20px 0}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-dot" id="logo-dot" style="background:var(--muted);animation:none"></div>
    SCALPBOT / MULTI-PAR
  </div>
  <div class="header-right">
    <span class="ts" id="last-ts">—</span>
    <div class="status-chip" id="status-chip">VERIFICANDO</div>
  </div>
</header>

<!-- Ticker -->
<div class="ticker" id="ticker-bar">
  <div class="ticker-item" id="tick-BTCUSDT"><div class="ticker-sym">BTC</div><div class="ticker-price">—</div><div class="ticker-change">—</div></div>
  <div class="ticker-item" id="tick-ETHUSDT"><div class="ticker-sym">ETH</div><div class="ticker-price">—</div><div class="ticker-change">—</div></div>
  <div class="ticker-item" id="tick-BNBUSDT"><div class="ticker-sym">BNB</div><div class="ticker-price">—</div><div class="ticker-change">—</div></div>
  <div class="ticker-item" id="tick-SOLUSDT"><div class="ticker-sym">SOL</div><div class="ticker-price">—</div><div class="ticker-change">—</div></div>
  <div class="ticker-item" id="tick-XRPUSDT"><div class="ticker-sym">XRP</div><div class="ticker-price">—</div><div class="ticker-change">—</div></div>
</div>

<main>

  <!-- Par ativo -->
  <div class="active-pair">
    <div>
      <div style="font-size:10px;color:var(--muted);font-family:var(--mono);letter-spacing:.1em;margin-bottom:6px">PAR ATIVO</div>
      <div class="pair-name" id="active-sym">—</div>
      <div class="pair-scanner" id="pair-badges" style="margin-top:8px"></div>
    </div>
    <div class="pair-meta">
      <div class="pair-stat"><div class="pair-stat-label">PREÇO</div><div class="pair-stat-val b" id="h-price">—</div></div>
      <div class="pair-stat"><div class="pair-stat-label">RSI</div><div class="pair-stat-val" id="h-rsi">—</div></div>
      <div class="pair-stat"><div class="pair-stat-label">MACD</div><div class="pair-stat-val" id="h-macd">—</div></div>
      <div class="pair-stat"><div class="pair-stat-label">BB%</div><div class="pair-stat-val" id="h-bb">—</div></div>
    </div>
  </div>

  <!-- Métricas -->
  <div class="metrics">
    <div class="metric"><div class="metric-label">PNL TOTAL</div><div class="metric-val" id="m-pnl">$0.0000</div><div class="metric-sub" id="m-pnl-sub">—</div></div>
    <div class="metric"><div class="metric-label">MELHOR OP</div><div class="metric-val g" id="m-best">—</div><div class="metric-sub" id="m-best-sub">—</div></div>
    <div class="metric"><div class="metric-label">PIOR OP</div><div class="metric-val r" id="m-worst">—</div><div class="metric-sub" id="m-worst-sub">—</div></div>
    <div class="metric"><div class="metric-label">WIN RATE</div><div class="metric-val" id="m-wr">—</div><div class="metric-sub" id="m-wr-sub">0W / 0L</div></div>
    <div class="metric"><div class="metric-label">SALDO USDT</div><div class="metric-val b" id="m-usdt">—</div><div class="metric-sub" id="m-ops">0 operações</div></div>
    <div class="metric"><div class="metric-label">POSIÇÃO</div><div class="metric-val" id="m-pos">NENHUMA</div><div class="metric-sub" id="m-pos-sub">—</div></div>
  </div>

  <!-- Gráfico + Posição aberta -->
  <div class="grid-60-40">
    <div class="card">
      <div class="card-head"><div class="card-title">PNL ACUMULADO POR OPERAÇÃO</div></div>
      <div class="chart-wrap"><canvas id="pnl-chart"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title" style="margin-bottom:10px">POSIÇÃO ABERTA</div>
      <div id="pos-detail"><div class="pos-none">Nenhuma posição aberta</div></div>
    </div>
  </div>

  <!-- Operações detalhadas -->
  <div class="card">
    <div class="card-head">
      <div class="card-title">OPERAÇÕES</div>
      <div class="tabs" id="ops-tabs">
        <button class="tab-btn active" onclick="switchTab('all')">TODAS</button>
        <button class="tab-btn" onclick="switchTab('wins')">GANHOS</button>
        <button class="tab-btn" onclick="switchTab('losses')">PERDAS</button>
        <button class="tab-btn" onclick="switchTab('open')">ABERTA</button>
      </div>
    </div>

    <!-- Aba: Todas -->
    <div class="tab-panel active" id="tab-all">
      <div class="ops-scroll">
        <table class="ops-table">
          <thead>
            <tr>
              <th>#</th><th>PAR</th><th>ENTRADA</th><th>SAÍDA</th>
              <th>QUANTIDADE</th><th>VALOR</th><th>PNL</th><th>MOTIVO</th><th>DATA/HORA</th>
            </tr>
          </thead>
          <tbody id="ops-tbody-all">
            <tr><td colspan="9" class="empty">nenhuma operação ainda</td></tr>
          </tbody>
        </table>
      </div>
      <div id="ops-summary" style="display:flex;gap:20px;margin-top:12px;padding-top:10px;border-top:1px solid var(--border)">
      </div>
    </div>

    <!-- Aba: Ganhos -->
    <div class="tab-panel" id="tab-wins">
      <div class="ops-scroll">
        <table class="ops-table">
          <thead>
            <tr><th>#</th><th>PAR</th><th>ENTRADA</th><th>SAÍDA</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>DATA/HORA</th></tr>
          </thead>
          <tbody id="ops-tbody-wins">
            <tr><td colspan="8" class="empty">nenhum ganho ainda</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Aba: Perdas -->
    <div class="tab-panel" id="tab-losses">
      <div class="ops-scroll">
        <table class="ops-table">
          <thead>
            <tr><th>#</th><th>PAR</th><th>ENTRADA</th><th>SAÍDA</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>DATA/HORA</th></tr>
          </thead>
          <tbody id="ops-tbody-losses">
            <tr><td colspan="8" class="empty">nenhuma perda ainda</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Aba: Posição aberta -->
    <div class="tab-panel" id="tab-open">
      <div id="tab-open-content"><div class="empty">nenhuma posição aberta</div></div>
    </div>
  </div>

  <!-- Resumo por par -->
  <div class="card">
    <div class="card-head"><div class="card-title">DESEMPENHO POR PAR</div></div>
    <div class="pair-stats-grid" id="pair-perf"></div>
  </div>

  <!-- Scanner + Log -->
  <div class="grid-60-40">
    <div class="card">
      <div class="card-head">
        <div class="card-title">SCANNER DE MERCADO</div>
        <div class="ts" id="scan-ts">—</div>
      </div>
      <table class="scanner-table">
        <thead><tr><th>PAR</th><th>SCORE</th><th>VARIAÇÃO</th><th>VOLUME</th><th>VOLATILIDADE</th></tr></thead>
        <tbody id="scanner-body"><tr><td colspan="5" style="color:var(--muted);text-align:center;padding:12px">aguardando scanner...</td></tr></tbody>
      </table>
    </div>
    <div class="card">
      <div class="card-head">
        <div class="card-title">LOG EM TEMPO REAL</div>
        <div class="ts" id="log-count">0 linhas</div>
      </div>
      <div class="log-inner" id="log-inner"><div class="log-line">aguardando bot...</div></div>
    </div>
  </div>

</main>

<script>
let pnlChart = null;
let allTrades = [];
let currentTab = 'all';

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-'+tab).classList.add('active');
  document.querySelectorAll('.tab-btn').forEach(b => { if(b.textContent === tab.toUpperCase() || (tab==='all'&&b.textContent==='TODAS') || (tab==='wins'&&b.textContent==='GANHOS') || (tab==='losses'&&b.textContent==='PERDAS') || (tab==='open'&&b.textContent==='ABERTA')) b.classList.add('active'); });
}

function initChart() {
  const ctx = document.getElementById('pnl-chart').getContext('2d');
  pnlChart = new Chart(ctx, {
    type: 'line',
    data: { labels: [], datasets: [
      { data: [], borderColor: '#00e87a', backgroundColor: 'rgba(0,232,122,0.06)', borderWidth: 1.5, pointRadius: 3, pointBackgroundColor: '#00e87a', fill: true, tension: 0.4, label: 'PnL acumulado' },
      { data: [], borderColor: '#4d9fff', backgroundColor: 'transparent', borderWidth: 1, pointRadius: 2, pointBackgroundColor: '#4d9fff', fill: false, tension: 0, label: 'PnL por op' }
    ]},
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: true, labels: { color: '#6060a0', font: { family: 'Space Mono', size: 8 }, boxWidth: 12 } } },
      scales: {
        x: { ticks: { color: '#6060a0', font: { family: 'Space Mono', size: 8 } }, grid: { color: '#16162a' } },
        y: { ticks: { color: '#6060a0', font: { family: 'Space Mono', size: 8 }, callback: v => '$'+v.toFixed(3) }, grid: { color: '#16162a' } }
      }
    }
  });
}

function fmt(n, d=2) { return Number(n).toLocaleString('pt-BR', {minimumFractionDigits:d, maximumFractionDigits:d}); }

function reasonTag(reason) {
  if (!reason) return '';
  if (reason.includes('TAKE_PROFIT') || reason.includes('take_profit')) return '<span class="tag tag-tp">TP</span>';
  if (reason.includes('STOP_LOSS') || reason.includes('stop_loss')) return '<span class="tag tag-sl">SL</span>';
  if (reason.includes('[FB]')) return '<span class="tag tag-ia" style="color:var(--amber)">FB</span>';
  return '<span class="tag tag-ia">IA</span>';
}

function buildOpsRow(t, i) {
  const pnlCls = t.pnl >= 0 ? 'pnl-pos' : 'pnl-neg';
  const pct = t.entry > 0 ? ((t.pnl / (t.entry * (t.qty || 0.003))) * 100).toFixed(2) : '—';
  return `<tr>
    <td style="color:var(--muted)">${i+1}</td>
    <td><span class="tag tag-sym">${(t.symbol||'BTC').replace('USDT','')}</span></td>
    <td>$${fmt(t.entry,4)}</td>
    <td>${t.exit > 0 ? '$'+fmt(t.exit,4) : '<span style="color:var(--amber)">aberta</span>'}</td>
    <td style="color:var(--muted)">${t.qty || '—'}</td>
    <td style="color:var(--muted)">$${fmt(t.usdt_used||0)}</td>
    <td class="${pnlCls}">${t.pnl >= 0 ? '+' : ''}$${Number(t.pnl).toFixed(4)}</td>
    <td>${reasonTag(t.reason)}</td>
    <td style="color:var(--muted);font-size:9px">${(t.close||'').substring(0,19)}</td>
  </tr>`;
}

function buildSimpleRow(t, i) {
  const pnlCls = t.pnl >= 0 ? 'pnl-pos' : 'pnl-neg';
  const pct = t.entry > 0 && t.usdt_used > 0 ? ((t.pnl / t.usdt_used) * 100).toFixed(2) + '%' : '—';
  return `<tr>
    <td style="color:var(--muted)">${i+1}</td>
    <td><span class="tag tag-sym">${(t.symbol||'BTC').replace('USDT','')}</span></td>
    <td>$${fmt(t.entry,4)}</td>
    <td>${t.exit > 0 ? '$'+fmt(t.exit,4) : '—'}</td>
    <td class="${pnlCls}">${t.pnl >= 0 ? '+' : ''}$${Number(t.pnl).toFixed(4)}</td>
    <td class="${pnlCls}">${pct}</td>
    <td>${reasonTag(t.reason)}</td>
    <td style="color:var(--muted);font-size:9px">${(t.close||'').substring(0,19)}</td>
  </tr>`;
}

async function refresh() {
  try {
    const d = await fetch('/api/status').then(r => r.json());
    document.getElementById('last-ts').textContent = new Date().toLocaleTimeString('pt-BR');

    // Status
    const chip = document.getElementById('status-chip');
    const dot  = document.getElementById('logo-dot');
    if (d.bot_running) { chip.textContent='BOT ATIVO'; chip.className='status-chip on'; dot.style.background='var(--green)'; dot.style.animation=''; }
    else { chip.textContent='BOT INATIVO'; chip.className='status-chip off'; dot.style.background='var(--red)'; dot.style.animation='none'; }

    // Par ativo
    document.getElementById('active-sym').textContent = d.active_symbol || '—';
    document.getElementById('h-price').textContent = d.price ? '$'+fmt(d.price,4) : '—';
    const rsiEl = document.getElementById('h-rsi');
    rsiEl.textContent = d.rsi || '—';
    rsiEl.style.color = d.rsi < 35 ? 'var(--green)' : d.rsi > 65 ? 'var(--red)' : 'var(--amber)';
    const macdEl = document.getElementById('h-macd');
    macdEl.textContent = d.macd_signal || '—';
    macdEl.style.color = d.macd_signal === 'bullish' ? 'var(--green)' : 'var(--red)';
    const bbEl = document.getElementById('h-bb');
    bbEl.textContent = d.bb_pct ? d.bb_pct+'%' : '—';
    bbEl.style.color = d.bb_pct < 30 ? 'var(--green)' : d.bb_pct > 70 ? 'var(--red)' : 'var(--amber)';

    // Badges
    if (d.watch_pairs) {
      document.getElementById('pair-badges').innerHTML = d.watch_pairs.map(p => {
        const isActive = p === d.active_symbol;
        const score = d.scanner_scores?.[p];
        const isBest = score && score === Math.max(...Object.values(d.scanner_scores||{}));
        return `<div class="pair-badge ${isActive?'active':''} ${isBest&&!isActive?'best':''}">${p.replace('USDT','')}${score?' '+score:''}</div>`;
      }).join('');
    }

    // Métricas
    const pnlEl = document.getElementById('m-pnl');
    pnlEl.textContent = (d.pnl>=0?'+':'')+'$'+Number(d.pnl).toFixed(4);
    pnlEl.className = 'metric-val '+(d.pnl>0?'g':d.pnl<0?'r':'');

    const trades = d.trades || [];
    allTrades = trades;
    const wins   = trades.filter(t => t.pnl > 0);
    const losses = trades.filter(t => t.pnl < 0);
    const best   = wins.length   ? wins.reduce((a,b) => b.pnl>a.pnl?b:a)   : null;
    const worst  = losses.length ? losses.reduce((a,b) => b.pnl<a.pnl?b:a) : null;

    document.getElementById('m-best').textContent  = best  ? '+$'+best.pnl.toFixed(4)  : '—';
    document.getElementById('m-best-sub').textContent  = best  ? (best.symbol||'').replace('USDT','')  : '—';
    document.getElementById('m-worst').textContent = worst ? '$'+worst.pnl.toFixed(4) : '—';
    document.getElementById('m-worst-sub').textContent = worst ? (worst.symbol||'').replace('USDT','') : '—';

    const total = d.wins + d.losses;
    const wr = total > 0 ? Math.round(d.wins/total*100) : null;
    const wrEl = document.getElementById('m-wr');
    wrEl.textContent = wr !== null ? wr+'%' : '—';
    wrEl.className = 'metric-val '+(wr>=55?'g':wr!==null&&wr<45?'r':'a');
    document.getElementById('m-wr-sub').textContent = d.wins+'W / '+d.losses+'L';
    document.getElementById('m-usdt').textContent = d.usdt ? '$'+fmt(d.usdt) : '—';
    document.getElementById('m-ops').textContent = trades.length+' operações';

    // Posição
    const posEl = document.getElementById('m-pos');
    const posDetail = document.getElementById('pos-detail');
    const tabOpenContent = document.getElementById('tab-open-content');
    if (d.position) {
      const pct = d.price ? ((d.price-d.position.entry_price)/d.position.entry_price*100) : 0;
      posEl.textContent = d.position.symbol||'ABERTA'; posEl.className='metric-val g';
      document.getElementById('m-pos-sub').textContent = 'entrada $'+fmt(d.position.entry_price,4);
      const posHTML = `
        <div class="pos-row"><span class="pos-key">Par</span><span class="pos-val b">${d.position.symbol||'—'}</span></div>
        <div class="pos-row"><span class="pos-key">Entrada</span><span class="pos-val">$${fmt(d.position.entry_price,4)}</span></div>
        <div class="pos-row"><span class="pos-key">Quantidade</span><span class="pos-val">${d.position.qty||'—'}</span></div>
        <div class="pos-row"><span class="pos-key">Valor usado</span><span class="pos-val">$${fmt(d.position.usdt_used||0)}</span></div>
        <div class="pos-row"><span class="pos-key">PnL atual</span><span class="pos-val ${pct>=0?'g':'r'}">${pct>=0?'+':''}${pct.toFixed(2)}%</span></div>
        <div class="pos-row"><span class="pos-key">Preço atual</span><span class="pos-val b">$${d.price?fmt(d.price,4):'—'}</span></div>
        <div class="pos-row"><span class="pos-key">Stop-loss</span><span class="pos-val r">$${fmt(d.position.entry_price*0.995,4)}</span></div>
        <div class="pos-row"><span class="pos-key">Take-profit</span><span class="pos-val g">$${fmt(d.position.entry_price*1.010,4)}</span></div>`;
      posDetail.innerHTML = posHTML;
      tabOpenContent.innerHTML = `<div style="padding:8px 0">${posHTML}</div>`;
    } else {
      posEl.textContent='NENHUMA'; posEl.className='metric-val';
      document.getElementById('m-pos-sub').textContent='—';
      posDetail.innerHTML='<div class="pos-none">Nenhuma posição aberta</div>';
      tabOpenContent.innerHTML='<div class="empty">nenhuma posição aberta</div>';
    }

    // Tabelas de operações
    if (trades.length > 0) {
      const rev = [...trades].reverse();
      document.getElementById('ops-tbody-all').innerHTML    = rev.map((t,i) => buildOpsRow(t, trades.length-1-i)).join('') || '<tr><td colspan="9" class="empty">—</td></tr>';
      const winsRev = wins.slice().reverse();
      document.getElementById('ops-tbody-wins').innerHTML   = winsRev.length   ? winsRev.map((t,i)   => buildSimpleRow(t,i)).join('') : '<tr><td colspan="8" class="empty">nenhum ganho ainda</td></tr>';
      const lossRev = losses.slice().reverse();
      document.getElementById('ops-tbody-losses').innerHTML = lossRev.length ? lossRev.map((t,i) => buildSimpleRow(t,i)).join('') : '<tr><td colspan="8" class="empty">nenhuma perda ainda</td></tr>';

      // Resumo
      const totalPnl = trades.reduce((a,t) => a+t.pnl, 0);
      const avgWin   = wins.length   ? wins.reduce((a,t)=>a+t.pnl,0)/wins.length     : 0;
      const avgLoss  = losses.length ? losses.reduce((a,t)=>a+t.pnl,0)/losses.length : 0;
      document.getElementById('ops-summary').innerHTML = `
        <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">Total: <span style="color:${totalPnl>=0?'var(--green)':'var(--red)'};font-weight:700">${totalPnl>=0?'+':''}$${totalPnl.toFixed(4)}</span></div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">Média ganho: <span style="color:var(--green)">+$${avgWin.toFixed(4)}</span></div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">Média perda: <span style="color:var(--red)">$${avgLoss.toFixed(4)}</span></div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">Operações: <span style="color:var(--blue)">${trades.length}</span></div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">Win rate: <span style="color:${wr>=55?'var(--green)':wr<45?'var(--red)':'var(--amber)'}">${wr!==null?wr+'%':'—'}</span></div>`;
    }

    // Desempenho por par
    const pairMap = {};
    trades.forEach(t => {
      const sym = (t.symbol||'BTCUSDT').replace('USDT','');
      if (!pairMap[sym]) pairMap[sym] = { ops:0, wins:0, pnl:0, best:0, worst:0 };
      pairMap[sym].ops++;
      pairMap[sym].pnl += t.pnl;
      if (t.pnl >= 0) pairMap[sym].wins++;
      if (t.pnl > pairMap[sym].best) pairMap[sym].best = t.pnl;
      if (t.pnl < pairMap[sym].worst) pairMap[sym].worst = t.pnl;
    });
    const pairs = ['BTC','ETH','BNB','SOL','XRP'];
    document.getElementById('pair-perf').innerHTML = pairs.map(p => {
      const s = pairMap[p];
      const wr2 = s ? Math.round(s.wins/s.ops*100) : null;
      return `<div class="pair-stat-box">
        <div class="psb-name">${p}/USDT</div>
        ${s ? `
        <div class="psb-row"><span class="psb-key">Ops</span><span class="psb-val">${s.ops}</span></div>
        <div class="psb-row"><span class="psb-key">WR</span><span class="psb-val" style="color:${wr2>=55?'var(--green)':wr2<45?'var(--red)':'var(--amber)'}">${wr2}%</span></div>
        <div class="psb-row"><span class="psb-key">PnL</span><span class="psb-val" style="color:${s.pnl>=0?'var(--green)':'var(--red)'}">${s.pnl>=0?'+':''}$${s.pnl.toFixed(3)}</span></div>
        <div class="psb-row"><span class="psb-key">Melhor</span><span class="psb-val" style="color:var(--green)">+$${s.best.toFixed(3)}</span></div>
        <div class="psb-row"><span class="psb-key">Pior</span><span class="psb-val" style="color:var(--red)">$${s.worst.toFixed(3)}</span></div>
        ` : '<div class="psb-row"><span class="psb-key" style="font-size:9px">sem operações</span></div>'}
      </div>`;
    }).join('');

    // Gráfico
    if (pnlChart && trades.length > 0) {
      let acc = 0;
      const labels=[], vals=[], perOp=[];
      trades.forEach((t,i) => { acc+=t.pnl; labels.push('#'+(i+1)); vals.push(parseFloat(acc.toFixed(4))); perOp.push(parseFloat(t.pnl.toFixed(4))); });
      pnlChart.data.labels = labels;
      pnlChart.data.datasets[0].data = vals;
      pnlChart.data.datasets[1].data = perOp;
      const color = acc>=0?'#00e87a':'#ff3d5a';
      pnlChart.data.datasets[0].borderColor = color;
      pnlChart.data.datasets[0].backgroundColor = acc>=0?'rgba(0,232,122,0.06)':'rgba(255,61,90,0.06)';
      pnlChart.update('none');
    }

    // Scanner
    if (d.scanner && d.scanner.length > 0) {
      const maxScore = Math.max(...d.scanner.map(s=>s.score));
      document.getElementById('scan-ts').textContent = d.scan_time||'';
      document.getElementById('scanner-body').innerHTML = d.scanner.map(s => {
        const isBest = s.score===maxScore, isActive = s.symbol===d.active_symbol;
        const pct = s.change>=0?`<span style="color:var(--green)">+${s.change}%</span>`:`<span style="color:var(--red)">${s.change}%</span>`;
        return `<tr class="${isBest?'best-row':''}">
          <td>${isActive?'★ ':''}${s.symbol.replace('USDT','')}</td>
          <td>${s.score.toFixed(1)}<div class="score-bar"><div class="score-fill ${isBest?'best':''}" style="width:${s.score}%"></div></div></td>
          <td>${pct}</td><td>${s.volume}M</td><td>${s.volatility}%</td></tr>`;
      }).join('');
    }

    // Log
    if (d.logs && d.logs.length > 0) {
      document.getElementById('log-count').textContent = d.logs.length+' linhas';
      document.getElementById('log-inner').innerHTML = d.logs.slice(-80).reverse().map(l => {
        let cls='log-line';
        if (l.includes('Comprado')||l.includes('📈')) cls+=' buy';
        else if (l.includes('Fechado')||l.includes('🔴')||l.includes('✅')||l.includes('❌')) cls+=' sell';
        else if (l.includes('Scanner')||l.includes('★')||l.includes('Par alter')) cls+=' scan';
        else if (l.includes('IA →')||l.includes('🤖')) cls+=' ia';
        else if (l.includes('WARNING')||l.includes('⚠️')||l.includes('FB')) cls+=' warn';
        else if (l.includes('ERROR')||l.includes('Erro')) cls+=' err';
        return `<div class="${cls}">${l}</div>`;
      }).join('');
    }

  } catch(e) {
    document.getElementById('status-chip').textContent='ERRO CONEXÃO';
    document.getElementById('status-chip').className='status-chip off';
  }
}

initChart();
refresh();
setInterval(refresh, 5000);

async function refreshTicker() {
  const pairs = ['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT'];
  for (const sym of pairs) {
    try {
      const r = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${sym}`);
      const d = await r.json();
      const el = document.getElementById('tick-'+sym);
      if (!el) continue;
      const price = parseFloat(d.lastPrice);
      const chg   = parseFloat(d.priceChangePercent);
      const fmtP  = price>1000?'$'+price.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}):price>10?'$'+price.toFixed(2):'$'+price.toFixed(4);
      el.querySelector('.ticker-price').textContent = fmtP;
      const chgEl = el.querySelector('.ticker-change');
      chgEl.textContent = (chg>=0?'+':'')+chg.toFixed(2)+'%';
      chgEl.className = 'ticker-change '+(chg>=0?'pos':'neg');
    } catch(e) {}
  }
  document.querySelectorAll('.ticker-item').forEach(el => el.classList.remove('active-ticker'));
  try {
    const d = await fetch('/api/status').then(r=>r.json());
    if (d.active_symbol) { const el = document.getElementById('tick-'+d.active_symbol); if(el) el.classList.add('active-ticker'); }
  } catch(e) {}
}
refreshTicker();
setInterval(refreshTicker, 10000);
</script>
</body>
</html>'''


WATCH_PAIRS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]

def parse_log():
    result = {
        "bot_running":False,"active_symbol":None,"watch_pairs":WATCH_PAIRS,
        "price":None,"rsi":None,"macd_signal":None,"bb_pct":None,
        "usdt":None,"btc":None,"pnl":0.0,"wins":0,"losses":0,
        "total_trades":0,"position":None,"trades":[],"scanner":[],
        "scanner_scores":{},"scan_time":None,"logs":[],
    }
    if not os.path.exists(LOG_FILE):
        return result
    try:
        with open(LOG_FILE,"r",encoding="utf-8") as f:
            lines = f.readlines()
    except:
        return result

    result["logs"] = [l.rstrip() for l in lines[-100:]]

    if lines:
        try:
            last_dt = datetime.strptime(lines[-1][:19],"%Y-%m-%d %H:%M:%S")
            result["bot_running"] = (datetime.now()-last_dt).total_seconds() < 180
        except:
            pass

    re_price  = re.compile(r'\[(\w+)\] \$([\d,.]+) \| RSI:([\d.]+) \| Tend:(\w+) \| MACD:(\w+) \| BB:([-\d.]+)% \| USDT:([\d.]+)')
    re_wl     = re.compile(r'W:(\d+) L:(\d+)')
    re_pnl    = re.compile(r'Total: \$([-+]?[\d.]+)')
    re_close  = re.compile(r'Fechado (\w+) \(([^)]+)\).*PnL: \$([-+]?[\d.]+)')
    re_open   = re.compile(r'Comprado ([\d.]+) (\w+) @ \$([\d,.]+) \(\$([\d,.]+) USDT\)')
    re_scan   = re.compile(r'[★ ] (\w+)\s+\| Score:\s*([\d.]+) \| Vol:\s*([\d.]+)M \| Var:([-+\d.]+)% \| Volat:([\d.]+)%')
    re_best   = re.compile(r'Melhor par selecionado: (\w+)')
    re_scan_t = re.compile(r'── Scanner')

    current_entry = None
    current_sym   = None
    current_qty   = None
    current_usdt  = None
    scanner_tmp   = []
    scan_active   = False

    for line in lines:
        m = re_price.search(line)
        if m:
            result["active_symbol"] = m.group(1)
            result["price"]         = float(m.group(2).replace(",",""))
            result["rsi"]           = float(m.group(3))
            result["macd_signal"]   = m.group(5)
            result["bb_pct"]        = float(m.group(6))
            result["usdt"]          = float(m.group(7))

        m = re_wl.search(line)
        if m:
            result["wins"]   = int(m.group(1))
            result["losses"] = int(m.group(2))

        m = re_pnl.search(line)
        if m:
            result["pnl"] = float(m.group(1))

        if re_scan_t.search(line):
            scan_active = True; scanner_tmp = []; result["scan_time"] = line[:19]

        if scan_active:
            m = re_scan.search(line)
            if m:
                sym = m.group(1); score = float(m.group(2))
                scanner_tmp.append({"symbol":sym,"score":score,"volume":m.group(3),"change":float(m.group(4)),"volatility":m.group(5)})
                result["scanner_scores"][sym] = score

        m = re_best.search(line)
        if m:
            result["active_symbol"] = m.group(1)
            if scanner_tmp: result["scanner"] = sorted(scanner_tmp,key=lambda x:x["score"],reverse=True)
            scan_active = False

        m = re_open.search(line)
        if m:
            current_qty   = m.group(1)
            current_sym   = m.group(2)
            current_entry = float(m.group(3).replace(",",""))
            current_usdt  = float(m.group(4).replace(",",""))

        m = re_close.search(line)
        if m:
            pnl = float(m.group(3))
            result["trades"].append({
                "symbol":  m.group(1),
                "side":    "BUY",
                "entry":   current_entry or 0,
                "exit":    0,
                "pnl":     pnl,
                "qty":     current_qty or "—",
                "usdt_used": current_usdt or 0,
                "close":   line[:19],
                "reason":  m.group(2),
            })
            current_entry = None; current_sym = None; current_qty = None; current_usdt = None

    result["total_trades"] = len(result["trades"])

    if current_entry and current_sym:
        result["position"] = {
            "symbol": current_sym,"side":"BUY",
            "entry_price": current_entry,
            "qty": current_qty or "—",
            "usdt_used": current_usdt or 0,
        }

    if result["trades"] and result["pnl"] == 0.0:
        result["pnl"]    = round(sum(t["pnl"] for t in result["trades"]),4)
        result["wins"]   = sum(1 for t in result["trades"] if t["pnl"]>=0)
        result["losses"] = sum(1 for t in result["trades"] if t["pnl"]<0)

    return result


@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/status")
def status():
    return jsonify(parse_log())

if __name__ == "__main__":
    print("="*50)
    print(" ScalpBot Dashboard — Multi-Par")
    print(" Acesse: http://localhost:5000")
    print("="*50)
    app.run(host="0.0.0.0", port=5000, debug=False)
