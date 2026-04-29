import { useState, useCallback } from 'react'
import { analyzeSymbol, AnalysisResponse } from '../services/api'

type Status = 'idle' | 'loading' | 'success' | 'error'

export function useAnalysis() {
  const [status, setStatus]   = useState<Status>('idle')
  const [data, setData]       = useState<AnalysisResponse | null>(null)
  const [error, setError]     = useState<string | null>(null)

  const analyze = useCallback(async (symbol: string, timeframe: string) => {
    setStatus('loading')
    setError(null)
    try {
      const result = await analyzeSymbol(symbol, timeframe)
      setData(result)
      setStatus('success')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
      setStatus('error')
    }
  }, [])

  return { status, data, error, analyze }
}
