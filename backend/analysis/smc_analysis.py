"""
Smart Money Concepts (SMC) Analysis Engine
Detects: Order Blocks, Fair Value Gaps, Liquidity Levels, BOS/CHOCH, Market Structure
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from models.schemas import (
    OrderBlock, FairValueGap, LiquidityLevel,
    BreakOfStructure, SMCAnalysis
)


# ─── Swing detection ────────────────────────────────────────────────────────

def find_swing_highs_lows(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """Identify swing highs and lows using a rolling window."""
    highs = df["high"].values
    lows  = df["low"].values
    n = len(df)

    swing_high = np.zeros(n, dtype=bool)
    swing_low  = np.zeros(n, dtype=bool)

    for i in range(lookback, n - lookback):
        window_high = highs[i - lookback: i + lookback + 1]
        window_low  = lows[i - lookback: i + lookback + 1]
        if highs[i] == window_high.max():
            swing_high[i] = True
        if lows[i] == window_low.min():
            swing_low[i] = True

    df = df.copy()
    df["swing_high"] = swing_high
    df["swing_low"]  = swing_low
    return df


# ─── Market Structure ────────────────────────────────────────────────────────

def analyze_market_structure(df: pd.DataFrame) -> str:
    """Determine higher-timeframe market structure from recent swing points."""
    swings = df[df["swing_high"] | df["swing_low"]].tail(20)
    if len(swings) < 4:
        return "ranging"

    sh = swings[swings["swing_high"]]["high"].values
    sl = swings[swings["swing_low"]]["low"].values

    if len(sh) < 2 or len(sl) < 2:
        return "ranging"

    hh = sh[-1] > sh[-2]   # higher high
    hl = sl[-1] > sl[-2]   # higher low
    lh = sh[-1] < sh[-2]   # lower high
    ll = sl[-1] < sl[-2]   # lower low

    if hh and hl:
        return "bullish"
    if lh and ll:
        return "bearish"
    return "ranging"


# ─── Break of Structure / Change of Character ───────────────────────────────

def detect_bos_choch(df: pd.DataFrame) -> List[BreakOfStructure]:
    results: List[BreakOfStructure] = []
    swings = df[df["swing_high"] | df["swing_low"]].copy()

    if len(swings) < 6:
        return results

    prev_structure = None   # "bullish" / "bearish"
    prev_sh = prev_sl = None
    swing_list = swings.iterrows()

    highs: List[tuple] = []
    lows:  List[tuple] = []

    for ts, row in swings.iterrows():
        if row["swing_high"]:
            highs.append((ts, row["high"]))
        if row["swing_low"]:
            lows.append((ts, row["low"]))

    close = df["close"]

    # BOS bullish: price closes above last swing high
    for i in range(1, len(highs)):
        prev_ts, prev_price = highs[i - 1]
        curr_ts, _ = highs[i]
        # find candles between prev and curr swing high
        segment = close.loc[prev_ts:curr_ts]
        if (segment > prev_price).any():
            # determine if it's BOS (continuation) or CHOCH (reversal)
            bos_type = "CHOCH" if prev_structure == "bearish" else "BOS"
            results.append(BreakOfStructure(
                timestamp=str(curr_ts),
                price=round(prev_price, 6),
                type=bos_type,
                direction="bullish",
                confirmed=True,
            ))
            prev_structure = "bullish"

    # BOS bearish: price closes below last swing low
    for i in range(1, len(lows)):
        prev_ts, prev_price = lows[i - 1]
        curr_ts, _ = lows[i]
        segment = close.loc[prev_ts:curr_ts]
        if (segment < prev_price).any():
            bos_type = "CHOCH" if prev_structure == "bullish" else "BOS"
            results.append(BreakOfStructure(
                timestamp=str(curr_ts),
                price=round(prev_price, 6),
                type=bos_type,
                direction="bearish",
                confirmed=True,
            ))
            prev_structure = "bearish"

    # return last 10 events sorted chronologically
    results.sort(key=lambda x: x.timestamp)
    return results[-10:]


# ─── Order Blocks ────────────────────────────────────────────────────────────

def detect_order_blocks(df: pd.DataFrame) -> List[OrderBlock]:
    """
    An order block is the last opposing candle before a strong impulsive move.
    Bullish OB: last bearish candle before a bullish impulse that breaks structure.
    Bearish OB: last bullish candle before a bearish impulse that breaks structure.
    """
    order_blocks: List[OrderBlock] = []
    closes = df["close"].values
    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    n      = len(df)

    impulse_threshold = 0.003  # 0.3 % move per candle

    for i in range(3, n - 3):
        # look for bullish impulse (3-candle move)
        move_up = (closes[i + 1] - opens[i + 1]) / opens[i + 1]
        move_up2 = (closes[i + 2] - opens[i + 2]) / opens[i + 2]
        if move_up > impulse_threshold and move_up2 > 0:
            # find last bearish candle at or before i
            for j in range(i, max(i - 5, 0), -1):
                if closes[j] < opens[j]:
                    # this is the bullish OB
                    strength = min(1.0, abs(move_up + move_up2) * 20)
                    current_price = closes[-1]
                    mitigated = current_price <= highs[j]
                    ob = OrderBlock(
                        index=j,
                        timestamp=str(df.index[j]),
                        high=round(highs[j], 6),
                        low=round(lows[j], 6),
                        open=round(opens[j], 6),
                        close=round(closes[j], 6),
                        type="bullish",
                        strength=round(strength, 3),
                        mitigated=mitigated,
                    )
                    order_blocks.append(ob)
                    break

        # look for bearish impulse
        move_dn = (opens[i + 1] - closes[i + 1]) / opens[i + 1]
        move_dn2 = (opens[i + 2] - closes[i + 2]) / opens[i + 2]
        if move_dn > impulse_threshold and move_dn2 > 0:
            for j in range(i, max(i - 5, 0), -1):
                if closes[j] > opens[j]:
                    strength = min(1.0, abs(move_dn + move_dn2) * 20)
                    current_price = closes[-1]
                    mitigated = current_price >= lows[j]
                    ob = OrderBlock(
                        index=j,
                        timestamp=str(df.index[j]),
                        high=round(highs[j], 6),
                        low=round(lows[j], 6),
                        open=round(opens[j], 6),
                        close=round(closes[j], 6),
                        type="bearish",
                        strength=round(strength, 3),
                        mitigated=mitigated,
                    )
                    order_blocks.append(ob)
                    break

    # deduplicate by index proximity and keep strongest
    seen_indices: set = set()
    unique_obs: List[OrderBlock] = []
    for ob in sorted(order_blocks, key=lambda x: -x.strength):
        if not any(abs(ob.index - s) < 3 for s in seen_indices):
            seen_indices.add(ob.index)
            unique_obs.append(ob)
        if len(unique_obs) >= 8:
            break

    return sorted(unique_obs, key=lambda x: x.index)[-8:]


# ─── Fair Value Gaps ─────────────────────────────────────────────────────────

def detect_fvg(df: pd.DataFrame) -> List[FairValueGap]:
    """
    A Fair Value Gap (imbalance) occurs when candle[i-1].high < candle[i+1].low (bullish FVG)
    or candle[i-1].low > candle[i+1].high (bearish FVG).
    """
    fvgs: List[FairValueGap] = []
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    n      = len(df)

    current_price = closes[-1]

    for i in range(1, n - 1):
        # Bullish FVG: gap above candle[i-1] below candle[i+1]
        if lows[i + 1] > highs[i - 1]:
            top    = lows[i + 1]
            bottom = highs[i - 1]
            gap_size = top - bottom
            if gap_size > 0:
                fill_pct = max(0.0, min(1.0, (top - current_price) / gap_size)) if current_price < top else 1.0
                fvgs.append(FairValueGap(
                    index=i,
                    timestamp=str(df.index[i]),
                    top=round(top, 6),
                    bottom=round(bottom, 6),
                    type="bullish",
                    filled=fill_pct >= 1.0,
                    fill_percentage=round(fill_pct, 3),
                ))

        # Bearish FVG: gap below candle[i-1] above candle[i+1]
        if highs[i + 1] < lows[i - 1]:
            top    = lows[i - 1]
            bottom = highs[i + 1]
            gap_size = top - bottom
            if gap_size > 0:
                fill_pct = max(0.0, min(1.0, (current_price - bottom) / gap_size)) if current_price > bottom else 1.0
                fvgs.append(FairValueGap(
                    index=i,
                    timestamp=str(df.index[i]),
                    top=round(top, 6),
                    bottom=round(bottom, 6),
                    type="bearish",
                    filled=fill_pct >= 1.0,
                    fill_percentage=round(fill_pct, 3),
                ))

    # Keep unfilled or recently filled FVGs closest to current price
    unfilled = [f for f in fvgs if not f.filled]
    unfilled.sort(key=lambda x: abs((x.top + x.bottom) / 2 - current_price))
    return unfilled[:10]


# ─── Liquidity Levels ────────────────────────────────────────────────────────

def detect_liquidity_levels(df: pd.DataFrame) -> List[LiquidityLevel]:
    """
    Liquidity sits above swing highs (buy-side) and below swing lows (sell-side).
    Equal highs/lows are extra-strong liquidity pools.
    """
    levels: List[LiquidityLevel] = []
    tolerance = df["close"].mean() * 0.001  # 0.1 % tolerance for "equal"
    current_price = df["close"].iloc[-1]

    swing_df = df[df["swing_high"] | df["swing_low"]].tail(30)

    # collect swing highs
    sh_prices = swing_df[swing_df["swing_high"]]["high"].values
    sl_prices = swing_df[swing_df["swing_low"]]["low"].values
    sh_ts     = swing_df[swing_df["swing_high"]].index
    sl_ts     = swing_df[swing_df["swing_low"]].index

    def count_touches(price_arr: np.ndarray, price: float, tol: float) -> int:
        return int(np.sum(np.abs(price_arr - price) <= tol))

    # Swing highs → buy-side liquidity
    for ts, price in zip(sh_ts, sh_prices):
        touches = count_touches(sh_prices, price, tolerance)
        ltype   = "equal_high" if touches >= 2 else "swing_high"
        swept   = current_price > price
        levels.append(LiquidityLevel(
            timestamp=str(ts),
            price=round(price, 6),
            type=ltype,
            swept=swept,
            strength=touches,
        ))

    # Swing lows → sell-side liquidity
    for ts, price in zip(sl_ts, sl_prices):
        touches = count_touches(sl_prices, price, tolerance)
        ltype   = "equal_low" if touches >= 2 else "swing_low"
        swept   = current_price < price
        levels.append(LiquidityLevel(
            timestamp=str(ts),
            price=round(price, 6),
            type=ltype,
            swept=swept,
            strength=touches,
        ))

    levels.sort(key=lambda x: abs(x.price - current_price))
    return levels[:12]


# ─── Premium / Discount ──────────────────────────────────────────────────────

def get_premium_discount(df: pd.DataFrame) -> str:
    recent_high = df["high"].rolling(50).max().iloc[-1]
    recent_low  = df["low"].rolling(50).min().iloc[-1]
    midpoint    = (recent_high + recent_low) / 2
    current     = df["close"].iloc[-1]

    if current > midpoint * 1.01:
        return "premium"
    if current < midpoint * 0.99:
        return "discount"
    return "equilibrium"


# ─── Main entry point ────────────────────────────────────────────────────────

def run_smc_analysis(df: pd.DataFrame) -> SMCAnalysis:
    df = find_swing_highs_lows(df, lookback=5)

    market_structure = analyze_market_structure(df)
    bos_choch        = detect_bos_choch(df)
    order_blocks     = detect_order_blocks(df)
    fvgs             = detect_fvg(df)
    liquidity        = detect_liquidity_levels(df)
    premium_discount = get_premium_discount(df)

    return SMCAnalysis(
        order_blocks=order_blocks,
        fair_value_gaps=fvgs,
        liquidity_levels=liquidity,
        break_of_structure=bos_choch,
        market_structure=market_structure,
        premium_discount=premium_discount,
    )
