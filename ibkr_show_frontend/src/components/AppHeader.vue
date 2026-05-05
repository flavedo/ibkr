<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'

import { fetchAccountOverview } from '@/api/account'
import { clearData, importCSV, triggerDataRefresh } from '@/api/data'
import type { AccountOverview } from '@/types/account'

const route = useRoute()
const router = useRouter()
const overview = ref<AccountOverview | null>(null)
const isRefreshing = ref(false)
const isImporting = ref(false)
const isClearing = ref(false)
let refreshTimer: number | null = null
const fileInputRef = ref<HTMLInputElement | null>(null)

const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
let toastTimer: number | null = null

function showToast(message: string, type: 'success' | 'error' = 'success'): void {
  toastMessage.value = message
  toastType.value = type
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
  }
  toastTimer = window.setTimeout(() => {
    toastMessage.value = ''
  }, 4000)
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  try {
    await triggerDataRefresh()
    await loadOverview()
    showToast('数据已刷新', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '刷新失败', 'error')
  } finally {
    isRefreshing.value = false
  }
}

async function handleClear(): Promise<void> {
  if (!confirm('确定要清除所有交易和分红数据吗？此操作不可恢复。')) {
    return
  }
  isClearing.value = true
  try {
    const result = await clearData()
    showToast(`已清除 cash_flows: ${result.deleted?.cash_flows ?? 0}, trades: ${result.deleted?.trades ?? 0}`, 'success')
    await loadOverview()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '清除失败', 'error')
  } finally {
    isClearing.value = false
  }
}

function handleImportClick(): void {
  fileInputRef.value?.click()
}

async function handleFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const fileList = input.files
  if (!fileList || fileList.length === 0) return
  isImporting.value = true
  const fileCount = fileList.length
  try {
    const result = await importCSV(Array.from(fileList))
    const successCount = Object.keys(result.results ?? {}).length
    const errorCount = Object.keys(result.errors ?? {}).length
    let msg = `成功导入 ${successCount}/${fileCount} 个文件`
    if (errorCount > 0) {
      msg += `，${errorCount} 个文件失败`
    }
    await loadOverview()
    showToast(msg, errorCount > 0 && successCount === 0 ? 'error' : 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '导入失败', 'error')
  } finally {
    isImporting.value = false
    input.value = ''
  }
}

const navItems = [
  { label: '财经', icon: 'pi pi-calendar', to: '/financial-calendar' },
  { label: '总览', icon: 'pi pi-chart-line', to: '/dashboard' },
  { label: '持仓', icon: 'pi pi-briefcase', to: '/positions' },
  { label: '交易', icon: 'pi pi-list', to: '/trades' },
  { label: '分红', icon: 'pi pi-dollar', to: '/dividends' },
  { label: '出入金', icon: 'pi pi-wallet', to: '/cash-flows' },
  { label: '设置', icon: 'pi pi-cog', to: '/earnings-settings' },
]

function isActive(path: string): boolean {
  return route.path === path
}

function navigate(path: string): void {
  void router.push(path)
}

function formatNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return '--'
  }
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

async function loadOverview(): Promise<void> {
  try {
    overview.value = await fetchAccountOverview()
  } catch {
    overview.value = null
  }
}

onMounted(() => {
  void loadOverview()
  refreshTimer = window.setInterval(() => {
    void loadOverview()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
  }
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer)
  }
})
</script>

<template>
  <header class="app-header surface-panel">
    <div class="surface-panel__content app-header__content">
      <div class="app-header__row">
        <nav class="app-header__nav">
          <Button
            v-for="item in navItems"
            :key="item.to"
            :label="item.label"
            :icon="item.icon"
            class="nav-button"
            :class="{ 'is-active': isActive(item.to) }"
            @click="navigate(item.to)"
          />
        </nav>

        <div class="app-header__right">
          <div class="app-header__metrics">
            <span class="app-header__metric">
              <span class="terminal-note">报告日期</span>
              <strong>{{ overview?.report_date ?? '--' }}</strong>
            </span>
            <span class="app-header__metric">
              <span class="terminal-note">总权益</span>
              <strong>{{ formatNumber(overview?.total_equity ?? null) }}</strong>
            </span>
            <span class="app-header__metric">
              <span class="terminal-note">总盈亏</span>
              <strong
                :class="
                  overview?.fifo_total_pnl !== null &&
                  overview?.fifo_total_pnl !== undefined &&
                  overview.fifo_total_pnl < 0
                    ? 'metric-negative'
                    : 'metric-positive'
                "
              >
                {{ formatNumber(overview?.fifo_total_pnl ?? null) }}
              </strong>
            </span>
          </div>

          <div class="app-header__actions">
            <Button
              icon="pi pi-refresh"
              class="p-button p-button--ghost action-button"
              :loading="isRefreshing"
              @click="handleRefresh"
            />
            <Button
              icon="pi pi-upload"
              class="p-button p-button--ghost action-button"
              :loading="isImporting"
              @click="handleImportClick"
            />
            <Button
              icon="pi pi-trash"
              class="p-button p-button--ghost action-button"
              :loading="isClearing"
              @click="handleClear"
            />
            <input
              ref="fileInputRef"
              type="file"
              accept=".csv"
              multiple
              style="display: none"
              @change="handleFileChange"
            />
          </div>
        </div>
      </div>
    </div>

    <transition name="toast-fade">
      <div v-if="toastMessage" class="app-header__toast" :class="`app-header__toast--${toastType}`">
        {{ toastMessage }}
      </div>
    </transition>
  </header>
</template>

<style scoped>
.app-header__content {
  display: grid;
  gap: var(--space-3);
}

.app-header__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.app-header__nav {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.nav-button {
  min-width: 80px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  font-size: 0.9rem;
}

.nav-button.is-active {
  border-color: rgba(86, 213, 255, 0.3);
  background: linear-gradient(180deg, rgba(32, 79, 129, 0.94), rgba(16, 45, 81, 0.96));
  box-shadow: 0 0 20px rgba(62, 169, 255, 0.12);
}

.nav-button :deep(.p-button-icon) {
  font-size: 1rem;
}

.nav-button :deep(.p-button-label) {
  font-size: 0.9rem;
}

.app-header__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.app-header__metrics {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-header__metric {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0.25rem 0.6rem;
  border: 1px solid rgba(74, 196, 255, 0.14);
  border-radius: 10px;
  background: rgba(10, 21, 44, 0.18);
  white-space: nowrap;
}

.app-header__metric strong {
  font-size: 0.9rem;
}

.app-header__metric .terminal-note {
  font-size: 0.75rem;
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-button {
  min-width: 38px;
  min-height: 36px;
  padding: 0 10px;
  border-radius: 10px;
}

.action-button :deep(.p-button-icon) {
  font-size: 1rem;
}

.app-header__toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
  pointer-events: none;
}

.app-header__toast--success {
  background: rgba(9, 47, 39, 0.95);
  border: 1px solid rgba(52, 210, 163, 0.4);
  color: var(--color-positive);
}

.app-header__toast--error {
  background: rgba(55, 18, 28, 0.95);
  border: 1px solid rgba(255, 107, 125, 0.4);
  color: var(--color-negative);
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}

@media (max-width: 1200px) {
  .app-header__row {
    flex-direction: column;
    align-items: stretch;
  }

  .app-header__right {
    justify-content: space-between;
  }

  .app-header__nav {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .app-header__right {
    flex-direction: column;
    align-items: stretch;
  }

  .app-header__metrics {
    justify-content: center;
  }

  .app-header__actions {
    justify-content: center;
  }
}
</style>
