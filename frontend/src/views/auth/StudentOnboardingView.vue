<template>
  <div class="onboarding-page">
    <div class="setup-card">
      <header class="setup-head">
        <div class="setup-brand">
          <span class="setup-logo" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </span>
          <div>
            <p class="setup-eyebrow">VoteBridge</p>
            <h1 class="setup-title">Set up your profile</h1>
          </div>
        </div>
      </header>

      <div class="step-heading">
        <h2>Your details</h2>
        <p>Enter your full name and mobile number. Your faculty is assigned by the election committee.</p>
      </div>

      <form class="setup-form" @submit.prevent="submitOnboarding">
        <div class="setup-body">
          <OnboardingStepFields
            v-model:form="form"
            step-id="profile"
            :index-number="indexNumber"
          />
          <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
        </div>

        <footer class="setup-actions">
          <button type="submit" class="btn-main" :disabled="loading">
            <i v-if="loading" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
            {{ loading ? 'Saving…' : 'Continue' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onboardingApi } from '@/api/academic'
import OnboardingStepFields from '@/components/onboarding/OnboardingStepFields.vue'
import { formatIndexDisplay } from '@/utils/index'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')

const form = ref({
  full_name: '',
  phone_number: '',
})

const indexNumber = computed(() => formatIndexDisplay(authStore.user?.index_number))

const submitOnboarding = async () => {
  errorMessage.value = ''
  if (!form.value.full_name.trim()) {
    errorMessage.value = 'Please enter your full name.'
    return
  }
  if (!form.value.phone_number.trim()) {
    errorMessage.value = 'Please enter your phone number.'
    return
  }

  loading.value = true
  try {
    const payload = {
      full_name: form.value.full_name.trim(),
      phone_number: form.value.phone_number.trim(),
    }
    const { data } = await onboardingApi.complete(payload)
    if (data.user) authStore.user = data.user
    else if (authStore.user) authStore.user.onboarding_completed = true
    authStore.isNewUser = false
    authStore.syncOnboardingFlag(authStore.user)
    localStorage.removeItem('is_new_user')
    localStorage.removeItem('requires_onboarding')
    await router.replace('/student')
  } catch (error) {
    console.error('Onboarding failed:', error)
    const data = error.response?.data
    if (data?.error) {
      errorMessage.value = data.error
    } else if (typeof data === 'object' && data) {
      const firstField = Object.keys(data)[0]
      const firstError = Array.isArray(data[firstField]) ? data[firstField][0] : data[firstField]
      errorMessage.value = firstError || 'Failed to complete onboarding.'
    } else {
      errorMessage.value = 'Failed to complete onboarding.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!authStore.initialized) await authStore.initialize()
  if (!authStore.isAuthenticated) {
    await router.replace('/login')
    return
  }
  if (!authStore.needsOnboarding) {
    await router.replace('/student')
  }
})
</script>

<style scoped>
.onboarding-page {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 1.5rem 1rem;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(15, 118, 110, 0.08), transparent),
    #f7f6f3;
}

.setup-card {
  width: min(100%, 24rem);
  background: #fff;
  border: 1px solid #e8e6e1;
  border-radius: 1.15rem;
  padding: 1.35rem 1.25rem 1.25rem;
  box-shadow: 0 10px 40px rgba(28, 25, 23, 0.06);
}

.setup-head {
  margin-bottom: 1.1rem;
}

.setup-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.setup-logo {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #0f766e;
  color: #fff;
  flex-shrink: 0;
}

.setup-logo svg {
  width: 1.25rem;
  height: 1.25rem;
}

.setup-eyebrow {
  margin: 0;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
}

.setup-title {
  margin: 0.1rem 0 0;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.step-heading {
  margin-bottom: 1rem;
}

.step-heading h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 750;
  color: #1c1917;
}

.step-heading p {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #78716c;
}

.setup-form {
  display: grid;
  gap: 1rem;
}

.setup-body {
  display: grid;
  gap: 0.75rem;
}

.form-error {
  margin: 0;
  font-size: 0.78rem;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #f5e6d3;
  border-radius: 0.65rem;
  padding: 0.55rem 0.7rem;
}

.setup-actions {
  display: flex;
  justify-content: stretch;
}

.btn-main {
  width: 100%;
  border: none;
  border-radius: 0.85rem;
  background: #1c1917;
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  padding: 0.85rem 1rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
}

.btn-main:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
