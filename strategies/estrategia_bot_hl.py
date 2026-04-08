"""
Estratégia BOT_HL — Scanner Inteligente com Carteira
Usada por: BOT_HL

Diferencial em relação à estratégia padrão:
  - Scanner inclui automaticamente os ativos já em carteira
  - Pares da carteira passam com volume mínimo 10x menor (5M vs 50M)
  - Isso permite operar ativos menores que o bot já possui
  - Ideal para quem tem cripto diversificada e quer scalping ativo

Regras de entrada (BUY):
  - Mesmas da estratégia padrão (RSI/EMA/MACD/BB)
  - Score mínimo: 2/4 para IA, 3/4 para fallback

Regras de saída (SELL):
  - Mesmas da estratégia padrão

Scanner:
  - Volume mínimo: 50M USDT para pares configurados
  - Volume mínimo: 5M USDT para pares da carteira (10x menor)
  - Inclui automaticamente qualquer ativo em carteira com saldo > 0
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


def _get_wallet_pairs(exchange, log) -> list:
    """Detecta automaticamente ativos em carteira e retorna pares XYZUSDT."""
    try:
        balances = exchange.get_balances()
        wallet_pairs = []
        for asset, qty in balances.items():
            if asset == "USDT" or qty <= 0:
                continue
            symbol = f"{asset}USDT"
            try:
                # Verifica se par existe (Binance)
                if hasattr(exchange, 'client'):
                    exchange.client.get_symbol_info(symbol)
                else:
                    # OKX — tenta formato BTC-USDT
                    symbol = f"{asset}-USDT"
                wallet_pairs.append(symbol)
                log.info(f"[CARTEIRA] Par detectado: {symbol} (saldo: {qty:.6f})")
            except Exception:
                pass
        return wallet_pairs
    except Exception as e:
        log.warning(f"[CARTEIRA] Erro ao buscar saldos: {e}")
        return []


def _score_pair(exchange, symbol: str, min_volume: float = 50_000_000) -> dict:
    """Avalia um par."""
    try:
        t = exchange.get_ticker(symbol)
        vol   = float(t["quoteVolume"])
        if vol < min_volume:
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


def score_pair(exchange, symbol: str) -> dict:
    return _score_pair(exchange, symbol, min_volume=50_000_000)


def scan_best_pair(exchange, pairs: list, log, **kwargs) -> dict:
    """Escaneia pares configurados + pares em carteira."""
    # Detecta ativos em carteira
    wallet_pairs = _get_wallet_pairs(exchange, log)

    # Mescla sem duplicatas, preservando ordem
    all_pairs = list(dict.fromkeys(pairs + wallet_pairs))

    results = []
    for p in all_pairs:
        # Pares da carteira: volume mínimo 10x menor
        min_vol = 5_000_000 if (p in wallet_pairs and p not in pairs) else 50_000_000
        r = _score_pair(exchange, p, min_volume=min_vol)
        if r:
            r["in_wallet"] = p in wallet_pairs
            results.append(r)

    if not results:
        return {"symbol": pairs[0], "score": 0}

    results.sort(key=lambda x: x["score"], reverse=True)
    best = results[0]

    log.info("── Scanner ──────────────────────────────")
    for r in results:
        tag    = "💼" if r.get("in_wallet") else "  "
        marker = "★" if r["symbol"] == best["symbol"] else " "
        log.info(f"{marker} {tag} {r['symbol']:<12} | Score:{r['score']:5.1f} | "
                 f"Vol:{r['volume']:6.0f}M | Var:{r['change']:+5.2f}% | Volat:{r['volatility']:.2f}%")
    log.info(f"Melhor: {best['symbol']}{' 💼 (carteira)' if best.get('in_wallet') else ''}")
    return best


def fallback_tecnico(ind: dict, usdt: float, position, min_usdt: float) -> dict:
    """Decisão sem IA."""
    score, tipo = calcular_score(ind, position)
    rsi = ind["rsi"]
    bb  = ind["bb_pct"]
    if tipo == "SELL" and score >= 3 and position:
        return {"action": "SELL", "reason": f"[FB] RSI={rsi} BB={bb}%", "confidence": score * 20}
    if tipo == "BUY" and score >= 3 and usdt >= min_usdt:
        return {"action": "BUY", "reason": f"[FB] RSI={rsi} BB={bb}%", "confidence": score * 20}
    return {"action": "WAIT", "reason": f"[FB] score={score}/4", "confidence": 0}


# Metadados da estratégia
NOME      = "BOT_HL Scanner Carteira"
DESCRICAO = "Inclui ativos em carteira no scanner — volume mínimo reduzido"
VERSAO    = "1.0"
AUTOR     = "ScalpBot"
