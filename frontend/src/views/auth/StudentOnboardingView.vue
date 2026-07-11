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
        <p class="setup-step-count">Step {{ currentStep }} of {{ steps.length }}</p>
      </header>

      <nav class="step-rail" aria-label="Progress">
        <template v-for="(step, index) in steps" :key="step.id">
          <button
            type="button"
            class="step-node"
            :class="{
              'is-active': currentStep === index + 1,
              'is-done': currentStep > index + 1,
            }"
            :disabled="index + 1 > currentStep"
            :aria-current="currentStep === index + 1 ? 'step' : undefined"
            @click="goToStep(index + 1)"
          >
            <span class="step-node-num">{{ index + 1 }}</span>
            <span class="step-node-label">{{ step.short }}</span>
          </button>
          <span
            v-if="index < steps.length - 1"
            class="step-connector"
            :class="{ 'is-done': currentStep > index + 1 }"
            aria-hidden="true"
          ></span>
        </template>
      </nav>

      <div class="step-heading">
        <h2>{{ activeStepMeta.title }}</h2>
        <p>{{ activeStepMeta.subtitle }}</p>
      </div>

      <form class="setup-form" @submit.prevent="handlePrimaryAction">
        <div v-if="loadingOptions" class="setup-loading">
          <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
          <span>Loading…</span>
        </div>

        <template v-else>
          <Transition :name="slideTransition" mode="out-in">
            <div :key="currentStep" class="setup-body">
              <OnboardingStepFields
                v-model:form="form"
                :step-id="activeStepMeta.id"
                :index-number="indexNumber"
                :levels="levels"
                :faculties-data="faculties"
                :departments-data="departments"
                :faculty-name="facultyName"
                :department-name="departmentName"
                :level-name="levelName"
              />
              <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
            </div>
          </Transition>

          <footer class="setup-actions">
            <button
              v-if="currentStep > 1"
              type="button"
              class="btn-ghost"
              @click="prevStep"
            >
              Back
            </button>
            <button type="submit" class="btn-main" :disabled="loading || loadingOptions">
              <i v-if="loading" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
              {{ loading ? 'Saving…' : isLastStep ? 'Finish' : 'Continue' }}
            </button>
          </footer>
        </template>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onboardingApi, academicApi } from '@/api/academic'
import OnboardingStepFields from '@/components/onboarding/OnboardingStepFields.vue'
import { formatIndexDisplay } from '@/utils/index'

const router = useRouter()
const authStore = useAuthStore()

const steps = [
  { id: 'profile', short: 'Details', title: 'Your details', subtitle: 'Tell us how to reach you.' },
  { id: 'academic', short: 'Faculty', title: 'Your faculty', subtitle: 'Select where you belong on campus.' },
  { id: 'finish', short: 'Confirm', title: 'Confirm', subtitle: 'Double-check everything looks right.' },
]

const currentStep = ref(1)
const stepDirection = ref(1)
const levels = ref([])
const faculties = ref([])
const departments = ref([])
const loading = ref(false)
const loadingOptions = ref(true)
const errorMessage = ref('')

const form = ref({
  full_name: '',
  phone_number: '',
  faculty_uuid: null,
  department_uuid: null,
  level_uuid: null,
})

const isLastStep = computed(() => currentStep.value === steps.length)
const activeStepMeta = computed(() => steps[currentStep.value - 1] || steps[0])
const slideTransition = computed(() =>
  stepDirection.value > 0 ? 'slide-next' : 'slide-prev'
)

const facultyName = computed(() =>
  faculties.value.find((f) => String(f.uuid) === String(form.value.faculty_uuid))?.name || '—'
)
const departmentName = computed(() =>
  departments.value.find((d) => String(d.uuid) === String(form.value.department_uuid))?.name || '—'
)
const levelName = computed(() =>
  levels.value.find((l) => String(l.uuid) === String(form.value.level_uuid))?.name || '—'
)
const indexNumber = computed(() => formatIndexDisplay(authStore.user?.index_number))
const optionsLoaded = computed(
  () => faculties.value.length > 0 && departments.value.length > 0 && levels.value.length > 0
)

