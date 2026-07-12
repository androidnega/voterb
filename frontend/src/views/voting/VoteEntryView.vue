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

    <template v-else>
      <button type="button" class="svt-back" @click="$router.push('/student')">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        Back
      </button>

      <article class="svt-card">
        <div class="svt-card__shield" aria-hidden="true">
          <i class="fas fa-shield-alt"></i>
        </div>
        <p class="svt-card__eyebrow">Secure voting gate</p>
        <h1 class="svt-card__title">{{ electionTitle }}</h1>
        <p class="svt-card__sub">
          {{ step === 'verifying'
            ? 'Confirming your secure session…'
            : 'Confirm your Secure Voting Token to unlock the ballot.' }}
        </p>

        <div v-if="step === 'request'" class="svt-panel">
          <div class="svt-note">
            <i class="fas fa-lock" aria-hidden="true"></i>
            <div>
              <strong>Secure Voting Token</strong>
              <p>Request a one-time token sent to your registered channel, then enter it here to unlock your ballot.</p>
            </div>
          </div>
          <button type="button" class="svt-btn svt-btn--primary" :disabled="requesting" @click="requestSVT">
            <i v-if="requesting" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
            <span>{{ requesting ? (actionSlow ? 'Still working…' : 'Sending…') : 'Request SVT' }}</span>
          </button>
          <p v-if="actionSlow && requesting" class="svt-soft">{{ slowHint }}</p>
          <p v-if="errorMessage" class="svt-error">{{ errorMessage }}</p>
        </div>

        <div v-else-if="step === 'validate'" class="svt-panel">
          <div class="svt-note svt-note--ok">
            <i class="fas fa-check-circle" aria-hidden="true"></i>
            <div>
              <strong>Token issued</strong>
              <p>Enter each character of your Secure Voting Token.</p>
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
import { friendlyActionError } from '@/utils/friendlyFeedback'
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
const letterDigits = ref(Array.from({ length: letterCount }, () => ''))
const numberDigits = ref(Array.from({ length: digitCount }, () => ''))
const letterInputs = ref([])
const digitInputs = ref([])
const requesting = ref(false)
const validating = ref(false)
const errorMessage = ref('')
const verifyStep = ref(0)
const verifyTitle = ref('Securing your session…')
const actionSlow = ref(false)
let actionSlowTimer = null
let resumeStarted = false

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
  'Opening sealed ballot positions',
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
  verifyTitle.value = 'Ballot unlocked'
  await new Promise((r) => setTimeout(r, 380))
}

async function openBallotAfterVerify({ resume = false } = {}) {
  await playVerifySequence({ resume })
  await router.replace(`/vote/${electionUuid}/ballot`)
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
  await openBallotAfterVerify({ resume: true })
}

async function bootPage() {
  begin()
  resumeStarted = false
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
  markActionPending()
  try {
    await votingApi.requestSVT(electionUuid)
    step.value = 'validate'
    clearBoxes()
    await nextTick()
    focusFirstBox()
  } catch (error) {
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
    await openBallotAfterVerify({ resume: !!data?.already_validated })
  } catch (error) {
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
  markActionPending()
  try {
    await votingApi.requestSVT(electionUuid, { resend: true })
    clearSvtSession(electionUuid)
    clearBoxes()
    await nextTick()
    focusFirstBox()
  } catch (error) {
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
  width: min(28rem, 100%);
  margin: 0 auto;
  padding: 0.5rem 0 2rem;
}

.svt-back {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: none;
  background: transparent;
  color: #78716c;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 1rem;
  padding: 0.25rem 0;
}

.svt-card {
  position: relative;
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.5rem;
  padding: 1.5rem 1.35rem 1.45rem;
  box-shadow: 0 10px 30px rgba(28, 25, 23, 0.04);
  overflow: hidden;
}

.svt-card::before {
  content: '';
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #0f766e, #3d4f44 55%, #a3b18a);
}

.svt-card__shield {
  width: 3rem;
  height: 3rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ecfdf5;
  color: #0f766e;
  font-size: 1.1rem;
  margin-bottom: 0.85rem;
}

.svt-card__eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.svt-card__title {
  margin: 0.35rem 0 0;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.svt-card__sub {
  margin: 0.4rem 0 0;
  font-size: 0.88rem;
  color: #78716c;
  line-height: 1.45;
}

.svt-panel {
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.svt-note {
  display: flex;
  gap: 0.7rem;
  padding: 0.85rem 0.9rem;
  border-radius: 1rem;
  background: #f8f7f4;
  border: 1px solid #ebe8e2;
  color: #57534e;
}

.svt-note--ok {
  background: #ecfdf5;
  border-color: #bbf7d0;
  color: #166534;
}

.svt-note i {
  margin-top: 0.15rem;
  color: #0f766e;
}

.svt-note strong {
  display: block;
  font-size: 0.84rem;
  margin-bottom: 0.15rem;
}

.svt-note p {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.45;
}

.svt-otp {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.25rem 0;
}

.svt-otp__prefix {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 999px;
  padding: 0.28rem 0.65rem;
}

.svt-otp__dash {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 700;
  color: #a8a29e;
  padding: 0 0.1rem;
}

.svt-otp__group {
  display: flex;
  gap: 0.35rem;
}

.svt-otp__box {
  width: 2.35rem;
  height: 2.75rem;
  text-align: center;
  font-size: 1.05rem;
  font-weight: 700;
  text-transform: lowercase;
  color: #1c1917;
  background: #fafaf8;
  border: 2px solid #e7e5e4;
  border-radius: 0.75rem;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.svt-otp__box.is-filled {
  border-color: #34d399;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
}

.svt-otp__box:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
  background: #fff;
}

.svt-otp__box:disabled {
  opacity: 0.6;
}

.svt-actions {
  display: grid;
  gap: 0.55rem;
}

.svt-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  border: none;
  border-radius: 0.85rem;
  padding: 0.85rem 1rem;
  font-size: 0.88rem;
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
}

.svt-error {
  margin: 0;
  font-size: 0.8rem;
  color: #b91c1c;
}

.svt-soft {
  margin: 0;
  text-align: center;
  font-size: 0.74rem;
  color: #a8a29e;
}

.svt-verify {
  margin-top: 1.4rem;
  text-align: center;
  padding: 0.5rem 0 0.25rem;
}

.svt-orbit {
  position: relative;
  width: 6.5rem;
  height: 6.5rem;
  margin: 0 auto 1.1rem;
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
  inset: 0.55rem;
  animation-duration: 1.6s;
  animation-direction: reverse;
  border-top-color: #a3b18a;
}

.svt-orbit__core {
  position: absolute;
  inset: 1.35rem;
  border-radius: 9999px;
  background: #ecfdf5;
  color: #0f766e;
  display: grid;
  place-items: center;
  font-size: 1.15rem;
}

.svt-verify__title {
  margin: 0 0 0.85rem;
  font-size: 1rem;
  font-weight: 700;
  color: #1c1917;
}

.svt-verify__log {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.45rem;
  text-align: left;
}

.svt-verify__log li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.8rem;
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

@media (max-width: 420px) {
  .svt-otp__box {
    width: 2.1rem;
    height: 2.5rem;
    font-size: 0.95rem;
  }
}
</style>
