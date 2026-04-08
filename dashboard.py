"""
ScalpBot Dashboard Unificado v3.0 — porta 5000
Todas as views em abas: Visão Geral + Bot individual + Relatório
Relatório diário automático às 22h via Telegram
Comandos via Telegram: /status /relatorio /saldo /ops /scanner /pausar /ativar
"""
from flask import Flask, jsonify, render_template_string, request
import os, re, glob, json, threading, time
from datetime import datetime, date
from dotenv import load_dotenv, set_key

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ENV  = os.path.join(BASE, '.env')
load_dotenv(dotenv_path=ENV)

THEMES = [
    {"accent":"#38bdf8","bg":"#060c1a","s1":"#0a1628","s2":"#0e1e36"},
    {"accent":"#fb923c","bg":"#0f0a04","s1":"#1a1208","s2":"#261b0d"},
    {"accent":"#c084fc","bg":"#080510","s1":"#120a1e","s2":"#1a102c"},
    {"accent":"#4ade80","bg":"#030a06","s1":"#071510","s2":"#0c1e18"},
    {"accent":"#f87171","bg":"#100404","s1":"#1e0808","s2":"#2c0f0f"},
]

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScalpBot</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--accent:#38bdf8;--bg:#060c1a;--s1:#0a1628;--s2:#0e1e36;--s3:#132544;
--green:#4ade80;--red:#f87171;--amber:#fbbf24;--purple:#c084fc;
--text:#e2eeff;--muted:#5a7299;--border:rgba(255,255,255,.07);
--mono:'Space Mono',monospace;--font:'DM Sans',sans-serif;--r:12px}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;font-size:14px}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:52px;
  background:rgba(10,22,40,.95);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:200}
.brand{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--accent);letter-spacing:.15em}
.hdr-r{display:flex;align-items:center;gap:12px}
.live{width:7px;height:7px;border-radius:50%;background:var(--muted);transition:all .3s}
.live.on{background:var(--green);box-shadow:0 0 10px var(--green);animation:p 2s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.4}}
.bot-st{font-family:var(--mono);font-size:11px;color:var(--muted)}
.bot-st.on{color:var(--green)}
.clk{font-family:var(--mono);font-size:11px;color:var(--muted);background:var(--s1);
  padding:4px 10px;border-radius:6px;border:1px solid var(--border)}
