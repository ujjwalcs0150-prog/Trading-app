"""
ICT (Inner Circle Trader) Analysis Engine
Detects: Kill Zones, OTE (Fibonacci), AMD Phases, Dealing Ranges, IPDA Logic
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Optional
from models.schemas import ICTAnalysis, KillZone, OTELevel


# ─── Kill Zones ──────────────────────────────────────────────────────────────

KILL_ZONES = [
    {"name": "Asian Session",    "start": 20, "end": 0,  "desc": "Low volatility range formation (NY time 8pm–midnight)"},
    {"name": "London Open",      "start": 2,  "end": 5,  "desc": "High probability reversal or expansion (2am–5am EST)"},
    {"name": "NY AM Session",    "start": 8,  "end": 11, "desc": "Most liquid session, major moves (8am–11am EST)"},
    {"name": "NY PM Session",    "start": 13, "end": 16, "desc": "Secondary NY expansion (1pm–4pm EST)"},
    {"name": "London Close",     "start": 10, "end": 12, "desc": "Reversal at London close, NY open confluence"},
]


def get_kill_zones() -> List[KillZone]:
    now_utc  = datetime.now(timezone.utc)
    est_hour = (now_utc.hour - 5) % 24   # rough EST offset (ignoring DST for simplicity)

    result = []
    for kz in KILL_ZONES:
        s, e = kz["start"], kz["end"]
        if s < e:
            active = s <= est_hour < e
        else:
            active = est_hour >= s or est_hour < e
        result.append(KillZone(
            name=kz["name"],
            start_hour=s,
            end_hour=e,
            active=active,
            description=kz["desc"],
        ))
    return result


# ─── OTE – Optimal Trade Entry (Fibonacci 61.8–79% retracement) ─────────────

OTE_FIBS = [
    (0.0,   "Swing Low (0%)"),
    (0.236, "23.6% Retracement"),
    (0.382, "38.2% Retracement"),
    (0.5,   "50% Equilibrium"),
    (0.618, "61.8% OTE Level"),
    (0.705, "70.5% OTE Midpoint"),
    (0.786, "78.6% Deep OTE"),
    (1.0,   "Swing High (100%)"),
    (1.272, "127.2% Extension"),
    (1.618, "161.8% Extension"),
    (2.0,   "200% Extension"),
]


def calculate_ote(df: pd.DataFrame) -> List[OTELevel]:
    """Calculate OTE from the last significant swing leg."""
    # Find last swing high and low in most recent 50 candles
    tail = df.tail(50)
    swing_high_price = tail["high"].max()
    swing_low_price  = tail["low"].min()

    sh_idx = tail["high"].idxmax()
    sl_idx = tail["low"].idxmin()

    current_price = df["close"].iloc[-1]
    levels: List[OTELevel] = []

    # Determine swing direction
    if sh_idx > sl_idx:
        # Most recent swing is upward: Low → High, expect pullback into OTE
        swing_range = swing_high_price - swing_low_price
        for ratio, label in OTE_FIBS:
            price = swing_high_price - swing_range * ratio
            in_ote = 0.618 <= ratio <= 0.786
            levels.append(OTELevel(
                fib_level=ratio,
                price=round(price, 6),
                label=label,
                in_ote=in_ote,
            ))
    else:
        # Most recent swing is downward: High → Low, expect retracement into OTE
        swing_range = swing_high_price - swing_low_price
        for ratio, label in OTE_FIBS:
            price = swing_low_price + swing_range * ratio
            in_ote = 0.618 <= ratio <= 0.786
            levels.append(OTELevel(
                fib_level=ratio,
                price=round(price, 6),
                label=label,
                in_ote=in_ote,
            ))

    return levels


def get_optimal_entry(ote_levels: List[OTELevel], current_price: float) -> Optional[float]:
    """Return closest OTE level to current price."""
    ote_zone = [l for l in ote_levels if l.in_ote]
    if not ote_zone:
        return None
    closest = min(ote_zone, key=lambda l: abs(l.price - current_price))
    return closest.price


# ─── AMD Phase – Accumulation / Manipulation / Distribution ─────────────────

def detect_amd_phase(df: pd.DataFrame) -> str:
    """
    Simplified AMD detection over the last session (~24 candles for hourly).
    - Accumulation: tight range, low volatility
    - Manipulation: spike beyond range (stop hunt)
    - Distribution: directional expansion after manipulation
    """
    session = df.tail(24)
    price_range = session["high"].max() - session["low"].min()
    avg_range   = (session["high"] - session["low"]).mean()
    last_3_range = (session.tail(3)["high"] - session.tail(3)["low"]).mean()

    volatility_ratio = last_3_range / avg_range if avg_range > 0 else 1.0

    # Detect if price spiked then reversed (manipulation)
    first_half_high = session.head(12)["high"].max()
    first_half_low  = session.head(12)["low"].min()
    second_half_high = session.tail(12)["high"].max()
    second_half_low  = session.tail(12)["low"].min()

    spike_above = second_half_high > first_half_high and session["close"].iloc[-1] < first_half_high
    spike_below = second_half_low < first_half_low  and session["close"].iloc[-1] > first_half_low

    if spike_above or spike_below:
        return "manipulation"

    if volatility_ratio > 1.5:
        return "distribution"

    return "accumulation"


# ─── Dealing Range ───────────────────────────────────────────────────────────

def get_dealing_range(df: pd.DataFrame, lookback: int = 20) -> tuple:
    """IPDA dealing range: 20/40/60 candle range high and low."""
    tail = df.tail(lookback)
    rng_high = tail["high"].max()
    rng_low  = tail["low"].min()
    equilibrium = (rng_high + rng_low) / 2
    return round(rng_high, 6), round(rng_low, 6), round(equilibrium, 6)


# ─── Main entry point ────────────────────────────────────────────────────────

def run_ict_analysis(df: pd.DataFrame) -> ICTAnalysis:
    kill_zones      = get_kill_zones()
    ote_levels      = calculate_ote(df)
    amd_phase       = detect_amd_phase(df)
    dr_high, dr_low, equil = get_dealing_range(df, lookback=20)
    current_price   = df["close"].iloc[-1]
    optimal_entry   = get_optimal_entry(ote_levels, current_price)

    return ICTAnalysis(
        kill_zones=kill_zones,
        ote_levels=ote_levels,
        amd_phase=amd_phase,
        dealing_range_high=dr_high,
        dealing_range_low=dr_low,
        equilibrium=equil,
        optimal_entry=optimal_entry,
    )
