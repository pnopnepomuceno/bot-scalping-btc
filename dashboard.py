"""
ScalpBot Dashboard Unificado v3.1 — porta 5000
Interface limpa com tooltips explicativos em cada métrica.
Relatório diário às 22h + comandos via Telegram.
"""
from flask import Flask, jsonify, render_template_string, request
import os, re, glob, json, threading, time
from datetime import datetime, date
from dotenv import load_dotenv, set_key

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ENV  = os.path.join(BASE, '.env')
load_dotenv(dotenv_path=ENV)

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScalpBot</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0f1a;--panel:#111827;--card:#1a2234;--border:#1e2d45;
  --text:#e8edf5;--muted:#5a7299;--dim:#384d6b;
  --green:#22c55e;--red:#ef4444;--amber:#f59e0b;--blue:#3b82f6;
  --green-bg:rgba(34,197,94,.08);--red-bg:rgba(239,68,68,.08);
  --amber-bg:rgba(245,158,11,.08);--blue-bg:rgba(59,130,246,.08);
  --font:'IBM Plex Sans',sans-serif;--mono:'IBM Plex Mono',monospace;
}
body{background:var(--bg);color:var(--text);font-family:var(--font);font-size:13px;min-height:100vh}

/* Tooltip system */
[data-tip]{position:relative;cursor:help}
[data-tip]::after{
  content:attr(data-tip);
  position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);
  background:#0d1829;border:1px solid var(--border);color:#b0c0d8;
  font-size:11px;font-family:var(--font);font-weight:400;
  padding:6px 10px;border-radius:6px;white-space:nowrap;max-width:220px;
  white-space:normal;text-align:left;line-height:1.5;z-index:1000;
  opacity:0;pointer-events:none;transition:opacity .15s;
  box-shadow:0 4px 16px rgba(0,0,0,.4);
}
[data-tip]:hover::after{opacity:1}

