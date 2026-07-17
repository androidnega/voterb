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
            <h1 class="setup-title">You're all set</h1>
          </div>
        </div>
      </header>

      <div class="step-heading">
        <h2>Sign in with your index number</h2>
        <p>
          Faculty, department, and level setup is no longer required.
          Enter your index on the login page — if you are on an approved voter register,
          you will receive an OTP and go straight to your eligible elections.
        </p>
      </div>

      <footer class="setup-actions">
        <button type="button" class="btn-main" @click="goStudent">
          Go to my elections
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const goStudent = async () => {
  authStore.syncOnboardingFlag()
  await router.replace('/student')
}

onMounted(goStudent)
</script>

<style scoped>
.onboarding-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background:
    radial-gradient(circle at top left, rgba(61, 79, 68, 0.08), transparent 40%),
    #f7f6f2;
}

.setup-card {
  width: min(28rem, 100%);
  background: #fff;
  border: 1px solid #ebeae4;
  border-radius: 1.25rem;
  padding: 1.5rem;
  box-shadow: 0 12px 40px rgba(28, 28, 28, 0.06);
}

.setup-head { margin-bottom: 1.25rem; }
.setup-brand { display: flex; gap: 0.85rem; align-items: center; }
.setup-logo {
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 0.85rem;
  display: grid;
  place-items: center;
  background: #ecfdf5;
  color: #0f766e;
}
.setup-logo svg { width: 1.25rem; height: 1.25rem; }
.setup-eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #8a8a8a;
}
.setup-title {
  margin: 0.15rem 0 0;
  font-size: 1.35rem;
  font-weight: 800;
  color: #1c1c1c;
}
.step-heading h2 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 750;
}
.step-heading p {
  margin: 0.45rem 0 0;
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
}
.setup-actions { margin-top: 1.4rem; }
.btn-main {
  width: 100%;
  border: none;
  border-radius: 0.85rem;
  padding: 0.85rem 1rem;
  background: #1c1c1c;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
</style>
