"""
ScalpBot Multi-Conta Multi-Exchange — Binance + OKX + IA (Claude)
Suporta múltiplas contas com exchanges, estratégias e pares independentes.

.env: BOT_N_EXCHANGE=binance|okx
"""

import os, time, logging, json, threading, subprocess
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import anthropic

# Proxy Tor — necessário para Binance em VPS nos EUA
# OKX não precisa de proxy — acesso direto
os.environ['HTTP_PROXY']  = 'socks5h://127.0.0.1:9050'
os.environ['HTTPS_PROXY'] = 'socks5h://127.0.0.1:9050'

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

import importlib.util as _ilu

# ── Adapters de Exchange ─────────────────────────────────────────────────────

class BinanceExchange:
    """Adapter para Binance com proxy Tor."""
    def __init__(self, key, secret, log, testnet=False):
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        self.BinanceAPIException = BinanceAPIException
        self.Client  = Client
        self._key    = key
        self._secret = secret
        self.log     = log
        self.testnet = testnet
        self.client  = self._conectar()

    def _conectar(self, max_t=8):
        from binance.client import Client
        proxies = {"http":"socks5h://127.0.0.1:9050","https":"socks5h://127.0.0.1:9050"}
        for i in range(1, max_t+1):
            try:
                c = Client(self._key, self._secret, requests_params={"proxies":proxies})
                self.log.info(f"[BINANCE][TOR] Conectada (tentativa {i})")
                return c
            except Exception as e:
                if "restricted location" in str(e) or "403" in str(e) or "cloudfront" in str(e).lower():
                    self.log.warning(f"[TOR] Nó bloqueado ({i}/{max_t}) — trocando...")
                    try:
                        subprocess.run(["sudo","systemctl","restart","tor"],timeout=10,capture_output=True)
                        time.sleep(20)
                    except: time.sleep(10)
                else: raise
        raise ConnectionError(f"[BINANCE] Bloqueada após {max_t} tentativas Tor.")

    def reconectar(self): self.client = self._conectar()

    def get_klines(self, symbol, limit=100):
        from binance.client import Client
        return self.client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=limit)

    def get_ticker(self, symbol):
        return self.client.get_ticker(symbol=symbol)

    def get_balances(self):
        info = self.client.get_account()
        return {b["asset"]: float(b["free"]) for b in info["balances"] if float(b["free"]) > 0}

    def get_usdt(self, balances): return balances.get("USDT", 0.0)

    def get_precision(self, symbol):
        info = self.client.get_symbol_info(symbol)
        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step = f["stepSize"].rstrip("0")
                return len(step.split(".")[-1]) if "." in step else 0
        return 5

    def buy_market(self, symbol, qty, precision):
        return self.client.order_market_buy(symbol=symbol, quantity=f"{qty:.{precision}f}")

    def sell_market(self, symbol, qty, precision, balances):
        asset = symbol.replace("USDT","")
        avail = balances.get(asset, 0.0)
        qty_r = min(qty, avail)
        if qty_r < 10**(-precision):
            self.log.warning(f"[BINANCE] Saldo insuficiente SELL {symbol}: {avail}")
            return None
        return self.client.order_market_sell(symbol=symbol, quantity=f"{qty_r:.{precision}f}")

    def format_pair(self, symbol):
        return symbol.replace("-","")

    @property
    def name(self): return "Binance"


