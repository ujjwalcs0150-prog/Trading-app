import yfinance as yf
import pandas as pd
from typing import Tuple
from datetime import datetime


MOCK_MODE = False  # set True to always use mock data

TIMEFRAME_MAP = {
    "1m":  ("7d",  "1m"),
    "5m":  ("60d", "5m"),
    "15m": ("60d", "15m"),
    "30m": ("60d", "30m"),
    "1h":  ("730d","1h"),
    "4h":  ("730d","1h"),   # yfinance lacks 4h; we resample from 1h
    "1d":  ("5y",  "1d"),
    "1wk": ("10y", "1wk"),
}

CRYPTO_SUFFIXES = ["-USD", "-USDT", "USDT", "-BTC"]
INDEX_PREFIXES  = ["^", "SPX", "NDX", "DJI", "FTSE", "DAX", "NIFTY"]


def detect_asset_type(symbol: str) -> str:
    sym = symbol.upper()
    if any(sym.startswith(p) for p in INDEX_PREFIXES) or sym.startswith("^"):
        return "index"
    if any(sym.endswith(s) for s in CRYPTO_SUFFIXES) or sym in {
        "BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE", "AVAX", "MATIC", "DOT"
    }:
        return "crypto"
    return "stock"


def normalize_symbol(symbol: str, asset_type: str) -> str:
    sym = symbol.upper().strip()
    if asset_type == "crypto":
        if not any(sym.endswith(s) for s in CRYPTO_SUFFIXES):
            sym = sym + "-USD"
    return sym


def fetch_ohlcv(symbol: str, timeframe: str) -> Tuple[pd.DataFrame, str]:
    asset_type = detect_asset_type(symbol)

    if MOCK_MODE:
        from analysis.mock_data import generate_ohlcv
        return generate_ohlcv(symbol, timeframe), asset_type

    period, interval = TIMEFRAME_MAP.get(timeframe, ("60d", "1d"))
    sym = normalize_symbol(symbol, asset_type)

    try:
        ticker = yf.Ticker(sym)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df.empty:
            ticker = yf.Ticker(symbol.upper())
            df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if not df.empty:
            df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_convert("UTC").tz_localize(None)
            df.columns = [c.lower() for c in df.columns]
            df = df[["open", "high", "low", "close", "volume"]].dropna()
            if timeframe == "4h":
                df = df.resample("4h").agg({
                    "open":   "first",
                    "high":   "max",
                    "low":    "min",
                    "close":  "last",
                    "volume": "sum",
                }).dropna()
            df = df.tail(500)
            return df, asset_type
    except Exception:
        pass

    # Fallback to mock data when network is unavailable
    from analysis.mock_data import generate_ohlcv
    return generate_ohlcv(symbol, timeframe), asset_type
