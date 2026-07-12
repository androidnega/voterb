<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-emerald-50/30 p-4">
    <!-- Animated background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div v-for="i in 3" :key="i" class="absolute rounded-full bg-emerald-200/10 animate-float"
        :style="{
          width: (Math.random() * 150 + 80) + 'px',
          height: (Math.random() * 150 + 80) + 'px',
          top: (Math.random() * 80 + 10) + '%',
          left: (Math.random() * 80 + 10) + '%',
          animationDuration: (Math.random() * 10 + 15) + 's',
          animationDelay: (Math.random() * 5) + 's'
        }"
      ></div>
    </div>

    <div class="relative w-full max-w-sm">
      <!-- Header - compact -->
      <div class="text-center mb-6">
        <div class="flex justify-center">
          <div class="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </div>
        </div>
        <h2 class="mt-3 text-2xl font-bold text-gray-900 tracking-tight">Verify OTP</h2>
        <p class="mt-1 text-sm text-gray-500">Enter the 6-digit code sent to your phone</p>
      </div>

      <!-- OTP Card - compact -->
      <div class="bg-white/80 backdrop-blur-xl rounded-2xl border border-white/60 shadow-2xl p-6">
        <form @submit.prevent="handleVerify" class="space-y-5">
          <!-- 6-Digit OTP Input -->
          <div>
            <div class="flex justify-center gap-2">
              <input
                v-for="(digit, index) in 6"
                :key="index"
                ref="otpInputs"
                v-model="otpDigits[index]"
                type="text"
                inputmode="numeric"
                maxlength="1"
                class="w-11 h-12 sm:w-12 sm:h-14 text-center text-xl font-semibold bg-gray-50/80 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-gray-900"
                :class="{ 'border-emerald-500 ring-2 ring-emerald-500/20': otpDigits[index] && otpDigits[index].length === 1 }"
                @input="handleInput(index, $event)"
                @keydown="handleKeydown(index, $event)"
                @paste="handlePaste"
                :disabled="loading"
                autofocus
              />
            </div>
          </div>

          <!-- Error / Success Message -->
          <transition name="slide-fade">
            <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-xl text-sm flex items-center gap-2">
              <svg class="w-4 h-4 flex-shrink-0 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {{ errorMessage }}
            </div>
          </transition>

          <div v-if="otpDigits.some(d => d)" class="text-center text-xs text-gray-400">
            Code: <span class="font-mono font-medium text-gray-600">{{ getOTPString() || '••••••' }}</span>
          </div>

          <!-- Verify Button -->
          <button
            type="submit"
            :disabled="loading || !isOTPComplete"
            class="w-full flex justify-center items-center py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-medium rounded-xl hover:shadow-lg hover:shadow-emerald-500/25 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Verifying...' : 'Verify OTP' }}
          </button>

          <!-- Resend -->
          <div class="text-center">
            <button
              type="button"
              @click="resendOTP"
              class="text-sm text-emerald-600 hover:text-emerald-700 font-medium transition-colors duration-200"
              :class="{ 'opacity-50 cursor-not-allowed': resendCooldown > 0 || loading }"
              :disabled="resendCooldown > 0 || loading"
            >
              <span v-if="resendCooldown > 0" class="text-gray-400">
                Resend in <span class="font-mono">{{ resendCooldown }}</span>s
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
const isOTPComplete = computed(() => {
  return otpDigits.value.every(d => d && d.length === 1)
})

const getOTPString = () => {
  return otpDigits.value.join('')
}

onMounted(() => {
  otpSessionId.value = route.query.sessionId || authStore.pendingOtp
  if (!otpSessionId.value) {
    errorMessage.value = 'No OTP session found. Please login again.'
    setTimeout(() => router.push('/login'), 1500)
  }
  nextTick(() => {
    if (otpInputs.value && otpInputs.value[0]) {
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
    otpInputs.value[index + 1].focus()
  }
  
  if (isOTPComplete.value && !loading.value) {
    setTimeout(() => {
      handleVerify()
    }, 350)
  }
}

const handleKeydown = (index, event) => {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    otpInputs.value[index - 1].focus()
  }
  if (event.key === 'ArrowLeft' && index > 0) {
    otpInputs.value[index - 1].focus()
  }
  if (event.key === 'ArrowRight' && index < 5) {
    otpInputs.value[index + 1].focus()
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
  if (nextIndex < 6) {
    otpInputs.value[nextIndex].focus()
  }
  
  if (isOTPComplete.value && !loading.value) {
    setTimeout(() => {
      handleVerify()
    }, 350)
  }
}

const handleVerify = async () => {
  if (!isOTPComplete.value || loading.value) return
  
  const code = getOTPString()
  loading.value = true
  errorMessage.value = ''
  
  try {
    const result = await authStore.verifyOtp(otpSessionId.value, code)
    await router.replace(result.homeRoute || authStore.homeRoute)
  } catch (error) {
    console.error('OTP verification error:', error)
    errorMessage.value = error.response?.data?.error || 'Invalid OTP. Please try again.'
    otpDigits.value = ['', '', '', '', '', '']
    nextTick(() => {
      if (otpInputs.value && otpInputs.value[0]) {
        otpInputs.value[0].focus()
      }
    })
  } finally {
    loading.value = false
  }
}

const resendOTP = async () => {
  if (resendCooldown.value > 0 || loading.value) return
  
  try {
    const response = await authStore.resendOtp(otpSessionId.value)
    if (response?.success) {
      resendCooldown.value = 30
      cooldownInterval = setInterval(() => {
        resendCooldown.value--
        if (resendCooldown.value <= 0) {
          clearInterval(cooldownInterval)
          cooldownInterval = null
        }
      }, 1000)
    }
  } catch (error) {
    console.error('Failed to resend OTP:', error)
    errorMessage.value = 'Failed to resend OTP. Please try again.'
  }
}
</script>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); opacity: 0.2; }
  50% { transform: translateY(-20px) scale(1.05); opacity: 0.4; }
}

.animate-float {
  animation: float ease-in-out infinite;
}

input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type="number"] {
  -moz-appearance: textfield;
}

/* Transition animations */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}
.slide-fade-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}
.slide-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}

/* Input focus ring */
input:focus-visible {
  outline: none;
}

/* Input hover effect */
input:hover:not(:disabled) {
  border-color: #a7f3d0;
}

/* Shake animation for error */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.shake {
  animation: shake 0.3s ease-in-out;
}
</style>
