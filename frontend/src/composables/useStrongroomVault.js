import { ref, computed, onUnmounted } from 'vue'
import { strongroomApi, getVaultToken, setVaultToken } from '@/api/strongroom'

const isUnlocked = ref(false)
const remainingSeconds = ref(0)
const expiresAt = ref(null)
const sessionError = ref('')
const authenticating = ref(false)

let countdownTimer = null

function formatRemaining(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

const remainingLabel = computed(() => formatRemaining(remainingSeconds.value))

function startCountdown() {
  stopCountdown()
  countdownTimer = setInterval(() => {
    if (remainingSeconds.value > 0) {
      remainingSeconds.value -= 1
    } else {
      lockVault()
    }
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

async function checkSession() {
  if (!getVaultToken()) {
    isUnlocked.value = false
    return false
  }
  try {
    const { data } = await strongroomApi.sessionStatus()
    if (data.active) {
      isUnlocked.value = true
      remainingSeconds.value = data.remaining_seconds || 0
      expiresAt.value = data.expires_at
      startCountdown()
      return true
    }
    lockVault()
    return false
  } catch {
    lockVault()
    return false
  }
}

async function authenticate(password) {
  authenticating.value = true
  sessionError.value = ''
  try {
    const { data } = await strongroomApi.authenticate(password)
    setVaultToken(data.vault_token)
    isUnlocked.value = true
    expiresAt.value = data.expires_at
    remainingSeconds.value = (data.ttl_minutes || 30) * 60
    startCountdown()
    return true
  } catch (error) {
    sessionError.value = error.response?.data?.error || 'Authentication failed'
    return false
  } finally {
    authenticating.value = false
  }
}

async function lockVault() {
  stopCountdown()
  try {
    if (getVaultToken()) await strongroomApi.closeSession()
  } catch {
    // ignore close errors
  }
  setVaultToken(null)
  isUnlocked.value = false
  remainingSeconds.value = 0
  expiresAt.value = null
}

export function useStrongroomVault() {
  onUnmounted(stopCountdown)

  return {
    isUnlocked,
    remainingSeconds,
    remainingLabel,
    expiresAt,
    sessionError,
    authenticating,
    checkSession,
    authenticate,
    lockVault,
  }
}
