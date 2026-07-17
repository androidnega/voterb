<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="auth-brand">
        <div class="auth-mark">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.25" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
          </svg>
        </div>
        <h1 class="auth-title">Verify OTP</h1>
        <p class="auth-subtitle">Enter the 6-digit code sent to your phone</p>
        <p v-if="isDev" class="auth-debug">
          Debug mode: master OTP is <span>111111</span>
        </p>
      </div>

      <div class="auth-card">
        <form @submit.prevent="handleVerify" class="auth-form">
          <div class="otp-row">
            <input
              v-for="(digit, index) in 6"
              :key="index"
              ref="otpInputs"
              v-model="otpDigits[index]"
              type="text"
              inputmode="numeric"
              maxlength="1"
              class="otp-cell"
              :class="{ 'is-filled': otpDigits[index] && otpDigits[index].length === 1 }"
              @input="handleInput(index, $event)"
              @keydown="handleKeydown(index, $event)"
              @paste="handlePaste"
              :disabled="loading"
            />
          </div>

          <transition name="slide-fade">
            <div v-if="errorMessage" class="auth-error">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {{ errorMessage }}
            </div>
          </transition>

          <p v-if="otpDigits.some(d => d)" class="otp-preview">
            Code: <span>{{ getOTPString() || '••••••' }}</span>
          </p>

          <button
            type="submit"
            class="auth-submit"
            :disabled="loading || !isOTPComplete"
          >
            <svg v-if="loading" class="auth-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Verifying…' : 'Verify OTP' }}
          </button>

          <div class="auth-footer">
            <button
              type="button"
              class="auth-link"
              :disabled="resendCooldown > 0 || loading"
              @click="resendOTP"
            >
              <span v-if="resendCooldown > 0" class="auth-cooldown">
                Resend in <span>{{ resendCooldown }}</span>s
              </span>
              <span v-else>Resend OTP</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const otpDigits = ref(['', '', '', '', '', ''])
const otpInputs = ref([])
const loading = ref(false)
const errorMessage = ref('')
const resendCooldown = ref(0)
let cooldownInterval = null

const otpSessionId = ref('')
const isDev = import.meta.env.DEV
let verifyInFlight = false

const getOTPString = () => otpDigits.value.join('').replace(/\s/g, '')

const isOTPComplete = computed(() => {
  const code = getOTPString()
  // Always require 6 digits so auto-submit does not fire early on 11111
  return code.length === 6 && otpDigits.value.every((d) => d && d.length === 1)
})

const scheduleVerify = () => {
  if (verifyInFlight || loading.value || !isOTPComplete.value) return
  setTimeout(() => {
    handleVerify()
  }, 250)
}

onMounted(() => {
  otpSessionId.value = route.query.sessionId || authStore.pendingOtp
  if (!otpSessionId.value) {
    errorMessage.value = 'No OTP session found. Please login again.'
    setTimeout(() => router.push('/login'), 1500)
  }
  nextTick(() => {
    if (otpInputs.value?.[0] && document.activeElement !== otpInputs.value[0]) {
      otpInputs.value[0].focus()
    }
  })
})

const handleInput = (index, event) => {
  const value = event.target.value
  if (value && !/^\d$/.test(value)) {
    otpDigits.value[index] = ''
    return
  }

  if (value && value.length === 1 && index < 5) {
    otpInputs.value[index + 1]?.focus()
  }

  scheduleVerify()
}

const handleKeydown = (index, event) => {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    otpInputs.value[index - 1]?.focus()
  }
  if (event.key === 'ArrowLeft' && index > 0) {
    otpInputs.value[index - 1]?.focus()
  }
  if (event.key === 'ArrowRight' && index < 5) {
    otpInputs.value[index + 1]?.focus()
  }
}

const handlePaste = (event) => {
  event.preventDefault()
  const pasteData = event.clipboardData.getData('text').replace(/\D/g, '')
  const digits = pasteData.slice(0, 6).split('')

  for (let i = 0; i < digits.length && i < 6; i++) {
    otpDigits.value[i] = digits[i]
  }

  const nextIndex = Math.min(digits.length, 5)
  otpInputs.value[nextIndex]?.focus()
  scheduleVerify()
}

const handleVerify = async () => {
  if (!isOTPComplete.value || verifyInFlight || loading.value) return
  if (!otpSessionId.value) {
    errorMessage.value = 'No OTP session found. Please login again.'
    return
  }

  const code = getOTPString()
  verifyInFlight = true
  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.verifyOtp(otpSessionId.value, code)
    if (authStore.isStudent) {
      await router.replace('/student')
    } else {
      await router.replace('/dashboard')
    }
  } catch (error) {
    verifyInFlight = false
    console.error('OTP verification error:', error)
    errorMessage.value = error.response?.data?.error || 'Invalid OTP. Please try again.'
    // Keep digits so staff can correct/retry without retyping master code
    nextTick(() => {
      otpInputs.value?.[5]?.focus()
    })
  } finally {
    loading.value = false
  }
}

