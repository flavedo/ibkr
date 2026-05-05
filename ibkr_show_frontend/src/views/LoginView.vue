<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card__header">
        <div class="login-card__logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="#56d5ff"/>
            <path d="M2 17l10 5 10-5" stroke="#56d5ff"/>
            <path d="M2 12l10 5 10-5" stroke="#56d5ff"/>
          </svg>
        </div>
        <h1 class="login-card__title">IBKR Show</h1>
        <p class="login-card__subtitle">请输入密码以继续</p>
      </div>

      <form class="login-card__form" @submit.prevent="handleLogin">
        <div class="login-card__field">
          <input
            v-model="password"
            type="password"
            class="login-card__input"
            placeholder="请输入密码"
            :disabled="loading"
            autocomplete="current-password"
            ref="passwordInput"
          />
        </div>

        <div v-if="errorMessage" class="login-card__error">
          {{ errorMessage }}
        </div>

        <button
          type="submit"
          class="login-card__button"
          :disabled="loading || !password"
        >
          <span v-if="loading" class="login-card__spinner"></span>
          <span v-else>进入系统</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'

const router = useRouter()
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const passwordInput = ref<HTMLInputElement | null>(null)

onMounted(() => {
  passwordInput.value?.focus()
})

async function handleLogin(): Promise<void> {
  if (!password.value || loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await login(password.value)
    localStorage.setItem('auth_token', res.token)
    router.push('/')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(25, 50, 80, 0.82), rgba(16, 34, 57, 0.9)),
    var(--color-bg-panel);
  border: 1px solid var(--color-border);
  box-shadow: var(--color-surface-glow);
}

.login-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(86, 213, 255, 0.07), transparent 35%, transparent 65%, rgba(255, 189, 122, 0.06));
  pointer-events: none;
}

.login-card__header {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 48px 32px 24px;
}

.login-card__logo {
  margin-bottom: 16px;
}

.login-card__title {
  margin: 0 0 8px;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #e8edf5, #94b8d9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-card__subtitle {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.92rem;
}

.login-card__form {
  position: relative;
  z-index: 1;
  padding: 0 32px 48px;
}

.login-card__field {
  margin-bottom: 16px;
}

.login-card__input {
  width: 100%;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid rgba(129, 160, 207, 0.2);
  background: rgba(14, 24, 41, 0.8);
  color: var(--color-text-primary);
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.login-card__input:focus {
  border-color: var(--color-accent-strong);
}

.login-card__input::placeholder {
  color: rgba(148, 184, 217, 0.35);
}

.login-card__input:disabled {
  opacity: 0.6;
}

.login-card__error {
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(63, 19, 30, 0.5);
  border: 1px solid rgba(255, 107, 125, 0.22);
  color: #ffd4da;
  font-size: 0.88rem;
}

.login-card__button {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(86, 213, 255, 0.2), rgba(86, 213, 255, 0.08));
  color: var(--color-accent-strong);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card__button:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(86, 213, 255, 0.3), rgba(86, 213, 255, 0.12));
}

.login-card__button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.login-card__spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(86, 213, 255, 0.3);
  border-top-color: var(--color-accent-strong);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
