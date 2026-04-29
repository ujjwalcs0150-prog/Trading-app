import { useEffect, useRef } from 'react'
import {
  createChart,
  ColorType,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
} from 'lightweight-charts'
import { AnalysisResponse } from '../services/api'

interface Props {
  data: AnalysisResponse
}

export default function CandlestickChart({ data }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef     = useRef<IChartApi | null>(null)
  const candleRef    = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeRef    = useRef<ISeriesApi<'Histogram'> | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#161b22' },
        textColor:  '#8b949e',
      },
      grid: {
        vertLines: { color: '#21262d' },
        horzLines: { color: '#21262d' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: {
        borderColor: '#30363d',
        scaleMargins: { top: 0.05, bottom: 0.25 },
      },
      timeScale: {
        borderColor: '#30363d',
        timeVisible: true,
        secondsVisible: false,
      },
      width:  containerRef.current.clientWidth,
      height: 460,
    })

    const candleSeries = chart.addCandlestickSeries({
      upColor:          '#26a69a',
      downColor:        '#ef5350',
      borderUpColor:    '#26a69a',
      borderDownColor:  '#ef5350',
      wickUpColor:      '#26a69a',
      wickDownColor:    '#ef5350',
    })

    const volumeSeries = chart.addHistogramSeries({
      priceFormat:    { type: 'volume' },
      priceScaleId:   'volume',
    })

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.80, bottom: 0.0 },
    })

    chartRef.current  = chart
    candleRef.current = candleSeries
    volumeRef.current = volumeSeries

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    })
    ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current) return

    const candles = data.chart_data.map(d => ({
      time:  d.time as CandlestickData['time'],
      open:  d.open,
      high:  d.high,
      low:   d.low,
      close: d.close,
    }))

    const volumes = data.volume_data.map(d => ({
      time:  d.time as HistogramData['time'],
      value: d.value,
      color: d.color,
    }))

    candleRef.current.setData(candles)
    volumeRef.current.setData(volumes)

    // Draw Order Blocks as price lines
    if (chartRef.current && candleRef.current) {
      data.smc.order_blocks.slice(-4).forEach(ob => {
        if (!ob.mitigated) {
          candleRef.current!.createPriceLine({
            price:       (ob.high + ob.low) / 2,
            color:       ob.type === 'bullish' ? '#26a69a' : '#ef5350',
            lineWidth:   1,
            lineStyle:   2, // dashed
            axisLabelVisible: true,
            title:       `OB ${ob.type === 'bullish' ? '▲' : '▼'}`,
          })
        }
      })

      // Draw FVG midpoints
      data.smc.fair_value_gaps.slice(-4).forEach(fvg => {
        if (!fvg.filled) {
          candleRef.current!.createPriceLine({
            price:       (fvg.top + fvg.bottom) / 2,
            color:       fvg.type === 'bullish' ? '#388bfd' : '#a371f7',
            lineWidth:   1,
            lineStyle:   3,
            axisLabelVisible: true,
            title:       `FVG`,
          })
        }
      })

      // Draw S/R levels
      data.price_action.support_resistance.slice(0, 4).forEach(sr => {
        candleRef.current!.createPriceLine({
          price:       sr.price,
          color:       sr.type === 'support' ? '#3fb950' : '#f85149',
          lineWidth:   1,
          lineStyle:   0,
          axisLabelVisible: true,
          title:       sr.type === 'support' ? 'S' : 'R',
        })
      })

      // Draw entry, SL, TP lines
      const setup = data.trade_setup
      if (setup.signal !== 'NEUTRAL') {
        const entryColor = setup.signal === 'BUY' ? '#26a69a' : '#ef5350'
        candleRef.current!.createPriceLine({ price: setup.entry,        color: entryColor, lineWidth: 2, lineStyle: 0, axisLabelVisible: true, title: 'ENTRY' })
        candleRef.current!.createPriceLine({ price: setup.stop_loss,    color: '#f85149',  lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'SL' })
        candleRef.current!.createPriceLine({ price: setup.take_profit_1,color: '#3fb950',  lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'TP1' })
        candleRef.current!.createPriceLine({ price: setup.take_profit_2,color: '#3fb950',  lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'TP2' })
        candleRef.current!.createPriceLine({ price: setup.take_profit_3,color: '#a371f7',  lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'TP3' })
      }

      chartRef.current.timeScale().fitContent()
    }
  }, [data])

  return <div ref={containerRef} className="chart-container" />
}
