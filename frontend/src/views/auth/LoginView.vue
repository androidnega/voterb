<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-emerald-50/30 p-4">
    <!-- Animated background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div v-for="i in 4" :key="i" class="absolute rounded-full bg-emerald-200/10 animate-float"
        :style="{
          width: (Math.random() * 200 + 100) + 'px',
          height: (Math.random() * 200 + 100) + 'px',
          top: (Math.random() * 80 + 10) + '%',
          left: (Math.random() * 80 + 10) + '%',
          animationDuration: (Math.random() * 10 + 15) + 's',
          animationDelay: (Math.random() * 5) + 's'
        }"
      ></div>
    </div>

    <div class="relative w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="flex justify-center">
          <div class="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-2xl flex items-center justify-center shadow-xl shadow-emerald-500/25">
            <svg class="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
        </div>
        <h2 class="mt-4 text-3xl font-bold text-gray-900 tracking-tight">Welcome Back</h2>
        <p class="mt-1.5 text-sm text-gray-500">Enter your credentials to continue</p>
      </div>

      <!-- Login Card -->
      <div class="bg-white/80 backdrop-blur-xl rounded-2xl border border-white/60 shadow-2xl p-6 sm:p-8">
        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Identifier Field -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              {{ isStaffLogin ? 'Email Address' : 'Index Number' }}
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
              </div>
              <input
                v-model="identifier"
                :type="isStaffLogin ? 'email' : 'text'"
                class="w-full pl-10 pr-4 py-3 bg-gray-50/80 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400"
                :placeholder="isStaffLogin ? 'admin@voterb.com' : 'BCITS24047'"
                autocomplete="username"
                :disabled="loading"
              />
            </div>
          </div>

          <!-- Password Field (Staff Only) -->
          <div v-if="isStaffLogin" class="transition-all duration-300">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </div>
              <input
                v-model="password"
                :type="showPasswordText ? 'text' : 'password'"
                class="w-full pl-10 pr-12 py-3 bg-gray-50/80 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400"
                placeholder="••••••••"
                autocomplete="current-password"
                :disabled="loading"
              />
              <button
                type="button"
                @click="showPasswordText = !showPasswordText"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg v-if="showPasswordText" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center gap-2.5">
            <svg class="w-5 h-5 flex-shrink-0 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {{ errorMessage }}
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex justify-center items-center py-3.5 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-medium rounded-xl hover:shadow-xl hover:shadow-emerald-500/30 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
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
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const identifier = ref('')
const password = ref('')
const showPassword = ref(false)
const showPasswordText = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const isStaffLogin = computed(() => identifier.value.includes('@') || showPassword.value)

watch(identifier, (value) => {
  if (value.includes('@')) {
    showPassword.value = true
  }
})

const handleLogin = async () => {
  errorMessage.value = ''
  const trimmedIdentifier = identifier.value.trim()

  if (!trimmedIdentifier) {
    errorMessage.value = isStaffLogin.value
      ? 'Please enter your email address'
      : 'Please enter your index number'
    return
  }

  if (isStaffLogin.value && !password.value) {
    showPassword.value = true
    errorMessage.value = 'Please enter your password'
    return
  }

  loading.value = true

  try {
    const result = await authStore.login(
      trimmedIdentifier,
      isStaffLogin.value ? password.value : undefined
    )

    if (result?.requires_password) {
      showPassword.value = true
      return
    }

    if (result?.requires_otp) {
      router.push({
        path: '/otp',
        query: { sessionId: authStore.pendingOtp },
      })
    } else if (result?.success) {
      await router.replace(result.homeRoute || authStore.homeRoute)
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

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; }
  50% { transform: translateY(-30px) scale(1.1); opacity: 0.6; }
}

.animate-float {
  animation: float ease-in-out infinite;
}
</style>
