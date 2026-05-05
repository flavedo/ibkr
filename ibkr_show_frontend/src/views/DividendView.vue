<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'

import { fetchDividends, fetchDividendSummary } from '@/api/dividends'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import StatCard from '@/components/StatCard.vue'
import type { DividendItem } from '@/api/dividends'

const state = reactive({
  start_date: '',
  end_date: '',
  symbol: '',
  page: 1,
  page_size: 20,
})

const dividendItems = ref<DividendItem[]>([])
const loading = ref(true)
const errorMessage = ref('')
const sortKey = ref<'amount' | 'gross_amount' | null>(null)
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

const sortedDividends = computed(() => {
  const values = [...dividendItems.value]
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

const paginatedDividends = computed(() => {
  const startIndex = (state.page - 1) * state.page_size
  return sortedDividends.value.slice(startIndex, startIndex + state.page_size)
})

const dividendSummary = computed(() => {
  const items = dividendItems.value
  const amountBySymbol: Record<string, number> = {}

  items.forEach((item) => {
    const sym = item.symbol ?? 'Unknown'
    amountBySymbol[sym] = (amountBySymbol[sym] ?? 0) + (item.amount ?? 0)
  })

  return {
    record_count: items.length,
    total_amount: items.reduce((sum, item) => sum + (item.amount ?? 0), 0),
    total_gross_amount: items.reduce((sum, item) => sum + (item.gross_amount ?? 0), 0),
    by_symbol: Object.entries(amountBySymbol)
      .sort((left, right) => left[0].localeCompare(right[0]))
      .map(([symbol, amount]) => ({ symbol, amount })),
  }
})

async function fetchAllDividends(): Promise<DividendItem[]> {
  const filters = {
    start_date: state.start_date,
    end_date: state.end_date,
    symbol: state.symbol.trim().toUpperCase(),
    sort_by: 'date_time',
    sort_order: 'desc' as const,
    page_size: 200,
  }

  const firstPage = await fetchDividends({
    ...filters,
    page: 1,
  })

  const items = [...firstPage.items]

  for (let page = 2; page <= firstPage.pagination.total_pages; page += 1) {
    const nextPage = await fetchDividends({
      ...filters,
      page,
    })
    items.push(...nextPage.items)
  }

  return items
}

async function loadDividends(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  try {
    dividendItems.value = await fetchAllDividends()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载分红记录失败'
  } finally {
    loading.value = false
  }
}

function applyFilters(): void {
  state.page = 1
  void loadDividends()
}

function setSort(nextKey: 'amount' | 'gross_amount'): void {
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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '--'
  return dateStr.slice(0, 10)
}

onMounted(() => {
  void loadDividends()
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
            <StatCard title="分红笔数" :value="String(dividendSummary.record_count)" icon="pi pi-list" tone="accent" />
            <StatCard title="分红总额" :value="formatNumber(dividendSummary.total_amount)" icon="pi pi-dollar" :tone="toneByNumber(dividendSummary.total_amount)" />
            <StatCard title="Gross总额" :value="formatNumber(dividendSummary.total_gross_amount)" icon="pi pi-dollar" :tone="toneByNumber(dividendSummary.total_gross_amount)" />
            <StatCard
              v-for="item in dividendSummary.by_symbol"
              :key="item.symbol"
              :title="`${item.symbol} 分红`"
              :value="formatNumber(item.amount)"
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
              <h2 class="panel-title">分红筛选</h2>
              <p class="panel-subtitle">支持按日期和代码筛选，排序直接在表头完成。</p>
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
              <InputText v-model="state.symbol" type="text" placeholder="QQQI" class="filter-input" />
            </label>
            <div class="field-stack field-stack--action">
              <button type="submit" class="refresh-btn">
                <i class="pi pi-refresh"></i>
                刷新分红
              </button>
            </div>
          </form>
        </div>
      </section>

      <section class="surface-panel">
        <div class="surface-panel__content">
          <div class="section-header">
            <div>
              <h2 class="panel-title">分红明细表</h2>
              <p class="panel-subtitle">点击表头可按金额排序。</p>
            </div>
          </div>
          <template v-if="dividendItems.length > 0">
            <div class="table-wrapper">
              <table class="data-table dividend-table">
                <colgroup>
                  <col style="width: 15%" />
                  <col style="width: 10%" />
                  <col style="width: 25%" />
                  <col style="width: 12%" />
                  <col style="width: 14%" />
                  <col style="width: 14%" />
                  <col style="width: 10%" />
                </colgroup>
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>代码</th>
                    <th>描述</th>
                    <th>活动描述</th>
                    <th class="sortable" @click="setSort('gross_amount')">
                      Gross金额
                      <span v-if="sortKey === 'gross_amount'" class="sort-indicator">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                    </th>
                    <th class="sortable" @click="setSort('amount')">
                      Net金额
                      <span v-if="sortKey === 'amount'" class="sort-indicator">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                    </th>
                    <th>Activity</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in paginatedDividends" :key="item.transaction_id ?? ''">
                    <td>{{ formatDate(item.date_time) }}</td>
                    <td><strong>{{ item.symbol ?? '--' }}</strong></td>
                    <td>{{ item.description ?? '--' }}</td>
                    <td>{{ item.activity_description ?? '--' }}</td>
                    <td class="number-cell" :class="toneByNumber(item.gross_amount)">
                      {{ formatNumber(item.gross_amount) }}
                    </td>
                    <td class="number-cell" :class="toneByNumber(item.amount)">
                      {{ formatNumber(item.amount) }}
                    </td>
                    <td><span class="tag-badge">{{ item.activity_code ?? '--' }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="trade-paginator-wrapper">
              <Paginator
                :rows="state.page_size"
                :totalRecords="sortedDividends.length"
                :first="(state.page - 1) * state.page_size"
                :rowsPerPageOptions="[20, 50, 100]"
                @page="onPageChange"
              />
            </div>
          </template>
          <div v-else class="empty-state">暂无分红数据</div>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.trade-filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
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

.table-wrapper {
  overflow-x: auto;
  border-radius: 16px;
  border: 1px solid rgba(129, 160, 207, 0.08);
}

.dividend-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 0.88rem;

  th,
  td {
    padding: 16px 14px;
    text-align: left;
    vertical-align: middle;
  }

  thead th {
    font-weight: 700;
    font-size: 0.84rem;
    letter-spacing: 0.02em;
    color: #94a3b8;
    background: rgba(15, 23, 42, 0.4);
    border-bottom: 2px solid rgba(86, 213, 255, 0.15);
    white-space: nowrap;
  }

  tbody tr {
    transition: all 200ms ease;
    border-bottom: 1px solid rgba(129, 160, 207, 0.06);

    &:hover td {
      background: rgba(86, 213, 255, 0.04);
    }
  }

  .sortable {
    cursor: pointer;
    user-select: none;
    white-space: nowrap;

    &:hover {
      color: #56d5ff;
    }
  }

  .sort-indicator {
    color: #56d5ff;
    font-weight: 800;
    font-size: 0.9rem;
  }

  .number-cell {
    text-align: right;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  .tag-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(86, 213, 255, 0.1);
    border: 1px solid rgba(86, 213, 255, 0.25);
    color: #56d5ff;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
}

.positive {
  color: var(--color-tone-positive);
}

.negative {
  color: var(--color-tone-negative);
}

.neutral {
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
}
</style>