<template>
  <div class="student-shell">
    <header class="student-topbar">
      <div class="student-topbar-inner">
        <router-link to="/student" class="student-brand">
          <span class="student-brand-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </span>
          <span class="student-brand-text">VoteBridge</span>
        </router-link>

        <div class="student-topbar-meta">
          <span v-if="indexDisplay" class="student-index">{{ indexDisplay }}</span>
          <button type="button" class="student-signout" @click="handleLogout">
            Sign out
          </button>
        </div>
      </div>
    </header>

    <main class="student-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { formatIndexDisplay } from '@/utils/index'

const router = useRouter()
const authStore = useAuthStore()

const indexDisplay = computed(() => formatIndexDisplay(authStore.user?.index_number))

async function handleLogout() {
  await authStore.logout()
  await router.replace('/login')
}
</script>

<style scoped>
.student-shell {
  --sd-bg: #f4f3ef;
  --sd-surface: #fdfcfa;
  --sd-border: #e5e2db;
  --sd-text: #1c1917;
  --sd-muted: #78716c;

  min-height: 100vh;
  min-height: 100dvh;
  background: var(--sd-bg);
  color: var(--sd-text);
}

.student-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(253, 252, 250, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--sd-border);
}

.student-topbar-inner {
  max-width: 42rem;
  margin: 0 auto;
  padding: 0.85rem 1.1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.student-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
  color: inherit;
}

.student-brand-icon {
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid var(--sd-border);
  color: var(--vb-accent, #0f766e);
}

.student-brand-icon svg {
  width: 1rem;
  height: 1rem;
}

.student-brand-text {
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.student-topbar-meta {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.student-index {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--sd-muted);
  letter-spacing: 0.02em;
}

.student-signout {
  border: 1px solid var(--sd-border);
  background: #fff;
  color: var(--sd-muted);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.4rem 0.7rem;
  border-radius: 0.45rem;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease;
}

.student-signout:hover {
  border-color: #d6d3cd;
  color: var(--sd-text);
}

.student-main {
  max-width: 42rem;
  margin: 0 auto;
  padding: 1.35rem 1.1rem 2rem;
  width: 100%;
}

@media (min-width: 769px) {
  .student-topbar-inner,
  .student-main {
    max-width: 44rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }

  .student-main {
    padding-top: 1.75rem;
    padding-bottom: 2.5rem;
  }
}
</style>
