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

        <div class="student-topbar-actions">
          <StudentNotificationBell />
          <StudentProfileMenu />
        </div>
      </div>
    </header>

    <main class="student-main">
      <router-view v-slot="{ Component, route }">
        <Transition :name="transitionName" mode="out-in">
          <component :is="Component" :key="routeViewKey(route)" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import StudentProfileMenu from '@/components/student/StudentProfileMenu.vue'
import StudentNotificationBell from '@/components/student/StudentNotificationBell.vue'

const router = useRouter()
const transitionName = ref('page-fade')

function routeDepth(path = '') {
  if (path.startsWith('/vote/') && path.includes('/confirmation')) return 4
  if (path.startsWith('/vote/') && path.includes('/ballot')) return 3
  if (path.startsWith('/vote/') && path.includes('/presence')) return 2
  if (path.startsWith('/vote/')) return 1
  if (path.startsWith('/student/results')) return 1
  return 0
}

function routeViewKey(route) {
  // Keep vote flow steps distinct; avoid remounting on minor query changes
  return route.path
}

router.beforeEach((to, from) => {
  const toVote = to.path.startsWith('/vote/')
  const fromVote = from.path.startsWith('/vote/')
  const toStudent = to.path === '/student' || to.path.startsWith('/student/')
  const fromStudent = from.path === '/student' || from.path.startsWith('/student/')

  if (toVote && fromStudent) {
    transitionName.value = 'page-forward'
    return
  }
  if (toStudent && fromVote) {
    transitionName.value = 'page-back'
    return
  }

  const toDepth = routeDepth(to.path)
  const fromDepth = routeDepth(from.path)
  if (toDepth > fromDepth) transitionName.value = 'page-forward'
  else if (toDepth < fromDepth) transitionName.value = 'page-back'
  else transitionName.value = 'page-fade'
})
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

.student-topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-shrink: 0;
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
  position: relative;
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

<style>
/* Unscoped so router-view transition classes reach nested page roots */
.student-shell {
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out-soft: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in-soft: cubic-bezier(0.4, 0, 1, 1);
}

.page-forward-enter-active {
  transition:
    opacity 0.48s var(--ease-out-expo),
    transform 0.52s var(--ease-out-expo),
    filter 0.48s var(--ease-out-expo);
}

.page-forward-leave-active {
  transition:
    opacity 0.28s var(--ease-in-soft),
    transform 0.32s var(--ease-in-out-soft),
    filter 0.28s var(--ease-in-soft);
}

.page-forward-enter-from {
  opacity: 0;
  transform: translate3d(1.75rem, 0.35rem, 0) scale(0.985);
  filter: blur(4px);
}

.page-forward-leave-to {
  opacity: 0;
  transform: translate3d(-1.1rem, -0.2rem, 0) scale(0.99);
  filter: blur(2px);
}

.page-back-enter-active {
  transition:
    opacity 0.45s var(--ease-out-expo),
    transform 0.5s var(--ease-out-expo),
    filter 0.45s var(--ease-out-expo);
}

.page-back-leave-active {
  transition:
    opacity 0.26s var(--ease-in-soft),
    transform 0.3s var(--ease-in-out-soft),
    filter 0.26s var(--ease-in-soft);
}

.page-back-enter-from {
  opacity: 0;
  transform: translate3d(-1.5rem, 0.25rem, 0) scale(0.985);
  filter: blur(4px);
}

.page-back-leave-to {
  opacity: 0;
  transform: translate3d(1.25rem, -0.15rem, 0) scale(0.99);
  filter: blur(2px);
}

.page-fade-enter-active {
  transition:
    opacity 0.4s var(--ease-out-expo),
    transform 0.4s var(--ease-out-expo);
}

.page-fade-leave-active {
  transition:
    opacity 0.24s var(--ease-in-soft),
    transform 0.24s var(--ease-in-out-soft);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translate3d(0, 0.6rem, 0);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translate3d(0, -0.35rem, 0);
}

@media (prefers-reduced-motion: reduce) {
  .page-forward-enter-active,
  .page-forward-leave-active,
  .page-back-enter-active,
  .page-back-leave-active,
  .page-fade-enter-active,
  .page-fade-leave-active {
    transition-duration: 0.01ms !important;
  }

  .page-forward-enter-from,
  .page-forward-leave-to,
  .page-back-enter-from,
  .page-back-leave-to,
  .page-fade-enter-from,
  .page-fade-leave-to {
    transform: none;
    filter: none;
  }
}
</style>
