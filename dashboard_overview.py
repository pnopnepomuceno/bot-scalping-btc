"""
ScalpBot — Dashboard Visão Geral v2.0 (porta 5004)
Resumo limpo e objetivo para monitoramento rápido.
"""
from flask import Flask, jsonify, render_template_string
import os, re, glob
from datetime import datetime
from dotenv import load_dotenv

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE, '.env'))

HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>ScalpBot — Visão Geral</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#060c1a;--s1:#0a1628;--s2:#0e1e36;--border:rgba(255,255,255,.07);
  --text:#e2eeff;--muted:#5a7299;--green:#4ade80;--red:#f87171;--amber:#fbbf24;
  --accent:#38bdf8;--purple:#c084fc;--r:12px;
  --font:'DM Sans',sans-serif;--mono:'Space Mono',monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;font-size:14px;padding-bottom:48px}

.hdr{display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:52px;
  background:rgba(10,22,40,.95);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100}
.brand{font-family:var(--mono);font-size:12px;font-weight:700;color:var(--accent);letter-spacing:.15em;
  display:flex;align-items:center;gap:8px}
.brand-sub{color:var(--muted);font-weight:400;font-size:10px;letter-spacing:.05em}
.hdr-r{display:flex;align-items:center;gap:12px}
.live{width:7px;height:7px;border-radius:50%;background:var(--muted)}
.live.on{background:var(--green);box-shadow:0 0 10px var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.ts{font-family:var(--mono);font-size:11px;color:var(--muted)}
.refresh-badge{font-size:10px;background:rgba(56,189,248,.08);color:var(--accent);
  border:1px solid rgba(56,189,248,.15);padding:3px 10px;border-radius:20px;font-family:var(--mono)}

main{max-width:1280px;margin:0 auto;padding:24px}

.section{margin-bottom:32px}
.sec-title{font-size:9px;font-weight:700;letter-spacing:.15em;color:var(--muted);
  text-transform:uppercase;display:flex;align-items:center;gap:10px;margin-bottom:16px}
.sec-title::after{content:'';flex:1;height:1px;background:var(--border)}

/* Resumo topo */
.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:32px}
@media(max-width:800px){.summary{grid-template-columns:repeat(2,1fr)}}
.sum-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);
  padding:20px;position:relative;overflow:hidden}
.sum-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.sum-card.green::before{background:var(--green)}.sum-card.blue::before{background:var(--accent)}
.sum-card.amber::before{background:var(--amber)}.sum-card.purple::before{background:var(--purple)}
.sum-label{font-size:9px;font-weight:700;letter-spacing:.12em;color:var(--muted);margin-bottom:10px;text-transform:uppercase}
.sum-val{font-family:var(--mono);font-size:26px;font-weight:700;line-height:1}
.sum-val.green{color:var(--green)}.sum-val.red{color:var(--red)}.sum-val.blue{color:var(--accent)}.sum-val.amber{color:var(--amber)}
.sum-sub{font-size:11px;color:var(--muted);margin-top:6px;font-family:var(--mono)}

/* Links dashboards */
.dash-links{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:32px}
.dash-link{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;
  border-radius:10px;background:var(--s1);border:1px solid var(--border);
  color:var(--text);text-decoration:none;font-size:12px;font-weight:500;
  transition:all .2s}
.dash-link:hover{border-color:var(--accent);color:var(--accent);background:rgba(56,189,248,.05)}
.dash-link .port{font-family:var(--mono);font-size:10px;color:var(--muted)}
.dash-link .dot{width:7px;height:7px;border-radius:50%}
.dash-link .dot.on{background:var(--green);box-shadow:0 0 6px var(--green)}
.dash-link .dot.off{background:var(--muted)}

/* Contas */
.accounts{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px;margin-bottom:32px}
.acc-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.acc-hdr{padding:14px 18px;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border)}
.acc-info{display:flex;align-items:center;gap:10px}
.acc-emoji{font-size:24px}
.acc-name{font-size:14px;font-weight:600}
.acc-exch{font-size:10px;color:var(--muted);margin-top:2px;font-family:var(--mono);
  display:flex;align-items:center;gap:6px}
