"""
Estratégia Padrão — ScalpBot
Usada por: BOT_PNO, BOT_OKX e qualquer bot sem estratégia definida

Regras de entrada (BUY):
  - RSI < 42
  - EMA bullish (cruzamento ou acima)
  - MACD bullish com histograma positivo
  - BB < 40% (preço na parte inferior da banda)
  Score mínimo: 2/4 para acionar IA, 3/4 para fallback direto

Regras de saída (SELL):
  - RSI > 58
  - EMA bearish
  - MACD bearish com histograma negativo
  - BB > 60% (preço na parte superior da banda)

Scanner:
  - Volume mínimo: 50M USDT/24h
  - Considera apenas os pares configurados no .env
"""


def calcular_score(ind: dict, position) -> tuple:
    """Calcula score técnico de 0 a 4. Retorna (score, tipo)."""
    rsi  = ind["rsi"]
    ema  = ind["ema_cross"]
    macd = ind["macd_signal"]
    hist = ind["macd_hist"]
    bb   = ind["bb_pct"]

    buy  = sum([
        rsi < 42,
        ema in ("cruzamento_alta", "acima_bullish"),
        macd == "bullish" and hist > 0,
        bb < 40
    ])
    sell = sum([
        rsi > 58,
        ema in ("cruzamento_baixa", "abaixo_bearish"),
        macd == "bearish" and hist < 0,
        bb > 60
    ])
    return (sell, "SELL") if position else (buy, "BUY")


def score_pair(client_or_exchange, symbol: str) -> dict:
    """Avalia um par pelo volume, variação e volatilidade."""
    MIN_VOLUME = 50_000_000  # 50M USDT mínimo
    try:
        t = client_or_exchange.get_ticker(symbol=symbol) if hasattr(client_or_exchange, 'get_ticker') \
            else client_or_exchange.get_ticker(symbol)
        vol   = float(t["quoteVolume"])
        if vol < MIN_VOLUME:
            return None
        chg   = float(t["priceChangePercent"])
        high  = float(t["highPrice"])
        low   = float(t["lowPrice"])
        volat = ((high - low) / low) * 100 if low > 0 else 0
        score = min(volat * 10, 40) + min(vol / 1_000_000_000 * 30, 30) + max(0, 30 - abs(chg) * 2)
        return {
            "symbol":     symbol,
            "price":      float(t["lastPrice"]),
            "change":     round(chg, 2),
            "volume":     round(vol / 1_000_000, 1),
            "volatility": round(volat, 2),
            "score":      round(score, 1),
            "in_wallet":  False,
        }
    except Exception:
        return None


def scan_best_pair(exchange, pairs: list, log, **kwargs) -> dict:
    """Escaneia os pares configurados e retorna o melhor."""
    results = [r for r in [score_pair(exchange, p) for p in pairs] if r]
    if not results:
        return {"symbol": pairs[0], "score": 0}
    results.sort(key=lambda x: x["score"], reverse=True)
    best = results[0]
    log.info("── Scanner ──────────────────────────────")
    for r in results:
        m = "★" if r["symbol"] == best["symbol"] else " "
        log.info(f"{m} {r['symbol']:<12} | Score:{r['score']:5.1f} | "
                 f"Vol:{r['volume']:6.0f}M | Var:{r['change']:+5.2f}% | Volat:{r['volatility']:.2f}%")
    log.info(f"Melhor: {best['symbol']}")
    return best


def fallback_tecnico(ind: dict, usdt: float, position, min_usdt: float) -> dict:
    """Decisão sem IA baseada nos indicadores técnicos."""
    score, tipo = calcular_score(ind, position)
    rsi = ind["rsi"]
    bb  = ind["bb_pct"]
    if tipo == "SELL" and score >= 3 and position:
        return {"action": "SELL", "reason": f"[FB] RSI={rsi} BB={bb}%", "confidence": score * 20}
    if tipo == "BUY" and score >= 3 and usdt >= min_usdt:
        return {"action": "BUY", "reason": f"[FB] RSI={rsi} BB={bb}%", "confidence": score * 20}
    return {"action": "WAIT", "reason": f"[FB] score={score}/4", "confidence": 0}


# Metadados da estratégia
NOME        = "Padrão"
DESCRICAO   = "RSI/EMA/MACD/BB clássico — conservador"
VERSAO      = "1.0"
AUTOR       = "ScalpBot"
