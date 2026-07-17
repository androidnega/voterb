<template>
  <div class="svt-page">
    <SvtGateSkeleton
      v-if="booting || showSkeleton"
      :hint="showSlowHint ? slowHint : ''"
    />

    <template v-else-if="bootError">
      <button type="button" class="svt-back" @click="$router.push('/student')">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        Back
      </button>
      <FriendlyLoadState
        tone="error"
        title="Couldn’t open this ballot"
        :message="bootError"
        action-label="Try again"
        @action="bootPage"
      />
    </template>

    <template v-else-if="alreadyVoted">
      <button type="button" class="svt-back" @click="$router.push('/student')">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        Back
      </button>
      <FriendlyLoadState
        tone="empty"
        title="You’ve already voted"
        message="Your ballot for this election is sealed. You can’t vote again."
        action-label="View receipt"
        icon="fas fa-check-circle"
        @action="goToConfirmation"
      />
    </template>

    <template v-else>
      <button type="button" class="svt-back" @click="$router.push('/student')">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        Back
      </button>

      <article class="svt-card">
        <header class="svt-card__head">
          <div class="svt-card__shield" aria-hidden="true">
            <i class="fas fa-shield-alt"></i>
          </div>
          <div class="svt-card__head-copy">
            <p class="svt-card__eyebrow">Secure voting token</p>
            <h1 class="svt-card__title">{{ electionTitle }}</h1>
          </div>
        </header>
        <p class="svt-card__sub">
          {{ step === 'verifying'
            ? 'Confirming your secure session…'
            : step === 'validate'
              ? 'Enter the SVT sent to your phone. Valid 20 minutes · one use.'
              : 'We’ll SMS a one-time SVT to your registered phone.' }}
        </p>

        <div v-if="step === 'request'" class="svt-panel">
          <p class="svt-meta">
            Starts with <strong>v-</strong> · max 3 requests · expires after use or 20 minutes.
          </p>
          <button type="button" class="svt-btn svt-btn--primary" :disabled="requesting" @click="requestSVT">
            <i v-if="requesting" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
            <span>{{ requesting ? (actionSlow ? 'Still working…' : 'Sending…') : 'Request SVT' }}</span>
          </button>
          <p v-if="actionSlow && requesting" class="svt-soft">{{ slowHint }}</p>
          <p v-if="errorMessage" class="svt-error">{{ errorMessage }}</p>
        </div>

        <div v-else-if="step === 'validate'" class="svt-panel">
          <div class="svt-status-row">
            <p class="svt-status">
              <i class="fas fa-check-circle" aria-hidden="true"></i>
              <span>{{ phoneMasked ? `Sent to ${phoneMasked}` : 'Token issued' }}</span>
            </p>
            <div
              v-if="svtExpiresAt"
              class="svt-countdown"
              :class="`is-${svtUrgency}`"
              role="timer"
              :aria-label="svtExpired ? 'SVT expired' : `SVT expires in ${svtCountdownDisplay}`"
            >
              <i class="fas fa-hourglass-half" aria-hidden="true"></i>
              <span>{{ svtExpired ? 'Expired' : svtCountdownDisplay || '—' }}</span>
            </div>
          </div>

          <div class="svt-otp" role="group" aria-label="Secure Voting Token">
            <span class="svt-otp__prefix" aria-hidden="true">v-</span>
            <div class="svt-otp__group">
              <input
                v-for="(_, index) in letterCount"
                :key="`L${index}`"
                :ref="(el) => setLetterRef(el, index)"
                v-model="letterDigits[index]"
                type="text"
                inputmode="text"
                maxlength="1"
                class="svt-otp__box"
                :class="{ 'is-filled': letterDigits[index] }"
                :disabled="validating || requesting"
                :aria-label="`Letter ${index + 1}`"
                autocomplete="one-time-code"
                spellcheck="false"
                @input="onLetterInput(index, $event)"
                @keydown="onLetterKeydown(index, $event)"
                @paste="onPaste"
              />
            </div>
            <span class="svt-otp__dash" aria-hidden="true">-</span>
            <div class="svt-otp__group">
              <input
                v-for="(_, index) in digitCount"
                :key="`D${index}`"
                :ref="(el) => setDigitRef(el, index)"
                v-model="numberDigits[index]"
                type="text"
                inputmode="numeric"
                maxlength="1"
                class="svt-otp__box"
                :class="{ 'is-filled': numberDigits[index] }"
                :disabled="validating || requesting"
                :aria-label="`Digit ${index + 1}`"
                autocomplete="one-time-code"
                spellcheck="false"
                @input="onDigitInput(index, $event)"
                @keydown="onDigitKeydown(index, $event)"
                @paste="onPaste"
              />
            </div>
          </div>

          <div class="svt-actions">
            <button type="button" class="svt-btn svt-btn--primary" :disabled="!canValidate || validating" @click="validateSVT">
              <i v-if="validating" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
              <span>{{ validating ? (actionSlow ? 'Still working…' : 'Checking…') : 'Unlock ballot' }}</span>
            </button>
            <button type="button" class="svt-btn svt-btn--ghost" :disabled="requesting || validating" @click="resendSVT">
              {{ requesting ? 'Sending…' : 'Resend' }}
            </button>
          </div>
          <p v-if="actionSlow && (validating || requesting)" class="svt-soft">{{ slowHint }}</p>
          <p v-if="errorMessage" class="svt-error">{{ errorMessage }}</p>
        </div>

        <div v-else-if="step === 'verifying'" class="svt-verify" aria-live="polite">
          <div class="svt-orbit" aria-hidden="true">
            <span class="svt-orbit__ring"></span>
            <span class="svt-orbit__ring svt-orbit__ring--delay"></span>
            <span class="svt-orbit__core">
              <i class="fas fa-shield-alt"></i>
            </span>
          </div>
          <p class="svt-verify__title">{{ verifyTitle }}</p>
          <ul class="svt-verify__log">
            <li
              v-for="(line, idx) in verifyLines"
              :key="line"
              :class="{ 'is-done': idx < verifyStep, 'is-active': idx === verifyStep }"
            >
              <i
                :class="idx < verifyStep ? 'fas fa-check' : (idx === verifyStep ? 'fas fa-spinner fa-spin' : 'far fa-circle')"
                aria-hidden="true"
              ></i>
              <span>{{ line }}</span>
            </li>
          </ul>
        </div>
      </article>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'
