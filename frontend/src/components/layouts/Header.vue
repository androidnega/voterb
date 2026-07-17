<template>
  <header class="soft-header">
    <div class="soft-header__left">
      <button
        type="button"
        class="soft-icon-btn soft-icon-btn--menu"
        :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="toggleSidebar"
      >
        <i class="fas fa-bars"></i>
      </button>

      <div class="soft-header__greeting">
        <h1 class="soft-header__title">{{ pageTitle }}</h1>
        <p class="soft-header__subtitle">{{ pageSubtitle }}</p>
      </div>
    </div>

    <div class="soft-header__right">
      <form class="soft-search" @submit.prevent="goSearch">
        <input
          v-model="searchQuery"
          type="search"
          class="soft-search__input"
          placeholder="Search..."
          aria-label="Search"
        />
        <button type="submit" class="soft-search__btn" aria-label="Submit search">
          <i class="fas fa-search"></i>
        </button>
      </form>

      <div class="relative" ref="notificationsRef">
        <button
          type="button"
          class="soft-icon-btn"
          :class="{ 'is-active': showNotifications }"
          aria-label="Notifications"
          @click.stop="toggleNotifications"
        >
          <i class="far fa-bell"></i>
          <span
            v-if="unreadCount > 0"
            class="soft-icon-btn__badge"
            :aria-label="`${unreadCount} unread notifications`"
          >
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </button>

        <div v-if="showNotifications" class="notif-popover">
          <NotificationInbox
            tone="admin"
            :items="notifications"
            :loading="loading"
            :unread-count="unreadCount"
            :now-ms="nowMs"
            @select="handleNotificationClick"
            @mark-all="markAllRead"
          />
        </div>
      </div>
      <div class="header-profile" ref="profileRef">
        <button
          type="button"
          class="header-profile__trigger"
          :aria-expanded="showProfile"
          aria-haspopup="true"
          @click.stop="toggleProfile"
        >
          <span class="header-profile__avatar" aria-hidden="true">{{ initials }}</span>
          <span class="header-profile__meta">
            <span class="header-profile__name">{{ profileName }}</span>
            <span class="header-profile__role">{{ roleLabel }}</span>
          </span>
          <i class="fas fa-chevron-down header-profile__chevron" :class="{ 'is-open': showProfile }" aria-hidden="true"></i>
        </button>

        <div v-if="showProfile" class="header-profile__panel" role="menu">
          <div class="header-profile__head">
            <span class="header-profile__avatar header-profile__avatar--lg" aria-hidden="true">{{ initials }}</span>
            <div>
              <p class="header-profile__panel-name">{{ profileName }}</p>
              <p class="header-profile__panel-email">{{ profileEmail }}</p>
            </div>
          </div>
          <button type="button" class="header-profile__signout" role="menuitem" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i>
            Sign out
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { notificationApi } from '@/api/notifications'
import { displayUserName } from '@/utils/user'
import { useShellPageHeading } from '@/composables/usePageHeading'
import { playNotificationChime, unlockAudio } from '@/utils/beep'
import NotificationInbox from '@/components/notifications/NotificationInbox.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

