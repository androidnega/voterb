<template>
  <header class="bg-white border-b border-gray-200 sticky top-0 z-30">
    <div class="flex items-center justify-between px-4 h-16">
      <!-- Left side -->
      <div class="flex items-center gap-3">
        <button 
          @click="toggleMobileMenu" 
          class="p-2 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
        >
          <i class="fas fa-bars text-gray-600 text-lg"></i>
        </button>
        <div class="hidden sm:flex items-center gap-2 text-sm">
          <span class="text-gray-400">/</span>
          <span class="text-gray-600 font-medium">{{ currentPage }}</span>
        </div>
      </div>

      <!-- Right side -->
      <div class="flex items-center gap-3">
        <!-- Notifications -->
        <div class="relative">
          <button 
            @click="toggleDropdown"
            class="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
          >
            <i class="fas fa-bell text-gray-500"></i>
            <span v-if="unreadCount > 0" class="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {{ unreadCount > 99 ? '99+' : unreadCount }}
            </span>
          </button>
          <!-- Dropdown -->
          <div 
            v-if="showDropdown"
            class="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-50"
          >
            <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <span class="text-sm font-semibold text-gray-900">Notifications</span>
              <button 
                v-if="unreadCount > 0"
                @click="markAllRead"
                class="text-xs text-emerald-600 hover:text-emerald-700"
              >
                Mark all read
              </button>
            </div>
            <div class="max-h-80 overflow-y-auto">
              <div v-if="loading" class="px-4 py-6 text-center text-gray-400 text-sm">
                <i class="fas fa-spinner fa-spin"></i> Loading...
              </div>
              <div v-else-if="notifications.length === 0" class="px-4 py-8 text-center text-gray-400 text-sm">
                <i class="fas fa-inbox text-2xl block mb-2 text-gray-300"></i>
                No notifications
              </div>
              <div 
                v-for="notif in notifications" 
                :key="notif.uuid"
                class="px-4 py-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                :class="{ 'bg-blue-50/50': !notif.is_read }"
                @click="handleNotificationClick(notif)"
              >
                <div class="flex items-start gap-2">
                  <i v-if="!notif.is_read" class="fas fa-circle text-emerald-500 text-xs mt-1"></i>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-800">{{ notif.title }}</p>
                    <p class="text-xs text-gray-500 truncate">{{ notif.body }}</p>
                    <span class="text-[10px] text-gray-400">{{ timeAgo(notif.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="px-4 py-2 border-t border-gray-100 text-center">
              <router-link to="/notifications" class="text-sm text-emerald-600 hover:text-emerald-700">
                View all
              </router-link>
            </div>
          </div>
        </div>

        <!-- User -->
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
            <span class="text-emerald-700 font-semibold text-sm">{{ userInitial }}</span>
          </div>
          <span class="text-sm font-medium text-gray-700 hidden sm:block">{{ userName }}</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { notificationApi } from '@/api/notifications'

const route = useRoute()
const authStore = useAuthStore()
const emit = defineEmits(['toggle-mobile'])

const showDropdown = ref(false)
const notifications = ref([])
const loading = ref(false)
let interval = null

const currentPage = computed(() => {
  const path = route.path
  if (path === '/dashboard') return 'Dashboard'
  if (path.startsWith('/elections')) return 'Elections'
  if (path.startsWith('/results')) return 'Results'
  if (path.startsWith('/strongroom')) return 'Strongroom'
  if (path.startsWith('/student')) return 'Student View'
  return 'Dashboard'
})

const userName = computed(() => {
  const user = authStore.user
  if (user?.first_name) return user.first_name
  if (user?.email) return user.email.split('@')[0]
  return 'User'
})

const userInitial = computed(() => {
  const name = userName.value
  return name.charAt(0).toUpperCase()
})

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

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
    notifications.value = notifications.value.map(n => ({ ...n, is_read: true }))
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
    showDropdown.value = false
    window.location.href = notif.link
  }
}

const timeAgo = (date) => {
  const diff = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago'
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago'
  return Math.floor(diff / 86400) + 'd ago'
}

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value) {
    fetchNotifications()
  }
}

const toggleMobileMenu = () => {
  emit('toggle-mobile')
}

// Poll every 30 seconds
onMounted(() => {
  interval = setInterval(() => {
    if (showDropdown.value) {
      fetchNotifications()
    }
  }, 30000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>