import { useFriendlyLoad } from '@/composables/useFriendlyLoad'
import { useExpiryCountdown } from '@/composables/useExpiryCountdown'
import { friendlyActionError } from '@/utils/friendlyFeedback'
import { unlockAudio, playBeep } from '@/utils/beep'
import {
  clearSvtSession,
  isValidSvtFormat,
  normalizeSvt,
  readSvtSession,
  writeSvtSession,
} from '@/utils/svtSession'
import SvtGateSkeleton from '@/components/student/SvtGateSkeleton.vue'
import FriendlyLoadState from '@/components/student/FriendlyLoadState.vue'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid

const letterCount = 3
const digitCount = 4

const electionTitle = ref('Election')
const step = ref('request')
const alreadyVoted = ref(false)
const letterDigits = ref(Array.from({ length: letterCount }, () => ''))
const numberDigits = ref(Array.from({ length: digitCount }, () => ''))
const letterInputs = ref([])
const digitInputs = ref([])
const requesting = ref(false)
const validating = ref(false)
const errorMessage = ref('')
const phoneMasked = ref('')
const svtExpiresAt = ref(null)
const verifyStep = ref(0)
const verifyTitle = ref('Securing your session…')
const actionSlow = ref(false)
let actionSlowTimer = null
let resumeStarted = false

const {
  display: svtCountdownDisplay,
  urgency: svtUrgency,
  expired: svtExpired,
} = useExpiryCountdown(svtExpiresAt, { beep: true })

const {
  loading: booting,
  showSkeleton,
  showSlowHint,
  slowHint,
  error: bootError,
  begin,
  succeed,
  fail,
} = useFriendlyLoad({ subject: 'this ballot', skeletonDelayMs: 0 })

const verifyLines = [
  'Checking token signature',
  'Matching voter eligibility',
  'Preparing presence check',
]

