import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

import PrimeVue from 'primevue/config'
import Lara from '@primevue/themes/lara'
import ToastService from 'primevue/toastservice'
import { useThemeStore } from '@/stores/theme'
import 'primeicons/primeicons.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import './style.css'
import '@/styles/themes.css'
import '@/styles/modal-animations.css'
import '@/components/admin/admin-page.css'
import '@/components/admin/admin-table.css'

const AUTH_BOOT_TIMEOUT_MS = 8000

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(PrimeVue, {
  theme: {
    preset: Lara,
    options: {
      darkModeSelector: '.dark',
    },
  },
})
app.use(ToastService)

async function bootstrap() {
  const authStore = useAuthStore()
  const themeStore = useThemeStore()
  authStore.bootstrapping = true

  try {
    await Promise.race([
      Promise.all([
        authStore.initialize(),
        themeStore.bootstrap(),
      ]),
      new Promise((resolve) => setTimeout(resolve, AUTH_BOOT_TIMEOUT_MS)),
    ])
  } finally {
    authStore.bootstrapping = false
    if (!authStore.initialized) {
      authStore.initialized = true
    }
  }

  app.use(router)

  const current = window.location.pathname
  const publicPaths = ['/', '/login', '/otp', '/verify']
  if (!authStore.isAuthenticated && !publicPaths.includes(current)) {
    await router.replace('/login')
  } else if (authStore.isAuthenticated && current === '/login') {
    const home = authStore.homeRoute
    if (home !== '/login') {
      await router.replace(home)
    }
  }

  app.mount('#app')
}

bootstrap()
