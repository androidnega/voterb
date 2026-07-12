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
        <h1 class="soft-header__title">Hello, {{ firstName }}!</h1>
        <p class="soft-header__subtitle">{{ subtitle }}</p>
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

      <div class="relative" ref="messagesRef">
        <button
          type="button"
          class="soft-icon-btn"
          :class="{ 'is-active': showMessages }"
          aria-label="Messages"
          @click.stop="toggleMessages"
        >
          <i class="far fa-comment-dots"></i>
          <span v-if="unreadCount > 0" class="soft-icon-btn__dot"></span>
        </button>
      </div>

      <div class="relative" ref="notificationsRef">
        <button
          type="button"
          class="soft-icon-btn"
          :class="{ 'is-active': showNotifications }"
          aria-label="Notifications"
          @click.stop="toggleNotifications"
        >
          <i class="far fa-bell"></i>
          <span v-if="unreadCount > 0" class="soft-icon-btn__dot"></span>
        </button>

        <div v-if="showNotifications" class="soft-dropdown">
          <div class="soft-dropdown__head">
            <span>Notifications</span>
            <button v-if="unreadCount > 0" type="button" class="soft-dropdown__action" @click="markAllRead">
              Mark all read
            </button>
          </div>
          <div class="soft-dropdown__body">
            <div v-if="loading" class="soft-dropdown__empty">
              <i class="fas fa-spinner fa-spin"></i> Loading…
            </div>
            <div v-else-if="notifications.length === 0" class="soft-dropdown__empty">
              No notifications
            </div>
            <button
              v-for="notif in notifications"
              :key="notif.uuid"
              type="button"
              class="soft-dropdown__item"
              :class="{ 'is-unread': !notif.is_read }"
              @click="handleNotificationClick(notif)"
            >
              <p class="soft-dropdown__item-title">{{ notif.title }}</p>
              <p class="soft-dropdown__item-body">{{ notif.body }}</p>
              <span class="soft-dropdown__item-time">{{ timeAgo(notif.created_at) }}</span>
            </button>
          </div>
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
const showMessages = ref(false)
const notificationsRef = ref(null)
const messagesRef = ref(null)
const notifications = ref([])
const loading = ref(false)
const searchQuery = ref('')
let interval = null

const firstName = computed(() => {
  const user = authStore.user
  if (user?.first_name) return user.first_name
  return displayUserName(user).split(' ')[0]
})

const subtitle = computed(() => {
  const path = route.path
  if (path === '/dashboard') {
    return 'Explore elections, turnout, and activity across your platform'
  }
  if (path.startsWith('/elections')) return 'Create, schedule, and manage election cycles'
  if (path.startsWith('/results')) return 'Review, certify, and publish election results'
  if (path.startsWith('/strongroom')) return 'Monitor seals, vault integrity, and access'
  if (path.startsWith('/fraud')) return 'Track suspicious activity and voting anomalies'
  if (path.startsWith('/ussd')) return 'Watch mobile USSD session health in real time'
  if (path.startsWith('/audit')) return 'Security events and administrative audit trails'
  if (path.startsWith('/users')) return 'Manage platform users and role assignments'
  if (path.startsWith('/settings')) return 'Configure platform preferences and themes'
  if (path.startsWith('/operations')) return 'Operations center and system health'
  if (path.startsWith('/academic')) return 'Faculties, departments, and academic structure'
  return 'Manage your VoterB workspace'
})

const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

const searchTargets = [
  { match: ['election', 'elections'], path: '/elections' },
  { match: ['result', 'results'], path: '/results' },
  { match: ['strong', 'vault', 'seal'], path: '/strongroom' },
  { match: ['fraud'], path: '/fraud' },
  { match: ['ussd', 'mobile'], path: '/ussd' },
  { match: ['audit', 'log'], path: '/audit' },
  { match: ['user', 'users'], path: '/users' },
  { match: ['setting', 'theme'], path: '/settings' },
  { match: ['academic', 'faculty', 'department'], path: '/academic' },
  { match: ['operation', 'ops'], path: '/operations' },
  { match: ['dashboard', 'home'], path: '/dashboard' },
]

const goSearch = () => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return
  const hit = searchTargets.find((t) => t.match.some((m) => q.includes(m) || m.includes(q)))
  if (hit) {
    router.push(hit.path)
    searchQuery.value = ''
  }
}

const fetchNotifications = async () => {
  loading.value = true
  try {
    const response = await notificationApi.list()
    notifications.value = response.data
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
  } finally {
    loading.value = false
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
    window.location.href = notif.link
  }
}

const timeAgo = (date) => {
  const diff = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

const closeMenus = () => {
  showNotifications.value = false
  showMessages.value = false
}

const toggleNotifications = () => {
  showMessages.value = false
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) fetchNotifications()
}

const toggleMessages = () => {
  showNotifications.value = false
  showMessages.value = !showMessages.value
  if (showMessages.value) {
    showNotifications.value = true
    fetchNotifications()
    showMessages.value = false
  }
}

const toggleSidebar = () => {
  emit('toggle-sidebar')
}

const handleClickOutside = (event) => {
  const inNotifications = notificationsRef.value?.contains(event.target)
  const inMessages = messagesRef.value?.contains(event.target)
  if (!inNotifications && !inMessages) closeMenus()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  fetchNotifications()
  interval = setInterval(() => {
    if (showNotifications.value) fetchNotifications()
  }, 30000)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (interval) clearInterval(interval)
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

.soft-icon-btn__dot {
  position: absolute;
  top: 0.55rem;
  right: 0.6rem;
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 9999px;
  background: #e11d48;
  box-shadow: 0 0 0 2px #fff;
}

.soft-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 0.65rem);
  width: 20rem;
  background: #fff;
  border-radius: 1.25rem;
  box-shadow: 0 18px 40px rgba(28, 28, 28, 0.12);
  overflow: hidden;
  z-index: 50;
}

.soft-dropdown__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--vb-line);
  font-size: 0.85rem;
  font-weight: 700;
}

.soft-dropdown__action {
  border: none;
  background: transparent;
  color: var(--vb-accent);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.soft-dropdown__body {
  max-height: 20rem;
  overflow-y: auto;
}

.soft-dropdown__empty {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--vb-muted);
  font-size: 0.85rem;
}

.soft-dropdown__item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid #f5f4ef;
  cursor: pointer;
}

.soft-dropdown__item.is-unread {
  background: #fafaf7;
}

.soft-dropdown__item:hover {
  background: #f5f4ef;
}

.soft-dropdown__item-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--vb-ink);
}

.soft-dropdown__item-body {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
  color: var(--vb-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.soft-dropdown__item-time {
  font-size: 0.68rem;
  color: #b0b0b0;
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
}
</style>
