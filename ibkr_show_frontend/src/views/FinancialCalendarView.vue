<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'

import { fetchEarningsCalendar, fetchEconomicCalendar } from '@/api/financialCalendar'
import type { EarningsEvent, EconomicEvent } from '@/api/financialCalendar'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import MarketSentimentCard from '@/components/MarketSentimentCard.vue'

const activeTab = ref<'earnings' | 'economic'>('earnings')
const earningsEvents = ref<EarningsEvent[]>([])
const economicEvents = ref<EconomicEvent[]>([])
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

function formatMarketcap(cap: number | null): string {
  if (cap === null) return '--'
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`
  return `$${cap.toFixed(0)}`
}

function formatNullable(val: number | null | undefined, digits = 2): string {
  if (val === null || val === undefined) return '--'
  return val.toFixed(digits)
}

function formatEps(val: number | null | undefined): string {
  if (val === null || val === undefined) return '--'
  return `$${val.toFixed(2)}`
}

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  const { start, end } = formatMonthRange()

  try {
    if (activeTab.value === 'earnings') {
      const res = await fetchEarningsCalendar(start, end)
      earningsEvents.value = res.items
    } else {
      const res = await fetchEconomicCalendar(start, end)
      economicEvents.value = res.items
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载财经日历失败'
  } finally {
    loading.value = false
  }
}

async function switchTab(tab: 'earnings' | 'economic'): Promise<void> {
  activeTab.value = tab
  await loadData()
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <section class="page-section">
    <Card class="surface-panel calendar-panel">
      <template #content>
        <div class="surface-panel__content">
          <div class="calendar-panel__header">
            <div>
              <p class="eyebrow">Financial Calendar</p>
              <h2 class="panel-title calendar-panel__title">财经日历</h2>
              <p class="panel-subtitle calendar-panel__subtitle">
                通过 Yahoo Finance 获取的美股财报与全球经济事件日历。
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

          <MarketSentimentCard />

          <div class="calendar-panel__tabs">
            <button
              class="tab-button"
              :class="{ 'tab-button--active': activeTab === 'earnings' }"
              @click="switchTab('earnings')"
            >
              📈 美股财报
            </button>
            <button
              class="tab-button"
              :class="{ 'tab-button--active': activeTab === 'economic' }"
              @click="switchTab('economic')"
            >
              📊 经济事件
            </button>
          </div>

          <LoadingBlock v-if="loading" />
          <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

          <template v-else-if="activeTab === 'earnings'">
            <div v-if="earningsEvents.length === 0" class="empty-state">本月无财报数据</div>
            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>公司</th>
                    <th>市值</th>
                    <th>事件</th>
                    <th>日期</th>
                    <th>时段</th>
                    <th>EPS预估</th>
                    <th>实际EPS</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in earningsEvents" :key="index">
                    <td class="cell-company">{{ item.company }}</td>
                    <td class="table-col--number">{{ formatMarketcap(item.marketcap) }}</td>
                    <td>{{ item.event_name ?? '--' }}</td>
                    <td>{{ item.date_time?.slice(5, 16) ?? '--' }}</td>
                    <td>
                      <span v-if="item.timing === 'AMC'" class="tag tag--amc">盘后</span>
                      <span v-else-if="item.timing === 'BMO'" class="tag tag--bmo">盘前</span>
                      <span v-else-if="item.timing === 'TAS'" class="tag tag--tas">盘中</span>
                      <span v-else>{{ item.timing || '--' }}</span>
                    </td>
                    <td class="table-col--number">{{ formatEps(item.eps_estimate) }}</td>
                    <td class="table-col--number">{{ formatEps(item.reported_eps) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="calendar-panel__footnote">
              共 {{ earningsEvents.length }} 条财报事件
            </p>
          </template>

          <template v-else-if="activeTab === 'economic'">
            <div v-if="economicEvents.length === 0" class="empty-state">本月无经济事件数据</div>
            <div v-else class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>事件</th>
                    <th>地区</th>
                    <th>时间</th>
                    <th>对应月份</th>
                    <th class="table-col--number">实际值</th>
                    <th class="table-col--number">预期值</th>
                    <th class="table-col--number">前值</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in economicEvents" :key="index">
                    <td class="cell-event-name">{{ item.event_name ?? '--' }}</td>
                    <td>
                      <span class="region-flag">{{ item.region }}</span>
                    </td>
                    <td>{{ item.event_time?.slice(5, 16) ?? '--' }}</td>
                    <td>{{ item.for_period ?? '--' }}</td>
                    <td class="table-col--number">{{ formatNullable(item.actual) }}</td>
                    <td class="table-col--number">{{ formatNullable(item.expected) }}</td>
                    <td class="table-col--number">{{ formatNullable(item.last) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="calendar-panel__footnote">
              共 {{ economicEvents.length }} 条经济事件
            </p>
          </template>
        </div>
      </template>
    </Card>
  </section>
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

.month-label {
  min-width: 100px;
  text-align: center;
  font-weight: 600;
  font-size: 1rem;
}

.calendar-panel__tabs {
  display: flex;
  gap: 8px;
  margin-bottom: var(--space-4);
}

.tab-button {
  padding: 8px 20px;
  border: 1px solid rgba(129, 160, 207, 0.16);
  border-radius: 10px;
  background: rgba(10, 18, 32, 0.6);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.15s ease;
}

.tab-button:hover {
  border-color: rgba(86, 213, 255, 0.3);
  background: rgba(18, 38, 64, 0.8);
}

.tab-button--active {
  border-color: rgba(86, 213, 255, 0.35);
  background: linear-gradient(180deg, rgba(32, 79, 129, 0.94), rgba(16, 45, 81, 0.96));
  color: var(--color-text-primary);
  box-shadow: 0 0 20px rgba(62, 169, 255, 0.1);
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

.cell-company {
  font-weight: 600;
}

.cell-event-name {
  font-weight: 500;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.region-flag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(129, 160, 207, 0.1);
  font-weight: 600;
  font-size: 0.85rem;
  letter-spacing: 0.04em;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
}

.tag--amc {
  background: rgba(52, 210, 163, 0.15);
  color: var(--color-positive);
}

.tag--bmo {
  background: rgba(255, 189, 122, 0.15);
  color: #ffbd7a;
}

.tag--tas {
  background: rgba(86, 213, 255, 0.12);
  color: var(--color-accent-strong);
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
