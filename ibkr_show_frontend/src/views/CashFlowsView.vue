<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'

import { fetchCashFlows, fetchCashFlowSummary } from '@/api/cashFlows'
import CashFlowTable from '@/components/CashFlowTable.vue'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import StatCard from '@/components/StatCard.vue'
import type {
  CashFlowCurrencySummaryItem,
  CashFlowItem,
  CashFlowSummaryResponse,
} from '@/types/cashFlows'

const state = reactive({
  start_date: '',
  end_date: '',
  currency: '',
  flow_direction: '',
  page: 1,
  page_size: 20,
})

const cashFlowItems = ref<CashFlowItem[]>([])
const cashFlowSummary = ref<CashFlowSummaryResponse | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const sortKey = ref<'date_time' | 'amount' | null>(null)
const sortOrder = ref<'asc' | 'desc'>('desc')

function formatNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return '--'
  }
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

async function loadCashFlows(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  try {
    const [summaryResponse, listResponse] = await Promise.all([
      fetchCashFlowSummary({
        start_date: state.start_date,
        end_date: state.end_date,
        currency: state.currency,
        flow_direction: state.flow_direction,
      }),
      fetchCashFlows({
        start_date: state.start_date,
        end_date: state.end_date,
        currency: state.currency,
        flow_direction: state.flow_direction,
        sort_by: 'date_time',
        sort_order: 'desc',
        page: 1,
        page_size: 200,
      }),
    ])

    cashFlowSummary.value = summaryResponse
    cashFlowItems.value = listResponse.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载出入金记录失败'
  } finally {
    loading.value = false
  }
}

function applyFilters(): void {
  state.page = 1
  void loadCashFlows()
}

function setDirection(nextDirection: 'deposit' | 'withdrawal'): void {
  state.flow_direction = state.flow_direction === nextDirection ? '' : nextDirection
  applyFilters()
}

function setSort(nextKey: 'date_time' | 'amount'): void {
  if (sortKey.value === nextKey) {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortKey.value = nextKey
    sortOrder.value = 'desc'
  }
  state.page = 1
}

function onPageChange(event: { page: number; rows: number }): void {
  state.page = event.page + 1
  state.page_size = event.rows
}

function toneByNumber(value: number | null | undefined): 'positive' | 'negative' | 'neutral' {
  if (!value) {
    return 'neutral'
  }
  return value > 0 ? 'positive' : 'negative'
}

const currencySummaries = computed<CashFlowCurrencySummaryItem[]>(() => {
  return cashFlowSummary.value?.by_currency ?? []
})

const sortedCashFlows = computed(() => {
  const items = [...cashFlowItems.value]
  if (!sortKey.value) {
    return items
  }

  items.sort((left, right) => {
    if (sortKey.value === 'date_time') {
      const leftTime = left.date_time ? Date.parse(left.date_time) : Number.NEGATIVE_INFINITY
      const rightTime = right.date_time ? Date.parse(right.date_time) : Number.NEGATIVE_INFINITY
      const result = leftTime - rightTime
      return sortOrder.value === 'asc' ? result : -result
    }

    const leftAmount = typeof left.amount === 'number' ? left.amount : Number.NEGATIVE_INFINITY
    const rightAmount = typeof right.amount === 'number' ? right.amount : Number.NEGATIVE_INFINITY
    const result = leftAmount - rightAmount
    return sortOrder.value === 'asc' ? result : -result
  })

  return items
})

const paginatedCashFlows = computed(() => {
  const startIndex = (state.page - 1) * state.page_size
  return sortedCashFlows.value.slice(startIndex, startIndex + state.page_size)
})

function currencyLabel(value: string | null): string {
  return value ?? '未知币种'
}

onMounted(() => {
  void loadCashFlows()
})
</script>

