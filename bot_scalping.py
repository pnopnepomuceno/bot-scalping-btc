"""
Bot de Scalping Multi-Par BTC/ETH/BNB/SOL/XRP + IA (Claude)
Estratégia: Scanner automático seleciona o melhor par a cada ciclo
Requisitos: pip install python-binance anthropic pandas requests python-dotenv
"""

import os
import time
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import anthropic

# ── Configuração ──────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Pares monitorados pelo scanner
WATCH_PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

INTERVAL        = Client.KLINE_INTERVAL_1MINUTE
LOOP_SECONDS    = 180          # ciclo base 3 min (reduz custo 3x vs 60s)
LOOP_SIGNAL     = 60           # ciclo rapido quando ha sinal tecnico
STOP_LOSS_PCT   = 0.005
TAKE_PROFIT_PCT = 0.010
TESTNET         = False
MIN_CONFIDENCE  = 60
TRADE_PCT       = 0.90
MIN_USDT        = 10.0
MIN_VOLUME_24H  = 50_000_000
SCAN_INTERVAL   = 3

# Controle de custo de API
SCORE_PARA_IA   = 2            # score minimo para acionar IA (0-4)
MODEL_HAIKU     = "claude-haiku-4-5-20251001"
MODEL_SONNET    = "claude-sonnet-4-20250514"
MAX_CALLS_DIA   = 150          # limite diario de chamadas IA
_ai_calls       = {"count": 0, "data": ""}

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.log"),
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Clientes ──────────────────────────────────────────────────────────────────
#client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
#ai     = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
import requests
proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
session = requests.Session()
session.proxies.update(proxies)
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, requests_params={"proxies": proxies})

# ── Estado ────────────────────────────────────────────────────────────────────
state = {
    "position":     None,   # {"symbol", "side", "entry_price", "qty", "usdt_used", "time"}
    "active_symbol": None,  # par atualmente selecionado pelo scanner
    "trades":       [],
    "pnl":          0.0,
    "wins":         0,
    "losses":       0,
    "scan_count":   0,
}


# ── Telegram ──────────────────────────────────────────────────────────────────

def send_telegram(msg: str):
    token   = TELEGRAM_TOKEN.strip()
    chat_id = TELEGRAM_CHAT_ID.strip()
    if not token or not chat_id:
        return
    try:
        import requests
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg},
            timeout=10
        )
        if not r.json().get("ok"):
            log.warning(f"Telegram: {r.text}")
    except Exception as e:
        log.warning(f"Telegram erro: {e}")


def notify(msg: str):
    log.info(msg)
    send_telegram(msg)


# ── Saldo ─────────────────────────────────────────────────────────────────────

def get_balances() -> dict:
    info     = client.get_account()
    return {b["asset"]: float(b["free"]) for b in info["balances"] if float(b["free"]) > 0}


def get_usdt(balances: dict) -> float:
    return balances.get("USDT", 0.0)


def get_asset_balance(balances: dict, symbol: str) -> float:
    asset = symbol.replace("USDT", "")
    return balances.get(asset, 0.0)


# ── Scanner de mercado ────────────────────────────────────────────────────────

def score_pair(symbol: str) -> dict:
    """Calcula score de oportunidade de um par (0-100)."""
    try:
        ticker = client.get_ticker(symbol=symbol)
        volume = float(ticker["quoteVolume"])
        change = float(ticker["priceChangePercent"])
        high   = float(ticker["highPrice"])
        low    = float(ticker["lowPrice"])
        last   = float(ticker["lastPrice"])

        if volume < MIN_VOLUME_24H:
            return None

        # Volatilidade (amplitude % entre máx e mín)
        volatility = ((high - low) / low) * 100

        # Score: favorece alta volatilidade + alto volume + variação moderada
        vol_score      = min(volatility * 10, 40)   # até 40 pts
        volume_score   = min(volume / 1_000_000_000 * 30, 30)  # até 30 pts
        # variação entre -5% e +5% é ideal para scalping
        change_score   = max(0, 30 - abs(change) * 2)  # até 30 pts

        score = vol_score + volume_score + change_score

        return {
            "symbol":     symbol,
            "price":      last,
            "change":     round(change, 2),
            "volume":     round(volume / 1_000_000, 1),
            "volatility": round(volatility, 2),
            "score":      round(score, 1),
        }
    except Exception as e:
        log.warning(f"Score {symbol}: {e}")
        return None


