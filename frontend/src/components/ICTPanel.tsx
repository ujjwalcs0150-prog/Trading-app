import { AnalysisResponse } from '../services/api'
import { Clock, Activity } from 'lucide-react'

interface Props { data: AnalysisResponse }

const fmt = (n: number) => n.toLocaleString(undefined, { maximumFractionDigits: 6 })

const amdColor = (phase: string) => {
  if (phase === 'accumulation') return 'var(--blue)'
  if (phase === 'manipulation') return 'var(--yellow)'
  return 'var(--green)'
}

export default function ICTPanel({ data }: Props) {
  const { ict } = data
  const current = data.current_price
  const drRange = ict.dealing_range_high - ict.dealing_range_low
  const positionPct = drRange > 0
    ? ((current - ict.dealing_range_low) / drRange) * 100
    : 50

  return (
    <>
      {/* Kill Zones */}
      <div className="card">
        <div className="card-title"><Clock size={14} /> ICT Kill Zones (EST)</div>
        <div>
          {ict.kill_zones.map((kz, i) => (
            <div key={i} className="kz-item">
              <div>
                <div className="kz-name">{kz.name}</div>
                <div className="kz-desc">{kz.description}</div>
              </div>
              <span className={`kz-status ${kz.active ? 'active' : 'inactive'}`}>
                {kz.active ? 'ACTIVE' : `${kz.start_hour}:00`}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* AMD Phase + Dealing Range */}
      <div className="card">
        <div className="card-title"><Activity size={14} /> AMD Phase & Dealing Range</div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 3 }}>AMD Phase</div>
            <span style={{ fontSize: 15, fontWeight: 800, color: amdColor(ict.amd_phase), textTransform: 'uppercase' }}>
              {ict.amd_phase}
            </span>
          </div>
          {ict.optimal_entry != null && (
            <div style={{ marginLeft: 'auto' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 3 }}>OTE Entry</div>
              <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--purple)' }}>{fmt(ict.optimal_entry)}</span>
            </div>
          )}
        </div>

        {/* Dealing range visual */}
        <div style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
            <span>Range Low {fmt(ict.dealing_range_low)}</span>
            <span>EQ {fmt(ict.equilibrium)}</span>
            <span>Range High {fmt(ict.dealing_range_high)}</span>
          </div>
          <div style={{ position: 'relative', height: 20, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
            {/* Premium zone */}
            <div style={{ position: 'absolute', right: 0, top: 0, width: '35%', height: '100%', background: 'rgba(239,83,80,0.15)' }} />
            {/* Discount zone */}
            <div style={{ position: 'absolute', left: 0, top: 0, width: '35%', height: '100%', background: 'rgba(38,166,154,0.15)' }} />
            {/* Equilibrium line */}
            <div style={{ position: 'absolute', left: '50%', top: 0, width: 1, height: '100%', background: 'var(--yellow)', opacity: 0.5 }} />
            {/* Current price marker */}
            <div style={{
              position: 'absolute',
              left: `${Math.max(2, Math.min(98, positionPct))}%`,
              top: 2,
              bottom: 2,
              width: 3,
              background: 'var(--text-primary)',
              borderRadius: 2,
              transform: 'translateX(-50%)',
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
            <span style={{ color: 'var(--green)' }}>Discount</span>
            <span style={{ color: 'var(--yellow)' }}>Equilibrium</span>
            <span style={{ color: 'var(--red)' }}>Premium</span>
          </div>
        </div>
      </div>

      {/* OTE Fibonacci Levels */}
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-title">📐 OTE Fibonacci Levels</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 4 }}>
          {ict.ote_levels.map((lvl, i) => (
            <div key={i} className={`fib-row ${lvl.in_ote ? 'ote-highlight' : ''}`}
                 style={{ background: lvl.in_ote ? 'rgba(163,113,247,0.08)' : undefined, borderRadius: 4, padding: '5px 8px' }}>
              <span className="fib-level">{(lvl.fib_level * 100).toFixed(1)}%</span>
              <span className="fib-price" style={{ color: lvl.in_ote ? 'var(--purple)' : 'var(--text-primary)' }}>
                {fmt(lvl.price)}
              </span>
              <span className="fib-label">{lvl.in_ote && <span style={{ color: 'var(--purple)', marginRight: 4 }}>★</span>}{lvl.label}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