const svtNormalized = computed(() => {
  const letters = letterDigits.value.join('').toLowerCase()
  const digits = numberDigits.value.join('')
  return normalizeSvt(`v-${letters}-${digits}`)
})

const canValidate = computed(() => isValidSvtFormat(svtNormalized.value))

function setLetterRef(el, index) {
  if (el) letterInputs.value[index] = el
}

function setDigitRef(el, index) {
  if (el) digitInputs.value[index] = el
}

function clearBoxes() {
  letterDigits.value = Array.from({ length: letterCount }, () => '')
  numberDigits.value = Array.from({ length: digitCount }, () => '')
}

function focusFirstBox() {
  nextTick(() => letterInputs.value[0]?.focus())
}

function clearActionSlow() {
  actionSlow.value = false
  if (actionSlowTimer) {
    clearTimeout(actionSlowTimer)
    actionSlowTimer = null
  }
}

function markActionPending() {
  clearActionSlow()
  actionSlowTimer = setTimeout(() => {
    actionSlow.value = true
  }, 3500)
}

function onLetterInput(index, event) {
  const value = String(event.target.value || '').toLowerCase().replace(/[^a-z]/g, '').slice(0, 1)
  letterDigits.value[index] = value
  errorMessage.value = ''
  if (value && index < letterCount - 1) {
    letterInputs.value[index + 1]?.focus()
  } else if (value && index === letterCount - 1) {
    digitInputs.value[0]?.focus()
  }
  maybeAutoValidate()
}

function onDigitInput(index, event) {
  const value = String(event.target.value || '').replace(/\D/g, '').slice(0, 1)
  numberDigits.value[index] = value
  errorMessage.value = ''
  if (value && index < digitCount - 1) {
    digitInputs.value[index + 1]?.focus()
  }
  maybeAutoValidate()
}

function onLetterKeydown(index, event) {
  if (event.key === 'Backspace' && !letterDigits.value[index] && index > 0) {
    letterInputs.value[index - 1]?.focus()
  }
  if (event.key === 'ArrowLeft' && index > 0) letterInputs.value[index - 1]?.focus()
  if (event.key === 'ArrowRight' && index < letterCount - 1) letterInputs.value[index + 1]?.focus()
  if (event.key === 'ArrowRight' && index === letterCount - 1) digitInputs.value[0]?.focus()
}

function onDigitKeydown(index, event) {
  if (event.key === 'Backspace' && !numberDigits.value[index] && index > 0) {
    digitInputs.value[index - 1]?.focus()
  } else if (event.key === 'Backspace' && !numberDigits.value[index] && index === 0) {
    letterInputs.value[letterCount - 1]?.focus()
  }
  if (event.key === 'ArrowLeft' && index > 0) digitInputs.value[index - 1]?.focus()
  if (event.key === 'ArrowLeft' && index === 0) letterInputs.value[letterCount - 1]?.focus()
  if (event.key === 'ArrowRight' && index < digitCount - 1) digitInputs.value[index + 1]?.focus()
  if (event.key === 'Enter') validateSVT()
}

function applyTokenParts(letters, digits) {
  for (let i = 0; i < letterCount; i += 1) letterDigits.value[i] = letters[i] || ''
  for (let i = 0; i < digitCount; i += 1) numberDigits.value[i] = digits[i] || ''
}

function onPaste(event) {
  event.preventDefault()
  const pasted = String(event.clipboardData.getData('text') || '').trim().toLowerCase()
  const normalized = normalizeSvt(pasted)
  const compact = normalized.replace(/-/g, '')
  if (!/^v[a-z]{3}\d{4}$/.test(compact)) return
  applyTokenParts(compact.slice(1, 4).split(''), compact.slice(4).split(''))
  digitInputs.value[digitCount - 1]?.focus()
  maybeAutoValidate()
}

function maybeAutoValidate() {
  if (canValidate.value && !validating.value && !requesting.value) {
    setTimeout(() => validateSVT(), 280)
  }
}

