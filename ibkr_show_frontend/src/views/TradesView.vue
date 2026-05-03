<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'

import { fetchTrades } from '@/api/trades'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import StatCard from '@/components/StatCard.vue'
import TradeTable from '@/components/TradeTable.vue'
import type { TradeItem } from '@/types/trades'

const state = reactive({
  start_date: '',
  end_date: '',
  symbol: '',
  buy_sell: '',
  page: 1,
  page_size: 20,
})

const tradeItems = ref<TradeItem[]>([])
const loading = ref(true)
const errorMessage = ref('')
const sortKey = ref<'proceeds' | 'fifo_pnl_realized' | null>(null)
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

const sortedTrades = computed(() => {
  const values = [...tradeItems.value]
  if (!sortKey.value) {
    return values
  }

  values.sort((left, right) => {
    const leftValue = typeof left[sortKey.value!] === 'number' ? Number(left[sortKey.value!]) : Number.NEGATIVE_INFINITY
    const rightValue = typeof right[sortKey.value!] === 'number' ? Number(right[sortKey.value!]) : Number.NEGATIVE_INFINITY
    const result = leftValue - rightValue
    return sortOrder.value === 'asc' ? result : -result
  })

  return values
})

const paginatedTrades = computed(() => {
  const startIndex = (state.page - 1) * state.page_size
  return sortedTrades.value.slice(startIndex, startIndex + state.page_size)
})

const tradeSummary = computed(() => {
  const items = tradeItems.value
  const proceedsByCurrency = new Map<string, number>()

  items.forEach((item) => {
    const currency = `${item.currency ?? ''}`.trim() || '未标币种'
    proceedsByCurrency.set(currency, (proceedsByCurrency.get(currency) ?? 0) + (item.proceeds ?? 0))
  })

  return {
    trade_count: items.length,
    buy_count: items.filter((item) => item.buy_sell === 'BUY').length,
    sell_count: items.filter((item) => item.buy_sell === 'SELL').length,
    total_commission: items.reduce((sum, item) => sum + (item.ib_commission ?? 0), 0),
    total_realized_pnl: items.reduce((sum, item) => sum + (item.fifo_pnl_realized ?? 0), 0),
    proceeds_by_currency: Array.from(proceedsByCurrency.entries())
      .filter(([currency]) => currency !== '未标币种')
      .sort((left, right) => left[0].localeCompare(right[0]))
      .map(([currency, amount]) => ({ currency, amount })),
  }
})

async function fetchAllTrades(): Promise<TradeItem[]> {
  const filters = {
    start_date: state.start_date,
    end_date: state.end_date,
    symbol: state.symbol.trim().toUpperCase(),
    buy_sell: state.buy_sell,
    sort_by: 'date_time',
    sort_order: 'desc' as const,
    page_size: 200,
  }

  const firstPage = await fetchTrades({
    ...filters,
    page: 1,
  })

  const items = [...firstPage.items]

  for (let page = 2; page <= firstPage.pagination.total_pages; page += 1) {
    const nextPage = await fetchTrades({
      ...filters,
      page,
    })
    items.push(...nextPage.items)
  }

  return items
}

async function loadTrades(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  try {
    tradeItems.value = await fetchAllTrades()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载交易记录失败'
  } finally {
    loading.value = false
  }
}

function applyFilters(): void {
  state.page = 1
  void loadTrades()
}

function setSide(nextSide: 'BUY' | 'SELL'): void {
  state.buy_sell = state.buy_sell === nextSide ? '' : nextSide
  applyFilters()
}

