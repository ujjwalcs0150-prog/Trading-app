import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Search, RefreshCw, TrendingUp } from 'lucide-react'
import { searchSymbols, SearchResult } from './services/api'
import { useAnalysis } from './hooks/useAnalysis'
import CandlestickChart from './components/CandlestickChart'
import TradeSetupCard from './components/TradeSetupCard'
import SMCPanel from './components/SMCPanel'
import ICTPanel from './components/ICTPanel'
import PriceActionPanel from './components/PriceActionPanel'

const TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1d', '1wk']

type TabKey = 'smc' | 'ict' | 'price_action'

export default function App() {
  const [symbol, setSymbol]       = useState('AAPL')
  const [inputVal, setInputVal]   = useState('AAPL')
  const [timeframe, setTimeframe] = useState('1h')
  const [tab, setTab]             = useState<TabKey>('smc')
  const [suggestions, setSuggestions] = useState<SearchResult[]>([])
  const [showSugg, setShowSugg]   = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)
  const { status, data, error, analyze } = useAnalysis()

  // Hide dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSugg(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = async (val: string) => {
    setInputVal(val)
    if (val.length < 1) { setSuggestions([]); return }
    const results = await searchSymbols(val)
    setSuggestions(results)
    setShowSugg(results.length > 0)
  }

  const selectSymbol = (sym: string) => {
    setInputVal(sym)
    setSymbol(sym)
    setShowSugg(false)
    analyze(sym, timeframe)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      setSymbol(inputVal.toUpperCase())
      setShowSugg(false)
      analyze(inputVal.toUpperCase(), timeframe)
    }
  }

  const handleTfChange = (tf: string) => {
    setTimeframe(tf)
    if (symbol) analyze(symbol, tf)
  }

  // Auto-analyze on first load
  useEffect(() => {
    analyze('AAPL', '1h')
  }, []) // eslint-disable-line

  const priceColor = data
    ? data.price_change_pct >= 0 ? 'var(--green)' : 'var(--red)'
    : 'var(--text-primary)'

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="logo">
          <TrendingUp size={22} className="logo-icon" />
          <span>SMC/ICT Analyzer</span>
        </div>

        <div className="search-container" ref={searchRef}>
          <Search size={14} className="search-icon" />
          <input
            className="search-input"
            value={inputVal}
            onChange={e => handleSearch(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => suggestions.length > 0 && setShowSugg(true)}
            placeholder="Search symbol… (AAPL, BTC-USD, ^GSPC)"
          />
          {showSugg && (
            <div className="search-dropdown">
              {suggestions.map((s, i) => (
                <div key={i} className="search-item" onClick={() => selectSymbol(s.symbol)}>
                  <span className="search-item-symbol">{s.symbol}</span>
                  <span className="search-item-cat">{s.category}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="tf-selector">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf}
              className={`tf-btn${timeframe === tf ? ' active' : ''}`}
              onClick={() => handleTfChange(tf)}
            >{tf}</button>
          ))}
        </div>

        <button
          className="analyze-btn"
          onClick={() => analyze(inputVal.toUpperCase(), timeframe)}
          disabled={status === 'loading'}
        >
          <RefreshCw size={14} className={status === 'loading' ? 'spinning' : ''} />
          {status === 'loading' ? 'Analyzing…' : 'Analyze'}
        </button>
      </header>

      {/* ── Main ── */}
      <main className="main-content">

        {status === 'loading' && (
          <div className="loading-screen">
            <div className="spinner" />
            <p>Fetching data & running SMC/ICT analysis…</p>
          </div>
        )}

        {status === 'error' && (
          <div className="error-box">
            <strong>Analysis Error:</strong> {error}
          </div>
        )}

        {status === 'idle' && (
          <div className="placeholder-screen">
            <TrendingUp size={48} color="var(--text-muted)" />
            <h2>SMC / ICT / Price Action Analyzer</h2>
            <p>Enter a stock, crypto, or index symbol above and click Analyze to get a comprehensive Smart Money Concepts, ICT, and Price Action trade setup.</p>
            <div className="tag-list" style={{ justifyContent: 'center', marginTop: 8 }}>
              {['AAPL','BTC-USD','ETH-USD','^GSPC','TSLA','NVDA','EUR/USD'].map(s => (
                <span key={s} className="tag blue" style={{ cursor: 'pointer' }} onClick={() => selectSymbol(s)}>{s}</span>
              ))}
            </div>
          </div>
        )}

        {status === 'success' && data && (
          <>
            {/* Symbol bar */}
            <div className="symbol-bar">
              <span className="symbol-name">{data.symbol}</span>
              <span className="symbol-price" style={{ color: priceColor }}>
                {data.current_price.toLocaleString(undefined, { maximumFractionDigits: 6 })}
              </span>
              <span className={`price-change ${data.price_change_pct >= 0 ? 'positive' : 'negative'}`}>
                {data.price_change_pct >= 0 ? '+' : ''}{data.price_change_pct.toFixed(2)}%
              </span>
              <span className="tag gray" style={{ textTransform: 'capitalize' }}>{data.asset_type}</span>
              <span className="tag blue">{data.timeframe}</span>
              <span className={`signal-badge ${data.trade_setup.signal}`}>
                {data.trade_setup.signal}
              </span>
            </div>

            {/* Chart */}
            <CandlestickChart data={data} />

            {/* Trade Setup */}
            <div className="grid-2">
              <TradeSetupCard setup={data.trade_setup} />
            </div>

            {/* Analysis Tabs */}
            <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--border)', paddingBottom: 0 }}>
              {([
                { key: 'smc',          label: '📊 SMC Analysis' },
                { key: 'ict',          label: '🎯 ICT Analysis' },
                { key: 'price_action', label: '🕯️ Price Action' },
              ] as { key: TabKey; label: string }[]).map(t => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  style={{
                    background: 'none',
                    border: 'none',
                    borderBottom: tab === t.key ? '2px solid var(--blue)' : '2px solid transparent',
                    color: tab === t.key ? 'var(--text-primary)' : 'var(--text-secondary)',
                    padding: '8px 16px',
                    cursor: 'pointer',
                    fontWeight: tab === t.key ? 700 : 400,
                    fontSize: 14,
                    transition: 'all 0.15s',
                    marginBottom: -1,
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="grid-2" style={{ gridTemplateColumns: tab === 'ict' ? '1fr 1fr' : '1fr 1fr' }}>
              {tab === 'smc'          && <SMCPanel data={data} />}
              {tab === 'ict'          && <ICTPanel data={data} />}
              {tab === 'price_action' && <PriceActionPanel data={data} />}
            </div>

            <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'right' }}>
              Analysis: {new Date(data.analysis_timestamp).toLocaleString()} UTC
              &nbsp;·&nbsp; <strong style={{ color: 'var(--red)' }}>Not financial advice.</strong> For educational use only.
            </div>
          </>
        )}
      </main>

      <style>{`
        .spinning { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