<template>
  <section class="page-section">
    <LoadingBlock v-if="loading" />
    <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

    <template v-else>
      <section class="surface-panel">
        <div class="surface-panel__content">
          <section class="stats-grid stats-grid--summary">
            <StatCard title="流水笔数" :value="String(cashFlowSummary?.record_count ?? 0)" icon="pi pi-list" tone="accent" />
            <StatCard title="入金笔数" :value="String(cashFlowSummary?.deposit_count ?? 0)" icon="pi pi-arrow-down-left" tone="positive" />
            <StatCard title="出金笔数" :value="String(cashFlowSummary?.withdrawal_count ?? 0)" icon="pi pi-arrow-up-right" tone="negative" />
          </section>
        </div>
      </section>

      <section class="surface-panel">
        <div class="surface-panel__content">
          <div class="section-header">
            <div>
              <h2 class="panel-title">筛选与排序</h2>
              <p class="panel-subtitle">按时间、币种和方向查看历史入金与出金流水。</p>
            </div>
          </div>

          <form class="cash-flow-filters" @submit.prevent="applyFilters">
            <label class="field-stack">
              <span class="field-stack__label">开始日期</span>
              <InputText v-model="state.start_date" type="date" class="filter-input" />
            </label>
            <label class="field-stack">
              <span class="field-stack__label">结束日期</span>
              <InputText v-model="state.end_date" type="date" class="filter-input" />
            </label>
            <label class="field-stack">
              <span class="field-stack__label">币种</span>
              <InputText v-model="state.currency" type="text" placeholder="USD / CNH / HKD" class="filter-input" />
            </label>
            <div class="field-stack">
              <div class="cash-flow-direction__label-row">
                <span class="field-stack__label">方向</span>
                <span class="cash-flow-direction__helper">默认全部</span>
              </div>
              <div class="cash-flow-direction">
                <button
                  type="button"
                  class="side-btn"
                  :class="{ 'side-btn--active': state.flow_direction === 'deposit' }"
                  @click="setDirection('deposit')"
                >
                  入金
                </button>
                <button
                  type="button"
                  class="side-btn"
                  :class="{ 'side-btn--active': state.flow_direction === 'withdrawal' }"
                  @click="setDirection('withdrawal')"
                >
                  出金
                </button>
              </div>
            </div>
            <div class="field-stack field-stack--action">
              <button type="submit" class="refresh-btn">
                <i class="pi pi-refresh"></i>
                刷新出入金
              </button>
            </div>
          </form>
        </div>
      </section>

      <section v-if="currencySummaries.length > 0" class="currency-summary-list">
        <section v-for="item in currencySummaries" :key="item.currency ?? 'unknown'" class="surface-panel">
          <div class="surface-panel__content">
            <div class="section-header">
              <div>
                <h2 class="panel-title">{{ currencyLabel(item.currency) }} 资金统计</h2>
                <p class="panel-subtitle">
                  {{ item.record_count }} 笔流水 · 入金 {{ item.deposit_count }} 笔 · 出金 {{ item.withdrawal_count }} 笔
                </p>
              </div>
            </div>

            <section class="stats-grid stats-grid--summary">
              <StatCard title="累计入金" :value="formatNumber(item.total_deposit_amount)" icon="pi pi-plus-circle" tone="positive" />
              <StatCard title="累计出金" :value="formatNumber(item.total_withdrawal_amount)" icon="pi pi-minus-circle" tone="negative" />
              <StatCard title="净流入" :value="formatNumber(item.net_amount)" icon="pi pi-chart-line" :tone="toneByNumber(item.net_amount)" />
            </section>
          </div>
        </section>
      </section>

      <section class="surface-panel">
        <div class="surface-panel__content">
          <div class="section-header">
            <div>
              <h2 class="panel-title">出入金明细表</h2>
              <p class="panel-subtitle">按账户资金流记录展示发生时间、结算日、币种和金额，点击表头可按发生时间和金额排序。</p>
            </div>
          </div>
          <template v-if="cashFlowItems.length > 0">
            <CashFlowTable
              :items="paginatedCashFlows"
              :format-number="formatNumber"
              :sort-key="sortKey"
              :sort-order="sortOrder"
              :on-sort="setSort"
            />
            <div class="trade-paginator-wrapper">
              <Paginator
                :rows="state.page_size"
                :totalRecords="sortedCashFlows.length"
                :first="(state.page - 1) * state.page_size"
                :rowsPerPageOptions="[20, 50, 100]"
                @page="onPageChange"
              />
            </div>
          </template>
          <div v-else class="empty-state">暂无出入金记录</div>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.terminal-hero-side {
  display: grid;
  gap: var(--space-4);
  align-content: center;
}

.terminal-hero-side strong {
  font-size: 1.6rem;
}

.currency-summary-list {
  display: grid;
  gap: var(--space-4);
}

.cash-flow-filters {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--space-3);
  align-items: end;
}

