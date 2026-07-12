<template>
  <div class="svt-page">
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
      <p class="svt-card__sub">Confirm your Secure Voting Token to unlock the ballot.</p>

      <!-- Request -->
      <div v-if="step === 'request'" class="svt-panel">
        <div class="svt-note">
          <i class="fas fa-lock" aria-hidden="true"></i>
          <div>
            <strong>SVT format</strong>
            <p>Tokens look like <code>v-sda-4539</code> — letters and digits, not a plain PIN.</p>
          </div>
        </div>
        <button type="button" class="svt-btn svt-btn--primary" :disabled="requesting" @click="requestSVT">
          <i v-if="requesting" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
          <span>{{ requesting ? 'Issuing token…' : 'Request SVT' }}</span>
        </button>
        <p v-if="errorMessage" class="svt-error">{{ errorMessage }}</p>
      </div>

      <!-- Enter token -->
      <div v-else-if="step === 'validate'" class="svt-panel">
        <div class="svt-note svt-note--ok">
          <i class="fas fa-check-circle" aria-hidden="true"></i>
          <div>
            <strong>Token issued</strong>
            <p>Enter the SVT exactly as received. It expires in 10 minutes.</p>
          </div>
        </div>

        <div v-if="devCode" class="svt-dev">
          <span>Local test token</span>
          <button type="button" class="svt-dev__code" @click="fillDevCode">{{ devCode }}</button>
        </div>

        <label class="svt-field">
          <span class="svt-field__label">
            <i class="fas fa-key" aria-hidden="true"></i>
            Secure Voting Token
          </span>
          <div class="svt-field__shell" :class="{ 'is-focus': fieldFocused, 'is-error': !!errorMessage }">
            <span class="svt-field__prefix" aria-hidden="true">SVT</span>
            <input
              ref="svtInput"
              v-model="svtDisplay"
              type="text"
              class="svt-field__input"
              autocomplete="one-time-code"
              spellcheck="false"
              maxlength="10"
              placeholder="v-sda-4539"
              aria-label="Secure Voting Token"
              @focus="fieldFocused = true"
              @blur="fieldFocused = false"
              @input="onSvtInput"
              @keyup.enter="validateSVT"
            />
            <i class="fas fa-fingerprint svt-field__seal" aria-hidden="true"></i>
          </div>
          <span class="svt-field__hint">Pattern: v · three letters · four digits</span>
        </label>

        <div class="svt-actions">
          <button type="button" class="svt-btn svt-btn--primary" :disabled="!canValidate || validating" @click="validateSVT">
            Unlock ballot
          </button>
          <button type="button" class="svt-btn svt-btn--ghost" :disabled="requesting" @click="resendSVT">
            Resend
          </button>
        </div>
        <p v-if="errorMessage" class="svt-error">{{ errorMessage }}</p>
      </div>

      <!-- Validating animation -->
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
          <li v-for="(line, idx) in verifyLines" :key="line" :class="{ 'is-done': idx < verifyStep, 'is-active': idx === verifyStep }">
            <i :class="idx < verifyStep ? 'fas fa-check' : (idx === verifyStep ? 'fas fa-spinner fa-spin' : 'far fa-circle')" aria-hidden="true"></i>
            <span>{{ line }}</span>
          </li>
        </ul>
      </div>
    </article>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid

const electionTitle = ref('Election')
const step = ref('request')
const svtDisplay = ref('')
const svtNormalized = ref('')
const requesting = ref(false)
const validating = ref(false)
const errorMessage = ref('')
const fieldFocused = ref(false)
const devCode = ref('')
const svtInput = ref(null)
const verifyStep = ref(0)
const verifyTitle = ref('Securing your session…')

const verifyLines = [
  'Checking token signature',
  'Matching voter eligibility',
  'Opening sealed ballot positions',
]

const canValidate = computed(() => /^v-[a-z]{3}-\d{4}$/.test(svtNormalized.value))

function normalizeSvt(value) {
  const raw = String(value || '').trim().toLowerCase().replace(/\s+/g, '')
  const compact = raw.replace(/-/g, '')
  if (/^v[a-z]{3}\d{4}$/.test(compact)) {
    return `v-${compact.slice(1, 4)}-${compact.slice(4)}`
  }
  return raw
}

function formatSvtInput(value) {
  const compact = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
  let out = ''
  for (const ch of compact) {
    if (out.length >= 10) break
    if (out.length === 0) {
      if (ch === 'v') out = 'v'
      continue
    }
    if (out.length === 1) out += '-'
    if (out.length >= 2 && out.length < 5) {
      if (/[a-z]/.test(ch)) out += ch
      continue
    }
    if (out.length === 5) out += '-'
    if (out.length >= 6 && /[0-9]/.test(ch)) out += ch
  }
  return out
}

function onSvtInput(event) {
  const formatted = formatSvtInput(event.target.value)
  svtDisplay.value = formatted
  svtNormalized.value = normalizeSvt(formatted)
  errorMessage.value = ''
}

function fillDevCode() {
  if (!devCode.value) return
  svtDisplay.value = formatSvtInput(devCode.value)
  svtNormalized.value = normalizeSvt(devCode.value)
  nextTick(() => svtInput.value?.focus())
}

