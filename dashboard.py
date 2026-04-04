"""
ScalpBot Dashboard Multi-Conta com temas distintos e controle de notificações
Acesse: http://localhost:5000
"""
from flask import Flask, jsonify, render_template_string, request
import os, re, glob, json
from datetime import datetime
from dotenv import load_dotenv, set_key

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ENV  = os.path.join(BASE, '.env')
load_dotenv(dotenv_path=ENV)

# Temas distintos por índice de bot
THEMES = [
    {"name":"Azul Neon",  "accent":"#00b4fc","accent2":"#00f5a0","bg":"#070b14","s1":"#0d1526","s2":"#111d35","s3":"#172347"},
    {"name":"Laranja",    "accent":"#ff6b35","accent2":"#ffd700","bg":"#0f0800","s1":"#1a1000","s2":"#261800","s3":"#332100"},
    {"name":"Roxo",       "accent":"#a855f7","accent2":"#ec4899","bg":"#09050f","s1":"#140d1f","s2":"#1c1230","s3":"#26183d"},
    {"name":"Verde",      "accent":"#00e87a","accent2":"#84cc16","bg":"#050f08","s1":"#0a1f10","s2":"#0f2e18","s3":"#153d20"},
    {"name":"Vermelho",   "accent":"#ff4757","accent2":"#ff9f43","bg":"#0f0505","s1":"#1f0a0a","s2":"#2e0f0f","s3":"#3d1515"},
]

HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScalpBot</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --accent:#00b4fc;--accent2:#00f5a0;
  --bg:#070b14;--s1:#0d1526;--s2:#111d35;--s3:#172347;
  --green:#00f5a0;--red:#ff4757;--amber:#ffa502;--purple:#a66cff;
  --text:#e8f0ff;--muted:#6b7fa8;--border:rgba(255,255,255,.08);
  --mono:'JetBrains Mono',monospace;--font:'Outfit',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh}

.hdr{display:flex;align-items:center;justify-content:space-between;padding:12px 24px;
  border-bottom:1px solid var(--border);background:var(--s1);position:sticky;top:0;z-index:100}
.brand{font-family:var(--mono);font-size:14px;font-weight:700;color:var(--accent);letter-spacing:.1em}
.hdr-r{display:flex;align-items:center;gap:14px}
.live{width:8px;height:8px;border-radius:50%;background:var(--muted)}
.live.on{background:var(--green);box-shadow:0 0 10px var(--green);animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.chip{font-family:var(--mono);font-size:11px;color:var(--muted)}

.ticker{display:flex;overflow-x:auto;border-bottom:1px solid var(--border);background:var(--s1);scrollbar-width:none}
.ticker::-webkit-scrollbar{display:none}
.ti{display:flex;flex-direction:column;align-items:center;padding:9px 20px;
  border-right:1px solid var(--border);min-width:115px;flex-shrink:0;transition:background .2s;cursor:default}
.ti:hover{background:var(--s2)}
.ti.hi{background:rgba(0,180,252,.06);border-bottom:2px solid var(--accent)}
.ti-s{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:.12em;margin-bottom:4px}
.ti-p{font-family:var(--mono);font-size:14px;font-weight:600}
.ti-c{font-family:var(--mono);font-size:10px;margin-top:2px}
.up{color:var(--green)}.dn{color:var(--red)}

main{padding:18px 24px;display:flex;flex-direction:column;gap:16px}

/* Bot tabs */
.tabs{display:flex;gap:8px;flex-wrap:wrap}
.tab{padding:8px 16px;border-radius:8px;border:1px solid var(--border);background:var(--s1);
  color:var(--muted);font-size:13px;font-weight:500;cursor:pointer;transition:all .2s;
  display:flex;align-items:center;gap:8px;font-family:var(--font)}
.tab:hover{border-color:var(--accent);color:var(--accent)}
.tab.on{background:rgba(0,180,252,.1);border-color:var(--accent);color:var(--accent)}
.tab .dot{width:6px;height:6px;border-radius:50%;background:var(--muted)}
.tab .dot.on{background:var(--green);box-shadow:0 0 6px var(--green)}
.tab .badge-testnet{font-size:9px;background:rgba(255,165,2,.15);color:var(--amber);
  border:1px solid rgba(255,165,2,.3);padding:1px 6px;border-radius:4px;font-family:var(--mono)}

.panel{display:none}
.panel.on{display:flex;flex-direction:column;gap:14px}

/* Stats */
.stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
.st{background:var(--s1);border:1px solid var(--border);border-radius:10px;padding:14px 16px;position:relative;overflow:hidden}
.st::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent);opacity:.4}
.st.g::after{background:var(--green)}.st.r::after{background:var(--red)}.st.a::after{background:var(--amber)}
.st-l{font-size:9px;color:var(--muted);letter-spacing:.1em;margin-bottom:8px;font-family:var(--mono)}
.st-v{font-family:var(--mono);font-size:20px;font-weight:700;line-height:1}
.st-v.g{color:var(--green)}.st-v.r{color:var(--red)}.st-v.b{color:var(--accent)}.st-v.a{color:var(--amber)}
.st-s{font-size:11px;color:var(--muted);margin-top:5px;font-family:var(--mono)}

