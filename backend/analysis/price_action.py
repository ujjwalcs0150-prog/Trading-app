"""
Price Action Analysis Engine
Detects: Trend, Candlestick Patterns, Support/Resistance, Momentum
"""
import pandas as pd
import numpy as np
from typing import List
from models.schemas import CandlePattern, SupportResistance, PriceActionAnalysis


# ─── Trend Detection ─────────────────────────────────────────────────────────

def detect_trend(df: pd.DataFrame) -> str:
    close = df["close"]
    ema20  = close.ewm(span=20, adjust=False).mean()
    ema50  = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    last_close = close.iloc[-1]
    last_e20   = ema20.iloc[-1]
    last_e50   = ema50.iloc[-1]
    last_e200  = ema200.iloc[-1]

    if last_close > last_e20 > last_e50 > last_e200:
        return "uptrend"
    if last_close < last_e20 < last_e50 < last_e200:
        return "downtrend"
    return "sideways"


# ─── Momentum ────────────────────────────────────────────────────────────────

def detect_momentum(df: pd.DataFrame) -> str:
    close  = df["close"]
    delta  = close.diff()
    gain   = delta.clip(lower=0)
    loss   = -delta.clip(upper=0)
    avg_g  = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_l  = loss.ewm(alpha=1/14, adjust=False).mean()
    rs     = avg_g / avg_l.replace(0, np.nan)
    rsi    = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]

    if last_rsi >= 70:
        return "strong_bullish"
    if last_rsi >= 55:
        return "bullish"
    if last_rsi <= 30:
        return "strong_bearish"
    if last_rsi <= 45:
        return "bearish"
    return "neutral"


# ─── Candlestick Patterns ────────────────────────────────────────────────────

def _body(o, c): return abs(c - o)
def _range(h, l): return h - l
def _upper_wick(o, c, h): return h - max(o, c)
def _lower_wick(o, c, l): return min(o, c) - l


def detect_candle_patterns(df: pd.DataFrame) -> List[CandlePattern]:
    patterns: List[CandlePattern] = []
    n = len(df)
    if n < 3:
        return patterns

    o = df["open"].values
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values

    # Only check last 20 candles for relevance
    start = max(2, n - 20)

    for i in range(start, n):
        ts    = str(df.index[i])
        body  = _body(o[i], c[i])
        rng   = _range(h[i], l[i])
        upper = _upper_wick(o[i], c[i], h[i])
        lower = _lower_wick(o[i], c[i], l[i])

        if rng == 0:
            continue

        prev_body  = _body(o[i-1], c[i-1])
        prev_range = _range(h[i-1], l[i-1])

        # ── Doji ──
        if body / rng < 0.1:
            patterns.append(CandlePattern(
                timestamp=ts, pattern="Doji", signal="neutral",
                strength=0.5, description="Indecision — watch for confirmation"))
            continue

        # ── Hammer / Hanging Man ──
        if lower >= 2 * body and upper < body * 0.5 and rng > 0:
            if c[i-1] < o[i-1]:  # after downtrend
                patterns.append(CandlePattern(
                    timestamp=ts, pattern="Hammer", signal="bullish",
                    strength=0.75, description="Bullish reversal — long lower wick rejection"))
            else:
                patterns.append(CandlePattern(
                    timestamp=ts, pattern="Hanging Man", signal="bearish",
                    strength=0.6, description="Bearish reversal warning at highs"))
            continue

        # ── Inverted Hammer / Shooting Star ──
        if upper >= 2 * body and lower < body * 0.5 and rng > 0:
            if c[i-1] < o[i-1]:
                patterns.append(CandlePattern(
                    timestamp=ts, pattern="Inverted Hammer", signal="bullish",
                    strength=0.65, description="Potential bullish reversal after downtrend"))
            else:
                patterns.append(CandlePattern(
                    timestamp=ts, pattern="Shooting Star", signal="bearish",
                    strength=0.75, description="Bearish reversal — upper wick rejection at highs"))
            continue

        # ── Bullish Engulfing ──
        if (c[i-1] < o[i-1]           # prev bearish
                and c[i] > o[i]        # curr bullish
                and o[i] <= c[i-1]     # opens at/below prev close
                and c[i] >= o[i-1]):   # closes at/above prev open
            str_ = min(1.0, body / prev_body) if prev_body > 0 else 0.8
            patterns.append(CandlePattern(
                timestamp=ts, pattern="Bullish Engulfing", signal="bullish",
                strength=round(str_, 3),
                description="Strong bullish reversal — engulfs prior bearish candle"))
            continue

        # ── Bearish Engulfing ──
        if (c[i-1] > o[i-1]
                and c[i] < o[i]
                and o[i] >= c[i-1]
                and c[i] <= o[i-1]):
            str_ = min(1.0, body / prev_body) if prev_body > 0 else 0.8
            patterns.append(CandlePattern(
                timestamp=ts, pattern="Bearish Engulfing", signal="bearish",
                strength=round(str_, 3),
                description="Strong bearish reversal — engulfs prior bullish candle"))
            continue

        # ── Bullish Pin Bar ──
        if lower >= 2.5 * body and c[i] > o[i]:
            patterns.append(CandlePattern(
                timestamp=ts, pattern="Bullish Pin Bar", signal="bullish",
                strength=0.8, description="Strong rejection of lower prices — bullish pressure"))
            continue

        # ── Bearish Pin Bar ──
        if upper >= 2.5 * body and c[i] < o[i]:
            patterns.append(CandlePattern(
                timestamp=ts, pattern="Bearish Pin Bar", signal="bearish",
                strength=0.8, description="Strong rejection of upper prices — bearish pressure"))
            continue

        # ── Morning Star (3-candle) ──
        if i >= 2:
            if (c[i-2] < o[i-2]
                    and _body(o[i-1], c[i-1]) < 0.3 * prev_range
                    and c[i] > o[i]
                    and c[i] > (o[i-2] + c[i-2]) / 2):
                patterns.append(CandlePattern(
                    timestamp=ts, pattern="Morning Star", signal="bullish",
                    strength=0.85, description="3-candle bullish reversal pattern"))
                continue

            # ── Evening Star ──
            if (c[i-2] > o[i-2]
                    and _body(o[i-1], c[i-1]) < 0.3 * prev_range
                    and c[i] < o[i]
                    and c[i] < (o[i-2] + c[i-2]) / 2):
                patterns.append(CandlePattern(
                    timestamp=ts, pattern="Evening Star", signal="bearish",
                    strength=0.85, description="3-candle bearish reversal pattern"))
                continue

        # ── Marubozu ──
        if body / rng > 0.85:
            sig = "bullish" if c[i] > o[i] else "bearish"
            patterns.append(CandlePattern(
                timestamp=ts, pattern="Marubozu", signal=sig,
                strength=0.7, description=f"Strong {sig} momentum — no wicks, full body candle"))

    return patterns[-10:]  # return last 10 significant patterns


