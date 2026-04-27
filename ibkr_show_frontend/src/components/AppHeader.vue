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
const refreshError = ref('')
const isClearing = ref(false)
const clearMessage = ref('')
let refreshTimer: number | null = null
const fileInputRef = ref<HTMLInputElement | null>(null)

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  refreshError.value = ''
  try {
    await triggerDataRefresh()
    await loadOverview()
  } catch (error) {
    refreshError.value = error instanceof Error ? error.message : '刷新失败'
  } finally {
    isRefreshing.value = false
  }
}

async function handleClear(): Promise<void> {
  if (!confirm('确定要清除所有交易和分红数据吗？此操作不可恢复。')) {
    return
  }
  isClearing.value = true
  clearMessage.value = ''
  try {
    const result = await clearData()
    clearMessage.value = `已清除 cash_flows: ${result.deleted?.cash_flows ?? 0}, trades: ${result.deleted?.trades ?? 0}`
    await loadOverview()
  } catch (error) {
    clearMessage.value = error instanceof Error ? error.message : '清除失败'
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
  isRefreshing.value = true
  refreshError.value = ''
  try {
    await importCSV(file)
    await loadOverview()
  } catch (error) {
    refreshError.value = error instanceof Error ? error.message : '导入失败'
  } finally {
    isRefreshing.value = false
    input.value = ''
  }
}

const baseNavItems = [
  { label: '总览', icon: 'pi pi-chart-line', to: '/' },
  { label: '持仓', icon: 'pi pi-briefcase', to: '/positions' },
]

const protectedNavItems = [
  { label: '交易', icon: 'pi pi-list', to: '/trades' },
  { label: '分红', icon: 'pi pi-dollar', to: '/dividends' },
  { label: '出入金', icon: 'pi pi-wallet', to: '/cash-flows' },
]

const navItems = computed(() =>
  authState.authenticated ? [...baseNavItems, ...protectedNavItems] : baseNavItems,
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
  } catch (error) {
    loginError.value = error instanceof Error ? error.message : '登录失败'
  }
}

async function handleLogout(): Promise<void> {
  await logoutCurrentSession()
  if (isProtectedPath(route.path)) {
    await router.push('/')
  }
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
})
</script>

<template>
  <header class="app-header surface-panel">
    <div class="surface-panel__content app-header__content">
      <div class="app-header__brand">
        <div>
          <p class="eyebrow">IBKR SHOW</p>
          <h1 class="app-header__title">IBKR 账户可视化分析</h1>
        </div>
        <div class="app-header__status">
          <div class="app-header__status-row">
            <Tag class="p-tag p-tag--accent" value="LIVE API"></Tag>
            <Button
              label="刷新数据"
              icon="pi pi-refresh"
              class="p-button p-button--ghost app-header__auth-button"
              :loading="isRefreshing"
              @click="handleRefresh"
            />
            <Button
              label="导入CSV"
              icon="pi pi-upload"
              class="p-button p-button--ghost app-header__auth-button"
              @click="handleImportClick"
            />
            <Button
              label="清除数据"
              icon="pi pi-trash"
              class="p-button p-button--ghost app-header__auth-button"
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
              label="登录"
              icon="pi pi-sign-in"
              class="p-button p-button--ghost app-header__auth-button"
              @click="openLoginDialog"
            />
            <div v-else class="app-header__auth-session">
              <span class="terminal-note">已登录：{{ authState.username }}</span>
              <Button
                label="退出"
                icon="pi pi-sign-out"
                class="p-button p-button--ghost app-header__auth-button"
                @click="handleLogout"
              />
            </div>
          </div>
          <p v-if="refreshError" class="refresh-error">{{ refreshError }}</p>
          <p v-if="clearMessage" class="refresh-error">{{ clearMessage }}</p>
          <div class="app-header__metrics">
            <div class="app-header__metric">
              <span class="terminal-note">报告日期</span>
              <strong>{{ overview?.report_date ?? '--' }}</strong>
            </div>
            <div class="app-header__metric">
              <span class="terminal-note">总权益</span>
              <strong>{{ formatNumber(overview?.total_equity ?? null) }}</strong>
            </div>
            <div class="app-header__metric">
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
            </div>
          </div>
        </div>
      </div>

      <nav class="app-header__nav">
        <Button
          v-for="item in navItems"
          :key="item.to"
          :label="item.label"
          :icon="item.icon"
          class="terminal-nav__button"
          :class="{ 'is-active': isActive(item.to) }"
          @click="navigate(item.to)"
        />
      </nav>
    </div>
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
  gap: var(--space-4);
}

.app-header__brand {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  align-items: flex-end;
}

.app-header__title {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3rem);
  letter-spacing: -0.04em;
}

.app-header__status {
  display: grid;
  gap: 14px;
  justify-items: end;
}

.app-header__status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.app-header__auth-session {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-header__auth-button {
  min-width: 92px;
}

.app-header__nav {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

.app-header__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  justify-content: flex-end;
}

.app-header__metric {
  display: grid;
  gap: 4px;
  min-width: 116px;
  padding: 0.3rem 0.7rem;
  border: 1px solid rgba(74, 196, 255, 0.16);
  border-radius: 14px;
  background: rgba(10, 21, 44, 0.22);
}

.app-header__metric strong {
  font-size: 1.05rem;
}

.terminal-nav__button {
  min-width: 240px;
  min-height: 64px;
  padding: 0 28px;
  border-radius: 14px;
  font-size: 1.4rem;
}

:deep(.terminal-nav__button .p-button-label) {
  font-size: 1.55rem;
  font-weight: 700;
}

:deep(.terminal-nav__button .p-button-icon) {
  font-size: 1.45rem;
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

.refresh-error {
  margin: 0;
  color: var(--color-loss);
  font-size: 0.875rem;
  max-width: 300px;
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

@media (max-width: 768px) {
  .app-header__brand {
    flex-direction: column;
    align-items: stretch;
  }

  .app-header__status {
    justify-items: stretch;
  }

  .app-header__status-row {
    justify-content: flex-start;
  }

  .terminal-nav__button {
    min-width: calc(50% - 9px);
    min-height: 58px;
    padding: 0 18px;
  }

  :deep(.terminal-nav__button .p-button-label) {
    font-size: 1.25rem;
  }

  .app-header__metrics {
    justify-content: flex-start;
  }
}
</style>
