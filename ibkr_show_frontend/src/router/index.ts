import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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

export default router