.ticker{display:flex;overflow-x:auto;scrollbar-width:none;background:var(--s1);border-bottom:1px solid var(--border)}
.ticker::-webkit-scrollbar{display:none}
.ti{display:flex;flex-direction:column;align-items:center;padding:8px 18px;border-right:1px solid var(--border);min-width:100px;flex-shrink:0;gap:3px}
.ti-s{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:.1em}
.ti-p{font-family:var(--mono);font-size:13px;font-weight:700}
.ti-c{font-family:var(--mono);font-size:10px}
.up{color:var(--green)}.dn{color:var(--red)}
.nav{display:flex;gap:0;border-bottom:1px solid var(--border);background:var(--s1);overflow-x:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav-tab{padding:12px 20px;border:none;background:transparent;color:var(--muted);font-size:12px;font-weight:600;
  cursor:pointer;transition:all .2s;border-bottom:2px solid transparent;font-family:var(--font);white-space:nowrap;
  display:flex;align-items:center;gap:8px}
.nav-tab:hover{color:var(--text)}
.nav-tab.on{color:var(--accent);border-bottom-color:var(--accent);background:rgba(56,189,248,.05)}
.nd{width:6px;height:6px;border-radius:50%;background:var(--muted)}
.nd.on{background:var(--green);box-shadow:0 0 6px var(--green)}
.exch{font-size:9px;font-weight:700;padding:2px 6px;border-radius:5px;font-family:var(--mono)}
.exch.bnb{background:rgba(240,185,11,.12);color:#f0b90b}
.exch.okx{background:rgba(192,132,252,.12);color:#c084fc}
.view{display:none;padding:20px 24px;max-width:1600px;margin:0 auto}
.view.on{display:block}
.sum{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}
.sum-c{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:20px;position:relative;overflow:hidden}
.sum-c::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.sum-c.g::before{background:var(--green)}.sum-c.b::before{background:var(--accent)}
.sum-c.a::before{background:var(--amber)}.sum-c.p::before{background:var(--purple)}
.sum-lbl{font-size:9px;font-weight:700;letter-spacing:.12em;color:var(--muted);margin-bottom:10px;text-transform:uppercase}
.sum-v{font-family:var(--mono);font-size:24px;font-weight:700;line-height:1}
.sum-v.g{color:var(--green)}.sum-v.r{color:var(--red)}.sum-v.b{color:var(--accent)}.sum-v.a{color:var(--amber)}
.sum-s{font-size:11px;color:var(--muted);margin-top:6px;font-family:var(--mono)}
.sec{font-size:9px;font-weight:700;letter-spacing:.15em;color:var(--muted);text-transform:uppercase;
  display:flex;align-items:center;gap:10px;margin:24px 0 14px}
.sec::after{content:'';flex:1;height:1px;background:var(--border)}
.accs{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.acc{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.acc-h{padding:12px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.acc-nm{display:flex;align-items:center;gap:8px}
.acc-mtr{display:grid;grid-template-columns:repeat(4,1fr)}
.acc-m{padding:9px 12px;border-right:1px solid var(--border)}
.acc-m:last-child{border:none}
.acc-ml{font-size:9px;color:var(--muted);margin-bottom:3px}
.acc-mv{font-family:var(--mono);font-size:12px;font-weight:700}
.acc-mv.pos{color:var(--green)}.acc-mv.neg{color:var(--red)}.acc-mv.neu{color:var(--text)}
.sp{font-size:9px;font-weight:700;padding:4px 10px;border-radius:20px;font-family:var(--mono)}
.sp.on{background:rgba(74,222,128,.1);color:var(--green);border:1px solid rgba(74,222,128,.2)}
.sp.off{background:rgba(248,113,113,.08);color:var(--red);border:1px solid rgba(248,113,113,.15)}
.oc{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.oh{padding:12px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.otabs{display:flex;gap:4px}
.ot{font-family:var(--mono);font-size:9px;font-weight:700;padding:4px 10px;border-radius:6px;
  border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;letter-spacing:.06em}
.ot.on{background:rgba(56,189,248,.1);border-color:rgba(56,189,248,.3);color:var(--accent)}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;white-space:nowrap}
th{color:var(--muted);font-size:9px;letter-spacing:.1em;padding:9px 14px;text-align:left;
  border-bottom:1px solid var(--border);background:rgba(0,0,0,.15);font-weight:700}
td{padding:9px 14px;border-bottom:1px solid rgba(255,255,255,.03)}
tr:last-child td{border:none}
tr:hover td{background:rgba(255,255,255,.02)}
.bk{display:inline-block;padding:2px 7px;border-radius:5px;font-size:10px;font-weight:700}
.bsym{background:rgba(56,189,248,.08);color:var(--accent);border:1px solid rgba(56,189,248,.12)}
.pp{color:var(--green);font-weight:700}.pn{color:var(--red);font-weight:700}
.sb{display:inline-flex;align-items:center;padding:3px 8px;border-radius:20px;font-size:9px;font-weight:700}
.sb-o{background:rgba(56,189,248,.1);color:var(--accent)}.sb-w{background:rgba(74,222,128,.1);color:var(--green)}
.sb-l{background:rgba(248,113,113,.08);color:var(--red)}.sb-t{color:var(--green)}.sb-s{color:var(--red)}
.sts{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.st{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:14px;position:relative;overflow:hidden}
.st::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent);opacity:.3}
.st.g::before{background:var(--green);opacity:1}.st.r::before{background:var(--red);opacity:1}.st.b::before{background:var(--accent);opacity:1}
.st-l{font-size:9px;font-weight:600;letter-spacing:.12em;color:var(--muted);margin-bottom:8px;text-transform:uppercase}
.st-v{font-family:var(--mono);font-size:19px;font-weight:700;line-height:1}
.st-v.g{color:var(--green)}.st-v.r{color:var(--red)}.st-v.b{color:var(--accent)}
.st-s{font-size:11px;color:var(--muted);margin-top:4px;font-family:var(--mono)}
.indr{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:4px 0}
.indi{background:var(--s1);border:1px solid var(--border);border-radius:8px;padding:9px 12px;text-align:center}
.indl{font-size:9px;color:var(--muted);letter-spacing:.08em;margin-bottom:4px;text-transform:uppercase}
.indv{font-family:var(--mono);font-size:13px;font-weight:700}
.mid{display:grid;grid-template-columns:1fr 300px;gap:12px}
.card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:16px;overflow:hidden}
.ct{font-size:10px;font-weight:700;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}
.ch{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.cw{position:relative;height:155px}
.pe{font-size:13px;color:var(--muted);text-align:center;padding:28px 0}
.pc{background:var(--s2);border:1px solid rgba(56,189,248,.15);border-radius:10px;padding:12px}
.ps{font-family:var(--mono);font-size:19px;font-weight:700;color:var(--accent);margin-bottom:8px}
.pr{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px}
.pr:last-child{border:none}
.pl{color:var(--muted)}.pv{font-family:var(--mono);font-weight:600}
.sc-i{display:flex;align-items:center;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);gap:8px}
.sc-i:last-child{border:none}
.sc-s{font-family:var(--mono);font-size:12px;font-weight:700;width:88px}
.sc-s.best{color:var(--accent)}
.sc-bw{flex:1;height:4px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden}
.sc-b{height:100%;border-radius:2px;background:var(--accent)}
.sc-sc{font-family:var(--mono);font-size:10px;color:var(--muted);width:40px;text-align:right}
.sc-ch{font-family:var(--mono);font-size:10px;width:50px;text-align:right}
.lw{height:230px;overflow-y:auto;padding:6px;scrollbar-width:thin;scrollbar-color:var(--s3) transparent}
.ll{display:block;line-height:17px;color:#4a6280;font-size:10px;padding:1px 2px;font-family:var(--mono);white-space:pre-wrap;word-break:break-all}
.ll.buy{color:#4ade80!important}.ll.sell{color:#f87171!important}.ll.warn{color:#fbbf24!important}
.ll.err{color:#f87171!important;opacity:.7}.ll.ia{color:#38bdf8!important}.ll.scan{color:#c084fc!important}
.br{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.np{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:16px}
.ng{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.ni{background:var(--s2);border:1px solid var(--border);border-radius:10px;padding:10px 12px;
  display:flex;align-items:center;justify-content:space-between;gap:8px}
.nl{font-size:12px;font-weight:500;margin-bottom:2px}
.nd2{font-size:10px;color:var(--muted)}
.tg{position:relative;display:inline-block;width:38px;height:21px;cursor:pointer;flex-shrink:0}
.tg input{opacity:0;width:0;height:0}
.tg-t{position:absolute;inset:0;background:rgba(255,255,255,.08);border-radius:11px;transition:.3s;border:1px solid var(--border)}
.tg-k{position:absolute;left:3px;top:3px;width:15px;height:15px;background:var(--muted);border-radius:50%;transition:.3s}
.tg input:checked+.tg-t{background:rgba(56,189,248,.2);border-color:var(--accent)}
.tg input:checked~.tg-k{left:20px;background:var(--accent)}
.sv-btn{padding:7px 16px;border-radius:8px;border:1px solid rgba(56,189,248,.3);
  background:rgba(56,189,248,.1);color:var(--accent);font-weight:600;font-size:13px;cursor:pointer;font-family:var(--font)}
.sm{font-size:12px;color:var(--green);margin-left:10px;display:none;font-family:var(--mono)}
.pg{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}
.pgi{background:var(--s2);border:1px solid var(--border);border-radius:8px;padding:9px 12px;flex:1;min-width:100px}
.rc{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:20px;margin-bottom:14px}
.rt{font-size:15px;font-weight:600;margin-bottom:4px}
.rs{font-size:12px;color:var(--muted);margin-bottom:14px;font-family:var(--mono)}
.rb2{padding:9px 18px;border-radius:9px;border:1px solid rgba(56,189,248,.3);
  background:rgba(56,189,248,.1);color:var(--accent);font-weight:600;font-size:13px;cursor:pointer;font-family:var(--font);margin-right:8px}
.rb2.g{border-color:rgba(74,222,128,.3);background:rgba(74,222,128,.08);color:var(--green)}
.rr{margin-top:14px;padding:12px 14px;background:var(--s2);border-radius:8px;
  font-family:var(--mono);font-size:11px;color:var(--muted);white-space:pre-wrap;display:none;max-height:280px;overflow-y:auto}
.cl{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.ci{background:var(--s2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:12px}
.cc{font-family:var(--mono);font-size:12px;color:var(--accent);background:rgba(56,189,248,.08);
  padding:3px 8px;border-radius:5px;white-space:nowrap}
.cd{font-size:12px;color:var(--muted)}
</style>
</head>
<body>
<div class="hdr">
  <div class="brand">SCALPBOT</div>
  <div class="hdr-r">
    <div class="live" id="live-dot"></div>
    <span class="bot-st" id="bot-st">—</span>
    <div class="clk" id="clk">--:--:--</div>
  </div>
</div>
<div class="ticker" id="ticker">
  <div class="ti" id="tick-BTCUSDT"><div class="ti-s">BTC</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-ETHUSDT"><div class="ti-s">ETH</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-BNBUSDT"><div class="ti-s">BNB</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-SOLUSDT"><div class="ti-s">SOL</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
  <div class="ti" id="tick-XRPUSDT"><div class="ti-s">XRP</div><div class="ti-p">—</div><div class="ti-c">—</div></div>
</div>
<div class="nav" id="nav">
  <button class="nav-tab on" onclick="sv('overview',this)">⊞ Visão Geral</button>
</div>

<div id="view-overview" class="view on">
  <div class="sum">
    <div class="sum-c g"><div class="sum-lbl">PnL Total</div><div class="sum-v" id="ov-pnl">$0.00</div><div class="sum-s" id="ov-ps">—</div></div>
    <div class="sum-c b"><div class="sum-lbl">Bots Ativos</div><div class="sum-v b" id="ov-bots">—</div><div class="sum-s" id="ov-bs">—</div></div>
    <div class="sum-c a"><div class="sum-lbl">Posições Abertas</div><div class="sum-v a" id="ov-pos">0</div><div class="sum-s" id="ov-pos-s">—</div></div>
    <div class="sum-c p"><div class="sum-lbl">Win Rate Geral</div><div class="sum-v" id="ov-wr" style="color:var(--purple)">—</div><div class="sum-s" id="ov-wrs">0W/0L</div></div>
  </div>
  <div class="sec">Contas & Saldos</div>
  <div class="accs" id="ov-accs"></div>
  <div class="sec" style="margin-top:20px">Todas as Operações</div>
  <div class="oc">
    <div class="oh">
      <div><span style="font-size:13px;font-weight:600">Histórico</span>&nbsp;&nbsp;<span style="font-size:11px;color:var(--muted);font-family:var(--mono)" id="ov-cnt">—</span></div>
      <div class="otabs">
        <button class="ot on" onclick="ovf('all',this)">TODAS</button>
        <button class="ot" onclick="ovf('open',this)">ABERTAS</button>
        <button class="ot" onclick="ovf('win',this)">GANHOS</button>
        <button class="ot" onclick="ovf('loss',this)">PERDAS</button>
      </div>
    </div>
    <div class="tw"><table>
      <thead><tr><th>STATUS</th><th>CONTA</th><th>PAR</th><th>ENTRADA</th><th>SAÍDA</th><th>CAPITAL</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>HORA</th></tr></thead>
      <tbody id="ov-ops"></tbody>
    </table></div>
  </div>
</div>
<div id="panels"></div>

<script>
const NT={inicio:{l:'Inicialização',d:'Bot iniciado'},compra:{l:'Compra',d:'Ordem executada'},
venda:{l:'Venda',d:'Ordem executada'},stop_loss:{l:'Stop-loss',d:'Stop atingido'},
take_profit:{l:'Take-profit',d:'Target atingido'},par_troca:{l:'Troca de par',d:'Scanner trocou'},
ia_erro:{l:'Erro IA',d:'Falha Anthropic'},resumo:{l:'Resumo',d:'Resumo diário'}};
const TH=[{a:'#38bdf8',b:'#060c1a',s1:'#0a1628',s2:'#0e1e36'},
{a:'#fb923c',b:'#0f0a04',s1:'#1a1208',s2:'#261b0d'},
{a:'#c084fc',b:'#080510',s1:'#120a1e',s2:'#1a102c'},
{a:'#4ade80',b:'#030a06',s1:'#071510',s2:'#0c1e18'},
{a:'#f87171',b:'#100404',s1:'#1e0808',s2:'#2c0f0f'}];
let bots=[],allOps=[],ovFilt='all',charts={};
function fmt(n,d=2){return(+n||0).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function sv(id,btn){
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('on'));
  btn.classList.add('on');
  const el=document.getElementById('view-'+id);if(el)el.classList.add('on');
  const idx=parseInt(id.replace('bot',''));
  if(!isNaN(idx)){const t=TH[idx%TH.length];const r=document.documentElement.style;
    r.setProperty('--accent',t.a);r.setProperty('--bg',t.b);r.setProperty('--s1',t.s1);r.setProperty('--s2',t.s2);}
  else{const r=document.documentElement.style;r.setProperty('--accent','#38bdf8');
    r.setProperty('--bg','#060c1a');r.setProperty('--s1','#0a1628');r.setProperty('--s2','#0e1e36');}
}
function sbadge(op){
  if(op._open)return'<span class="sb sb-o">● ABERTA</span>';
  const r=(op.reason||'').toUpperCase();
  if(r.includes('TAKE_PROFIT'))return'<span class="sb sb-t">✓ TP</span>';
  if(r.includes('STOP_LOSS'))return'<span class="sb sb-s">✗ SL</span>';
  return(op.pnl||0)>=0?'<span class="sb sb-w">✓ GANHO</span>':'<span class="sb sb-l">✗ PERDA</span>';
}
function rb(r){if(!r)return'—';const u=r.toUpperCase();
  if(u.includes('STOP_LOSS'))return'<span style="font-size:9px;color:var(--red)">SL</span>';
  if(u.includes('TAKE_PROFIT'))return'<span style="font-size:9px;color:var(--green)">TP</span>';
  return`<span style="font-size:9px;color:var(--muted)">Tec.</span>`;}
function ovf(f,btn){
  document.querySelectorAll('#view-overview .ot').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');ovFilt=f;
  const ops=f==='all'?allOps:f==='open'?allOps.filter(o=>o._open):f==='win'?allOps.filter(o=>!o._open&&(o.pnl||0)>=0):allOps.filter(o=>!o._open&&(o.pnl||0)<0);
  rops_ov(ops);}
function rops_ov(ops){
  const tb=document.getElementById('ov-ops');
  if(!ops?.length){tb.innerHTML='<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:24px">Nenhuma operação ainda</td></tr>';return;}
  tb.innerHTML=[...ops].reverse().map(op=>{
    const pct=op.usdt_used>0?((op.pnl||0)/op.usdt_used*100).toFixed(2)+'%':'—';
    const pc=(op.pnl||0)>=0?'pp':'pn';const sym=(op.symbol||'').replace('USDT','').replace('-USDT','');
    return`<tr><td>${sbadge(op)}</td><td style="font-size:11px;font-weight:600">${op._bot||'—'}</td>
    <td><span class="bk bsym">${sym}</span></td><td>$${fmt(op.entry||0,4)}</td>
    <td>${op._open?'<span style="color:var(--amber)">aberta</span>':'$'+fmt(op.exit||0,4)}</td>
    <td style="color:var(--muted)">$${fmt(op.usdt_used||0)}</td>
    <td class="${pc}">${op._open?'—':(op.pnl>=0?'+':'')+'$'+Math.abs(op.pnl||0).toFixed(4)}</td>
    <td class="${pc}">${op._open?'—':pct}</td>
    <td style="color:var(--muted);font-size:10px">${(op.reason||'').replace('STOP_LOSS','SL').replace('TAKE_PROFIT','TP').replace('[FB]','Tec.')}</td>
    <td style="color:var(--muted);font-size:10px">${(op.close||op.time||'').slice(11,16)}</td></tr>`;}).join('');}
function upd_ov(data){
  const tp=data.reduce((a,b)=>a+(b.pnl||0),0);
  const at=data.filter(b=>b.bot_running).length;
  const ab=data.filter(b=>b.position).length;
  const w=data.reduce((a,b)=>a+(b.wins||0),0),l=data.reduce((a,b)=>a+(b.losses||0),0);
  const tot=w+l;const wr=tot>0?Math.round(w/tot*100):null;
  const pe=document.getElementById('ov-pnl');
  pe.textContent=(tp>=0?'+':'')+'$'+Math.abs(tp).toFixed(4);
  pe.className='sum-v '+(tp>0?'g':tp<0?'r':'');
  document.getElementById('ov-ps').textContent=data.length+' conta(s)';
  document.getElementById('ov-bots').textContent=at+'/'+data.length;
  document.getElementById('ov-bs').textContent=data.reduce((a,b)=>a+(b.trades||[]).length,0)+' ops total';
  document.getElementById('ov-pos').textContent=ab;
  document.getElementById('ov-pos-s').textContent=ab?ab+' aberta(s)':'nenhuma aberta';
  const we=document.getElementById('ov-wr');we.textContent=wr!==null?wr+'%':'—';
  we.style.color=wr!==null&&wr>=55?'var(--green)':wr!==null&&wr<45?'var(--red)':'var(--purple)';
  document.getElementById('ov-wrs').textContent=w+'W / '+l+'L';
  document.getElementById('ov-accs').innerHTML=data.map(b=>{
    const ex=(b.exchange||'binance').toLowerCase();
    const bd=`<span class="exch ${ex}">${ex.toUpperCase()}</span>`;
    const p=b.pnl||0;const wb=b.wins||0;const lb=b.losses||0;const tb2=wb+lb;
    const wr2=tb2>0?Math.round(wb/tb2*100):null;
    const ph=b.position?`<div style="padding:8px 12px;background:rgba(56,189,248,.05);border-top:1px solid rgba(56,189,248,.1);
      display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px">
      <span style="color:var(--accent);font-weight:700">${(b.position.symbol||'').replace('USDT','').replace('-USDT','')}/USDT</span>
      <span style="color:var(--muted)">$${fmt(b.position.entry_price||0,2)}</span></div>`:'';
    return`<div class="acc"><div class="acc-h">
      <div class="acc-nm"><span style="font-size:20px">${b.emoji||'🤖'}</span>
      <div><div style="font-size:13px;font-weight:600">${b.name} ${bd}</div>
      <div style="font-size:10px;color:var(--muted);font-family:var(--mono)">${b.active_symbol||'—'}</div></div></div>
      <div class="sp ${b.bot_running?'on':'off'}">${b.bot_running?'● ATIVO':'○ INATIVO'}</div></div>
      <div class="acc-mtr">
        <div class="acc-m"><div class="acc-ml">USDT</div><div class="acc-mv neu">$${fmt(b.usdt||0)}</div></div>
        <div class="acc-m"><div class="acc-ml">PnL</div><div class="acc-mv ${p>0?'pos':p<0?'neg':'neu'}">${p>=0?'+':''}$${p.toFixed(3)}</div></div>
        <div class="acc-m"><div class="acc-ml">WR</div><div class="acc-mv ${wr2!==null&&wr2>=55?'pos':wr2!==null&&wr2<45?'neg':'neu'}">${wr2!==null?wr2+'%':'—'}</div></div>
        <div class="acc-m"><div class="acc-ml">OPS</div><div class="acc-mv neu">${tb2}</div></div>
      </div>${ph}</div>`;}).join('');
  allOps=[];
  data.forEach(b=>{
    (b.trades||[]).forEach(t=>allOps.push({...t,_bot:b.name,_open:false}));
    if(b.position)allOps.push({symbol:b.position.symbol,entry:b.position.entry_price,
      qty:b.position.qty,usdt_used:b.position.usdt_used||0,pnl:0,_bot:b.name,_open:true,time:''});
  });
  allOps.sort((a,b)=>(a.close||a.time||'')>(b.close||b.time||'')?1:-1);
  document.getElementById('ov-cnt').textContent=allOps.length+' operações';
  const ab2=document.querySelector('#view-overview .ot.on');if(ab2)ab2.click();else rops_ov(allOps);}
function initChart(id,a){
  const c=document.getElementById(id);if(!c)return;
  if(charts[id])charts[id].destroy();
  charts[id]=new Chart(c.getContext('2d'),{type:'line',
    data:{labels:[],datasets:[{label:'Acum.',data:[],borderColor:a||'#38bdf8',backgroundColor:(a||'#38bdf8')+'18',
      fill:true,tension:.4,borderWidth:2,pointRadius:0},
      {label:'Op.',data:[],borderColor:'rgba(255,255,255,.15)',fill:false,tension:.4,borderWidth:1,pointRadius:0}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false,
        backgroundColor:'rgba(10,22,40,.95)',borderColor:'rgba(255,255,255,.1)',borderWidth:1,padding:10,cornerRadius:8}},
      scales:{x:{display:false},y:{display:true,grid:{color:'rgba(255,255,255,.04)',drawBorder:false},
        ticks:{color:'#5a7299',font:{size:9},maxTicksLimit:5,callback:v=>'$'+v.toFixed(2)}}}}});}
function upd_bot(b,idx){
  const a=TH[idx%TH.length].a;
  const pe=document.getElementById('v-pnl-'+idx);
  if(pe){pe.textContent=(b.pnl>=0?'+':'')+'$'+Math.abs(b.pnl||0).toFixed(4);
    pe.className='st-v '+(b.pnl>0?'g':b.pnl<0?'r':'');}
  const be=document.getElementById('v-best-'+idx);
  const best=b.trades?.filter(t=>t.pnl>0).sort((a,b)=>b.pnl-a.pnl)[0];
  if(be)be.textContent=best?'+$'+best.pnl.toFixed(4):'—';
  const we2=document.getElementById('v-worst-'+idx);
  const worst=b.trades?.filter(t=>t.pnl<0).sort((a,b)=>a.pnl-b.pnl)[0];
  if(we2)we2.textContent=worst?'-$'+Math.abs(worst.pnl).toFixed(4):'—';
  const tot=(b.wins||0)+(b.losses||0);const wr=tot>0?Math.round(b.wins/tot*100):null;
  const wre=document.getElementById('v-wr-'+idx);
  if(wre){wre.textContent=wr!==null?wr+'%':'—';wre.style.color=wr>=55?'var(--green)':wr!==null&&wr<45?'var(--red)':'var(--text)';}
  const wrs=document.getElementById('v-wrs-'+idx);if(wrs)wrs.textContent=`${b.wins||0}W/${b.losses||0}L`;
  const ue=document.getElementById('v-u-'+idx);if(ue)ue.textContent=b.usdt!=null?'$'+fmt(b.usdt):'—';
  const oe=document.getElementById('v-o-'+idx);if(oe)oe.textContent=(b.total_trades||0)+' ops';
  const pe2=document.getElementById('v-pos-'+idx);if(pe2)pe2.textContent=b.position?b.position.symbol:'NENHUMA';
  const pr=document.getElementById('v-pr-'+idx);if(pr)pr.textContent=b.active_symbol||'—';
  const ind=document.getElementById('ind-'+idx);
  if(ind&&b.rsi!=null){
    const rc=b.rsi<40?'var(--green)':b.rsi>60?'var(--red)':'var(--text)';
    const mc=b.macd_signal==='bullish'?'var(--green)':'var(--red)';
    const bc=b.bb_pct<30?'var(--green)':b.bb_pct>70?'var(--red)':'var(--text)';
    ind.innerHTML=`<div class="indi"><div class="indl">RSI</div><div class="indv" style="color:${rc}">${b.rsi}</div></div>
      <div class="indi"><div class="indl">MACD</div><div class="indv" style="color:${mc}">${(b.macd_signal||'?').slice(0,4).toUpperCase()}</div></div>
      <div class="indi"><div class="indl">BB%</div><div class="indv" style="color:${bc}">${b.bb_pct}%</div></div>
      <div class="indi"><div class="indl">TEND</div><div class="indv" style="color:${b.trend==='alta'?'var(--green)':'var(--red)'}">${b.trend==='alta'?'↑ ALTA':'↓ BAIXA'}</div></div>`;}
  const pos=document.getElementById('pos-'+idx);
  if(pos){if(!b.position){pos.innerHTML='<div class="pe">Aguardando sinal...</div>';}
    else{const p=b.position;const curr=b.price||p.entry_price;
      const pct=p.entry_price>0?((curr-p.entry_price)/p.entry_price*100):0;
      const pnl=(pct/100*p.usdt_used);
      pos.innerHTML=`<div class="pc"><div class="ps">${(p.symbol||'').replace('USDT','').replace('-USDT','')}/USDT</div>
        <div class="pr"><span class="pl">Entrada</span><span class="pv">$${fmt(p.entry_price,4)}</span></div>
        <div class="pr"><span class="pl">Atual</span><span class="pv" style="color:${pct>=0?'var(--green)':'var(--red)'}">$${fmt(curr,4)}</span></div>
        <div class="pr"><span class="pl">PnL</span><span class="pv ${pct>=0?'pp':'pn'}">${pct>=0?'+':''}${pct.toFixed(2)}% / $${Math.abs(pnl).toFixed(4)}</span></div>
        <div class="pr"><span class="pl">Capital</span><span class="pv">$${fmt(p.usdt_used)}</span></div>
        <div class="pr"><span class="pl" style="color:var(--red)">Stop</span><span class="pv" style="color:var(--red)">$${fmt(p.entry_price*(1-b.stop_loss),4)}</span></div>
        <div class="pr"><span class="pl" style="color:var(--green)">Target</span><span class="pv" style="color:var(--green)">$${fmt(p.entry_price*(1+b.take_profit),4)}</span></div>
      </div>`;}}
  const sc=document.getElementById('sc-'+idx);
  if(sc&&b.scanner?.length){const mx=Math.max(...b.scanner.map(s=>s.score),1);
    sc.innerHTML=b.scanner.map(s=>{const be2=s.symbol===b.active_symbol;const cc=s.change>=0?'var(--green)':'var(--red)';
      return`<div class="sc-i"><div class="sc-s ${be2?'best':''}">${be2?'★ ':'  '}${s.symbol}</div>
        <div class="sc-bw"><div class="sc-b" style="width:${(s.score/mx*100).toFixed(0)}%"></div></div>
        <div class="sc-sc">${s.score}</div><div class="sc-ch" style="color:${cc}">${s.change>=0?'+':''}${s.change}%</div>
      </div>`;}).join('');
    const st2=document.getElementById('sc-ts-'+idx);if(st2)st2.textContent=b.scan_time?b.scan_time.slice(11,19):'—';}
  const lwe=document.getElementById('lw-'+idx);
  if(lwe&&b.logs?.length){const lce=document.getElementById('lc-'+idx);if(lce)lce.textContent=b.logs.length+' linhas';
    const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    lwe.innerHTML=b.logs.slice(-100).reverse().map(l=>{let c='ll';
      if(l.includes('Comprado'))c+=' buy';else if(l.includes('Fechado'))c+=' sell';
      else if(l.includes('Scanner')||l.includes('Melhor:'))c+=' scan';
      else if(l.includes('[IA]')||l.includes('[OKX]'))c+=' ia';
      else if(l.includes('[TOR]')||l.includes('WARNING'))c+=' warn';
      else if(l.includes('ERROR'))c+=' err';
      return`<div class="${c}">${esc(l)}</div>`;}).join('');}
  const pg=document.getElementById('pg-'+idx);
  if(pg){const bp={};(b.trades||[]).forEach(t=>{const p=t.symbol||'?';if(!bp[p])bp[p]={pnl:0,cnt:0};bp[p].pnl+=t.pnl||0;bp[p].cnt++;});
    const ps=Object.entries(bp).sort((a,b)=>b[1].pnl-a[1].pnl);
    pg.innerHTML=ps.length?ps.map(([s,d])=>`<div class="pgi"><div style="font-family:var(--mono);font-size:11px;font-weight:700;color:var(--accent);margin-bottom:3px">${s.replace('USDT','').replace('-USDT','')}</div>
      <div style="font-family:var(--mono);font-size:12px;font-weight:700;color:${d.pnl>=0?'var(--green)':'var(--red)'}">${d.pnl>=0?'+':''}$${d.pnl.toFixed(4)}</div>
      <div style="font-size:10px;color:var(--muted)">${d.cnt} op${d.cnt!==1?'s':''}</div></div>`).join(''):'<div style="color:var(--muted);font-size:12px">Sem dados</div>';}
  const ta=document.getElementById('tg-a-'+idx);if(ta)ta.checked=b.tg_ativo!==false;
  const gr=document.getElementById('ng-'+idx);if(gr)gr.style.opacity=b.tg_ativo!==false?'1':'0.4';
  const ts=document.getElementById('tg-st-'+idx);
  if(ts)ts.textContent=`${(b.exchange||'binance').toUpperCase()} | ${b.tg_token?(b.tg_ativo!==false?'✓ Telegram':'⏸ Pausado'):'✗ Sem token'}`;
  if(b.notif_cfg)Object.keys(NT).forEach(k=>{const el=document.getElementById(`nf-${idx}-${k}`);if(el)el.checked=b.notif_cfg[k]!==false;});
  if(charts['ch-'+idx]){let ac=0;const tr=b.trades||[];
    charts['ch-'+idx].data.labels=tr.map((_,i)=>'#'+(i+1));
    charts['ch-'+idx].data.datasets[0].data=tr.map(t=>{ac+=t.pnl||0;return+ac.toFixed(4);});
    charts['ch-'+idx].data.datasets[1].data=tr.map(t=>t.pnl||0);
    charts['ch-'+idx].update('none');}
  const bsort=document.getElementById('bops-'+idx);
  if(bsort){const tr=bots[idx]?.trades||[];
    bsort.innerHTML=!tr.length?'<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:20px">Nenhuma operação ainda</td></tr>':
    [...tr].reverse().map((t,i)=>{const pct=t.usdt_used>0?(t.pnl/t.usdt_used*100).toFixed(2)+'%':'—';const c=t.pnl>=0?'pp':'pn';
      return`<tr><td style="color:var(--muted)">${tr.length-i}</td>
        <td><span class="bk bsym">${(t.symbol||'').replace('USDT','').replace('-USDT','')}</span></td>
        <td>$${fmt(t.entry||0,4)}</td><td>${t.exit>0?'$'+fmt(t.exit,4):'<span style="color:var(--amber)">aberta</span>'}</td>
        <td style="color:var(--muted)">${t.qty||'—'}</td><td style="color:var(--muted)">$${fmt(t.usdt_used||0)}</td>
        <td class="${c}">${t.pnl>=0?'+':''}$${(t.pnl||0).toFixed(4)}</td><td class="${c}">${pct}</td>
        <td>${rb(t.reason)}</td><td style="color:var(--muted);font-size:10px">${(t.close||'').slice(0,16)}</td></tr>`;}).join('');}}
function bvw(b,idx){
  const ne=Object.entries(NT).map(([k,info])=>`
    <div class="ni"><div><div class="nl">${info.l}</div><div class="nd2">${info.d}</div></div>
      <label class="tg"><input type="checkbox" id="nf-${idx}-${k}" onchange="sn(${idx})">
      <div class="tg-t"></div><div class="tg-k"></div></label></div>`).join('');
  return`<div id="view-bot${idx}" class="view" style="display:flex;flex-direction:column;gap:14px;padding:20px 24px">
    <div class="sts">
      <div class="st"><div class="st-l">PNL TOTAL</div><div class="st-v" id="v-pnl-${idx}">$0.0000</div></div>
      <div class="st g"><div class="st-l">MELHOR OP</div><div class="st-v g" id="v-best-${idx}">—</div></div>
      <div class="st r"><div class="st-l">PIOR OP</div><div class="st-v r" id="v-worst-${idx}">—</div></div>
      <div class="st"><div class="st-l">WIN RATE</div><div class="st-v" id="v-wr-${idx}">—</div><div class="st-s" id="v-wrs-${idx}">0W/0L</div></div>
      <div class="st b"><div class="st-l">SALDO USDT</div><div class="st-v b" id="v-u-${idx}">—</div><div class="st-s" id="v-o-${idx}">0 ops</div></div>
      <div class="st"><div class="st-l">POSIÇÃO</div><div class="st-v" id="v-pos-${idx}">NENHUMA</div></div>
    </div>
    <div id="ind-${idx}" class="indr"></div>
    <div class="mid">
      <div class="card"><div class="ch"><div class="ct">PNL ACUMULADO</div><div class="ct" id="v-pr-${idx}" style="color:var(--accent)">—</div></div>
        <div class="cw"><canvas id="ch-${idx}"></canvas></div></div>
      <div class="card"><div class="ct" style="margin-bottom:10px">POSIÇÃO ABERTA</div>
        <div id="pos-${idx}"><div class="pe">Aguardando sinal...</div></div></div>
    </div>
    <div class="oc">
      <div class="oh"><div class="ct">OPERAÇÕES</div>
        <div class="otabs"><button class="ot on" onclick="fbo(${idx},'all',this)">TODAS</button>
          <button class="ot" onclick="fbo(${idx},'win',this)">GANHOS</button>
          <button class="ot" onclick="fbo(${idx},'loss',this)">PERDAS</button></div></div>
      <div class="tw"><table>
        <thead><tr><th>#</th><th>PAR</th><th>ENTRADA</th><th>SAÍDA</th><th>QTD</th><th>CAPITAL</th><th>PNL</th><th>%</th><th>MOTIVO</th><th>DATA/HORA</th></tr></thead>
        <tbody id="bops-${idx}"></tbody></table></div></div>
    <div class="card"><div class="ch"><div class="ct">DESEMPENHO POR PAR</div></div><div class="pg" id="pg-${idx}"></div></div>
    <div class="br">
      <div class="card"><div class="ch"><div class="ct">SCANNER</div><div class="ct" id="sc-ts-${idx}" style="color:var(--muted)">—</div></div><div id="sc-${idx}"></div></div>
      <div class="card"><div class="ch"><div class="ct">LOG EM TEMPO REAL</div><div class="ct" id="lc-${idx}" style="color:var(--muted)">0 linhas</div></div><div class="lw" id="lw-${idx}"></div></div>
    </div>
    <div class="np"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <div class="ct">NOTIFICAÇÕES TELEGRAM</div>
        <div style="display:flex;align-items:center;gap:10px">
          <span style="font-size:11px;color:var(--muted)" id="tg-st-${idx}">—</span>
          <label class="tg"><input type="checkbox" id="tg-a-${idx}" onchange="sta(${idx})">
          <div class="tg-t"></div><div class="tg-k"></div></label></div></div>
      <div class="ng" id="ng-${idx}">${ne}</div>
      <div style="display:flex;align-items:center;margin-top:12px">
        <button class="sv-btn" onclick="sn(${idx})">Salvar</button>
        <span class="sm" id="sm-${idx}">✓ Salvo!</span>
        <span class="sm" id="sm2-${idx}" style="margin-left:8px">✓ Telegram!</span>
      </div></div>
  </div>`;}
function fbo(idx,f,btn){
  document.querySelectorAll(`#view-bot${idx} .ot`).forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');const tr=bots[idx]?.trades||[];
  const tb=document.getElementById('bops-'+idx);if(!tb)return;
  const filtered=f==='all'?tr:tr.filter(t=>f==='win'?t.pnl>=0:t.pnl<0);
  tb.innerHTML=!filtered.length?'<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:20px">Nenhuma operação</td></tr>':
    [...filtered].reverse().map((t,i)=>{const pct=t.usdt_used>0?(t.pnl/t.usdt_used*100).toFixed(2)+'%':'—';const c=t.pnl>=0?'pp':'pn';
      return`<tr><td style="color:var(--muted)">${filtered.length-i}</td>
        <td><span class="bk bsym">${(t.symbol||'').replace('USDT','').replace('-USDT','')}</span></td>
        <td>$${fmt(t.entry||0,4)}</td><td>${t.exit>0?'$'+fmt(t.exit,4):'<span style="color:var(--amber)">aberta</span>'}</td>
        <td style="color:var(--muted)">${t.qty||'—'}</td><td style="color:var(--muted)">$${fmt(t.usdt_used||0)}</td>
        <td class="${c}">${t.pnl>=0?'+':''}$${(t.pnl||0).toFixed(4)}</td><td class="${c}">${pct}</td>
        <td>${rb(t.reason)}</td><td style="color:var(--muted);font-size:10px">${(t.close||'').slice(0,16)}</td></tr>`;}).join('');}
async function sta(idx){
  const a=document.getElementById('tg-a-'+idx)?.checked;
  await fetch('/api/tg_ativo/'+idx,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ativo:a})});
  const g=document.getElementById('ng-'+idx);if(g)g.style.opacity=a?'1':'0.4';
  const m=document.getElementById('sm2-'+idx);if(m){m.style.display='inline';setTimeout(()=>m.style.display='none',2e3);}}
async function sn(idx){
  const cfg={};Object.keys(NT).forEach(k=>{const el=document.getElementById(`nf-${idx}-${k}`);if(el)cfg[k]=el.checked;});
  await fetch('/api/notif/'+idx,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
  const m=document.getElementById('sm-'+idx);if(m){m.style.display='inline';setTimeout(()=>m.style.display='none',2e3);}}
async function sendReport(){
  const btn=document.getElementById('btn-rep');btn.textContent='Enviando...';btn.disabled=true;
  try{const r=await fetch('/api/report/send',{method:'POST'});const d=await r.json();
    const el=document.getElementById('rr');el.style.display='block';el.textContent=d.msg||JSON.stringify(d);
    btn.textContent='✓ Enviado!';}catch(e){document.getElementById('rr').textContent='Erro: '+e;btn.textContent='Erro';}
  setTimeout(()=>{btn.textContent='📊 Enviar Agora';btn.disabled=false;},3e3);}
async function showReport(){
  const r=await fetch('/api/report/preview');const d=await r.json();
  const el=document.getElementById('rr');el.style.display='block';el.textContent=d.text||'Erro';}
async function refresh(){
  try{
    const data=await fetch('/api/bots').then(r=>r.json());
    const nav=document.getElementById('nav');const panels=document.getElementById('panels');
    if(nav.children.length<=1){
      data.forEach((b,i)=>{
        const ex=(b.exchange||'binance').toLowerCase();
        const bd=ex==='okx'?'<span class="exch okx">OKX</span>':'<span class="exch bnb">BNB</span>';
        const btn=document.createElement('button');
        btn.className='nav-tab';btn.id='nb-'+i;btn.onclick=()=>sv('bot'+i,btn);
        btn.innerHTML=`<div class="nd ${b.bot_running?'on':''}"></div>${b.emoji||'🤖'} ${b.name} ${bd}`;
        nav.appendChild(btn);
        const div=document.createElement('div');div.innerHTML=bvw(b,i);panels.appendChild(div.firstChild||div);});
      const br=document.createElement('button');br.className='nav-tab';br.onclick=()=>sv('relatorio',br);
      br.innerHTML='📊 Relatório';nav.appendChild(br);
      const rd=document.createElement('div');
      rd.innerHTML=`<div id="view-relatorio" class="view" style="padding:20px 24px">
        <div class="rc"><div class="rt">Relatório Diário</div>
          <div class="rs">Enviado automaticamente às 22h00 via Telegram</div>
          <button class="rb2 g" id="btn-rep" onclick="sendReport()">📊 Enviar Agora</button>
          <button class="rb2" onclick="showReport()">👁 Pré-visualizar</button>
          <div class="rr" id="rr"></div></div>
        <div class="rc"><div class="rt">Comandos via Telegram</div>
          <div class="rs">Envie no chat do Telegram para controlar os bots</div>
          <div class="cl">
            <div class="ci"><span class="cc">/status</span><span class="cd">Status de todos os bots</span></div>
            <div class="ci"><span class="cc">/relatorio</span><span class="cd">Relatório completo do dia</span></div>
            <div class="ci"><span class="cc">/saldo</span><span class="cd">Saldo de todas as contas</span></div>
            <div class="ci"><span class="cc">/ops</span><span class="cd">Últimas 5 operações</span></div>
            <div class="ci"><span class="cc">/scanner</span><span class="cd">Último scan de mercado</span></div>
            <div class="ci"><span class="cc">/pausar N</span><span class="cd">Pausa notificações do Bot N</span></div>
            <div class="ci"><span class="cc">/ativar N</span><span class="cd">Ativa notificações do Bot N</span></div>
          </div></div></div>`;
      panels.appendChild(rd.firstChild||rd);
      setTimeout(()=>data.forEach((_,i)=>initChart('ch-'+i,TH[i%TH.length].a)),100);}
    data.forEach((b,i)=>{
      const btn2=document.getElementById('nb-'+i);
      if(btn2){const ex=(b.exchange||'binance').toLowerCase();
        const bd=ex==='okx'?'<span class="exch okx">OKX</span>':'<span class="exch bnb">BNB</span>';
        btn2.innerHTML=`<div class="nd ${b.bot_running?'on':''}"></div>${b.emoji||'🤖'} ${b.name} ${bd}`;}
      bots[i]=b;upd_bot(b,i);});
    upd_ov(data);
    const ao=data.some(b=>b.bot_running);
    const ld=document.getElementById('live-dot');if(ld)ld.className='live '+(ao?'on':'');
    const st=document.getElementById('bot-st');
    if(st){st.textContent=ao?data.filter(b=>b.bot_running).length+' bot(s) ativo(s)':'INATIVO';st.className='bot-st '+(ao?'on':'');}
  }catch(e){const st=document.getElementById('bot-st');if(st)st.textContent='ERRO';}}
async function refreshTicker(){
  const pairs=['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT'];
  for(const sym of pairs){
    try{const d=await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol='+sym).then(r=>r.json());
      const el=document.getElementById('tick-'+sym);if(!el)continue;
      const p=parseFloat(d.lastPrice),c=parseFloat(d.priceChangePercent);
      const fp=p>1000?'$'+p.toLocaleString('pt-BR',{minimumFractionDigits:2}):p>10?'$'+p.toFixed(2):'$'+p.toFixed(4);
      el.querySelector('.ti-p').textContent=fp;
      const ce=el.querySelector('.ti-c');ce.textContent=(c>=0?'+':'')+c.toFixed(2)+'%';ce.className='ti-c '+(c>=0?'up':'dn');
    }catch(e){}}  }
setInterval(()=>{const e=document.getElementById('clk');if(e)e.textContent=new Date().toLocaleTimeString('pt-BR');},1e3);
refresh();refreshTicker();setInterval(refresh,5e3);setInterval(refreshTicker,1e4);
</script></body></html>"""



# ── Parser do log ─────────────────────────────────────────────────────────────

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
