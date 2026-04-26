<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import DatePicker from 'primevue/datepicker'

import type { EquityCurvePoint } from '@/types/charts'

type CalendarCell = {
  key: string
  reportDate: string | null
  dayNumber: number | null
  pnl: number | null
  twr: number | null
  isCurrentMonth: boolean
  isLatestReportDate: boolean
}

const props = defineProps<{
  items: EquityCurvePoint[]
}>()

const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']

const latestPoint = computed(() => props.items[props.items.length - 1] ?? null)

const currentYear = ref<number>(new Date().getFullYear())
const currentMonth = ref<number>(new Date().getMonth() + 1)

watch(latestPoint, (point) => {
  if (point?.report_date) {
    const { year, month } = parseIsoDate(point.report_date)
    currentYear.value = year
    currentMonth.value = month
  }
}, { immediate: true })

function goToPrevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value -= 1
  } else {
    currentMonth.value -= 1
  }
}

function goToNextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value += 1
  } else {
    currentMonth.value += 1
  }
}

function goToLatestMonth() {
  if (latestPoint.value?.report_date) {
    const { year, month } = parseIsoDate(latestPoint.value.report_date)
    currentYear.value = year
    currentMonth.value = month
  }
}

function onMonthSelect(event: { year: number; month: number }) {
  currentYear.value = event.year
  currentMonth.value = event.month
}

const monthLabel = computed(() => {
  return `${currentYear.value}年${currentMonth.value}月`
})

const selectedMonth = computed({
  get: () => new Date(currentYear.value, currentMonth.value - 1, 15),
  set: (val: Date) => {
    if (val) {
      currentYear.value = val.getFullYear()
      currentMonth.value = val.getMonth() + 1
    }
  }
})

