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

  // Restore tokens synchronously BEFORE router mounts — this is what keeps
  // users logged in across a normal page refresh.
  authStore.restoreCachedSession()

  try {
    await Promise.all([
      authStore.initialize(),
      themeStore.bootstrap().catch(() => {}),
    ])
  } catch (error) {
    console.warn('Auth bootstrap warning:', error)
  } finally {
    if (!authStore.initialized) {
      authStore.initialized = true
    }
  }

  app.use(router)

  const current = window.location.pathname
  const publicPaths = ['/', '/login', '/otp']
  if (authStore.isAuthenticated && current === '/login') {
    const home = authStore.homeRoute
    if (home !== '/login') {
      await router.replace(home)
    }
  } else if (!authStore.isAuthenticated && !publicPaths.includes(current)) {
    // restoreCachedSession already ran; only redirect if tokens are truly gone.
    if (!localStorage.getItem('access_token') && !localStorage.getItem('refresh_token')) {
      await router.replace('/login')
    }
  }

  app.mount('#app')
}

bootstrap()
