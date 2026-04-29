export interface OrderBlock {
  index: number
  timestamp: string
  high: number
  low: number
  open: number
  close: number
  type: 'bullish' | 'bearish'
  strength: number
  mitigated: boolean
}

export interface FairValueGap {
  index: number
  timestamp: string
  top: number
  bottom: number
  type: 'bullish' | 'bearish'
  filled: boolean
  fill_percentage: number
}

export interface LiquidityLevel {
  timestamp: string
  price: number
  type: 'swing_high' | 'swing_low' | 'equal_high' | 'equal_low'
  swept: boolean
  strength: number
}

export interface BreakOfStructure {
  timestamp: string
  price: number
  type: 'BOS' | 'CHOCH'
  direction: 'bullish' | 'bearish'
  confirmed: boolean
}

export interface KillZone {
  name: string
  start_hour: number
  end_hour: number
  active: boolean
  description: string
}

export interface OTELevel {
  fib_level: number
  price: number
  label: string
  in_ote: boolean
}

export interface CandlePattern {
  timestamp: string
  pattern: string
  signal: 'bullish' | 'bearish' | 'neutral'
  strength: number
  description: string
}

export interface SupportResistance {
  price: number
  type: 'support' | 'resistance'
  strength: number
  touches: number
  last_tested: string
}

export interface TradeSetup {
  signal: 'BUY' | 'SELL' | 'NEUTRAL'
  entry: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  risk_reward: number
  confidence: number
  reasons: string[]
  timeframe: string
  asset_type: string
}

export interface AnalysisResponse {
  symbol: string
  asset_type: string
  timeframe: string
  current_price: number
  price_change_pct: number
  smc: {
    order_blocks: OrderBlock[]
    fair_value_gaps: FairValueGap[]
    liquidity_levels: LiquidityLevel[]
    break_of_structure: BreakOfStructure[]
    market_structure: string
    premium_discount: string
  }
  ict: {
    kill_zones: KillZone[]
    ote_levels: OTELevel[]
    amd_phase: string
    dealing_range_high: number
    dealing_range_low: number
    equilibrium: number
    optimal_entry: number | null
  }
  price_action: {
    trend: string
    candle_patterns: CandlePattern[]
    support_resistance: SupportResistance[]
    momentum: string
    key_levels: number[]
  }
  trade_setup: TradeSetup
  chart_data: { time: number; open: number; high: number; low: number; close: number }[]
  volume_data: { time: number; value: number; color: string }[]
  analysis_timestamp: string
}

export interface SearchResult {
  symbol: string
  category: string
}

// On Android (Capacitor) we can't use the Vite proxy — hit the backend directly.
// Set VITE_API_URL=http://<your-server-ip>:8000 before building for Android.
// On web (dev) the Vite proxy rewrites /api → http://localhost:8000.
const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api'

export async function analyzeSymbol(symbol: string, timeframe: string): Promise<AnalysisResponse> {
  const res = await fetch(`${BASE}/analyze?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function searchSymbols(q: string): Promise<SearchResult[]> {
  const res = await fetch(`${BASE}/search?q=${encodeURIComponent(q)}`)
  if (!res.ok) return []
  return res.json()
}
