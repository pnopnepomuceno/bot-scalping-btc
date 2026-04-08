"""
ScalpBot Dashboard Multi-Conta — v2.0
Design refinado com melhor legibilidade e UX
"""
from flask import Flask, jsonify, render_template_string, request
import os, re, glob, json
from datetime import datetime
from dotenv import load_dotenv, set_key

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ENV  = os.path.join(BASE, '.env')
load_dotenv(dotenv_path=ENV)

THEMES = [
    {"accent":"#38bdf8","accent2":"#34d399","bg":"#060c1a","s1":"#0a1628","s2":"#0e1e36","s3":"#132544","name":"Azul"},
    {"accent":"#fb923c","accent2":"#fbbf24","bg":"#0f0a04","s1":"#1a1208","s2":"#261b0d","s3":"#332312","name":"Laranja"},
    {"accent":"#c084fc","accent2":"#f472b6","bg":"#080510","s1":"#120a1e","s2":"#1a102c","s3":"#22153a","name":"Roxo"},
    {"accent":"#4ade80","accent2":"#a3e635","bg":"#030a06","s1":"#071510","s2":"#0c1e18","s3":"#112820","name":"Verde"},
    {"accent":"#f87171","accent2":"#fb923c","bg":"#100404","s1":"#1e0808","s2":"#2c0f0f","s3":"#3a1515","name":"Vermelho"},
]

HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScalpBot</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --accent:#38bdf8;--accent2:#34d399;
  --bg:#060c1a;--s1:#0a1628;--s2:#0e1e36;--s3:#132544;
  --green:#4ade80;--red:#f87171;--amber:#fbbf24;--purple:#c084fc;
  --text:#e2eeff;--muted:#5a7299;--border:rgba(255,255,255,.07);
  --mono:'Space Mono',monospace;--font:'DM Sans',sans-serif;
  --r:12px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;font-size:14px}

/* ── Header ── */
.hdr{
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;height:52px;
  background:rgba(10,22,40,.9);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;
}
.brand{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--accent);
  letter-spacing:.15em;display:flex;align-items:center;gap:10px}
.brand-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 12px var(--accent)}
.hdr-r{display:flex;align-items:center;gap:16px}
.live-wrap{display:flex;align-items:center;gap:7px}
.live{width:7px;height:7px;border-radius:50%;background:var(--muted);transition:all .3s}
.live.on{background:var(--green);box-shadow:0 0 10px var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.bot-st{font-family:var(--mono);font-size:11px;color:var(--muted)}
.bot-st.on{color:var(--green)}
.clk{font-family:var(--mono);font-size:11px;color:var(--muted);
  background:var(--s1);padding:4px 10px;border-radius:6px;border:1px solid var(--border)}
.overview-btn{
  font-family:var(--mono);font-size:10px;font-weight:700;
  padding:5px 12px;border-radius:7px;border:1px solid rgba(56,189,248,.3);
  background:rgba(56,189,248,.08);color:var(--accent);
  text-decoration:none;letter-spacing:.05em;
  transition:all .2s;display:flex;align-items:center;gap:6px
}
.overview-btn:hover{background:rgba(56,189,248,.15);border-color:var(--accent)}

/* ── Ticker ── */
.ticker{
  display:flex;overflow-x:auto;scrollbar-width:none;
  background:var(--s1);border-bottom:1px solid var(--border);
}
.ticker::-webkit-scrollbar{display:none}
.ti{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:8px 20px;border-right:1px solid var(--border);min-width:110px;
  flex-shrink:0;cursor:default;transition:background .15s;gap:3px;
}
.ti:hover{background:var(--s2)}
.ti.hi{background:rgba(56,189,248,.06);border-bottom:2px solid var(--accent)}
.ti-s{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:.1em}
.ti-p{font-family:var(--mono);font-size:13px;font-weight:700}
.ti-c{font-family:var(--mono);font-size:10px}
.up{color:var(--green)}.dn{color:var(--red)}

/* ── Layout principal ── */
main{padding:20px 24px;display:flex;flex-direction:column;gap:16px;max-width:1600px;margin:0 auto}

/* ── Tabs ── */
.tabs{display:flex;gap:8px;flex-wrap:wrap}
.tab{
  padding:8px 18px;border-radius:10px;border:1px solid var(--border);
  background:var(--s1);color:var(--muted);font-size:13px;font-weight:500;
  cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:8px;
  font-family:var(--font);white-space:nowrap;
}
.tab:hover{border-color:var(--accent);color:var(--text)}
.tab.on{background:rgba(56,189,248,.1);border-color:var(--accent);color:var(--accent)}
.tab .dot{width:7px;height:7px;border-radius:50%;background:var(--muted);flex-shrink:0}
.tab .dot.on{background:var(--green);box-shadow:0 0 8px var(--green)}
.exch{font-size:9px;font-weight:700;padding:2px 6px;border-radius:5px;font-family:var(--mono)}
.exch.bnb{background:rgba(240,185,11,.12);color:#f0b90b;border:1px solid rgba(240,185,11,.2)}
.exch.okx{background:rgba(192,132,252,.12);color:#c084fc;border:1px solid rgba(192,132,252,.2)}
.badge-sim{font-size:9px;background:rgba(251,191,36,.12);color:var(--amber);
  border:1px solid rgba(251,191,36,.2);padding:2px 6px;border-radius:5px;font-family:var(--mono)}

.panel{display:none}
.panel.on{display:flex;flex-direction:column;gap:14px}

/* ── Stats grid ── */
.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
@media(max-width:1200px){.stats{grid-template-columns:repeat(3,1fr)}}
@media(max-width:600px){.stats{grid-template-columns:repeat(2,1fr)}}
.st{
  background:var(--s1);border:1px solid var(--border);border-radius:var(--r);
  padding:14px 16px;position:relative;overflow:hidden;
  transition:border-color .2s;
}
.st:hover{border-color:rgba(255,255,255,.12)}
.st::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent);opacity:.4}
.st.g::before{background:var(--green)}
.st.r::before{background:var(--red)}
.st.b::before{background:var(--accent)}
.st-l{font-size:9px;font-weight:600;letter-spacing:.12em;color:var(--muted);margin-bottom:8px;text-transform:uppercase}
.st-v{font-family:var(--mono);font-size:20px;font-weight:700;line-height:1}
.st-v.g{color:var(--green)}.st-v.r{color:var(--red)}.st-v.b{color:var(--accent)}
.st-s{font-size:11px;color:var(--muted);margin-top:5px;font-family:var(--mono)}

/* ── Middle row ── */
.mid{display:grid;grid-template-columns:1fr 320px;gap:12px}
@media(max-width:900px){.mid{grid-template-columns:1fr}}

/* ── Cards ── */
.card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:16px;overflow:hidden}
.ct{font-size:10px;font-weight:700;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}
.ch{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.cw{position:relative;height:160px}

/* ── Posição aberta ── */
.pos-e{font-size:13px;color:var(--muted);text-align:center;padding:32px 0}
.pos-card{background:var(--s2);border:1px solid rgba(56,189,248,.15);border-radius:10px;padding:14px}
.pos-sym{font-family:var(--mono);font-size:22px;font-weight:700;color:var(--accent);margin-bottom:12px}
.pos-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;
  border-bottom:1px solid var(--border);font-size:12px}