class OKXExchange:
    """Adapter para OKX — sem proxy, acesso direto."""
    def __init__(self, key, secret, passphrase, log, testnet=False):
        self._key        = key
        self._secret     = secret
        self._passphrase = passphrase
        self.log         = log
        self.testnet     = testnet
        self._init()

    def _init(self):
        try:
            import okx.MarketData as MD
            import okx.Trade as TR
            import okx.Account as AC
            flag = "1" if self.testnet else "0"
            self._market  = MD.MarketAPI(flag=flag, debug=False)
            self._trade   = TR.TradeAPI(self._key,self._secret,self._passphrase,False,flag,debug=False)
            self._account = AC.AccountAPI(self._key,self._secret,self._passphrase,False,flag,debug=False)
            self.log.info("[OKX] Conectada com sucesso!")
        except ImportError:
            raise ImportError("python-okx não instalado. Execute: pip install python-okx")

    def reconectar(self): self._init()

    def get_klines(self, symbol, limit=100):
        r = self._market.get_candlesticks(instId=symbol, bar="1m", limit=str(limit))
        if r.get("code") != "0": raise Exception(f"OKX klines: {r}")
        candles = list(reversed(r["data"]))
        return [[int(c[0]),c[1],c[2],c[3],c[4],c[5],0,0,0,0,0,0] for c in candles]

    def get_ticker(self, symbol):
        r = self._market.get_ticker(instId=symbol)
        if r.get("code") != "0": raise Exception(f"OKX ticker: {r}")
        d = r["data"][0]
        sod = float(d.get("sodUtc8", d.get("last","1")) or "1")
        last = float(d.get("last","0") or "0")
        chg_pct = (last - sod) / sod * 100 if sod else 0
        return {
            "quoteVolume":        d.get("volCcy24h","0"),
            "priceChangePercent": str(round(chg_pct,2)),
            "highPrice":          d.get("high24h","0"),
            "lowPrice":           d.get("low24h","0"),
            "lastPrice":          d.get("last","0"),
        }

    def get_balances(self):
        r = self._account.get_account_balance()
        if r.get("code") != "0": raise Exception(f"OKX balance: {r}")
        out = {}
        for item in r["data"][0]["details"]:
            free = float(item.get("availBal","0") or "0")
            if free > 0: out[item["ccy"]] = free
        return out

    def get_usdt(self, balances): return balances.get("USDT", 0.0)

    def get_precision(self, symbol):
        r = self._market.get_instruments(instType="SPOT", instId=symbol)
        if r.get("code") != "0": return 6
        lot = r["data"][0].get("lotSz","0.000001").rstrip("0")
        return len(lot.split(".")[-1]) if "." in lot else 0

    def buy_market(self, symbol, qty, precision):
        r = self._trade.place_order(instId=symbol,tdMode="cash",side="buy",
                                     ordType="market",sz=f"{qty:.{precision}f}")
        if r.get("code") != "0": raise Exception(f"OKX buy: {r}")
        return r

    def sell_market(self, symbol, qty, precision, balances):
        asset = symbol.split("-")[0]
        avail = balances.get(asset, 0.0)
        qty_r = min(qty, avail)
        if qty_r < 10**(-precision):
            self.log.warning(f"[OKX] Saldo insuficiente SELL {symbol}: {avail}")
            return None
        r = self._trade.place_order(instId=symbol,tdMode="cash",side="sell",
                                     ordType="market",sz=f"{qty_r:.{precision}f}")
        if r.get("code") != "0": raise Exception(f"OKX sell: {r}")
        return r

    def format_pair(self, symbol):
        if "-" not in symbol and len(symbol) > 4:
            return symbol[:-4] + "-" + symbol[-4:]
        return symbol

    @property
    def name(self): return "OKX"


