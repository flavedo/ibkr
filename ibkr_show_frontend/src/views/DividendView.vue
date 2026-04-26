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
            <InputText v-model="state.start_date" type="date" />
          </label>
          <label class="field-stack">
            <span class="field-stack__label">结束日期</span>
            <InputText v-model="state.end_date" type="date" />
          </label>
          <label class="field-stack">
            <span class="field-stack__label">代码</span>
            <InputText v-model="state.symbol" type="text" placeholder="QQQI" />
          </label>
          <div class="field-stack field-stack--action">
            <Button label="刷新分红" icon="pi pi-search" class="p-button p-button--accent" type="submit" />
          </div>
        </form>
      </div>
    </section>

    <LoadingBlock v-if="loading" />
    <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

    <template v-else>
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
              <table class="data-table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>代码</th>
                    <th>描述</th>
                    <th>数量</th>
                    <th class="table-col--number" @click="setSort('gross_amount')" style="cursor: pointer">
                      Gross金额 <span v-if="sortKey === 'gross_amount'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                    </th>
                    <th class="table-col--number" @click="setSort('amount')" style="cursor: pointer">
                      Net金额 <span v-if="sortKey === 'amount'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
                    </th>
                    <th>Activity</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in paginatedDividends" :key="item.transaction_id ?? ''">
                    <td>{{ formatDate(item.date_time) }}</td>
                    <td>{{ item.symbol ?? '--' }}</td>
                    <td>{{ item.description ?? '--' }}</td>
                    <td>{{ item.activity_description ?? '--' }}</td>
                    <td class="table-col--number" :class="toneByNumber(item.gross_amount)">
                      {{ formatNumber(item.gross_amount) }}
                    </td>
                    <td class="table-col--number" :class="toneByNumber(item.amount)">
                      {{ formatNumber(item.amount) }}
                    </td>
                    <td>{{ item.activity_code ?? '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <Paginator
              :rows="state.page_size"
              :totalRecords="sortedDividends.length"
              :first="(state.page - 1) * state.page_size"
              :rowsPerPageOptions="[20, 50, 100]"
              @page="onPageChange"
            />
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
}

.data-table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-surface-raised);
}

.data-table tbody tr:hover {
  background: var(--color-surface-hover);
}

.table-col--number {
  text-align: right;
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
</style>