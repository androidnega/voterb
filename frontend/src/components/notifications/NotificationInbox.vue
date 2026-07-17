<template>
  <div class="ni" :data-tone="tone">
    <div class="ni__head">
      <div class="ni__head-main">
        <p class="ni__eyebrow">Inbox</p>
        <h2 class="ni__title">Notifications</h2>
      </div>
      <button
        v-if="unreadCount > 0"
        type="button"
        class="ni__mark"
        @click="$emit('mark-all')"
      >
        Mark all read
      </button>
    </div>

    <div class="ni__body">
      <div v-if="loading" class="ni__empty">
        <span class="ni__spinner" aria-hidden="true" />
        <p>Loading…</p>
      </div>

      <div v-else-if="!items.length" class="ni__empty ni__empty--quiet">
        <div class="ni__empty-icon" aria-hidden="true">
          <i class="far fa-bell"></i>
        </div>
        <p class="ni__empty-title">You’re all caught up</p>
        <p class="ni__empty-copy">New election and voting updates will show up here.</p>
      </div>

      <button
        v-for="notif in enriched"
        :key="notif.uuid"
        type="button"
        class="ni__item"
        :class="{ 'is-unread': !notif.is_read }"
        @click="$emit('select', notif)"
      >
        <span class="ni__icon" :data-kind="kindFor(notif)" aria-hidden="true">
          <i :class="iconFor(notif)"></i>
        </span>
        <div class="ni__content">
          <div class="ni__row">
            <p class="ni__item-title">{{ cleanTitle(notif.title) }}</p>
            <span v-if="!notif.is_read" class="ni__dot" title="Unread" />
          </div>
          <p class="ni__item-body">{{ notif.body }}</p>
          <div class="ni__meta">
            <span
              v-if="notif.countdown"
              class="ni__timer"
              :class="`is-${notif.countdown.urgency}`"
            >
              <i class="fas fa-clock" aria-hidden="true"></i>
              {{ notif.countdown.expired ? 'Expired' : notif.countdown.display }}
            </span>
            <span class="ni__time">{{ timeAgo(notif.created_at) }}</span>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { parseCountdown, formatCountdownUnit } from '@/composables/useCountdown'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  unreadCount: { type: Number, default: 0 },
  nowMs: { type: Number, default: () => Date.now() },
  tone: { type: String, default: 'admin' }, // admin | student
})

defineEmits(['select', 'mark-all'])

const EMOJI_RE = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu

const cleanTitle = (title) => String(title || '').replace(EMOJI_RE, '').replace(/\s+/g, ' ').trim()

const kindFor = (notif) => {
  const type = String(notif.notification_type || '').toLowerCase()
  if (type.includes('svt')) return 'svt'
  if (type.includes('vote')) return 'vote'
  if (type.includes('result')) return 'result'
  if (type.includes('fraud') || type.includes('alert')) return 'alert'
  if (type.includes('open')) return 'open'
  if (type.includes('close')) return 'close'
  return 'default'
}

const iconFor = (notif) => {
  const map = {
    svt: 'fas fa-key',
    vote: 'fas fa-check',
    result: 'fas fa-chart-bar',
    alert: 'fas fa-exclamation',
    open: 'fas fa-door-open',
    close: 'fas fa-lock',
    default: 'fas fa-bell',
  }
  return map[kindFor(notif)] || map.default
}

const countdownFor = (notif) => {
  const expires = notif?.metadata?.expires_at
  if (!expires) return null
  const parts = parseCountdown(expires, props.nowMs)
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

const enriched = computed(() =>
  props.items.map((n) => ({ ...n, countdown: countdownFor(n) })),
)

const timeAgo = (date) => {
  const diff = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
</script>

<style scoped>
.ni {
  --ni-ink: #1a1a1a;
  --ni-muted: #6b7280;
  --ni-line: #eceae4;
  --ni-surface: #ffffff;
  --ni-soft: #f7f6f2;
  --ni-accent: #2f6f5e;
  --ni-accent-soft: rgba(47, 111, 94, 0.1);
  width: min(22.5rem, calc(100vw - 1.25rem));
  background: var(--ni-surface);
  border: 1px solid var(--ni-line);
  border-radius: 1.15rem;
  box-shadow: 0 20px 48px rgba(26, 26, 26, 0.1);
  overflow: hidden;
}

.ni[data-tone='student'] {
  --ni-accent: #0f766e;
  --ni-accent-soft: rgba(15, 118, 110, 0.1);
}

.ni__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem 1.05rem 0.85rem;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--ni-accent) 6%, #fff) 0%, #fff 100%);
  border-bottom: 1px solid var(--ni-line);
}