def carregar_estrategia(nome: str):
    """Carrega um arquivo de estratégia da pasta strategies/."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "strategies", f"{nome}.py")
    if not os.path.exists(path):
        path = os.path.join(base, "strategies", "estrategia_padrao.py")
    spec   = _ilu.spec_from_file_location(nome, path)
    modulo = _ilu.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo

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

def get_klines(exchange_or_client, symbol: str, interval=None, limit: int = 100) -> pd.DataFrame:
    if hasattr(exchange_or_client, 'get_klines') and callable(getattr(exchange_or_client, 'get_klines')):
        # Exchange adapter (BinanceExchange ou OKXExchange)
        raw = exchange_or_client.get_klines(symbol, limit)
    else:
        # Binance client legado
        from binance.client import Client
        raw = exchange_or_client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=limit)
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
        import re as _re; m = _re.search(r'\{[^{}]+\}', text)
        return json.loads(m.group(0)) if m else fallback_tecnico(ind, usdt, position, min_usdt)
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
        # Liga/desliga Telegram desta conta
        self.tg_ativo    = cfg.get("telegram_ativo", True)

        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"bot_{self.name.lower().replace(' ','_')}.log"
        )
        self.log = setup_logger(self.name, log_file)

        # Carrega estratégia do bot
        nome_estrategia = cfg.get("estrategia", "estrategia_padrao")
        self.estrategia = carregar_estrategia(nome_estrategia)
        self.log.info(f"[ESTRATEGIA] {self.estrategia.NOME} v{self.estrategia.VERSAO} — {self.estrategia.DESCRICAO}")

        # Inicializa exchange correta
        exchange_name = cfg.get("exchange","binance").lower()
        self.exchange_name = exchange_name
        if exchange_name == "okx":
            self.exchange = OKXExchange(
                cfg.get("okx_key",""), cfg.get("okx_secret",""), cfg.get("okx_passphrase",""),
                self.log, self.testnet
            )
            self.pairs = [self.exchange.format_pair(p) for p in self.pairs]
            self.binance = None  # compatibilidade
        else:
            self.exchange = BinanceExchange(cfg["binance_key"], cfg["binance_secret"], self.log, self.testnet)
            self.binance = self.exchange.client  # compatibilidade legada
            self.pairs = [self.exchange.format_pair(p) for p in self.pairs]

        self.ai = anthropic.Anthropic(api_key=cfg["anthropic_key"])
        self.state = {
            "position": None, "active_symbol": None,
            "trades": [], "pnl": 0.0, "wins": 0, "losses": 0,
        }
        self.ai_calls = {"count": 0, "data": ""}
        self.cycle    = 0

    # _conectar_binance mantido para compatibilidade
    def _conectar_binance(self, max_tentativas: int = 8):
        return self.exchange._conectar(max_tentativas) if hasattr(self.exchange, '_conectar') else None

    def notify(self, msg: str, tipo: str = None):
        self.log.info(msg)
        # Verifica se Telegram está ativado para esta conta
        if not self.tg_ativo:
            return
        # Verifica se este tipo de notificação está ativado
        if tipo and not self.notify_cfg.get(tipo, True):
            return
        prefixo = f"{self.bot_emoji} [{self.name}]\n"
        send_telegram(self.tg_token, self.tg_chat, prefixo + msg, self.log)

    def get_balances(self) -> dict:
        return self.exchange.get_balances()

    def get_usdt(self) -> float:
        return self.exchange.get_usdt(self.get_balances())

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
            precision = self.exchange.get_precision(symbol)
            balances  = self.get_balances()
            if side == "BUY":
                order = self.exchange.buy_market(symbol, qty, precision)
            else:
                order = self.exchange.sell_market(symbol, qty, precision, balances)
            if order:
                emoji = "🟢" if side == "BUY" else "🔴"
                self.notify(f"{emoji} {side} {qty:.{precision}f} {symbol} @ ~${price:,.4f}")
            return order
        except Exception as e:
            self.notify(f"❌ Erro {side} {symbol}: {e}")
            return None

    def open_buy(self, symbol: str, price: float, reason: str, usdt: float):
        amount = usdt * self.trade_pct
        if amount < self.min_usdt:
            self.log.info(f"USDT insuficiente: ${amount:.2f}")
            return
        precision = self.exchange.get_precision(symbol)
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
        exch = getattr(self.exchange, 'name', 'Exchange')
        self.notify(f"🤖 Bot '{self.name}' iniciado na {exch}!", tipo="inicio")
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
                        best = self.estrategia.scan_best_pair(self.binance, self.pairs, self.log)
                        if best["symbol"] != self.state["active_symbol"]:
                            old = self.state["active_symbol"]
                            self.state["active_symbol"] = best["symbol"]
                            if old:
                                self.notify(f"🔄 Par: {old} → {best['symbol']} (score:{best.get('score',0):.1f})", tipo="par_troca")

                symbol = (self.state["position"]["symbol"]
                          if self.state["position"]
                          else self.state["active_symbol"] or self.pairs[0])

                df  = get_klines(self.exchange, symbol, None)
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

                score_pre, _ = self.estrategia.calcular_score(ind, self.state["position"])
                sleep = self.loop_signal if score_pre >= self.score_ia or self.state["position"] else self.loop_base
                time.sleep(sleep)

            except KeyboardInterrupt:
                self.notify("⛔ Bot encerrado.", tipo="resumo")
                break
            except Exception as e:
                err = str(e)
                if "restricted location" in err or "cloudfront" in err.lower() or "403" in err:
                    self.log.warning("[TOR] Bloqueio no loop — reconectando...")
                    try:
                        self.exchange.reconectar()
                        if hasattr(self.exchange, 'client'):
                            self.binance = self.exchange.client
                        self.log.info("[TOR] Reconectado com sucesso!")
                    except Exception as re:
                        self.log.error(f"[TOR] Falha ao reconectar: {re}")
                        time.sleep(30)
                else:
                    self.log.error(f"Erro: {e}")
                    time.sleep(15)


# ── Carrega configurações e inicia bots ───────────────────────────────────────

def load_bot_config(prefix: str) -> dict:
    def g(key, default=""): return os.getenv(f"{prefix}_{key}", default)
    pairs_raw = g("PAIRS","BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT")
    return {
        "name":           g("NAME", prefix),
        "emoji":          g("EMOJI", "🤖"),
        "exchange":       g("EXCHANGE","binance"),
        "binance_key":    g("BINANCE_KEY"),
        "binance_secret": g("BINANCE_SECRET"),
        "okx_key":        g("OKX_KEY"),
        "okx_secret":     g("OKX_SECRET"),
        "okx_passphrase": g("OKX_PASSPHRASE"),
        "anthropic_key":  g("ANTHROPIC_KEY"),
        "telegram_token": g("TELEGRAM_TOKEN"),
        "telegram_chat":  g("TELEGRAM_CHAT"),
        "pairs":          [p.strip() for p in pairs_raw.split(",")],
        "estrategia":     g("ESTRATEGIA", "estrategia_padrao"),
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
        # Liga/desliga Telegram desta conta
        "telegram_ativo":     g("TELEGRAM_ATIVO","true").lower()=="true",
    }


if __name__ == "__main__":
    bot_count = int(os.getenv("BOT_COUNT","1"))
    threads   = []

    for i in range(1, bot_count + 1):
        prefix = f"BOT_{i}"
        cfg    = load_bot_config(prefix)
        exch = cfg.get("exchange","binance").lower()
        if exch == "okx":
            if not cfg.get("okx_key","").strip():
                print(f"[AVISO] {prefix} sem chave OKX — verifique o .env")
                continue
        else:
            if not cfg.get("binance_key","").strip():
                print(f"[AVISO] {prefix} sem chave Binance — verifique o .env")
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
