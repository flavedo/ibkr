<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'

import { fetchCashFlows, fetchCashFlowSummary } from '@/api/cashFlows'
import { importCSV } from '@/api/data'
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

const fileInput = ref<HTMLInputElement | null>(null)
const showImportDialog = ref(false)
const isImporting = ref(false)
const importMessage = ref('')
const importSuccess = ref(false)

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

function openImportDialog(): void {
  importMessage.value = ''
  importSuccess.value = false
  showImportDialog.value = true
}

function closeImportDialog(): void {
  showImportDialog.value = false
  importMessage.value = ''
  importSuccess.value = false
}

function triggerFileInput(): void {
  fileInput.value?.click()
}

async function handleFileChange(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  isImporting.value = true
  importMessage.value = ''
  importSuccess.value = false

  try {
    const result = await importCSV(file)
    importSuccess.value = true
    importMessage.value = `导入成功！${JSON.stringify(result.result)}`
    target.value = ''
    void loadCashFlows()
  } catch (error) {
    importSuccess.value = false
    importMessage.value = error instanceof Error ? error.message : '导入失败'
  } finally {
    isImporting.value = false
  }
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
            <InputText v-model="state.start_date" type="date" />
          </label>
          <label class="field-stack">
            <span class="field-stack__label">结束日期</span>
            <InputText v-model="state.end_date" type="date" />
          </label>
          <label class="field-stack">
            <span class="field-stack__label">币种</span>
            <InputText v-model="state.currency" type="text" placeholder="USD / CNH / HKD" />
          </label>
          <div class="field-stack">
            <div class="cash-flow-direction__label-row">
              <span class="field-stack__label">方向</span>
              <span class="cash-flow-direction__helper">默认全部</span>
            </div>
            <div class="cash-flow-direction">
              <Button
                type="button"
                label="入金"
                class="cash-flow-direction__button"
                :class="{ 'is-active': state.flow_direction === 'deposit' }"
                @click="setDirection('deposit')"
              />
              <Button
                type="button"
                label="出金"
                class="cash-flow-direction__button"
                :class="{ 'is-active': state.flow_direction === 'withdrawal' }"
                @click="setDirection('withdrawal')"
              />
            </div>
          </div>
          <div class="field-stack field-stack--action">
            <Button label="刷新出入金" icon="pi pi-wallet" class="p-button p-button--accent" type="submit" />
            <Button label="导入CSV" icon="pi pi-upload" class="p-button p-button--ghost" @click="openImportDialog" />
          </div>
        </form>
      </div>
    </section>

    <div v-if="showImportDialog" class="import-dialog-backdrop" @click.self="closeImportDialog">
      <section class="surface-panel import-dialog">
        <div class="surface-panel__content import-dialog__content">
          <div class="import-dialog__header">
            <div>
              <p class="eyebrow">IMPORT</p>
              <h2 class="import-dialog__title">导入历史 CSV 文件</h2>
            </div>
            <Button
              icon="pi pi-times"
              class="p-button p-button--ghost"
              @click="closeImportDialog"
            />
          </div>
          <div class="import-dialog__body">
            <p class="import-dialog__desc">选择要导入的 Flex CSV 文件（包含历史数据）</p>
            <input
              ref="fileInput"
              type="file"
              accept=".csv"
              style="display: none"
              @change="handleFileChange"
            />
            <Button
              label="选择文件"
              icon="pi pi-folder-open"
              class="p-button p-button--accent"
              :loading="isImporting"
              @click="triggerFileInput"
            />
            <p v-if="importMessage" :class="['import-dialog__message', importSuccess ? 'is-success' : 'is-error']">
              {{ importMessage }}
            </p>
          </div>
        </div>
      </section>
    </div>

    <LoadingBlock v-if="loading" />
    <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

    <template v-else>
      <section class="stats-grid stats-grid--summary">
        <StatCard title="流水笔数" :value="String(cashFlowSummary?.record_count ?? 0)" icon="pi pi-list" tone="accent" />
        <StatCard title="入金笔数" :value="String(cashFlowSummary?.deposit_count ?? 0)" icon="pi pi-arrow-down-left" tone="positive" />
        <StatCard title="出金笔数" :value="String(cashFlowSummary?.withdrawal_count ?? 0)" icon="pi pi-arrow-up-right" tone="negative" />
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
            <Paginator
              :rows="state.page_size"
              :totalRecords="sortedCashFlows.length"
              :first="(state.page - 1) * state.page_size"
              :rowsPerPageOptions="[20, 50, 100]"
              @page="onPageChange"
            />
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

.cash-flow-direction {
  display: flex;
  gap: 10px;
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

.cash-flow-direction__button {
  min-width: 96px;
}

.cash-flow-direction__button.is-active {
  background: linear-gradient(135deg, rgba(60, 146, 255, 0.95), rgba(25, 92, 182, 0.95));
  border-color: rgba(116, 194, 255, 0.75);
  box-shadow: 0 0 0 1px rgba(116, 194, 255, 0.25) inset;
}

.import-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(7, 14, 29, 0.7);
  backdrop-filter: blur(10px);
}

.import-dialog {
  width: min(480px, 100%);
}

.import-dialog__content {
  display: grid;
  gap: 20px;
}

.import-dialog__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.import-dialog__title {
  margin: 0;
  font-size: 1.1rem;
}

.import-dialog__body {
  display: grid;
  gap: 16px;
}

.import-dialog__desc {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

.import-dialog__message {
  margin: 0;
  font-size: 0.95rem;
}

.import-dialog__message.is-success {
  color: var(--color-profit);
}

.import-dialog__message.is-error {
  color: var(--color-loss);
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
