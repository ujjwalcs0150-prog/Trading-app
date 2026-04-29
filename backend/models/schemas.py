from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1wk"


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    INDEX = "index"
    FOREX = "forex"


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class OrderBlock(BaseModel):
    index: int
    timestamp: str
    high: float
    low: float
    open: float
    close: float
    type: str  # "bullish" or "bearish"
    strength: float
    mitigated: bool


class FairValueGap(BaseModel):
    index: int
    timestamp: str
    top: float
    bottom: float
    type: str  # "bullish" or "bearish"
    filled: bool
    fill_percentage: float


class LiquidityLevel(BaseModel):
    timestamp: str
    price: float
    type: str  # "swing_high" or "swing_low" or "equal_high" or "equal_low"
    swept: bool
    strength: int


class BreakOfStructure(BaseModel):
    timestamp: str
    price: float
    type: str  # "BOS" or "CHOCH"
    direction: str  # "bullish" or "bearish"
    confirmed: bool


class KillZone(BaseModel):
    name: str
    start_hour: int
    end_hour: int
    active: bool
    description: str


class OTELevel(BaseModel):
    fib_level: float
    price: float
    label: str
    in_ote: bool


class CandlePattern(BaseModel):
    timestamp: str
    pattern: str
    signal: str  # "bullish" or "bearish"
    strength: float
    description: str


class SupportResistance(BaseModel):
    price: float
    type: str  # "support" or "resistance"
    strength: int
    touches: int
    last_tested: str


class TradeSetup(BaseModel):
    signal: SignalType
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    confidence: float
    reasons: List[str]
    timeframe: str
    asset_type: str


class SMCAnalysis(BaseModel):
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    liquidity_levels: List[LiquidityLevel]
    break_of_structure: List[BreakOfStructure]
    market_structure: str  # "bullish", "bearish", "ranging"
    premium_discount: str  # "premium", "discount", "equilibrium"


class ICTAnalysis(BaseModel):
    kill_zones: List[KillZone]
    ote_levels: List[OTELevel]
    amd_phase: str  # "accumulation", "manipulation", "distribution"
    dealing_range_high: float
    dealing_range_low: float
    equilibrium: float
    optimal_entry: Optional[float]


class PriceActionAnalysis(BaseModel):
    trend: str  # "uptrend", "downtrend", "sideways"
    candle_patterns: List[CandlePattern]
    support_resistance: List[SupportResistance]
    momentum: str  # "strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"
    key_levels: List[float]


class AnalysisResponse(BaseModel):
    symbol: str
    asset_type: str
    timeframe: str
    current_price: float
    price_change_pct: float
    smc: SMCAnalysis
    ict: ICTAnalysis
    price_action: PriceActionAnalysis
    trade_setup: TradeSetup
    chart_data: List[dict]
    volume_data: List[dict]
    analysis_timestamp: str
