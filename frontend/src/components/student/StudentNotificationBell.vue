<template>
  <div ref="rootRef" class="student-bell">
    <button
      type="button"
      class="student-bell__btn"
      :class="{ 'is-open': open, 'has-unread': unreadCount > 0 }"
      aria-label="Notifications"
      @click.stop="toggle"
    >
      <i class="far fa-bell" aria-hidden="true"></i>
      <span
        v-if="unreadCount > 0"
        class="student-bell__badge"
        :aria-label="`${unreadCount} unread notifications`"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <Transition name="bell-drop">
      <div v-if="open" class="student-bell__panel" role="menu">
        <NotificationInbox
          tone="student"
          :items="notifications"
          :loading="loading"
          :unread-count="unreadCount"
          :now-ms="nowMs"
          @select="openNotif"
          @mark-all="markAllRead"
        />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationApi } from '@/api/notifications'
import { playNotificationChime, unlockAudio } from '@/utils/beep'
import NotificationInbox from '@/components/notifications/NotificationInbox.vue'

const router = useRouter()
const open = ref(false)
const loading = ref(false)
const notifications = ref([])
const nowMs = ref(Date.now())
const rootRef = ref(null)
let pollTimer = null
let clockTimer = null
let knownUnreadIds = new Set()

const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

const fetchNotifications = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  try {
    const { data } = await notificationApi.list()
    const next = Array.isArray(data) ? data : []
    const nextUnread = next.filter((n) => !n.is_read).map((n) => n.uuid)
    const isFirst = knownUnreadIds.size === 0 && notifications.value.length === 0
    const fresh = nextUnread.filter((id) => !knownUnreadIds.has(id))
    notifications.value = next
    knownUnreadIds = new Set(nextUnread)
    if (!isFirst && fresh.length) {
      unlockAudio()
      playNotificationChime()
    }
  } catch {
    /* keep last good list */
  } finally {
    if (!silent) loading.value = false
  }
}

const toggle = () => {
  open.value = !open.value
  if (open.value) {
    unlockAudio()
    fetchNotifications()
  }
}

const markAllRead = async () => {
  try {
    await notificationApi.markAllRead()
    notifications.value = notifications.value.map((n) => ({ ...n, is_read: true }))
    knownUnreadIds = new Set()
  } catch {
    /* ignore */
  }
}

const openNotif = async (notif) => {
  if (!notif.is_read) {
    try {
      await notificationApi.markRead(notif.uuid)
      notif.is_read = true
    } catch {
      /* ignore */
    }
  }
  open.value = false
  if (notif.link?.startsWith('/')) router.push(notif.link)
}

const onDocClick = (event) => {
  if (!rootRef.value?.contains(event.target)) open.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  fetchNotifications()
  pollTimer = setInterval(() => fetchNotifications({ silent: true }), 15000)
  clockTimer = setInterval(() => { nowMs.value = Date.now() }, 1000)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<style scoped>
.student-bell {
  position: relative;
}

.student-bell__btn {
  position: relative;
  width: 2.45rem;
  height: 2.45rem;
  border: 1px solid #e4ebe8;
  border-radius: 9999px;
  background: #fff;
  color: #334155;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease;
}

.student-bell__btn.has-unread {
  color: #0f766e;
  border-color: #99f6e4;
  background: #f0fdfa;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.08);
}

.student-bell__btn.is-open,
.student-bell__btn:hover {
  border-color: #99f6e4;
  color: #0f766e;
  background: #f0fdfa;
}

.student-bell__badge {
  position: absolute;
  top: 0.05rem;
  right: 0.02rem;
  min-width: 1.05rem;
  height: 1.05rem;
  padding: 0 0.24rem;
  border-radius: 9999px;
  background: #0f766e;
  color: #fff;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.05rem;
  text-align: center;
  border: 2px solid #fff;
  box-sizing: content-box;
}

.student-bell__panel {
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  z-index: 40;
}

.bell-drop-enter-active,
.bell-drop-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.bell-drop-enter-from,
.bell-drop-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>
