<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import Card from 'primevue/card'
import { use, init, graphic, format, type ComposeOption, type EChartsType } from 'echarts/core'
import { LineChart, type LineSeriesOption } from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  TooltipComponent,
  type DataZoomComponentOption,
  type GridComponentOption,
  type TooltipComponentOption,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { useCurrency } from '@/composables/useCurrency'
import type { EquityCurvePoint } from '@/types/charts'

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer])

type CurveChartOption = ComposeOption<
  | LineSeriesOption
  | GridComponentOption
  | TooltipComponentOption
  | DataZoomComponentOption
>

const props = defineProps<{
  items: EquityCurvePoint[]
  formatNumber: (value: number | null, digits?: number) => string
}>()

const chartRef = ref<HTMLDivElement | null>(null)
const chartInstance = shallowRef<EChartsType | null>(null)
let resizeObserver: ResizeObserver | null = null

const activeTab = ref<'value' | 'performance'>('value')
const twrMode = ref<'twr' | 'daily' | 'simple'>('daily')
const {
  currentCurrency: currency,
  switchCurrency,
  convertValue,
  currencySymbol,
} = useCurrency()
const selectedRange = ref<string>('all')
const customStartDate = ref('')
const customEndDate = ref('')

const timeRanges = [
  { key: '1w', label: '1周' },
  { key: 'mtd', label: '本月迄今' },
  { key: '1m', label: '1个月' },
  { key: '3m', label: '3个月' },
  { key: 'ytd', label: '本年迄今' },
  { key: '1y', label: '1年' },
  { key: 'all', label: '全部' },
  { key: 'custom', label: '自定义' },
]

const latestPoint = computed(() => props.items[props.items.length - 1] ?? null)
const firstPoint = computed(() => props.items[0] ?? null)

