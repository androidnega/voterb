<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <div class="flex justify-center">
          <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
        </div>
        <h2 class="mt-6 text-3xl font-bold text-gray-900">VoterB</h2>
        <p class="mt-2 text-sm text-gray-600">Secure Campus Election Platform</p>
      </div>

      <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Index Number</label>
            <input
              v-model="identifier"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="BC/ITS/24/047"
              autocomplete="username"
            />
          </div>

          <div v-if="showPassword" class="transition-all duration-300">
            <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              v-model="password"
              type="password"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="••••••••"
              autocomplete="current-password"
            />
          </div>

          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Signing In...' : 'Sign In' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const identifier = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  errorMessage.value = ''
  const trimmedIdentifier = identifier.value.trim()

  if (!trimmedIdentifier) {
    errorMessage.value = 'Please enter your index number'
    return
  }

  loading.value = true

  try {
    const result = await authStore.login(
      trimmedIdentifier,
      showPassword.value ? password.value : undefined
    )

    if (result?.requires_password) {
      showPassword.value = true
      loading.value = false
      return
    }

    if (result?.requires_otp) {
      router.push({
        path: '/otp',
        query: { sessionId: authStore.pendingOtp },
      })
    } else if (result?.success) {
      router.push('/dashboard')
    } else {
      errorMessage.value = 'Login failed. Please try again.'
    }
  } catch (error) {
    console.error('Login error:', error)
    if (error.response?.data?.requires_password) {
      showPassword.value = true
      errorMessage.value = ''
    } else if (error.response?.data?.error) {
      errorMessage.value = error.response.data.error
    } else if (error.request) {
      errorMessage.value = 'Cannot connect to server. Make sure the backend is running.'
    } else {
      errorMessage.value = 'An unexpected error occurred.'
    }
  } finally {
    loading.value = false
  }
}
</script>
