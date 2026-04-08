"""
Estratégia OKX — Multi-par com suporte a BRL
Usada por: BOT_OKX

Diferencial:
  - Suporta pares crypto-USDT (BTC-USDT, ETH-USDT, SOL-USDT, XRP-USDT)
  - Suporta par fiat USDT-BRL (câmbio dólar/real)
  - Para USDT-BRL: lógica inversa — compra USDT quando dólar cai (BRL sobe)
  - Volume mínimo ajustado para pares BRL (menor liquidez)
  - OKX sem proxy Tor — acesso direto, mais rápido

Par USDT-BRL na OKX:
  - Comprar USDT = apostar que dólar vai subir (BRL desvalorizar)
  - Vender USDT = apostar que dólar vai cair (BRL valorizar)
  - RSI < 35 em USDT-BRL = dólar muito barato → oportunidade de COMPRAR USDT
  - RSI > 65 em USDT-BRL = dólar muito caro → oportunidade de VENDER USDT
  - Stop/TP mais apertados para BRL (câmbio oscila menos que cripto)
"""

# Pares fiat — tratamento diferente
FIAT_PAIRS = {"USDT-BRL", "BTC-BRL", "ETH-BRL"}

# Volume mínimo por tipo de par
MIN_VOL_CRYPTO = 10_000_000   # 10M USDT para cripto
MIN_VOL_BRL    = 500_000      # 500k para pares BRL (menor liquidez)


def _is_fiat(symbol: str) -> bool:
    return symbol in FIAT_PAIRS or symbol.endswith("-BRL")


def calcular_score(ind: dict, position) -> tuple:
    """Score técnico adaptado — para BRL usa limiares diferentes."""
    rsi  = ind["rsi"]
    ema  = ind["ema_cross"]
    macd = ind["macd_signal"]
    hist = ind["macd_hist"]
    bb   = ind["bb_pct"]
    sym  = ind.get("symbol", "")

    if _is_fiat(sym):
        # Para USDT-BRL: RSI baixo = dólar barato = comprar USDT
        buy  = sum([rsi < 35, ema in ("cruzamento_alta","acima_bullish"), macd=="bullish" and hist>0, bb < 30])
        sell = sum([rsi > 65, ema in ("cruzamento_baixa","abaixo_bearish"), macd=="bearish" and hist<0, bb > 70])
    else:
        # Cripto padrão
        buy  = sum([rsi < 42, ema in ("cruzamento_alta","acima_bullish"), macd=="bullish" and hist>0, bb < 40])
        sell = sum([rsi > 58, ema in ("cruzamento_baixa","abaixo_bearish"), macd=="bearish" and hist<0, bb > 60])

    return (sell, "SELL") if position else (buy, "BUY")


def _get_ticker_okx(exchange, symbol: str) -> dict:
    """Busca ticker da OKX e normaliza para formato padrão."""
    try:
        t = exchange.get_ticker(symbol)
        vol_raw = float(t.get("quoteVolume", "0") or "0")
        # OKX retorna volume em moeda de cotação — para BRL converter para USDT
        if _is_fiat(symbol):
            # volume em BRL — converter aproximado
            brl_rate = 5.1  # aprox
            vol_usdt = vol_raw / brl_rate
        else:
            vol_usdt = vol_raw
        return {
            "symbol":     symbol,
            "price":      float(t.get("lastPrice","0") or "0"),
            "change":     float(t.get("priceChangePercent","0") or "0"),
            "highPrice":  float(t.get("highPrice","0") or "0"),
            "lowPrice":   float(t.get("lowPrice","0") or "0"),
            "vol_usdt":   vol_usdt,
        }
    except:
        return None


def score_pair(exchange, symbol: str) -> dict:
    """Avalia um par para o scanner."""
    min_vol = MIN_VOL_BRL if _is_fiat(symbol) else MIN_VOL_CRYPTO
    try:
        d = _get_ticker_okx(exchange, symbol)
        if not d: return None
        if d["vol_usdt"] < min_vol: return None
        chg   = d["change"]
        high  = d["highPrice"]; low = d["lowPrice"]
        price = d["price"]
        volat = ((high - low) / low) * 100 if low > 0 else 0
        # Score BRL: menor peso de volatilidade (câmbio é menos volátil)
        if _is_fiat(symbol):
            score = min(volat*20,40) + min(d["vol_usdt"]/10_000_000*30,30) + max(0,30-abs(chg)*5)
        else:
            score = min(volat*10,40) + min(d["vol_usdt"]/1_000_000_000*30,30) + max(0,30-abs(chg)*2)
        return {
            "symbol":     symbol,
            "price":      round(price,6),
            "change":     round(chg,2),
            "volume":     round(d["vol_usdt"]/1_000_000,1),
            "volatility": round(volat,2),
            "score":      round(score,1),
            "in_wallet":  False,
            "is_fiat":    _is_fiat(symbol),
        }
    except: return None


def scan_best_pair(exchange, pairs: list, log, **kwargs) -> dict:
    """Scanner — separa pares cripto de BRL na exibição."""
    results = [r for r in [score_pair(exchange, p) for p in pairs] if r]
    if not results: return {"symbol": pairs[0], "score": 0}
    results.sort(key=lambda x: x["score"], reverse=True)
    best = results[0]

    crypto = [r for r in results if not r.get("is_fiat")]
    fiat   = [r for r in results if r.get("is_fiat")]

    log.info("── Scanner OKX ──────────────────────────")
    if crypto:
        log.info("  [CRIPTO]")
        for r in crypto:
            m = "★" if r["symbol"]==best["symbol"] else " "
            log.info(f"  {m} {r['symbol']:<14} | Score:{r['score']:5.1f} | Vol:{r['volume']:6.0f}M | Var:{r['change']:+5.2f}% | Volat:{r['volatility']:.2f}%")
    if fiat:
        log.info("  [FIAT/BRL]")
        for r in fiat:
            m = "★" if r["symbol"]==best["symbol"] else " "
            log.info(f"  {m} {r['symbol']:<14} | Score:{r['score']:5.1f} | Vol:{r['volume']:6.0f}M | Var:{r['change']:+5.2f}%")
    log.info(f"Melhor: {best['symbol']}")
    return best


def fallback_tecnico(ind: dict, usdt: float, position, min_usdt: float) -> dict:
    """Fallback técnico sem IA."""
    score, tipo = calcular_score(ind, position)
    rsi = ind["rsi"]; bb = ind["bb_pct"]
    sym = ind.get("symbol","")

    # Para BRL: precisa sinal mais forte (score >= 3)
    min_score = 3 if _is_fiat(sym) else 3

    if tipo == "SELL" and score >= min_score and position:
        motivo = f"[FB-OKX] {'Dólar caro, vendendo USDT' if _is_fiat(sym) else f'RSI={rsi} BB={bb}%'}"
        return {"action":"SELL","reason":motivo,"confidence":score*20}
    if tipo == "BUY" and score >= min_score and usdt >= min_usdt:
        motivo = f"[FB-OKX] {'Dólar barato, comprando USDT' if _is_fiat(sym) else f'RSI={rsi} BB={bb}%'}"
        return {"action":"BUY","reason":motivo,"confidence":score*20}
    return {"action":"WAIT","reason":f"[FB-OKX] score={score}/4","confidence":0}


NOME      = "OKX Multi-Exchange"
DESCRICAO = "Cripto + BRL — suporta USDT-BRL com lógica de câmbio"
VERSAO    = "1.0"
AUTOR     = "ScalpBot"
