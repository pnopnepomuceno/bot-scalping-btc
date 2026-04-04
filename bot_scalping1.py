"""
ScalpBot Multi-Conta — Binance Spot + IA (Claude)
Suporta múltiplas contas Binance com estratégias independentes.

Configuração via .env:
  BOT_1_NAME=Conta Principal
  BOT_1_BINANCE_KEY=...
  BOT_1_BINANCE_SECRET=...
  BOT_1_ANTHROPIC_KEY=...
  BOT_1_TELEGRAM_TOKEN=...
  BOT_1_TELEGRAM_CHAT=...
  BOT_1_PAIRS=BTCUSDT,ETHUSDT
  BOT_1_TRADE_PCT=0.90
  BOT_1_STOP_LOSS=0.005
  BOT_1_TAKE_PROFIT=0.010
  BOT_1_MIN_CONFIDENCE=60
  BOT_1_SCORE_PARA_IA=2
  BOT_1_LOOP_SECONDS=180
  BOT_1_TESTNET=false

  BOT_2_NAME=Conta Agressiva
  BOT_2_BINANCE_KEY=...
  ... (mesmas chaves com prefixo BOT_2_)

  BOT_COUNT=2  (quantas contas rodar)
"""

import os, time, logging, json, threading
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import anthropic

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# ── Utilitários ───────────────────────────────────────────────────────────────

def setup_logger(name: str, log_file: str) -> logging.Logger:
    fmt = logging.Formatter(f"%(asctime)s [{name}] [%(levelname)s] %(message)s")
    fh  = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    sh  = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


# Tipos de notificação Telegram
NOTIFY_TYPES = {
    "inicio":      "notify_inicio",      # bot iniciado
    "compra":      "notify_compra",      # ordem de compra executada
    "venda":       "notify_venda",       # ordem de venda executada
    "stop_loss":   "notify_stop_loss",   # stop-loss atingido
    "take_profit": "notify_take_profit", # take-profit atingido
    "par_troca":   "notify_par_troca",   # scanner trocou de par
    "ia_erro":     "notify_ia_erro",     # erro na API da IA
    "resumo":      "notify_resumo",      # resumo ao encerrar
}

def send_telegram(token: str, chat_id: str, msg: str, log):
    if not token or not chat_id:
        return
    try:
        import requests
        r = requests.post(
            f"https://api.telegram.org/bot{token.strip()}/sendMessage",
            json={"chat_id": chat_id.strip(), "text": msg}, timeout=10
        )
        if not r.json().get("ok"):
            log.warning(f"Telegram: {r.text}")
    except Exception as e:
        log.warning(f"Telegram erro: {e}")


# ── Indicadores ───────────────────────────────────────────────────────────────

def get_klines(client, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
    raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df  = pd.DataFrame(raw, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_vol","trades","taker_buy_base","taker_buy_quote","ignore"
    ])
    for col in ["close","high","low","open","volume"]:
        df[col] = df[col].astype(float)

    delta = df["close"].diff()
    avg_g = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    avg_l = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
    df["rsi"] = 100 - (100 / (1 + avg_g / avg_l))

    df["ema9"]  = df["close"].ewm(span=9,  adjust=False).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"]   = ema12 - ema26
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"]   = df["macd"] - df["signal"]

    sma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    df["bb_up"]  = sma20 + 2 * std20
    df["bb_low"] = sma20 - 2 * std20
    df["bb_mid"] = sma20

    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).ewm(com=13, adjust=False).mean()
    return df


