import { AnalysisResponse } from '../services/api'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Props { data: AnalysisResponse }

const fmt = (n: number) => n.toLocaleString(undefined, { maximumFractionDigits: 6 })

const trendIcon = (t: string) => {
  if (t === 'uptrend')   return <TrendingUp size={14} color="var(--green)" />
  if (t === 'downtrend') return <TrendingDown size={14} color="var(--red)" />
  return <Minus size={14} color="var(--text-secondary)" />
}

const momentumColor = (m: string) => {
  if (m === 'strong_bullish') return 'var(--green)'
  if (m === 'bullish')        return 'var(--green-bright)'
  if (m === 'strong_bearish') return 'var(--red)'
  if (m === 'bearish')        return 'var(--red-bright)'
  return 'var(--text-secondary)'
}

const patternSignalIcon = (s: string) => {
  if (s === 'bullish') return '▲'
  if (s === 'bearish') return '▼'
  return '↔'
}

export default function PriceActionPanel({ data }: Props) {
  const { price_action: pa } = data

  return (
    <>
      {/* Trend + Momentum */}
      <div className="card">
        <div className="card-title">📈 Trend & Momentum</div>
        <div style={{ display: 'flex', gap: 20, marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Trend (EMA Stack)</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 15, fontWeight: 700 }}>
              {trendIcon(pa.trend)}
              <span style={{ color: pa.trend === 'uptrend' ? 'var(--green)' : pa.trend === 'downtrend' ? 'var(--red)' : 'var(--text-secondary)', textTransform: 'capitalize' }}>
                {pa.trend}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Momentum (RSI)</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: momentumColor(pa.momentum), textTransform: 'capitalize' }}>
              {pa.momentum.replace('_', ' ')}
            </div>
          </div>
        </div>

        {/* Key levels */}
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>Key Round Levels</div>
        <div className="tag-list">
          {pa.key_levels.slice(0, 8).map((lvl, i) => (
            <span key={i} className={`tag ${lvl > data.current_price ? 'red' : lvl < data.current_price ? 'green' : 'yellow'}`}>
              {fmt(lvl)}
            </span>
          ))}
        </div>
      </div>

      {/* Candle Patterns */}
      <div className="card">
        <div className="card-title">🕯️ Candlestick Patterns</div>
        {pa.candle_patterns.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>No significant patterns detected</p>
        ) : (
          <div className="pattern-list">
            {pa.candle_patterns.slice(-6).map((p, i) => (
              <div key={i} className="pattern-item">
                <div className={`pattern-icon ${p.signal === 'bullish' ? 'bull-text' : p.signal === 'bearish' ? 'bear-text' : 'neutral-text'}`}>
                  {patternSignalIcon(p.signal)}
                </div>
                <div className="pattern-info">
                  <div className="pattern-name">{p.pattern}</div>
                  <div className="pattern-desc">{p.description}</div>
                </div>
                <div className="pattern-str">
                  {(p.strength * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Support & Resistance */}
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-title">🧱 Support & Resistance Levels</div>
        {pa.support_resistance.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Insufficient data for S/R analysis</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Price</th>
                <th>Strength</th>
                <th>Touches</th>
                <th>Distance</th>
              </tr>
            </thead>
            <tbody>
              {pa.support_resistance.slice(0, 8).map((sr, i) => {
                const distPct = Math.abs(sr.price - data.current_price) / data.current_price * 100
                return (
                  <tr key={i}>
                    <td><span className={`badge ${sr.type === 'support' ? 'bull' : 'bear'}`}>{sr.type}</span></td>
                    <td style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{fmt(sr.price)}</td>
                    <td style={{ color: 'var(--yellow)' }}>{'★'.repeat(Math.min(sr.strength, 5))}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{sr.touches}x</td>
                    <td style={{ color: distPct < 1 ? 'var(--yellow)' : 'var(--text-muted)', fontSize: 12 }}>
                      {distPct.toFixed(2)}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
