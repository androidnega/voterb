<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Header -->
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

      <!-- Login Form -->
      <div class="bg-white rounded-lg shadow-md border border-gray-200 p-8">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Identifier Field -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ isStaff ? 'Email Address' : 'Index Number' }}
            </label>
            <input 
              v-model="identifier" 
              :type="isStaff ? 'email' : 'text'"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              :placeholder="isStaff ? 'admin@voterb.com' : 'BC/ITS/24/047'"
              required
            />
          </div>

          <!-- Password Field (Staff Only) -->
          <div v-if="isStaff">
            <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input 
              v-model="password" 
              type="password"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="••••••••"
              required
            />
          </div>

          <!-- Staff Toggle -->
          <div class="flex items-center justify-between bg-gray-50 rounded-lg p-3 border border-gray-200">
            <span class="text-sm font-medium text-gray-700">Staff Access</span>
            <button 
              type="button"
              @click="toggleStaff"
              class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-200 focus:outline-none"
              :class="isStaff ? 'bg-green-600' : 'bg-gray-300'"
            >
              <span 
                class="inline-block w-4 h-4 transform bg-white rounded-full transition-transform duration-200"
                :class="isStaff ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>

          <!-- Error Message -->
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {{ errorMessage }}
          </div>

          <!-- Submit Button -->
          <button 
            type="submit" 
            :disabled="loading"
            class="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Signing In...' : 'Sign In' }}
          </button>

          <!-- Demo Hint -->
          <div class="text-center">
            <p class="text-xs text-gray-500">
              Demo: admin@voterb.com / admin123
            </p>
          </div>
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
const isStaff = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const toggleStaff = () => {
  isStaff.value = !isStaff.value
  identifier.value = ''
  password.value = ''
  errorMessage.value = ''
}

const handleLogin = async () => {
  errorMessage.value = ''
  
  // Validation
  if (isStaff.value) {
    if (!identifier.value || !password.value) {
      errorMessage.value = 'Please enter both email and password'
      return
    }
  } else {
    if (!identifier.value) {
      errorMessage.value = 'Please enter your index number'
      return
    }
  }

  loading.value = true

  try {
    const payload = {
      identifier: identifier.value.trim()
    }
    
    if (isStaff.value) {
      payload.password = password.value
    }

    console.log('🔐 Login payload:', payload)

    const result = await authStore.login(payload.identifier, payload.password)

    console.log('✅ Login result:', result)

    if (result && result.requires_otp) {
      router.push({
        path: '/otp',
        query: { sessionId: authStore.pendingOtp }
      })
    } else if (result && result.success) {
      router.push('/dashboard')
    } else {
      errorMessage.value = 'Login failed. Please try again.'
    }
  } catch (error) {
    console.error('❌ Login error:', error)
    
    if (error.response) {
      const data = error.response.data
      errorMessage.value = data.error || 'Login failed. Please try again.'
    } else if (error.request) {
      errorMessage.value = 'Cannot connect to server. Make sure backend is running.'
    } else {
      errorMessage.value = 'An unexpected error occurred.'
    }
  } finally {
    loading.value = false
  }
}
</script>