import { createApp } from 'vue'
import PrimeVue from 'primevue/config'

import App from './App.vue'
import router from './router'
import 'primeicons/primeicons.css'
import './styles/theme.css'
import './styles/base.css'
import './styles/primevue-overrides.css'
import './style.css'

createApp(App)
  .use(router)
  .use(PrimeVue, {
    ripple: true,
    unstyled: true,
  })
  .mount('#app')
