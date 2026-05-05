<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Card from 'primevue/card'

import { fetchEarningsCalendar } from '@/api/financialCalendar'
import type { EarningsEvent } from '@/api/financialCalendar'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import MarketSentimentCard from '@/components/MarketSentimentCard.vue'

const earningsEvents = ref<EarningsEvent[]>([])
const loading = ref(true)
const errorMessage = ref('')

const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth() + 1)

const monthLabel = computed(() => `${currentYear.value}年${currentMonth.value}月`)

function goToPrevMonth(): void {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value -= 1
  } else {
    currentMonth.value -= 1
  }
  void loadData()
}

function goToNextMonth(): void {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value += 1
  } else {
    currentMonth.value += 1
  }
  void loadData()
}

function goToCurrentMonth(): void {
  currentYear.value = today.getFullYear()
  currentMonth.value = today.getMonth() + 1
  void loadData()
}

function formatMonthRange(): { start: string; end: string } {
  const y = currentYear.value
  const m = currentMonth.value
  const start = `${y}-${String(m).padStart(2, '0')}-01`
  if (m === 12) {
    return { start, end: `${y + 1}-01-01` }
  }
  return { start, end: `${y}-${String(m + 1).padStart(2, '0')}-01` }
}

function formatMarketcap(cap: number): string {
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`
  return `$${cap.toFixed(0)}`
}

function formatEps(val: number | null): string {
  if (val === null || val === undefined) return '--'
  return `$${val.toFixed(2)}`
}

function formatRevenue(val: number | null): string {
  if (val === null || val === undefined) return '--'
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`
  if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`
  return `$${val.toFixed(0)}`
}

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  const { start, end } = formatMonthRange()

  try {
    const res = await fetchEarningsCalendar(start, end)
    earningsEvents.value = res.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载财报日历失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <section class="page-section">
    <MarketSentimentCard />

    <Card class="surface-panel calendar-panel">
      <template #content>
        <div class="surface-panel__content">
          <div class="calendar-panel__header">
            <div>
              <p class="eyebrow">Financial Calendar</p>
              <h2 class="panel-title calendar-panel__title">美股财报日历</h2>
              <p class="panel-subtitle calendar-panel__subtitle">
                通过 Yahoo Finance 获取的美股财报日历，包含 EPS/营收预估数据。
              </p>
            </div>
            <div class="calendar-panel__nav">
              <button class="p-button p-button-sm p-button-text" type="button" aria-label="上个月" @click="goToPrevMonth">
                <span class="pi pi-chevron-left" />
              </button>
              <span class="month-label">{{ monthLabel }}</span>
              <button class="p-button p-button-sm p-button-text" type="button" aria-label="下个月" @click="goToNextMonth">
                <span class="pi pi-chevron-right" />
              </button>
              <button class="p-button p-button-sm p-button-secondary" type="button" @click="goToCurrentMonth">
                本月
              </button>
            </div>
          </div>

          <LoadingBlock v-if="loading" />
          <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

          <template v-else>
            <div v-if="earningsEvents.length === 0" class="empty-state">本月无财报数据</div>
            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>代码</th>
                    <th>公司</th>
                    <th>市值</th>
                    <th>交易所</th>
                    <th class="table-col--number">EPS均值</th>
                    <th class="table-col--number">EPS范围</th>
                    <th class="table-col--number">营收均值</th>
                    <th>电话会议</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in earningsEvents" :key="index">
                    <td>
                      <span class="tag" :class="item.is_estimate ? 'tag--estimate' : 'tag--confirmed'">
                        {{ item.is_estimate ? '预估' : '确认' }}
                      </span>
                      {{ item.date ? item.date.slice(5) : '--' }}
                    </td>
                    <td class="cell-symbol">{{ item.symbol }}</td>
                    <td class="cell-company">{{ item.name }}</td>
                    <td class="table-col--number">{{ formatMarketcap(item.mcap) }}</td>
                    <td>
                      <span class="exchange-tag">{{ item.exchange || '--' }}</span>
                    </td>
                    <td class="table-col--number">{{ formatEps(item.eps_avg) }}</td>
                    <td class="table-col--number">
                      <span v-if="item.eps_low !== null && item.eps_high !== null" class="eps-range">
                        {{ formatEps(item.eps_low) }} ~ {{ formatEps(item.eps_high) }}
                      </span>
                      <span v-else>--</span>
                    </td>
                    <td class="table-col--number">{{ formatRevenue(item.rev_avg) }}</td>
                    <td>{{ item.call_date || '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="calendar-panel__footnote">
              共 {{ earningsEvents.length }} 家公司财报
            </p>
          </template>
        </div>
      </template>
    </Card>
  </section>
</template>

<style scoped>
.page-section :deep(.sentiment-card) {
  margin-bottom: var(--space-5);
}

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

.month-label {
  min-width: 100px;
  text-align: center;
  font-weight: 600;
  font-size: 1rem;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.data-table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-surface-raised);
  position: sticky;
  top: 0;
}

.data-table tbody tr:hover {
  background: var(--color-surface-hover);
}

.table-col--number {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.cell-symbol {
  font-weight: 600;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  color: var(--primitive-color-blue-400);
  white-space: nowrap;
}

.cell-company {
  font-weight: 600;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exchange-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(129, 160, 207, 0.1);
  font-weight: 600;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  margin-right: 4px;
}

.tag--confirmed {
  background: rgba(52, 210, 163, 0.15);
  color: var(--color-positive);
}

.tag--estimate {
  background: rgba(255, 189, 122, 0.15);
  color: #ffbd7a;
}

.eps-range {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.calendar-panel__footnote {
  margin-top: var(--space-3);
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  text-align: right;
}

@media (max-width: 900px) {
  .calendar-panel__header {
    flex-direction: column;
  }
}
</style>