function storeSvt(code) {
  sessionStorage.setItem(`svt:${electionUuid}`, code)
}

async function playVerifySequence() {
  step.value = 'verifying'
  verifyStep.value = 0
  verifyTitle.value = 'Validating secure token…'
  for (let i = 0; i < verifyLines.length; i += 1) {
    verifyStep.value = i
    await new Promise((r) => setTimeout(r, 520 + i * 120))
  }
  verifyStep.value = verifyLines.length
  verifyTitle.value = 'Ballot unlocked'
  await new Promise((r) => setTimeout(r, 420))
}

onMounted(async () => {
  try {
    const { data } = await votingApi.getEligibleElections()
    const match = (Array.isArray(data) ? data : []).find((e) => String(e.uuid) === String(electionUuid))
    if (match?.title) electionTitle.value = match.title
  } catch {
    electionTitle.value = 'Election'
  }
})

const requestSVT = async () => {
  requesting.value = true
  errorMessage.value = ''
  try {
    const { data } = await votingApi.requestSVT(electionUuid)
    devCode.value = data?.svt_code || ''
    step.value = 'validate'
    await nextTick()
    svtInput.value?.focus()
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Failed to send SVT. Please try again.'
  } finally {
    requesting.value = false
  }
}

const validateSVT = async () => {
  if (!canValidate.value) {
    errorMessage.value = 'Enter a token like v-sda-4539.'
    return
  }
  validating.value = true
  errorMessage.value = ''
  try {
    await votingApi.validateSVT(electionUuid, svtNormalized.value)
    storeSvt(svtNormalized.value)
    await playVerifySequence()
    router.push(`/vote/${electionUuid}/ballot`)
  } catch (error) {
    step.value = 'validate'
    errorMessage.value = error.response?.data?.error || 'Invalid code. Please try again.'
  } finally {
    validating.value = false
  }
}

const resendSVT = async () => {
  requesting.value = true
  errorMessage.value = ''
  try {
    const { data } = await votingApi.requestSVT(electionUuid)
    devCode.value = data?.svt_code || ''
    svtDisplay.value = ''
    svtNormalized.value = ''
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Failed to resend. Please try again.'
  } finally {
    requesting.value = false
  }
}
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
  font-size: 0.82rem;
  color: inherit;
}

.svt-note p {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
  line-height: 1.4;
  opacity: 0.9;
}

.svt-note code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.78rem;
  background: rgba(255, 255, 255, 0.7);
  padding: 0.05rem 0.3rem;
  border-radius: 0.3rem;
}

.svt-dev {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.65rem 0.8rem;
  border-radius: 0.85rem;
  background: #1c1917;
  color: #fafaf9;
  font-size: 0.75rem;
}

.svt-dev__code {
  border: none;
  background: transparent;
  color: #a3b18a;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  cursor: pointer;
}

.svt-field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.svt-field__label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: #57534e;
}

.svt-field__shell {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.35rem 0.55rem 0.35rem 0.75rem;
  border-radius: 1rem;
  background: #f6f5f2;
  border: 1px solid #e7e5e4;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.svt-field__shell.is-focus {
  background: #fff;
  border-color: #0f766e;
  box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.12);
}

.svt-field__shell.is-error {
  border-color: #f87171;
  box-shadow: 0 0 0 4px rgba(248, 113, 113, 0.12);
}

.svt-field__prefix {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #a8a29e;
}

.svt-field__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #1c1917;
}

.svt-field__input::placeholder {
  color: #d6d3d1;
  letter-spacing: 0.08em;
  font-weight: 600;
}

.svt-field__seal {
  width: 2rem;
  height: 2rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #0f766e;
  font-size: 0.85rem;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.06);
}

.svt-field__hint {
  font-size: 0.72rem;
  color: #a8a29e;
}

.svt-actions {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 0.55rem;
}

.svt-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  border-radius: 0.95rem;
  border: none;
  padding: 0.85rem 1rem;
  font-size: 0.88rem;
  font-weight: 700;
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
  border-top-color: #a3b18a;
  animation-duration: 1.6s;
  animation-direction: reverse;
}

.svt-orbit__core {
  position: absolute;
  inset: 1.35rem;
  border-radius: 9999px;
  background: linear-gradient(145deg, #ecfdf5, #fff);
  border: 1px solid #d8e0cf;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0f766e;
  font-size: 1.25rem;
  box-shadow: inset 0 0 0 4px rgba(255, 255, 255, 0.8);
}

.svt-verify__title {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 800;
  color: #1c1917;
}

.svt-verify__log {
  list-style: none;
  margin: 0 auto;
  padding: 0;
  width: min(100%, 18rem);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.svt-verify__log li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.8rem;
  color: #a8a29e;
  transition: color 0.2s ease;
}

.svt-verify__log li.is-active {
  color: #0f766e;
  font-weight: 700;
}

.svt-verify__log li.is-done {
  color: #166534;
}

@keyframes svt-spin {
  to { transform: rotate(360deg); }
}
</style>