# ─── Support / Resistance ────────────────────────────────────────────────────

def detect_support_resistance(df: pd.DataFrame) -> List[SupportResistance]:
    """Cluster pivot points into significant S/R zones."""
    levels: List[SupportResistance] = []
    close   = df["close"]
    current = close.iloc[-1]
    tolerance = current * 0.005  # 0.5 %

    pivots: List[tuple] = []   # (price, type, timestamp)

    highs = df["high"].values
    lows  = df["low"].values

    for i in range(2, len(df) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            pivots.append((highs[i], "resistance", str(df.index[i])))
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            pivots.append((lows[i], "support", str(df.index[i])))

    # Cluster nearby pivots
    clustered: List[SupportResistance] = []
    used = set()

    for idx, (price, typ, ts) in enumerate(pivots):
        if idx in used:
            continue
        cluster = [(price, ts)]
        for jdx, (p2, t2, ts2) in enumerate(pivots):
            if jdx != idx and jdx not in used and abs(p2 - price) <= tolerance:
                cluster.append((p2, ts2))
                used.add(jdx)
        used.add(idx)

        avg_price = np.mean([x[0] for x in cluster])
        touches   = len(cluster)
        last_ts   = sorted([x[1] for x in cluster])[-1]

        clustered.append(SupportResistance(
            price=round(avg_price, 6),
            type=typ,
            strength=min(5, touches),
            touches=touches,
            last_tested=last_ts,
        ))

    # Sort by proximity to current price
    clustered.sort(key=lambda x: abs(x.price - current))
    return clustered[:10]


# ─── Key Levels ──────────────────────────────────────────────────────────────

def get_key_levels(df: pd.DataFrame) -> List[float]:
    """Round number levels and recent significant pivots."""
    current = df["close"].iloc[-1]
    magnitude = 10 ** (len(str(int(current))) - 2)

    round_levels = []
    base = (current // magnitude) * magnitude
    for mult in range(-5, 6):
        lvl = base + mult * magnitude
        if lvl > 0:
            round_levels.append(round(lvl, 6))

    # Add recent day high/low and week high/low
    round_levels.append(round(df["high"].tail(1).iloc[0], 6))
    round_levels.append(round(df["low"].tail(1).iloc[0], 6))
    round_levels.append(round(df["high"].tail(5).max(), 6))
    round_levels.append(round(df["low"].tail(5).min(), 6))

    return sorted(set(round_levels))


# ─── Main entry point ────────────────────────────────────────────────────────

def run_price_action_analysis(df: pd.DataFrame) -> PriceActionAnalysis:
    trend       = detect_trend(df)
    momentum    = detect_momentum(df)
    patterns    = detect_candle_patterns(df)
    sr_levels   = detect_support_resistance(df)
    key_levels  = get_key_levels(df)

    return PriceActionAnalysis(
        trend=trend,
        candle_patterns=patterns,
        support_resistance=sr_levels,
        momentum=momentum,
        key_levels=key_levels,
    )
