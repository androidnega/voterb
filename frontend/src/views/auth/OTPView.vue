<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <div class="flex justify-center">
          <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </div>
        </div>
        <h2 class="mt-6 text-3xl font-bold text-gray-900">Verify OTP</h2>
        <p class="mt-2 text-sm text-gray-600">Enter the 6-digit code (check backend console in dev)</p>
      </div>

      <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8">
        <form @submit.prevent="handleVerify" class="space-y-6">
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {{ errorMessage }}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">OTP Code</label>
            <input
              v-model="code"
              type="text"
              maxlength="6"
              inputmode="numeric"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-center text-2xl tracking-widest"
              placeholder="123456"
              autofocus
            />
          </div>

          <button
            type="submit"
            :disabled="loading || code.length !== 6"
            class="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Verifying...' : 'Verify OTP' }}
          </button>

          <div class="text-center">
            <button type="button" @click="resendOTP" class="text-sm text-green-600 hover:text-green-700 font-medium">
              Resend OTP
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const code = ref('')
const loading = ref(false)
const otpSessionId = ref('')
const errorMessage = ref('')

onMounted(() => {
  otpSessionId.value = route.query.sessionId || authStore.pendingOtp
  if (!otpSessionId.value) {
    errorMessage.value = 'No OTP session found. Please login again.'
  }
})

const handleVerify = async () => {
  errorMessage.value = ''
  if (code.value.length !== 6) {
    errorMessage.value = 'Please enter a valid 6-digit OTP code'
    return
  }

  loading.value = true
  try {
    await authStore.verifyOtp(otpSessionId.value, code.value)
    router.push(authStore.isStudent ? '/student' : '/dashboard')
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Invalid OTP. Please try again.'
  } finally {
    loading.value = false
  }
}

const resendOTP = () => {
  alert('OTP resend functionality coming soon!')
}
</script>
