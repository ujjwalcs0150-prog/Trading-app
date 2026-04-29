from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from analysis.data_fetcher import fetch_ohlcv, detect_asset_type, normalize_symbol
from analysis.smc_analysis import run_smc_analysis
from analysis.ict_analysis import run_ict_analysis
from analysis.price_action import run_price_action_analysis
from analysis.trade_signals import generate_trade_setup
from models.schemas import AnalysisResponse

app = FastAPI(
    title="SMC/ICT Trading Analysis API",
    description="Smart Money Concepts, ICT, and Price Action analysis for stocks, crypto, and indices",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/analyze", response_model=AnalysisResponse)
def analyze(
    symbol: str   = Query(..., description="Ticker symbol, e.g. AAPL, BTC-USD, ^GSPC"),
    timeframe: str = Query("1h", description="Timeframe: 1m,5m,15m,30m,1h,4h,1d,1wk"),
):
    try:
        df, asset_type = fetch_ohlcv(symbol, timeframe)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    if len(df) < 30:
        raise HTTPException(status_code=422, detail="Insufficient data for analysis (need ≥30 bars)")

    # Run all analysis engines
    smc = run_smc_analysis(df)
    ict = run_ict_analysis(df)
    pa  = run_price_action_analysis(df)
    trade_setup = generate_trade_setup(df, smc, ict, pa, asset_type, timeframe)

    current_price = float(df["close"].iloc[-1])
    prev_price    = float(df["close"].iloc[-2]) if len(df) >= 2 else current_price
    price_change  = round((current_price - prev_price) / prev_price * 100, 4)

    # Build chart data for frontend (last 200 candles)
    chart_df = df.tail(200).copy()
    chart_data = [
        {
            "time":  int(ts.timestamp()) if hasattr(ts, "timestamp") else int(pd.Timestamp(ts).timestamp()),
            "open":  round(float(row["open"]), 6),
            "high":  round(float(row["high"]), 6),
            "low":   round(float(row["low"]), 6),
            "close": round(float(row["close"]), 6),
        }
        for ts, row in chart_df.iterrows()
    ]
    volume_data = [
        {
            "time":  int(ts.timestamp()) if hasattr(ts, "timestamp") else int(pd.Timestamp(ts).timestamp()),
            "value": round(float(row["volume"]), 2),
            "color": "#26a69a" if row["close"] >= row["open"] else "#ef5350",
        }
        for ts, row in chart_df.iterrows()
    ]

    return AnalysisResponse(
        symbol=symbol.upper(),
        asset_type=asset_type,
        timeframe=timeframe,
        current_price=round(current_price, 6),
        price_change_pct=price_change,
        smc=smc,
        ict=ict,
        price_action=pa,
        trade_setup=trade_setup,
        chart_data=chart_data,
        volume_data=volume_data,
        analysis_timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/search")
def search_symbols(q: str = Query(..., min_length=1)):
    """Quick symbol suggestions — returns popular matches."""
    popular = {
        "stocks":  ["AAPL","MSFT","GOOGL","AMZN","META","TSLA","NVDA","NFLX","AMD","INTC",
                    "JPM","BAC","GS","V","MA","BRK-B","JNJ","PFE","XOM","CVX"],
        "crypto":  ["BTC-USD","ETH-USD","BNB-USD","SOL-USD","ADA-USD","XRP-USD",
                    "DOGE-USD","AVAX-USD","MATIC-USD","DOT-USD","LINK-USD","UNI-USD"],
        "indices": ["^GSPC","^NDX","^DJI","^RUT","^VIX","^FTSE","^GDAXI","^N225","^HSI"],
        "forex":   ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X"],
    }
    q = q.upper()
    results = []
    for category, symbols in popular.items():
        for sym in symbols:
            if q in sym.upper():
                results.append({"symbol": sym, "category": category})
    return results[:15]