.exch-badge{font-size:9px;font-weight:700;padding:2px 7px;border-radius:5px;font-family:var(--mono)}
.exch-badge.bnb{background:rgba(240,185,11,.12);color:#f0b90b;border:1px solid rgba(240,185,11,.2)}
.exch-badge.okx{background:rgba(192,132,252,.12);color:#c084fc;border:1px solid rgba(192,132,252,.2)}
.status-pill{font-size:9px;font-weight:700;padding:4px 10px;border-radius:20px;font-family:var(--mono)}
.status-pill.on{background:rgba(74,222,128,.1);color:var(--green);border:1px solid rgba(74,222,128,.2)}
.status-pill.off{background:rgba(248,113,113,.08);color:var(--red);border:1px solid rgba(248,113,113,.15)}

.acc-body{padding:14px 18px}
.bal-grid{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.bal-item{background:var(--s2);border:1px solid var(--border);border-radius:8px;
  padding:9px 12px;flex:1;min-width:90px}
.bal-coin{font-size:9px;font-weight:700;letter-spacing:.1em;color:var(--muted);margin-bottom:4px}
.bal-amount{font-family:var(--mono);font-size:13px;font-weight:700}
.bal-usd{font-size:10px;color:var(--muted);margin-top:2px;font-family:var(--mono)}

.acc-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:0;
  border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--s2)}
.acc-metric{padding:10px 12px;border-right:1px solid var(--border)}
.acc-metric:last-child{border:none}
.acc-metric-l{font-size:9px;color:var(--muted);letter-spacing:.08em;margin-bottom:4px}
.acc-metric-v{font-family:var(--mono);font-size:13px;font-weight:700}
.acc-metric-v.pos{color:var(--green)}.acc-metric-v.neg{color:var(--red)}.acc-metric-v.neu{color:var(--text)}

.pos-open{margin-top:10px;background:rgba(56,189,248,.06);border:1px solid rgba(56,189,248,.15);
  border-radius:8px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between}
.pos-sym{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--accent)}
.pos-entry{font-size:11px;color:var(--muted);font-family:var(--mono)}

/* Tabela de operações */
.ops-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.ops-hdr{padding:14px 18px;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border)}
.ops-title{font-size:13px;font-weight:600}
.ops-count{font-size:11px;color:var(--muted);font-family:var(--mono)}
.filters{display:flex;gap:4px}
.ftab{font-size:9px;font-weight:700;padding:4px 12px;border-radius:7px;
  border:1px solid var(--border);background:transparent;color:var(--muted);
  cursor:pointer;font-family:var(--mono);transition:all .15s;letter-spacing:.06em}
.ftab.on{background:rgba(56,189,248,.1);border-color:rgba(56,189,248,.3);color:var(--accent)}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;white-space:nowrap}
th{color:var(--muted);font-size:9px;letter-spacing:.1em;padding:10px 16px;text-align:left;
  border-bottom:1px solid var(--border);background:rgba(0,0,0,.15);font-weight:700}
td{padding:11px 16px;border-bottom:1px solid rgba(255,255,255,.03)}
tr:last-child td{border:none}
tr:hover td{background:rgba(255,255,255,.02)}
.status-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;
  border-radius:20px;font-size:9px;font-weight:700}
.sb-open{background:rgba(56,189,248,.1);color:var(--accent);border:1px solid rgba(56,189,248,.2)}
.sb-win{background:rgba(74,222,128,.1);color:var(--green);border:1px solid rgba(74,222,128,.2)}
.sb-loss{background:rgba(248,113,113,.08);color:var(--red);border:1px solid rgba(248,113,113,.15)}
.sb-tp{background:rgba(74,222,128,.06);color:var(--green)}
.sb-sl{background:rgba(248,113,113,.06);color:var(--red)}
.pair-badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700;
  background:rgba(56,189,248,.08);color:var(--accent);border:1px solid rgba(56,189,248,.12)}
