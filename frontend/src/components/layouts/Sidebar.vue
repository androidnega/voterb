<template>
  <div
    v-if="isMobileMenuOpen"
    class="sidebar-backdrop fixed inset-0 bg-black/40 z-40 lg:hidden"
    @click="closeMobileMenu"
  ></div>

  <aside
    class="vb-sidebar soft-sidebar"
    :class="[
      isCollapsed && !isMobileMenuOpen ? 'is-collapsed' : '',
      isMobileMenuOpen ? 'is-open' : '',
      showLabels ? 'has-labels' : '',
    ]"
  >
    <div class="soft-sidebar__brand">
      <router-link :to="homeRoute" class="soft-sidebar__logo" @click="closeMobileMenu">
        <svg viewBox="0 0 40 40" class="soft-sidebar__mark" aria-hidden="true">
          <circle cx="20" cy="20" r="7" fill="currentColor" />
          <g stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
            <line v-for="i in 12" :key="i" :x1="20" :y1="4" :x2="20" :y2="9" :transform="`rotate(${(i - 1) * 30} 20 20)`" />
          </g>
        </svg>
        <span v-if="showLabels" class="soft-sidebar__title">VoterB</span>
      </router-link>
    </div>

    <nav class="soft-sidebar__nav">
      <ul class="soft-sidebar__list">
        <li v-for="item in menuItems" :key="item.path">
          <router-link
            :to="item.path"
            class="soft-sidebar__link"
            :class="{ 'is-active': isActive(item.path) }"
            :title="item.label"
            @click="closeMobileMenu"
          >
            <span class="soft-sidebar__icon">
              <i :class="item.icon"></i>
            </span>
            <span v-if="showLabels" class="soft-sidebar__text">{{ item.label }}</span>
            <span v-else class="sr-only">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="soft-sidebar__footer">
      <router-link
        v-if="showSettings"
        to="/settings"
        class="soft-sidebar__link"
        :class="{ 'is-active': isActive('/settings') }"
        title="Settings"
        @click="closeMobileMenu"
      >
        <span class="soft-sidebar__icon"><i class="fas fa-cog"></i></span>
        <span v-if="showLabels" class="soft-sidebar__text">Settings</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  isMobileMenuOpen: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close-mobile'])

const route = useRoute()
const authStore = useAuthStore()
const isCollapsed = inject('sidebarCollapsed')
const isDesktop = ref(typeof window !== 'undefined' ? window.innerWidth >= 1024 : true)

const syncViewport = () => {
  isDesktop.value = window.innerWidth >= 1024
}

const homeRoute = computed(() => authStore.homeRoute || '/dashboard')
// Never render label text while the mobile drawer is closed — overflowing "VoterB" was peeking on screen.
const showLabels = computed(() => {
  if (props.isMobileMenuOpen) return true
  if (!isDesktop.value) return false
  return !isCollapsed.value
})

onMounted(() => {
  syncViewport()
  window.addEventListener('resize', syncViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncViewport)
})

const showSettings = computed(() => {
  const role = authStore.roleName
  return role === 'super_admin' || authStore.isSuperAdmin
})

