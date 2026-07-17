<template>
  <div class="auth-page">
    <div class="auth-shell">
      <div class="auth-brand">
        <div class="auth-mark">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.25" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
        </div>
        <h1 class="auth-title">Welcome back</h1>
        <p class="auth-subtitle">Sign in to continue to VoteBridge</p>
      </div>

      <div class="auth-card">
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="field">
            <label class="field-label">
              {{ isStaffLogin ? 'Email address' : 'Index number' }}
            </label>
            <div class="field-control">
              <span class="field-icon" aria-hidden="true">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
              </span>
              <input
                v-model="identifier"
                :type="isStaffLogin ? 'email' : 'text'"
                class="field-input"
                :placeholder="isStaffLogin ? 'admin@voterb.com' : 'BCITS24047'"
                autocomplete="username"
                :disabled="loading"
              />
            </div>
          </div>

          <div v-if="isStaffLogin" class="field">
            <label class="field-label">Password</label>
            <div class="field-control">
              <span class="field-icon" aria-hidden="true">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </span>
              <input
                v-model="password"
                :type="showPasswordText ? 'text' : 'password'"
                class="field-input has-toggle"
                placeholder="••••••••"
                autocomplete="current-password"
                :disabled="loading"
              />
              <button
                type="button"
                class="field-toggle"
                @click="showPasswordText = !showPasswordText"
              >
                <svg v-if="showPasswordText" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="auth-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            {{ errorMessage }}
          </div>

          <button type="submit" class="auth-submit" :disabled="loading">
            <svg v-if="loading" class="auth-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Signing in…' : 'Sign in' }}
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
  width: min(100%, 24rem);
}

.auth-brand {
  text-align: center;
  margin-bottom: 1.35rem;
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
  width: 1.35rem;
  height: 1.35rem;
}

.auth-title {
  margin: 0.9rem 0 0.3rem;
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.auth-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: #78716c;
}

.auth-card {
  background: #fff;
  border: 1px solid #e8e6e1;
  border-radius: 1.15rem;
  padding: 1.35rem 1.25rem 1.25rem;
  box-shadow: 0 8px 28px rgba(28, 25, 23, 0.045);
}

.auth-form {
  display: grid;
  gap: 1rem;
}

.field-label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #44403c;
}

.field-control {
  position: relative;
}

.field-icon {
  position: absolute;
  inset: 0 auto 0 0.8rem;
  display: inline-flex;
  align-items: center;
  color: #a8a29e;
  pointer-events: none;
}

.field-icon svg,
.field-toggle svg {
  width: 1.05rem;
  height: 1.05rem;
}

.field-input {
  width: 100%;
  padding: 0.75rem 0.9rem 0.75rem 2.55rem;
  border: 1px solid #e7e5e4;
  border-radius: 0.75rem;
  background: #fafaf9;
  color: #1c1917;
  font-size: 0.9rem;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.field-input.has-toggle {
  padding-right: 2.6rem;
}

.field-input::placeholder {
  color: #a8a29e;
}

.field-input:focus {
  outline: none;
  border-color: #99f6e4;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1);
}

.field-input:disabled {
  opacity: 0.6;
}

.field-toggle {
  position: absolute;
  inset: 0 0.55rem 0 auto;
  display: inline-flex;
  align-items: center;
  border: none;
  background: transparent;
  color: #a8a29e;
  cursor: pointer;
  padding: 0 0.25rem;
}

.field-toggle:hover {
  color: #57534e;
}

.auth-error {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.7rem 0.85rem;
  border-radius: 0.7rem;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 0.82rem;
  line-height: 1.4;
}

.auth-error svg {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.auth-submit {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  margin-top: 0.2rem;
  padding: 0.8rem 1rem;
  border: none;
  border-radius: 0.75rem;
  background: #0f766e;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.auth-submit:hover:not(:disabled) {
  background: #0d6b64;
}

.auth-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auth-spin {
  width: 1rem;
  height: 1rem;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