def get_indicators(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    prev = df.iloc[-2]
    trend = "alta" if last["close"] > last["ema50"] else "baixa"
    if   last["ema9"] > last["ema21"] and prev["ema9"] <= prev["ema21"]: ema_cross = "cruzamento_alta"
    elif last["ema9"] < last["ema21"] and prev["ema9"] >= prev["ema21"]: ema_cross = "cruzamento_baixa"
    elif last["ema9"] > last["ema21"]:                                    ema_cross = "acima_bullish"
    else:                                                                  ema_cross = "abaixo_bearish"
    bb_range = last["bb_up"] - last["bb_low"]
    bb_pct   = (last["close"] - last["bb_low"]) / bb_range * 100 if bb_range > 0 else 50
    return {
        "price": round(last["close"], 6), "trend": trend,
        "rsi": round(last["rsi"], 2), "ema_cross": ema_cross,
        "macd_hist": round(last["hist"], 6),
        "macd_signal": "bullish" if last["hist"] > 0 else "bearish",
        "bb_upper": round(last["bb_up"], 6), "bb_lower": round(last["bb_low"], 6),
        "bb_mid": round(last["bb_mid"], 6), "bb_pct": round(bb_pct, 1),
        "atr": round(last["atr"], 6),
    }


def calcular_score(ind: dict, position) -> tuple:
    rsi  = ind["rsi"]; ema = ind["ema_cross"]
    macd = ind["macd_signal"]; hist = ind["macd_hist"]; bb = ind["bb_pct"]
    buy  = sum([rsi<42, ema in("cruzamento_alta","acima_bullish"), macd=="bullish" and hist>0, bb<40])
    sell = sum([rsi>58, ema in("cruzamento_baixa","abaixo_bearish"), macd=="bearish" and hist<0, bb>60])
    return (sell, "SELL") if position else (buy, "BUY")


def score_pair(client, symbol: str, min_volume: float = 50_000_000) -> dict:
    try:
        t  = client.get_ticker(symbol=symbol)
        vol = float(t["quoteVolume"])
        if vol < min_volume: return None
        chg   = float(t["priceChangePercent"])
        high  = float(t["highPrice"]); low = float(t["lowPrice"])
        volat = ((high - low) / low) * 100
        score = min(volat*10,40) + min(vol/1_000_000_000*30,30) + max(0,30-abs(chg)*2)
        return {"symbol":symbol,"price":float(t["lastPrice"]),"change":round(chg,2),
                "volume":round(vol/1_000_000,1),"volatility":round(volat,2),"score":round(score,1)}
    except: return None


def scan_best_pair(client, pairs: list, log) -> dict:
    results = [r for r in [score_pair(client, p) for p in pairs] if r]
    if not results: return {"symbol": pairs[0], "score": 0}
    results.sort(key=lambda x: x["score"], reverse=True)
    best = results[0]
    log.info("── Scanner ──────────────────────────────")
    for r in results:
        m = "★" if r["symbol"] == best["symbol"] else " "
        log.info(f"{m} {r['symbol']:<10} | Score:{r['score']:5.1f} | Vol:{r['volume']:6.0f}M | Var:{r['change']:+5.2f}% | Volat:{r['volatility']:.2f}%")
    log.info(f"Melhor: {best['symbol']}")
    return best


def fallback_tecnico(ind: dict, usdt: float, position, min_usdt: float) -> dict:
    score, tipo = calcular_score(ind, position)
    rsi = ind["rsi"]; bb = ind["bb_pct"]
    if tipo == "SELL" and score >= 3 and position:
        return {"action":"SELL","reason":f"[FB] RSI={rsi} BB={bb}%","confidence":score*20}
    if tipo == "BUY" and score >= 3 and usdt >= min_usdt:
        return {"action":"BUY","reason":f"[FB] RSI={rsi} BB={bb}%","confidence":score*20}
    return {"action":"WAIT","reason":f"[FB] score={score}/4","confidence":0}


def ask_ia(ai_client, symbol: str, ind: dict, usdt: float, position,
           score_para_ia: int, min_usdt: float, ai_calls: dict,
           max_calls: int, log) -> dict:
    score, tipo = calcular_score(ind, position)
    hoje = datetime.now().strftime("%Y-%m-%d")
    if ai_calls["data"] != hoje:
        ai_calls.update({"count":0,"data":hoje})
        log.info("[IA] Contador diário resetado.")
    if score < score_para_ia:
        log.info(f"[ECON] Score={score}/4 < {score_para_ia} — fallback (0 tokens)")
        return fallback_tecnico(ind, usdt, position, min_usdt)
    if ai_calls["count"] >= max_calls:
        log.warning(f"[ECON] Limite {max_calls} atingido — fallback.")
        return fallback_tecnico(ind, usdt, position, min_usdt)

    pos_info = "sem posicao"
    if position:
        pct = (ind["price"] - position["entry_price"]) / position["entry_price"] * 100
        pos_info = f"comprado@${position['entry_price']:,.2f} PnL:{pct:+.1f}%"

    prompt = (
        f"Scalping {symbol} 1min. RSI:{ind['rsi']} EMA:{ind['ema_cross'][:3]} "
        f"MACD:{ind['macd_signal'][:4]}({ind['macd_hist']:+.5f}) BB:{ind['bb_pct']}% "
        f"USDT:{usdt:.0f} {pos_info}. Score_{tipo}:{score}/4. "
        'JSON:{"action":"BUY|SELL|WAIT","reason":"max 8 palavras","confidence":0-100}'
    )
    model = "claude-sonnet-4-20250514" if score >= 3 else "claude-haiku-4-5-20251001"
    try:
        resp = ai_client.messages.create(
            model=model, max_tokens=60,
            messages=[{"role":"user","content":prompt}]
        )
        ai_calls["count"] += 1
        custo = 0.003 if "sonnet" in model else 0.00025
        log.info(f"[IA] {model.split('-')[1]} score={score} #={ai_calls['count']} ~${custo:.5f}")
        text = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        log.error(f"Erro IA: {e}")
        return fallback_tecnico(ind, usdt, position, min_usdt)


def get_symbol_precision(client, symbol: str) -> int:
    info = client.get_symbol_info(symbol)
    for f in info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step = f["stepSize"].rstrip("0")
            return len(step.split(".")[-1]) if "." in step else 0
    return 5


# ── Classe principal de cada bot ──────────────────────────────────────────────

class ScalpBot:
    def __init__(self, cfg: dict):
        self.name        = cfg["name"]
        self.pairs       = cfg["pairs"]
        self.trade_pct   = cfg["trade_pct"]
        self.stop_loss   = cfg["stop_loss"]
        self.take_profit = cfg["take_profit"]
        self.min_conf    = cfg["min_confidence"]
        self.score_ia    = cfg["score_para_ia"]
        self.loop_base   = cfg["loop_seconds"]
        self.loop_signal = max(60, cfg["loop_seconds"] // 3)
        self.min_usdt    = cfg.get("min_usdt", 10.0)
        self.scan_interval = cfg.get("scan_interval", 3)
        self.tg_token    = cfg["telegram_token"]
        self.tg_chat     = cfg["telegram_chat"]
        self.testnet     = cfg["testnet"]
        # Controle granular de notificações
        self.notify_cfg  = {k: cfg.get(v, True) for k,v in NOTIFY_TYPES.items()}
        # Cor/emoji do bot para identificação no Telegram
        self.bot_emoji   = cfg.get("emoji", "🤖")

        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"bot_{self.name.lower().replace(' ','_')}.log"
        )
        self.log = setup_logger(self.name, log_file)

        self.binance = Client(cfg["binance_key"], cfg["binance_secret"])
        self.ai      = anthropic.Anthropic(api_key=cfg["anthropic_key"])

        self.state = {
            "position": None, "active_symbol": None,
            "trades": [], "pnl": 0.0, "wins": 0, "losses": 0,
        }
        self.ai_calls = {"count": 0, "data": ""}
        self.cycle    = 0

    def notify(self, msg: str, tipo: str = None):
        self.log.info(msg)
        # Verifica se este tipo de notificação está ativado
        if tipo and not self.notify_cfg.get(tipo, True):
            return
        prefixo = f"{self.bot_emoji} [{self.name}]\n"
        send_telegram(self.tg_token, self.tg_chat, prefixo + msg, self.log)

    def get_balances(self) -> dict:
        info = self.binance.get_account()
        return {b["asset"]: float(b["free"]) for b in info["balances"] if float(b["free"]) > 0}

    def check_exit(self, price: float):
        pos = self.state["position"]
        if not pos: return
        pct = (price - pos["entry_price"]) / pos["entry_price"]
        if pct <= -self.stop_loss:
            self.notify(f"🔴 Stop-loss {pct*100:.2f}% | {pos['symbol']} ${price:,.4f}", tipo="stop_loss")
            self.close_position(price, "STOP_LOSS")
        elif pct >= self.take_profit:
            self.notify(f"🟢 Take-profit {pct*100:.2f}% | {pos['symbol']} ${price:,.4f}", tipo="take_profit")
            self.close_position(price, "TAKE_PROFIT")

    def place_order(self, symbol: str, side: str, qty: float, price: float):
        if self.testnet:
            self.notify(f"[SIM] {side} {qty} {symbol} @ ${price:,.4f}")
            return {"status":"SIMULATED"}
        try:
            precision = get_symbol_precision(self.binance, symbol)
            qty_str   = f"{qty:.{precision}f}"
            if side == "BUY":
                order = self.binance.order_market_buy(symbol=symbol, quantity=qty_str)
            else:
                # Verifica saldo antes de vender
                bals = self.get_balances()
                asset = symbol.replace("USDT","")
                available = bals.get(asset, 0.0)
                qty_real = min(float(qty_str), available)
                if qty_real < 10 ** (-precision):
                    self.log.warning(f"Saldo insuficiente para SELL {symbol}: {available}")
                    return None
                qty_str = f"{qty_real:.{precision}f}"
                order = self.binance.order_market_sell(symbol=symbol, quantity=qty_str)
            emoji = "🟢" if side == "BUY" else "🔴"
            self.notify(f"{emoji} {side} {qty_str} {symbol} @ ~${price:,.4f}")
            return order
        except BinanceAPIException as e:
            self.notify(f"❌ Erro {side} {symbol}: {e}")
            return None

    def open_buy(self, symbol: str, price: float, reason: str, usdt: float):
        amount = usdt * self.trade_pct
        if amount < self.min_usdt:
            self.log.info(f"USDT insuficiente: ${amount:.2f}")
            return
        precision = get_symbol_precision(self.binance, symbol)
        qty   = round(amount / price, precision)
        order = self.place_order(symbol, "BUY", qty, price)
        if order:
            self.state["position"] = {
                "symbol": symbol, "side": "BUY",
                "entry_price": price, "qty": qty,
                "usdt_used": amount, "time": datetime.now().isoformat(),
            }
            self.notify(f"📈 Comprado {qty} {symbol} @ ${price:,.4f} (${amount:.2f})\n{reason}", tipo="compra")

    def close_position(self, price: float, reason: str):
        pos = self.state["position"]
        if not pos: return
        order = self.place_order(pos["symbol"], "SELL", pos["qty"], price)
        if order:
            pct = (price - pos["entry_price"]) / pos["entry_price"]
            pnl = pct * pos["usdt_used"]
            self.state["pnl"] += pnl
            if pnl >= 0: self.state["wins"] += 1
            else:        self.state["losses"] += 1
            total = self.state["wins"] + self.state["losses"]
            wr = round(self.state["wins"] / total * 100, 1) if total > 0 else 0
            self.state["trades"].append({
                "symbol": pos["symbol"], "entry": pos["entry_price"],
                "exit": price, "pnl": round(pnl,4), "qty": pos["qty"],
                "usdt_used": pos["usdt_used"],
                "close": datetime.now().isoformat(), "reason": reason,
            })
            self.notify(
                f"{'✅' if pnl>=0 else '❌'} Fechado {pos['symbol']} ({reason})\n"
                f"PnL: ${pnl:+.4f} | Total: ${self.state['pnl']:+.4f} | WR: {wr}%",
                tipo="venda"
            )
            self.state["position"] = None

    def run(self):
        self.notify(f"🤖 Bot '{self.name}' iniciado!", tipo="inicio")
        self.notify(
            f"Pares: {', '.join(self.pairs)}\n"
            f"Modo: {'SIMULAÇÃO' if self.testnet else '⚠️ REAL'} | "
            f"Stop:{self.stop_loss*100}% | TP:{self.take_profit*100}%"
        )
        while True:
            try:
                balances = self.get_balances()
                usdt     = balances.get("USDT", 0.0)
                self.cycle += 1

                if self.cycle == 1 or self.cycle % self.scan_interval == 0:
                    if not self.state["position"]:
                        best = scan_best_pair(self.binance, self.pairs, self.log)
                        if best["symbol"] != self.state["active_symbol"]:
                            old = self.state["active_symbol"]
                            self.state["active_symbol"] = best["symbol"]
                            if old:
                                self.notify(f"🔄 Par: {old} → {best['symbol']} (score:{best.get('score',0):.1f})", tipo="par_troca")

                symbol = (self.state["position"]["symbol"]
                          if self.state["position"]
                          else self.state["active_symbol"] or self.pairs[0])

                df  = get_klines(self.binance, symbol, Client.KLINE_INTERVAL_1MINUTE)
                ind = get_indicators(df)
                price = ind["price"]

                self.log.info(
                    f"[{symbol}] ${price:,.4f} | RSI:{ind['rsi']} | "
                    f"Tend:{ind['trend']} | MACD:{ind['macd_signal']} | "
                    f"BB:{ind['bb_pct']}% | USDT:{usdt:.2f}"
                )

                if self.state["position"]:
                    self.check_exit(price)

                decision = ask_ia(
                    self.ai, symbol, ind, usdt, self.state["position"],
                    self.score_ia, self.min_usdt, self.ai_calls,
                    150, self.log
                )
                action = decision.get("action","WAIT")
                reason = decision.get("reason","")
                conf   = decision.get("confidence",0)
                self.log.info(f"→ {action} ({conf}%) | {reason}")

                if action == "BUY" and conf >= self.min_conf:
                    if self.state["position"]: self.log.info("Posição já aberta.")
                    elif usdt >= self.min_usdt: self.open_buy(symbol, price, reason, usdt)
                    else: self.log.info(f"USDT insuficiente: ${usdt:.2f}")

                elif action == "SELL" and conf >= self.min_conf:
                    if self.state["position"]: self.close_position(price, reason)
                    else: self.log.info("SELL: sem posição aberta.")

                else:
                    self.log.info("Aguardando...")

                score_pre, _ = calcular_score(ind, self.state["position"])
                sleep = self.loop_signal if score_pre >= self.score_ia or self.state["position"] else self.loop_base
                time.sleep(sleep)

            except KeyboardInterrupt:
                self.notify("⛔ Bot encerrado.", tipo="resumo")
                break
            except Exception as e:
                self.log.error(f"Erro: {e}")
                time.sleep(15)


# ── Carrega configurações e inicia bots ───────────────────────────────────────

def load_bot_config(prefix: str) -> dict:
    def g(key, default=""): return os.getenv(f"{prefix}_{key}", default)
    pairs_raw = g("PAIRS","BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT")
    return {
        "name":           g("NAME", prefix),
        "emoji":          g("EMOJI", "🤖"),
        "binance_key":    g("BINANCE_KEY"),
        "binance_secret": g("BINANCE_SECRET"),
        "anthropic_key":  g("ANTHROPIC_KEY"),
        "telegram_token": g("TELEGRAM_TOKEN"),
        "telegram_chat":  g("TELEGRAM_CHAT"),
        "pairs":          [p.strip() for p in pairs_raw.split(",")],
        "trade_pct":      float(g("TRADE_PCT","0.90")),
        "stop_loss":      float(g("STOP_LOSS","0.005")),
        "take_profit":    float(g("TAKE_PROFIT","0.010")),
        "min_confidence": int(g("MIN_CONFIDENCE","60")),
        "score_para_ia":  int(g("SCORE_PARA_IA","2")),
        "loop_seconds":   int(g("LOOP_SECONDS","180")),
        "min_usdt":       float(g("MIN_USDT","10.0")),
        "scan_interval":  int(g("SCAN_INTERVAL","3")),
        "testnet":        g("TESTNET","false").lower() == "true",
        # Notificações granulares (true/false por tipo)
        "notify_inicio":      g("NOTIFY_INICIO","true").lower()=="true",
        "notify_compra":      g("NOTIFY_COMPRA","true").lower()=="true",
        "notify_venda":       g("NOTIFY_VENDA","true").lower()=="true",
        "notify_stop_loss":   g("NOTIFY_STOP_LOSS","true").lower()=="true",
        "notify_take_profit": g("NOTIFY_TAKE_PROFIT","true").lower()=="true",
        "notify_par_troca":   g("NOTIFY_PAR_TROCA","false").lower()=="true",
        "notify_ia_erro":     g("NOTIFY_IA_ERRO","false").lower()=="true",
        "notify_resumo":      g("NOTIFY_RESUMO","true").lower()=="true",
    }


if __name__ == "__main__":
    bot_count = int(os.getenv("BOT_COUNT","1"))
    threads   = []

    for i in range(1, bot_count + 1):
        prefix = f"BOT_{i}"
        cfg    = load_bot_config(prefix)
        if not cfg["binance_key"]:
            print(f"[AVISO] {prefix} sem chave Binance — pulando.")
            continue
        bot = ScalpBot(cfg)
        t   = threading.Thread(target=bot.run, name=f"bot-{i}", daemon=True)
        threads.append(t)
        t.start()
        print(f"[OK] Bot {i} '{cfg['name']}' iniciado em thread separada.")
        time.sleep(2)

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Encerrando todos os bots...")