defineProps({
  sidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['toggle-sidebar'])

const showNotifications = ref(false)
const showProfile = ref(false)
const notificationsRef = ref(null)
const profileRef = ref(null)
const notifications = ref([])
const loading = ref(false)
const searchQuery = ref('')
const nowMs = ref(Date.now())
let interval = null
let clockInterval = null
let knownUnreadIds = new Set()
let audioPrimed = false

const pageMeta = computed(() => {
  const path = route.path

  if (path === '/dashboard') {
    if (authStore.isSuperAdmin) {
      return {
        title: 'Dashboard',
        subtitle: 'Platform users, institutions, and categories',
      }
    }
    if (authStore.isAuditor) {
      return {
        title: 'Dashboard',
        subtitle: 'View-only oversight across elections and audit activity',
      }
    }
    return {
      title: 'Dashboard',
      subtitle: 'Institutional EC dashboard — register, elections, and Sub EC oversight',
    }
  }

  if (path.startsWith('/elections')) {
    return {
      title: 'Elections',
      subtitle: 'Create, schedule, and monitor institutional elections',
    }
  }
  if (path.startsWith('/results')) {
    return {
      title: 'Results',
      subtitle: 'Review, certify, and publish election results',
    }
  }
  if (path.startsWith('/strongroom')) {
    return {
      title: 'Strongroom',
      subtitle: 'Custody committee, seals, and vault access',
    }
  }
  if (path.startsWith('/fraud')) {
    return {
      title: 'Fraud',
      subtitle: 'Suspicious activity and voting anomalies',
    }
  }
  if (path.startsWith('/ussd')) {
    return {
      title: 'USSD',
      subtitle: 'Mobile USSD session health and logs',
    }
  }
  if (path.startsWith('/audit')) {
    return {
      title: 'Audit',
      subtitle: 'Voter device, location, and presence records — ballot choices never shown',
    }
  }
  if (path.startsWith('/users')) {
    return {
      title: 'Users',
      subtitle: 'Platform users and role assignments',
    }
  }
  if (path.startsWith('/settings')) {
    return {
      title: 'Settings',
      subtitle: 'Appearance, feature flags, and maintenance',
    }
  }
  if (path.startsWith('/operations')) {
    return {
      title: 'Operations',
      subtitle: 'System health and infrastructure',
    }
  }
  if (path.startsWith('/register')) {
    return {
      title: 'Register',
      subtitle: 'Institutional voter register assigned to faculty and department categories',
    }
  }
  if (path.startsWith('/categories') || path.startsWith('/academic')) {
    return {
      title: 'Categories',
      subtitle: 'Institution categories for Main EC, plus faculties and departments for Sub ECs',
    }
  }
  if (path.startsWith('/sub-ec') || path.startsWith('/ec-structure')) {
    return {
      title: 'Sub ECs',
      subtitle: 'Propose and manage faculty / department Sub Electoral Commissions',
    }
  }
  if (path.startsWith('/approvals')) {
    return {
      title: 'Approvals',
      subtitle: 'Both Main ECs must approve before a decision is enrolled',
    }
  }
  if (path.startsWith('/institutions')) {
    return {
      title: 'Institutions',
      subtitle: 'Create institutions and attach Main EC accounts',
    }
  }

  return {
    title: 'VoterB',
    subtitle: 'Manage your workspace',
  }
})

const shellHeading = useShellPageHeading(pageMeta)
const pageTitle = computed(() => shellHeading.value.title)
const pageSubtitle = computed(() => shellHeading.value.subtitle)

const profileName = computed(() => displayUserName(authStore.user, 'Administrator'))

const profileEmail = computed(() => authStore.user?.email || '—')

const roleLabel = computed(() => {
  const role = authStore.roleName || authStore.user?.role?.name || 'admin'
  const labels = {
    admin: 'Main EC',
    sub_ec: 'Sub EC',
    super_admin: 'Super Admin',
    auditor: 'Auditor',
    student: 'Student',
    candidate: 'Candidate',
  }
  return labels[role] || String(role).replaceAll('_', ' ')
})

const initials = computed(() => {
  const name = profileName.value.trim()
  if (!name) return 'A'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
})

const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

const allSearchTargets = [
  { match: ['election', 'elections'], path: '/elections', roles: ['admin', 'auditor'] },
  { match: ['result', 'results'], path: '/results', roles: ['admin', 'auditor'] },
  { match: ['strong', 'vault', 'seal'], path: '/strongroom', roles: ['admin', 'auditor', 'super_admin'] },
  { match: ['fraud'], path: '/fraud', roles: ['admin'] },
  { match: ['ussd', 'mobile'], path: '/ussd', roles: ['admin'] },
  { match: ['audit', 'log'], path: '/audit', roles: ['admin', 'auditor', 'super_admin'] },
  { match: ['user', 'users'], path: '/users', roles: ['super_admin'] },
  { match: ['setting', 'theme'], path: '/settings', roles: ['super_admin'] },
  { match: ['register', 'voters'], path: '/register', roles: ['admin'] },
  { match: ['category', 'categories', 'faculty', 'department'], path: '/categories', roles: ['super_admin', 'admin'] },
  { match: ['sub ec', 'sub-ec', 'ec structure'], path: '/sub-ec', roles: ['admin'] },
  { match: ['approval', 'dual'], path: '/approvals', roles: ['admin'] },
  { match: ['institution'], path: '/institutions', roles: ['super_admin'] },
  { match: ['operation', 'ops'], path: '/operations', roles: ['super_admin'] },
  { match: ['dashboard', 'home'], path: '/dashboard', roles: ['admin', 'auditor', 'super_admin'] },
]

const searchTargets = computed(() => {
  const role = authStore.roleName
  return allSearchTargets.filter((t) => {
    if (t.roles.includes(role)) return true
    if (t.roles.includes('super_admin') && authStore.isSuperAdmin) return true
    if (t.roles.includes('admin') && authStore.isElectionManager) return true
    if (t.roles.includes('auditor') && authStore.isAuditor) return true
    return false
  })
})

const goSearch = () => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return
  const hit = searchTargets.value.find((t) => t.match.some((m) => q.includes(m) || m.includes(q)))
  if (hit) {
    router.push(hit.path)
    searchQuery.value = ''
  }
}

