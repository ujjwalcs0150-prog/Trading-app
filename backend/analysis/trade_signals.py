"""
Trade Signal Aggregator
Combines SMC + ICT + Price Action signals into a unified trade setup
with entry, SL, TP, RR ratio, and confidence score.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple
from models.schemas import (
    SMCAnalysis, ICTAnalysis, PriceActionAnalysis,
    TradeSetup, SignalType
)


# ─── Scoring weights ─────────────────────────────────────────────────────────

WEIGHTS = {
    "smc_market_structure":   0.20,
    "smc_order_block":        0.15,
    "smc_fvg":                0.10,
    "smc_liquidity":          0.10,
    "smc_premium_discount":   0.10,
    "ict_ote":                0.10,
    "ict_amd":                0.05,
    "pa_trend":               0.10,
    "pa_candle_pattern":      0.05,
    "pa_momentum":            0.05,
}


def _score_smc(smc: SMCAnalysis, current_price: float) -> Tuple[float, List[str]]:
    """Returns a net directional score [-1, +1] and list of reasons."""
    score = 0.0
    reasons: List[str] = []

    # Market structure
    if smc.market_structure == "bullish":
        score += WEIGHTS["smc_market_structure"]
        reasons.append("✅ SMC: Bullish market structure (HH/HL)")
    elif smc.market_structure == "bearish":
        score -= WEIGHTS["smc_market_structure"]
        reasons.append("🔴 SMC: Bearish market structure (LL/LH)")
    else:
        reasons.append("⚪ SMC: Ranging market structure")

    # Premium / Discount
    if smc.premium_discount == "discount":
        score += WEIGHTS["smc_premium_discount"]
        reasons.append("✅ SMC: Price in discount zone — buy opportunity")
    elif smc.premium_discount == "premium":
        score -= WEIGHTS["smc_premium_discount"]
        reasons.append("🔴 SMC: Price in premium zone — sell opportunity")
    else:
        reasons.append("⚪ SMC: Price at equilibrium")

    # Nearest Order Block
    nearby_obs = sorted(
        smc.order_blocks,
        key=lambda ob: abs((ob.high + ob.low) / 2 - current_price)
    )
    if nearby_obs:
        ob = nearby_obs[0]
        mid = (ob.high + ob.low) / 2
        if ob.type == "bullish" and not ob.mitigated and current_price >= ob.low and current_price <= ob.high * 1.005:
            score += WEIGHTS["smc_order_block"] * ob.strength
            reasons.append(f"✅ SMC: Inside bullish Order Block @ {ob.low:.4f}–{ob.high:.4f}")
        elif ob.type == "bearish" and not ob.mitigated and current_price >= ob.low * 0.995 and current_price <= ob.high:
            score -= WEIGHTS["smc_order_block"] * ob.strength
            reasons.append(f"🔴 SMC: Inside bearish Order Block @ {ob.low:.4f}–{ob.high:.4f}")

    # Fair Value Gaps
    nearby_fvgs = sorted(
        [f for f in smc.fair_value_gaps if not f.filled],
        key=lambda f: abs((f.top + f.bottom) / 2 - current_price)
    )
    if nearby_fvgs:
        fvg = nearby_fvgs[0]
        if fvg.type == "bullish" and current_price <= fvg.top:
            score += WEIGHTS["smc_fvg"]
            reasons.append(f"✅ SMC: Bullish FVG at {fvg.bottom:.4f}–{fvg.top:.4f} acting as support")
        elif fvg.type == "bearish" and current_price >= fvg.bottom:
            score -= WEIGHTS["smc_fvg"]
            reasons.append(f"🔴 SMC: Bearish FVG at {fvg.bottom:.4f}–{fvg.top:.4f} acting as resistance")

    # Liquidity: price approaching unswept liquidity
    unswept = [l for l in smc.liquidity_levels if not l.swept]
    above_liq = [l for l in unswept if l.price > current_price]
    below_liq = [l for l in unswept if l.price < current_price]
    if below_liq:
        nearest_below = min(below_liq, key=lambda l: current_price - l.price)
        gap = (current_price - nearest_below.price) / current_price
        if gap < 0.01:
            score += WEIGHTS["smc_liquidity"] * 0.5
            reasons.append(f"✅ SMC: Buy-side liquidity pool above @ {nearest_below.price:.4f}")
    if above_liq:
        nearest_above = min(above_liq, key=lambda l: l.price - current_price)
        gap = (nearest_above.price - current_price) / current_price
        if gap < 0.01:
            score -= WEIGHTS["smc_liquidity"] * 0.5
            reasons.append(f"🔴 SMC: Sell-side liquidity pool below @ {nearest_above.price:.4f}")

    # BOS/CHOCH direction
    recent_bos = smc.break_of_structure[-3:] if smc.break_of_structure else []
    for bos in recent_bos:
        if bos.direction == "bullish":
            score += 0.02
        elif bos.direction == "bearish":
            score -= 0.02
    if recent_bos:
        last = recent_bos[-1]
        reasons.append(f"📊 SMC: Recent {last.type} ({last.direction}) @ {last.price:.4f}")

    return score, reasons


def _score_ict(ict: ICTAnalysis, current_price: float) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    # OTE zone
    in_ote = any(l.in_ote and abs(l.price - current_price) / current_price < 0.005
                 for l in ict.ote_levels)
    if in_ote:
        score += WEIGHTS["ict_ote"]
        reasons.append("✅ ICT: Price inside Optimal Trade Entry (61.8–78.6%) zone")
    else:
        reasons.append("⚪ ICT: Price outside OTE zone")

    # Dealing range position
    dr_range = ict.dealing_range_high - ict.dealing_range_low
    if dr_range > 0:
        position = (current_price - ict.dealing_range_low) / dr_range
        if position < 0.35:
            score += WEIGHTS["ict_ote"] * 0.5
            reasons.append(f"✅ ICT: Price in lower 35% of dealing range — discount")
        elif position > 0.65:
            score -= WEIGHTS["ict_ote"] * 0.5
            reasons.append(f"🔴 ICT: Price in upper 35% of dealing range — premium")

    # AMD Phase
    if ict.amd_phase == "accumulation":
        reasons.append("⚪ ICT: AMD Phase — Accumulation (range bound, await breakout)")
    elif ict.amd_phase == "manipulation":
        score += WEIGHTS["ict_amd"] * 0.5
        reasons.append("⚠️ ICT: AMD Phase — Manipulation detected (stop hunt), reversal likely")
    elif ict.amd_phase == "distribution":
        score += WEIGHTS["ict_amd"]
        reasons.append("✅ ICT: AMD Phase — Distribution (trend in progress)")

    # Kill zone
    active_kz = [kz for kz in ict.kill_zones if kz.active]
    if active_kz:
        kz = active_kz[0]
        reasons.append(f"🕐 ICT: Active Kill Zone — {kz.name} ({kz.description})")
        score += 0.02  # slight bonus for being in a kill zone
    else:
        reasons.append("⚪ ICT: No active kill zone")

    return score, reasons


def _score_price_action(pa: PriceActionAnalysis, current_price: float) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    # Trend
    if pa.trend == "uptrend":
        score += WEIGHTS["pa_trend"]
        reasons.append("✅ PA: Uptrend confirmed (EMA 20 > 50 > 200)")
    elif pa.trend == "downtrend":
        score -= WEIGHTS["pa_trend"]
        reasons.append("🔴 PA: Downtrend confirmed (EMA 20 < 50 < 200)")
    else:
        reasons.append("⚪ PA: Sideways / no clear trend")

    # Momentum (RSI)
    if pa.momentum == "strong_bullish":
        score += WEIGHTS["pa_momentum"]
        reasons.append("✅ PA: RSI overbought (>70) — strong momentum")
    elif pa.momentum == "bullish":
        score += WEIGHTS["pa_momentum"] * 0.6
        reasons.append("✅ PA: RSI bullish (55–70)")
    elif pa.momentum == "strong_bearish":
        score -= WEIGHTS["pa_momentum"]
        reasons.append("🔴 PA: RSI oversold (<30) — bearish momentum")
    elif pa.momentum == "bearish":
        score -= WEIGHTS["pa_momentum"] * 0.6
        reasons.append("🔴 PA: RSI bearish (30–45)")
    else:
        reasons.append("⚪ PA: RSI neutral (45–55)")

    # Candle patterns
    recent_patterns = pa.candle_patterns[-3:]
    for pat in recent_patterns:
        if pat.signal == "bullish":
            score += WEIGHTS["pa_candle_pattern"] * pat.strength
            reasons.append(f"✅ PA: {pat.pattern} — {pat.description}")
        elif pat.signal == "bearish":
            score -= WEIGHTS["pa_candle_pattern"] * pat.strength
            reasons.append(f"🔴 PA: {pat.pattern} — {pat.description}")

    # Nearest S/R
    sr = sorted(pa.support_resistance, key=lambda x: abs(x.price - current_price))
    if sr:
        nearest = sr[0]
        gap_pct = abs(nearest.price - current_price) / current_price * 100
        if nearest.type == "support" and gap_pct < 1.0:
            score += 0.03
            reasons.append(f"✅ PA: Strong support @ {nearest.price:.4f} (touched {nearest.touches}x)")
        elif nearest.type == "resistance" and gap_pct < 1.0:
            score -= 0.03
            reasons.append(f"🔴 PA: Strong resistance @ {nearest.price:.4f} (touched {nearest.touches}x)")

    return score, reasons


# ─── SL/TP calculation ───────────────────────────────────────────────────────

def calculate_sl_tp(
    signal: SignalType,
    current_price: float,
    smc: SMCAnalysis,
    pa: PriceActionAnalysis,
    atr: float,
) -> Tuple[float, float, float, float]:
    """Returns (stop_loss, tp1, tp2, tp3)."""

    # Use nearby S/R for SL placement
    sr = sorted(pa.support_resistance, key=lambda x: abs(x.price - current_price))
    obs = sorted(smc.order_blocks, key=lambda ob: abs((ob.high + ob.low) / 2 - current_price))

    if signal == SignalType.BUY:
        # SL: below nearest support or OB low, min 1 ATR below entry
        sl_candidates = [current_price - atr * 1.5]
        for s in sr[:3]:
            if s.type == "support" and s.price < current_price:
                sl_candidates.append(s.price - atr * 0.3)
        for ob in obs[:2]:
            if ob.type == "bullish":
                sl_candidates.append(ob.low - atr * 0.2)
        sl = max(sl_candidates)  # tightest valid SL (nearest)
        sl = min(sl, current_price - atr)  # at least 1 ATR

        rr1_dist = (current_price - sl) * 1.5
        rr2_dist = (current_price - sl) * 2.5
        rr3_dist = (current_price - sl) * 4.0
        tp1 = current_price + rr1_dist
        tp2 = current_price + rr2_dist
        tp3 = current_price + rr3_dist

    else:  # SELL
        sl_candidates = [current_price + atr * 1.5]
        for s in sr[:3]:
            if s.type == "resistance" and s.price > current_price:
                sl_candidates.append(s.price + atr * 0.3)
        for ob in obs[:2]:
            if ob.type == "bearish":
                sl_candidates.append(ob.high + atr * 0.2)
        sl = min(sl_candidates)
        sl = max(sl, current_price + atr)

        rr1_dist = (sl - current_price) * 1.5
        rr2_dist = (sl - current_price) * 2.5
        rr3_dist = (sl - current_price) * 4.0
        tp1 = current_price - rr1_dist
        tp2 = current_price - rr2_dist
        tp3 = current_price - rr3_dist

    rr = abs(current_price - tp2) / abs(current_price - sl) if sl != current_price else 0
    return round(sl, 6), round(tp1, 6), round(tp2, 6), round(tp3, 6)


# ─── ATR helper ─────────────────────────────────────────────────────────────

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    high  = df["high"]
    low   = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    return float(tr.ewm(span=period, adjust=False).mean().iloc[-1])


# ─── Main aggregator ─────────────────────────────────────────────────────────

def generate_trade_setup(
    df: pd.DataFrame,
    smc: SMCAnalysis,
    ict: ICTAnalysis,
    pa: PriceActionAnalysis,
    asset_type: str,
    timeframe: str,
) -> TradeSetup:
    current_price = float(df["close"].iloc[-1])
    atr           = calculate_atr(df)

    smc_score, smc_reasons = _score_smc(smc, current_price)
    ict_score, ict_reasons = _score_ict(ict, current_price)
    pa_score,  pa_reasons  = _score_price_action(pa, current_price)

    total_score = smc_score + ict_score + pa_score
    all_reasons = smc_reasons + ict_reasons + pa_reasons

    # Signal determination
    if total_score >= 0.20:
        signal = SignalType.BUY
    elif total_score <= -0.20:
        signal = SignalType.SELL
    else:
        signal = SignalType.NEUTRAL

    # Confidence: map score magnitude to 0–100 %
    confidence = min(100.0, abs(total_score) * 200)
    confidence = round(confidence, 1)

    if signal == SignalType.NEUTRAL:
        entry  = current_price
        sl     = current_price - atr * 2
        tp1    = current_price + atr * 1.5
        tp2    = current_price + atr * 2.5
        tp3    = current_price + atr * 4.0
        rr     = 1.5
    else:
        sl, tp1, tp2, tp3 = calculate_sl_tp(signal, current_price, smc, pa, atr)
        entry = current_price
        rr    = round(abs(entry - tp2) / abs(entry - sl), 2) if sl != entry else 0

    return TradeSetup(
        signal=signal,
        entry=round(entry, 6),
        stop_loss=round(sl, 6),
        take_profit_1=round(tp1, 6),
        take_profit_2=round(tp2, 6),
        take_profit_3=round(tp3, 6),
        risk_reward=rr,
        confidence=confidence,
        reasons=all_reasons,
        timeframe=timeframe,
        asset_type=asset_type,
    )