.pos-row:last-child{border:none}
.pos-lbl{color:var(--muted)}
.pos-val{font-family:var(--mono);font-weight:600}

/* ── Indicadores técnicos ── */
.ind-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}
.ind-item{background:var(--s2);border-radius:8px;padding:8px 10px;text-align:center}
.ind-label{font-size:9px;color:var(--muted);letter-spacing:.08em;margin-bottom:4px}
.ind-val{font-family:var(--mono);font-size:13px;font-weight:700}

/* ── Operações ── */
.ops-c{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.ops-hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;
  border-bottom:1px solid var(--border)}
.op-tabs{display:flex;gap:4px}
.ot{font-family:var(--mono);font-size:9px;font-weight:700;padding:4px 10px;border-radius:6px;
  border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;
  transition:all .15s;letter-spacing:.06em}
.ot.on{background:rgba(56,189,248,.1);border-color:rgba(56,189,248,.3);color:var(--accent)}
.ot:hover:not(.on){border-color:rgba(255,255,255,.15);color:var(--text)}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;white-space:nowrap}
th{color:var(--muted);font-size:9px;letter-spacing:.1em;padding:10px 14px;text-align:left;
  border-bottom:1px solid var(--border);font-weight:700;background:rgba(0,0,0,.2)}
td{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.03)}
tr:last-child td{border:none}
tr:hover td{background:rgba(255,255,255,.02)}
.bk{display:inline-block;padding:2px 8px;border-radius:5px;font-size:10px;font-weight:700}
.bsym{background:rgba(56,189,248,.1);color:var(--accent);border:1px solid rgba(56,189,248,.15)}
.pp{color:var(--green);font-weight:700}.pn{color:var(--red);font-weight:700}
.reason-badge{display:inline-block;padding:2px 7px;border-radius:5px;font-size:9px;font-weight:700}
.rb-sl{background:rgba(248,113,113,.1);color:var(--red);border:1px solid rgba(248,113,113,.2)}
.rb-tp{background:rgba(74,222,128,.1);color:var(--green);border:1px solid rgba(74,222,128,.2)}
.rb-fb{background:rgba(90,114,153,.1);color:var(--muted)}
.os{padding:10px 16px;font-size:11px;color:var(--muted);font-family:var(--mono);text-align:right}

/* ── Desempenho por par ── */
.pg{display:flex;gap:10px;flex-wrap:wrap;margin-top:4px}
.pg-item{background:var(--s2);border:1px solid var(--border);border-radius:8px;
  padding:10px 14px;min-width:120px;flex:1}
.pg-sym{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--accent);margin-bottom:4px}
.pg-val{font-family:var(--mono);font-size:13px;font-weight:700}
.pg-cnt{font-size:10px;color:var(--muted);margin-top:2px}

/* ── Bot row (scanner + log) ── */
.bot{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:900px){.bot{grid-template-columns:1fr}}

/* ── Scanner ── */
.sc-item{display:flex;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);gap:10px}
.sc-item:last-child{border:none}
.sc-sym{font-family:var(--mono);font-size:12px;font-weight:700;width:90px;color:var(--text)}
.sc-sym.best{color:var(--accent)}
.sc-bar-wrap{flex:1;height:4px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden}
.sc-bar{height:100%;border-radius:2px;background:var(--accent);transition:width .5s}
.sc-score{font-family:var(--mono);font-size:11px;color:var(--muted);width:44px;text-align:right}
.sc-chg{font-family:var(--mono);font-size:10px;width:52px;text-align:right}
.sc-vol{font-family:var(--mono);font-size:10px;color:var(--muted);width:52px;text-align:right}
.sc-wallet{font-size:9px;color:var(--amber);margin-left:2px}

