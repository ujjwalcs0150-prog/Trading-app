import { TradeSetup } from '../services/api'
import { TrendingUp, TrendingDown, Minus, Target, Shield } from 'lucide-react'

interface Props { setup: TradeSetup }

const signalIcon = (s: string) => {
  if (s === 'BUY')  return <TrendingUp  size={16} />
  if (s === 'SELL') return <TrendingDown size={16} />
  return <Minus size={16} />
}

const reasonClass = (r: string) => {
  if (r.startsWith('✅')) return 'bull'
  if (r.startsWith('🔴')) return 'bear'
  return 'info'
}

const confidenceColor = (c: number) => {
  if (c >= 70) return '#26a69a'
  if (c >= 45) return '#e3b341'
  return '#8b949e'
}

export default function TradeSetupCard({ setup }: Props) {
  return (
    <div className="card" style={{ gridColumn: '1 / -1' }}>
      <div className="card-title">
        <Target size={14} /> Trade Setup
        <span className={`signal-badge ${setup.signal}`} style={{ marginLeft: 8, fontSize: 12 }}>
          {signalIcon(setup.signal)} {setup.signal}
        </span>
        <span className="confidence-bar-wrap" style={{ marginLeft: 12 }}>
          <span style={{ color: confidenceColor(setup.confidence), fontWeight: 700 }}>
            {setup.confidence}%
          </span>
          <span>confidence</span>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{ width: `${setup.confidence}%`, background: confidenceColor(setup.confidence) }}
            />
          </div>
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Level grid */}
        <div>
          <div className="trade-levels">
            <div className="level-item entry">
              <div className="level-label">Entry Price</div>
              <div className="level-value">{setup.entry.toLocaleString(undefined, { maximumFractionDigits: 6 })}</div>
            </div>
            <div className="level-item sl">
              <div className="level-label">Stop Loss</div>
              <div className="level-value">{setup.stop_loss.toLocaleString(undefined, { maximumFractionDigits: 6 })}</div>
            </div>
            <div className="level-item tp1">
              <div className="level-label">Take Profit 1</div>
              <div className="level-value">{setup.take_profit_1.toLocaleString(undefined, { maximumFractionDigits: 6 })}</div>
            </div>
            <div className="level-item tp2">
              <div className="level-label">Take Profit 2</div>
              <div className="level-value">{setup.take_profit_2.toLocaleString(undefined, { maximumFractionDigits: 6 })}</div>
            </div>
            <div className="level-item tp3">
              <div className="level-label">Take Profit 3</div>
              <div className="level-value">{setup.take_profit_3.toLocaleString(undefined, { maximumFractionDigits: 6 })}</div>
            </div>
            <div className="level-item rr">
              <div className="level-label">Risk : Reward</div>
              <div className="level-value">1 : {setup.risk_reward.toFixed(2)}</div>
            </div>
          </div>
        </div>

        {/* Reasons */}
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
            <Shield size={12} /> Analysis Confluence
          </div>
          <ul className="reasons-list">
            {setup.reasons.map((r, i) => (
              <li key={i} className={`reason-item ${reasonClass(r)}`}>{r}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
