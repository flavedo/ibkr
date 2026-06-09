import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/',
      redirect: '/financial-calendar',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/positions',
      name: 'positions',
      component: () => import('@/views/PositionsView.vue'),
    },
    {
      path: '/trades',
      name: 'trades',
      component: () => import('@/views/TradesView.vue'),
    },
    {
      path: '/dividends',
      name: 'dividends',
      component: () => import('@/views/DividendView.vue'),
    },
    {
      path: '/financial-calendar',
      name: 'financial-calendar',
      component: () => import('@/views/FinancialCalendarView.vue'),
    },
    {
      path: '/cash-flows',
      name: 'cash-flows',
      component: () => import('@/views/CashFlowsView.vue'),
    },
    {
      path: '/earnings-settings',
      name: 'earnings-settings',
      component: () => import('@/views/EarningsSettingsView.vue'),
    },
  ],
})

const publicPaths = ['/login']

function isTokenExpired(token: string): boolean {
  try {
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload))
    return decoded.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('auth_token')
  if (publicPaths.includes(to.path)) {
    next()
  } else if (!token || isTokenExpired(token)) {
    localStorage.removeItem('auth_token')
    next('/login')
  } else {
    next()
  }
})

export default router