const calendarMetrics = computed(() => {
  const monthPrefix = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-`
  const monthItems = props.items.filter((item) => item.report_date.startsWith(monthPrefix))

  let totalPnl = 0
  let positiveDays = 0
  let negativeDays = 0
  let hasPnl = false
  for (const item of monthItems) {
    const dailyPnl = item.daily_mtm
    if (dailyPnl === null || dailyPnl === undefined) {
      continue
    }
    hasPnl = true
    totalPnl += dailyPnl
    if (dailyPnl > 0) {
      positiveDays += 1
    } else if (dailyPnl < 0) {
      negativeDays += 1
    }
  }

  return {
    tradingDays: monthItems.length,
    positiveDays,
    negativeDays,
    totalPnl: hasPnl ? totalPnl : null,
  }
})

const calendarCells = computed<CalendarCell[]>(() => {
  if (!props.items.length) {
    return []
  }

  const firstDay = new Date(Date.UTC(currentYear.value, currentMonth.value - 1, 1))
  const nextMonthFirstDay = new Date(Date.UTC(currentYear.value, currentMonth.value, 1))
  const monthEnd = new Date(nextMonthFirstDay.getTime() - 24 * 60 * 60 * 1000)
  const daysInMonth = monthEnd.getUTCDate()
  const leadingPadding = (firstDay.getUTCDay() + 6) % 7

  const pointsByDate = new Map(props.items.map((item) => [item.report_date, item]))
  const latestDate = latestPoint.value?.report_date ?? ''
  const cells: CalendarCell[] = []

  for (let index = 0; index < leadingPadding; index += 1) {
    cells.push({
      key: `leading-${index}`,
      reportDate: null,
      dayNumber: null,
      pnl: null,
      twr: null,
      isCurrentMonth: false,
      isLatestReportDate: false,
    })
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const reportDate = `${latestDateParts.year}-${String(latestDateParts.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const point = pointsByDate.get(reportDate)
    cells.push({
      key: reportDate,
      reportDate,
      dayNumber: day,
      pnl: point?.daily_mtm ?? null,
      twr: point?.daily_twr ?? null,
      isCurrentMonth: true,
      isLatestReportDate: reportDate === latestDate,
    })
  }

  const trailingPadding = (7 - (cells.length % 7)) % 7
  for (let index = 0; index < trailingPadding; index += 1) {
    cells.push({
      key: `trailing-${index}`,
      reportDate: null,
      dayNumber: null,
      pnl: null,
      twr: null,
      isCurrentMonth: false,
      isLatestReportDate: false,
    })
  }

  return cells
})

function parseIsoDate(value: string): { year: number; month: number; day: number } {
  const [yearText, monthText, dayText] = value.split('-')
  return {
    year: Number(yearText),
    month: Number(monthText),
    day: Number(dayText),
  }
}

function pnlTone(value: number | null): 'positive' | 'negative' | 'neutral' {
  if (value === null || value === 0) {
    return 'neutral'
  }
  return value > 0 ? 'positive' : 'negative'
}

function isFlatDay(value: number | null): boolean {
  return value === 0
}

function formatSignedInteger(value: number | null): string {
  if (value === null) {
    return '--'
  }
  if (value === 0) {
    return '无变化'
  }
  const rounded = Math.round(value)
  return `${rounded > 0 ? '+' : ''}${new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(rounded)}`
}

function formatSignedPercent(value: number | null): string {
  if (value === null) {
    return ''
  }
  if (value === 0) {
    return ''
  }
  return `${value > 0 ? '+' : ''}${new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)}%`
}

function formatSummaryAmount(value: number | null): string {
  if (value === null) {
    return '--'
  }
  return `${value > 0 ? '+' : ''}${new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)}`
}
</script>

<template>
  <Card class="surface-panel calendar-panel">
    <template #content>
      <div class="surface-panel__content">
        <div class="calendar-panel__header">
          <div>
            <p class="eyebrow">Calendar</p>
            <h2 class="panel-title calendar-panel__title">近一个月盈亏日历</h2>
            <p class="panel-subtitle calendar-panel__subtitle">
              按最新报告月份展示日度盈亏，金额口径采用 IBKR CNAV 里的当日 MTM。
            </p>
          </div>
          <div class="calendar-panel__tags">
            <Tag class="p-tag p-tag--accent" :value="monthLabel" />
            <Tag class="p-tag" :value="`${calendarMetrics.tradingDays} 个交易日`" />
            <Tag class="p-tag" :value="`月内 ${formatSummaryAmount(calendarMetrics.totalPnl)}`" />
          </div>
          <div class="calendar-panel__nav">
            <button class="p-button p-button-sm p-button-text" type="button" aria-label="上个月" @click="goToPrevMonth">
              <span class="pi pi-chevron-left" />
            </button>
            <DatePicker
              v-model="selectedMonth"
              view="month"
              date-format="yy/mm"
              :manual-input="false"
              :max-date="latestPoint ? new Date(latestPoint.report_date) : undefined"
              @update:model-value="(val: Date) => { if (val) { currentYear = val.getFullYear(); currentMonth = val.getMonth() + 1 } }"
            />
            <button class="p-button p-button-sm p-button-text" type="button" aria-label="下个月" @click="goToNextMonth">
              <span class="pi pi-chevron-right" />
            </button>
            <button class="p-button p-button-sm p-button-secondary" type="button" @click="goToLatestMonth">
              最新月
            </button>
          </div>
        </div>

        <div v-if="calendarCells.length === 0" class="empty-state">暂无日历数据</div>

        <div v-else class="calendar-panel__body">
          <div class="calendar-summary">
            <div class="calendar-summary__item">
              <span>上涨日</span>
              <strong class="metric-positive">{{ calendarMetrics.positiveDays }}</strong>
            </div>
            <div class="calendar-summary__item">
              <span>下跌日</span>
              <strong class="metric-negative">{{ calendarMetrics.negativeDays }}</strong>
            </div>
            <div class="calendar-summary__item">
              <span>净变化</span>
              <strong :class="pnlTone(calendarMetrics.totalPnl) === 'positive' ? 'metric-positive' : pnlTone(calendarMetrics.totalPnl) === 'negative' ? 'metric-negative' : ''">
                {{ formatSummaryAmount(calendarMetrics.totalPnl) }}
              </strong>
            </div>
          </div>

          <div class="calendar-grid" aria-label="Monthly performance calendar">
            <div v-for="label in weekdayLabels" :key="label" class="calendar-grid__weekday">{{ label }}</div>

            <article
              v-for="cell in calendarCells"
              :key="cell.key"
              class="calendar-cell"
              :class="{
                'calendar-cell--muted': !cell.isCurrentMonth,
                'calendar-cell--positive': pnlTone(cell.pnl) === 'positive',
                'calendar-cell--negative': pnlTone(cell.pnl) === 'negative',
                'calendar-cell--latest': cell.isLatestReportDate,
              }"
            >
              <template v-if="cell.isCurrentMonth">
                <div class="calendar-cell__day">{{ cell.dayNumber }}</div>
                <div class="calendar-cell__amount" :class="{ 'calendar-cell__amount--flat': isFlatDay(cell.pnl) }">
                  {{ formatSignedInteger(cell.pnl) }}
                </div>
                <div class="calendar-cell__meta">{{ formatSignedPercent(cell.twr) || '\u00A0' }}</div>
              </template>
            </article>
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.calendar-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.calendar-panel__nav {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.calendar-panel__title {
  font-size: 1.4rem;
}

.calendar-panel__subtitle {
  max-width: 46rem;
}

.calendar-panel__tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.calendar-panel__body {
  display: grid;
  gap: var(--space-4);
}

.calendar-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.calendar-summary__item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(129, 160, 207, 0.12);
  background: rgba(15, 26, 45, 0.66);
}

