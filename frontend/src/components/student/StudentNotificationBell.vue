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
        <div class="student-bell__head">
          <span>Notifications</span>
          <button
            v-if="unreadCount > 0"
            type="button"
            class="student-bell__mark"
            @click="markAllRead"
          >
            Mark all read
          </button>
        </div>
        <div class="student-bell__body">
          <p v-if="loading" class="student-bell__empty">Loading…</p>
          <p v-else-if="!notifications.length" class="student-bell__empty">No notifications</p>
          <button
            v-for="notif in notifications"
            :key="notif.uuid"
            type="button"
            class="student-bell__item"
            :class="{ 'is-unread': !notif.is_read }"
            @click="openNotif(notif)"
          >
            <span class="student-bell__accent" aria-hidden="true"></span>
            <div class="student-bell__content">
              <div class="student-bell__top">
                <p class="student-bell__title">{{ notif.title }}</p>
                <span v-if="!notif.is_read" class="student-bell__live">New</span>
              </div>
              <p class="student-bell__copy">{{ notif.body }}</p>
              <div class="student-bell__meta">
                <span
                  v-if="countdownFor(notif)"
                  class="student-bell__countdown"
                  :class="`is-${countdownFor(notif).urgency}`"
                >
                  <i class="fas fa-hourglass-half" aria-hidden="true"></i>
                  {{ countdownFor(notif).expired ? 'Expired' : countdownFor(notif).display }}
                </span>
                <span class="student-bell__time">{{ timeAgo(notif.created_at) }}</span>
              </div>
            </div>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationApi } from '@/api/notifications'
import { parseCountdown, formatCountdownUnit } from '@/composables/useCountdown'
import { playNotificationChime, unlockAudio } from '@/utils/beep'

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

const countdownFor = (notif) => {
  const expires = notif?.metadata?.expires_at
  if (!expires) return null
  const parts = parseCountdown(expires, nowMs.value)
  const total = Math.max(0, Math.floor((parts.totalMs || 0) / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  let urgency = 'ok'
  if (parts.expired) urgency = 'expired'
  else if (total <= 30) urgency = 'critical'
  else if (total <= 120) urgency = 'urgent'
  else if (total <= 300) urgency = 'warn'
  return {
    expired: parts.expired,
    display: `${formatCountdownUnit(m)}:${formatCountdownUnit(s)}`,
    urgency,
  }
}

const timeAgo = (date) => {
  const diff = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

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
  width: 2.4rem;
  height: 2.4rem;
  border: 1px solid #d6ebe5;
  border-radius: 9999px;
  background: #fff;
  color: #0f766e;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.student-bell__btn.has-unread {
  background: #ecfdf5;
  border-color: #99f6e4;
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.12);
}

.student-bell__btn.is-open,
.student-bell__btn:hover {
  border-color: #5eead4;
  background: #f0fdf9;
}

.student-bell__badge {
  position: absolute;
  top: 0.1rem;
  right: 0.08rem;
  min-width: 1.1rem;
  height: 1.1rem;
  padding: 0 0.26rem;
  border-radius: 9999px;
  background: #0d9488;
  color: #fff;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1rem;
  text-align: center;
  border: 2px solid #fff;
  box-sizing: content-box;
}

.student-bell__panel {
  position: absolute;
  right: 0;
  top: calc(100% + 0.45rem);
  width: min(21rem, calc(100vw - 1.5rem));
  background: #fff;
  border: 1px solid #d6ebe5;
  border-radius: 1rem;
  box-shadow: 0 16px 40px rgba(15, 118, 110, 0.14);
  z-index: 40;
  overflow: hidden;
}

.student-bell__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.8rem 0.9rem;
  border-bottom: 1px solid #e7f5f1;
  font-size: 0.8rem;
  font-weight: 750;
  color: #134e4a;
  background: linear-gradient(180deg, #f0fdf9 0%, #fff 100%);
}

.student-bell__mark {
  border: none;
  background: transparent;
  color: #0d9488;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
}

.student-bell__body {
  max-height: 18rem;
  overflow: auto;
}

.student-bell__empty {
  margin: 0;
  padding: 1.35rem 0.9rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.8rem;
}

.student-bell__item {
  display: flex;
  width: 100%;
  text-align: left;
  border: none;
  border-bottom: 1px solid #eef7f4;
  background: #fff;
  padding: 0;
  cursor: pointer;
}

.student-bell__item.is-unread {
  background: linear-gradient(90deg, #ecfdf5 0%, #f0fdf9 55%, #fff 100%);
}

.student-bell__accent {
  width: 0.28rem;
  flex-shrink: 0;
  background: transparent;
}

.student-bell__item.is-unread .student-bell__accent {
  background: #0d9488;
}

.student-bell__content {
  flex: 1;
  min-width: 0;
  padding: 0.8rem 0.85rem;
}

.student-bell__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.45rem;
}

.student-bell__title {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 750;
  color: #134e4a;
  line-height: 1.3;
}

.student-bell__live {
  flex-shrink: 0;
  font-size: 0.56rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #fff;
  background: #0d9488;
  border-radius: 9999px;
  padding: 0.16rem 0.42rem;
}

.student-bell__copy {
  margin: 0.25rem 0 0;
  font-size: 0.74rem;
  color: #5b716c;
  line-height: 1.4;
}

.student-bell__meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.4rem;
}

.student-bell__countdown {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.68rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0f766e;
  background: rgba(13, 148, 136, 0.1);
  border-radius: 9999px;
  padding: 0.14rem 0.45rem;
}

.student-bell__countdown.is-warn {
  color: #c2410c;
  background: rgba(194, 65, 12, 0.1);
}
.student-bell__countdown.is-urgent,
.student-bell__countdown.is-critical {
  color: #b91c1c;
  background: rgba(185, 28, 28, 0.1);
}
.student-bell__countdown.is-expired {
  color: #78716c;
  background: #f5f5f4;
}

.student-bell__time {
  margin-left: auto;
  font-size: 0.66rem;
  color: #94a3b8;
}

.bell-drop-enter-active,
.bell-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.bell-drop-enter-from,
.bell-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