const fetchNotifications = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  try {
    const response = await notificationApi.list()
    const next = Array.isArray(response.data) ? response.data : []
    const nextUnread = next.filter((n) => !n.is_read).map((n) => n.uuid)
    const isFirst = knownUnreadIds.size === 0 && notifications.value.length === 0
    const fresh = nextUnread.filter((id) => !knownUnreadIds.has(id))
    notifications.value = next
    knownUnreadIds = new Set(nextUnread)
    if (!isFirst && fresh.length > 0) {
      if (!audioPrimed) {
        unlockAudio()
        audioPrimed = true
      }
      playNotificationChime()
    }
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
  } finally {
    if (!silent) loading.value = false
  }
}

const markAllRead = async () => {
  try {
    await notificationApi.markAllRead()
    notifications.value = notifications.value.map((n) => ({ ...n, is_read: true }))
  } catch (error) {
    console.error('Failed to mark all read:', error)
  }
}

const handleNotificationClick = async (notif) => {
  if (!notif.is_read) {
    try {
      await notificationApi.markRead(notif.uuid)
      notif.is_read = true
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }
  if (notif.link) {
    showNotifications.value = false
    const link = notif.link
    if (typeof link === 'string' && link.startsWith('/')) {
      router.push(link)
    } else {
      window.location.href = link
    }
  }
}

const closeMenus = () => {
  showNotifications.value = false
  showProfile.value = false
}

const toggleNotifications = () => {
  showProfile.value = false
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    unlockAudio()
    audioPrimed = true
    fetchNotifications()
  }
}

const toggleProfile = () => {
  showNotifications.value = false
  showProfile.value = !showProfile.value
}

const handleLogout = async () => {
  showProfile.value = false
  await authStore.logout()
  await router.replace('/login')
}

const toggleSidebar = () => {
  emit('toggle-sidebar')
}

const handleClickOutside = (event) => {
  const inNotifications = notificationsRef.value?.contains(event.target)
  const inProfile = profileRef.value?.contains(event.target)
  if (!inNotifications && !inProfile) closeMenus()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  fetchNotifications()
  // Keep the bell badge current even when the dropdown is closed.
  interval = setInterval(() => fetchNotifications({ silent: true }), 15000)
  clockInterval = setInterval(() => {
    nowMs.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (interval) clearInterval(interval)
  if (clockInterval) clearInterval(clockInterval)
})
</script>

<style scoped>
.soft-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 0.2rem 0 1rem;
  flex-wrap: wrap;
}

.soft-header__left {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  min-width: 0;
  flex: 1 1 auto;
}

.soft-icon-btn--menu {
  margin-top: 0.1rem;
}

.soft-header__greeting {
  min-width: 0;
  flex: 1;
}

.soft-header__title {
  margin: 0;
  font-size: clamp(1.35rem, 5vw, 2rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink);
  line-height: 1.15;
}

.soft-header__subtitle {
  margin: 0.3rem 0 0;
  font-size: 0.84rem;
  color: var(--vb-muted);
  line-height: 1.45;
  max-width: 28rem;
}

.soft-header__right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
  flex-shrink: 0;
}

.soft-search {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 9999px;
  padding: 0.35rem 0.35rem 0.35rem 1.1rem;
  box-shadow: var(--vb-card-shadow);
  min-width: min(100%, 16rem);
  width: clamp(12rem, 28vw, 22rem);
}