const loadAcademicOptions = async () => {
  try {
    const { data } = await onboardingApi.getOptions()
    return {
      faculties: data.faculties || [],
      departments: data.departments || [],
      levels: data.levels || [],
    }
  } catch (primaryError) {
    console.warn('Onboarding options failed, using elections API fallback:', primaryError)
    const params = { active_only: 'true' }
    const [facultyRes, departmentRes, levelRes] = await Promise.all([
      academicApi.faculties(params),
      academicApi.departments(params),
      academicApi.levels(),
    ])
    return {
      faculties: facultyRes.data || [],
      departments: departmentRes.data || [],
      levels: levelRes.data || [],
    }
  }
}

const fetchOnboardingOptions = async () => {
  loadingOptions.value = true
  errorMessage.value = ''
  try {
    if (!authStore.initialized) await authStore.initialize()
    if (!authStore.isAuthenticated) {
      await router.replace('/login')
      return
    }

    const options = await loadAcademicOptions()
    faculties.value = options.faculties
    departments.value = options.departments
    levels.value = options.levels

    if (!optionsLoaded.value) {
      errorMessage.value = 'No faculty, department, or level data is available yet. Please try again later.'
    }
  } catch (error) {
    console.error('Failed to load onboarding options:', error)
    if (error.response?.status === 401) {
      authStore.clearLocalStorage()
      await router.replace('/login')
      return
    }
    const status = error.response?.status
    if (!status || status >= 500) {
      errorMessage.value = 'Could not reach the server. Make sure the backend is running, then refresh.'
    } else {
      errorMessage.value = 'Could not load academic options. Please refresh.'
    }
  } finally {
    loadingOptions.value = false
  }
}

const validateStep = (step) => {
  errorMessage.value = ''
  if (step === 1) {
    if (!form.value.full_name.trim()) {
      errorMessage.value = 'Please enter your full name.'
      return false
    }
    if (!form.value.phone_number.trim()) {
      errorMessage.value = 'Please enter your phone number.'
      return false
    }
  }
  if (step === 2) {
    if (!optionsLoaded.value) {
      errorMessage.value = 'Academic options are not loaded. Refresh the page and ensure the backend is running.'
      return false
    }
    if (!String(form.value.faculty_uuid || '').trim()
      || !String(form.value.department_uuid || '').trim()
      || !String(form.value.level_uuid || '').trim()) {
      errorMessage.value = 'Please select faculty, department, and level.'
      return false
    }
  }
  return true
}

const goToStep = (step) => {
  if (step < currentStep.value) {
    stepDirection.value = -1
    currentStep.value = step
    errorMessage.value = ''
  }
}

const nextStep = () => {
  if (!validateStep(currentStep.value)) return
  if (currentStep.value < steps.length) {
    stepDirection.value = 1
    currentStep.value += 1
    errorMessage.value = ''
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    stepDirection.value = -1
    currentStep.value -= 1
    errorMessage.value = ''
  }
}

const submitOnboarding = async () => {
  if (!validateStep(2)) {
    stepDirection.value = 1
    currentStep.value = 2
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await onboardingApi.complete(form.value)
    if (data.user) authStore.user = data.user
    authStore.requiresOnboarding = false
    authStore.isNewUser = false
    localStorage.removeItem('is_new_user')
    localStorage.removeItem('requires_onboarding')
    await router.replace('/student')
  } catch (error) {
    console.error('Onboarding failed:', error)
    errorMessage.value = error.response?.data?.error || 'Failed to complete onboarding.'
  } finally {
    loading.value = false
  }
}

const handlePrimaryAction = () => {
  if (isLastStep.value) submitOnboarding()
  else nextStep()
}

onMounted(fetchOnboardingOptions)
</script>

<style scoped>
.onboarding-page {
  --ob-bg: #f4f3ef;
  --ob-card: #fdfcfa;
  --ob-input: #ffffff;
  --ob-border: #e5e2db;
  --ob-text: #1c1917;
  --ob-muted: #78716c;

  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  background: var(--ob-bg);
}

.setup-card {
  width: 100%;
  max-width: 24rem;
  background: var(--ob-card);
  border: 1px solid var(--ob-border);
  border-radius: 0.8rem;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.04), 0 12px 40px rgba(28, 25, 23, 0.06);
  padding: 1.05rem;
}

.setup-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.7rem;
  margin-bottom: 0.9rem;
}

.setup-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.setup-logo {
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ob-input);
  border: 1px solid var(--ob-border);
  color: var(--vb-accent, #0f766e);
}

