import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

import PrimeVue from 'primevue/config'
import Lara from '@primevue/themes/lara'
import ToastService from 'primevue/toastservice'
import 'primeicons/primeicons.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import './style.css'

const AUTH_BOOT_TIMEOUT_MS = 4000

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
  authStore.bootstrapping = true

  try {
    await Promise.race([
      authStore.initialize(),
      new Promise((_, reject) => {
        setTimeout(() => reject(new Error('auth_boot_timeout')), AUTH_BOOT_TIMEOUT_MS)
      }),
    ])
  } catch {
    authStore.clearLocalStorage()
    authStore.initialized = true
  } finally {
    authStore.bootstrapping = false
  }

  app.use(router)

  // Default entry: login when not signed in
  const current = window.location.pathname
  const publicPaths = ['/', '/login', '/otp', '/verify']
  if (!authStore.isAuthenticated && !publicPaths.includes(current)) {
    await router.replace('/login')
  } else if (authStore.isAuthenticated && (current === '/login')) {
    await router.replace(authStore.isStudent ? '/student' : '/dashboard')
  }

  app.mount('#app')
}

bootstrap()