.ni__eyebrow {
  margin: 0;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ni-muted);
}

.ni__title {
  margin: 0.15rem 0 0;
  font-size: 1rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: var(--ni-ink);
}

.ni__mark {
  border: 1px solid var(--ni-line);
  background: #fff;
  color: var(--ni-accent);
  font-size: 0.7rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  cursor: pointer;
  white-space: nowrap;
}

.ni__mark:hover {
  background: var(--ni-soft);
}

.ni__body {
  max-height: min(22rem, 58vh);
  overflow: auto;
}

.ni__empty {
  display: grid;
  place-items: center;
  gap: 0.45rem;
  padding: 2.25rem 1.25rem;
  text-align: center;
  color: var(--ni-muted);
  font-size: 0.82rem;
}

.ni__empty--quiet {
  gap: 0.35rem;
}

.ni__empty-icon {
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: var(--ni-soft);
  color: var(--ni-accent);
  margin-bottom: 0.35rem;
}

.ni__empty-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 750;
  color: var(--ni-ink);
}

.ni__empty-copy {
  margin: 0;
  max-width: 14rem;
  font-size: 0.76rem;
  line-height: 1.4;
  color: var(--ni-muted);
}

.ni__spinner {
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 999px;
  border: 2px solid var(--ni-line);
  border-top-color: var(--ni-accent);
  animation: ni-spin 0.7s linear infinite;
}

.ni__item {
  display: flex;
  gap: 0.75rem;
  width: 100%;
  text-align: left;
  border: none;
  border-bottom: 1px solid color-mix(in srgb, var(--ni-line) 80%, transparent);
  background: transparent;
  padding: 0.85rem 1.05rem;
  cursor: pointer;
  transition: background 0.15s ease;
}

.ni__item:hover {
  background: var(--ni-soft);
}

.ni__item.is-unread {
  background: color-mix(in srgb, var(--ni-accent) 5%, #fff);
}

.ni__item.is-unread:hover {
  background: color-mix(in srgb, var(--ni-accent) 8%, #fff);
}

.ni__icon {
  width: 2.15rem;
  height: 2.15rem;
  border-radius: 0.75rem;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--ni-soft);
  color: var(--ni-muted);
  font-size: 0.78rem;
}

.ni__icon[data-kind='svt'] { background: #eef6ff; color: #2563eb; }
.ni__icon[data-kind='vote'] { background: #ecfdf5; color: #059669; }
.ni__icon[data-kind='result'] { background: #f5f3ff; color: #7c3aed; }
.ni__icon[data-kind='alert'] { background: #fff1f2; color: #e11d48; }
.ni__icon[data-kind='open'] { background: #ecfdf5; color: #0f766e; }
.ni__icon[data-kind='close'] { background: #f8fafc; color: #475569; }

.ni__content {
  flex: 1;
  min-width: 0;
}

.ni__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.ni__item-title {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--ni-ink);
  line-height: 1.3;
}

.ni__dot {
  width: 0.45rem;
  height: 0.45rem;
  margin-top: 0.35rem;
  border-radius: 999px;
  background: var(--ni-accent);
  flex-shrink: 0;
  box-shadow: 0 0 0 3px var(--ni-accent-soft);
}

.ni__item-body {
  margin: 0.28rem 0 0;
  font-size: 0.76rem;
  color: var(--ni-muted);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ni__meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.45rem;
}

.ni__timer {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  font-size: 0.66rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--ni-accent);
  background: var(--ni-accent-soft);
  border-radius: 999px;
  padding: 0.18rem 0.5rem;
}

.ni__timer.is-warn { color: #c2410c; background: rgba(194, 65, 12, 0.1); }
.ni__timer.is-urgent,
.ni__timer.is-critical { color: #b91c1c; background: rgba(185, 28, 28, 0.1); }
.ni__timer.is-expired { color: #78716c; background: #f5f5f4; }

.ni__time {
  margin-left: auto;
  font-size: 0.66rem;
  color: #9ca3af;
}

@keyframes ni-spin {
  to { transform: rotate(360deg); }
}
</style>
