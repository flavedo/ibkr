<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import {
  use,
  init,
  format,
  type ComposeOption,
  type EChartsType,
} from 'echarts/core'
import { CandlestickChart, ScatterChart, type CandlestickSeriesOption, type ScatterSeriesOption } from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  type DataZoomComponentOption,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import type { PositionDetailResponse } from '@/types/positions'

use([CandlestickChart, ScatterChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, CanvasRenderer])

type DetailChartOption = ComposeOption<
  | CandlestickSeriesOption
  | ScatterSeriesOption
  | GridComponentOption
  | TooltipComponentOption
  | LegendComponentOption
  | DataZoomComponentOption
>

const props = defineProps<{
  detail: PositionDetailResponse
  formatNumber: (value: number | null, digits?: number) => string
}>()

const chartRef = ref<HTMLDivElement | null>(null)
const chartInstance = shallowRef<EChartsType | null>(null)
let resizeObserver: ResizeObserver | null = null

const categories = computed(() => props.detail.bars.map((item) => item.report_date))

const klineData = computed(() =>
  props.detail.bars.map((item) => [
    item.open_price ?? item.close_price ?? 0,
    item.close_price ?? item.open_price ?? 0,
    item.low_price ?? item.close_price ?? item.open_price ?? 0,
    item.high_price ?? item.close_price ?? item.open_price ?? 0,
  ]),
)

const buyMarkers = computed(() => buildTradeMarkers('BUY'))

const sellMarkers = computed(() => buildTradeMarkers('SELL'))

function formatAxisValue(value: number): string {
  if (Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }
  return value.toFixed(2)
}

function formatMarkerQuantity(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '--'
  }
  const absoluteValue = Math.abs(value)
  const digits = Number.isInteger(absoluteValue) ? 0 : 4
  return props.formatNumber(absoluteValue, digits)
}

function buildTradeMarkers(side: 'BUY' | 'SELL') {
  const groupCount = new Map<string, number>()
  const direction = side === 'BUY' ? -1 : 1
  const stackStep = 26

  return props.detail.trades
    .filter((item) => item.buy_sell === side && item.trade_date && item.trade_price !== null)
    .map((item) => {
      const groupKey = `${item.trade_date}:${item.trade_price}`
      const stackIndex = groupCount.get(groupKey) ?? 0
      groupCount.set(groupKey, stackIndex + 1)
      const verticalOffset = direction * stackIndex * stackStep

      return {
        value: [item.trade_date as string, item.trade_price as number, item.quantity ?? 0],
        trade: item,
        quantityText: formatMarkerQuantity(item.quantity),
        symbolOffset: [0, verticalOffset] as [number, number],
      }
    })
}

