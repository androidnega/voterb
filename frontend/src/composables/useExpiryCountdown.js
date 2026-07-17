import { ref, computed, watch, onUnmounted } from 'vue'
import { playBeep } from '@/utils/beep'

/**
 * Live MM:SS countdown against an absolute expiry timestamp.
 * Beeps escalate as time runs out (not silent).
 */
export function useExpiryCountdown(expiresAtRef, {
  enabled = true,
  beep = true,
} = {}) {
  const nowMs = ref(Date.now())
  let timer = null
  let lastBeepBucket = null
  let expiredFired = false

  const remainingMs = computed(() => {
    const raw = typeof expiresAtRef === 'function' ? expiresAtRef() : expiresAtRef?.value
    if (!raw) return null
    const end = new Date(raw).getTime()
    if (Number.isNaN(end)) return null
    return Math.max(0, end - nowMs.value)
  })

  const expired = computed(() => remainingMs.value !== null && remainingMs.value <= 0)

  const totalSeconds = computed(() => {
    if (remainingMs.value === null) return null
    return Math.ceil(remainingMs.value / 1000)
  })

  const display = computed(() => {
    if (totalSeconds.value === null) return ''
    const s = Math.max(0, totalSeconds.value)
    const m = Math.floor(s / 60)
    const sec = s % 60
    if (m >= 60) {
      const h = Math.floor(m / 60)
      const mm = m % 60
      return `${String(h).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
    }
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  })

  const urgency = computed(() => {
    const s = totalSeconds.value
    if (s === null) return 'idle'
    if (s <= 0) return 'expired'
    if (s <= 30) return 'critical'
    if (s <= 120) return 'urgent'
    if (s <= 300) return 'warn'
    return 'ok'
  })

  const tick = () => {
    nowMs.value = Date.now()
    if (!beep || !enabled) return
    const s = totalSeconds.value
    if (s === null) return

    if (s <= 0) {
      if (!expiredFired) {
        expiredFired = true
        playBeep('expire')
      }
      return
    }

    // Beep cadence by urgency bucket (avoid spam every second until critical)
    let bucket = null
    let kind = 'tick'
    if (s <= 10) {
      bucket = `c-${s}`
      kind = 'urgent'
    } else if (s <= 30) {
      bucket = `u-${Math.floor(s / 5)}`
      kind = 'urgent'
    } else if (s <= 60) {
      bucket = `w-${Math.floor(s / 10)}`
      kind = 'warn'
    } else if (s <= 300) {
      bucket = `m-${Math.floor(s / 30)}`
      kind = 'warn'
    } else if (s % 60 === 0) {
      bucket = `ok-${s}`
      kind = 'tick'
    }

    if (bucket && bucket !== lastBeepBucket) {
      lastBeepBucket = bucket
      playBeep(kind)
    }
  }

  const start = () => {
    stop()
    expiredFired = false
    lastBeepBucket = null
    tick()
    timer = window.setInterval(tick, 1000)
  }

  const stop = () => {
    if (timer) {
      window.clearInterval(timer)
      timer = null
    }
  }

  watch(
    () => (typeof expiresAtRef === 'function' ? expiresAtRef() : expiresAtRef?.value),
    (val) => {
      if (val && enabled) start()
      else stop()
    },
    { immediate: true },
  )

  onUnmounted(stop)

  return {
    remainingMs,
    totalSeconds,
    display,
    urgency,
    expired,
    start,
    stop,
  }
}