.mid{display:grid;grid-template-columns:1fr 300px;gap:14px}
.card{background:var(--s1);border:1px solid var(--border);border-radius:10px;padding:16px}
.ch{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.ct{font-family:var(--mono);font-size:9px;letter-spacing:.12em;color:var(--muted)}
.cw{position:relative;height:175px}

/* Posição */
.pos-e{text-align:center;padding:20px;color:var(--muted);font-size:12px;font-family:var(--mono)}
.pos-h{display:flex;align-items:center;justify-content:space-between;
  padding:10px 12px;background:rgba(0,245,160,.06);border-radius:7px;margin-bottom:10px}
.pos-sym{font-family:var(--mono);font-size:16px;font-weight:700;color:var(--green)}
.pos-pnl{font-family:var(--mono);font-size:13px;font-weight:700}
.pr{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border)}
.pr:last-of-type{border:none}
.pk{font-size:11px;color:var(--muted);font-family:var(--mono)}
.pv{font-size:11px;font-weight:600;font-family:var(--mono)}
.slbar{height:4px;border-radius:2px;background:var(--s3);margin-top:10px;overflow:hidden}
.slf{height:100%;border-radius:2px;background:linear-gradient(90deg,var(--green),var(--amber),var(--red));transition:width .5s}

/* Ops */
.ops-c{background:var(--s1);border:1px solid var(--border);border-radius:10px;padding:16px}
.op-tabs{display:flex;gap:5px;margin-bottom:12px}
.ot{font-family:var(--mono);font-size:9px;padding:3px 10px;border-radius:5px;
  border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer}
.ot.on{border-color:var(--accent);color:var(--accent);background:rgba(0,180,252,.08)}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:10px;white-space:nowrap}
th{color:var(--muted);font-size:8px;letter-spacing:.1em;padding:5px 9px;text-align:left;border-bottom:1px solid var(--border)}
td{padding:7px 9px;border-bottom:1px solid rgba(255,255,255,.04)}
tr:last-child td{border:none}tr:hover td{background:var(--s2)}
.bk{font-size:8px;padding:2px 6px;border-radius:3px;font-weight:700}
.bb{background:rgba(0,245,160,.12);color:var(--green)}
.bs{background:rgba(255,71,87,.12);color:var(--red)}
.bsym{background:rgba(0,180,252,.1);color:var(--accent);border:1px solid rgba(0,180,252,.2)}
.btp{background:rgba(0,245,160,.1);color:var(--green)}
.bsl{background:rgba(255,71,87,.1);color:var(--red)}
.bia{background:rgba(166,108,255,.1);color:var(--purple)}
.bfb{background:rgba(255,165,2,.1);color:var(--amber)}
.pp{color:var(--green);font-weight:700}.pn{color:var(--red);font-weight:700}
.os{display:flex;gap:20px;margin-top:10px;padding-top:8px;border-top:1px solid var(--border)}
.osi{font-family:var(--mono);font-size:10px;color:var(--muted)}

/* Perf por par */
.pg{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin-top:12px}
.pb{background:var(--s2);border:1px solid var(--border);border-radius:7px;padding:9px 11px}
.pbn{font-family:var(--mono);font-size:10px;font-weight:700;color:var(--accent);margin-bottom:5px}
.pbr{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;margin-bottom:2px}
.pbk{color:var(--muted)}.pbv{color:var(--text)}

.bot{display:grid;grid-template-columns:1fr 1fr;gap:14px}

/* Scanner */
.sr{display:grid;grid-template-columns:75px 1fr 65px 65px 60px;gap:7px;align-items:center;padding:7px 0;border-bottom:1px solid var(--border)}
.sr:last-child{border:none}
.ss{font-family:var(--mono);font-size:11px;font-weight:600}
.sb-w{background:var(--s3);border-radius:2px;height:3px;overflow:hidden}
.sb{height:100%;border-radius:2px;background:var(--accent);transition:width .5s}
.sb.best{background:var(--green)}
.sn{font-family:var(--mono);font-size:10px;text-align:right}

