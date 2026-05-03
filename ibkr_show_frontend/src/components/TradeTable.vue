<script setup lang="ts">
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'

import type { TradeItem } from '@/types/trades'

defineProps<{
  items: TradeItem[]
  formatNumber: (value: number | null, digits?: number) => string
  sortKey: 'proceeds' | 'fifo_pnl_realized' | null
  sortOrder: 'asc' | 'desc'
  onSort: (key: 'proceeds' | 'fifo_pnl_realized') => void
}>()

function formatSide(value: string | null): string {
  if (value === 'BUY') {
    return '买入'
  }
  if (value === 'SELL') {
    return '卖出'
  }
  return value ?? '--'
}

function sideClass(value: string | null): string {
  if (value === 'BUY') {
    return 'p-tag--positive'
  }
  if (value === 'SELL') {
    return 'p-tag--negative'
  }
  return 'p-tag--accent'
}

function pnlClass(value: number | null): string {
  if (value === null || value === 0) {
    return 'table-pnl--neutral'
  }
  return value > 0 ? 'table-pnl--positive' : 'table-pnl--negative'
}

function sortLabel(key: 'proceeds' | 'fifo_pnl_realized'): string {
  return key === 'proceeds' ? '成交金额' : '已实现盈亏'
}

function sortIndicator(
  activeKey: 'proceeds' | 'fifo_pnl_realized' | null,
  activeOrder: 'asc' | 'desc',
  key: 'proceeds' | 'fifo_pnl_realized',
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
        <div class="empty-state">当前筛选条件下没有交易数据</div>
      </template>

      <Column header="成交时间" headerClass="table-head--left table-col--datetime" bodyClass="table-col--datetime">
        <template #body="{ data }">
          <div class="table-symbol">
            <span class="table-symbol__code">{{ data.date_time ?? '--' }}</span>
            <span class="table-symbol__desc">{{ data.trade_date ?? '--' }}</span>
          </div>
        </template>
      </Column>

      <Column header="代码" headerClass="table-head--left table-col--symbol" bodyClass="table-col--symbol">
        <template #body="{ data }">
          <div class="table-symbol">
            <span class="table-symbol__code">{{ data.symbol ?? '--' }}</span>
            <span class="table-symbol__desc">{{ data.description ?? '无名称' }}</span>
          </div>
        </template>
      </Column>

      <Column header="资产类型" headerClass="table-head--center table-col--asset" bodyClass="table-col--asset">
        <template #body="{ data }">
          <Tag :value="data.asset_class ?? '--'" class="p-tag p-tag--accent" />
        </template>
      </Column>

      <Column header="方向" headerClass="table-head--center table-col--side" bodyClass="table-col--side">
        <template #body="{ data }">
          <Tag :value="formatSide(data.buy_sell)" class="p-tag" :class="sideClass(data.buy_sell)" />
        </template>
      </Column>

      <Column header="数量" headerClass="table-head--number table-col--qty" bodyClass="table-number table-col--qty">
        <template #body="{ data }">
          <span class="cell-number">{{ formatNumber(data.quantity, 4) }}</span>
        </template>
      </Column>

      <Column header="成交价" headerClass="table-head--number table-col--price" bodyClass="table-number table-col--price">
        <template #body="{ data }">
          <span class="cell-number">{{ formatNumber(data.trade_price, 2) }}</span>
        </template>
      </Column>

      <Column headerClass="table-head--number table-col--value" bodyClass="table-number table-col--value">
        <template #header>
          <button type="button" class="sort-button" @click="onSort('proceeds')">
            <span>{{ sortLabel('proceeds') }}</span>
            <span class="sort-button__indicator">{{ sortIndicator(sortKey, sortOrder, 'proceeds') }}</span>
          </button>
        </template>
        <template #body="{ data }">
          <span class="cell-number">{{ formatNumber(data.proceeds, 2) }}</span>
        </template>
      </Column>

      <Column header="佣金" headerClass="table-head--number table-col--fee" bodyClass="table-number table-col--fee">
        <template #body="{ data }">
          <span class="cell-number" :class="pnlClass(data.ib_commission)">
            {{ formatNumber(data.ib_commission, 4) }}
          </span>
        </template>
      </Column>

      <Column headerClass="table-head--number table-col--pnl" bodyClass="table-number table-col--pnl">
        <template #header>
          <button type="button" class="sort-button" @click="onSort('fifo_pnl_realized')">
            <span>{{ sortLabel('fifo_pnl_realized') }}</span>
            <span class="sort-button__indicator">{{ sortIndicator(sortKey, sortOrder, 'fifo_pnl_realized') }}</span>
          </button>
        </template>
        <template #body="{ data }">
          <span class="cell-number" :class="pnlClass(data.fifo_pnl_realized)">
            {{ formatNumber(data.fifo_pnl_realized, 2) }}
          </span>
        </template>
      </Column>

      <Column header="交易所" headerClass="table-head--left table-col--exchange" bodyClass="table-col--exchange">
        <template #body="{ data }">
          <span class="terminal-muted">{{ data.exchange ?? '--' }}</span>
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

.sort-button__indicator {
  color: var(--color-accent-strong);
  font-size: 0.88rem;
}

.terminal-datatable :deep(.table-col--datetime) {
  width: 15%;
}

.terminal-datatable :deep(.table-col--symbol) {
  width: 12%;
}

.terminal-datatable :deep(.table-col--asset) {
  width: 7%;
}

.terminal-datatable :deep(.table-col--side) {
  width: 6%;
}

.terminal-datatable :deep(.table-col--qty) {
  width: 8%;
}

.terminal-datatable :deep(.table-col--price) {
  width: 8%;
}

.terminal-datatable :deep(.table-col--value) {
  width: 11%;
}

.terminal-datatable :deep(.table-col--fee) {
  width: 9%;
}

.terminal-datatable :deep(.table-col--pnl) {
  width: 10%;
}

.terminal-datatable :deep(.table-col--exchange) {
  width: 14%;
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
