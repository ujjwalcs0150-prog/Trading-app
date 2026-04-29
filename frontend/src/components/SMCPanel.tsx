import { AnalysisResponse } from '../services/api'
import { Layers, Zap, BarChart2 } from 'lucide-react'

interface Props { data: AnalysisResponse }

const fmt = (n: number) => n.toLocaleString(undefined, { maximumFractionDigits: 6 })

export default function SMCPanel({ data }: Props) {
  const { smc } = data

  return (
    <>
      {/* Market Structure */}
      <div className="card">
        <div className="card-title"><BarChart2 size={14} /> SMC Market Structure</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
          <span className={`ms-pill ${smc.market_structure}`}>
            {smc.market_structure === 'bullish' ? '▲' : smc.market_structure === 'bearish' ? '▼' : '↔'}{' '}
            {smc.market_structure}
          </span>
          <span className={`tag ${smc.premium_discount === 'discount' ? 'green' : smc.premium_discount === 'premium' ? 'red' : 'yellow'}`}>
            {smc.premium_discount}
          </span>
        </div>

        {/* BOS / CHOCH */}
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>
          Break of Structure / Change of Character
        </div>
        <div className="tag-list">
          {smc.break_of_structure.slice(-5).map((b, i) => (
            <span key={i} className={`tag ${b.direction === 'bullish' ? 'green' : 'red'}`}>
              {b.type} {b.direction === 'bullish' ? '▲' : '▼'} @ {fmt(b.price)}
            </span>
          ))}
          {smc.break_of_structure.length === 0 && <span className="tag gray">No recent BOS/CHOCH</span>}
        </div>
      </div>

      {/* Order Blocks */}
      <div className="card">
        <div className="card-title"><Layers size={14} /> Order Blocks</div>
        {smc.order_blocks.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>No order blocks detected</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Low</th>
                <th>High</th>
                <th>Strength</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {smc.order_blocks.slice(-6).map((ob, i) => (
                <tr key={i}>
                  <td><span className={`badge ${ob.type === 'bullish' ? 'bull' : 'bear'}`}>{ob.type}</span></td>
                  <td className={ob.type === 'bullish' ? 'bull-text' : 'bear-text'}>{fmt(ob.low)}</td>
                  <td className={ob.type === 'bullish' ? 'bull-text' : 'bear-text'}>{fmt(ob.high)}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 40, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ width: `${ob.strength * 100}%`, height: '100%', background: ob.type === 'bullish' ? 'var(--green)' : 'var(--red)', borderRadius: 2 }} />
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(ob.strength * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td><span className={`badge ${ob.mitigated ? 'mitg' : ob.type === 'bullish' ? 'bull' : 'bear'}`}>{ob.mitigated ? 'mitigated' : 'active'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Fair Value Gaps */}
      <div className="card">
        <div className="card-title"><Zap size={14} /> Fair Value Gaps (Imbalances)</div>
        {smc.fair_value_gaps.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>No unfilled FVGs</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>Type</th><th>Bottom</th><th>Top</th><th>Filled</th></tr>
            </thead>
            <tbody>
              {smc.fair_value_gaps.slice(0, 6).map((fvg, i) => (
                <tr key={i}>
                  <td><span className={`badge ${fvg.type === 'bullish' ? 'bull' : 'bear'}`}>{fvg.type}</span></td>
                  <td>{fmt(fvg.bottom)}</td>
                  <td>{fmt(fvg.top)}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <div style={{ width: 36, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ width: `${fvg.fill_percentage * 100}%`, height: '100%', background: 'var(--blue)', borderRadius: 2 }} />
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(fvg.fill_percentage * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Liquidity */}
      <div className="card">
        <div className="card-title">💧 Liquidity Levels</div>
        {smc.liquidity_levels.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>No liquidity levels found</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>Type</th><th>Price</th><th>Strength</th><th>Swept</th></tr>
            </thead>
            <tbody>
              {smc.liquidity_levels.slice(0, 8).map((l, i) => (
                <tr key={i}>
                  <td style={{ fontSize: 11, color: l.type.includes('high') ? 'var(--red)' : 'var(--green)' }}>
                    {l.type.replace('_', ' ')}
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>{fmt(l.price)}</td>
                  <td>{'★'.repeat(Math.min(l.strength, 5))}</td>
                  <td style={{ color: l.swept ? 'var(--text-muted)' : 'var(--yellow)', fontSize: 11, fontWeight: 600 }}>
                    {l.swept ? 'swept' : 'intact'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
