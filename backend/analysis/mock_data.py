"""
Realistic OHLCV mock data generator.
Used as a fallback when yfinance cannot reach the internet.
Generates price data that looks like a real asset using GBM + trend regimes.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple

SEED_PRICES: Dict[str, float] = {
    "AAPL": 213.0, "MSFT": 420.0, "GOOGL": 175.0, "AMZN": 192.0,
    "META": 503.0, "TSLA": 173.0, "NVDA": 118.0, "NFLX": 650.0,
    "AMD": 155.0,  "INTC": 31.0,  "JPM": 214.0,   "BAC": 40.0,
    "V": 275.0,    "MA": 472.0,   "MSFT": 420.0,
    "BTC-USD": 67000.0, "ETH-USD": 3500.0, "BNB-USD": 580.0,
    "SOL-USD": 175.0,   "XRP-USD": 0.55,   "DOGE-USD": 0.15,
    "ADA-USD": 0.45,    "AVAX-USD": 38.0,  "MATIC-USD": 0.8,
    "^GSPC": 5300.0,    "^NDX": 18500.0,   "^DJI": 39000.0,
    "^VIX": 14.5,       "^FTSE": 8200.0,   "^N225": 38000.0,
    "EURUSD=X": 1.082,  "GBPUSD=X": 1.268, "USDJPY=X": 154.0,
}

TIMEFRAME_SECONDS: Dict[str, int] = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400, "1wk": 604800,
}

TIMEFRAME_BARS: Dict[str, int] = {
    "1m": 200, "5m": 300, "15m": 300, "30m": 300,
    "1h": 300, "4h": 300, "1d": 365, "1wk": 104,
}


def _base_price(symbol: str) -> float:
    sym = symbol.upper()
    for k, v in SEED_PRICES.items():
        if sym == k.upper():
            return v
    # Derive a deterministic price from symbol hash
    h = sum(ord(c) for c in sym) % 1000
    return 50.0 + h * 0.5


def generate_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame:
    np.random.seed(abs(hash(symbol.upper())) % (2**31))

    base   = _base_price(symbol)
    n_bars = TIMEFRAME_BARS.get(timeframe, 300)
    tf_sec = TIMEFRAME_SECONDS.get(timeframe, 3600)

    # Volatility scaled to timeframe
    annual_vol = 0.45 if "USD" in symbol.upper() else 0.25
    bar_vol    = annual_vol * np.sqrt(tf_sec / (252 * 86400))

    # Generate price path with regime changes (trending + ranging segments)
    prices = [base]
    regime_len = n_bars // 5
    for seg in range(5):
        drift = np.random.choice([-1, 0, 1]) * bar_vol * 0.3
        seg_prices = [prices[-1]]
        for _ in range(regime_len):
            ret = drift + np.random.normal(0, bar_vol)
            seg_prices.append(seg_prices[-1] * (1 + ret))
        prices.extend(seg_prices[1:])

    prices = prices[:n_bars]

    # Build OHLCV candles from close prices
    opens, highs, lows, closes, volumes = [], [], [], [], []
    now  = datetime.utcnow().replace(second=0, microsecond=0)
    start_ts = now - timedelta(seconds=tf_sec * n_bars)
    timestamps = [start_ts + timedelta(seconds=tf_sec * i) for i in range(n_bars)]

    avg_vol = base * 1e6 / (n_bars * base)  # rough volume

    for i, close in enumerate(prices):
        prev = prices[i - 1] if i > 0 else close
        open_ = prev * (1 + np.random.normal(0, bar_vol * 0.1))
        wick_mult = abs(np.random.normal(1.0, 0.5))
        high  = max(open_, close) * (1 + abs(np.random.normal(0, bar_vol)) * wick_mult)
        low   = min(open_, close) * (1 - abs(np.random.normal(0, bar_vol)) * wick_mult)
        vol   = abs(np.random.normal(avg_vol * base, avg_vol * base * 0.5))
        opens.append(open_)
        highs.append(high)
        lows.append(low)
        closes.append(close)
        volumes.append(vol)

    df = pd.DataFrame({
        "open":   opens,
        "high":   highs,
        "low":    lows,
        "close":  closes,
        "volume": volumes,
    }, index=pd.DatetimeIndex(timestamps))

    return df
