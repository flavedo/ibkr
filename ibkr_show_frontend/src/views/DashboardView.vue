<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { fetchAccountOverview } from '@/api/account'
import { fetchEquityCurve } from '@/api/charts'
import { useCurrency } from '@/composables/useCurrency'
import EquityCurveSimple from '@/components/EquityCurveSimple.vue'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PerformanceCalendar from '@/components/PerformanceCalendar.vue'
import StatCard from '@/components/StatCard.vue'
import type { AccountDeltaMetric, AccountOverview } from '@/types/account'
import type { EquityCurvePoint } from '@/types/charts'

const overview = ref<AccountOverview | null>(null)
const curveItems = ref<EquityCurvePoint[]>([])
const loading = ref(true)
const errorMessage = ref('')
let refreshTimer: number | null = null

const {
  currentCurrency,
  switchCurrency,
  convertValue,
  formatConverted,
} = useCurrency()

function formatNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return '--'
  }
  if (currentCurrency.value === 'CNH') {
    return formatConverted(value, digits)
  }
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

function formatPercent(value: number | null): string {
  if (value === null) {
    return '--'
  }
  return `${formatNumber(value, 2)}%`
}

function formatSignedNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return ''
  }
  const converted = currentCurrency.value === 'CNH' ? convertValue(value) : value
  if (converted === null) return ''
  const prefix = converted > 0 ? '+' : ''
  return `${prefix}${new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Math.abs(converted))}`
}

