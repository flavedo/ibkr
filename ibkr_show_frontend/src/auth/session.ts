import { reactive, readonly } from 'vue'

import { fetchAuthSession, login, logout } from '@/api/auth'

type AuthState = {
  initialized: boolean
  loading: boolean
  authenticated: boolean
  username: string | null
}

const authState = reactive<AuthState>({
  initialized: false,
  loading: false,
  authenticated: false,
  username: null,
})

let pendingSessionRequest: Promise<void> | null = null

function applyAuthState(authenticated: boolean, username: string | null): void {
  authState.authenticated = authenticated
  authState.username = authenticated ? username : null
  authState.initialized = true
}

export async function ensureAuthSession(force = false): Promise<void> {
  if (authState.initialized && !force) {
    return
  }
  if (pendingSessionRequest && !force) {
    return pendingSessionRequest
  }

  pendingSessionRequest = (async () => {
    authState.loading = true
    try {
      const session = await fetchAuthSession()
      applyAuthState(session.authenticated, session.username)
    } catch {
      applyAuthState(false, null)
    } finally {
      authState.loading = false
      pendingSessionRequest = null
    }
  })()

  return pendingSessionRequest
}

export async function loginWithCredentials(username: string, password: string): Promise<void> {
  authState.loading = true
  try {
    const session = await login({ username, password })
    applyAuthState(session.authenticated, session.username)
  } finally {
    authState.loading = false
  }
}

export async function logoutCurrentSession(): Promise<void> {
  authState.loading = true
  try {
    await logout()
    applyAuthState(false, null)
  } finally {
    authState.loading = false
  }
}

export function useAuthSession() {
  return {
    authState: readonly(authState),
    ensureAuthSession,
    loginWithCredentials,
    logoutCurrentSession,
  }
}