/* Log */
.lw{height:190px;overflow-y:auto;font-family:var(--mono);font-size:9px;display:flex;flex-direction:column;gap:2px}
.ll{line-height:1.7;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ll.buy{color:var(--green)}.ll.sell{color:var(--red)}.ll.warn{color:var(--amber)}
.ll.err{color:var(--red);opacity:.7}.ll.ia{color:var(--accent)}.ll.scan{color:var(--purple)}

/* Notificações */
.notif-panel{background:var(--s1);border:1px solid var(--border);border-radius:10px;padding:16px}
.notif-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
.notif-item{background:var(--s2);border:1px solid var(--border);border-radius:8px;padding:12px;
  display:flex;align-items:center;justify-content:space-between}
.notif-label{font-size:12px;color:var(--text);font-family:var(--mono)}
.notif-desc{font-size:10px;color:var(--muted);margin-top:2px}
.toggle{position:relative;width:38px;height:20px;flex-shrink:0}
.toggle input{opacity:0;width:0;height:0;position:absolute}
.toggle-track{position:absolute;inset:0;background:var(--s3);border-radius:10px;
  border:1px solid var(--border);cursor:pointer;transition:background .2s}
.toggle input:checked + .toggle-track{background:var(--accent);border-color:var(--accent)}
.toggle-thumb{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
  background:#fff;transition:transform .2s;pointer-events:none}
.toggle input:checked ~ .toggle-thumb{transform:translateX(18px)}
.save-btn{margin-top:14px;padding:8px 20px;background:var(--accent);color:var(--bg);
  border:none;border-radius:7px;font-family:var(--mono);font-size:12px;font-weight:700;cursor:pointer}
.save-btn:hover{opacity:.85}
.save-msg{font-family:var(--mono);font-size:11px;color:var(--green);margin-left:12px;display:none}

/* Controles do bot */
.ctrl-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.ctrl-btn{padding:7px 16px;border-radius:7px;border:1px solid var(--border);background:var(--s2);
  color:var(--text);font-family:var(--mono);font-size:11px;cursor:pointer;transition:all .2s}
.ctrl-btn:hover{border-color:var(--accent);color:var(--accent)}
.ctrl-btn.danger{border-color:rgba(255,71,87,.4);color:var(--red)}
.ctrl-btn.danger:hover{background:rgba(255,71,87,.1)}

::-webkit-scrollbar{width:3px;height:3px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>

<div class="hdr">
  <div class="brand" id="brand">⬡ SCALPBOT</div>
  <div class="hdr-r">
    <div class="live" id="live-dot"></div>
    <div class="chip" id="bot-st">verificando...</div>
    <div class="chip" id="clk">--:--:--</div>
  </div>
</div>

<div class="ticker">
  <div class="ti" id="tick-BTCUSDT"><div class="ti-s">BTC</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
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
const THEMES=[
  {accent:'#00b4fc',accent2:'#00f5a0',bg:'#070b14',s1:'#0d1526',s2:'#111d35',s3:'#172347'},
  {accent:'#ff6b35',accent2:'#ffd700',bg:'#0f0800',s1:'#1a1000',s2:'#261800',s3:'#332100'},
  {accent:'#a855f7',accent2:'#ec4899',bg:'#09050f',s1:'#140d1f',s2:'#1c1230',s3:'#26183d'},
  {accent:'#00e87a',accent2:'#84cc16',bg:'#050f08',s1:'#0a1f10',s2:'#0f2e18',s3:'#153d20'},
  {accent:'#ff4757',accent2:'#ff9f43',bg:'#0f0505',s1:'#1f0a0a',s2:'#2e0f0f',s3:'#3d1515'},
];
let charts={}, bots=[], cur=0;

function applyTheme(idx){
  const t=THEMES[idx%THEMES.length];
  const r=document.documentElement.style;
  r.setProperty('--accent',t.accent);r.setProperty('--accent2',t.accent2);
  r.setProperty('--bg',t.bg);r.setProperty('--s1',t.s1);
  r.setProperty('--s2',t.s2);r.setProperty('--s3',t.s3);
  document.body.style.background=t.bg;
}

function fmt(n,d=2){return Number(n).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}

function rb(r){
  if(!r)return'';
  if(r.includes('TAKE_PROFIT')||r.includes('take_profit'))return'<span class="bk btp">TP</span>';
  if(r.includes('STOP_LOSS')||r.includes('stop_loss'))return'<span class="bk bsl">SL</span>';
  if(r.includes('[FB]'))return'<span class="bk bfb">FB</span>';
  return'<span class="bk bia">IA</span>';
}

const NOTIF_TYPES={
  inicio:      {label:'Inicialização',   desc:'Bot iniciado/encerrado'},
  compra:      {label:'Compra',          desc:'Ordem de compra executada'},
  venda:       {label:'Venda',           desc:'Ordem de venda executada'},
  stop_loss:   {label:'Stop-loss',       desc:'Stop-loss atingido'},
  take_profit: {label:'Take-profit',     desc:'Take-profit atingido'},
  par_troca:   {label:'Troca de par',    desc:'Scanner trocou o par ativo'},
  ia_erro:     {label:'Erro IA',         desc:'Falha na API Anthropic'},
  resumo:      {label:'Resumo',          desc:'Resumo ao encerrar'},
};

function buildNotifPanel(b, idx){
  const entries = Object.entries(NOTIF_TYPES).map(([key,info])=>{
    const checked = b.notif_cfg?.[key]!==false;
    return `<div class="notif-item">
      <div>
        <div class="notif-label">${info.label}</div>
        <div class="notif-desc">${info.desc}</div>
      </div>
      <label class="toggle">
        <input type="checkbox" id="notif-${idx}-${key}" ${checked?'checked':''} onchange="saveNotif(${idx})">
        <div class="toggle-track"></div>
        <div class="toggle-thumb"></div>
      </label>
    </div>`;
  }).join('');
  return `<div class="notif-panel">
    <div class="ch">
      <div class="ct">NOTIFICAÇÕES TELEGRAM</div>
      <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">${b.tg_token?'✓ Token configurado':'✗ Sem token'}</div>
    </div>
    <div class="notif-grid">${entries}</div>
    <div style="display:flex;align-items:center;margin-top:14px">
      <button class="save-btn" onclick="saveNotif(${idx})">Salvar configurações</button>
      <span class="save-msg" id="save-msg-${idx}">✓ Salvo!</span>
    </div>
  </div>`;
}

async function saveNotif(idx){
  const b=bots[idx];if(!b)return;
  const cfg={};
  Object.keys(NOTIF_TYPES).forEach(key=>{
    const el=document.getElementById(`notif-${idx}-${key}`);
    if(el) cfg[key]=el.checked;
  });
  await fetch(`/api/notif/${idx}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
  const msg=document.getElementById(`save-msg-${idx}`);
  if(msg){msg.style.display='inline';setTimeout(()=>msg.style.display='none',2000);}
}

function buildPanel(b, idx){
  return `<div class="panel" id="panel-${idx}">
    <div class="stats">
      <div class="st ${b.pnl>0?'g':b.pnl<0?'r':''}">
        <div class="st-l">PNL TOTAL</div>
        <div class="st-v" id="v-pnl-${idx}">$0.0000</div>
        <div class="st-s" id="v-pnl-s-${idx}">—</div>
      </div>
      <div class="st g"><div class="st-l">MELHOR OP</div><div class="st-v g" id="v-best-${idx}">—</div><div class="st-s" id="v-best-s-${idx}">—</div></div>
      <div class="st r"><div class="st-l">PIOR OP</div><div class="st-v r" id="v-worst-${idx}">—</div><div class="st-s" id="v-worst-s-${idx}">—</div></div>
      <div class="st"><div class="st-l">WIN RATE</div><div class="st-v" id="v-wr-${idx}">—</div><div class="st-s" id="v-wr-s-${idx}">0W/0L</div></div>
      <div class="st"><div class="st-l">SALDO USDT</div><div class="st-v b" id="v-usdt-${idx}">—</div><div class="st-s" id="v-ops-${idx}">0 ops</div></div>
      <div class="st"><div class="st-l">POSIÇÃO</div><div class="st-v" id="v-pos-${idx}">NENHUMA</div><div class="st-s" id="v-pos-s-${idx}">—</div></div>
    </div>
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
      <div class="ch">
        <div class="ct">OPERAÇÕES</div>
        <div class="op-tabs">
          <button class="ot on" onclick="fops(${idx},'all',this)">TODAS</button>
          <button class="ot" onclick="fops(${idx},'win',this)">GANHOS</button>
          <button class="ot" onclick="fops(${idx},'loss',this)">PERDAS</button>
        </div>
      </div>
      <div class="tw"><table>
        <thead><tr><th>#</th><th>PAR</th><th>COMPRA</th><th>VENDA</th><th>QTD</th><th>CAPITAL</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>DATA/HORA</th></tr></thead>
        <tbody id="ops-${idx}"><tr><td colspan="10" style="text-align:center;color:var(--muted);padding:18px">Nenhuma operação ainda</td></tr></tbody>
      </table></div>
      <div class="os" id="os-${idx}"></div>
    </div>
    <div class="card">
      <div class="ct">DESEMPENHO POR PAR</div>
      <div class="pg" id="pg-${idx}"></div>
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
    ${buildNotifPanelHTML(idx)}
  </div>`;
}

function buildNotifPanelHTML(idx){
  const entries=Object.entries(NOTIF_TYPES).map(([key,info])=>`
    <div class="notif-item">
      <div><div class="notif-label">${info.label}</div><div class="notif-desc">${info.desc}</div></div>
      <label class="toggle">
        <input type="checkbox" id="notif-${idx}-${key}" checked onchange="saveNotif(${idx})">
        <div class="toggle-track"></div><div class="toggle-thumb"></div>
      </label>
    </div>`).join('');
  return `<div class="notif-panel">
    <div class="ch"><div class="ct">NOTIFICAÇÕES TELEGRAM</div><div class="ct" id="tg-st-${idx}" style="color:var(--muted)">—</div></div>
    <div class="notif-grid">${entries}</div>
    <div style="display:flex;align-items:center;margin-top:14px">
      <button class="save-btn" onclick="saveNotif(${idx})">Salvar</button>
      <span class="save-msg" id="sv-${idx}">✓ Salvo!</span>
    </div>
  </div>`;
}

function fops(idx,f,btn){
  document.querySelectorAll(`#panel-${idx} .ot`).forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  const tr=bots[idx]?.trades||[];
  renderOps(idx,f==='all'?tr:tr.filter(t=>f==='win'?t.pnl>=0:t.pnl<0));
}

function renderOps(idx,trades){
  const tb=document.getElementById(`ops-${idx}`);if(!tb)return;
  if(!trades||!trades.length){
    tb.innerHTML='<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:18px">Nenhuma operação ainda</td></tr>';return;
  }
  tb.innerHTML=[...trades].reverse().map((t,i)=>{
    const pct=t.usdt_used>0?(t.pnl/t.usdt_used*100).toFixed(2)+'%':'—';
    const c=t.pnl>=0?'pp':'pn';
    return`<tr>
      <td style="color:var(--muted)">${trades.length-i}</td>
      <td><span class="bk bsym">${(t.symbol||'BTC').replace('USDT','')}</span></td>
      <td>$${fmt(t.entry,4)}</td>
      <td>${t.exit>0?'$'+fmt(t.exit,4):'<span style="color:var(--amber)">aberta</span>'}</td>
      <td style="color:var(--muted)">${t.qty||'—'}</td>
      <td style="color:var(--muted)">$${fmt(t.usdt_used||0)}</td>
      <td class="${c}">${t.pnl>=0?'+':''}$${Number(t.pnl).toFixed(4)}</td>
      <td class="${c}">${pct}</td>
      <td>${rb(t.reason)}</td>
      <td style="color:var(--muted);font-size:8px">${(t.close||'').substring(0,19)}</td>
    </tr>`;
  }).join('');
}

function initChart(id){
  const ctx=document.getElementById(id);if(!ctx)return;
  charts[id]=new Chart(ctx.getContext('2d'),{
    type:'line',
    data:{labels:[],datasets:[
      {data:[],borderColor:'#00f5a0',backgroundColor:'rgba(0,245,160,.05)',borderWidth:1.5,pointRadius:2,fill:true,tension:.4,label:'Acum.'},
      {data:[],borderColor:'#00b4fc',backgroundColor:'transparent',borderWidth:1,pointRadius:2,fill:false,tension:0,label:'Por op'},
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:true,labels:{color:'#6b7fa8',font:{family:'JetBrains Mono',size:8},boxWidth:8}}},
      scales:{
        x:{ticks:{color:'#6b7fa8',font:{family:'JetBrains Mono',size:7}},grid:{color:'rgba(255,255,255,.04)'}},
        y:{ticks:{color:'#6b7fa8',font:{family:'JetBrains Mono',size:7},callback:v=>'$'+v.toFixed(3)},grid:{color:'rgba(255,255,255,.04)'}}
      }
    }
  });
}

function updatePanel(d,idx){
  bots[idx]=d;
  const T=THEMES[idx%THEMES.length];

  // Par ativo
  const pe=document.getElementById(`v-pair-${idx}`);if(pe)pe.textContent=d.active_symbol||'—';

  // Ticker destaque
  document.querySelectorAll('.ti').forEach(e=>e.classList.remove('hi'));
  if(d.active_symbol){const te=document.getElementById('tick-'+d.active_symbol);if(te)te.classList.add('hi')}

  // PnL
  const pnl=d.pnl||0;
  const pe2=document.getElementById(`v-pnl-${idx}`);
  if(pe2){pe2.textContent=(pnl>=0?'+':'')+'$'+pnl.toFixed(4);pe2.className='st-v '+(pnl>0?'g':pnl<0?'r':'');}

  // WR
  const w=d.wins||0,l=d.losses||0,tot=w+l;
  const wr=tot>0?Math.round(w/tot*100):null;
  const wre=document.getElementById(`v-wr-${idx}`);
  if(wre){wre.textContent=wr!==null?wr+'%':'—';wre.className='st-v '+(wr>=55?'g':wr!==null&&wr<45?'r':'a');}
  const wrs=document.getElementById(`v-wr-s-${idx}`);if(wrs)wrs.textContent=w+'W/'+l+'L';

  const ue=document.getElementById(`v-usdt-${idx}`);if(ue)ue.textContent=d.usdt?'$'+fmt(d.usdt):'—';
  const oe=document.getElementById(`v-ops-${idx}`);if(oe)oe.textContent=(d.trades||[]).length+' ops';

  // Melhor/pior
  const tr=d.trades||[];
  const tw=tr.filter(t=>t.pnl>0),tl=tr.filter(t=>t.pnl<0);
  const best=tw.length?tw.reduce((a,b)=>b.pnl>a.pnl?b:a):null;
  const worst=tl.length?tl.reduce((a,b)=>b.pnl<a.pnl?b:a):null;
  const bv=document.getElementById(`v-best-${idx}`);if(bv)bv.textContent=best?'+$'+best.pnl.toFixed(4):'—';
  const bs=document.getElementById(`v-best-s-${idx}`);if(bs)bs.textContent=best?(best.symbol||'').replace('USDT',''):'—';
  const wv=document.getElementById(`v-worst-${idx}`);if(wv)wv.textContent=worst?'$'+worst.pnl.toFixed(4):'—';
  const ws=document.getElementById(`v-worst-s-${idx}`);if(ws)ws.textContent=worst?(worst.symbol||'').replace('USDT',''):'—';

  // Posição
  const pe3=document.getElementById(`v-pos-${idx}`);
  const pd=document.getElementById(`pos-${idx}`);
  if(d.position){
    const pct=d.price?((d.price-d.position.entry_price)/d.position.entry_price*100):0;
    const pc=pct>=0?'g':'r';
    const prog=Math.min(100,Math.max(0,(pct+(d.stop_loss||.005)*100)/((d.take_profit||.01)+(d.stop_loss||.005))*100));
    if(pe3){pe3.textContent=d.position.symbol||'ABERTA';pe3.className='st-v g';}
    const ps=document.getElementById(`v-pos-s-${idx}`);if(ps)ps.textContent='entrada $'+fmt(d.position.entry_price,4);
    if(pd)pd.innerHTML=`<div>
      <div class="pos-h"><div class="pos-sym">${d.position.symbol||'—'}</div><div class="pos-pnl ${pc}">${pct>=0?'+':''}${pct.toFixed(2)}%</div></div>
      <div class="pr"><span class="pk">Entrada</span><span class="pv">$${fmt(d.position.entry_price,4)}</span></div>
      <div class="pr"><span class="pk">Preço atual</span><span class="pv" style="color:var(--accent)">$${d.price?fmt(d.price,4):'—'}</span></div>
      <div class="pr"><span class="pk">Quantidade</span><span class="pv">${d.position.qty||'—'}</span></div>
      <div class="pr"><span class="pk">Capital</span><span class="pv">$${fmt(d.position.usdt_used||0)}</span></div>
      <div class="pr"><span class="pk">Stop-loss</span><span class="pv" style="color:var(--red)">$${fmt(d.position.entry_price*(1-(d.stop_loss||.005)),4)}</span></div>
      <div class="pr"><span class="pk">Take-profit</span><span class="pv" style="color:var(--green)">$${fmt(d.position.entry_price*(1+(d.take_profit||.01)),4)}</span></div>
      <div class="slbar"><div class="slf" style="width:${prog}%"></div></div>
    </div>`;
  }else{
    if(pe3){pe3.textContent='NENHUMA';pe3.className='st-v';}
    const ps=document.getElementById(`v-pos-s-${idx}`);if(ps)ps.textContent='—';
    if(pd)pd.innerHTML='<div class="pos-e">Aguardando sinal...</div>';
  }

  // Operações
  renderOps(idx,tr);
  const os=document.getElementById(`os-${idx}`);
  if(os&&tr.length>0){
    const tp=tr.reduce((a,t)=>a+t.pnl,0);
    const aw=tw.length?tw.reduce((a,t)=>a+t.pnl,0)/tw.length:0;
    const al=tl.length?tl.reduce((a,t)=>a+t.pnl,0)/tl.length:0;
    os.innerHTML=`
      <div class="osi">Total: <b class="${tp>=0?'pp':'pn'}">${tp>=0?'+':''}$${tp.toFixed(4)}</b></div>
      <div class="osi">Ganho médio: <b class="pp">+$${aw.toFixed(4)}</b></div>
      <div class="osi">Perda média: <b class="pn">$${al.toFixed(4)}</b></div>
      <div class="osi">Ops: <b style="color:var(--accent)">${tr.length}</b></div>
      <div class="osi">WR: <b class="${wr>=55?'pp':wr!==null&&wr<45?'pn':''}">${wr!==null?wr+'%':'—'}</b></div>`;
  }

  // Perf por par
  const pge=document.getElementById(`pg-${idx}`);
  if(pge){
    const pm={};
    tr.forEach(t=>{
      const s=(t.symbol||'BTCUSDT').replace('USDT','');
      if(!pm[s])pm[s]={ops:0,wins:0,pnl:0,best:-Infinity,worst:Infinity};
      pm[s].ops++;pm[s].pnl+=t.pnl;if(t.pnl>=0)pm[s].wins++;
      if(t.pnl>pm[s].best)pm[s].best=t.pnl;if(t.pnl<pm[s].worst)pm[s].worst=t.pnl;
    });
    pge.innerHTML=['BTC','ETH','BNB','SOL','XRP'].map(p=>{
      const s=pm[p];const wr2=s?Math.round(s.wins/s.ops*100):null;
      return`<div class="pb"><div class="pbn">${p}</div>${s?`
        <div class="pbr"><span class="pbk">Ops</span><span class="pbv">${s.ops}</span></div>
        <div class="pbr"><span class="pbk">WR</span><span class="pbv" style="color:${wr2>=55?'var(--green)':wr2<45?'var(--red)':'var(--amber)'}">${wr2}%</span></div>
        <div class="pbr"><span class="pbk">PnL</span><span class="pbv" style="color:${s.pnl>=0?'var(--green)':'var(--red)'}">${s.pnl>=0?'+':''}$${s.pnl.toFixed(3)}</span></div>
        <div class="pbr"><span class="pbk">Melhor</span><span class="pbv pp">+$${s.best===Infinity?'0.000':s.best.toFixed(3)}</span></div>
        <div class="pbr"><span class="pbk">Pior</span><span class="pbv pn">$${s.worst===-Infinity?'0.000':s.worst.toFixed(3)}</span></div>`
        :'<div class="pbr"><span class="pbk" style="font-size:8px">sem ops</span></div>'}</div>`;
    }).join('');
  }

  // Gráfico
  const cid=`ch-${idx}`;
  if(charts[cid]&&tr.length>0){
    let acc=0;const lb=[],vl=[],vp=[];
    tr.forEach((t,i)=>{acc+=t.pnl;lb.push('#'+(i+1));vl.push(parseFloat(acc.toFixed(4)));vp.push(parseFloat(t.pnl.toFixed(4)));});
    charts[cid].data.labels=lb;
    charts[cid].data.datasets[0].data=vl;
    charts[cid].data.datasets[1].data=vp;
    const T2=THEMES[idx%THEMES.length];
    charts[cid].data.datasets[0].borderColor=acc>=0?T2.accent2:T2.accent;
    charts[cid].data.datasets[0].backgroundColor=acc>=0?'rgba(0,245,160,.05)':'rgba(255,71,87,.05)';
    charts[cid].data.datasets[1].borderColor=T2.accent;
    charts[cid].update('none');
  }

  // Scanner
  const sce=document.getElementById(`sc-${idx}`);
  if(sce&&d.scanner&&d.scanner.length>0){
    const ts=document.getElementById(`sc-ts-${idx}`);if(ts)ts.textContent=d.scan_time||'';
    const ms=Math.max(...d.scanner.map(s=>s.score));
    sce.innerHTML=d.scanner.map(s=>{
      const ib=s.score===ms,ia=s.symbol===d.active_symbol;
      const pc=s.change>=0?'up':'dn';
      return`<div class="sr">
        <div class="ss" style="color:${ib?'var(--green)':'var(--text)'}">${ia?'★ ':''}${s.symbol.replace('USDT','')}</div>
        <div><div class="sb-w"><div class="sb ${ib?'best':''}" style="width:${s.score}%"></div></div></div>
        <div class="sn ${pc}">${s.change>=0?'+':''}${s.change}%</div>
        <div class="sn" style="color:var(--muted)">${s.volume}M</div>
        <div class="sn" style="color:var(--muted)">${s.score.toFixed(1)}</div>
      </div>`;
    }).join('');
  }

  // Log
  const lwe=document.getElementById(`lw-${idx}`);
  if(lwe&&d.logs){
    const lce=document.getElementById(`lc-${idx}`);if(lce)lce.textContent=d.logs.length+' linhas';
    lwe.innerHTML=d.logs.slice(-80).reverse().map(l=>{
      let c='ll';
      if(l.includes('Comprado')||l.includes('📈'))c+=' buy';
      else if(l.includes('Fechado')||l.includes('✅')||l.includes('❌'))c+=' sell';
      else if(l.includes('Scanner')||l.includes('★'))c+=' scan';
      else if(l.includes('IA ')||l.includes('🤖'))c+=' ia';
      else if(l.includes('WARNING')||l.includes('⚠️')||l.includes('ECON')||l.includes('FB'))c+=' warn';
      else if(l.includes('ERROR')||l.includes('Erro'))c+=' err';
      return`<div class="${c}">${l}</div>`;
    }).join('');
  }

  // Notificações estado
  if(d.notif_cfg){
    Object.keys(NOTIF_TYPES).forEach(key=>{
      const el=document.getElementById(`notif-${idx}-${key}`);
      if(el) el.checked=d.notif_cfg[key]!==false;
    });
  }
  const tgs=document.getElementById(`tg-st-${idx}`);
  if(tgs)tgs.textContent=d.tg_token?'✓ Telegram configurado':'✗ Sem token Telegram';
}

async function refresh(){
  try{
    const r=await fetch('/api/bots');
    const data=await r.json();
    const tabsEl=document.getElementById('tabs');
    const panelsEl=document.getElementById('panels');

    if(tabsEl.children.length===0&&data.length>0){
      data.forEach((b,i)=>{
        const T=THEMES[i%THEMES.length];
        const tab=document.createElement('div');
        tab.className='tab'+(i===0?' on':'');
        tab.id=`tab-${i}`;
        tab.innerHTML=`<div class="dot ${b.bot_running?'on':''}"></div>
          ${b.emoji||'🤖'} ${b.name}
          ${b.testnet?'<span class="badge-testnet">SIM</span>':''}`;
        tab.style.setProperty('--accent',T.accent);
        tab.onclick=()=>{
          document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
          document.querySelectorAll('.panel').forEach(p=>p.classList.remove('on'));
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
      if(tab){const d=tab.querySelector('.dot');if(d)d.className='dot '+(b.bot_running?'on':'');}
      bots[i]=b;
      if(document.getElementById(`panel-${i}`)) updatePanel(b,i);
    });

    const anyOn=data.some(b=>b.bot_running);
    const ld=document.getElementById('live-dot');
    const st=document.getElementById('bot-st');
    if(ld)ld.className='live '+(anyOn?'on':'');
    if(st)st.textContent=anyOn?data.filter(b=>b.bot_running).length+' bot(s) ativo(s)':'INATIVO';

  }catch(e){
    const st=document.getElementById('bot-st');if(st)st.textContent='ERRO DE CONEXÃO';
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
      const fp=p>1000?'$'+p.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}):p>10?'$'+p.toFixed(2):'$'+p.toFixed(4);
      el.querySelector('.ti-p').textContent=fp;
      const ce=el.querySelector('.ti-c');
      ce.textContent=(c>=0?'+':'')+c.toFixed(2)+'%';
      ce.className='ti-c '+(c>=0?'up':'dn');
    }catch(e){}
  }
}

setInterval(()=>{const e=document.getElementById('clk');if(e)e.textContent=new Date().toLocaleTimeString('pt-BR');},1000);
refresh();refreshTicker();
setInterval(refresh,5000);setInterval(refreshTicker,10000);
</script>
</body>
</html>'''


# ── Parser do log ─────────────────────────────────────────────────────────────

def parse_bot_log(log_file: str, bot_name: str, bot_idx: int = 0) -> dict:
    result = {
        "name": bot_name, "emoji": "🤖", "bot_running": False,
        "testnet": False, "tg_token": False,
        "active_symbol": None, "price": None, "rsi": None,
        "macd_signal": None, "bb_pct": None, "usdt": None,
        "pnl": 0.0, "wins": 0, "losses": 0, "stop_loss": 0.005, "take_profit": 0.010,
        "position": None, "trades": [], "scanner": [],
        "scanner_scores": {}, "scan_time": None, "logs": [],
        "notif_cfg": {k: True for k in ["inicio","compra","venda","stop_loss","take_profit","par_troca","ia_erro","resumo"]},
    }

    # Lê config do .env para este bot
    prefix = f"BOT_{bot_idx+1}"
    result["emoji"]       = os.getenv(f"{prefix}_EMOJI", "🤖")
    result["testnet"]     = os.getenv(f"{prefix}_TESTNET","false").lower()=="true"
    result["tg_token"]    = bool(os.getenv(f"{prefix}_TELEGRAM_TOKEN",""))
    result["stop_loss"]   = float(os.getenv(f"{prefix}_STOP_LOSS","0.005"))
    result["take_profit"] = float(os.getenv(f"{prefix}_TAKE_PROFIT","0.010"))

    for key in result["notif_cfg"]:
        env_key = f"{prefix}_NOTIFY_{key.upper()}"
        val = os.getenv(env_key)
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

    re_price = re.compile(r'\[(\w+)\] \$([\d,.]+) \| RSI:([\d.]+) \| Tend:(\w+) \| MACD:(\w+) \| BB:([-\d.]+)% \| USDT:([\d.]+)')
    re_wl    = re.compile(r'W:(\d+) L:(\d+)')
    re_pnl   = re.compile(r'Total: \$([-+]?[\d.]+)')
    re_close = re.compile(r'Fechado (\w+) \(([^)]+)\).*PnL: \$([-+]?[\d.]+)')
    re_open  = re.compile(r'Comprado ([\d.]+) (\w+) @ \$([\d,.]+) \(\$([\d,.]+) USDT\)')
    re_scan  = re.compile(r'[★ ] (\w+)\s+\| Score:\s*([\d.]+) \| Vol:\s*([\d.]+)M \| Var:([-+\d.]+)% \| Volat:([\d.]+)%')
    re_best  = re.compile(r'Melhor: (\w+)|Melhor par selecionado: (\w+)')
    re_scan_t = re.compile(r'── Scanner')

    current_entry = current_sym = current_qty = current_usdt = None
    scanner_tmp = []; scan_active = False

    for line in lines:
        m = re_price.search(line)
        if m:
            result["active_symbol"] = m.group(1); result["price"] = float(m.group(2).replace(",",""))
            result["rsi"] = float(m.group(3)); result["macd_signal"] = m.group(5)
            result["bb_pct"] = float(m.group(6)); result["usdt"] = float(m.group(7))

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
                    "volume":m.group(3),"change":float(m.group(4)),"volatility":m.group(5)})
                result["scanner_scores"][m.group(1)]=float(m.group(2))

        m = re_best.search(line)
        if m:
            result["active_symbol"] = m.group(1) or m.group(2)
            if scanner_tmp: result["scanner"] = sorted(scanner_tmp,key=lambda x:x["score"],reverse=True)
            scan_active=False

        m = re_open.search(line)
        if m:
            current_qty=m.group(1); current_sym=m.group(2)
            current_entry=float(m.group(3).replace(",","")); current_usdt=float(m.group(4).replace(",",""))

        m = re_close.search(line)
        if m:
            result["trades"].append({
                "symbol":m.group(1),"side":"BUY","entry":current_entry or 0,
                "exit":0,"pnl":float(m.group(3)),"qty":current_qty or "—",
                "usdt_used":current_usdt or 0,"close":line[:19],"reason":m.group(2),
            })
            current_entry=current_sym=current_qty=current_usdt=None

    result["total_trades"] = len(result["trades"])
    if current_entry and current_sym:
        result["position"] = {"symbol":current_sym,"entry_price":current_entry,
                               "qty":current_qty or "—","usdt_used":current_usdt or 0}
    if result["trades"] and result["pnl"]==0.0:
        result["pnl"]=round(sum(t["pnl"] for t in result["trades"]),4)
        result["wins"]=sum(1 for t in result["trades"] if t["pnl"]>=0)
        result["losses"]=sum(1 for t in result["trades"] if t["pnl"]<0)
    return result


def get_all_bots():
    bots = []
    bot_count = int(os.getenv("BOT_COUNT","1"))
    for i in range(bot_count):
        prefix = f"BOT_{i+1}"
        name   = os.getenv(f"{prefix}_NAME", f"Bot {i+1}")
        log_file = os.path.join(BASE, f"bot_{name.lower().replace(' ','_')}.log")
        if not os.path.exists(log_file):
            log_file = os.path.join(BASE, "bot.log")
        bots.append(parse_bot_log(log_file, name, i))
    if not bots:
        bots.append(parse_bot_log(os.path.join(BASE,"bot.log"),"Principal",0))
    return bots


@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/bots")
def api_bots():
    return jsonify(get_all_bots())

@app.route("/api/status")
def api_status():
    bots = get_all_bots()
    return jsonify(bots[0] if bots else {})

@app.route("/api/notif/<int:idx>", methods=["POST"])
def save_notif(idx):
    """Salva configuração de notificações de um bot no .env"""
    cfg = request.get_json()
    prefix = f"BOT_{idx+1}"
    for key, val in cfg.items():
        env_key = f"{prefix}_NOTIFY_{key.upper()}"
        set_key(ENV, env_key, "true" if val else "false")
    load_dotenv(dotenv_path=ENV, override=True)
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("="*50)
    print(" ScalpBot Dashboard Multi-Conta")
    print(" Acesse: http://localhost:5000")
    print("="*50)
    app.run(host="0.0.0.0", port=5000, debug=False)