.pp{color:var(--green);font-weight:700}.pn{color:var(--red);font-weight:700}
.empty-row{text-align:center;color:var(--muted);padding:36px !important;font-size:13px}
.tr-open{background:rgba(56,189,248,.03) !important}
</style>
</head>
<body>
<div class="hdr">
  <div class="brand">SCALPBOT <span class="brand-sub">/ VISÃO GERAL</span></div>
  <div class="hdr-r">
    <div class="live" id="live-dot"></div>
    <span class="ts" id="clk">--:--:--</span>
    <div class="refresh-badge">↻ 30s</div>
  </div>
</div>

<main>
  <!-- Resumo -->
  <div class="summary">
    <div class="sum-card green"><div class="sum-label">PnL Total</div><div class="sum-val" id="s-pnl">$0.00</div><div class="sum-sub" id="s-pnl-sub">—</div></div>
    <div class="sum-card blue"><div class="sum-label">Bots Ativos</div><div class="sum-val blue" id="s-bots">—</div><div class="sum-sub" id="s-bots-sub">—</div></div>
    <div class="sum-card amber"><div class="sum-label">Posições Abertas</div><div class="sum-val amber" id="s-pos">0</div><div class="sum-sub" id="s-pos-sub">—</div></div>
    <div class="sum-card purple"><div class="sum-label">Win Rate Geral</div><div class="sum-val" id="s-wr" style="color:var(--purple)">—</div><div class="sum-sub" id="s-wr-sub">0W / 0L</div></div>
  </div>

  <!-- Links -->
  <div class="sec-title">Dashboards</div>
  <div class="dash-links" id="dash-links"></div>

  <!-- Contas -->
  <div class="sec-title">Contas & Saldos</div>
  <div class="accounts" id="accounts"></div>

  <!-- Operações -->
  <div class="sec-title">Operações</div>
  <div class="ops-card">
    <div class="ops-hdr">
      <div><div class="ops-title">Histórico Completo</div><div class="ops-count" id="ops-count">—</div></div>
      <div class="filters">
        <button class="ftab on" onclick="filter('all',this)">TODAS</button>
        <button class="ftab" onclick="filter('open',this)">ABERTAS</button>
        <button class="ftab" onclick="filter('win',this)">GANHOS</button>
        <button class="ftab" onclick="filter('loss',this)">PERDAS</button>
      </div>
    </div>
    <div class="tw">
      <table>
        <thead><tr>
          <th>STATUS</th><th>CONTA</th><th>EXCHANGE</th><th>PAR</th>
          <th>ENTRADA</th><th>SAÍDA</th><th>CAPITAL</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>HORA</th>
        </tr></thead>
        <tbody id="ops-body"></tbody>
      </table>
    </div>
  </div>
</main>

<script>
let allData=[], allOps=[], activeFilter='all';

