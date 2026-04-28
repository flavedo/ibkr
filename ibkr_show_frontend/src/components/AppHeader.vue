<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'

import { useAuthSession } from '@/auth/session'
import { fetchAccountOverview } from '@/api/account'
import { clearData, importCSV, triggerDataRefresh } from '@/api/data'
import type { AccountOverview } from '@/types/account'

const route = useRoute()
const router = useRouter()
const { authState, ensureAuthSession, loginWithCredentials, logoutCurrentSession } = useAuthSession()
const overview = ref<AccountOverview | null>(null)
const showLoginDialog = ref(false)
const loginError = ref('')
const loginForm = reactive({
  username: '',
  password: '',
})
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
  const file = input.files?.[0]
  if (!file) return
  isImporting.value = true
  try {
    await importCSV(file)
    await loadOverview()
    showToast('CSV 导入成功', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '导入失败', 'error')
  } finally {
    isImporting.value = false
    input.value = ''
  }
}

const navItems = [
  { label: '总览', icon: 'pi pi-chart-line', to: '/' },
  { label: '持仓', icon: 'pi pi-briefcase', to: '/positions' },
  { label: '交易', icon: 'pi pi-list', to: '/trades' },
  { label: '分红', icon: 'pi pi-dollar', to: '/dividends' },
  { label: '出入金', icon: 'pi pi-wallet', to: '/cash-flows' },
]

const visibleNavItems = computed(() =>
  authState.authenticated ? navItems : navItems.filter((item) => item.to === '/' || item.to === '/positions'),
)

function isActive(path: string): boolean {
  return route.path === path
}

function isProtectedPath(path: string): boolean {
  return path === '/trades' || path === '/dividends' || path === '/cash-flows'
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

function openLoginDialog(): void {
  loginError.value = ''
  loginForm.username = authState.username ?? ''
  loginForm.password = ''
  showLoginDialog.value = true
}

function closeLoginDialog(): void {
  showLoginDialog.value = false
  loginError.value = ''
  loginForm.password = ''
}

async function submitLogin(): Promise<void> {
  loginError.value = ''

  try {
    await loginWithCredentials(loginForm.username.trim(), loginForm.password)
    closeLoginDialog()
    showToast('登录成功', 'success')
  } catch (error) {
    loginError.value = error instanceof Error ? error.message : '登录失败'
  }
}

async function handleLogout(): Promise<void> {
  await logoutCurrentSession()
  if (isProtectedPath(route.path)) {
    await router.push('/')
  }
  showToast('已退出登录', 'success')
}

onMounted(() => {
  void ensureAuthSession()
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
            v-for="item in visibleNavItems"
            :key="item.to"
            :label="item.label"
            :icon="item.icon"
            class="nav-button"
            :class="{ 'is-active': isActive(item.to) }"
            @click="navigate(item.to)"
          />
        </nav>

        <div class="app-header__right">
          <Tag class="p-tag p-tag--accent app-header__live-tag" value="LIVE API"></Tag>

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
              style="display: none"
              @change="handleFileChange"
            />
            <Button
              v-if="!authState.authenticated"
              icon="pi pi-sign-in"
              class="p-button p-button--ghost action-button"
              @click="openLoginDialog"
            />
            <Button
              v-else
              icon="pi pi-sign-out"
              class="p-button p-button--ghost action-button"
              @click="handleLogout"
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

  <div v-if="showLoginDialog" class="auth-dialog-backdrop" @click.self="closeLoginDialog">
    <section class="surface-panel auth-dialog">
      <div class="surface-panel__content auth-dialog__content">
        <div class="auth-dialog__header">
          <div>
            <p class="eyebrow">ACCESS</p>
            <h2 class="auth-dialog__title">登录后可查看交易和出入金模块</h2>
          </div>
          <Button
            icon="pi pi-times"
            class="p-button p-button--ghost auth-dialog__close"
            aria-label="关闭登录弹窗"
            @click="closeLoginDialog"
          />
        </div>

        <form class="auth-dialog__form" @submit.prevent="submitLogin">
          <label class="field-stack">
            <span class="field-stack__label">用户名</span>
            <InputText v-model="loginForm.username" type="text" autocomplete="username" />
          </label>
          <label class="field-stack">
            <span class="field-stack__label">密码</span>
            <InputText v-model="loginForm.password" type="password" autocomplete="current-password" />
          </label>
          <p v-if="loginError" class="auth-dialog__error">{{ loginError }}</p>
          <div class="auth-dialog__actions">
            <Button label="取消" type="button" class="p-button p-button--ghost" @click="closeLoginDialog" />
            <Button
              label="登录"
              icon="pi pi-sign-in"
              type="submit"
              class="p-button p-button--accent"
              :loading="authState.loading"
            />
          </div>
        </form>
      </div>
    </section>
  </div>
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

.app-header__live-tag {
  font-size: 0.7rem;
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

.auth-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(7, 14, 29, 0.7);
  backdrop-filter: blur(10px);
}

.auth-dialog {
  width: min(460px, 100%);
}

.auth-dialog__content {
  display: grid;
  gap: 20px;
  max-width: 100%;
  box-sizing: border-box;
}

.auth-dialog__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.auth-dialog__title {
  margin: 0;
  font-size: 1.1rem;
}

.auth-dialog__close {
  min-width: 44px;
  min-height: 44px;
}

.auth-dialog__form {
  display: grid;
  gap: 16px;
  max-width: 100%;
  overflow: hidden;
}

.auth-dialog__form :deep(.p-inputtext) {
  width: 100%;
  font-size: 1rem;
}

.auth-dialog__error {
  margin: 0;
  color: var(--color-loss);
}

.auth-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.auth-dialog__actions :deep(.p-button) {
  min-width: auto;
  min-height: 38px;
  padding: 0.6rem 1rem;
  font-size: 0.95rem;
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