const resendOTP = async () => {
  if (resendCooldown.value > 0 || loading.value) return
  if (!otpSessionId.value) {
    errorMessage.value = 'No OTP session found. Please login again.'
    return
  }

  try {
    const response = await authStore.resendOtp(otpSessionId.value)
    if (response?.success) {
      // Critical: resend invalidates the old session — use the new id
      if (authStore.pendingOtp) {
        otpSessionId.value = authStore.pendingOtp
        await router.replace({ path: '/otp', query: { sessionId: otpSessionId.value } })
      }
      errorMessage.value = ''
      otpDigits.value = ['', '', '', '', '', '']
      resendCooldown.value = 30
      cooldownInterval = setInterval(() => {
        resendCooldown.value--
        if (resendCooldown.value <= 0) {
          clearInterval(cooldownInterval)
          cooldownInterval = null
        }
      }, 1000)
      nextTick(() => otpInputs.value?.[0]?.focus())
    }
  } catch (error) {
    console.error('Failed to resend OTP:', error)
    errorMessage.value = 'Failed to resend OTP. Please try again.'
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem 1rem;
  background:
    radial-gradient(ellipse 70% 45% at 50% -15%, rgba(15, 118, 110, 0.07), transparent 60%),
    #f7f6f3;
}

.auth-shell {
  width: min(100%, 22.5rem);
}

.auth-brand {
  text-align: center;
  margin-bottom: 1.2rem;
}

.auth-mark {
  width: 2.75rem;
  height: 2.75rem;
  margin: 0 auto;
  border-radius: 0.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #0f766e;
  color: #fff;
}

.auth-mark svg {
  width: 1.3rem;
  height: 1.3rem;
}

.auth-title {
  margin: 0.85rem 0 0.3rem;
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.auth-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: #78716c;
}

.auth-debug {
  display: inline-block;
  margin: 0.7rem 0 0;
  padding: 0.35rem 0.65rem;
  border-radius: 0.5rem;
  border: 1px solid #f5e6d3;
  background: #fffbeb;
  color: #92400e;
  font-size: 0.72rem;
}

.auth-debug span {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 700;
}

.auth-card {
  background: #fff;
  border: 1px solid #e8e6e1;
  border-radius: 1.15rem;
  padding: 1.25rem 1.15rem 1.15rem;
  box-shadow: 0 8px 28px rgba(28, 25, 23, 0.045);
}

.auth-form {
  display: grid;
  gap: 1rem;
}

.otp-row {
  display: flex;
  justify-content: center;
  gap: 0.45rem;
}

.otp-cell {
  width: 2.55rem;
  height: 2.9rem;
  text-align: center;
  font-size: 1.15rem;
  font-weight: 650;
  color: #1c1917;
  background: #fafaf9;
  border: 1px solid #e7e5e4;
  border-radius: 0.7rem;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.otp-cell:focus {
  outline: none;
  border-color: #99f6e4;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1);
}

.otp-cell.is-filled {
  border-color: #5eead4;
  background: #fff;
}

.otp-cell:disabled {
  opacity: 0.55;
}

.otp-preview {
  margin: 0;
  text-align: center;
  font-size: 0.75rem;
  color: #a8a29e;
}

.otp-preview span {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #57534e;
  font-weight: 600;
}

.auth-error {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.65rem 0.8rem;
  border-radius: 0.7rem;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 0.8rem;
  line-height: 1.4;
}

.auth-error svg {
  width: 0.95rem;
  height: 0.95rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.auth-submit {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.78rem 1rem;
  border: none;
  border-radius: 0.75rem;
  background: #0f766e;
  color: #fff;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.auth-submit:hover:not(:disabled) {
  background: #0d6b64;
}

.auth-submit:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.auth-spin {
  width: 0.95rem;
  height: 0.95rem;
  animation: spin 0.8s linear infinite;
}

.auth-footer {
  text-align: center;
}

.auth-link {
  border: none;
  background: transparent;
  color: #0f766e;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.15rem 0.35rem;
}

.auth-link:hover:not(:disabled) {
  color: #0d6b64;
}

.auth-link:disabled {
  cursor: not-allowed;
}

.auth-cooldown {
  color: #a8a29e;
  font-weight: 500;
}

.auth-cooldown span {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.slide-fade-enter-active {
  transition: all 0.25s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.18s ease-in;
}

.slide-fade-enter-from {
  transform: translateY(-8px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(6px);
  opacity: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