async function playVerifySequence({ resume = false } = {}) {
  step.value = 'verifying'
  verifyStep.value = 0
  verifyTitle.value = resume ? 'Restoring your secure session…' : 'Validating secure token…'
  for (let i = 0; i < verifyLines.length; i += 1) {
    verifyStep.value = i
    await new Promise((r) => setTimeout(r, 480 + i * 100))
  }
  verifyStep.value = verifyLines.length
  verifyTitle.value = 'Identity check next'
  await new Promise((r) => setTimeout(r, 380))
}

async function openBallotAfterVerify({ resume = false, presenceCaptured = false } = {}) {
  await playVerifySequence({ resume })
  if (presenceCaptured) {
    await router.replace(`/vote/${electionUuid}/ballot`)
    return
  }
  await router.replace(`/vote/${electionUuid}/presence`)
}

async function resumeValidatedSession(sessionPayload = {}) {
  if (resumeStarted) return
  resumeStarted = true
  const local = readSvtSession(electionUuid)
  if (local?.code) {
    writeSvtSession(electionUuid, {
      code: local.code,
      expires_at: sessionPayload.expires_at || local.expires_at,
      status: 'validated',
    })
  } else if (sessionPayload.expires_at) {
    // Keep a lightweight marker so the ballot flow knows a session is active
    sessionStorage.setItem(
      `svt:${electionUuid}`,
      JSON.stringify({
        code: '',
        expires_at: sessionPayload.expires_at,
        status: 'validated',
        saved_at: new Date().toISOString(),
      }),
    )
  }
  await openBallotAfterVerify({
    resume: true,
    presenceCaptured: !!sessionPayload.presence_captured,
  })
}

function goToConfirmation() {
  router.push(`/vote/${electionUuid}/confirmation`)
}

async function bootPage() {
  begin()
  resumeStarted = false
  alreadyVoted.value = false
  try {
    const [eligibleRes, sessionRes] = await Promise.all([
      votingApi.getEligibleElections(),
      votingApi.getSvtSession(electionUuid),
    ])
    const elections = eligibleRes.data
    const session = sessionRes.data || { status: 'none' }
    const match = (Array.isArray(elections) ? elections : []).find(
      (e) => String(e.uuid) === String(electionUuid),
    )
    electionTitle.value = match?.title || 'Election'
    succeed()

    if (match?.has_voted || session.status === 'voted' || session.has_voted) {
      clearSvtSession(electionUuid)
      alreadyVoted.value = true
      return
    }

    if (session.status === 'validated') {
      await resumeValidatedSession(session)
      return
    }

    if (session.status === 'expired') {
      clearSvtSession(electionUuid)
      step.value = 'request'
      errorMessage.value = 'Your previous token expired. Request a new one to continue.'
      return
    }

    if (session.status === 'issued') {
      svtExpiresAt.value = session.expires_at || null
      phoneMasked.value = session.phone_masked || phoneMasked.value
      step.value = 'validate'
      await nextTick()
      focusFirstBox()
      return
    }

    // Local leftover without server session → clear and start fresh
    clearSvtSession(electionUuid)
    step.value = 'request'
  } catch (err) {
    console.error('Failed to open voting gate:', err)
    fail(err)
  }
}

const requestSVT = async () => {
  requesting.value = true
  errorMessage.value = ''
  unlockAudio()
  markActionPending()
  try {
    const { data } = await votingApi.requestSVT(electionUuid)
    if (data?.already_validated) {
      writeSvtSession(electionUuid, {
        code: readSvtSession(electionUuid)?.code || '',
        expires_at: data?.expires_at || null,
        status: 'validated',
      })
      await openBallotAfterVerify({
        resume: true,
        presenceCaptured: !!data?.presence_captured,
      })
      return
    }
    phoneMasked.value = data?.phone_masked || ''
    svtExpiresAt.value = data?.expires_at || null
    step.value = 'validate'
    playBeep('alert')
    clearBoxes()
    await nextTick()
    focusFirstBox()
  } catch (error) {
    if (error?.response?.data?.has_voted) {
      alreadyVoted.value = true
      return
    }
    errorMessage.value = friendlyActionError(error, 'We couldn’t send your token. Please try again.')
  } finally {
    clearActionSlow()
    requesting.value = false
  }
}