def scan_best_pair() -> dict:
    """Escaneia todos os pares e retorna o melhor."""
    results = []
    for symbol in WATCH_PAIRS:
        r = score_pair(symbol)
        if r:
            results.append(r)

    if not results:
        return {"symbol": "BTCUSDT", "score": 0}

    results.sort(key=lambda x: x["score"], reverse=True)
    best = results[0]

    log.info("── Scanner de mercado ──────────────────")
    for r in results:
        marker = "★" if r["symbol"] == best["symbol"] else " "
        log.info(f"{marker} {r['symbol']:<10} | Score:{r['score']:5.1f} | "
                 f"Vol:{r['volume']:6.0f}M | Var:{r['change']:+5.2f}% | Volat:{r['volatility']:.2f}%")
    log.info(f"Melhor par selecionado: {best['symbol']}")

    return best


# ── Indicadores ───────────────────────────────────────────────────────────────

def get_klines(symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
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

    ema12        = df["close"].ewm(span=12, adjust=False).mean()
    ema26        = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"]   = ema12 - ema26
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"]   = df["macd"] - df["signal"]

    sma20        = df["close"].rolling(20).mean()
    std20        = df["close"].rolling(20).std()
    df["bb_up"]  = sma20 + 2 * std20
    df["bb_low"] = sma20 - 2 * std20
    df["bb_mid"] = sma20

    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).ewm(com=13, adjust=False).mean()

    return df


