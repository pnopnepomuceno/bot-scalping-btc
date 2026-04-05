"""
ScalpBot — Dashboard Visão Geral (porta 5004)
Mostra todas as contas, saldos e operações de forma simples e clara.
"""
from flask import Flask, jsonify, render_template_string
import os, re, glob, json
from datetime import datetime
from dotenv import load_dotenv

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ENV  = os.path.join(BASE, '.env')
load_dotenv(dotenv_path=ENV)

HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>ScalpBot — Visão Geral</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0e1a;color:#e2e8f0;font-family:'Inter',sans-serif;min-height:100vh;padding:0 0 40px}

/* Header */
.hdr{background:linear-gradient(135deg,#0d1526,#111d35);border-bottom:1px solid rgba(255,255,255,.07);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.brand{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:600;color:#60a5fa;letter-spacing:.05em}
.brand span{color:#34d399}
.hdr-r{display:flex;align-items:center;gap:14px}
.live{width:9px;height:9px;border-radius:50%;background:#34d399;box-shadow:0 0 12px #34d399;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.ts{font-family:'JetBrains Mono',monospace;font-size:12px;color:#64748b}
.refresh-badge{font-size:10px;background:rgba(96,165,250,.1);color:#60a5fa;border:1px solid rgba(96,165,250,.2);padding:3px 8px;border-radius:20px}

main{max-width:1200px;margin:0 auto;padding:24px}

/* Seção título */
.section-title{font-size:11px;font-weight:600;letter-spacing:.1em;color:#64748b;text-transform:uppercase;margin:28px 0 14px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:rgba(255,255,255,.06)}

/* Cards de resumo */
.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}
.sum-card{background:#0d1526;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:18px 20px;position:relative;overflow:hidden}
.sum-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.sum-card.green::before{background:linear-gradient(90deg,#34d399,#059669)}
.sum-card.blue::before{background:linear-gradient(90deg,#60a5fa,#3b82f6)}
.sum-card.amber::before{background:linear-gradient(90deg,#fbbf24,#d97706)}
.sum-card.purple::before{background:linear-gradient(90deg,#a78bfa,#7c3aed)}
.sum-label{font-size:11px;color:#64748b;font-weight:500;letter-spacing:.05em;margin-bottom:8px}
.sum-val{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;line-height:1}
.sum-val.green{color:#34d399}.sum-val.blue{color:#60a5fa}.sum-val.amber{color:#fbbf24}.sum-val.red{color:#f87171}
.sum-sub{font-size:11px;color:#64748b;margin-top:6px;font-family:'JetBrains Mono',monospace}

/* Cards de conta */
.accounts-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}
.account-card{background:#0d1526;border:1px solid rgba(255,255,255,.07);border-radius:16px;overflow:hidden}
.acc-header{padding:16px 20px;display:flex;align-items:center;justify-content:space-between}
.acc-name{display:flex;align-items:center;gap:10px}
.acc-emoji{font-size:22px}
.acc-title{font-size:15px;font-weight:600}
.acc-sub{font-size:11px;color:#64748b;margin-top:2px;font-family:'JetBrains Mono',monospace}
.status-pill{font-size:10px;font-weight:600;padding:4px 10px;border-radius:20px;font-family:'JetBrains Mono',monospace}
.status-pill.on{background:rgba(52,211,153,.12);color:#34d399;border:1px solid rgba(52,211,153,.2)}
.status-pill.off{background:rgba(248,113,113,.1);color:#f87171;border:1px solid rgba(248,113,113,.2)}
.status-pill.sim{background:rgba(251,191,36,.1);color:#fbbf24;border:1px solid rgba(251,191,36,.2)}

/* Saldos */
.balances{padding:0 20px 16px;display:flex;flex-wrap:wrap;gap:8px}
.bal-item{background:#111d35;border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:10px 14px;min-width:110px;flex:1}
.bal-coin{font-size:10px;font-weight:600;color:#64748b;letter-spacing:.08em;margin-bottom:4px}
.bal-amount{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;color:#e2e8f0}
.bal-usd{font-size:10px;color:#64748b;margin-top:2px;font-family:'JetBrains Mono',monospace}

/* PnL da conta */
.acc-pnl{padding:12px 20px;background:#080c18;border-top:1px solid rgba(255,255,255,.05);display:flex;gap:20px;flex-wrap:wrap}
.pnl-item{display:flex;flex-direction:column;gap:2px}
.pnl-label{font-size:10px;color:#64748b;font-weight:500}
.pnl-val{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700}
.pnl-val.pos{color:#34d399}.pnl-val.neg{color:#f87171}.pnl-val.neu{color:#94a3b8}

/* Tabela de operações */
.ops-section{background:#0d1526;border:1px solid rgba(255,255,255,.07);border-radius:16px;overflow:hidden}
.ops-header{padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.05)}
.ops-title{font-size:14px;font-weight:600}
.ops-count{font-size:11px;color:#64748b;font-family:'JetBrains Mono',monospace}
.filter-tabs{display:flex;gap:6px}
.ftab{font-size:10px;padding:4px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.08);background:transparent;color:#64748b;cursor:pointer;font-weight:500;transition:all .2s;font-family:'JetBrains Mono',monospace}
.ftab.on{background:rgba(96,165,250,.12);border-color:rgba(96,165,250,.3);color:#60a5fa}
.ops-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:'JetBrains Mono',monospace;font-size:11px;white-space:nowrap}
th{color:#475569;font-size:9px;letter-spacing:.1em;padding:10px 16px;text-align:left;border-bottom:1px solid rgba(255,255,255,.05);font-weight:600}
td{padding:12px 16px;border-bottom:1px solid rgba(255,255,255,.03)}
tr:last-child td{border:none}
tr:hover td{background:rgba(255,255,255,.02)}

/* Status badges */
.op-status{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:20px;font-size:9px;font-weight:700}
.op-status.aberta{background:rgba(96,165,250,.12);color:#60a5fa;border:1px solid rgba(96,165,250,.2)}
.op-status.ganho{background:rgba(52,211,153,.12);color:#34d399;border:1px solid rgba(52,211,153,.2)}
.op-status.perda{background:rgba(248,113,113,.1);color:#f87171;border:1px solid rgba(248,113,113,.2)}
.op-status.tp{background:rgba(52,211,153,.08);color:#10b981}
.op-status.sl{background:rgba(248,113,113,.08);color:#ef4444}
.op-status dot{width:5px;height:5px;border-radius:50%;background:currentColor}

.pair-badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700;background:rgba(96,165,250,.1);color:#60a5fa;border:1px solid rgba(96,165,250,.15)}
.exch-badge{display:inline-block;padding:2px 6px;border-radius:5px;font-size:8px;font-weight:700}
.exch-badge.binance{background:rgba(240,185,11,.1);color:#f0b90b}
.exch-badge.okx{background:rgba(167,139,250,.1);color:#a78bfa}
.pp{color:#34d399;font-weight:700}.pn{color:#f87171;font-weight:700}
.empty-row{text-align:center;color:#475569;padding:32px !important;font-size:13px}

/* Posição aberta destaque */
.pos-open{background:rgba(96,165,250,.04) !important;border-left:3px solid #60a5fa !important}

/* Link para dash completo */
.dash-link{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:8px;background:rgba(96,165,250,.08);color:#60a5fa;border:1px solid rgba(96,165,250,.15);font-size:11px;font-weight:500;text-decoration:none;transition:all .2s;font-family:'JetBrains Mono',monospace}
.dash-link:hover{background:rgba(96,165,250,.15)}
.dash-links{display:flex;gap:8px;flex-wrap:wrap}
</style>
</head>
<body>
<div class="hdr">
  <div class="brand">SCALP<span>BOT</span> <span style="color:#64748b;font-size:12px;font-weight:400">/ Visão Geral</span></div>
  <div class="hdr-r">
    <div class="live"></div>
    <div class="ts" id="clk">--:--:--</div>
    <div class="refresh-badge">↻ auto 30s</div>
  </div>
</div>

<main>
  <!-- Resumo geral -->
  <div class="section-title">Resumo Geral</div>
  <div class="summary-grid" id="summary">
    <div class="sum-card green"><div class="sum-label">PNL TOTAL</div><div class="sum-val" id="s-pnl">$0.00</div><div class="sum-sub" id="s-pnl-sub">todas as contas</div></div>
    <div class="sum-card blue"><div class="sum-label">BOTS ATIVOS</div><div class="sum-val blue" id="s-bots">0/0</div><div class="sum-sub" id="s-ops-total">0 operações</div></div>
    <div class="sum-card amber"><div class="sum-label">POSIÇÕES ABERTAS</div><div class="sum-val amber" id="s-pos">0</div><div class="sum-sub" id="s-pos-sub">aguardando</div></div>
    <div class="sum-card purple"><div class="sum-label">WIN RATE GERAL</div><div class="sum-val" id="s-wr" style="color:#a78bfa">—</div><div class="sum-sub" id="s-wr-sub">0W / 0L</div></div>
  </div>

  <!-- Links para dashboards completos -->
  <div class="section-title">Dashboards Completos</div>
  <div class="dash-links" id="dash-links"></div>

  <!-- Saldos por conta -->
  <div class="section-title">Saldos por Conta</div>
  <div class="accounts-grid" id="accounts"></div>

  <!-- Operações -->
  <div class="section-title">Todas as Operações</div>
  <div class="ops-section">
    <div class="ops-header">
      <div>
        <div class="ops-title">Histórico de Operações</div>
        <div class="ops-count" id="ops-count">0 operações</div>
      </div>
      <div class="filter-tabs">
        <button class="ftab on" onclick="filter('all',this)">TODAS</button>
        <button class="ftab" onclick="filter('open',this)">ABERTAS</button>
        <button class="ftab" onclick="filter('win',this)">GANHOS</button>
        <button class="ftab" onclick="filter('loss',this)">PERDAS</button>
      </div>
    </div>
    <div class="ops-wrap">
      <table>
        <thead><tr>
          <th>STATUS</th><th>CONTA</th><th>EXCHANGE</th><th>PAR</th>
          <th>ENTRADA</th><th>SAÍDA</th><th>QTD</th><th>CAPITAL</th>
          <th>PNL</th><th>%</th><th>MOTIVO</th><th>DATA/HORA</th>
        </tr></thead>
        <tbody id="ops-body"></tbody>
      </table>
    </div>
  </div>
</main>

<script>
let allData=[], allOps=[];

function fmt(n,d=2){return Number(n).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function fmtCrypto(n){return Number(n).toFixed(6).replace(/\.?0+$/,'')}

function statusBadge(op){
  if(op._open) return '<span class="op-status aberta"><span class="dot"></span>ABERTA</span>';
  const r=(op.reason||'').toUpperCase();
  if(r.includes('TAKE_PROFIT')) return '<span class="op-status tp">✓ TAKE PROFIT</span>';
  if(r.includes('STOP_LOSS'))   return '<span class="op-status sl">✗ STOP LOSS</span>';
  if(op.pnl>=0) return '<span class="op-status ganho">✓ GANHO</span>';
  return '<span class="op-status perda">✗ PERDA</span>';
}

function filter(f, btn){
  document.querySelectorAll('.ftab').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  let ops = f==='all' ? allOps
           : f==='open' ? allOps.filter(o=>o._open)
           : f==='win'  ? allOps.filter(o=>!o._open&&o.pnl>=0)
           : allOps.filter(o=>!o._open&&o.pnl<0);
  renderOps(ops);
}

function renderOps(ops){
  const tbody=document.getElementById('ops-body');
  if(!ops||!ops.length){
    tbody.innerHTML='<tr><td colspan="12" class="empty-row">Nenhuma operação ainda — aguardando sinais do mercado</td></tr>';
    return;
  }
  tbody.innerHTML=[...ops].reverse().map(op=>{
    const pct=op.usdt_used>0?(op.pnl/op.usdt_used*100).toFixed(2)+'%':'—';
    const pc=op.pnl>=0?'pp':'pn';
    const rowCls=op._open?'pos-open':'';
    const exch=(op._exchange||'binance').toLowerCase();
    return`<tr class="${rowCls}">
      <td>${statusBadge(op)}</td>
      <td style="font-weight:600">${op._bot||'—'}</td>
      <td><span class="exch-badge ${exch}">${exch.toUpperCase()}</span></td>
      <td><span class="pair-badge">${(op.symbol||'—').replace('USDT','').replace('-USDT','')}/USDT</span></td>
      <td>$${fmt(op.entry||0,4)}</td>
      <td>${op._open?'<span style="color:#fbbf24">aberta</span>':'$'+fmt(op.exit||0,4)}</td>
      <td style="color:#94a3b8">${op.qty||'—'}</td>
      <td style="color:#94a3b8">$${fmt(op.usdt_used||0)}</td>
      <td class="${pc}">${op._open?'—':(op.pnl>=0?'+':'')+'$'+Number(op.pnl||0).toFixed(4)}</td>
      <td class="${pc}">${op._open?'—':pct}</td>
      <td style="color:#64748b;font-size:9px">${(op.reason||'—').replace('STOP_LOSS','SL').replace('TAKE_PROFIT','TP').replace('[FB]','Técnico')}</td>
      <td style="color:#475569;font-size:9px">${(op.close||op.time||'—').substring(0,16)}</td>
    </tr>`;
  }).join('');
}

function renderAccounts(bots){
  const el=document.getElementById('accounts');
  const prices={BTC:67000,ETH:2000,SOL:80,XRP:1.3,BNB:600};
  el.innerHTML=bots.map((b,i)=>{
    const exchColors=['#60a5fa','#fb923c','#a78bfa','#34d399','#f87171'];
    const running=b.bot_running;
    const exch=(b.exchange||'binance').toLowerCase();
    const exchBadge=exch==='okx'
      ?'<span class="exch-badge okx">OKX</span>'
      :'<span class="exch-badge binance">BINANCE</span>';

    // Saldos
    const bals=b.balances||{};
    const balHtml=Object.entries(bals).map(([coin,amt])=>{
      const usd=(prices[coin]||1)*amt;
      return`<div class="bal-item">
        <div class="bal-coin">${coin}</div>
        <div class="bal-amount">${fmtCrypto(amt)}</div>
        <div class="bal-usd">≈ $${fmt(usd)}</div>
      </div>`;
    }).join('') || '<div class="bal-item"><div class="bal-coin">USDT</div><div class="bal-amount">$'+fmt(b.usdt||0)+'</div></div>';

    const pnl=b.pnl||0;
    const w=b.wins||0,l=b.losses||0,tot=w+l;
    const wr=tot>0?Math.round(w/tot*100):null;

    return`<div class="account-card">
      <div class="acc-header" style="border-bottom:1px solid rgba(255,255,255,.05)">
        <div class="acc-name">
          <div class="acc-emoji">${b.emoji||'🤖'}</div>
          <div>
            <div class="acc-title">${b.name} ${exchBadge}</div>
            <div class="acc-sub">${b.active_symbol||'aguardando scanner...'} ${b.testnet?'· SIMULAÇÃO':''}</div>
          </div>
        </div>
        <div class="status-pill ${running?'on':b.testnet?'sim':'off'}">${running?'● ATIVO':'○ INATIVO'}</div>
      </div>
      <div class="balances">${balHtml}</div>
      <div class="acc-pnl">
        <div class="pnl-item"><div class="pnl-label">PNL Total</div><div class="pnl-val ${pnl>0?'pos':pnl<0?'neg':'neu'}">${pnl>=0?'+':''}$${pnl.toFixed(4)}</div></div>
        <div class="pnl-item"><div class="pnl-label">Win Rate</div><div class="pnl-val ${wr>=55?'pos':wr!==null&&wr<45?'neg':'neu'}">${wr!==null?wr+'%':'—'}</div></div>
        <div class="pnl-item"><div class="pnl-label">Operações</div><div class="pnl-val neu">${tot}</div></div>
        <div class="pnl-item"><div class="pnl-label">Ganhos/Perdas</div><div class="pnl-val neu">${w}W / ${l}L</div></div>
        ${b.position?`<div class="pnl-item"><div class="pnl-label">Posição Aberta</div><div class="pnl-val" style="color:#60a5fa">${b.position.symbol||'—'}</div></div>`:''}
      </div>
    </div>`;
  }).join('');
}

function updateSummary(bots){
  const totalPnl=bots.reduce((a,b)=>a+(b.pnl||0),0);
  const ativos=bots.filter(b=>b.bot_running).length;
  const totalOps=bots.reduce((a,b)=>a+(b.trades||[]).length,0);
  const abertas=bots.filter(b=>b.position).length;
  const wins=bots.reduce((a,b)=>a+(b.wins||0),0);
  const losses=bots.reduce((a,b)=>a+(b.losses||0),0);
  const tot=wins+losses;
  const wr=tot>0?Math.round(wins/tot*100):null;

  const pnlEl=document.getElementById('s-pnl');
  pnlEl.textContent=(totalPnl>=0?'+':'')+'$'+Math.abs(totalPnl).toFixed(4);
  pnlEl.className='sum-val '+(totalPnl>0?'green':totalPnl<0?'red':'neu');
  document.getElementById('s-pnl-sub').textContent=bots.length+' conta(s)';
  document.getElementById('s-bots').textContent=ativos+'/'+bots.length;
  document.getElementById('s-ops-total').textContent=totalOps+' operações realizadas';
  document.getElementById('s-pos').textContent=abertas;
  document.getElementById('s-pos-sub').textContent=abertas?abertas+' posição(ões) aberta(s)':'sem posições abertas';
  const wrEl=document.getElementById('s-wr');
  wrEl.textContent=wr!==null?wr+'%':'—';
  wrEl.style.color=wr>=55?'#34d399':wr!==null&&wr<45?'#f87171':'#a78bfa';
  document.getElementById('s-wr-sub').textContent=wins+'W / '+losses+'L';
}

function buildDashLinks(bots){
  const links=document.getElementById('dash-links');
  const anchors=[
    {url:'http://'+location.hostname+':5000',label:'⊞ Todos os Bots','sub':'porta 5000'},
    ...bots.map((b,i)=>({url:'http://'+location.hostname+':'+(5001+i),label:b.emoji+' '+b.name,sub:'porta '+(5001+i)}))
  ];
  links.innerHTML=anchors.map(a=>`<a class="dash-link" href="${a.url}" target="_blank">${a.label} <span style="color:#475569">· ${a.sub}</span></a>`).join('');
}

async function refresh(){
  try{
    const r=await fetch('/api/overview');
    const d=await r.json();
    allData=d.bots||[];

    // Coleta todas as operações com info de bot e exchange
    allOps=[];
    allData.forEach(b=>{
      (b.trades||[]).forEach(t=>{
        allOps.push({...t,_bot:b.name,_exchange:b.exchange||'binance',_open:false});
      });
      if(b.position){
        allOps.push({
          symbol:b.position.symbol,entry:b.position.entry_price,
          qty:b.position.qty,usdt_used:b.position.usdt_used||0,
          pnl:0,_bot:b.name,_exchange:b.exchange||'binance',_open:true,
          time:b.position.time||''
        });
      }
    });
    allOps.sort((a,b)=>(a.close||a.time||'')>(b.close||b.time||'')?1:-1);

    document.getElementById('ops-count').textContent=allOps.length+' operações';
    updateSummary(allData);
    renderAccounts(allData);
    buildDashLinks(allData);

    // Re-aplica filtro ativo
    const activeTab=document.querySelector('.ftab.on');
    if(activeTab) activeTab.click();
    else renderOps(allOps);

  }catch(e){console.error(e)}
}

setInterval(()=>{
  const c=document.getElementById('clk');
  if(c)c.textContent=new Date().toLocaleTimeString('pt-BR');
},1000);

refresh();
setInterval(refresh,15000);
</script>
</body>
</html>'''


# ── Parser reutilizado do dashboard principal ─────────────────────────────────

def parse_bot_log(log_file, bot_name, bot_idx=0):
    result = {
        "name":bot_name,"emoji":"🤖","bot_running":False,
        "exchange":os.getenv(f"BOT_{bot_idx+1}_EXCHANGE","binance").lower(),
        "testnet":os.getenv(f"BOT_{bot_idx+1}_TESTNET","false").lower()=="true",
        "active_symbol":None,"price":None,"usdt":None,
        "pnl":0.0,"wins":0,"losses":0,
        "position":None,"trades":[],"balances":{},
    }
    if not os.path.exists(log_file): return result
    try:
        lines = open(log_file, encoding='utf-8').readlines()
    except: return result

    if lines:
        try:
            last_dt = datetime.strptime(lines[-1][:19], "%Y-%m-%d %H:%M:%S")
            result["bot_running"] = (datetime.now()-last_dt).total_seconds()<300
        except: pass

    re_price = re.compile(r'\[([\w-]+)\] \$([\d,.]+) \| RSI:[\d.]+ \| Tend:\w+ \| MACD:\w+ \| BB:[-\d.]+% \| USDT:([\d.]+)')
    re_pnl   = re.compile(r'Total: \$([-+]?[\d.]+)')
    re_wl    = re.compile(r'W:(\d+) L:(\d+)')
    re_close = re.compile(r'Fechado ([\w-]+) \(([^)]+)\).*PnL: \$([-+]?[\d.]+)')
    re_open  = re.compile(r'Comprado ([\d.]+) ([\w-]+) @ \$([\d,.]+) \(\$([\d,.]+)\)')

    cur_entry=cur_sym=cur_qty=cur_usdt=None

    for line in lines:
        m=re_price.search(line)
        if m:
            result["active_symbol"]=m.group(1)
            result["price"]=float(m.group(2).replace(",",""))
            result["usdt"]=float(m.group(3))

        m=re_pnl.search(line)
        if m: result["pnl"]=float(m.group(1))

        m=re_wl.search(line)
        if m: result["wins"]=int(m.group(1));result["losses"]=int(m.group(2))

        m=re_open.search(line)
        if m:
            cur_qty=m.group(1);cur_sym=m.group(2)
            cur_entry=float(m.group(3).replace(",",""))
            cur_usdt=float(m.group(4).replace(",",""))

        m=re_close.search(line)
        if m:
            result["trades"].append({
                "symbol":m.group(1),"entry":cur_entry or 0,"exit":0,
                "pnl":float(m.group(3)),"qty":cur_qty or "—",
                "usdt_used":cur_usdt or 0,"close":line[:19],"reason":m.group(2),
            })
            cur_entry=cur_sym=cur_qty=cur_usdt=None

    if cur_entry and cur_sym:
        result["position"]={"symbol":cur_sym,"entry_price":cur_entry,
                             "qty":cur_qty or "—","usdt_used":cur_usdt or 0}

    if result["trades"] and result["pnl"]==0.0:
        result["pnl"]=round(sum(t["pnl"] for t in result["trades"]),4)
        result["wins"]=sum(1 for t in result["trades"] if t["pnl"]>=0)
        result["losses"]=sum(1 for t in result["trades"] if t["pnl"]<0)

    # Saldo simulado por enquanto (pode integrar com API real depois)
    if result["usdt"]: result["balances"]["USDT"]=result["usdt"]

    return result


def get_overview():
    bots=[]
    bot_count=int(os.getenv("BOT_COUNT","1"))
    for i in range(bot_count):
        prefix=f"BOT_{i+1}"
        name=os.getenv(f"{prefix}_NAME",f"Bot {i+1}")
        slug=name.lower().replace(" ","_")
        candidatos=[
            os.path.join(BASE,f"bot_bot_{slug}.log"),
            os.path.join(BASE,f"bot_{slug}.log"),
            os.path.join(BASE,"bot.log"),
        ]
        for f in sorted(glob.glob(os.path.join(BASE,"*.log"))):
            if slug in os.path.basename(f).lower() and f not in candidatos:
                candidatos.insert(0,f)
        log_file=next((f for f in candidatos if os.path.exists(f)),candidatos[-1])
        b=parse_bot_log(log_file,name,i)
        b["emoji"]=os.getenv(f"{prefix}_EMOJI","🤖")
        bots.append(b)
    return bots


@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/overview")
def api_overview():
    return jsonify({"bots": get_overview()})

if __name__ == "__main__":
    print("="*50)
    print(" ScalpBot — Dashboard Visão Geral")
    print(" Acesse: http://localhost:5004")
    print("="*50)
    app.run(host="0.0.0.0", port=5004, debug=False)
