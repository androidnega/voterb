import { onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const LAST_ACTIVITY_KEY = 'session_last_activity'
const DEFAULT_TIMEOUT_MINUTES = 20
const ACTIVITY_EVENTS = ['mousedown', 'keydown', 'touchstart', 'scroll', 'click']

export function useSessionTimeout() {
  const authStore = useAuthStore()
  const router = useRouter()
  let timer = null
  let bound = false

  const timeoutMs = () => {
    const minutes = Number(authStore.sessionTimeoutMinutes) || DEFAULT_TIMEOUT_MINUTES
    return Math.max(1, minutes) * 60 * 1000
  }

  const expireSession = async () => {
    if (!authStore.isAuthenticated) return
    await authStore.logout()
    if (router.currentRoute.value.path !== '/login') {
      await router.replace('/login')
    }
  }

  const scheduleLogout = () => {
    if (timer) clearTimeout(timer)
    if (!authStore.isAuthenticated) return

    const last = Number(localStorage.getItem(LAST_ACTIVITY_KEY) || Date.now())
    const remaining = timeoutMs() - (Date.now() - last)
    if (remaining <= 0) {
      void expireSession()
      return
    }
    timer = setTimeout(expireSession, remaining)
  }

  const markActivity = () => {
    if (!authStore.isAuthenticated) return
    localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()))
    scheduleLogout()
  }

  const checkStoredIdle = () => {
    if (!authStore.isAuthenticated) return
    // Never expire during bootstrap / before hydration finishes.
    if (authStore.bootstrapping || !authStore.initialized) {
      markActivity()
      return
    }
    const last = Number(localStorage.getItem(LAST_ACTIVITY_KEY) || 0)
    if (!last) {
      markActivity()
      return
    }
    if (Date.now() - last >= timeoutMs()) {
      void expireSession()
      return
    }
    scheduleLogout()
  }

  const onVisibility = () => {
    if (document.visibilityState === 'visible') {
      checkStoredIdle()
    }
  }

  const bind = () => {
    if (bound) return
    ACTIVITY_EVENTS.forEach((eventName) => {
      window.addEventListener(eventName, markActivity, { passive: true })
    })
    document.addEventListener('visibilitychange', onVisibility)
    bound = true
  }

  const unbind = () => {
    if (!bound) return
    ACTIVITY_EVENTS.forEach((eventName) => {
      window.removeEventListener(eventName, markActivity)
    })
    document.removeEventListener('visibilitychange', onVisibility)
    bound = false
  }

  watch(
    () => authStore.isAuthenticated,
    (authed) => {
      if (authed) {
        checkStoredIdle()
        bind()
        return
      }
      if (timer) clearTimeout(timer)
      unbind()
      // Do not wipe activity timestamps during initial bootstrap before tokens hydrate.
      if (!authStore.bootstrapping && authStore.initialized) {
        localStorage.removeItem(LAST_ACTIVITY_KEY)
      }
    },
    { immediate: true },
  )

  watch(
    () => authStore.sessionTimeoutMinutes,
    () => {
      if (authStore.isAuthenticated) {
        checkStoredIdle()
      }
    },
  )

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
    unbind()
  })
}