function renderChart(): void {
  if (!chartInstance.value) {
    return
  }

  const option: DetailChartOption = {
    animationDuration: 500,
    backgroundColor: 'transparent',
    legend: {
      top: 10,
      data: ['近似日K', '买入 B', '卖出 S'],
      textStyle: {
        color: '#6d7d9d',
      },
    },
    grid: {
      top: 52,
      right: 44,
      bottom: 80,
      left: 28,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: {
          color: 'rgba(86, 213, 255, 0.24)',
        },
      },
      backgroundColor: 'rgba(6, 12, 24, 0.96)',
      borderColor: 'rgba(129, 160, 207, 0.22)',
      textStyle: {
        color: '#e6eefc',
      },
      formatter(params: unknown) {
        const entries = Array.isArray(params) ? params as Array<Record<string, unknown>> : [params as Record<string, unknown>]
        const dateLabel = String(entries[0]?.axisValue ?? '--')
        const lines = [`<div style="margin-bottom:8px;color:#9aa9c8">${dateLabel}</div>`]

        entries.forEach((entry) => {
          if (entry.seriesType === 'candlestick') {
            const value = entry.value as number[]
            lines.push(
              `<div>开 ${props.formatNumber(value[0], 2)} / 收 ${props.formatNumber(value[1], 2)}</div>` +
              `<div>低 ${props.formatNumber(value[2], 2)} / 高 ${props.formatNumber(value[3], 2)}</div>`,
            )
            return
          }

          const trade = entry.data && typeof entry.data === 'object' && 'trade' in entry.data
            ? (entry.data as { trade: { buy_sell?: string | null; quantity?: number | null; trade_price?: number | null } }).trade
            : null
          if (trade) {
            lines.push(
              `<div>${trade.buy_sell === 'BUY' ? '买入' : '卖出'} ${props.formatNumber(trade.quantity ?? null, 4)} @ ${props.formatNumber(trade.trade_price ?? null, 2)}</div>`,
            )
          }
        })

        return lines.join('')
      },
    },
    xAxis: {
      type: 'category',
      data: categories.value,
      boundaryGap: true,
      axisLine: {
        lineStyle: {
          color: 'rgba(129, 160, 207, 0.16)',
        },
      },
      axisLabel: {
        color: '#6d7d9d',
        formatter(value: string) {
          return format.formatTime('yyyy-MM-dd', value)
        },
      },
      splitLine: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      position: 'right',
      scale: true,
      axisLabel: {
        color: '#6d7d9d',
        formatter(value: number) {
          return formatAxisValue(value)
        },
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(129, 160, 207, 0.11)',
          type: 'dashed',
        },
      },
    },
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none',
        zoomOnMouseWheel: 'ctrl',
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        height: 20,
        bottom: 18,
        borderColor: 'rgba(129, 160, 207, 0.08)',
        backgroundColor: 'rgba(9, 16, 29, 0.72)',
        fillerColor: 'rgba(62, 169, 255, 0.18)',
        handleStyle: {
          color: '#13284a',
          borderColor: '#56d5ff',
          borderWidth: 1,
        },
        textStyle: {
          color: '#6d7d9d',
        },
      },
    ],
    series: [
      {
        name: '近似日K',
        type: 'candlestick',
        data: klineData.value,
        itemStyle: {
          color: '#34d2a3',
          color0: '#ff6b7d',
          borderColor: '#34d2a3',
          borderColor0: '#ff6b7d',
        },
      },
      {
        name: '买入 B',
        type: 'scatter',
        data: buyMarkers.value,
        symbol: 'circle',
        symbolSize: 24,
        itemStyle: {
          color: '#4d95ff',
          borderColor: '#d9e7ff',
          borderWidth: 1.5,
          shadowBlur: 14,
          shadowColor: 'rgba(77, 149, 255, 0.38)',
        },
        label: {
          show: true,
          formatter: 'B',
          color: '#f7fbff',
          fontWeight: 800,
          fontSize: 12,
        },
        encode: {
          x: 0,
          y: 1,
        },
      },
      {
        name: '买入数量',
        type: 'scatter',
        data: buyMarkers.value,
        symbol: 'circle',
        symbolSize: 1,
        silent: true,
        tooltip: {
          show: false,
        },
        itemStyle: {
          color: 'transparent',
        },
        label: {
          show: true,
          position: 'right',
          offset: [10, 0],
          formatter(params) {
            return typeof params.data === 'object' && params.data && 'quantityText' in params.data
              ? String(params.data.quantityText)
              : '--'
          },
          color: '#d9e7ff',
          fontWeight: 700,
          fontSize: 12,
          textBorderColor: 'rgba(11, 18, 33, 0.9)',
          textBorderWidth: 3,
        },
        encode: {
          x: 0,
          y: 1,
        },
      },
      {
        name: '卖出 S',
        type: 'scatter',
        data: sellMarkers.value,
        symbol: 'circle',
        symbolSize: 24,
        itemStyle: {
          color: '#ff5c73',
          borderColor: '#ffe2e6',
          borderWidth: 1.5,
          shadowBlur: 14,
          shadowColor: 'rgba(255, 92, 115, 0.38)',
        },
        label: {
          show: true,
          formatter: 'S',
          color: '#fff7f8',
          fontWeight: 800,
          fontSize: 12,
        },
        encode: {
          x: 0,
          y: 1,
        },
      },
      {
        name: '卖出数量',
        type: 'scatter',
        data: sellMarkers.value,
        symbol: 'circle',
        symbolSize: 1,
        silent: true,
        tooltip: {
          show: false,
        },
        itemStyle: {
          color: 'transparent',
        },
        label: {
          show: true,
          position: 'right',
          offset: [10, 0],
          formatter(params) {
            return typeof params.data === 'object' && params.data && 'quantityText' in params.data
              ? String(params.data.quantityText)
              : '--'
          },
          color: '#ffe2e6',
          fontWeight: 700,
          fontSize: 12,
          textBorderColor: 'rgba(11, 18, 33, 0.9)',
          textBorderWidth: 3,
        },
        encode: {
          x: 0,
          y: 1,
        },
      },
    ],
  }

  chartInstance.value.setOption(option, true)
}

onMounted(() => {
  if (!chartRef.value) {
    return
  }
  chartInstance.value = init(chartRef.value)
  renderChart()

  resizeObserver = new ResizeObserver(() => {
    chartInstance.value?.resize()
  })
  resizeObserver.observe(chartRef.value)
})

watch(
  () => props.detail,
  () => {
    renderChart()
  },
  { deep: true },
)

onUnmounted(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<template>
  <section class="surface-panel position-detail-chart">
    <div class="surface-panel__content">
      <div class="section-header">
        <div>
          <h3 class="panel-title">{{ detail.symbol ?? '--' }} 详情</h3>
          <p class="panel-subtitle">
            近似日 K 基于历史价格索引生成，买卖点按成交价和数量标注。
          </p>
        </div>
      </div>
      <div ref="chartRef" class="position-detail-chart__canvas"></div>
    </div>
  </section>
</template>

<style scoped>
.position-detail-chart__canvas {
  width: 100%;
  height: 420px;
}
</style>