/* Header */
.hdr{
  display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;height:48px;
  background:var(--panel);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;
}
.brand{font-family:var(--mono);font-size:14px;font-weight:600;color:var(--blue);letter-spacing:.1em}
.hdr-r{display:flex;align-items:center;gap:16px}
.status-dot{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--dim)}
.dot.on{background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
.clk{font-family:var(--mono);font-size:11px;color:var(--dim);background:#0d1829;
  padding:3px 8px;border-radius:4px;border:1px solid var(--border)}

/* Ticker */
.ticker{display:flex;overflow-x:auto;scrollbar-width:none;background:var(--panel);border-bottom:1px solid var(--border)}
.ticker::-webkit-scrollbar{display:none}
.ti{display:flex;align-items:center;gap:12px;padding:8px 16px;border-right:1px solid var(--border);
  min-width:130px;flex-shrink:0;cursor:default}
.ti-sym{font-family:var(--mono);font-size:11px;color:var(--muted);font-weight:600;letter-spacing:.08em}
.ti-price{font-family:var(--mono);font-size:13px;font-weight:600}
.ti-chg{font-family:var(--mono);font-size:11px}
.up{color:var(--green)}.dn{color:var(--red)}

/* Nav */
.nav{display:flex;background:var(--panel);border-bottom:1px solid var(--border);overflow-x:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.ntab{padding:10px 18px;border:none;background:none;color:var(--muted);font-size:12px;font-weight:500;
  cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;white-space:nowrap;
  font-family:var(--font);display:flex;align-items:center;gap:7px}
.ntab:hover{color:var(--text)}
.ntab.on{color:var(--blue);border-bottom-color:var(--blue)}
.nb{width:6px;height:6px;border-radius:50%;background:var(--dim);flex-shrink:0}
.nb.on{background:var(--green)}
.xbadge{font-size:9px;font-weight:600;padding:1px 5px;border-radius:3px;font-family:var(--mono)}
.xb-bnb{background:rgba(240,185,11,.15);color:#f0b90b}
.xb-okx{background:rgba(147,51,234,.15);color:#a855f7}

/* Views */
.view{display:none;padding:20px;max-width:1400px;margin:0 auto}
.view.on{display:block}

/* ── VISÃO GERAL ── */
.ov-top{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.metric{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 16px}
.metric-label{font-size:10px;font-weight:600;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin-bottom:8px;display:flex;align-items:center;gap:4px}
.metric-value{font-family:var(--mono);font-size:22px;font-weight:600;line-height:1}
.metric-sub{font-size:11px;color:var(--muted);margin-top:5px;font-family:var(--mono)}
.mv-pos{color:var(--green)}.mv-neg{color:var(--red)}.mv-blue{color:var(--blue)}.mv-amber{color:var(--amber)}
.metric.pos{border-left:3px solid var(--green)}.metric.neg{border-left:3px solid var(--red)}
.metric.blue{border-left:3px solid var(--blue)}.metric.amb{border-left:3px solid var(--amber)}

/* Bot cards na visão geral */
.ov-bots{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px;margin-bottom:20px}
.bc{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.bc-head{padding:12px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.bc-name{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600}
.bc-sub{font-size:11px;color:var(--muted);margin-top:2px;font-family:var(--mono)}
.pill{font-size:9px;font-weight:700;padding:3px 8px;border-radius:12px;font-family:var(--mono);letter-spacing:.04em}
.pill-on{background:var(--green-bg);color:var(--green);border:1px solid rgba(34,197,94,.2)}
.pill-off{background:var(--red-bg);color:var(--red);border:1px solid rgba(239,68,68,.2)}

.bc-metrics{display:grid;grid-template-columns:repeat(4,1fr)}
.bc-m{padding:10px 14px;border-right:1px solid var(--border)}
.bc-m:last-child{border:none}
.bc-ml{font-size:9px;color:var(--muted);font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}
.bc-mv{font-family:var(--mono);font-size:13px;font-weight:600}

/* Posição aberta destaque */
.pos-alert{background:rgba(59,130,246,.06);border-top:1px solid rgba(59,130,246,.15);
  padding:10px 14px;display:flex;align-items:center;justify-content:space-between}
.pos-sym{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--blue)}
.pos-detail{font-size:11px;color:var(--muted);font-family:var(--mono)}

/* Tabela de operações */
.ops-wrap{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.ops-head{padding:12px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.ops-title{font-size:13px;font-weight:600}
.ops-cnt{font-size:11px;color:var(--muted);font-family:var(--mono)}
.filter-row{display:flex;gap:4px}
.fb{font-size:10px;font-weight:600;padding:3px 10px;border-radius:4px;border:1px solid var(--border);
  background:none;color:var(--muted);cursor:pointer;font-family:var(--mono);letter-spacing:.04em;transition:all .1s}
.fb.on{background:var(--blue-bg);border-color:rgba(59,130,246,.3);color:var(--blue)}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;white-space:nowrap}
thead th{padding:9px 14px;text-align:left;font-size:9px;letter-spacing:.1em;color:var(--dim);
  font-weight:600;border-bottom:1px solid var(--border);background:rgba(0,0,0,.2);text-transform:uppercase}
td{padding:9px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:var(--text)}
tr:last-child td{border:none}
tr:hover td{background:rgba(255,255,255,.02)}
.sym-badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;
  background:var(--blue-bg);color:var(--blue);border:1px solid rgba(59,130,246,.12)}
.st-badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:10px;font-size:9px;font-weight:700}
.st-open{background:var(--blue-bg);color:var(--blue)}
.st-win{background:var(--green-bg);color:var(--green)}
.st-loss{background:var(--red-bg);color:var(--red)}
.st-tp{color:var(--green)}.st-sl{color:var(--red)}
.pp{color:var(--green);font-weight:600}.pn{color:var(--red);font-weight:600}
.empty{text-align:center;color:var(--dim);padding:28px;font-size:12px}
.tr-open{background:rgba(59,130,246,.03)}

/* ── BOT INDIVIDUAL ── */
.bot-layout{display:grid;grid-template-columns:1fr 280px;gap:14px}
@media(max-width:900px){.bot-layout{grid-template-columns:1fr}}

.section{font-size:9px;font-weight:600;letter-spacing:.14em;color:var(--dim);text-transform:uppercase;
  display:flex;align-items:center;gap:8px;margin-bottom:10px;margin-top:18px}
.section::after{content:'';flex:1;height:1px;background:var(--border)}

/* Status de posição — destaque principal */
.pos-box{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:14px}
.pos-box-head{padding:10px 14px;background:rgba(59,130,246,.08);border-bottom:1px solid rgba(59,130,246,.15);
  display:flex;align-items:center;justify-content:space-between}
.pos-box-sym{font-family:var(--mono);font-size:18px;font-weight:600;color:var(--blue)}
.pos-box-body{padding:0}
.pos-row{display:flex;justify-content:space-between;align-items:center;padding:9px 14px;border-bottom:1px solid var(--border)}
.pos-row:last-child{border:none}
.pos-key{font-size:11px;color:var(--muted);display:flex;align-items:center;gap:4px}
.pos-val{font-family:var(--mono);font-size:12px;font-weight:600}
.no-pos{background:var(--card);border:1px solid var(--border);border-radius:8px;
  padding:24px;text-align:center;color:var(--dim);font-size:12px;margin-bottom:14px}

/* Indicadores técnicos */
.ind-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}
.ind-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.ind-label{font-size:9px;font-weight:600;letter-spacing:.08em;color:var(--muted);text-transform:uppercase;margin-bottom:4px;display:flex;align-items:center;gap:3px}
.ind-value{font-family:var(--mono);font-size:15px;font-weight:600}

/* Stats row */
.stats-row{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px}
@media(max-width:1100px){.stats-row{grid-template-columns:repeat(3,1fr)}}
.stat{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:11px 14px}
.stat-label{font-size:9px;font-weight:600;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin-bottom:6px;display:flex;align-items:center;gap:4px}
.stat-value{font-family:var(--mono);font-size:18px;font-weight:600}
.sv-pos{color:var(--green)}.sv-neg{color:var(--red)}.sv-blue{color:var(--blue)}

/* Scanner */
.scanner-wrap{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:14px}
.sc-row{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.sc-row:last-child{border:none}
.sc-sym{font-family:var(--mono);font-size:12px;font-weight:600;width:95px}
.sc-best{color:var(--blue)}
.sc-bar-wrap{flex:1;height:3px;background:var(--border);border-radius:2px;overflow:hidden}
.sc-bar{height:100%;border-radius:2px;background:var(--blue);transition:width .5s}
.sc-score{font-family:var(--mono);font-size:10px;color:var(--muted);width:38px;text-align:right}
.sc-chg{font-family:var(--mono);font-size:10px;width:50px;text-align:right}

/* Log */
.log-wrap{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:14px}
.log-head{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.log-body{height:220px;overflow-y:auto;padding:8px;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.log-body::-webkit-scrollbar{width:3px}
.log-body::-webkit-scrollbar-thumb{background:var(--border)}
.ll{display:block;line-height:17px;color:var(--dim);font-size:10px;padding:1px 3px;font-family:var(--mono);word-break:break-all}
.ll.buy{color:#22c55e}.ll.sell{color:#ef4444}.ll.scan{color:#6366f1}
.ll.ia{color:#3b82f6}.ll.warn{color:#f59e0b}.ll.err{color:#ef4444;opacity:.8}

/* Sidebar */
.sidebar{display:flex;flex-direction:column;gap:12px}
.side-card{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.side-head{padding:10px 14px;border-bottom:1px solid var(--border);font-size:10px;font-weight:600;
  letter-spacing:.1em;color:var(--muted);text-transform:uppercase}
.side-body{padding:14px}

/* Notificações */
.notif-grid{display:flex;flex-direction:column;gap:6px}
.ni{display:flex;align-items:center;justify-content:space-between;padding:7px 10px;
  background:rgba(255,255,255,.02);border-radius:6px;gap:8px}
.ni-text{font-size:12px}.ni-desc{font-size:10px;color:var(--muted);margin-top:1px}
.tog{position:relative;display:inline-block;width:36px;height:20px;cursor:pointer;flex-shrink:0}
.tog input{opacity:0;width:0;height:0}
.tog-t{position:absolute;inset:0;background:var(--border);border-radius:10px;transition:.25s}
.tog-k{position:absolute;left:2px;top:2px;width:16px;height:16px;background:var(--muted);border-radius:50%;transition:.25s}
.tog input:checked+.tog-t{background:rgba(59,130,246,.3)}
.tog input:checked~.tog-k{left:18px;background:var(--blue)}
.save-btn{width:100%;margin-top:10px;padding:8px;border-radius:6px;border:1px solid rgba(59,130,246,.3);
  background:rgba(59,130,246,.08);color:var(--blue);font-weight:600;font-size:12px;
  cursor:pointer;font-family:var(--font);transition:all .15s}
.save-btn:hover{background:rgba(59,130,246,.15)}
.sm{font-size:11px;color:var(--green);display:none;text-align:center;margin-top:6px;font-family:var(--mono)}

/* Desempenho por par */
.par-list{display:flex;flex-direction:column;gap:6px}
.par-item{display:flex;justify-content:space-between;align-items:center;
  padding:6px 10px;background:rgba(255,255,255,.02);border-radius:6px}
.par-sym{font-family:var(--mono);font-size:11px;font-weight:600}
.par-pnl{font-family:var(--mono);font-size:11px;font-weight:600}
.par-cnt{font-size:10px;color:var(--muted)}

/* Relatório */
.rep-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:14px}
.rep-title{font-size:15px;font-weight:600;margin-bottom:4px}
.rep-sub{font-size:12px;color:var(--muted);margin-bottom:16px;font-family:var(--mono)}
.rep-btn{padding:8px 16px;border-radius:6px;border:1px solid rgba(59,130,246,.3);
  background:rgba(59,130,246,.08);color:var(--blue);font-weight:600;font-size:12px;
  cursor:pointer;font-family:var(--font);margin-right:8px;transition:all .15s}
.rep-btn:hover{background:rgba(59,130,246,.15)}
.rep-btn.g{border-color:rgba(34,197,94,.3);background:rgba(34,197,94,.06);color:var(--green)}
.rep-preview{margin-top:14px;padding:12px;background:#0d1829;border-radius:6px;
  font-family:var(--mono);font-size:11px;color:var(--muted);white-space:pre-wrap;
  display:none;max-height:260px;overflow-y:auto;border:1px solid var(--border)}
.cmd-list{display:flex;flex-direction:column;gap:6px;margin-top:12px}
.cmd{display:flex;align-items:flex-start;gap:12px;padding:9px 12px;
  background:rgba(255,255,255,.02);border-radius:6px}
.cmd-code{font-family:var(--mono);font-size:11px;color:var(--blue);background:var(--blue-bg);
  padding:2px 8px;border-radius:4px;border:1px solid rgba(59,130,246,.15);white-space:nowrap;flex-shrink:0}
.cmd-desc{font-size:12px;color:var(--muted);padding-top:1px}

/* Help icon */
.hi{font-size:10px;color:var(--dim);cursor:help}
</style>
</head>
<body>

<div class="hdr">
  <div class="brand">SCALP<span style="color:var(--muted);font-weight:400">BOT</span></div>
  <div class="hdr-r">
    <div class="status-dot"><div class="dot" id="live-dot"></div><span id="bot-st">—</span></div>
    <div class="clk" id="clk">--:--:--</div>
  </div>
</div>

<div class="ticker" id="ticker">
  <div class="ti" id="tick-BTCUSDT"><div class="ti-sym">BTC</div><div class="ti-price">—</div><div class="ti-chg">—</div></div>
  <div class="ti" id="tick-ETHUSDT"><div class="ti-sym">ETH</div><div class="ti-price">—</div><div class="ti-chg">—</div></div>
  <div class="ti" id="tick-BNBUSDT"><div class="ti-sym">BNB</div><div class="ti-price">—</div><div class="ti-chg">—</div></div>
  <div class="ti" id="tick-SOLUSDT"><div class="ti-sym">SOL</div><div class="ti-price">—</div><div class="ti-chg">—</div></div>
  <div class="ti" id="tick-XRPUSDT"><div class="ti-sym">XRP</div><div class="ti-price">—</div><div class="ti-chg">—</div></div>
</div>

<div class="nav" id="nav">
  <button class="ntab on" onclick="sv('ov',this)">Visão Geral</button>
</div>

<div id="view-ov" class="view on">
  <div class="ov-top">
    <div class="metric" id="m-pnl">
      <div class="metric-label" data-tip="Lucro ou Prejuízo total somado de todos os bots. Verde = lucro, Vermelho = prejuízo.">PNL TOTAL <span class="hi">?</span></div>
      <div class="metric-value" id="ov-pnl">$0.0000</div>
      <div class="metric-sub" id="ov-ps">todas as contas</div>
    </div>
    <div class="metric blue">
      <div class="metric-label" data-tip="Quantos bots estão ativos e processando dados no momento.">BOTS ATIVOS <span class="hi">?</span></div>
      <div class="metric-value mv-blue" id="ov-bots">—</div>
      <div class="metric-sub" id="ov-bs">—</div>
    </div>
    <div class="metric amb">
      <div class="metric-label" data-tip="Número de posições de compra abertas. Uma posição aberta significa que o bot comprou e ainda não vendeu.">POSIÇÕES ABERTAS <span class="hi">?</span></div>
      <div class="metric-value mv-amber" id="ov-pos">0</div>
      <div class="metric-sub" id="ov-pos-s">—</div>
    </div>
    <div class="metric">
      <div class="metric-label" data-tip="Taxa de acerto: percentual de operações encerradas com lucro. Acima de 55% é considerado bom para scalping.">WIN RATE <span class="hi">?</span></div>
      <div class="metric-value" id="ov-wr" style="color:var(--blue)">—</div>
      <div class="metric-sub" id="ov-wrs">0W / 0L</div>
    </div>
  </div>

  <div class="section">Contas</div>
  <div class="ov-bots" id="ov-accs"></div>

  <div class="section">Operações</div>
  <div class="ops-wrap">
    <div class="ops-head">
      <div>
        <span class="ops-title">Histórico completo</span>
        <span class="ops-cnt" id="ov-cnt" style="margin-left:10px">—</span>
      </div>
      <div class="filter-row">
        <button class="fb on" onclick="ovf('all',this)">TODAS</button>
        <button class="fb" onclick="ovf('open',this)">ABERTAS</button>
        <button class="fb" onclick="ovf('win',this)">GANHOS</button>
        <button class="fb" onclick="ovf('loss',this)">PERDAS</button>
      </div>
    </div>
    <div class="tw"><table>
      <thead><tr>
        <th data-tip="Status atual da operação">STATUS</th>
        <th>CONTA</th>
        <th data-tip="Par de negociação (ex: BTC = Bitcoin contra USDT)">PAR</th>
        <th data-tip="Preço de compra">COMPRA</th>
        <th data-tip="Preço de venda (ou 'aberta' se ainda não vendeu)">VENDA</th>
        <th data-tip="Capital investido em dólares">CAPITAL</th>
        <th data-tip="Lucro ou Prejuízo em dólares desta operação">PNL $</th>
        <th data-tip="Retorno percentual desta operação">PNL %</th>
        <th data-tip="Motivo de encerramento: SL=Stop Loss (limite de perda), TP=Take Profit (meta de lucro), Tec=decisão técnica da IA">MOTIVO</th>
        <th>HORA</th>
      </tr></thead>
      <tbody id="ov-ops"></tbody>
    </table></div>
  </div>
</div>

<div id="panels"></div>

<script>
const NOTIF={
  inicio:{l:'Inicialização',d:'Bot ligou ou desligou'},
  compra:{l:'Compra',d:'Compra executada'},
  venda:{l:'Venda',d:'Venda executada'},
  stop_loss:{l:'Stop Loss',d:'Limite de perda atingido'},
  take_profit:{l:'Take Profit',d:'Meta de lucro atingida'},
  par_troca:{l:'Troca de par',d:'Bot mudou de ativo'},
  ia_erro:{l:'Erro IA',d:'Falha na API Anthropic'},
  resumo:{l:'Resumo diário',d:'Enviado ao encerrar'},
};
let bots=[],allOps=[],ovFilt='all';

function fmt(n,d=2){return(+n||0).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}

function sv(id,btn){
  document.querySelectorAll('.ntab').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('on'));
  btn.classList.add('on');
  const el=document.getElementById('view-'+id);if(el)el.classList.add('on');
}

function sbadge(op){
  if(op._open)return'<span class="st-badge st-open">● ABERTA</span>';
  const r=(op.reason||'').toUpperCase();
  if(r.includes('TAKE_PROFIT'))return'<span class="st-badge st-win st-tp">✓ TAKE PROFIT</span>';
  if(r.includes('STOP_LOSS'))return'<span class="st-badge st-loss st-sl">✗ STOP LOSS</span>';
  return(op.pnl||0)>=0?'<span class="st-badge st-win">✓ GANHO</span>':'<span class="st-badge st-loss">✗ PERDA</span>';
}

function rmotivo(r){
  if(!r)return'—';const u=r.toUpperCase();
  if(u.includes('STOP_LOSS'))return'<span style="color:var(--red);font-size:10px">SL</span>';
  if(u.includes('TAKE_PROFIT'))return'<span style="color:var(--green);font-size:10px">TP</span>';
  if(u.includes('[FB]'))return'<span style="color:var(--muted);font-size:10px">Tec.</span>';
  return`<span style="color:var(--muted);font-size:10px">${r.slice(0,10)}</span>`;
}

function renderOpsTable(tbodyId, ops){
  const tb=document.getElementById(tbodyId);if(!tb)return;
  if(!ops?.length){tb.innerHTML=`<tr><td colspan="10" class="empty">Nenhuma operação ainda — o bot está aguardando sinais de compra</td></tr>`;return;}
  tb.innerHTML=[...ops].reverse().map(op=>{
    const pct=op.usdt_used>0?((op.pnl||0)/op.usdt_used*100).toFixed(2)+'%':'—';
    const pc=(op.pnl||0)>=0?'pp':'pn';
    const sym=(op.symbol||'').replace('USDT','').replace('-USDT','');
    return`<tr class="${op._open?'tr-open':''}">
      <td>${sbadge(op)}</td>
      <td style="color:var(--muted);font-size:11px">${op._bot||b?.name||'—'}</td>
      <td><span class="sym-badge">${sym}</span></td>
      <td>$${fmt(op.entry||0,4)}</td>
      <td>${op._open?'<span style="color:var(--amber)">em aberto</span>':'$'+fmt(op.exit||0,4)}</td>
      <td style="color:var(--muted)">$${fmt(op.usdt_used||0)}</td>
      <td class="${pc}">${op._open?'—':(op.pnl>=0?'+':'')+'$'+Math.abs(op.pnl||0).toFixed(4)}</td>
      <td class="${pc}">${op._open?'—':pct}</td>
      <td>${rmotivo(op.reason)}</td>
      <td style="color:var(--dim);font-size:10px">${(op.close||op.time||'—').slice(11,16)}</td>
    </tr>`;
  }).join('');
}

function ovf(f,btn){
  document.querySelectorAll('#view-ov .fb').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');ovFilt=f;
  const ops=f==='all'?allOps:f==='open'?allOps.filter(o=>o._open):
    f==='win'?allOps.filter(o=>!o._open&&(o.pnl||0)>=0):allOps.filter(o=>!o._open&&(o.pnl||0)<0);
  renderOpsTable('ov-ops',ops);
}

function updOv(data){
  const tp=data.reduce((a,b)=>a+(b.pnl||0),0);
  const at=data.filter(b=>b.bot_running).length;
  const ab=data.filter(b=>b.position).length;
  const w=data.reduce((a,b)=>a+(b.wins||0),0),l=data.reduce((a,b)=>a+(b.losses||0),0);
  const tot=w+l;const wr=tot>0?Math.round(w/tot*100):null;

  const pe=document.getElementById('ov-pnl');
  pe.textContent=(tp>=0?'+':'')+'$'+Math.abs(tp).toFixed(4);
  pe.className='metric-value '+(tp>0?'mv-pos':tp<0?'mv-neg':'');
  const pm=document.getElementById('m-pnl');
  pm.className='metric '+(tp>0?'pos':tp<0?'neg':'');
  document.getElementById('ov-ps').textContent=data.length+' conta(s) combinadas';
  document.getElementById('ov-bots').textContent=at+'/'+data.length;
  document.getElementById('ov-bs').textContent=data.reduce((a,b)=>a+(b.trades||[]).length,0)+' operações realizadas';
  document.getElementById('ov-pos').textContent=ab;
  document.getElementById('ov-pos-s').textContent=ab?ab+' posição(ões) em aberto':'nenhuma posição aberta';
  const we=document.getElementById('ov-wr');
  we.textContent=wr!==null?wr+'%':'—';
  we.style.color=wr!==null&&wr>=55?'var(--green)':wr!==null&&wr<45?'var(--red)':'var(--blue)';
  document.getElementById('ov-wrs').textContent=`${w} ganhos / ${l} perdas`;

  document.getElementById('ov-accs').innerHTML=data.map(b=>{
    const ex=(b.exchange||'binance').toLowerCase();
    const xb=`<span class="xbadge ${ex==='okx'?'xb-okx':'xb-bnb'}">${ex.toUpperCase()}</span>`;
    const pnl=b.pnl||0;const wb=b.wins||0;const lb=b.losses||0;const tb2=wb+lb;
    const wr2=tb2>0?Math.round(wb/tb2*100):null;
    const posH=b.position?`<div class="pos-alert">
      <span class="pos-sym">${(b.position.symbol||'').replace('USDT','').replace('-USDT','')}/USDT</span>
      <span class="pos-detail">entrada $${fmt(b.position.entry_price||0,2)} · capital $${fmt(b.position.usdt_used||0)}</span>
    </div>`:'';
    return`<div class="bc">
      <div class="bc-head">
        <div>
          <div class="bc-name">${b.emoji||'🤖'} ${b.name} ${xb}</div>
          <div class="bc-sub">${b.active_symbol||'aguardando scanner...'}</div>
        </div>
        <span class="pill ${b.bot_running?'pill-on':'pill-off'}">${b.bot_running?'● ATIVO':'○ PARADO'}</span>
      </div>
      <div class="bc-metrics">
        <div class="bc-m" data-tip="Saldo de USDT disponível para novas compras nesta conta">
          <div class="bc-ml">USDT livre</div>
          <div class="bc-mv" style="color:${(b.usdt||0)<10?'var(--red)':'var(--text)'}">$${fmt(b.usdt||0)}</div>
        </div>
        <div class="bc-m" data-tip="Lucro ou Prejuízo total desta conta">
          <div class="bc-ml">PnL</div>
          <div class="bc-mv" style="color:${pnl>0?'var(--green)':pnl<0?'var(--red)':'var(--text)'}">${pnl>=0?'+':''}$${pnl.toFixed(3)}</div>
        </div>
        <div class="bc-m" data-tip="Win Rate: percentual de operações com lucro. Acima de 55% é bom.">
          <div class="bc-ml">Win rate</div>
          <div class="bc-mv" style="color:${wr2!==null&&wr2>=55?'var(--green)':wr2!==null&&wr2<45?'var(--red)':'var(--text)'}">${wr2!==null?wr2+'%':'—'}</div>
        </div>
        <div class="bc-m" data-tip="Total de operações já encerradas (compra + venda)">
          <div class="bc-ml">Operações</div>
          <div class="bc-mv">${tb2}</div>
        </div>
      </div>
      ${posH}
    </div>`;
  }).join('');

  allOps=[];
  data.forEach(b=>{
    (b.trades||[]).forEach(t=>allOps.push({...t,_bot:b.name,_open:false}));
    if(b.position)allOps.push({
      symbol:b.position.symbol,entry:b.position.entry_price,
      qty:b.position.qty,usdt_used:b.position.usdt_used||0,pnl:0,
      _bot:b.name,_open:true,time:'',reason:''
    });
  });
  allOps.sort((a,b)=>(a.close||a.time||'')>(b.close||b.time||'')?1:-1);
  document.getElementById('ov-cnt').textContent=allOps.length+' operações';
  const ab2=document.querySelector('#view-ov .fb.on');if(ab2)ab2.click();else renderOpsTable('ov-ops',allOps);
}

function buildBotView(b,idx){
  const notifHtml=Object.entries(NOTIF).map(([k,info])=>`
    <div class="ni">
      <div><div class="ni-text">${info.l}</div><div class="ni-desc">${info.d}</div></div>
      <label class="tog"><input type="checkbox" id="nf-${idx}-${k}" onchange="sn(${idx})">
        <div class="tog-t"></div><div class="tog-k"></div></label>
    </div>`).join('');

  return`<div id="view-bot${idx}" class="view" style="padding:20px">
    <div class="bot-layout">
      <div>
        <!-- Posição atual — informação mais importante -->
        <div class="section">Posição Atual</div>
        <div id="pos-box-${idx}"></div>

        <!-- Indicadores técnicos -->
        <div class="section">Indicadores Técnicos</div>
        <div class="ind-grid" id="ind-${idx}">
          <div class="ind-card"><div class="ind-label" data-tip="RSI (Índice de Força Relativa): mede se o ativo está sobrecomprado ou sobrevendido. Abaixo de 30 = muito barato (possível compra), Acima de 70 = muito caro (possível venda).">RSI <span class="hi">?</span></div><div class="ind-value" id="iv-rsi-${idx}">—</div></div>
          <div class="ind-card"><div class="ind-label" data-tip="MACD: indica a direção da tendência. BULL = tendência de alta (favorável para compra), BEAR = tendência de baixa (favorável para venda).">MACD <span class="hi">?</span></div><div class="ind-value" id="iv-macd-${idx}">—</div></div>
          <div class="ind-card"><div class="ind-label" data-tip="BB% (Bandas de Bollinger): posição do preço dentro das bandas. 0% = extremo inferior (possível compra), 100% = extremo superior (possível venda). Valores além de 100% indicam movimento muito forte.">BB% <span class="hi">?</span></div><div class="ind-value" id="iv-bb-${idx}">—</div></div>
          <div class="ind-card"><div class="ind-label" data-tip="Tendência de preço calculada pela média móvel de 50 períodos. ALTA = preço acima da média (momentum positivo), BAIXA = preço abaixo (momentum negativo).">TEND <span class="hi">?</span></div><div class="ind-value" id="iv-tend-${idx}">—</div></div>
        </div>

        <!-- Estatísticas -->
        <div class="section">Estatísticas</div>
        <div class="stats-row">
          <div class="stat"><div class="stat-label" data-tip="Lucro/Prejuízo acumulado de todas as operações encerradas desta conta.">PNL TOTAL <span class="hi">?</span></div><div class="stat-value" id="sv-pnl-${idx}">—</div></div>
          <div class="stat"><div class="stat-label" data-tip="Saldo de USDT disponível para novas compras. Abaixo de $10 o bot não consegue operar.">USDT LIVRE <span class="hi">?</span></div><div class="stat-value sv-blue" id="sv-usdt-${idx}">—</div></div>
          <div class="stat"><div class="stat-label" data-tip="Win Rate: percentual de operações com lucro. Ex: 60% significa que 6 em cada 10 operações deram lucro.">WIN RATE <span class="hi">?</span></div><div class="stat-value" id="sv-wr-${idx}">—</div></div>
          <div class="stat"><div class="stat-label" data-tip="Total de operações já encerradas com lucro (wins) e prejuízo (losses).">W / L <span class="hi">?</span></div><div class="stat-value" id="sv-wl-${idx}">—</div></div>
          <div class="stat"><div class="stat-label" data-tip="Melhor operação já realizada nesta conta.">MELHOR OP <span class="hi">?</span></div><div class="stat-value sv-pos" id="sv-best-${idx}">—</div></div>
          <div class="stat"><div class="stat-label" data-tip="Pior operação já realizada nesta conta.">PIOR OP <span class="hi">?</span></div><div class="stat-value sv-neg" id="sv-worst-${idx}">—</div></div>
        </div>

        <!-- Operações -->
        <div class="section">Operações</div>
        <div class="ops-wrap" style="margin-bottom:14px">
          <div class="ops-head">
            <div><span class="ops-title">Histórico</span><span class="ops-cnt" id="ops-cnt-${idx}" style="margin-left:10px">—</span></div>
            <div class="filter-row">
              <button class="fb on" onclick="bfilt(${idx},'all',this)">TODAS</button>
              <button class="fb" onclick="bfilt(${idx},'win',this)">GANHOS</button>
              <button class="fb" onclick="bfilt(${idx},'loss',this)">PERDAS</button>
            </div>
          </div>
          <div class="tw"><table>
            <thead><tr>
              <th>#</th><th data-tip="Par de negociação">PAR</th>
              <th data-tip="Preço de compra">COMPRA</th>
              <th data-tip="Preço de venda">VENDA</th>
              <th data-tip="Quantidade comprada">QTD</th>
              <th data-tip="Capital investido em USDT">CAPITAL</th>
              <th data-tip="Lucro ou Prejuízo em dólares">PNL $</th>
              <th data-tip="Retorno percentual">PNL %</th>
              <th data-tip="SL=Stop Loss (saiu por limite de perda), TP=Take Profit (saiu por meta de lucro), Tec=decisão técnica">MOTIVO</th>
              <th>DATA/HORA</th>
            </tr></thead>
            <tbody id="bops-${idx}"></tbody>
          </table></div>
        </div>

        <!-- Scanner -->
        <div class="section">Scanner de Mercado</div>
        <div class="scanner-wrap">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <span style="font-size:10px;font-weight:600;letter-spacing:.1em;color:var(--muted)" data-tip="O scanner analisa todos os pares configurados e escolhe o melhor para operar, baseado em volume, volatilidade e variação de preço. Maior score = melhor oportunidade.">PARES MONITORADOS <span class="hi">?</span></span>
            <span style="font-size:10px;color:var(--dim);font-family:var(--mono)" id="sc-ts-${idx}">—</span>
          </div>
          <div id="sc-${idx}"></div>
        </div>

        <!-- Log -->
        <div class="section">Log em Tempo Real</div>
        <div class="log-wrap">
          <div class="log-head">
            <span style="font-size:10px;font-weight:600;letter-spacing:.1em;color:var(--muted)">ATIVIDADE DO BOT</span>
            <span style="font-size:10px;color:var(--dim);font-family:var(--mono)" id="lc-${idx}">0 linhas</span>
          </div>
          <div class="log-body" id="lw-${idx}"></div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="sidebar">
        <!-- Desempenho por par -->
        <div class="side-card">
          <div class="side-head" data-tip="PnL acumulado por cada par de negociação. Mostra quais ativos estão dando mais resultado.">Por par <span class="hi">?</span></div>
          <div class="side-body"><div class="par-list" id="pg-${idx}"><span style="color:var(--dim);font-size:12px">Sem dados ainda</span></div></div>
        </div>

        <!-- Notificações -->
        <div class="side-card">
          <div class="side-head">Notificações Telegram</div>
          <div class="side-body">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--border)">
              <span style="font-size:12px" id="tg-st-${idx}">—</span>
              <label class="tog"><input type="checkbox" id="tg-a-${idx}" onchange="sta(${idx})">
                <div class="tog-t"></div><div class="tog-k"></div></label>
            </div>
            <div class="notif-grid" id="ng-${idx}">${notifHtml}</div>
            <button class="save-btn" onclick="sn(${idx})">Salvar configurações</button>
            <div class="sm" id="sm-${idx}">✓ Salvo!</div>
          </div>
        </div>
      </div>
    </div>
  </div>`;
}

function updBotPos(b,idx){
  const el=document.getElementById('pos-box-'+idx);if(!el)return;
  if(!b.position){
    el.innerHTML='<div class="no-pos">Nenhuma posição aberta — bot aguardando sinal de compra</div>';
    return;
  }
  const p=b.position;const curr=b.price||p.entry_price;
  const pct=p.entry_price>0?((curr-p.entry_price)/p.entry_price*100):0;
  const pnl=(pct/100*(p.usdt_used||0));
  const sl=b.stop_loss||0.005;const tp=b.take_profit||0.010;
  const pColor=pct>=0?'var(--green)':'var(--red)';
  el.innerHTML=`<div class="pos-box">
    <div class="pos-box-head">
      <div>
        <div class="pos-box-sym">${(p.symbol||'').replace('USDT','').replace('-USDT','')}/USDT</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px;font-family:var(--mono)">POSIÇÃO EM ABERTO</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:var(--mono);font-size:20px;font-weight:600;color:${pColor}">${pct>=0?'+':''}${pct.toFixed(2)}%</div>
        <div style="font-family:var(--mono);font-size:13px;font-weight:600;color:${pColor}">${pnl>=0?'+':''}$${Math.abs(pnl).toFixed(4)}</div>
      </div>
    </div>
    <div class="pos-box-body">
      <div class="pos-row">
        <span class="pos-key" data-tip="Preço no qual o bot comprou o ativo">Preço de compra <span class="hi">?</span></span>
        <span class="pos-val">$${fmt(p.entry_price,4)}</span>
      </div>
      <div class="pos-row">
        <span class="pos-key" data-tip="Preço atual do ativo no mercado">Preço atual <span class="hi">?</span></span>
        <span class="pos-val" style="color:${pColor}">$${fmt(curr,4)}</span>
      </div>
      <div class="pos-row">
        <span class="pos-key" data-tip="Quanto foi investido nesta operação em dólares">Capital investido <span class="hi">?</span></span>
        <span class="pos-val">$${fmt(p.usdt_used||0)}</span>
      </div>
      <div class="pos-row">
        <span class="pos-key" data-tip="Quantidade do ativo comprado">Quantidade <span class="hi">?</span></span>
        <span class="pos-val">${p.qty||'—'}</span>
      </div>
      <div class="pos-row" style="background:var(--red-bg)">
        <span class="pos-key" style="color:var(--red)" data-tip="Stop Loss: se o preço cair até este valor, o bot vende automaticamente para limitar a perda. Configurado em ${(sl*100).toFixed(1)}% de queda.">Stop Loss -${(sl*100).toFixed(1)}% <span class="hi">?</span></span>
        <span class="pos-val" style="color:var(--red)">$${fmt(p.entry_price*(1-sl),4)}</span>
      </div>
      <div class="pos-row" style="background:var(--green-bg)">
        <span class="pos-key" style="color:var(--green)" data-tip="Take Profit: se o preço subir até este valor, o bot vende automaticamente para garantir o lucro. Configurado em ${(tp*100).toFixed(1)}% de alta.">Take Profit +${(tp*100).toFixed(1)}% <span class="hi">?</span></span>
        <span class="pos-val" style="color:var(--green)">$${fmt(p.entry_price*(1+tp),4)}</span>
      </div>
    </div>
  </div>`;
}

function updBotPanel(b,idx){
  updBotPos(b,idx);

  // Indicadores
  if(b.rsi!=null){
    const rsiC=b.rsi<35?'var(--green)':b.rsi>65?'var(--red)':'var(--text)';
    const macdC=b.macd_signal==='bullish'?'var(--green)':'var(--red)';
    const bbC=b.bb_pct<25?'var(--green)':b.bb_pct>75?'var(--red)':'var(--text)';
    const tendC=b.trend==='alta'?'var(--green)':'var(--red)';
    const rsi=document.getElementById('iv-rsi-'+idx);if(rsi){rsi.textContent=b.rsi;rsi.style.color=rsiC;}
    const macd=document.getElementById('iv-macd-'+idx);if(macd){macd.textContent=b.macd_signal==='bullish'?'BULL':'BEAR';macd.style.color=macdC;}
    const bb=document.getElementById('iv-bb-'+idx);if(bb){bb.textContent=b.bb_pct+'%';bb.style.color=bbC;}
    const tend=document.getElementById('iv-tend-'+idx);if(tend){tend.textContent=b.trend==='alta'?'↑ ALTA':'↓ BAIXA';tend.style.color=tendC;}
  }

  // Stats
  const pnl=b.pnl||0;const pe=document.getElementById('sv-pnl-'+idx);
  if(pe){pe.textContent=(pnl>=0?'+':'')+'$'+Math.abs(pnl).toFixed(4);pe.className='stat-value '+(pnl>0?'sv-pos':pnl<0?'sv-neg':'');}
  const ue=document.getElementById('sv-usdt-'+idx);
  if(ue){const usdt=b.usdt||0;ue.textContent='$'+fmt(usdt);ue.style.color=usdt<10?'var(--red)':'var(--blue)';}
  const tot=(b.wins||0)+(b.losses||0);const wr=tot>0?Math.round(b.wins/tot*100):null;
  const wre=document.getElementById('sv-wr-'+idx);
  if(wre){wre.textContent=wr!==null?wr+'%':'—';wre.style.color=wr>=55?'var(--green)':wr!==null&&wr<45?'var(--red)':'var(--text)';}
  const wle=document.getElementById('sv-wl-'+idx);if(wle)wle.textContent=`${b.wins||0} / ${b.losses||0}`;
  const best=(b.trades||[]).filter(t=>t.pnl>0).sort((a,b)=>b.pnl-a.pnl)[0];
  const worst=(b.trades||[]).filter(t=>t.pnl<0).sort((a,b)=>a.pnl-b.pnl)[0];
  const be=document.getElementById('sv-best-'+idx);if(be)be.textContent=best?'+$'+best.pnl.toFixed(4):'—';
  const we=document.getElementById('sv-worst-'+idx);if(we)we.textContent=worst?'-$'+Math.abs(worst.pnl).toFixed(4):'—';

  // Operações
  const cnt=document.getElementById('ops-cnt-'+idx);if(cnt)cnt.textContent=(b.trades||[]).length+' operações';
  const bopsActive=document.querySelector(`#view-bot${idx} .fb.on`);
  if(bopsActive)bopsActive.click();else renderBotOps(idx,'all');

  // Scanner
  const sc=document.getElementById('sc-'+idx);
  if(sc&&b.scanner?.length){
    const mx=Math.max(...b.scanner.map(s=>s.score),1);
    sc.innerHTML=b.scanner.map(s=>{
      const best2=s.symbol===b.active_symbol;
      const cc=s.change>=0?'var(--green)':'var(--red)';
      return`<div class="sc-row">
        <div class="sc-sym ${best2?'sc-best':''}">${best2?'★ ':'  '}${s.symbol}</div>
        <div class="sc-bar-wrap"><div class="sc-bar" style="width:${(s.score/mx*100).toFixed(0)}%"></div></div>
        <div class="sc-score">${s.score}</div>
        <div class="sc-chg" style="color:${cc}">${s.change>=0?'+':''}${s.change}%</div>
      </div>`;}).join('');
    const ts=document.getElementById('sc-ts-'+idx);if(ts)ts.textContent=b.scan_time?b.scan_time.slice(11,19):'—';
  }

  // Log
  const lwe=document.getElementById('lw-'+idx);
  if(lwe&&b.logs?.length){
    const lce=document.getElementById('lc-'+idx);if(lce)lce.textContent=b.logs.length+' linhas';
    const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    lwe.innerHTML=b.logs.slice(-100).reverse().map(l=>{
      let c='ll';
      if(l.includes('Comprado'))c+=' buy';
      else if(l.includes('Fechado')||l.includes('PnL:'))c+=' sell';
      else if(l.includes('Scanner')||l.includes('Melhor:'))c+=' scan';
      else if(l.includes('[IA]')||l.includes('[OKX]')||l.includes('[BINANCE]'))c+=' ia';
      else if(l.includes('WARNING')||l.includes('[TOR]'))c+=' warn';
      else if(l.includes('ERROR'))c+=' err';
      return`<div class="${c}">${esc(l)}</div>`;}).join('');
  }

  // Desempenho por par
  const pg=document.getElementById('pg-'+idx);
  if(pg){
    const bp={};(b.trades||[]).forEach(t=>{const p=t.symbol||'?';if(!bp[p])bp[p]={pnl:0,cnt:0};bp[p].pnl+=t.pnl||0;bp[p].cnt++;});
    const ps=Object.entries(bp).sort((a,b)=>b[1].pnl-a[1].pnl);
    pg.innerHTML=ps.length?ps.map(([s,d])=>`<div class="par-item">
      <div>
        <div class="par-sym">${s.replace('USDT','').replace('-USDT','')}</div>
        <div class="par-cnt">${d.cnt} operação${d.cnt!==1?'s':''}</div>
      </div>
      <div class="par-pnl" style="color:${d.pnl>=0?'var(--green)':'var(--red)'}">${d.pnl>=0?'+':''}$${d.pnl.toFixed(4)}</div>
    </div>`).join(''):'<span style="color:var(--dim);font-size:12px">Sem dados ainda</span>';
  }

  // Notif
  const ta=document.getElementById('tg-a-'+idx);if(ta)ta.checked=b.tg_ativo!==false;
  const gr=document.getElementById('ng-'+idx);if(gr)gr.style.opacity=b.tg_ativo!==false?'1':'0.5';
  const ts2=document.getElementById('tg-st-'+idx);
  if(ts2)ts2.textContent=`${(b.exchange||'binance').toUpperCase()} | ${b.tg_token?(b.tg_ativo!==false?'Telegram ativo':'Pausado'):'Sem token Telegram'}`;
  if(b.notif_cfg)Object.keys(NOTIF).forEach(k=>{const el=document.getElementById(`nf-${idx}-${k}`);if(el)el.checked=b.notif_cfg[k]!==false;});
}

function renderBotOps(idx,f){
  const tr=(bots[idx]?.trades||[]);
  const filtered=f==='all'?tr:tr.filter(t=>f==='win'?t.pnl>=0:t.pnl<0);
  const tb=document.getElementById('bops-'+idx);if(!tb)return;
  const name=bots[idx]?.name||'—';
  if(!filtered.length){tb.innerHTML=`<tr><td colspan="10" class="empty">Nenhuma operação ainda</td></tr>`;return;}
  tb.innerHTML=[...filtered].reverse().map((t,i)=>{
    const pct=t.usdt_used>0?(t.pnl/t.usdt_used*100).toFixed(2)+'%':'—';
    const c=t.pnl>=0?'pp':'pn';
    return`<tr>
      <td style="color:var(--dim)">${filtered.length-i}</td>
      <td><span class="sym-badge">${(t.symbol||'').replace('USDT','').replace('-USDT','')}</span></td>
      <td>$${fmt(t.entry||0,4)}</td>
      <td>${t.exit>0?'$'+fmt(t.exit,4):'<span style="color:var(--amber)">em aberto</span>'}</td>
      <td style="color:var(--muted)">${t.qty||'—'}</td>
      <td style="color:var(--muted)">$${fmt(t.usdt_used||0)}</td>
      <td class="${c}">${t.pnl>=0?'+':''}$${(t.pnl||0).toFixed(4)}</td>
      <td class="${c}">${pct}</td>
      <td>${rmotivo(t.reason)}</td>
      <td style="color:var(--dim);font-size:10px">${(t.close||'—').slice(0,16)}</td>
    </tr>`;
  }).join('');
}

function bfilt(idx,f,btn){
  document.querySelectorAll(`#view-bot${idx} .fb`).forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');renderBotOps(idx,f);
}

async function sta(idx){
  const a=document.getElementById('tg-a-'+idx)?.checked;
  await fetch('/api/tg_ativo/'+idx,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ativo:a})});
  const g=document.getElementById('ng-'+idx);if(g)g.style.opacity=a?'1':'0.5';
}
async function sn(idx){
  const cfg={};Object.keys(NOTIF).forEach(k=>{const el=document.getElementById(`nf-${idx}-${k}`);if(el)cfg[k]=el.checked;});
  await fetch('/api/notif/'+idx,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
  const m=document.getElementById('sm-'+idx);if(m){m.style.display='block';setTimeout(()=>m.style.display='none',2e3);}
}

async function sendReport(){
  const btn=document.getElementById('btn-rep');btn.textContent='Enviando...';btn.disabled=true;
  try{
    const r=await fetch('/api/report/send',{method:'POST'});const d=await r.json();
    const el=document.getElementById('rr');el.style.display='block';el.textContent=d.msg;
    btn.textContent='✓ Enviado!';
  }catch(e){btn.textContent='Erro';}
  setTimeout(()=>{btn.textContent='Enviar agora';btn.disabled=false;},3e3);
}

async function showReport(){
  const r=await fetch('/api/report/preview');const d=await r.json();
  const el=document.getElementById('rr');el.style.display='block';el.textContent=d.text||'Erro';
}

async function refresh(){
  try{
    const data=await fetch('/api/bots').then(r=>r.json());
    const nav=document.getElementById('nav');
    const panels=document.getElementById('panels');

    if(nav.children.length<=1){
      data.forEach((b,i)=>{
        const ex=(b.exchange||'binance').toLowerCase();
        const xb=`<span class="xbadge ${ex==='okx'?'xb-okx':'xb-bnb'}">${ex.toUpperCase()}</span>`;
        const btn=document.createElement('button');
        btn.className='ntab';btn.id='nb-'+i;
        btn.onclick=()=>sv('bot'+i,btn);
        btn.innerHTML=`<div class="nb ${b.bot_running?'on':''}"></div>${b.emoji||'🤖'} ${b.name} ${xb}`;
        nav.appendChild(btn);
        const div=document.createElement('div');div.innerHTML=buildBotView(b,i);
        panels.appendChild(div.firstChild||div);
      });

      // Aba relatório
      const rbtn=document.createElement('button');rbtn.className='ntab';
      rbtn.onclick=()=>sv('relatorio',rbtn);rbtn.textContent='📊 Relatório';nav.appendChild(rbtn);
      const rdiv=document.createElement('div');
      rdiv.innerHTML=`<div id="view-relatorio" class="view" style="padding:20px;max-width:700px">
        <div class="rep-card">
          <div class="rep-title">Relatório Diário</div>
          <div class="rep-sub">Enviado automaticamente às 22h00 pelo Telegram</div>
          <button class="rep-btn g" id="btn-rep" onclick="sendReport()">Enviar agora</button>
          <button class="rep-btn" onclick="showReport()">Pré-visualizar</button>
          <div class="rep-preview" id="rr"></div>
        </div>
        <div class="rep-card">
          <div class="rep-title">Comandos no Telegram</div>
          <div class="rep-sub">Envie esses comandos no chat para controlar os bots remotamente</div>
          <div class="cmd-list">
            <div class="cmd"><span class="cmd-code">/status</span><span class="cmd-desc">Status completo de todos os bots agora</span></div>
            <div class="cmd"><span class="cmd-code">/relatorio</span><span class="cmd-desc">Relatório do dia com PnL, operações e win rate</span></div>
            <div class="cmd"><span class="cmd-code">/saldo</span><span class="cmd-desc">Saldo de USDT disponível em cada conta</span></div>
            <div class="cmd"><span class="cmd-code">/ops</span><span class="cmd-desc">Últimas 5 operações realizadas</span></div>
            <div class="cmd"><span class="cmd-code">/scanner</span><span class="cmd-desc">Quais ativos estão sendo monitorados agora</span></div>
            <div class="cmd"><span class="cmd-code">/pausar N</span><span class="cmd-desc">Para notificações do Bot N (ex: /pausar 1)</span></div>
            <div class="cmd"><span class="cmd-code">/ativar N</span><span class="cmd-desc">Retoma notificações do Bot N (ex: /ativar 1)</span></div>
          </div>
        </div>
      </div>`;
      panels.appendChild(rdiv.firstChild||rdiv);
    }

    data.forEach((b,i)=>{
      const btn2=document.getElementById('nb-'+i);
      if(btn2){
        const ex=(b.exchange||'binance').toLowerCase();
        const xb=`<span class="xbadge ${ex==='okx'?'xb-okx':'xb-bnb'}">${ex.toUpperCase()}</span>`;
        btn2.innerHTML=`<div class="nb ${b.bot_running?'on':''}"></div>${b.emoji||'🤖'} ${b.name} ${xb}`;
      }
      bots[i]=b;updBotPanel(b,i);
    });
    updOv(data);

    const ao=data.some(b=>b.bot_running);
    const ld=document.getElementById('live-dot');if(ld)ld.className='dot '+(ao?'on':'');
    const st=document.getElementById('bot-st');
    if(st)st.textContent=ao?data.filter(b=>b.bot_running).length+' bot(s) ativo(s)':'nenhum bot ativo';
  }catch(e){
    const st=document.getElementById('bot-st');if(st)st.textContent='erro de conexão';
  }
}

async function refreshTicker(){
  for(const sym of ['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT']){
    try{
      const d=await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol='+sym).then(r=>r.json());
      const el=document.getElementById('tick-'+sym);if(!el)continue;
      const p=parseFloat(d.lastPrice),c=parseFloat(d.priceChangePercent);
      const fp=p>1000?'$'+p.toLocaleString('pt-BR',{minimumFractionDigits:2}):p>10?'$'+p.toFixed(2):'$'+p.toFixed(4);
      el.querySelector('.ti-price').textContent=fp;
      const ce=el.querySelector('.ti-chg');ce.textContent=(c>=0?'+':'')+c.toFixed(2)+'%';ce.className='ti-chg '+(c>=0?'up':'dn');
    }catch(e){}
  }
}

setInterval(()=>{const e=document.getElementById('clk');if(e)e.textContent=new Date().toLocaleTimeString('pt-BR');},1e3);
refresh();refreshTicker();setInterval(refresh,5e3);setInterval(refreshTicker,1e4);
</script>
</body>
</html>"""


def parse_bot_log(log_file: str, bot_name: str, bot_idx: int = 0) -> dict:
    result = {
        "name":bot_name,"emoji":"🤖","bot_running":False,
        "exchange":os.getenv(f"BOT_{bot_idx+1}_EXCHANGE","binance").lower(),
        "testnet":os.getenv(f"BOT_{bot_idx+1}_TESTNET","false").lower()=="true",
        "tg_token":bool(os.getenv(f"BOT_{bot_idx+1}_TELEGRAM_TOKEN","")),
        "tg_ativo":os.getenv(f"BOT_{bot_idx+1}_TELEGRAM_ATIVO","true").lower()=="true",
        "stop_loss":float(os.getenv(f"BOT_{bot_idx+1}_STOP_LOSS","0.005")),
        "take_profit":float(os.getenv(f"BOT_{bot_idx+1}_TAKE_PROFIT","0.010")),
        "active_symbol":None,"price":None,"rsi":None,"trend":None,
        "macd_signal":None,"bb_pct":None,"usdt":None,
        "pnl":0.0,"wins":0,"losses":0,
        "position":None,"trades":[],"scanner":[],"scanner_scores":{},"scan_time":None,"logs":[],
        "notif_cfg":{k:True for k in ["inicio","compra","venda","stop_loss","take_profit","par_troca","ia_erro","resumo"]},
    }
    prefix = f"BOT_{bot_idx+1}"
    result["emoji"] = os.getenv(f"{prefix}_EMOJI","🤖")
    for key in result["notif_cfg"]:
        val = os.getenv(f"{prefix}_NOTIFY_{key.upper()}")
        if val is not None: result["notif_cfg"][key] = val.lower()=="true"

    if not os.path.exists(log_file): return result
    try: lines = open(log_file,encoding='utf-8').readlines()
    except: return result

    result["logs"] = [l.rstrip() for l in lines[-100:]]
    if lines:
        try:
            last_dt = datetime.strptime(lines[-1][:19],"%Y-%m-%d %H:%M:%S")
            result["bot_running"] = (datetime.now()-last_dt).total_seconds()<300
        except: pass

    re_price  = re.compile(r'\[([\w-]+)\] \$([\d,.]+) \| RSI:([\d.]+) \| Tend:(\w+) \| MACD:(\w+) \| BB:([-\d.]+)% \| USDT:([\d.]+)')
    re_wl     = re.compile(r'W:(\d+) L:(\d+)')
    re_pnl    = re.compile(r'Total: \$([-+]?[\d.]+)')
    re_close  = re.compile(r'Fechado ([\w-]+) \(([^)]+)\).*PnL: \$([-+]?[\d.]+)')
    re_open   = re.compile(r'Comprado ([\d.]+) ([\w-]+) @ \$([\d,.]+) \(\$([\d,.]+)\)')
    re_scan   = re.compile(r'[★ ] ([\w-]+)\s+\| Score:\s*([\d.]+) \| Vol:\s*([\d.]+)M \| Var:([-+\d.]+)% \| Volat:([\d.]+)%')
    re_best   = re.compile(r'Melhor: ([\w-]+)')
    re_scan_t = re.compile(r'── Scanner')

    ce=cs=cq=cu=None; scanner_tmp=[]; scan_active=False

    for line in lines:
        m = re_price.search(line)
        if m:
            result["active_symbol"]=m.group(1); result["price"]=float(m.group(2).replace(",",""))
            result["rsi"]=float(m.group(3)); result["trend"]=m.group(4)
            result["macd_signal"]=m.group(5); result["bb_pct"]=float(m.group(6)); result["usdt"]=float(m.group(7))
        m = re_wl.search(line)
        if m: result["wins"]=int(m.group(1)); result["losses"]=int(m.group(2))
        m = re_pnl.search(line)
        if m: result["pnl"]=float(m.group(1))
        if re_scan_t.search(line): scan_active=True; scanner_tmp=[]; result["scan_time"]=line[:19]
        if scan_active:
            m = re_scan.search(line)
            if m:
                scanner_tmp.append({"symbol":m.group(1),"score":float(m.group(2)),"volume":m.group(3),
                    "change":float(m.group(4)),"volatility":m.group(5),"in_wallet":False})
                result["scanner_scores"][m.group(1)]=float(m.group(2))
        m = re_best.search(line)
        if m:
            result["active_symbol"]=m.group(1)
            if scanner_tmp: result["scanner"]=sorted(scanner_tmp,key=lambda x:x["score"],reverse=True)
            scan_active=False
        m = re_open.search(line)
        if m: cq=m.group(1); cs=m.group(2); ce=float(m.group(3).replace(",","")); cu=float(m.group(4).replace(",",""))
        m = re_close.search(line)
        if m:
            result["trades"].append({"symbol":m.group(1),"entry":ce or 0,"exit":0,
                "pnl":float(m.group(3)),"qty":cq or "—","usdt_used":cu or 0,"close":line[:19],"reason":m.group(2)})
            ce=cs=cq=cu=None

    result["total_trades"] = len(result["trades"])
    if ce and cs: result["position"] = {"symbol":cs,"entry_price":ce,"qty":cq or "—","usdt_used":cu or 0}
    if result["trades"] and result["pnl"]==0.0:
        result["pnl"]=round(sum(t["pnl"] for t in result["trades"]),4)
        result["wins"]=sum(1 for t in result["trades"] if t["pnl"]>=0)
        result["losses"]=sum(1 for t in result["trades"] if t["pnl"]<0)
    return result


def get_all_bots(bot_filter: int = 0):
    bots = []
    bot_count = int(os.getenv("BOT_COUNT","1"))
    indices = [bot_filter-1] if bot_filter>0 else range(bot_count)
    for i in indices:
        prefix = f"BOT_{i+1}"
        name   = os.getenv(f"{prefix}_NAME",f"Bot {i+1}")
        slug   = name.lower().replace(" ","_")
        candidatos = [
            os.path.join(BASE,f"bot_bot_{slug}.log"),
            os.path.join(BASE,f"bot_{slug}.log"),
            os.path.join(BASE,"bot.log"),
        ]
        for f in sorted(glob.glob(os.path.join(BASE,"*.log"))):
            if slug in os.path.basename(f).lower() and f not in candidatos:
                candidatos.insert(0,f)
        log_file = next((f for f in candidatos if os.path.exists(f)),candidatos[-1])
        bots.append(parse_bot_log(log_file,name,i))
    if not bots: bots.append(parse_bot_log(os.path.join(BASE,"bot.log"),"Principal",0))
    return bots


# ── Relatório e Telegram ──────────────────────────────────────────────────────

def gerar_relatorio(bots: list, tipo: str = "diario") -> str:
    hoje  = date.today().strftime("%d/%m/%Y")
    hora  = datetime.now().strftime("%H:%M")
    tp    = sum(b["pnl"] for b in bots)
    tops  = sum(len(b["trades"]) for b in bots)
    tw    = sum(b["wins"] for b in bots)
    tl    = sum(b["losses"] for b in bots)
    tot   = tw + tl
    wr    = f"{round(tw/tot*100)}%" if tot>0 else "—"
    at    = sum(1 for b in bots if b["bot_running"])
    ab    = sum(1 for b in bots if b.get("position"))
    ep    = "🟢" if tp>=0 else "🔴"
    titulo = "📊 *RELATÓRIO DIÁRIO — ScalpBot*" if tipo=="diario" else "📈 *STATUS — ScalpBot*"
    lines = [titulo, f"📅 {hoje} às {hora}","",
        "━━━━━━━━━━━━━━━━━━━━","*RESUMO GERAL*",
        f"{ep} PnL Total: `{'+'if tp>=0 else ''}${tp:.4f}`",
        f"🤖 Bots ativos: `{at}/{len(bots)}`",
        f"📋 Operações: `{tops}` ({tw}W / {tl}L)",
        f"🎯 Win Rate: `{wr}`",
        f"📌 Posições abertas: `{ab}`","",
        "━━━━━━━━━━━━━━━━━━━━"]
    for b in bots:
        exch = b.get("exchange","binance").upper()
        pnl  = b["pnl"]; ep2="🟢" if pnl>=0 else "🔴"
        t2   = (b["wins"]or 0)+(b["losses"]or 0)
        wr2  = f"{round(b['wins']/t2*100)}%" if t2>0 else "—"
        usdt = b.get("usdt") or 0
        st   = "✅ ATIVO" if b["bot_running"] else "⛔ INATIVO"
        lines += [f"*{b['emoji']} {b['name']}* ({exch})",f"Status: {st}",
            f"{ep2} PnL: `{'+'if pnl>=0 else ''}${pnl:.4f}`",
            f"💵 USDT: `${usdt:.2f}`",f"📊 Ops: `{t2}` | WR: `{wr2}`"]
        if b.get("position"):
            pos=b["position"]; lines.append(f"📌 Posição: `{pos['symbol']}` @ ${pos['entry_price']:.4f}")
        if b.get("active_symbol"): lines.append(f"🔍 Monitorando: `{b['active_symbol']}`")
        lines.append("")
    lines += ["━━━━━━━━━━━━━━━━━━━━",
        "💡 Comandos: /status /saldo /ops /scanner",
        "_ScalpBot Multi-Exchange v3.0_"]
    return "\n".join(lines)


def send_tg_all(msg: str):
    try:
        import requests as rq
    except ImportError:
        import urllib.request as rq
        return []
    enviados = []
    bc = int(os.getenv("BOT_COUNT","1"))
    for i in range(1, bc+1):
        token = os.getenv(f"BOT_{i}_TELEGRAM_TOKEN","").strip()
        chat  = os.getenv(f"BOT_{i}_TELEGRAM_CHAT","").strip()
        if not token or not chat: continue
        try:
            r = rq.post(f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id":chat,"text":msg,"parse_mode":"Markdown"},timeout=10,proxies={})
            if r.json().get("ok"): enviados.append(f"BOT_{i}")
        except Exception as e: print(f"[TG] Erro BOT_{i}: {e}")
    return enviados


def proc_cmd(text: str) -> str:
    cmd = text.strip().lower().split()[0] if text.strip() else ""
    bots = get_all_bots()
    if cmd in ("/status","/start"): return gerar_relatorio(bots,"status")
    if cmd == "/relatorio": return gerar_relatorio(bots,"diario")
    if cmd == "/saldo":
        lines=["💵 *SALDO DAS CONTAS*\n"]
        for b in bots:
            usdt=b.get("usdt") or 0; exch=b.get("exchange","binance").upper()
            lines.append(f"{b['emoji']} *{b['name']}* ({exch})\n  USDT: `${usdt:.2f}`\n")
        return "\n".join(lines)
    if cmd == "/ops":
        lines=["📋 *ÚLTIMAS OPERAÇÕES*\n"]; all_ops=[]
        for b in bots:
            for t in b.get("trades",[]): all_ops.append({**t,"_bot":b["name"]})
        all_ops.sort(key=lambda x:x.get("close",""),reverse=True)
        for op in all_ops[:5]:
            ep="✅" if op.get("pnl",0)>=0 else "❌"
            lines.append(f"{ep} {op['_bot']} | {op.get('symbol','?')} | `${op.get('pnl',0):.4f}`")
        if not all_ops: lines.append("Nenhuma operação ainda.")
        return "\n".join(lines)
    if cmd == "/scanner":
        lines=["🔍 *SCANNER DE MERCADO*\n"]
        for b in bots:
            if b.get("scanner"):
                lines.append(f"*{b['name']}*")
                for s in b["scanner"][:3]:
                    star="★" if s["symbol"]==b.get("active_symbol") else " "
                    lines.append(f"{star} `{s['symbol']}` Score:{s['score']} Vol:{s['volume']}M")
                lines.append("")
        if not any(b.get("scanner") for b in bots): lines.append("Sem dados ainda.")
        return "\n".join(lines)
    if cmd.startswith("/pausar"):
        parts=text.strip().split()
        if len(parts)>1 and parts[1].isdigit():
            idx=int(parts[1]); set_key(ENV,f"BOT_{idx}_TELEGRAM_ATIVO","false")
            load_dotenv(dotenv_path=ENV,override=True)
            return f"⏸ Notificações do Bot {idx} pausadas."
        return "Uso: /pausar N (ex: /pausar 1)"
    if cmd.startswith("/ativar"):
        parts=text.strip().split()
        if len(parts)>1 and parts[1].isdigit():
            idx=int(parts[1]); set_key(ENV,f"BOT_{idx}_TELEGRAM_ATIVO","true")
            load_dotenv(dotenv_path=ENV,override=True)
            return f"✅ Notificações do Bot {idx} ativadas."
        return "Uso: /ativar N (ex: /ativar 1)"
    return "❓ Comando não reconhecido. Use:\n/status /relatorio /saldo /ops /scanner /pausar N /ativar N"


# ── Agendador relatório às 22h ────────────────────────────────────────────────

def _scheduler():
    while True:
        agora = datetime.now()
        if agora.hour == 22 and agora.minute == 0:
            print("[SCHEDULER] Enviando relatório diário 22h...")
            bots = get_all_bots()
            msg  = gerar_relatorio(bots,"diario")
            env  = send_tg_all(msg)
            print(f"[SCHEDULER] Enviado para: {env}")
            time.sleep(61)
        time.sleep(30)

threading.Thread(target=_scheduler,daemon=True,name="scheduler").start()


# ── Polling Telegram ──────────────────────────────────────────────────────────

def _tg_poller():
    try:
        import requests as rq
    except ImportError:
        return
    offset = 0
    while True:
        try:
            bc = int(os.getenv("BOT_COUNT","1"))
            for i in range(1, bc+1):
                token = os.getenv(f"BOT_{i}_TELEGRAM_TOKEN","").strip()
                if not token: continue
                r = rq.get(f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"offset":offset,"timeout":5,"limit":5},timeout=10,proxies={})
                updates = r.json().get("result",[])
                for u in updates:
                    offset = max(offset, u["update_id"]+1)
                    msg    = u.get("message",{})
                    text   = msg.get("text","")
                    chat_id= str(msg.get("chat",{}).get("id",""))
                    if text.startswith("/"):
                        resp = proc_cmd(text)
                        rq.post(f"https://api.telegram.org/bot{token}/sendMessage",
                            json={"chat_id":chat_id,"text":resp,"parse_mode":"Markdown"},
                            timeout=10,proxies={})
        except: pass
        time.sleep(3)

threading.Thread(target=_tg_poller,daemon=True,name="tg-poller").start()


# ── Rotas Flask ───────────────────────────────────────────────────────────────

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/api/bots")
def api_bots(): return jsonify(get_all_bots(app.config.get("BOT_FILTER",0)))

@app.route("/api/status")
def api_status():
    bots=get_all_bots(app.config.get("BOT_FILTER",0))
    return jsonify(bots[0] if bots else {})

@app.route("/api/report/preview")
def report_preview():
    bots=get_all_bots(); return jsonify({"text":gerar_relatorio(bots,"diario")})

@app.route("/api/report/send", methods=["POST"])
def report_send():
    bots=get_all_bots(); msg=gerar_relatorio(bots,"diario"); env=send_tg_all(msg)
    return jsonify({"ok":bool(env),"msg":f"✓ Enviado para: {', '.join(env) if env else 'nenhum bot configurado'}"})

@app.route("/api/notif/<int:idx>", methods=["POST"])
def save_notif(idx):
    try:
        cfg=request.get_json(); prefix=f"BOT_{idx+1}"
        for key,val in cfg.items(): set_key(ENV,f"{prefix}_NOTIFY_{key.upper()}","true" if val else "false")
        load_dotenv(dotenv_path=ENV,override=True); return jsonify({"ok":True})
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}),500

@app.route("/api/tg_ativo/<int:idx>", methods=["POST"])
def save_tg_ativo(idx):
    try:
        cfg=request.get_json(); prefix=f"BOT_{idx+1}"
        set_key(ENV,f"{prefix}_TELEGRAM_ATIVO","true" if cfg.get("ativo") else "false")
        load_dotenv(dotenv_path=ENV,override=True); return jsonify({"ok":True})
    except Exception as e: return jsonify({"ok":False,"msg":str(e)}),500

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=5000)
    parser.add_argument("--bot",type=int,default=0)
    args=parser.parse_args()
    app.config["BOT_FILTER"]=args.bot
    print(f" ScalpBot Dashboard Unificado v3.0 — http://localhost:{args.port}")
    app.run(host="0.0.0.0",port=args.port,debug=False)
