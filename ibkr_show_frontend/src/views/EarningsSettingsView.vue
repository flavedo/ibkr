<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import ToggleSwitch from 'primevue/toggleswitch'

import { fetchPushSettings, sendTestEmail, triggerDailyPush, updatePushSettings } from '@/api/earningsSettings'
import type { EarningsPushSettings } from '@/api/earningsSettings'
import ErrorBlock from '@/components/ErrorBlock.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'

const settings = ref<EarningsPushSettings>({
  enabled: false,
  push_time: '09:00',
  smtp_server: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  sender_email: '',
  target_email: '',
})

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const triggering = ref(false)
const errorMessage = ref('')

const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
const showToastMessage = ref(false)

function showToast(msg: string, type: 'success' | 'error'): void {
  toastMessage.value = msg
  toastType.value = type
  showToastMessage.value = true
  setTimeout(() => {
    showToastMessage.value = false
  }, 4000)
}

async function loadSettings(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchPushSettings()
    settings.value = data
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载设置失败'
  } finally {
    loading.value = false
  }
}

async function handleSave(): Promise<void> {
  saving.value = true
  try {
    const result = await updatePushSettings(settings.value)
    settings.value = result
    showToast('设置已保存', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function handleTestSend(): Promise<void> {
  testing.value = true
  try {
    const result = await sendTestEmail(settings.value)
    if (result.success) {
      showToast(result.message, 'success')
    } else {
      showToast(result.message, 'error')
    }
  } catch (error) {
    showToast(error instanceof Error ? error.message : '测试发送失败', 'error')
  } finally {
    testing.value = false
  }
}

async function handleTriggerPush(): Promise<void> {
  triggering.value = true
  try {
    await handleSave()
    const result = await triggerDailyPush()
    if (result.success) {
      showToast(result.message, 'success')
    } else {
      showToast(result.message, 'error')
    }
  } catch (error) {
    showToast(error instanceof Error ? error.message : '推送触发失败', 'error')
  } finally {
    triggering.value = false
  }
}

onMounted(() => {
  void loadSettings()
})
</script>

<template>
  <section class="page-section">
    <div class="section-header">
      <div>
        <p class="eyebrow">Settings</p>
        <h1 class="page-hero__title">财报推送设置</h1>
        <p class="page-hero__subtitle">配置每日美股财报日历的邮件推送功能。</p>
      </div>
    </div>

    <LoadingBlock v-if="loading" />
    <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

    <template v-else>
      <Card class="surface-panel">
        <template #content>
          <div class="surface-panel__content">
            <div class="card-header">
              <div>
                <h2 class="panel-title">📬 每日财报推送</h2>
                <p class="panel-subtitle">每天定时获取美股财报日历数据并通过邮件推送。</p>
              </div>
              <div class="toggle-wrapper">
                <label class="toggle-label" :class="{ 'toggle-label--active': settings.enabled }">
                  {{ settings.enabled ? '已开启' : '已关闭' }}
                </label>
                <ToggleSwitch v-model="settings.enabled" />
              </div>
            </div>

            <div class="settings-grid">
              <div class="field-stack field-stack--full">
                <label class="field-stack__label">每日推送时间</label>
                <div class="time-picker-row">
                  <InputText
                    v-model="settings.push_time"
                    type="time"
                    class="settings-input time-input"
                  />
                  <span class="terminal-note">每天 {{ settings.push_time || '09:00' }} 自动发送财报推送</span>
                </div>
              </div>

              <div class="field-stack">
                <label class="field-stack__label">SMTP 服务器</label>
                <InputText
                  v-model="settings.smtp_server"
                  placeholder="smtp.gmail.com"
                  class="settings-input"
                />
              </div>

              <div class="field-stack">
                <label class="field-stack__label">SMTP 端口</label>
                <InputNumber
                  v-model="settings.smtp_port"
                  :min="1"
                  :max="65535"
                  class="settings-input"
                />
              </div>

              <div class="field-stack">
                <label class="field-stack__label">SMTP 用户名（邮箱地址）</label>
                <InputText
                  v-model="settings.smtp_username"
                  placeholder="user@gmail.com"
                  class="settings-input"
                />
              </div>

              <div class="field-stack">
                <label class="field-stack__label">SMTP 密钥 / App Password</label>
                <InputText
                  v-model="settings.smtp_password"
                  type="password"
                  placeholder="输入 SMTP 密码或应用专用密码"
                  class="settings-input"
                />
              </div>

              <div class="field-stack">
                <label class="field-stack__label">发件邮箱</label>
                <InputText
                  v-model="settings.sender_email"
                  placeholder="sender@gmail.com"
                  class="settings-input"
                />
              </div>

              <div class="field-stack">
                <label class="field-stack__label">目标邮箱（接收推送）</label>
                <InputText
                  v-model="settings.target_email"
                  placeholder="you@example.com"
                  class="settings-input"
                />
              </div>
            </div>

            <div class="settings-actions">
              <div class="settings-actions__left">
                <Button
                  label="保存设置"
                  icon="pi pi-check"
                  class="p-button"
                  :loading="saving"
                  @click="handleSave"
                />
                <Button
                  label="测试发送"
                  icon="pi pi-send"
                  class="p-button p-button--ghost"
                  :loading="testing"
                  @click="handleTestSend"
                />
                <Button
                  label="立即推送"
                  icon="pi pi-refresh"
                  class="p-button p-button--ghost"
                  :loading="triggering"
                  @click="handleTriggerPush"
                />
              </div>
              <div class="settings-actions__hint">
                <span class="terminal-note">SMTP 密钥建议使用邮箱的"应用专用密码"</span>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </template>

    <transition name="toast-fade">
      <div
        v-if="showToastMessage"
        class="settings-toast"
        :class="toastType === 'success' ? 'settings-toast--success' : 'settings-toast--error'"
      >
        {{ toastMessage }}
      </div>
    </transition>
  </section>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.toggle-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  transition: color 0.2s ease;
}

.toggle-label--active {
  color: var(--color-positive);
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.field-stack--full {
  grid-column: 1 / -1;
}

.time-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-input {
  width: 160px;
}

.settings-input {
  width: 100%;
}

.settings-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.settings-actions__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.settings-actions__hint {
  text-align: right;
}

.settings-toast {
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

.settings-toast--success {
  background: rgba(9, 47, 39, 0.95);
  border: 1px solid rgba(52, 210, 163, 0.4);
  color: var(--color-positive);
}

.settings-toast--error {
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

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .time-picker-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-header {
    flex-direction: column;
  }

  .settings-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .settings-actions__left {
    flex-direction: column;
  }

  .settings-actions__hint {
    text-align: left;
  }
}
</style>