.filter-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  background: rgba(15, 23, 42, 0.6);
  color: #e2e8f0;
  font-size: 0.9rem;
  font-family: inherit;
  outline: none;
  transition: all 200ms ease;

  &:focus {
    border-color: rgba(86, 213, 255, 0.5);
    box-shadow: 0 0 0 3px rgba(86, 213, 255, 0.1);
  }

  &::placeholder {
    color: #64748b;
  }

  &::-webkit-calendar-picker-indicator {
    filter: invert(1) opacity(0.6);
    cursor: pointer;
  }
}

.cash-flow-direction {
  display: flex;
  gap: 8px;
}

.side-btn {
  flex: 1;
  padding: 9px 16px;
  border-radius: 10px;
  border: 1px solid rgba(71, 85, 105, 0.35);
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;

  &:hover {
    border-color: rgba(148, 163, 184, 0.45);
    color: #cbd5e1;
    background: rgba(25, 40, 65, 0.7);
  }

  &--active {
    &.side-btn:nth-child(1) {
      background: linear-gradient(135deg, rgba(52, 210, 163, 0.2), rgba(16, 95, 70, 0.3));
      border-color: rgba(52, 210, 163, 0.4);
      color: #34d2a3;
      box-shadow: 0 0 12px rgba(52, 210, 163, 0.15);
    }

    &.side-btn:nth-child(2) {
      background: linear-gradient(135deg, rgba(255, 107, 125, 0.2), rgba(120, 30, 50, 0.3));
      border-color: rgba(255, 107, 125, 0.4);
      color: #ff6b7d;
      box-shadow: 0 0 12px rgba(255, 107, 125, 0.15);
    }
  }
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 10px;
  border: 1px solid rgba(86, 213, 255, 0.3);
  background: linear-gradient(135deg, rgba(60, 146, 255, 0.15), rgba(25, 92, 182, 0.2));
  color: #56d5ff;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
  white-space: nowrap;

  &:hover {
    background: linear-gradient(135deg, rgba(60, 146, 255, 0.25), rgba(25, 92, 182, 0.35));
    border-color: rgba(86, 213, 255, 0.5);
    box-shadow: 0 4px 16px rgba(86, 213, 255, 0.2);
    transform: translateY(-1px);
  }

  i {
    font-size: 0.85rem;
  }
}

.cash-flow-direction__label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cash-flow-direction__helper {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
}

.trade-paginator-wrapper {
  margin-top: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(129, 160, 207, 0.12);

  :deep(.p-paginator) {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    background: transparent;
    padding: 0;
  }

  :deep(.p-paginator-pages) {
    display: flex;
    gap: 6px;
  }

  :deep(.p-paginator-page),
  :deep(.p-paginator-prev),
  :deep(.p-paginator-next),
  :deep(.p-paginator-first),
  :deep(.p-paginator-last) {
    min-width: 36px;
    min-height: 36px;
    padding: 8px 14px;
    border-radius: 10px;
    border: 1px solid rgba(71, 85, 105, 0.3);
    background: rgba(15, 23, 42, 0.6);
    color: #94a3b8;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 200ms ease;

    &:hover:not(.p-disabled) {
      border-color: rgba(86, 213, 255, 0.4);
      background: rgba(25, 45, 75, 0.7);
      color: #cbd5e1;
      transform: translateY(-1px);
    }
  }

  :deep(.p-paginator-page.p-paginator-page-selected) {
    border-color: rgba(86, 213, 255, 0.5);
    background: linear-gradient(135deg, rgba(60, 146, 255, 0.2), rgba(25, 92, 182, 0.3));
    color: #56d5ff;
    font-weight: 700;
    box-shadow: 0 0 12px rgba(86, 213, 255, 0.15);
  }

  :deep(.p-paginator-rpp-dropdown) {
    min-width: auto;
    height: 36px;
    padding: 6px 12px;
    border-radius: 10px;
    border: 1px solid rgba(71, 85, 105, 0.3);
    background: rgba(15, 23, 42, 0.6);
    color: #94a3b8;
    font-size: 0.85rem;
  }

  :deep(.p-paginator-current) {
    color: #64748b;
    font-size: 0.84rem;
    margin: 0 12px;
  }

  :deep(.p-disabled) {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

@media (max-width: 1200px) {
  .cash-flow-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .cash-flow-filters {
    grid-template-columns: 1fr;
  }

  .cash-flow-direction {
    flex-wrap: wrap;
  }
}
</style>