const filteredItems = computed(() => {
  if (selectedRange.value === 'all' || !firstPoint.value || !latestPoint.value) {
    return props.items
  }

  const latestDate = new Date(latestPoint.value.report_date)
  let startDate: Date

  switch (selectedRange.value) {
    case '1w':
      startDate = new Date(latestDate.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case 'mtd':
      startDate = new Date(latestDate.getFullYear(), latestDate.getMonth(), 1)
      break
    case '1m':
      startDate = new Date(latestDate.getFullYear(), latestDate.getMonth() - 1, latestDate.getDate())
      break
    case '3m':
      startDate = new Date(latestDate.getFullYear(), latestDate.getMonth() - 3, latestDate.getDate())
      break
    case 'ytd':
      startDate = new Date(latestDate.getFullYear(), 0, 1)
      break
    case '1y':
      startDate = new Date(latestDate.getFullYear() - 1, latestDate.getMonth(), latestDate.getDate())
      break
    case 'custom':
      if (customStartDate.value && customEndDate.value) {
        startDate = new Date(customStartDate.value)
        const endDate = new Date(customEndDate.value)
        return props.items.filter((item) => {
          const itemDate = new Date(item.report_date)
          return itemDate >= startDate && itemDate <= endDate
        })
      }
      return props.items
    default:
      return props.items
  }

  return props.items.filter((item) => new Date(item.report_date) >= startDate)
})

const displayData = computed(() => filteredItems.value)

const currentDisplayPoint = computed(() => displayData.value[displayData.value.length - 1] ?? null)
const firstDisplayPoint = computed(() => displayData.value[0] ?? null)

const twrModeLabel = computed(() => {
  switch (twrMode.value) {
    case 'twr': return '时间加权收益率'
    case 'daily': return '自算日收益率'
    case 'simple': return '简单收益率'
  }
})

const performanceValue = computed(() => {
  if (!displayData.value.length) return null

  if (twrMode.value === 'simple') {
    const first = firstDisplayPoint.value
    const last = currentDisplayPoint.value
    if (!first || !last || first.total_equity === null || first.total_equity === 0) return null
    if (last.total_equity === null) return null
    return ((last.total_equity - first.total_equity) / Math.abs(first.total_equity)) * 100
  }

  const field = twrMode.value === 'twr' ? 'cnav_twr' : 'daily_twr'
  let cumulative = 1.0
  for (const item of displayData.value) {
    const val = item[field]
    if (val !== null && val !== undefined) {
      cumulative *= 1.0 + val / 100.0
    }
  }
  return (cumulative - 1.0) * 100.0
})

const currentValue = computed(() => {
  if (!currentDisplayPoint.value) return null
  return activeTab.value === 'value' ? currentDisplayPoint.value.total_equity : performanceValue.value
})

const startValue = computed(() => {
  if (!displayData.value.length) return null
  const first = displayData.value[0]
  return activeTab.value === 'value' ? first.total_equity : 0
})

const deltaValue = computed(() => {
  if (currentValue.value === null || startValue.value === null) return null
  return currentValue.value - startValue.value
})

const deltaPercent = computed(() => {
  if (currentValue.value === null || startValue.value === null || startValue.value === 0) return null
  if (activeTab.value === 'performance') {
    return currentValue.value
  }
  return ((currentValue.value - startValue.value) / Math.abs(startValue.value)) * 100
})

const dateRangeText = computed(() => {
  if (!displayData.value.length) return '--'
  const first = displayData.value[0]
  const last = displayData.value[displayData.value.length - 1]
  return `${first.report_date} ~ ${last.report_date}`
})

function formatDisplayValue(value: number | null): string {
  if (value === null) return '--'
  if (activeTab.value === 'value') {
    return `${currencySymbol()}${props.formatNumber(value, 2)}`
  }
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatDeltaValue(value: number | null): string {
  if (value === null) return ''
  if (activeTab.value === 'value') {
    const prefix = value > 0 ? '+' : ''
    return `${prefix}${currencySymbol()}${props.formatNumber(Math.abs(value), 2)}`
  }
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function isPositive(value: number | null): boolean | null {
  if (value === null) return null
  return value > 0
}

function selectRange(rangeKey: string): void {
  selectedRange.value = rangeKey
}

function buildChartData(): Array<[string, number]> {
  if (activeTab.value === 'value') {
    return displayData.value.flatMap((item) => {
      if (item.total_equity === null || item.total_equity === undefined) return []
      return [[item.report_date, convertValue(item.total_equity) ?? item.total_equity]]
    })
  }

  if (twrMode.value === 'simple') {
    return displayData.value.map((item) => {
      const first = displayData.value[0]
      if (!first || first.total_equity === null || first.total_equity === 0 || item.total_equity === null) {
        return [item.report_date, 0]
      }
      const val = ((item.total_equity - first.total_equity) / Math.abs(first.total_equity)) * 100
      return [item.report_date, val]
    })
  }

  const field = twrMode.value === 'twr' ? 'cnav_twr' : 'daily_twr'
  let cumulative = 1.0
  const result: Array<[string, number]> = []
  for (const item of displayData.value) {
    const val = item[field]
    if (val !== null && val !== undefined) {
      cumulative *= 1.0 + val / 100.0
    }
    result.push([item.report_date, (cumulative - 1.0) * 100.0])
  }
  return result
}

function renderChart(): void {
  if (!chartInstance.value) {
    return
  }

  const lineColor = activeTab.value === 'value' ? '#56d5ff' : '#4ade80'
  const areaColorStart = activeTab.value === 'value' ? 'rgba(86, 213, 255, 0.26)' : 'rgba(74, 222, 128, 0.26)'
  const areaColorEnd = activeTab.value === 'value' ? 'rgba(86, 213, 255, 0.02)' : 'rgba(74, 222, 128, 0.02)'

  const option: CurveChartOption = {
    animationDuration: 700,
    animationEasing: 'cubicOut',
    backgroundColor: 'transparent',
    grid: {
      top: 20,
      right: 20,
      bottom: 30,
      left: 20,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(6, 12, 24, 0.96)',
      borderColor: 'rgba(129, 160, 207, 0.22)',
      borderWidth: 1,
      textStyle: {
        color: '#e6eefc',
      },
      padding: 14,
      extraCssText: 'box-shadow: 0 18px 36px rgba(2, 10, 24, 0.45); border-radius: 14px;',
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: 'rgba(86, 213, 255, 0.36)',
          width: 1,
        },
      },
      formatter(params: unknown) {
        const entries = Array.isArray(params) ? params : [params]
        const first = entries[0] as { axisValueLabel?: string; value?: [string, number] } | undefined
        const value = first?.value?.[1]
        const formattedValue = value !== undefined ? formatDisplayValue(value) : '--'

        return `<div style="margin-bottom:4px;color:#9aa8c8">${first?.axisValueLabel ?? '--'}</div>` +
               `<div style="font-weight:600;font-size:15px;color:#fff">${formattedValue}</div>`
      },
    },
    xAxis: {
      type: 'time',
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        show: false,
      },
      splitLine: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      show: false,
    },
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none',
        zoomOnMouseWheel: 'ctrl',
      },
    ],
    series: [
      {
        name: activeTab.value === 'value' ? '账户净值' : '收益率',
        type: 'line',
        smooth: 0.25,
        showSymbol: false,
        sampling: 'lttb',
        data: buildChartData(),
        lineStyle: {
          width: 2.5,
          color: lineColor,
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: areaColorStart },
            { offset: 1, color: areaColorEnd },
          ]),
        },
        z: 6,
      },
    ],
  }

  chartInstance.value.setOption(option, true)
}