.setup-logo svg {
  width: 0.95rem;
  height: 0.95rem;
}

.setup-eyebrow {
  margin: 0;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ob-muted);
}

.setup-title {
  margin: 0.12rem 0 0;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ob-text);
}

.setup-step-count {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--ob-muted);
  white-space: nowrap;
  padding-top: 0.15rem;
}

/* Step rail */
.step-rail {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  margin-bottom: 0.9rem;
  padding: 0 0.1rem;
}

.step-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  border: none;
  background: transparent;
  padding: 0;
  cursor: default;
  min-width: 3.25rem;
}

.step-node:disabled {
  cursor: default;
}

.step-node.is-done {
  cursor: pointer;
}

.step-node-num {
  width: 1.65rem;
  height: 1.65rem;
  aspect-ratio: 1;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1.5px solid var(--ob-border);
  background: var(--ob-input);
  color: var(--ob-muted);
  transition: all 0.2s ease;
}

.step-node.is-active .step-node-num {
  border-color: var(--vb-accent, #0f766e);
  background: var(--vb-accent, #0f766e);
  color: #fff;
  box-shadow: 0 0 0 2px var(--vb-accent-soft, #ecfdf5);
}

.step-node.is-done .step-node-num {
  border-color: var(--vb-accent-border, #99f6e4);
  background: var(--vb-accent-soft, #ecfdf5);
  color: var(--vb-accent, #0f766e);
}

.step-node-label {
  font-size: 0.56rem;
  font-weight: 600;
  color: var(--ob-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.step-node.is-active .step-node-label {
  color: var(--ob-text);
}

.step-connector {
  flex: 1;
  height: 1.5px;
  background: var(--ob-border);
  margin-top: 0.78rem;
  min-width: 1rem;
  max-width: 2rem;
  transition: background 0.2s ease;
}

.step-connector.is-done {
  background: var(--vb-accent-border, #99f6e4);
}

.step-heading {
  margin-bottom: 0.85rem;
}

.step-heading h2 {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--ob-text);
}

.step-heading p {
  margin: 0.2rem 0 0;
  font-size: 0.72rem;
  color: var(--ob-muted);
}

.setup-form {
  display: flex;
  flex-direction: column;
  min-height: 8.5rem;
}

.setup-body {
  flex: 1;
}

.setup-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  color: var(--ob-muted);
  font-size: 0.75rem;
  min-height: 6rem;
}

.setup-loading i {
  color: var(--vb-accent, #0f766e);
}

.form-error {
  margin-top: 0.7rem;
  padding: 0.5rem 0.65rem;
  border-radius: 0.5rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  font-size: 0.72rem;
}

.setup-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.4rem;
  margin-top: 0.9rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--ob-border);
}

.btn-main,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  padding: 0.52rem 0.85rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.btn-main {
  border: none;
  background: var(--vb-accent, #0f766e);
  color: #fff;
  min-width: 6rem;
}

.btn-main:hover:not(:disabled) {
  background: var(--vb-accent-hover, #0d6b64);
}

.btn-main:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-ghost {
  margin-right: auto;
  border: 1px solid var(--ob-border);
  background: var(--ob-input);
  color: var(--ob-muted);
}

.btn-ghost:hover {
  border-color: #d6d3cd;
  color: var(--ob-text);
}

/* Transitions */
.slide-next-enter-active,
.slide-next-leave-active,
.slide-prev-enter-active,
.slide-prev-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.slide-next-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.slide-next-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.slide-prev-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.slide-prev-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

@media (min-width: 769px) {
  .onboarding-page {
    padding: 2.5rem 1.5rem;
  }

  .setup-card {
    padding: 1.4rem 1.55rem;
    max-width: 25rem;
  }

  .setup-title {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .onboarding-page {
    padding: 0;
    align-items: stretch;
  }

  .setup-card {
    min-height: 100dvh;
    border-radius: 0;
    border-left: none;
    border-right: none;
    box-shadow: none;
    padding: 0.95rem 0.9rem 1.15rem;
  }

  .step-node {
    min-width: 2.75rem;
  }

  .step-node-num {
    width: 1.5rem;
    height: 1.5rem;
    font-size: 0.68rem;
  }

  .step-connector {
    margin-top: 0.7rem;
  }

  .step-node-label {
    font-size: 0.52rem;
  }

  .btn-main {
    flex: 1;
  }
}
</style>