function fmt(n,d=2){return(+n||0).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function fmtC(n){return(+n||0).toFixed(6).replace(/\.?0+$/,'')}

function statusBadge(op){
  if(op._open)return'<span class="status-badge sb-open">● ABERTA</span>';
  const r=(op.reason||'').toUpperCase();
  if(r.includes('TAKE_PROFIT'))return'<span class="status-badge sb-tp">✓ TAKE PROFIT</span>';
  if(r.includes('STOP_LOSS'))return'<span class="status-badge sb-sl">✗ STOP LOSS</span>';
  if((op.pnl||0)>=0)return'<span class="status-badge sb-win">✓ GANHO</span>';
  return'<span class="status-badge sb-loss">✗ PERDA</span>';
}

function filter(f,btn){
  document.querySelectorAll('.ftab').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on'); activeFilter=f;
  const ops=f==='all'?allOps:f==='open'?allOps.filter(o=>o._open):f==='win'?allOps.filter(o=>!o._open&&(o.pnl||0)>=0):allOps.filter(o=>!o._open&&(o.pnl||0)<0);
  renderOps(ops);
}

function renderOps(ops){
  const tb=document.getElementById('ops-body');
  if(!ops?.length){
    tb.innerHTML='<tr><td colspan="11" class="empty-row">Nenhuma operação ainda</td></tr>';return;
  }
  tb.innerHTML=[...ops].reverse().map(op=>{
    const pct=op.usdt_used>0?((op.pnl||0)/op.usdt_used*100).toFixed(2)+'%':'—';
    const pc=(op.pnl||0)>=0?'pp':'pn';
    const exch=(op._exchange||'binance').toLowerCase();
    const sym=(op.symbol||'—').replace('USDT','').replace('-USDT','');
    const rowCls=op._open?'tr-open':'';
    return`<tr class="${rowCls}">
      <td>${statusBadge(op)}</td>
      <td style="font-weight:600">${op._bot||'—'}</td>
      <td><span class="exch-badge ${exch}">${exch.toUpperCase()}</span></td>
      <td><span class="pair-badge">${sym}/USDT</span></td>
      <td>$${fmt(op.entry||0,4)}</td>
      <td>${op._open?'<span style="color:var(--amber)">aberta</span>':'$'+fmt(op.exit||0,4)}</td>
      <td style="color:var(--muted)">$${fmt(op.usdt_used||0)}</td>
      <td class="${pc}">${op._open?'—':(op.pnl>=0?'+':'')+'$'+Math.abs(op.pnl||0).toFixed(4)}</td>
      <td class="${pc}">${op._open?'—':pct}</td>
      <td style="color:var(--muted);font-size:10px">${(op.reason||'—').replace('STOP_LOSS','SL').replace('TAKE_PROFIT','TP').replace('[FB]','Técnico')}</td>
      <td style="color:var(--muted);font-size:10px">${(op.close||op.time||'—').slice(11,16)}</td>
    </tr>`;
  }).join('');
}

function renderAccounts(bots){
  const prices={BTC:69000,ETH:2200,SOL:82,XRP:1.3,BNB:600,ATOM:5,DOT:4,POL:0.3};
  document.getElementById('accounts').innerHTML=bots.map(b=>{
    const running=b.bot_running;
    const exch=(b.exchange||'binance').toLowerCase();
    const exchBadge=`<span class="exch-badge ${exch}">${exch.toUpperCase()}</span>`;
    const usdt=b.usdt||0;
    const bals={USDT:usdt};
    const balHtml=Object.entries(bals).map(([c,a])=>{
      const usd=(prices[c]||1)*a;
      return`<div class="bal-item">
        <div class="bal-coin">${c}</div>
        <div class="bal-amount">${c==='USDT'?'$'+fmt(a):fmtC(a)}</div>
        ${c!=='USDT'?`<div class="bal-usd">≈$${fmt(usd)}</div>`:''}
      </div>`;
    }).join('');
    const pnl=b.pnl||0; const w=b.wins||0; const l=b.losses||0; const tot=w+l;
    const wr=tot>0?Math.round(w/tot*100):null;
    const posHtml=b.position?`<div class="pos-open">
      <div><span class="pos-sym">${(b.position.symbol||'—').replace('USDT','').replace('-USDT','')}/USDT</span></div>
      <div class="pos-entry">Entrada $${fmt(b.position.entry_price||0,2)}</div>
    </div>`:'';
    return`<div class="acc-card">
      <div class="acc-hdr">
        <div class="acc-info">
          <div class="acc-emoji">${b.emoji||'🤖'}</div>
          <div>
            <div class="acc-name">${b.name} ${exchBadge}</div>
            <div class="acc-exch">${b.active_symbol||'aguardando scanner...'}</div>
          </div>
        </div>
        <div class="status-pill ${running?'on':'off'}">${running?'● ATIVO':'○ INATIVO'}</div>
      </div>
      <div class="acc-body">
        <div class="bal-grid">${balHtml}</div>
        <div class="acc-metrics">
          <div class="acc-metric"><div class="acc-metric-l">PnL</div><div class="acc-metric-v ${pnl>0?'pos':pnl<0?'neg':'neu'}">${pnl>=0?'+':''}$${pnl.toFixed(3)}</div></div>
          <div class="acc-metric"><div class="acc-metric-l">Win Rate</div><div class="acc-metric-v ${wr!==null&&wr>=55?'pos':wr!==null&&wr<45?'neg':'neu'}">${wr!==null?wr+'%':'—'}</div></div>
          <div class="acc-metric"><div class="acc-metric-l">Ops</div><div class="acc-metric-v neu">${tot}</div></div>
          <div class="acc-metric"><div class="acc-metric-l">W/L</div><div class="acc-metric-v neu">${w}/${l}</div></div>
        </div>
        ${posHtml}
      </div>
    </div>`;
  }).join('');
}

function buildDashLinks(bots){
  const links=[
    {url:`http://${location.hostname}:5000`,label:'⊞ Todos os Bots',port:'5000',on:true},
    ...bots.map((b,i)=>({url:`http://${location.hostname}:${5001+i}`,label:`${b.emoji} ${b.name}`,port:String(5001+i),on:b.bot_running}))
  ];
  document.getElementById('dash-links').innerHTML=links.map(a=>
    `<a class="dash-link" href="${a.url}" target="_blank">
      <div class="dot ${a.on?'on':'off'}"></div>
      ${a.label}
      <span class="port">· ${a.port}</span>
    </a>`
  ).join('');
}

function updateSummary(bots){
  const totalPnl=bots.reduce((a,b)=>a+(b.pnl||0),0);
  const ativos=bots.filter(b=>b.bot_running).length;
  const totalOps=bots.reduce((a,b)=>a+(b.trades||[]).length+(b.position?1:0),0);
  const abertas=bots.filter(b=>b.position).length;
  const wins=bots.reduce((a,b)=>a+(b.wins||0),0);
  const losses=bots.reduce((a,b)=>a+(b.losses||0),0);
  const tot=wins+losses;
  const wr=tot>0?Math.round(wins/tot*100):null;

  const pe=document.getElementById('s-pnl');
  pe.textContent=(totalPnl>=0?'+':'')+'$'+Math.abs(totalPnl).toFixed(4);
  pe.className='sum-val '+(totalPnl>0?'green':totalPnl<0?'red':'');
  document.getElementById('s-pnl-sub').textContent=bots.length+' conta(s) combinadas';
  document.getElementById('s-bots').textContent=ativos+'/'+bots.length;
  document.getElementById('s-bots-sub').textContent=totalOps+' operações no total';
  document.getElementById('s-pos').textContent=abertas;
  document.getElementById('s-pos-sub').textContent=abertas?abertas+' posição(ões) abertas':'nenhuma posição aberta';
  const wre=document.getElementById('s-wr');
  wre.textContent=wr!==null?wr+'%':'—';
  wre.style.color=wr!==null&&wr>=55?'var(--green)':wr!==null&&wr<45?'var(--red)':'var(--purple)';
  document.getElementById('s-wr-sub').textContent=wins+'W / '+losses+'L';

  const ld=document.getElementById('live-dot');
  if(ld)ld.className='live '+(ativos>0?'on':'');
}

async function refresh(){
  try{
    const d=await fetch('/api/overview').then(r=>r.json());
    allData=d.bots||[];
    allOps=[];
    allData.forEach(b=>{
      (b.trades||[]).forEach(t=>allOps.push({...t,_bot:b.name,_exchange:b.exchange||'binance',_open:false}));
      if(b.position)allOps.push({
        symbol:b.position.symbol,entry:b.position.entry_price,
        qty:b.position.qty,usdt_used:b.position.usdt_used||0,pnl:0,
        _bot:b.name,_exchange:b.exchange||'binance',_open:true,time:''
      });
    });
    allOps.sort((a,b)=>(a.close||a.time||'')>(b.close||b.time||'')?1:-1);
    document.getElementById('ops-count').textContent=allOps.length+' operações';
    updateSummary(allData);
    renderAccounts(allData);
    buildDashLinks(allData);
    // Re-aplica filtro ativo
    const active=document.querySelector('.ftab.on');
    if(active)active.click();
    else renderOps(allOps);
  }catch(e){console.error(e)}
}

setInterval(()=>{const c=document.getElementById('clk');if(c)c.textContent=new Date().toLocaleTimeString('pt-BR');},1000);
refresh();setInterval(refresh,15000);
</script>
</body>
</html>'''


def parse_bot_log(log_file, bot_name, bot_idx=0):
    result = {
        "name":bot_name,"emoji":"🤖","bot_running":False,
        "exchange":os.getenv(f"BOT_{bot_idx+1}_EXCHANGE","binance").lower(),
        "testnet":os.getenv(f"BOT_{bot_idx+1}_TESTNET","false").lower()=="true",
        "active_symbol":None,"price":None,"usdt":None,
        "pnl":0.0,"wins":0,"losses":0,"position":None,"trades":[],
    }
    if not os.path.exists(log_file): return result
    try: lines=open(log_file,encoding='utf-8').readlines()
    except: return result

    if lines:
        try:
            last_dt=datetime.strptime(lines[-1][:19],"%Y-%m-%d %H:%M:%S")
            result["bot_running"]=(datetime.now()-last_dt).total_seconds()<300
        except: pass

    re_price=re.compile(r'\[([\w-]+)\] \$([\d,.]+) \| RSI:[\d.]+ \| Tend:\w+ \| MACD:\w+ \| BB:[-\d.]+% \| USDT:([\d.]+)')
    re_pnl=re.compile(r'Total: \$([-+]?[\d.]+)')
    re_wl=re.compile(r'W:(\d+) L:(\d+)')
    re_close=re.compile(r'Fechado ([\w-]+) \(([^)]+)\).*PnL: \$([-+]?[\d.]+)')
    re_open=re.compile(r'Comprado ([\d.]+) ([\w-]+) @ \$([\d,.]+) \(\$([\d,.]+)\)')

    ce=cs=cq=cu=None
    for line in lines:
        m=re_price.search(line)
        if m: result["active_symbol"]=m.group(1);result["price"]=float(m.group(2).replace(",",""));result["usdt"]=float(m.group(3))
        m=re_pnl.search(line)
        if m: result["pnl"]=float(m.group(1))
        m=re_wl.search(line)
        if m: result["wins"]=int(m.group(1));result["losses"]=int(m.group(2))
        m=re_open.search(line)
        if m: cq=m.group(1);cs=m.group(2);ce=float(m.group(3).replace(",",""));cu=float(m.group(4).replace(",",""))
        m=re_close.search(line)
        if m:
            result["trades"].append({"symbol":m.group(1),"entry":ce or 0,"exit":0,
                "pnl":float(m.group(3)),"qty":cq or "—","usdt_used":cu or 0,"close":line[:19],"reason":m.group(2)})
            ce=cs=cq=cu=None
    if ce and cs: result["position"]={"symbol":cs,"entry_price":ce,"qty":cq or "—","usdt_used":cu or 0}
    if result["trades"] and result["pnl"]==0.0:
        result["pnl"]=round(sum(t["pnl"] for t in result["trades"]),4)
        result["wins"]=sum(1 for t in result["trades"] if t["pnl"]>=0)
        result["losses"]=sum(1 for t in result["trades"] if t["pnl"]<0)
    result["emoji"]=os.getenv(f"BOT_{bot_idx+1}_EMOJI","🤖")
    return result


def get_overview():
    bots=[]
    for i in range(int(os.getenv("BOT_COUNT","1"))):
        prefix=f"BOT_{i+1}"
        name=os.getenv(f"{prefix}_NAME",f"Bot {i+1}")
        slug=name.lower().replace(" ","_")
        candidatos=[os.path.join(BASE,f"bot_bot_{slug}.log"),os.path.join(BASE,f"bot_{slug}.log"),os.path.join(BASE,"bot.log")]
        for f in sorted(glob.glob(os.path.join(BASE,"*.log"))):
            if slug in os.path.basename(f).lower() and f not in candidatos:candidatos.insert(0,f)
        log_file=next((f for f in candidatos if os.path.exists(f)),candidatos[-1])
        bots.append(parse_bot_log(log_file,name,i))
    return bots

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/api/overview")
def api_overview(): return jsonify({"bots":get_overview()})

if __name__=="__main__":
    print(" ScalpBot Visão Geral v2.0 — http://localhost:5004")
    app.run(host="0.0.0.0",port=5004,debug=False)
