<script setup lang="ts">
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'

import type { CashFlowItem } from '@/types/cashFlows'

defineProps<{
  items: CashFlowItem[]
  formatNumber: (value: number | null, digits?: number) => string
  sortKey: 'date_time' | 'amount' | null
  sortOrder: 'asc' | 'desc'
  onSort: (key: 'date_time' | 'amount') => void
}>()

function directionLabel(value: string | null): string {
  if (value === 'deposit') {
    return '入金'
  }
  if (value === 'withdrawal') {
    return '出金'
  }
  return value ?? '--'
}

function directionClass(value: string | null): string {
  if (value === 'deposit') {
    return 'p-tag--positive'
  }
  if (value === 'withdrawal') {
    return 'p-tag--negative'
  }
  return 'p-tag--accent'
}

function amountClass(value: number | null): string {
  if (value === null || value === 0) {
    return 'table-pnl--neutral'
  }
  return value > 0 ? 'table-pnl--positive' : 'table-pnl--negative'
}

function sortLabel(key: 'date_time' | 'amount'): string {
  return key === 'date_time' ? '发生时间' : '金额'
}

function sortIndicator(
  activeKey: 'date_time' | 'amount' | null,
  activeOrder: 'asc' | 'desc',
  key: 'date_time' | 'amount',
): string {
  if (activeKey !== key) {
    return '↕'
  }
  return activeOrder === 'desc' ? '↓' : '↑'
}
</script>

<template>
  <div class="table-shell">
    <DataTable :value="items" class="terminal-datatable">
      <template #empty>
        <div class="empty-state">当前筛选条件下没有出入金记录</div>
      </template>

      <Column headerClass="table-head--left table-col--datetime" bodyClass="table-col--datetime">
        <template #header>
          <button type="button" class="sort-button sort-button--left" @click="onSort('date_time')">
            <span>{{ sortLabel('date_time') }}</span>
            <span class="sort-button__indicator">{{ sortIndicator(sortKey, sortOrder, 'date_time') }}</span>
          </button>
        </template>
        <template #body="{ data }">
          <div class="table-symbol">
            <span class="table-symbol__code">{{ data.date_time ?? '--' }}</span>
            <span class="table-symbol__desc">{{ data.report_date ?? data.settle_date ?? '--' }}</span>
          </div>
        </template>
      </Column>

      <Column header="币种" headerClass="table-head--center table-col--asset" bodyClass="table-col--asset">
        <template #body="{ data }">
          <Tag :value="data.currency ?? '--'" class="p-tag p-tag--accent" />
        </template>
      </Column>

      <Column header="方向" headerClass="table-head--center table-col--side" bodyClass="table-col--side">
        <template #body="{ data }">
          <Tag :value="directionLabel(data.flow_direction)" class="p-tag" :class="directionClass(data.flow_direction)" />
        </template>
      </Column>

      <Column headerClass="table-head--number table-col--value" bodyClass="table-number table-col--value">
        <template #header>
          <button type="button" class="sort-button" @click="onSort('amount')">
            <span>{{ sortLabel('amount') }}</span>
            <span class="sort-button__indicator">{{ sortIndicator(sortKey, sortOrder, 'amount') }}</span>
          </button>
        </template>
        <template #body="{ data }">
          <span class="cell-number" :class="amountClass(data.amount)">{{ formatNumber(data.amount, 2) }}</span>
        </template>
      </Column>

      <Column header="结算日" headerClass="table-head--left table-col--price" bodyClass="table-col--price">
        <template #body="{ data }">
          <span class="terminal-muted">{{ data.settle_date ?? '--' }}</span>
        </template>
      </Column>

      <Column header="说明" headerClass="table-head--left table-col--symbol" bodyClass="table-col--symbol">
        <template #body="{ data }">
          <div class="table-symbol">
            <span class="table-symbol__code">{{ data.description ?? '--' }}</span>
            <span class="table-symbol__desc">{{ data.client_reference ?? data.flow_type ?? '--' }}</span>
          </div>
        </template>
      </Column>

      <Column header="流水号" headerClass="table-head--left table-col--exchange" bodyClass="table-col--exchange">
        <template #body="{ data }">
          <span class="terminal-muted">{{ data.transaction_id ?? '--' }}</span>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.sort-button {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.38rem;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.sort-button--left {
  justify-content: flex-start;
}

.sort-button__indicator {
  color: var(--color-accent-strong);
  font-size: 0.88rem;
}

.terminal-datatable :deep(.table-col--datetime) {
  width: 16%;
}

.terminal-datatable :deep(.table-col--asset) {
  width: 8%;
}

.terminal-datatable :deep(.table-col--side) {
  width: 9%;
}

.terminal-datatable :deep(.table-col--value) {
  width: 14%;
}

.terminal-datatable :deep(.table-col--price) {
  width: 12%;
}

.terminal-datatable :deep(.table-col--symbol) {
  width: 25%;
}

.terminal-datatable :deep(.table-col--exchange) {
  width: 16%;
}

.terminal-datatable :deep(.table-symbol__desc) {
  white-space: nowrap;
}

.terminal-datatable :deep(.p-datatable-thead > tr > th) {
  padding: 13px 10px;
  font-size: 0.84rem;
  letter-spacing: 0.02em;
  border-bottom: 2px solid rgba(86, 213, 255, 0.15);
  white-space: nowrap;
}

.terminal-datatable :deep(.p-datatable-tbody > tr > td) {
  padding: 14px 10px;
  font-size: 0.88rem;
  vertical-align: middle;
  border-bottom: 1px solid rgba(129, 160, 207, 0.06);
}

.terminal-datatable :deep(.p-datatable-tbody > tr) {
  transition: all 200ms ease;

  &:hover > td {
    background: rgba(86, 213, 255, 0.04);
  }
}

.table-shell {
  border-radius: 16px;
  overflow: hidden;
}
</style>