def get_indicators_summary(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    prev = df.iloc[-2]

    trend = "alta" if last["close"] > last["ema50"] else "baixa"

    if   last["ema9"] > last["ema21"] and prev["ema9"] <= prev["ema21"]: ema_cross = "cruzamento_alta"
    elif last["ema9"] < last["ema21"] and prev["ema9"] >= prev["ema21"]: ema_cross = "cruzamento_baixa"
    elif last["ema9"] > last["ema21"]:                                    ema_cross = "acima_bullish"
    else:                                                                 ema_cross = "abaixo_bearish"

    bb_range = last["bb_up"] - last["bb_low"]
    bb_pct   = (last["close"] - last["bb_low"]) / bb_range * 100 if bb_range > 0 else 50

    return {
        "price":       round(last["close"], 6),
        "trend":       trend,
        "rsi":         round(last["rsi"], 2),
        "ema_cross":   ema_cross,
        "macd_hist":   round(last["hist"], 6),
        "macd_signal": "bullish" if last["hist"] > 0 else "bearish",
        "bb_upper":    round(last["bb_up"], 6),
        "bb_lower":    round(last["bb_low"], 6),
        "bb_mid":      round(last["bb_mid"], 6),
        "bb_pct":      round(bb_pct, 1),
        "atr":         round(last["atr"], 6),
    }


# ── IA com controle de custo ─────────────────────────────────────────────────

def calcular_score(indicators: dict, position) -> tuple:
    """Calcula score tecnico de compra ou venda (0-4). Retorna (score, tipo)."""
    rsi  = indicators["rsi"]
    ema  = indicators["ema_cross"]
    macd = indicators["macd_signal"]
    hist = indicators["macd_hist"]
    bb   = indicators["bb_pct"]

    buy_score  = sum([rsi<42, ema in("cruzamento_alta","acima_bullish"), macd=="bullish" and hist>0, bb<40])
    sell_score = sum([rsi>58, ema in("cruzamento_baixa","abaixo_bearish"), macd=="bearish" and hist<0, bb>60])

    if position:
        return sell_score, "SELL"
    return buy_score, "BUY"


def technical_fallback(indicators: dict, usdt: float, position) -> dict:
    score, tipo = calcular_score(indicators, position)
    rsi = indicators["rsi"]
    bb  = indicators["bb_pct"]

    if tipo == "SELL" and score >= 3 and position:
        return {"action":"SELL","reason":f"[FB] RSI={rsi} BB={bb}%","confidence":score*20}
    if tipo == "BUY" and score >= 3 and usdt >= MIN_USDT:
        return {"action":"BUY","reason":f"[FB] RSI={rsi} BB={bb}%","confidence":score*20}
    return {"action":"WAIT","reason":f"[FB] score={score}/4","confidence":0}


def ask_claude(symbol: str, indicators: dict, usdt: float, position) -> dict:
    """Chama a IA somente quando o score tecnico justifica. Economiza ~90% de tokens."""
    global _ai_calls

    # Reseta contador diario
    hoje = datetime.now().strftime("%Y-%m-%d")
    if _ai_calls["data"] != hoje:
        _ai_calls = {"count": 0, "data": hoje}
        log.info(f"[ECON] Novo dia — contador de chamadas IA resetado.")

    # Calcula score tecnico primeiro (sem custo)
    score, tipo = calcular_score(indicators, position)

    # Se score baixo, usa fallback direto (sem chamar IA)
    if score < SCORE_PARA_IA:
        log.info(f"[ECON] Score={score}/4 < {SCORE_PARA_IA} — fallback tecnico (0 tokens)")
        return technical_fallback(indicators, usdt, position)

    # Verifica limite diario
    if _ai_calls["count"] >= MAX_CALLS_DIA:
        log.warning(f"[ECON] Limite diario atingido ({MAX_CALLS_DIA}). Fallback tecnico.")
        return technical_fallback(indicators, usdt, position)

    # Score suficiente — chama IA
    pos_info = "sem posicao"
    if position:
        pct = (indicators["price"] - position["entry_price"]) / position["entry_price"] * 100
        pos_info = f"comprado@${position['entry_price']:,.2f} PnL:{pct:+.1f}%"

    # Prompt ultra-compacto para minimizar tokens de entrada
    prompt = (
        f"Scalping {symbol} 1min. "
        f"RSI:{indicators['rsi']} EMA:{indicators['ema_cross'][:3]} "
        f"MACD:{indicators['macd_signal'][:4]}({indicators['macd_hist']:+.5f}) "
        f"BB:{indicators['bb_pct']}% ATR:{indicators['atr']:.2f} "
        f"USDT:{usdt:.0f} {pos_info}. "
        f"Score_{tipo}:{score}/4. "
        'Responda JSON: {"action":"BUY|SELL|WAIT","reason":"max 8 palavras","confidence":0-100}'
    )

    # Score 2 = Haiku (barato ~$0,00025), score 3-4 = Sonnet (preciso ~$0,003)
    model = MODEL_SONNET if score >= 3 else MODEL_HAIKU

    try:
        resp = ai.messages.create(
            model=model, max_tokens=60,
            messages=[{"role": "user", "content": prompt}]
        )
        _ai_calls["count"] += 1
        custo_est = 0.00025 if model == MODEL_HAIKU else 0.003
        log.info(f"[ECON] IA={model.split('-')[1]} score={score} #dia={_ai_calls['count']} ~${custo_est:.5f}")
        text = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        log.error(f"Erro IA: {e}")
        return technical_fallback(indicators, usdt, position)


# ── Ordens ────────────────────────────────────────────────────────────────────

def get_symbol_precision(symbol: str) -> int:
    """Retorna casas decimais permitidas para quantidade do par."""
    info = client.get_symbol_info(symbol)
    for f in info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step = f["stepSize"].rstrip("0")
            return len(step.split(".")[-1]) if "." in step else 0
    return 5


def place_order(symbol: str, side: str, qty: float, price: float):
    if TESTNET:
        notify(f"[SIM] {side} {qty} {symbol} @ ${price:,.4f}")
        return {"status": "SIMULATED"}
    try:
        precision = get_symbol_precision(symbol)
        qty_str   = f"{qty:.{precision}f}"
        if side == "BUY":
            order = client.order_market_buy(symbol=symbol,  quantity=qty_str)
        else:
            order = client.order_market_sell(symbol=symbol, quantity=qty_str)
        emoji = "🟢" if side == "BUY" else "🔴"
        notify(f"{emoji} {side} {qty_str} {symbol} @ ~${price:,.4f}")
        return order
    except BinanceAPIException as e:
        notify(f"❌ Erro {side} {symbol}: {e}")
        return None


def check_exit(price: float):
    pos = state["position"]
    if not pos:
        return
    pct = (price - pos["entry_price"]) / pos["entry_price"]
    if pct <= -STOP_LOSS_PCT:
        notify(f"🔴 Stop-loss {pct*100:.2f}% | {pos['symbol']} ${price:,.4f}")
        close_position(price, "STOP_LOSS")
    elif pct >= TAKE_PROFIT_PCT:
        notify(f"🟢 Take-profit {pct*100:.2f}% | {pos['symbol']} ${price:,.4f}")
        close_position(price, "TAKE_PROFIT")


def open_buy(symbol: str, price: float, reason: str, usdt: float):
    amount = usdt * TRADE_PCT
    if amount < MIN_USDT:
        log.info(f"USDT insuficiente: ${amount:.2f}")
        return
    precision = get_symbol_precision(symbol)
    qty       = round(amount / price, precision)
    order     = place_order(symbol, "BUY", qty, price)
    if order:
        state["position"] = {
            "symbol": symbol, "side": "BUY",
            "entry_price": price, "qty": qty,
            "usdt_used": amount, "time": datetime.now().isoformat(),
        }
        notify(f"📈 Comprado {qty} {symbol} @ ${price:,.4f} (${amount:.2f} USDT)\n{reason}")


def close_position(price: float, reason: str):
    pos = state["position"]
    if not pos:
        return
    order = place_order(pos["symbol"], "SELL", pos["qty"], price)
    if order:
        pct = (price - pos["entry_price"]) / pos["entry_price"]
        pnl = pct * pos["usdt_used"]
        state["pnl"] += pnl
        if pnl >= 0: state["wins"]   += 1
        else:        state["losses"] += 1
        total = state["wins"] + state["losses"]
        wr    = round(state["wins"] / total * 100, 1) if total > 0 else 0
        state["trades"].append({
            "symbol": pos["symbol"], "entry": pos["entry_price"],
            "exit": price, "pnl": round(pnl, 4),
            "close": datetime.now().isoformat(), "reason": reason,
        })
        notify(
            f"{'✅' if pnl >= 0 else '❌'} Fechado {pos['symbol']} ({reason})\n"
            f"PnL: ${pnl:+.4f} | Total: ${state['pnl']:+.4f} | WR: {wr}%"
        )
        state["position"] = None


# ── Loop principal ─────────────────────────────────────────────────────────────

def run():
    notify("🤖 Bot Scalping Multi-Par iniciado!")
    notify(
        f"Pares: {', '.join(WATCH_PAIRS)}\n"
        f"Modo: {'SIMULAÇÃO' if TESTNET else '⚠️ REAL'} | "
        f"Stop: {STOP_LOSS_PCT*100}% | TP: {TAKE_PROFIT_PCT*100}%"
    )

    ai_failures  = 0
    MAX_FAILURES = 3
    cycle        = 0

    while True:
        try:
            balances = get_balances()
            usdt     = get_usdt(balances)
            cycle   += 1

            # ── Scanner a cada N ciclos ou na inicialização ──────────────────
            if cycle == 1 or cycle % SCAN_INTERVAL == 0:
                if not state["position"]:  # não troca par com posição aberta
                    best = scan_best_pair()
                    if best["symbol"] != state["active_symbol"]:
                        old = state["active_symbol"]
                        state["active_symbol"] = best["symbol"]
                        if old:
                            notify(f"🔄 Par alterado: {old} → {best['symbol']} (score: {best.get('score',0):.1f})")

            symbol = state["position"]["symbol"] if state["position"] else state["active_symbol"] or "BTCUSDT"

            # ── Indicadores do par ativo ─────────────────────────────────────
            df         = get_klines(symbol, INTERVAL)
            indicators = get_indicators_summary(df)
            price      = indicators["price"]

            log.info(
                f"[{symbol}] ${price:,.4f} | RSI:{indicators['rsi']} | "
                f"Tend:{indicators['trend']} | MACD:{indicators['macd_signal']} | "
                f"BB:{indicators['bb_pct']}% | USDT:{usdt:.2f}"
            )

            # Verifica stop/tp
            if state["position"]:
                check_exit(price)

            # Calcula score tecnico para definir intervalo e se aciona IA
            score_pre, tipo_pre = calcular_score(indicators, state["position"])

            # Executa decisao (IA so e chamada se score >= SCORE_PARA_IA)
            decision = ask_claude(symbol, indicators, usdt, state["position"])
            action = decision.get("action", "WAIT")
            reason = decision.get("reason", "")
            conf   = decision.get("confidence", 0)

            log.info(f"[{symbol}] → {action} ({conf}%) | {reason}")

            # ── Executa decisao ─────────────────────────────────────────────
            if action == "BUY" and conf >= MIN_CONFIDENCE:
                if state["position"]:
                    log.info("Ja ha posicao aberta.")
                elif usdt >= MIN_USDT:
                    open_buy(symbol, price, reason, usdt)
                else:
                    log.info(f"BUY: USDT insuficiente (${usdt:.2f})")

            elif action == "SELL" and conf >= MIN_CONFIDENCE:
                if state["position"]:
                    close_position(price, reason)
                else:
                    log.info("SELL: sem posicao aberta.")

            else:
                log.info("Aguardando...")

            # Intervalo adaptativo: 60s se ha sinal, 180s se mercado parado
            sleep_time = LOOP_SIGNAL if score_pre >= SCORE_PARA_IA or state["position"] else LOOP_SECONDS
            log.info(f"[ECON] proximo ciclo em {sleep_time}s (score={score_pre}/4)")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            notify("⛔ Bot encerrado pelo usuário.")
            total = state["wins"] + state["losses"]
            wr    = round(state["wins"] / total * 100, 1) if total > 0 else 0
            log.info(f"Resumo: {total} ops | W:{state['wins']} L:{state['losses']} | WR:{wr}% | PnL:${state['pnl']:+.4f}")
            break
        except Exception as e:
            log.error(f"Erro: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run()