.soft-search__input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.9rem;
  color: var(--vb-ink);
  min-width: 0;
}

.soft-search__input::placeholder {
  color: #b0b0b0;
}

.soft-search__btn {
  width: 2.55rem;
  height: 2.55rem;
  border-radius: 9999px;
  border: none;
  background: #1c1c1c;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.soft-icon-btn {
  width: 2.85rem;
  height: 2.85rem;
  border-radius: 9999px;
  border: none;
  background: #fff;
  color: #9a9a9a;
  box-shadow: var(--vb-card-shadow);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  font-size: 1rem;
  flex-shrink: 0;
}

.soft-icon-btn.is-active,
.soft-icon-btn:hover {
  color: var(--vb-ink);
}

.soft-icon-btn__badge {
  position: absolute;
  top: 0.2rem;
  right: 0.15rem;
  min-width: 1.15rem;
  height: 1.15rem;
  padding: 0 0.28rem;
  border-radius: 9999px;
  background: #e11d48;
  color: #fff;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.15rem;
  text-align: center;
  box-shadow: 0 0 0 2px #fff;
}

.notif-popover {
  position: absolute;
  right: 0;
  top: calc(100% + 0.55rem);
  z-index: 50;
  animation: notif-pop 0.18s ease;
}

@keyframes notif-pop {
  from {
    opacity: 0;
    transform: translateY(-6px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 900px) {
  .soft-search {
    display: none;
  }

  .soft-header__subtitle {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .soft-icon-btn {
    width: 2.55rem;
    height: 2.55rem;
  }
}

@media (max-width: 480px) {
  .soft-header {
    gap: 0.65rem;
    padding-bottom: 0.85rem;
  }

  .soft-header__right {
    gap: 0.4rem;
  }

  .header-profile__meta {
    display: none;
  }

  .header-profile__chevron {
    display: none;
  }
}

.header-profile {
  position: relative;
  margin-left: 0.15rem;
}

.header-profile__trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  border: none;
  background: #fff;
  border-radius: 9999px;
  padding: 0.28rem 0.65rem 0.28rem 0.28rem;
  box-shadow: var(--vb-card-shadow);
  cursor: pointer;
  max-width: 14rem;
}

.header-profile__trigger:hover,
.header-profile__trigger[aria-expanded='true'] {
  box-shadow: 0 2px 8px rgba(28, 28, 28, 0.06);
}

.header-profile__avatar {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--vb-accent-soft);
  color: var(--vb-accent);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  flex-shrink: 0;
}

.header-profile__avatar--lg {
  width: 2.55rem;
  height: 2.55rem;
  font-size: 0.75rem;
}

.header-profile__meta {
  display: grid;
  gap: 0.05rem;
  text-align: left;
  min-width: 0;
}

.header-profile__name {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vb-ink);
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 7.5rem;
  text-transform: capitalize;
}

.header-profile__role {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--vb-muted);
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 7.5rem;
  text-transform: capitalize;
}

.header-profile__chevron {
  font-size: 0.55rem;
  color: #b0b0b0;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.header-profile__chevron.is-open {
  transform: rotate(180deg);
}

.header-profile__panel {
  position: absolute;
  right: 0;
  top: calc(100% + 0.65rem);
  width: min(16.5rem, calc(100vw - 1.5rem));
  background: #fff;
  border-radius: 1.1rem;
  box-shadow: 0 12px 32px rgba(28, 28, 28, 0.08);
  border: 1px solid #f0efe9;
  padding: 0.85rem;
  z-index: 40;
}

.header-profile__head {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding-bottom: 0.75rem;
  margin-bottom: 0.65rem;
  border-bottom: 1px solid #f0efe9;
}

.header-profile__panel-name {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.header-profile__panel-email {
  margin: 0.2rem 0 0;
  font-size: 0.72rem;
  color: var(--vb-muted);
  word-break: break-all;
}

.header-profile__signout {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  border: none;
  border-radius: 0.85rem;
  padding: 0.7rem 0.85rem;
  background: #1c1c1c;
  color: #fff;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

.header-profile__signout:hover {
  background: #111;
}
</style>