function resizeChart(): void {
  chartInstance.value?.resize()
}

function initChart(): void {
  if (!chartRef.value) {
    return
  }

  chartInstance.value = init(chartRef.value, undefined, {
    renderer: 'canvas',
  })
  renderChart()

  resizeObserver = new ResizeObserver(() => {
    resizeChart()
  })
  resizeObserver.observe(chartRef.value)
  window.addEventListener('resize', resizeChart)
}

onMounted(() => {
  initChart()
})

watch(
  () => [displayData.value, activeTab.value, currency.value, twrMode.value],
  () => {
    renderChart()
  },
  { deep: true },
)

onUnmounted(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  window.removeEventListener('resize', resizeChart)
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<template>
  <Card class="surface-panel ibkr-curve-panel">
    <template #content>
      <div class="ibkr-curve-container">
        <div class="curve-header">
          <div class="tab-switcher">
            <button
              type="button"
              class="tab-button"
              :class="{ 'tab-button--active': activeTab === 'value' }"
              @click="activeTab = 'value'"
            >
              价值
            </button>
            <button
              type="button"
              class="tab-button"
              :class="{ 'tab-button--active': activeTab === 'performance' }"
              @click="activeTab = 'performance'"
            >
              业绩
            </button>
          </div>
          <div class="account-info">
            账户{{ activeTab === 'value' ? '净值' : '收益率' }} (DEMO) 截止 {{ latestPoint?.report_date ?? '--' }}
          </div>
        </div>

        <div class="currency-switcher">
          <button
            type="button"
            class="currency-btn"
            :class="{ 'currency-btn--active': currency === 'CNH' }"
            @click="switchCurrency('CNH')"
          >
            CNH
          </button>
          <button
            type="button"
            class="currency-btn"
            :class="{ 'currency-btn--active': currency === 'USD' }"
            @click="switchCurrency('USD')"
          >
            USD
          </button>
        </div>

        <div v-if="activeTab === 'performance'" class="twr-mode-switcher">
          <button
            type="button"
            class="currency-btn"
            :class="{ 'currency-btn--active': twrMode === 'twr' }"
            @click="twrMode = 'twr'"
          >
            TWR
          </button>
          <button
            type="button"
            class="currency-btn"
            :class="{ 'currency-btn--active': twrMode === 'daily' }"
            @click="twrMode = 'daily'"
          >
            自算日
          </button>
          <button
            type="button"
            class="currency-btn"
            :class="{ 'currency-btn--active': twrMode === 'simple' }"
            @click="twrMode = 'simple'"
          >
            简单
          </button>
          <span class="twr-mode-label">{{ twrModeLabel }}</span>
        </div>

        <div class="value-display">
          <div class="main-value" :class="{ 'text-positive': isPositive(currentValue) === true, 'text-negative': isPositive(currentValue) === false }">
            {{ formatDisplayValue(currentValue) }}
          </div>
          <div v-if="deltaValue !== null" class="delta-info">
            <span class="delta-value" :class="{ 'text-positive': isPositive(deltaValue) === true, 'text-negative': isPositive(deltaValue) === false }">
              {{ formatDeltaValue(deltaValue) }}
            </span>
            <span v-if="deltaPercent !== null" class="delta-percent" :class="{ 'text-positive': isPositive(deltaPercent) === true, 'text-negative': isPositive(deltaPercent) === false }">
              {{ formatDeltaValue(deltaPercent) }}
            </span>
            <span class="date-range">{{ dateRangeText }}</span>
          </div>
        </div>

        <div ref="chartRef" class="curve-chart-area" />

        <div class="time-range-selector">
          <button
            v-for="range in timeRanges"
            :key="range.key"
            type="button"
            class="range-button"
            :class="{ 'range-button--active': selectedRange === range.key }"
            @click="selectRange(range.key)"
          >
            {{ range.label }}
          </button>
          <template v-if="selectedRange === 'custom'">
            <input
              v-model="customStartDate"
              type="date"
              class="date-input"
            />
            <span class="date-separator">~</span>
            <input
              v-model="customEndDate"
              type="date"
              class="date-input"
            />
          </template>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.ibkr-curve-panel {
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
  border: 1px solid rgba(71, 85, 105, 0.2);
  border-radius: 16px;
  overflow: hidden;
}

.ibkr-curve-container {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.curve-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-switcher {
  display: flex;
  gap: 4px;
  background: rgba(15, 23, 42, 0.6);
  padding: 4px;
  border-radius: 10px;
  border: 1px solid rgba(71, 85, 105, 0.2);
}

.tab-button {
  padding: 8px 24px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
}

.tab-button:hover {
  color: #cbd5e1;
}

.tab-button--active {
  background: rgba(148, 163, 184, 0.12);
  color: #f1f5f9;
  font-weight: 600;
}

.account-info {
  color: #64748b;
  font-size: 13px;
}

.currency-switcher {
  display: flex;
  gap: 6px;
}

.currency-btn {
  padding: 6px 16px;
  border-radius: 8px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
}

.currency-btn:hover {
  border-color: rgba(148, 163, 184, 0.4);
  color: #cbd5e1;
}

.currency-btn--active {
  background: rgba(148, 163, 184, 0.1);
  border-color: rgba(148, 163, 184, 0.5);
  color: #f1f5f9;
}

.twr-mode-switcher {
  display: flex;
  align-items: center;
  gap: 6px;
}

.twr-mode-label {
  font-size: 12px;
  color: #64748b;
  margin-left: 6px;
}

.value-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.main-value {
  font-size: 42px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #f1f5f9;
  line-height: 1.1;
}

.delta-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
}

.delta-value,
.delta-percent {
  font-weight: 600;
}

.date-range {
  color: #64748b;
  font-weight: 400;
}

.text-positive {
  color: #4ade80;
}

.text-negative {
  color: #f87171;
}

.curve-chart-area {
  width: 100%;
  height: 320px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.4) 0%, rgba(2, 6, 23, 0.6) 100%);
  border: 1px solid rgba(71, 85, 105, 0.15);
}

.time-range-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.range-button {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(71, 85, 105, 0.25);
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 200ms ease;
  white-space: nowrap;
}

.range-button:hover {
  border-color: rgba(148, 163, 184, 0.35);
  color: #cbd5e1;
}

.range-button--active {
  background: rgba(148, 163, 184, 0.12);
  border-color: rgba(148, 163, 184, 0.45);
  color: #f1f5f9;
  font-weight: 600;
}

.date-input {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  background: rgba(15, 23, 42, 0.6);
  color: #e2e8f0;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 200ms ease;
  cursor: pointer;
  min-width: 130px;

  &::-webkit-calendar-picker-indicator {
    filter: invert(1);
    opacity: 0.6;
    cursor: pointer;
  }

  &::-webkit-inner-spin-button,
  &::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  &:focus {
    border-color: rgba(86, 213, 255, 0.5);
  }
}

.date-separator {
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 720px) {
  .ibkr-curve-container {
    padding: 16px;
  }

  .curve-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .main-value {
    font-size: 32px;
  }

  .curve-chart-area {
    height: 240px;
  }

  .time-range-selector {
    gap: 6px;
  }

  .range-button {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
