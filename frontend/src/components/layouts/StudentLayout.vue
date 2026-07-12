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

        <StudentProfileMenu />
      </div>
    </header>

    <main class="student-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import StudentProfileMenu from '@/components/student/StudentProfileMenu.vue'
</script>

<style scoped>
.student-shell {
  --sd-bg: #f6f5f2;
  --sd-border: #ebe8e2;
  --sd-text: #1c1917;

  min-height: 100vh;
  min-height: 100dvh;
  background: var(--sd-bg);
  color: var(--sd-text);
}

.student-topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(246, 245, 242, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--sd-border);
}

.student-topbar-inner {
  width: 100%;
  margin: 0 auto;
  padding: 0.7rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.student-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: inherit;
  flex-shrink: 0;
}

.student-brand-icon {
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 0.45rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid var(--sd-border);
  color: var(--vb-accent, #0f766e);
}

.student-brand-icon svg {
  width: 0.9rem;
  height: 0.9rem;
}

.student-brand-text {
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.student-main {
  margin: 0 auto;
  padding: 1.1rem 1rem 2.5rem;
  width: 100%;
}

@media (min-width: 768px) {
  .student-topbar-inner {
    padding: 0.85rem 1.5rem;
  }

  .student-main {
    max-width: 40rem;
    padding: 1.75rem 0 3rem;
  }
}

@media (min-width: 1100px) {
  .student-topbar-inner {
    padding: 0.9rem 2rem;
  }
}
</style>