const validateSVT = async () => {
  if (!canValidate.value || validating.value) return
  validating.value = true
  errorMessage.value = ''
  markActionPending()
  try {
    const { data } = await votingApi.validateSVT(electionUuid, svtNormalized.value)
    writeSvtSession(electionUuid, {
      code: svtNormalized.value,
      expires_at: data?.expires_at || null,
      status: 'validated',
    })
    clearActionSlow()
    await openBallotAfterVerify({
      resume: !!data?.already_validated,
      presenceCaptured: !!data?.presence_captured,
    })
  } catch (error) {
    if (error?.response?.data?.has_voted) {
      alreadyVoted.value = true
      return
    }
    step.value = 'validate'
    errorMessage.value = friendlyActionError(error, 'That token didn’t work. Please try again.')
    clearBoxes()
    await nextTick()
    focusFirstBox()
  } finally {
    clearActionSlow()
    validating.value = false
  }
}

const resendSVT = async () => {
  requesting.value = true
  errorMessage.value = ''
  unlockAudio()
  markActionPending()
  try {
    const { data } = await votingApi.requestSVT(electionUuid, { resend: true })
    phoneMasked.value = data?.phone_masked || phoneMasked.value
    svtExpiresAt.value = data?.expires_at || null
    clearSvtSession(electionUuid)
    playBeep('alert')
    clearBoxes()
    await nextTick()
    focusFirstBox()
  } catch (error) {
    if (error?.response?.data?.has_voted) {
      alreadyVoted.value = true
      return
    }
    errorMessage.value = friendlyActionError(error, 'We couldn’t resend your token. Please try again.')
  } finally {
    clearActionSlow()
    requesting.value = false
  }
}

onMounted(bootPage)
onUnmounted(clearActionSlow)
</script>

<style scoped>
.svt-page {
  width: min(24.5rem, 100%);
  margin: 0 auto;
  padding: 0.35rem 0 1.5rem;
}

.svt-back {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: none;
  background: transparent;
  color: #78716c;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 0.7rem;
  padding: 0.2rem 0;
}

.svt-card {
  position: relative;
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1rem;
  padding: 1rem 1.05rem 1.05rem;
  box-shadow: 0 3px 12px rgba(28, 25, 23, 0.04);
  overflow: hidden;
}

.svt-card::before {
  content: '';
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #0f766e, #3d4f44 55%, #a3b18a);
}