const menuItems = computed(() => {
  const role = authStore.roleName

  if (authStore.isStudent) {
    return [{ path: '/student', label: 'My Elections', icon: 'fas fa-th-large' }]
  }

  if (role === 'super_admin' || authStore.isSuperAdmin) {
    return [
      { path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' },
      { path: '/institutions', label: 'Institutions', icon: 'fas fa-university' },
      { path: '/users', label: 'Users', icon: 'fas fa-users' },
      { path: '/categories', label: 'Categories', icon: 'fas fa-layer-group' },
      { path: '/audit', label: 'Audit', icon: 'fas fa-clipboard-list' },
      { path: '/operations', label: 'Operations', icon: 'fas fa-server' },
    ]
  }

  if (role === 'admin' || authStore.isMainEC) {
    return [
      { path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' },
      { path: '/approvals', label: 'Dual Approvals', icon: 'fas fa-check-double' },
      { path: '/categories', label: 'Categories', icon: 'fas fa-layer-group' },
      { path: '/register', label: 'Register', icon: 'fas fa-book' },
      { path: '/sub-ec', label: 'Sub ECs', icon: 'fas fa-sitemap' },
      { path: '/elections', label: 'Elections', icon: 'fas fa-calendar-check' },
      { path: '/results', label: 'Results', icon: 'fas fa-chart-bar' },
      { path: '/strongroom', label: 'Strongroom', icon: 'fas fa-shield-alt' },
      { path: '/fraud', label: 'Fraud', icon: 'fas fa-user-shield' },
      { path: '/ussd', label: 'USSD', icon: 'fas fa-phone' },
      { path: '/audit', label: 'Audit', icon: 'fas fa-clipboard-list' },
    ]
  }

  if (role === 'sub_ec' || authStore.isSubEC) {
    return [
      { path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' },
      { path: '/elections', label: 'Elections', icon: 'fas fa-calendar-check' },
      { path: '/results', label: 'Results', icon: 'fas fa-chart-bar' },
      { path: '/audit', label: 'Audit', icon: 'fas fa-clipboard-list' },
    ]
  }

  if (role === 'auditor' || authStore.isAuditor) {
    return [
      { path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' },
      { path: '/elections', label: 'Elections', icon: 'fas fa-calendar-check' },
      { path: '/results', label: 'Results', icon: 'fas fa-chart-bar' },
      { path: '/strongroom', label: 'Strongroom', icon: 'fas fa-shield-alt' },
      { path: '/audit', label: 'Audit', icon: 'fas fa-clipboard-list' },
    ]
  }

  return [{ path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' }]
})

const isActive = (path) => {
  if (path === '/dashboard') return route.path === '/dashboard'
  if (path === '/student') {
    return route.path === '/student' || route.path.startsWith('/student/')
  }
  return route.path === path || route.path.startsWith(`${path}/`)
}

const closeMobileMenu = () => {
  emit('close-mobile')
}
</script>

<style scoped>
.soft-sidebar {
  position: fixed;
  top: 0.85rem;
  left: 0.85rem;
  bottom: 0.85rem;
  z-index: 50;
  width: 5.25rem;
  display: flex;
  flex-direction: column;
  background: var(--vb-sidebar-bg);
  border-radius: 1.75rem;
  box-shadow: var(--vb-card-shadow);
  padding: 1rem 0.65rem;
  transform: translateX(calc(-100% - 1.5rem));
  transition: transform 0.3s ease, width 0.3s ease;
  overflow: hidden;
}

@media (max-width: 1023px) {
  .soft-sidebar:not(.is-open) {
    visibility: hidden;
    pointer-events: none;
  }
}

@media (min-width: 1024px) {
  .soft-sidebar {
    transform: translateX(0);
  }

  .soft-sidebar:not(.is-collapsed) {
    width: 15rem;
    padding: 1.1rem 0.8rem;
  }
}

.soft-sidebar.is-open {
  transform: translateX(0);
  width: min(17rem, calc(100vw - 1.7rem));
}

.soft-sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  min-height: 2.5rem;
}

.soft-sidebar.has-labels .soft-sidebar__brand {
  justify-content: flex-start;
  padding: 0 0.25rem;
}

.soft-sidebar__logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--vb-accent);
  min-width: 0;
}

.soft-sidebar__mark {
  width: 2.2rem;
  height: 2.2rem;
  flex-shrink: 0;
}

.soft-sidebar__title {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--vb-ink);
  letter-spacing: -0.02em;
}

.soft-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 0.15rem 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.soft-sidebar__nav::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}

.soft-sidebar__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}

.soft-sidebar.has-labels .soft-sidebar__list {
  align-items: stretch;
}

.soft-sidebar__link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  color: var(--vb-sidebar-text);
  text-decoration: none;
  border: none;
  background: transparent;
  cursor: pointer;
  width: 100%;
  padding: 0.15rem;
  border-radius: 9999px;
  transition: color 0.15s ease, background 0.15s ease;
}

.soft-sidebar.has-labels .soft-sidebar__link {
  justify-content: flex-start;
  padding: 0.28rem 0.45rem 0.28rem 0.28rem;
}

.soft-sidebar__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  flex-shrink: 0;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}

.soft-sidebar__text {
  font-size: 0.875rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.soft-sidebar__link:hover {
  color: var(--vb-sidebar-text-hover);
}

.soft-sidebar__link:hover .soft-sidebar__icon {
  background: var(--vb-sidebar-hover-bg);
}

.soft-sidebar__link.is-active {
  color: var(--vb-ink);
}

.soft-sidebar__link.is-active .soft-sidebar__icon {
  background: var(--vb-sidebar-active-bg);
  color: var(--vb-sidebar-active-text);
  box-shadow: 0 6px 14px rgba(28, 28, 28, 0.14);
}

.soft-sidebar__footer {
  margin-top: auto;
  padding-top: 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}

.soft-sidebar.has-labels .soft-sidebar__footer {
  align-items: stretch;
}
</style>