function setSort(nextKey: 'proceeds' | 'fifo_pnl_realized'): void {
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

onMounted(() => {
  void loadTrades()
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
            <StatCard title="成交笔数" :value="String(tradeSummary.trade_count)" icon="pi pi-list" tone="accent" />
            <StatCard title="买入笔数" :value="String(tradeSummary.buy_count)" icon="pi pi-arrow-up" tone="positive" />
            <StatCard title="卖出笔数" :value="String(tradeSummary.sell_count)" icon="pi pi-arrow-down" tone="negative" />
            <StatCard title="总佣金" :value="formatNumber(tradeSummary.total_commission, 4)" icon="pi pi-minus-circle" :tone="toneByNumber(tradeSummary.total_commission)" />
            <StatCard title="已实现盈亏" :value="formatNumber(tradeSummary.total_realized_pnl)" icon="pi pi-chart-line" :tone="toneByNumber(tradeSummary.total_realized_pnl)" />
            <StatCard
              v-for="item in tradeSummary.proceeds_by_currency"
              :key="item.currency"
              :title="`${item.currency} 成交净额`"
              :value="formatNumber(item.amount)"
              helper="按币种分组的 proceeds 净和"
              icon="pi pi-chart-bar"
              :tone="toneByNumber(item.amount)"
            />
          </section>
        </div>
      </section>

      <section class="surface-panel">
        <div class="surface-panel__content">
          <div class="section-header">
            <div>
              <h2 class="panel-title">交易筛选</h2>
              <p class="panel-subtitle">支持按日期、代码和买卖方向筛选，排序直接在表头完成。</p>
            </div>
          </div>

          <form class="trade-filters" @submit.prevent="applyFilters">
            <label class="field-stack">
              <span class="field-stack__label">开始日期</span>
              <InputText v-model="state.start_date" type="date" class="filter-input" />
            </label>
            <label class="field-stack">
              <span class="field-stack__label">结束日期</span>
              <InputText v-model="state.end_date" type="date" class="filter-input" />
            </label>
            <label class="field-stack">
              <span class="field-stack__label">代码</span>
              <InputText v-model="state.symbol" type="text" placeholder="AAPL" class="filter-input" />
            </label>
            <div class="field-stack">
              <div class="trade-side-toggle__label-row">
                <span class="field-stack__label">方向</span>
                <span class="trade-side-toggle__helper">默认全部</span>
              </div>
              <div class="trade-side-toggle">
                <button
                  type="button"
                  class="side-btn"
                  :class="{ 'side-btn--active': state.buy_sell === 'BUY' }"
                  @click="setSide('BUY')"
                >
                  买入
                </button>
                <button
                  type="button"
                  class="side-btn"
                  :class="{ 'side-btn--active': state.buy_sell === 'SELL' }"
                  @click="setSide('SELL')"
                >
                  卖出
                </button>
              </div>
            </div>
            <div class="field-stack field-stack--action">
              <button type="submit" class="refresh-btn">
                <i class="pi pi-refresh"></i>
                刷新交易
              </button>
            </div>
          </form>
        </div>
      </section>

      <section class="surface-panel">
        <div class="surface-panel__content">
          <div class="section-header">
            <div>
              <h2 class="panel-title">交易明细表</h2>
              <p class="panel-subtitle">点击表头可按成交金额和已实现盈亏排序。</p>
            </div>
          </div>
          <template v-if="tradeItems.length > 0">
            <TradeTable
              :items="paginatedTrades"
              :format-number="formatNumber"
              :sort-key="sortKey"
              :sort-order="sortOrder"
              :on-sort="setSort"
            />
            <div class="trade-paginator-wrapper">
              <Paginator
                :rows="state.page_size"
                :totalRecords="sortedTrades.length"
                :first="(state.page - 1) * state.page_size"
                :rowsPerPageOptions="[20, 50, 100]"
                @page="onPageChange"
              />
            </div>
          </template>
          <div v-else class="empty-state">暂无交易数据</div>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.trade-filters {
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

.trade-side-toggle {
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

.trade-side-toggle__label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trade-side-toggle__helper {
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
  .trade-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .trade-filters {
    grid-template-columns: 1fr;
  }

  .trade-side-toggle {
    flex-wrap: wrap;
  }
}
</style>
