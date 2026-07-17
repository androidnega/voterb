import { ref, computed, onUnmounted } from 'vue'
import { strongroomApi, getVaultToken, setVaultToken } from '@/api/strongroom'

const isUnlocked = ref(false)
const remainingSeconds = ref(0)
const expiresAt = ref(null)
const sessionError = ref('')
const authenticating = ref(false)
const unlockChallenge = ref(null)

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

function applyOpenSession(data) {
  if (!data?.vault_token) return false
  setVaultToken(data.vault_token)
  isUnlocked.value = true
  expiresAt.value = data.expires_at
  remainingSeconds.value = (data.ttl_minutes || 30) * 60
  unlockChallenge.value = null
  startCountdown()
  return true
}

async function refreshUnlockStatus() {
  try {
    const { data } = await strongroomApi.unlockStatus()
    if (data.active) {
      unlockChallenge.value = data.challenge
      return data.challenge
    }
    unlockChallenge.value = null
    return null
  } catch {
    unlockChallenge.value = null
    return null
  }
}

async function checkSession() {
  if (!getVaultToken()) {
    isUnlocked.value = false
    await refreshUnlockStatus()
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

/** Step 1 — EC password starts peer-confirm challenge (does not unlock yet). */
async function authenticate(password) {
  authenticating.value = true
  sessionError.value = ''
  try {
    const { data } = await strongroomApi.authenticate(password)
    if (data.vault_token) {
      return applyOpenSession(data)
    }
    unlockChallenge.value = data
    return { challenge: data }
  } catch (error) {
    sessionError.value = error.response?.data?.error || 'Authentication failed'
    return false
  } finally {
    authenticating.value = false
  }
}

async function peerConfirm(challengeUuid) {
  authenticating.value = true
  sessionError.value = ''
  try {
    const { data } = await strongroomApi.peerConfirm(challengeUuid)
    unlockChallenge.value = data
    return data
  } catch (error) {
    sessionError.value = error.response?.data?.error || 'Peer confirmation failed'
    return null
  } finally {
    authenticating.value = false
  }
}

async function submitNomineeKey(challengeUuid, nomineeKey) {
  authenticating.value = true
  sessionError.value = ''
  try {
    const { data } = await strongroomApi.nomineeKey(challengeUuid, nomineeKey)
    return applyOpenSession(data)
  } catch (error) {
    sessionError.value = error.response?.data?.error || 'Nominee key rejected'
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
  unlockChallenge.value = null
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
    unlockChallenge,
    checkSession,
    refreshUnlockStatus,
    authenticate,
    peerConfirm,
    submitNomineeKey,
    lockVault,
  }
}