.calendar-summary__item span {
  color: var(--color-text-secondary);
  font-size: 0.84rem;
}

.calendar-summary__item strong {
  font-size: 1.12rem;
  letter-spacing: -0.03em;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
}

.calendar-grid__weekday {
  padding: 0 6px 4px;
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.08em;
}

.calendar-cell {
  min-height: 116px;
  padding: 12px 12px 10px;
  border-radius: 18px;
  border: 1px solid rgba(129, 160, 207, 0.12);
  background: linear-gradient(180deg, rgba(16, 30, 53, 0.82), rgba(9, 16, 29, 0.92));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
  display: grid;
  align-content: space-between;
  gap: 10px;
}

.calendar-cell--muted {
  background: rgba(9, 16, 29, 0.28);
  border-style: dashed;
  opacity: 0.42;
}

.calendar-cell--positive {
  border-color: rgba(52, 210, 163, 0.22);
  background:
    radial-gradient(circle at top right, rgba(52, 210, 163, 0.2), transparent 45%),
    linear-gradient(180deg, rgba(12, 39, 36, 0.82), rgba(6, 22, 20, 0.92));
}

.calendar-cell--negative {
  border-color: rgba(255, 107, 125, 0.2);
  background:
    radial-gradient(circle at top right, rgba(255, 107, 125, 0.16), transparent 45%),
    linear-gradient(180deg, rgba(46, 18, 28, 0.84), rgba(20, 9, 16, 0.94));
}

.calendar-cell--latest {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.03),
    0 0 0 1px rgba(86, 213, 255, 0.18);
}

.calendar-cell__day {
  color: var(--color-text-secondary);
  font-size: 0.84rem;
  font-weight: 600;
}

.calendar-cell__amount {
  font-size: clamp(1rem, 1.4vw, 1.35rem);
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.03em;
}

.calendar-cell__amount--flat {
  font-size: 1rem;
  color: var(--color-text-primary);
  letter-spacing: 0;
}

.calendar-cell--positive .calendar-cell__amount {
  color: var(--color-positive);
}

.calendar-cell--negative .calendar-cell__amount {
  color: var(--color-negative);
}

.calendar-cell__meta {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}

@media (max-width: 1080px) {
  .calendar-panel__header {
    flex-direction: column;
  }

  .calendar-panel__tags {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .calendar-summary {
    grid-template-columns: 1fr;
  }

  .calendar-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .calendar-grid__weekday {
    display: none;
  }

  .calendar-cell {
    min-height: 96px;
  }
}
</style>