.svt-card__head {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.svt-card__shield {
  flex-shrink: 0;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.7rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ecfdf5;
  color: #0f766e;
  font-size: 0.9rem;
}

.svt-card__head-copy {
  min-width: 0;
}

.svt-card__eyebrow {
  margin: 0;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.svt-card__title {
  margin: 0.1rem 0 0;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: #1c1917;
  line-height: 1.25;
}

.svt-card__sub {
  margin: 0.55rem 0 0;
  font-size: 0.8rem;
  color: #78716c;
  line-height: 1.4;
}

.svt-panel {
  margin-top: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.svt-meta {
  margin: 0;
  font-size: 0.74rem;
  line-height: 1.4;
  color: #78716c;
}

.svt-meta strong {
  color: #0f766e;
  font-weight: 700;
}

.svt-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.svt-status {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 650;
  color: #166534;
}

.svt-status i {
  color: #0f766e;
}

.svt-countdown {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  border: 1px solid #d6ebe5;
  background: #f4fbf8;
  font-size: 0.74rem;
  font-weight: 750;
  font-variant-numeric: tabular-nums;
  color: #134e4a;
  letter-spacing: 0.02em;
}

.svt-countdown.is-warn {
  border-color: #f5d0a9;
  background: #fff7ed;
  color: #c2410c;
}

.svt-countdown.is-urgent,
.svt-countdown.is-critical {
  border-color: #fecaca;
  background: #fef2f2;
  color: #b91c1c;
  animation: svt-pulse 1s ease-in-out infinite;
}

.svt-countdown.is-expired {
  border-color: #e7e5e4;
  background: #f5f5f4;
  color: #78716c;
  animation: none;
}

@keyframes svt-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

.svt-otp {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  width: 100%;
  overflow: hidden;
}

.svt-otp__prefix {
  flex-shrink: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 999px;
  padding: 0.18rem 0.42rem;
}

.svt-otp__dash {
  flex-shrink: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 700;
  color: #a8a29e;
  line-height: 1;
}

.svt-otp__group {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.22rem;
  flex-shrink: 0;
}

.svt-otp__box {
  width: 2rem;
  height: 2.25rem;
  flex: 0 0 auto;
  text-align: center;
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: lowercase;
  color: #1c1917;
  background: #fafaf8;
  border: 1.5px solid #e7e5e4;
  border-radius: 0.55rem;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.svt-otp__box.is-filled {
  border-color: #34d399;
  background: #fff;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

.svt-otp__box:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.16);
  background: #fff;
}

.svt-otp__box:disabled {
  opacity: 0.6;
}

.svt-actions {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.45rem;
}

.svt-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  border: none;
  border-radius: 0.7rem;
  padding: 0.65rem 0.9rem;
  min-height: 2.45rem;
  font-size: 0.84rem;
  font-weight: 650;
  cursor: pointer;
}

.svt-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.svt-btn--primary {
  background: #1c1917;
  color: #fff;
}

.svt-btn--ghost {
  background: #f5f5f4;
  color: #57534e;
  padding-inline: 0.85rem;
}

.svt-error {
  margin: 0;
  font-size: 0.76rem;
  color: #b91c1c;
}

.svt-soft {
  margin: 0;
  text-align: center;
  font-size: 0.72rem;
  color: #a8a29e;
}

.svt-verify {
  margin-top: 0.9rem;
  text-align: center;
  padding: 0.15rem 0 0;
}

.svt-orbit {
  position: relative;
  width: 4.5rem;
  height: 4.5rem;
  margin: 0 auto 0.75rem;
}

.svt-orbit__ring {
  position: absolute;
  inset: 0;
  border-radius: 9999px;
  border: 2px solid transparent;
  border-top-color: #0f766e;
  border-right-color: rgba(15, 118, 110, 0.25);
  animation: svt-spin 1.1s linear infinite;
}

.svt-orbit__ring--delay {
  inset: 0.4rem;
  animation-duration: 1.6s;
  animation-direction: reverse;
  border-top-color: #a3b18a;
}

.svt-orbit__core {
  position: absolute;
  inset: 0.95rem;
  border-radius: 9999px;
  background: #ecfdf5;
  color: #0f766e;
  display: grid;
  place-items: center;
  font-size: 0.95rem;
}

.svt-verify__title {
  margin: 0 0 0.65rem;
  font-size: 0.92rem;
  font-weight: 700;
  color: #1c1917;
}

.svt-verify__log {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
  text-align: left;
}

.svt-verify__log li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.76rem;
  color: #a8a29e;
}

.svt-verify__log li.is-active {
  color: #0f766e;
  font-weight: 600;
}

.svt-verify__log li.is-done {
  color: #57534e;
}

@keyframes svt-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .svt-page {
    padding: 0.15rem 0 1rem;
  }

  .svt-back {
    margin-bottom: 0.5rem;
  }

  .svt-card {
    padding: 0.85rem 0.85rem 0.9rem;
    border-radius: 0.9rem;
  }

  .svt-card__title {
    font-size: 0.98rem;
  }

  .svt-card__sub {
    font-size: 0.76rem;
  }

  .svt-panel {
    margin-top: 0.7rem;
    gap: 0.55rem;
  }

  .svt-actions {
    grid-template-columns: 1fr;
  }

  .svt-otp {
    gap: 0.2rem;
  }

  .svt-otp__group {
    gap: 0.16rem;
  }

  .svt-otp__box {
    width: 1.75rem;
    height: 2.05rem;
    font-size: 0.86rem;
    border-radius: 0.45rem;
  }

  .svt-btn {
    min-height: 2.35rem;
    padding: 0.58rem 0.8rem;
    font-size: 0.82rem;
  }
}

@media (max-width: 380px) {
  .svt-otp__box {
    width: 1.55rem;
    height: 1.9rem;
    font-size: 0.8rem;
  }

  .svt-otp__prefix {
    font-size: 0.64rem;
    padding: 0.12rem 0.3rem;
  }
}
</style>