/* ── Log ── */
.lw{height:240px;overflow-y:auto;padding:8px;scrollbar-width:thin;scrollbar-color:var(--s3) transparent}
.lw::-webkit-scrollbar{width:4px}
.lw::-webkit-scrollbar-thumb{background:var(--s3);border-radius:2px}
.ll{display:block;line-height:18px;color:#5a7299;font-size:10px;padding:1px 2px;font-family:var(--mono);white-space:pre-wrap;word-break:break-all}
.ll.buy{color:#4ade80 !important}.ll.sell{color:#f87171 !important}
.ll.warn{color:#fbbf24 !important}.ll.err{color:#f87171 !important;opacity:.8}
.ll.ia{color:#38bdf8 !important}.ll.scan{color:#c084fc !important}

/* ── Notificações ── */
.notif-panel{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:16px}
.notif-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.tg-row{display:flex;align-items:center;gap:10px}
.notif-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:2px}
@media(max-width:900px){.notif-grid{grid-template-columns:repeat(2,1fr)}}
.notif-item{background:var(--s2);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.notif-label{font-size:12px;font-weight:500;margin-bottom:2px}
.notif-desc{font-size:10px;color:var(--muted)}
.toggle{position:relative;display:inline-block;width:40px;height:22px;cursor:pointer;flex-shrink:0}
.toggle input{opacity:0;width:0;height:0}
.toggle-track{position:absolute;inset:0;background:rgba(255,255,255,.1);border-radius:11px;transition:.3s;border:1px solid var(--border)}
.toggle-thumb{position:absolute;left:3px;top:3px;width:16px;height:16px;background:var(--muted);border-radius:50%;transition:.3s}
.toggle input:checked+.toggle-track{background:rgba(56,189,248,.2);border-color:var(--accent)}
.toggle input:checked~.toggle-thumb{left:21px;background:var(--accent);box-shadow:0 0 8px var(--accent)}
.save-btn{padding:8px 20px;border-radius:8px;border:1px solid rgba(56,189,248,.3);
  background:rgba(56,189,248,.1);color:var(--accent);font-weight:600;font-size:13px;
  cursor:pointer;transition:all .2s;font-family:var(--font)}
.save-btn:hover{background:rgba(56,189,248,.2)}
.save-msg{font-size:12px;color:var(--green);margin-left:10px;display:none;font-family:var(--mono)}

/* ── Separador de seção ── */
.section-sep{display:flex;align-items:center;gap:10px;margin:2px 0}
.section-sep-txt{font-size:9px;font-weight:700;letter-spacing:.15em;color:var(--muted);text-transform:uppercase;white-space:nowrap}
.section-sep-line{flex:1;height:1px;background:var(--border)}
</style>
</head>
<body>

<div class="hdr">
  <div class="brand"><div class="brand-dot"></div>SCALP<span style="color:var(--text);opacity:.5">BOT</span></div>
  <div class="hdr-r">
    <a class="overview-btn" href="http://HOSTNAME:5004" target="_blank">⊞ Visão Geral</a>
    <div class="live-wrap"><div class="live" id="live-dot"></div><span class="bot-st" id="bot-st">—</span></div>
    <div class="clk" id="clk">--:--:--</div>
  </div>
</div>

<div class="ticker" id="ticker">
  <div class="ti hi" id="tick-BTCUSDT"><div class="ti-s">BTC</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-ETHUSDT"><div class="ti-s">ETH</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-BNBUSDT"><div class="ti-s">BNB</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-SOLUSDT"><div class="ti-s">SOL</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-XRPUSDT"><div class="ti-s">XRP</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
</div>

<main>
  <div class="tabs" id="tabs"></div>
  <div id="panels"></div>
</main>

<script>
const NOTIF_TYPES={
  inicio:     {label:'Inicialização', desc:'Bot iniciado/encerrado'},
  compra:     {label:'Compra',        desc:'Ordem de compra executada'},
  venda:      {label:'Venda',         desc:'Ordem de venda executada'},
  stop_loss:  {label:'Stop-loss',     desc:'Stop-loss atingido'},
  take_profit:{label:'Take-profit',   desc:'Take-profit atingido'},
  par_troca:  {label:'Troca de par',  desc:'Scanner trocou o ativo'},
  ia_erro:    {label:'Erro IA',       desc:'Falha na API Anthropic'},
  resumo:     {label:'Resumo',        desc:'Resumo ao encerrar'},
};

const THEMES=[
  {accent:'#38bdf8',accent2:'#34d399',bg:'#060c1a',s1:'#0a1628',s2:'#0e1e36',s3:'#132544'},
  {accent:'#fb923c',accent2:'#fbbf24',bg:'#0f0a04',s1:'#1a1208',s2:'#261b0d',s3:'#332312'},
  {accent:'#c084fc',accent2:'#f472b6',bg:'#080510',s1:'#120a1e',s2:'#1a102c',s3:'#22153a'},
  {accent:'#4ade80',accent2:'#a3e635',bg:'#030a06',s1:'#071510',s2:'#0c1e18',s3:'#112820'},
  {accent:'#f87171',accent2:'#fb923c',bg:'#100404',s1:'#1e0808',s2:'#2c0f0f',s3:'#3a1515'},
];

let bots=[], cur=0, charts={};

function fmt(n,d=2){return(+n||0).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}

function applyTheme(idx){
  const t=THEMES[idx%THEMES.length];
  const r=document.documentElement.style;
  r.setProperty('--accent',t.accent);r.setProperty('--accent2',t.accent2);
  r.setProperty('--bg',t.bg);r.setProperty('--s1',t.s1);r.setProperty('--s2',t.s2);r.setProperty('--s3',t.s3);
}

function reasonBadge(r){
  if(!r)return'—';
  const ru=r.toUpperCase();
  if(ru.includes('STOP_LOSS'))  return`<span class="reason-badge rb-sl">SL</span>`;
  if(ru.includes('TAKE_PROFIT'))return`<span class="reason-badge rb-tp">TP</span>`;
  if(ru.includes('[FB]'))       return`<span class="reason-badge rb-fb">TÉC</span>`;
  return`<span class="reason-badge rb-fb">${r.slice(0,12)}</span>`;
}

function initChart(id){
  const c=document.getElementById(id);if(!c)return;
  const ctx=c.getContext('2d');
  if(charts[id]) charts[id].destroy();
  const accent=getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
  charts[id]=new Chart(ctx,{
    type:'line',
    data:{labels:[],datasets:[
      {label:'Acum.',data:[],borderColor:accent,backgroundColor:accent+'18',
       fill:true,tension:.4,borderWidth:2,pointRadius:0,pointHoverRadius:4},
      {label:'Por op.',data:[],borderColor:'rgba(255,255,255,.2)',backgroundColor:'transparent',
       fill:false,tension:.4,borderWidth:1,pointRadius:0,pointHoverRadius:3},
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false,
        backgroundColor:'rgba(10,22,40,.95)',titleColor:'#e2eeff',bodyColor:'#5a7299',
        borderColor:'rgba(255,255,255,.1)',borderWidth:1,padding:10,cornerRadius:8}},
      scales:{x:{display:false},y:{
        display:true,grid:{color:'rgba(255,255,255,.04)',drawBorder:false},
        ticks:{color:'#5a7299',font:{size:9},maxTicksLimit:5,
               callback:v=>'$'+v.toFixed(2)}
      }}}
  });
}

function updateChart(id,trades){
  if(!charts[id]||!trades.length)return;
  let acum=0;
  const labels=trades.map((_,i)=>'#'+(i+1));
  const byOp=trades.map(t=>t.pnl||0);
  const cumul=trades.map(t=>{acum+=t.pnl||0;return+acum.toFixed(4);});
  charts[id].data.labels=labels;
  charts[id].data.datasets[0].data=cumul;
  charts[id].data.datasets[1].data=byOp;
  const accent=getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
  charts[id].data.datasets[0].borderColor=accent;
  charts[id].data.datasets[0].backgroundColor=accent+'18';
  charts[id].update('none');
}

function renderPos(b,idx){
  const el=document.getElementById(`pos-${idx}`);if(!el)return;
  if(!b.position){el.innerHTML='<div class="pos-e">Aguardando sinal...</div>';return;}
  const p=b.position;
  const curr=b.price||p.entry_price;
  const pct=p.entry_price>0?((curr-p.entry_price)/p.entry_price*100):0;
  const pnl=(pct/100*p.usdt_used);
  const sl=b.stop_loss*100; const tp=b.take_profit*100;
  el.innerHTML=`<div class="pos-card">
    <div class="pos-sym">${(p.symbol||'—').replace('USDT','').replace('-USDT','')}/USDT</div>
    <div class="pos-row"><span class="pos-lbl">Entrada</span><span class="pos-val">$${fmt(p.entry_price,4)}</span></div>
    <div class="pos-row"><span class="pos-lbl">Atual</span><span class="pos-val" style="color:${pct>=0?'var(--green)':'var(--red)'}">$${fmt(curr,4)}</span></div>
    <div class="pos-row"><span class="pos-lbl">PnL</span><span class="pos-val ${pct>=0?'pp':'pn'}">${pct>=0?'+':''}${pct.toFixed(2)}% / ${pnl>=0?'+':''}$${Math.abs(pnl).toFixed(4)}</span></div>
    <div class="pos-row"><span class="pos-lbl">Capital</span><span class="pos-val">$${fmt(p.usdt_used)}</span></div>
    <div class="pos-row"><span class="pos-lbl">Qty</span><span class="pos-val">${p.qty||'—'}</span></div>
    <div class="pos-row"><span class="pos-lbl" style="color:var(--red)">Stop /${sl.toFixed(1)}%</span>
      <span class="pos-val" style="color:var(--red)">$${fmt(p.entry_price*(1-b.stop_loss),4)}</span></div>
    <div class="pos-row"><span class="pos-lbl" style="color:var(--green)">Target +${tp.toFixed(1)}%</span>
      <span class="pos-val" style="color:var(--green)">$${fmt(p.entry_price*(1+b.take_profit),4)}</span></div>
  </div>`;
}

function renderScanner(b,idx){
  const el=document.getElementById(`sc-${idx}`);if(!el||!b.scanner?.length)return;
  const maxScore=Math.max(...b.scanner.map(s=>s.score),1);
  el.innerHTML=b.scanner.map(s=>{
    const isBest=s.symbol===b.active_symbol;
    const wallet=s.in_wallet?'<span class="sc-wallet">💼</span>':'';
    const chgColor=s.change>=0?'var(--green)':'var(--red)';
    return`<div class="sc-item">
      <div class="sc-sym ${isBest?'best':''}">${isBest?'★ ':' '}${s.symbol}${wallet}</div>
      <div class="sc-bar-wrap"><div class="sc-bar" style="width:${(s.score/maxScore*100).toFixed(0)}%"></div></div>
      <div class="sc-score">${s.score}</div>
      <div class="sc-chg" style="color:${chgColor}">${s.change>=0?'+':''}${s.change}%</div>
      <div class="sc-vol">${s.volume}M</div>
    </div>`;
  }).join('');
  const ts=document.getElementById(`sc-ts-${idx}`);
  if(ts)ts.textContent=b.scan_time?b.scan_time.slice(11,19):'—';
}

function renderOps(idx,trades){
  const tb=document.getElementById(`ops-${idx}`);if(!tb)return;
  if(!trades?.length){
    tb.innerHTML='<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:24px;font-family:var(--mono);font-size:11px">Nenhuma operação ainda</td></tr>';
    return;
  }
  tb.innerHTML=[...trades].reverse().map((t,i)=>{
    const pct=t.usdt_used>0?(t.pnl/t.usdt_used*100).toFixed(2)+'%':'—';
    const c=t.pnl>=0?'pp':'pn';
    return`<tr>
      <td style="color:var(--muted);font-size:10px">${trades.length-i}</td>
      <td><span class="bk bsym">${(t.symbol||'—').replace('USDT','').replace('-USDT','')}</span></td>
      <td>$${fmt(t.entry||0,4)}</td>
      <td>${t.exit>0?'$'+fmt(t.exit,4):'<span style="color:var(--amber)">aberta</span>'}</td>
      <td style="color:var(--muted)">${t.qty||'—'}</td>
      <td style="color:var(--muted)">$${fmt(t.usdt_used||0)}</td>
      <td class="${c}">${t.pnl>=0?'+':''}$${(t.pnl||0).toFixed(4)}</td>
      <td class="${c}">${pct}</td>
      <td>${reasonBadge(t.reason)}</td>
      <td style="color:var(--muted);font-size:10px">${(t.close||'—').slice(0,16)}</td>
    </tr>`;
  }).join('');
}

function renderLog(b,idx){
  const lwe=document.getElementById(`lw-${idx}`);
  if(!lwe||!b.logs?.length)return;
  const lce=document.getElementById(`lc-${idx}`);
  if(lce)lce.textContent=b.logs.length+' linhas';
  const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  lwe.innerHTML=b.logs.slice(-100).reverse().map(l=>{
    let c='ll';
    if(l.includes('Comprado'))c+=' buy';
    else if(l.includes('Fechado')||l.includes('PnL:'))c+=' sell';
    else if(l.includes('Scanner')||l.includes('Melhor:'))c+=' scan';
    else if(l.includes('[IA]')||l.includes('[ECON]')||l.includes('[OKX]')||l.includes('[BINANCE]'))c+=' ia';
    else if(l.includes('[TOR]')||l.includes('WARNING')||l.includes('[FB]'))c+=' warn';
    else if(l.includes('ERROR')||l.includes('[ERRO]'))c+=' err';
    return`<div class="${c}">${esc(l)}</div>`;
  }).join('');
}

function renderPairPerf(b,idx){
  const el=document.getElementById(`pg-${idx}`);if(!el)return;
  const byPair={};
  (b.trades||[]).forEach(t=>{
    const p=t.symbol||'?';
    if(!byPair[p])byPair[p]={pnl:0,cnt:0};
    byPair[p].pnl+=t.pnl||0;byPair[p].cnt++;
  });
  const pairs=Object.entries(byPair).sort((a,b)=>b[1].pnl-a[1].pnl);
  if(!pairs.length){el.innerHTML='<div style="color:var(--muted);font-size:12px">Sem dados ainda</div>';return;}
  el.innerHTML=pairs.map(([sym,d])=>{
    const pnlColor=d.pnl>=0?'var(--green)':'var(--red)';
    return`<div class="pg-item">
      <div class="pg-sym">${sym.replace('USDT','').replace('-USDT','')}</div>
      <div class="pg-val" style="color:${pnlColor}">${d.pnl>=0?'+':''}$${d.pnl.toFixed(4)}</div>
      <div class="pg-cnt">${d.cnt} op${d.cnt!==1?'s':''}</div>
    </div>`;
  }).join('');
}

function updatePanel(b,idx){
  // Stats
  const pnlEl=document.getElementById(`v-pnl-${idx}`);
  if(pnlEl){
    pnlEl.textContent=(b.pnl>=0?'+':'')+'$'+Math.abs(b.pnl||0).toFixed(4);
    pnlEl.className='st-v '+(b.pnl>0?'g':b.pnl<0?'r':'');
  }
  const best=b.trades?.filter(t=>t.pnl>0).sort((a,b)=>b.pnl-a.pnl)[0];
  const worst=b.trades?.filter(t=>t.pnl<0).sort((a,b)=>a.pnl-b.pnl)[0];
  const be=document.getElementById(`v-best-${idx}`);
  const bs=document.getElementById(`v-best-s-${idx}`);
  if(be)be.textContent=best?'+$'+best.pnl.toFixed(4):'—';
  if(bs)bs.textContent=best?best.symbol:'—';
  const we=document.getElementById(`v-worst-${idx}`);
  const ws=document.getElementById(`v-worst-s-${idx}`);
  if(we)we.textContent=worst?'-$'+Math.abs(worst.pnl).toFixed(4):'—';
  if(ws)ws.textContent=worst?worst.symbol:'—';
  const tot=(b.wins||0)+(b.losses||0);
  const wr=tot>0?Math.round(b.wins/tot*100):null;
  const wre=document.getElementById(`v-wr-${idx}`);
  const wrs=document.getElementById(`v-wr-s-${idx}`);
  if(wre){wre.textContent=wr!==null?wr+'%':'—';wre.style.color=wr>=55?'var(--green)':wr!==null&&wr<45?'var(--red)':'var(--text)'}
  if(wrs)wrs.textContent=`${b.wins||0}W / ${b.losses||0}L`;
  const ue=document.getElementById(`v-usdt-${idx}`);
  const oe=document.getElementById(`v-ops-${idx}`);
  if(ue)ue.textContent=b.usdt!=null?'$'+fmt(b.usdt):'—';
  if(oe)oe.textContent=(b.total_trades||0)+' operações';
  const pe=document.getElementById(`v-pos-${idx}`);
  const ps=document.getElementById(`v-pos-s-${idx}`);
  if(pe)pe.textContent=b.position?b.position.symbol:'NENHUMA';
  if(ps)ps.textContent=b.position?('Entrada $'+fmt(b.position.entry_price,2)):'—';
  const pair=document.getElementById(`v-pair-${idx}`);
  if(pair)pair.textContent=b.active_symbol||'—';

  // Indicadores técnicos
  const indEl=document.getElementById(`ind-${idx}`);
  if(indEl&&b.rsi!=null){
    const rsiColor=b.rsi<40?'var(--green)':b.rsi>60?'var(--red)':'var(--text)';
    const macdColor=b.macd_signal==='bullish'?'var(--green)':'var(--red)';
    const bbColor=b.bb_pct<30?'var(--green)':b.bb_pct>70?'var(--red)':'var(--text)';
    indEl.innerHTML=`
      <div class="ind-item"><div class="ind-label">RSI</div><div class="ind-val" style="color:${rsiColor}">${b.rsi}</div></div>
      <div class="ind-item"><div class="ind-label">MACD</div><div class="ind-val" style="color:${macdColor}">${(b.macd_signal||'—').toUpperCase().slice(0,4)}</div></div>
      <div class="ind-item"><div class="ind-label">BB%</div><div class="ind-val" style="color:${bbColor}">${b.bb_pct}%</div></div>
      <div class="ind-item"><div class="ind-label">TEND</div><div class="ind-val" style="color:${b.trend==='alta'?'var(--green)':'var(--red)'}">↑</div></div>`;
  }

  renderPos(b,idx);
  renderScanner(b,idx);
  renderLog(b,idx);
  renderPairPerf(b,idx);
  updateChart(`ch-${idx}`,b.trades||[]);

  // Notif
  const tgAtivo=document.getElementById(`tg-ativo-${idx}`);
  if(tgAtivo)tgAtivo.checked=b.tg_ativo!==false;
  const grid=document.getElementById(`notif-grid-${idx}`);
  if(grid)grid.style.opacity=b.tg_ativo!==false?'1':'0.4';
  const tgs=document.getElementById(`tg-st-${idx}`);
  if(tgs){
    const exch=(b.exchange||'binance').toUpperCase();
    tgs.textContent=`${exch} | ${b.tg_token?(b.tg_ativo!==false?'✓ Telegram ativo':'⏸ Pausado'):'✗ Sem token'}`;
  }
  if(b.notif_cfg){
    Object.keys(NOTIF_TYPES).forEach(key=>{
      const el=document.getElementById(`notif-${idx}-${key}`);
      if(el)el.checked=b.notif_cfg[key]!==false;
    });
  }
}

async function saveTgAtivo(idx){
  const ativo=document.getElementById(`tg-ativo-${idx}`)?.checked;
  await fetch(`/api/tg_ativo/${idx}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ativo})});
  const grid=document.getElementById(`notif-grid-${idx}`);
  if(grid)grid.style.opacity=ativo?'1':'0.4';
  const msg=document.getElementById(`sv-${idx}`);
  if(msg){msg.textContent=ativo?'✓ Ativado!':'✓ Desativado!';msg.style.display='inline';setTimeout(()=>msg.style.display='none',2000);}
}

async function saveNotif(idx){
  const cfg={};
  Object.keys(NOTIF_TYPES).forEach(key=>{
    const el=document.getElementById(`notif-${idx}-${key}`);
    if(el)cfg[key]=el.checked;
  });
  await fetch(`/api/notif/${idx}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
  const msg=document.getElementById(`save-msg-${idx}`);
  if(msg){msg.style.display='inline';setTimeout(()=>msg.style.display='none',2000);}
}

function fops(idx,f,btn){
  document.querySelectorAll(`#ops-hdr-${idx} .ot`).forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  const tr=bots[idx]?.trades||[];
  renderOps(idx,f==='all'?tr:tr.filter(t=>f==='win'?t.pnl>=0:t.pnl<0));
}

function buildPanel(b,idx){
  const notifEntries=Object.entries(NOTIF_TYPES).map(([key,info])=>`
    <div class="notif-item">
      <div><div class="notif-label">${info.label}</div><div class="notif-desc">${info.desc}</div></div>
      <label class="toggle">
        <input type="checkbox" id="notif-${idx}-${key}" onchange="saveNotif(${idx})">
        <div class="toggle-track"></div><div class="toggle-thumb"></div>
      </label>
    </div>`).join('');

  return`<div class="panel" id="panel-${idx}">
    <div class="stats">
      <div class="st"><div class="st-l">PNL TOTAL</div><div class="st-v" id="v-pnl-${idx}">$0.0000</div><div class="st-s" id="v-pnl-s-${idx}">—</div></div>
      <div class="st g"><div class="st-l">MELHOR OP</div><div class="st-v g" id="v-best-${idx}">—</div><div class="st-s" id="v-best-s-${idx}">—</div></div>
      <div class="st r"><div class="st-l">PIOR OP</div><div class="st-v r" id="v-worst-${idx}">—</div><div class="st-s" id="v-worst-s-${idx}">—</div></div>
      <div class="st"><div class="st-l">WIN RATE</div><div class="st-v" id="v-wr-${idx}">—</div><div class="st-s" id="v-wr-s-${idx}">0W/0L</div></div>
      <div class="st b"><div class="st-l">SALDO USDT</div><div class="st-v b" id="v-usdt-${idx}">—</div><div class="st-s" id="v-ops-${idx}">0 operações</div></div>
      <div class="st"><div class="st-l">POSIÇÃO</div><div class="st-v" id="v-pos-${idx}">NENHUMA</div><div class="st-s" id="v-pos-s-${idx}">—</div></div>
    </div>

    <div id="ind-${idx}" class="ind-row"></div>

    <div class="mid">
      <div class="card">
        <div class="ch"><div class="ct">PNL ACUMULADO</div><div class="ct" id="v-pair-${idx}" style="color:var(--accent)">—</div></div>
        <div class="cw"><canvas id="ch-${idx}"></canvas></div>
      </div>
      <div class="card">
        <div class="ct" style="margin-bottom:10px">POSIÇÃO ABERTA</div>
        <div id="pos-${idx}"><div class="pos-e">Aguardando sinal...</div></div>
      </div>
    </div>

    <div class="ops-c">
      <div class="ops-hdr" id="ops-hdr-${idx}">
        <div class="ct">OPERAÇÕES</div>
        <div class="op-tabs">
          <button class="ot on" onclick="fops(${idx},'all',this)">TODAS</button>
          <button class="ot" onclick="fops(${idx},'win',this)">GANHOS</button>
          <button class="ot" onclick="fops(${idx},'loss',this)">PERDAS</button>
        </div>
      </div>
      <div class="tw"><table>
        <thead><tr><th>#</th><th>PAR</th><th>ENTRADA</th><th>SAÍDA</th><th>QTD</th><th>CAPITAL</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>DATA/HORA</th></tr></thead>
        <tbody id="ops-${idx}"></tbody>
      </table></div>
      <div class="os" id="os-${idx}"></div>
    </div>

    <div class="card">
      <div class="ch"><div class="ct">DESEMPENHO POR PAR</div></div>
      <div class="pg" id="pg-${idx}"><div style="color:var(--muted);font-size:12px">Sem dados ainda</div></div>
    </div>

    <div class="bot">
      <div class="card">
        <div class="ch"><div class="ct">SCANNER DE MERCADO</div><div class="ct" id="sc-ts-${idx}" style="color:var(--muted)">—</div></div>
        <div id="sc-${idx}"></div>
      </div>
      <div class="card">
        <div class="ch"><div class="ct">LOG EM TEMPO REAL</div><div class="ct" id="lc-${idx}" style="color:var(--muted)">0 linhas</div></div>
        <div class="lw" id="lw-${idx}"></div>
      </div>
    </div>

    <div class="notif-panel">
      <div class="notif-head">
        <div class="ct">NOTIFICAÇÕES TELEGRAM</div>
        <div class="tg-row">
          <span style="font-size:11px;color:var(--muted)" id="tg-st-${idx}">—</span>
          <label class="toggle" title="Ativar/desativar Telegram">
            <input type="checkbox" id="tg-ativo-${idx}" onchange="saveTgAtivo(${idx})">
            <div class="toggle-track"></div><div class="toggle-thumb"></div>
          </label>
        </div>
      </div>
      <div class="notif-grid" id="notif-grid-${idx}">${notifEntries}</div>
      <div style="display:flex;align-items:center;margin-top:14px">
        <button class="save-btn" onclick="saveNotif(${idx})">Salvar</button>
        <span class="save-msg" id="save-msg-${idx}">✓ Salvo!</span>
        <span class="save-msg" id="sv-${idx}" style="margin-left:8px">✓ Telegram atualizado!</span>
      </div>
    </div>
  </div>`;
}

async function refresh(){
  try{
    const data=await fetch('/api/bots').then(r=>r.json());
    const tabsEl=document.getElementById('tabs');
    const panelsEl=document.getElementById('panels');

    if(!tabsEl.children.length){
      data.forEach((b,i)=>{
        const tab=document.createElement('button');
        tab.className='tab'+(i===0?' on':'');
        tab.id=`tab-${i}`;
        const exch=(b.exchange||'binance').toLowerCase();
        const exchBadge=exch==='okx'
          ?'<span class="exch okx">OKX</span>'
          :'<span class="exch bnb">BNB</span>';
        tab.onclick=()=>{
          document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
          document.querySelectorAll('.panel').forEach(t=>t.classList.remove('on'));
          tab.classList.add('on');
          document.getElementById(`panel-${i}`).classList.add('on');
          cur=i; applyTheme(i);
        };
        tabsEl.appendChild(tab);
        const div=document.createElement('div');
        div.innerHTML=buildPanel(b,i);
        panelsEl.appendChild(div.firstChild||div);
      });
      setTimeout(()=>{
        const p=document.getElementById('panel-0');if(p)p.classList.add('on');
        data.forEach((_,i)=>initChart(`ch-${i}`));
        applyTheme(0);
      },100);
    }

    data.forEach((b,i)=>{
      const tab=document.getElementById(`tab-${i}`);
      if(tab){
        const exch=(b.exchange||'binance').toLowerCase();
        const exchBadge=exch==='okx'
          ?'<span class="exch okx">OKX</span>'
          :'<span class="exch bnb">BNB</span>';
        const dot=`<div class="dot ${b.bot_running?'on':''}"></div>`;
        const sim=b.testnet?'<span class="badge-sim">SIM</span>':'';
        tab.innerHTML=`${dot}${b.emoji||'🤖'} ${b.name} ${exchBadge}${sim}`;
      }
      bots[i]=b;
      if(document.getElementById(`panel-${i}`))updatePanel(b,i);
    });

    const anyOn=data.some(b=>b.bot_running);
    const ld=document.getElementById('live-dot');
    const st=document.getElementById('bot-st');
    if(ld)ld.className='live '+(anyOn?'on':'');
    if(st){
      st.textContent=anyOn?data.filter(b=>b.bot_running).length+' bot(s) ativo(s)':'INATIVO';
      st.className='bot-st '+(anyOn?'on':'');
    }
  }catch(e){
    const st=document.getElementById('bot-st');
    if(st)st.textContent='ERRO DE CONEXÃO';
  }
}

async function refreshTicker(){
  const pairs=['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT'];
  for(const sym of pairs){
    try{
      const r=await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${sym}`);
      const d=await r.json();
      const el=document.getElementById('tick-'+sym);if(!el)continue;
      const p=parseFloat(d.lastPrice),c=parseFloat(d.priceChangePercent);
      const fp=p>1000?'$'+p.toLocaleString('pt-BR',{minimumFractionDigits:2}):p>10?'$'+p.toFixed(2):'$'+p.toFixed(4);
      el.querySelector('.ti-p').textContent=fp;
      const ce=el.querySelector('.ti-c');
      ce.textContent=(c>=0?'+':'')+c.toFixed(2)+'%';
      ce.className='ti-c '+(c>=0?'up':'dn');
    }catch(e){}
  }
}

// Atualiza hostname do link visão geral
document.querySelectorAll('.overview-btn').forEach(a=>{
  a.href=a.href.replace('HOSTNAME',location.hostname);
});

setInterval(()=>{const e=document.getElementById('clk');if(e)e.textContent=new Date().toLocaleTimeString('pt-BR');},1000);
refresh();refreshTicker();
setInterval(refresh,5000);setInterval(refreshTicker,10000);
</script>
</body>
</html>'''


# ── Backend (mantido igual ao original) ──────────────────────────────────────

def parse_bot_log(log_file: str, bot_name: str, bot_idx: int = 0) -> dict:
    result = {
        "name": bot_name, "emoji": "🤖", "bot_running": False,
        "exchange": "binance", "testnet": False, "tg_token": False, "tg_ativo": True,
        "active_symbol": None, "price": None, "rsi": None, "trend": None,
        "macd_signal": None, "bb_pct": None, "usdt": None,
        "pnl": 0.0, "wins": 0, "losses": 0, "stop_loss": 0.005, "take_profit": 0.010,
        "position": None, "trades": [], "scanner": [],
        "scanner_scores": {}, "scan_time": None, "logs": [],
        "notif_cfg": {k: True for k in ["inicio","compra","venda","stop_loss","take_profit","par_troca","ia_erro","resumo"]},
    }
    prefix = f"BOT_{bot_idx+1}"
    result["emoji"]       = os.getenv(f"{prefix}_EMOJI", "🤖")
    result["exchange"]    = os.getenv(f"{prefix}_EXCHANGE", "binance").lower()
    result["testnet"]     = os.getenv(f"{prefix}_TESTNET","false").lower()=="true"
    result["tg_token"]    = bool(os.getenv(f"{prefix}_TELEGRAM_TOKEN",""))
    result["tg_ativo"]    = os.getenv(f"{prefix}_TELEGRAM_ATIVO","true").lower()=="true"
    result["stop_loss"]   = float(os.getenv(f"{prefix}_STOP_LOSS","0.005"))
    result["take_profit"] = float(os.getenv(f"{prefix}_TAKE_PROFIT","0.010"))
    for key in result["notif_cfg"]:
        val = os.getenv(f"{prefix}_NOTIFY_{key.upper()}")
        if val is not None:
            result["notif_cfg"][key] = val.lower() == "true"

    if not os.path.exists(log_file):
        return result
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        return result

    result["logs"] = [l.rstrip() for l in lines[-100:]]
    if lines:
        try:
            last_dt = datetime.strptime(lines[-1][:19], "%Y-%m-%d %H:%M:%S")
            result["bot_running"] = (datetime.now() - last_dt).total_seconds() < 300
        except: pass

    re_price = re.compile(r'\[([\w-]+)\] \$([\d,.]+) \| RSI:([\d.]+) \| Tend:(\w+) \| MACD:(\w+) \| BB:([-\d.]+)% \| USDT:([\d.]+)')
    re_wl    = re.compile(r'W:(\d+) L:(\d+)')
    re_pnl   = re.compile(r'Total: \$([-+]?[\d.]+)')
    re_close = re.compile(r'Fechado ([\w-]+) \(([^)]+)\).*PnL: \$([-+]?[\d.]+)')
    re_open  = re.compile(r'Comprado ([\d.]+) ([\w-]+) @ \$([\d,.]+) \(\$([\d,.]+)\)')
    re_scan  = re.compile(r'[★ ] ([\w-]+)\s+\| Score:\s*([\d.]+) \| Vol:\s*([\d.]+)M \| Var:([-+\d.]+)% \| Volat:([\d.]+)%')
    re_best  = re.compile(r'Melhor: ([\w-]+)')
    re_scan_t = re.compile(r'── Scanner')

    cur_entry = cur_sym = cur_qty = cur_usdt = None
    scanner_tmp = []; scan_active = False

    for line in lines:
        m = re_price.search(line)
        if m:
            result["active_symbol"] = m.group(1)
            result["price"]         = float(m.group(2).replace(",",""))
            result["rsi"]           = float(m.group(3))
            result["trend"]         = m.group(4)
            result["macd_signal"]   = m.group(5)
            result["bb_pct"]        = float(m.group(6))
            result["usdt"]          = float(m.group(7))

        m = re_wl.search(line)
        if m: result["wins"]=int(m.group(1)); result["losses"]=int(m.group(2))

        m = re_pnl.search(line)
        if m: result["pnl"] = float(m.group(1))

        if re_scan_t.search(line):
            scan_active=True; scanner_tmp=[]; result["scan_time"]=line[:19]
        if scan_active:
            m = re_scan.search(line)
            if m:
                scanner_tmp.append({"symbol":m.group(1),"score":float(m.group(2)),
                    "volume":m.group(3),"change":float(m.group(4)),
                    "volatility":m.group(5),"in_wallet":False})
                result["scanner_scores"][m.group(1)]=float(m.group(2))

        m = re_best.search(line)
        if m:
            result["active_symbol"] = m.group(1)
            if scanner_tmp: result["scanner"] = sorted(scanner_tmp,key=lambda x:x["score"],reverse=True)
            scan_active=False

        m = re_open.search(line)
        if m:
            cur_qty=m.group(1); cur_sym=m.group(2)
            cur_entry=float(m.group(3).replace(",","")); cur_usdt=float(m.group(4).replace(",",""))

        m = re_close.search(line)
        if m:
            result["trades"].append({
                "symbol":m.group(1),"entry":cur_entry or 0,"exit":0,
                "pnl":float(m.group(3)),"qty":cur_qty or "—",
                "usdt_used":cur_usdt or 0,"close":line[:19],"reason":m.group(2),
            })
            cur_entry=cur_sym=cur_qty=cur_usdt=None

    result["total_trades"] = len(result["trades"])
    if cur_entry and cur_sym:
        result["position"] = {"symbol":cur_sym,"entry_price":cur_entry,
                               "qty":cur_qty or "—","usdt_used":cur_usdt or 0}
    if result["trades"] and result["pnl"]==0.0:
        result["pnl"]=round(sum(t["pnl"] for t in result["trades"]),4)
        result["wins"]=sum(1 for t in result["trades"] if t["pnl"]>=0)
        result["losses"]=sum(1 for t in result["trades"] if t["pnl"]<0)
    return result


def get_all_bots(bot_filter: int = 0):
    bots = []
    bot_count = int(os.getenv("BOT_COUNT","1"))
    indices = [bot_filter - 1] if bot_filter > 0 else range(bot_count)
    for i in indices:
        prefix = f"BOT_{i+1}"
        name   = os.getenv(f"{prefix}_NAME", f"Bot {i+1}")
        slug   = name.lower().replace(" ","_")
        candidatos = [
            os.path.join(BASE, f"bot_bot_{slug}.log"),
            os.path.join(BASE, f"bot_{slug}.log"),
            os.path.join(BASE, f"bot.log"),
        ]
        for f in sorted(glob.glob(os.path.join(BASE, "*.log"))):
            if slug in os.path.basename(f).lower() and f not in candidatos:
                candidatos.insert(0, f)
        log_file = next((f for f in candidatos if os.path.exists(f)), candidatos[-1])
        bots.append(parse_bot_log(log_file, name, i))
    if not bots:
        bots.append(parse_bot_log(os.path.join(BASE,"bot.log"),"Principal",0))
    return bots


BOT_FILTER = 0

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/api/bots")
def api_bots(): return jsonify(get_all_bots(app.config.get("BOT_FILTER",0)))

@app.route("/api/status")
def api_status():
    bots = get_all_bots(app.config.get("BOT_FILTER",0))
    return jsonify(bots[0] if bots else {})

@app.route("/api/notif/<int:idx>", methods=["POST"])
def save_notif(idx):
    try:
        cfg = request.get_json()
        prefix = f"BOT_{idx+1}"
        for key, val in cfg.items():
            set_key(ENV, f"{prefix}_NOTIFY_{key.upper()}", "true" if val else "false")
        load_dotenv(dotenv_path=ENV, override=True)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/api/tg_ativo/<int:idx>", methods=["POST"])
def save_tg_ativo(idx):
    try:
        cfg = request.get_json()
        prefix = f"BOT_{idx+1}"
        set_key(ENV, f"{prefix}_TELEGRAM_ATIVO", "true" if cfg.get("ativo") else "false")
        load_dotenv(dotenv_path=ENV, override=True)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--bot",  type=int, default=0)
    args = parser.parse_args()
    app.config["BOT_FILTER"] = args.bot
    nome = f"Bot {args.bot}" if args.bot else "Todos os Bots"
    print(f" ScalpBot Dashboard v2.0 — {nome} — http://localhost:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False)
