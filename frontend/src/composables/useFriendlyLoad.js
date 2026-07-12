import { ref, onUnmounted } from 'vue'
import { friendlyLoadError, SLOW_LOAD_HINT } from '@/utils/friendlyFeedback'

/**
 * Loading UX with delayed skeleton + slow-network hint.
 * Keeps the UI calm on fast responses and helpful when the network lags.
 */
export function useFriendlyLoad({
  subject = 'this page',
  skeletonDelayMs = 160,
  slowHintMs = 4200,
} = {}) {
  const loading = ref(false)
  const showSkeleton = ref(false)
  const showSlowHint = ref(false)
  const error = ref('')
  const slowHint = SLOW_LOAD_HINT

  let skeletonTimer = null
  let slowTimer = null

  function clearTimers() {
    if (skeletonTimer) {
      clearTimeout(skeletonTimer)
      skeletonTimer = null
    }
    if (slowTimer) {
      clearTimeout(slowTimer)
      slowTimer = null
    }
  }

  function begin() {
    loading.value = true
    error.value = ''
    showSlowHint.value = false
    showSkeleton.value = skeletonDelayMs <= 0
    clearTimers()

    if (skeletonDelayMs > 0) {
      skeletonTimer = setTimeout(() => {
        if (loading.value) showSkeleton.value = true
      }, skeletonDelayMs)
    }

    slowTimer = setTimeout(() => {
      if (loading.value) showSlowHint.value = true
    }, slowHintMs)
  }

  function succeed() {
    clearTimers()
    loading.value = false
    showSkeleton.value = false
    showSlowHint.value = false
    error.value = ''
  }

  function fail(err) {
    clearTimers()
    loading.value = false
    showSkeleton.value = false
    showSlowHint.value = false
    error.value = friendlyLoadError(err, subject)
  }

  onUnmounted(clearTimers)

  return {
    loading,
    showSkeleton,
    showSlowHint,
    slowHint,
    error,
    begin,
    succeed,
    fail,
    clearTimers,
  }
}