function formatSignedPercent(value: number | null): string {
  if (value === null) {
    return ''
  }
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(value))}%`
}

function deltaTone(metric: AccountDeltaMetric | null): 'neutral' | 'positive' | 'negative' | 'accent' {
  if (!metric || !metric.amount_change) {
    return 'neutral'
  }
  return metric.amount_change > 0 ? 'positive' : 'negative'
}

function metricTone(value: number | null, fallback: 'neutral' | 'accent' = 'neutral'): 'neutral' | 'positive' | 'negative' | 'accent' {
  if (value === null || value === 0) {
    return fallback
  }
  return value > 0 ? 'positive' : 'negative'
}

const statCards = computed(() => {
  if (!overview.value) {
    return []
  }

  return [
    {
      title: '总权益',
      value: formatNumber(overview.value.total_equity),
      helper: overview.value.report_date,
      icon: 'pi pi-wallet',
      tone: 'accent' as const,
      deltaAmount: formatSignedNumber(overview.value.total_equity_delta?.amount_change ?? null),
      deltaPercent: formatSignedPercent(overview.value.total_equity_delta?.percent_change ?? null),
      deltaTone: deltaTone(overview.value.total_equity_delta),
    },
    { title: '现金', value: formatNumber(overview.value.cash), icon: 'pi pi-dollar', tone: 'neutral' as const },
    { title: '股票市值', value: formatNumber(overview.value.stock_value), icon: 'pi pi-chart-bar', tone: 'neutral' as const },
    {
      title: '已实现盈亏',
      value: formatNumber(overview.value.fifo_total_realized_pnl),
      icon: 'pi pi-check-circle',
      tone: overview.value.fifo_total_realized_pnl !== null && overview.value.fifo_total_realized_pnl < 0 ? 'negative' as const : 'positive' as const,
      deltaAmount: formatSignedNumber(overview.value.fifo_total_realized_pnl_delta?.amount_change ?? null),
      deltaPercent: formatSignedPercent(overview.value.fifo_total_realized_pnl_delta?.percent_change ?? null),
      deltaTone: deltaTone(overview.value.fifo_total_realized_pnl_delta),
    },
    {
      title: '未实现盈亏',
      value: formatNumber(overview.value.fifo_total_unrealized_pnl),
      icon: 'pi pi-bolt',
      tone: overview.value.fifo_total_unrealized_pnl !== null && overview.value.fifo_total_unrealized_pnl < 0 ? 'negative' as const : 'positive' as const,
      deltaAmount: formatSignedNumber(overview.value.fifo_total_unrealized_pnl_delta?.amount_change ?? null),
      deltaPercent: formatSignedPercent(overview.value.fifo_total_unrealized_pnl_delta?.percent_change ?? null),
      deltaTone: deltaTone(overview.value.fifo_total_unrealized_pnl_delta),
    },
    {
      title: '总盈亏',
      value: formatNumber(overview.value.fifo_total_pnl),
      icon: 'pi pi-chart-line',
      tone: overview.value.fifo_total_pnl !== null && overview.value.fifo_total_pnl < 0 ? 'negative' as const : 'positive' as const,
      deltaAmount: formatSignedNumber(overview.value.fifo_total_pnl_delta?.amount_change ?? null),
      deltaPercent: formatSignedPercent(overview.value.fifo_total_pnl_delta?.percent_change ?? null),
      deltaTone: deltaTone(overview.value.fifo_total_pnl_delta),
    },
    {
      title: '当日TWR',
      value: formatPercent(overview.value.cnav_twr),
      helper: 'IBKR CNAV 单日收益率',
      icon: 'pi pi-percentage',
      tone: metricTone(overview.value.cnav_twr, 'accent'),
    },
    {
      title: '年初至今TWR',
      value: formatPercent(overview.value.ytd_twr),
      helper: `${overview.value.report_date.slice(0, 4)}-01-01 至今`,
      icon: 'pi pi-calendar',
      tone: metricTone(overview.value.ytd_twr, 'accent'),
    },
    { 
      title: '年内分红', 
      value: formatNumber(overview.value.crtt_dividends_ytd), 
      icon: 'pi pi-briefcase', 
      tone: 'neutral' as const 
    },
    { 
      title: '年内佣金', 
      value: formatNumber(overview.value.crtt_commissions_ytd), 
      icon: 'pi pi-minus-circle',
       tone: 'negative' as const 
    },
  ]
})

async function loadDashboard(): Promise<void> {
  await loadDashboardData(true)
}

async function loadDashboardData(showLoading: boolean): Promise<void> {
  if (showLoading) {
    loading.value = true
  }
  errorMessage.value = ''

  try {
    const [overviewResponse, curveResponse] = await Promise.all([
      fetchAccountOverview(),
      fetchEquityCurve(),
    ])
    overview.value = overviewResponse
    curveItems.value = curveResponse.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载总览失败'
  } finally {
    if (showLoading) {
      loading.value = false
    }
  }
}

onMounted(() => {
  void loadDashboard()
  refreshTimer = window.setInterval(() => {
    void loadDashboardData(false)
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
  }
})
</script>

<template>
  <section class="page-section">
    <LoadingBlock v-if="loading" />
    <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

    <template v-else>
      <section class="surface-panel dashboard-metrics-panel">
        <div class="surface-panel__content">
          <div class="dashboard-metrics-header">
            <div class="currency-switcher">
              <button
                type="button"
                class="currency-btn"
                :class="{ 'currency-btn--active': currentCurrency === 'CNH' }"
                @click="switchCurrency('CNH')"
              >
                CNH
              </button>
              <button
                type="button"
                class="currency-btn"
                :class="{ 'currency-btn--active': currentCurrency === 'USD' }"
                @click="switchCurrency('USD')"
              >
                USD
              </button>
            </div>
          </div>
          <section class="stats-grid dashboard-metrics-grid">
            <StatCard
              v-for="card in statCards"
              :key="card.title"
              :title="card.title"
              :value="card.value"
              :helper="card.helper"
              :icon="card.icon"
              :tone="card.tone"
              :delta-amount="card.deltaAmount"
              :delta-percent="card.deltaPercent"
              :delta-tone="card.deltaTone"
            />
          </section>
        </div>
      </section>

      <EquityCurveSimple :items="curveItems" :format-number="formatNumber" />
      <PerformanceCalendar :items="curveItems" />
    </template>
  </section>
</template>

<style scoped>
.dashboard-metrics-panel {
  margin-bottom: var(--space-4);
}

.dashboard-metrics-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
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

.dashboard-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}
</style>
