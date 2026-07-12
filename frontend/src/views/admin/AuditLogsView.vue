<template>
  <div class="audit-page">
    <header class="audit-hero">
      <div>
        <h1 class="audit-hero__title">Audit trail</h1>
        <p class="audit-hero__sub">Review MFA and system activity across the platform.</p>
      </div>
      <button type="button" class="audit-icon-btn" :disabled="loading" title="Refresh" @click="fetchLogs">
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
      </button>
    </header>

    <section class="audit-toolbar">
      <div class="audit-chips">
        <button
          v-for="chip in chips"
          :key="chip.key"
          type="button"
          class="audit-chip"
          :class="{ 'is-active': activeChip === chip.key }"
          @click="setChip(chip.key)"
        >
          <span class="audit-chip__icon"><i :class="chip.icon"></i></span>
          <span class="audit-chip__label">{{ chip.label }}</span>
        </button>
      </div>

      <div class="audit-search">
        <i class="fas fa-search"></i>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Search user or event…"
          @keyup.enter="applyLocalFilter"
        />
        <button type="button" class="audit-search__filter" title="Apply filters" @click="applyLocalFilter">
          <i class="fas fa-sliders-h"></i>
        </button>
      </div>
    </section>

    <section class="audit-grid">
      <article class="audit-card audit-card--list">
        <div class="audit-tabs">
          <button
            type="button"
            class="audit-tab"
            :class="{ 'is-active': listTab === 'recent' }"
            @click="listTab = 'recent'"
          >
            Recent activity
          </button>
          <button
            type="button"
            class="audit-tab"
            :class="{ 'is-active': listTab === 'mfa' }"
            @click="listTab = 'mfa'"
          >
            MFA events
          </button>
        </div>

        <div v-if="loading && !displayLogs.length" class="audit-empty">
          <i class="fas fa-spinner fa-spin"></i>
          Loading activity…
        </div>

        <ul v-else-if="displayLogs.length" class="audit-list">
          <li v-for="log in displayLogs" :key="log.uuid || `${log.type}-${log.timestamp}-${log.event_type}`" class="audit-row">
            <div class="audit-avatar" :class="log.type === 'mfa' ? 'is-mfa' : 'is-audit'">
              <i :class="log.type === 'mfa' ? 'fas fa-key' : 'fas fa-clipboard-list'"></i>
            </div>
            <div class="audit-row__main">
              <p class="audit-row__title">{{ log.user?.email || log.user || 'System' }}</p>
              <p class="audit-row__sub">{{ formatEvent(log.event_type) }}</p>
            </div>
            <div class="audit-row__meta">
              <span class="audit-row__date">{{ formatDate(log.timestamp || log.created_at) }}</span>
              <span class="audit-row__ip">{{ log.ip_address || '—' }}</span>
            </div>
            <span class="audit-row__type" :class="log.type === 'mfa' ? 'is-mfa' : 'is-audit'">
              {{ log.type }}
            </span>
          </li>
        </ul>

        <div v-else class="audit-empty">
          <i class="fas fa-inbox"></i>
          No matching activity yet.
        </div>

        <div v-if="totalPages > 1" class="audit-pager">
          <button type="button" class="audit-pager__btn" :disabled="page <= 1" @click="setPage(page - 1)">Prev</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button type="button" class="audit-pager__btn" :disabled="page >= totalPages" @click="setPage(page + 1)">Next</button>
        </div>
      </article>

      <div class="audit-side">
        <article class="audit-card">
          <h2 class="audit-card__title">Filter activity</h2>
          <p class="audit-card__hint">Narrow the trail by event type or account.</p>

          <label class="audit-field">
            <span>Event type</span>
            <input v-model="filters.event_type" type="text" placeholder="e.g. login_success" />
          </label>

          <label class="audit-field">
            <span>User</span>
            <input v-model="filters.user" type="text" placeholder="email@school.edu" />
          </label>

          <div class="audit-actions">
            <button type="button" class="audit-btn audit-btn--primary" @click="applyFilters">
              Apply filters
            </button>
            <button type="button" class="audit-btn audit-btn--ghost" @click="clearFilters">
              Clear
            </button>
          </div>
        </article>

        <article class="audit-card">
          <h2 class="audit-card__title">Coverage</h2>
          <p class="audit-card__hint">Share of loaded events in this view.</p>

          <div class="audit-meter">
            <div class="audit-meter__head">
              <span>MFA events</span>
              <strong>{{ derivedStats.mfa }}</strong>
            </div>
            <div class="audit-meter__track">
              <div class="audit-meter__fill" :style="{ width: `${mfaPct}%` }"></div>
            </div>
          </div>

          <div class="audit-meter">
            <div class="audit-meter__head">
              <span>Audit events</span>
              <strong>{{ derivedStats.audit }}</strong>
            </div>
            <div class="audit-meter__track">
              <div class="audit-meter__fill is-slate" :style="{ width: `${auditPct}%` }"></div>
            </div>
          </div>

          <div class="audit-meter">
            <div class="audit-meter__head">
              <span>Today</span>
              <strong>{{ derivedStats.today }}</strong>
            </div>
            <div class="audit-meter__track">
              <div class="audit-meter__fill is-soft" :style="{ width: `${todayPct}%` }"></div>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { auditApi } from '@/api/audit'
import { usePagination } from '@/composables/usePagination'

const logs = ref([])
const loading = ref(false)
const filters = ref({ event_type: '', user: '' })
const searchQuery = ref('')
const activeChip = ref('all')
const listTab = ref('recent')

const { page, size, setPage, reset } = usePagination(logs, 8)

const chips = [
  { key: 'all', label: 'All', icon: 'fas fa-layer-group' },
  { key: 'mfa', label: 'MFA', icon: 'fas fa-key' },
  { key: 'audit', label: 'Audit', icon: 'fas fa-clipboard-list' },
  { key: 'today', label: 'Today', icon: 'fas fa-sun' },
]

const startOfToday = () => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}

const derivedStats = computed(() => {
  const today = startOfToday()
  let mfa = 0
  let audit = 0
  let todayCount = 0
  for (const log of logs.value) {
    if (log.type === 'mfa') mfa += 1
    else audit += 1
    const ts = new Date(log.timestamp || log.created_at || 0)
    if (ts >= today) todayCount += 1
  }
  return { total: logs.value.length, today: todayCount, mfa, audit }
})

const mfaPct = computed(() => {
  if (!derivedStats.value.total) return 0
  return Math.round((derivedStats.value.mfa / derivedStats.value.total) * 100)
})
const auditPct = computed(() => {
  if (!derivedStats.value.total) return 0
  return Math.round((derivedStats.value.audit / derivedStats.value.total) * 100)
})
const todayPct = computed(() => {
  if (!derivedStats.value.total) return 0
  return Math.round((derivedStats.value.today / derivedStats.value.total) * 100)
})

const filteredLogs = computed(() => {
  const today = startOfToday()
  const q = searchQuery.value.trim().toLowerCase()
  return logs.value.filter((log) => {
    if (activeChip.value === 'mfa' && log.type !== 'mfa') return false
    if (activeChip.value === 'audit' && log.type === 'mfa') return false
    if (activeChip.value === 'today') {
      const ts = new Date(log.timestamp || log.created_at || 0)
      if (ts < today) return false
    }
    if (listTab.value === 'mfa' && log.type !== 'mfa') return false
    if (!q) return true
    const hay = `${log.user?.email || log.user || ''} ${log.event_type || ''} ${log.ip_address || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

watch(filteredLogs, () => {
  setPage(1)
})

const displayLogs = computed(() => {
  const start = (page.value - 1) * size.value
  return filteredLogs.value.slice(start, start + size.value)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredLogs.value.length / size.value) || 1))

watch([activeChip, listTab, searchQuery], () => {
  setPage(1)
})

watch(totalPages, (pages) => {
  if (page.value > pages) setPage(pages)
})

const normalizeLogs = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.logs)) return payload.logs
  return []
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.event_type) params.event_type = filters.value.event_type
    if (filters.value.user) params.user = filters.value.user
    const response = await auditApi.getCombined(params)
    logs.value = normalizeLogs(response.data)
    reset()
  } catch (error) {
    console.error('Failed to fetch logs:', error)
    logs.value = []
  } finally {
    loading.value = false
  }
}

const setChip = (key) => {
  activeChip.value = key
  if (key === 'mfa') listTab.value = 'mfa'
  if (key === 'all' || key === 'audit' || key === 'today') listTab.value = 'recent'
}

const applyFilters = () => fetchLogs()
const applyLocalFilter = () => setPage(1)
const clearFilters = () => {
  filters.value = { event_type: '', user: '' }
  searchQuery.value = ''
  activeChip.value = 'all'
  listTab.value = 'recent'
  fetchLogs()
}

const formatEvent = (eventType) => (eventType || 'event').replaceAll('_', ' ')
const formatDate = (date) => (
  date
    ? new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
    : '—'
)

onMounted(fetchLogs)
</script>

<style scoped>
.audit-page {
  width: 100%;
  max-width: 78rem;
  margin: 0 auto;
}

.audit-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.35rem;
}

.audit-hero__title {
  margin: 0;
  font-size: clamp(1.55rem, 3vw, 2rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1c1c;
}

.audit-hero__sub {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
  color: #8a8a8a;
}

.audit-icon-btn {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 9999px;
  border: 1px solid #ebeae4;
  background: #fff;
  color: #6b6b6b;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.03);
}

.audit-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.15rem;
}

.audit-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem 1.1rem;
}

.audit-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  color: #8a8a8a;
}

.audit-chip__icon {
  width: 3.1rem;
  height: 3.1rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid #ebeae4;
  color: #5c5c5c;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.03);
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.audit-chip__label {
  font-size: 0.75rem;
  font-weight: 600;
}

.audit-chip.is-active {
  color: #1c1c1c;
}

.audit-chip.is-active .audit-chip__icon {
  background: #1c1c1c;
  border-color: #1c1c1c;
  color: #fff;
}

.audit-search {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: min(100%, 17rem);
  padding: 0.35rem 0.4rem 0.35rem 0.95rem;
  border-radius: 9999px;
  background: #fff;
  border: 1px solid #ebeae4;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.03);
}

.audit-search i {
  color: #9a9a9a;
}

.audit-search input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.88rem;
  color: #1c1c1c;
}

.audit-search__filter {
  width: 2.35rem;
  height: 2.35rem;
  border: none;
  border-radius: 9999px;
  background: #f3f2ed;
  color: #5c5c5c;
  cursor: pointer;
}

.audit-grid {
  display: grid;
  gap: 1rem;
  align-items: start;
}

@media (min-width: 1024px) {
  .audit-grid {
    grid-template-columns: minmax(0, 1.35fr) minmax(17rem, 0.85fr);
    gap: 1.15rem;
  }
}

.audit-side {
  display: grid;
  gap: 1rem;
}

.audit-card {
  background: #fff;
  border-radius: 1.35rem;
  padding: 1.25rem 1.25rem 1.15rem;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.03);
}

.audit-card__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: #1c1c1c;
  letter-spacing: -0.02em;
}

.audit-card__hint {
  margin: 0.3rem 0 1rem;
  font-size: 0.8rem;
  color: #8a8a8a;
}

.audit-tabs {
  display: flex;
  gap: 1.25rem;
  margin-bottom: 0.85rem;
  border-bottom: 1px solid #f0efe9;
}

.audit-tab {
  border: none;
  background: transparent;
  padding: 0 0 0.75rem;
  font-size: 0.92rem;
  font-weight: 700;
  color: #9a9a9a;
  cursor: pointer;
  position: relative;
}

.audit-tab.is-active {
  color: #1c1c1c;
}

.audit-tab.is-active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  border-radius: 9999px;
  background: #1c1c1c;
}

.audit-list {
  list-style: none;
  margin: 0;
  padding: 0.25rem 0 0;
  display: flex;
  flex-direction: column;
  max-height: min(32rem, 58vh);
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.audit-list::-webkit-scrollbar {
  display: none;
}

.audit-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1.2fr) minmax(0, 0.9fr) auto;
  gap: 0.85rem;
  align-items: center;
  padding: 0.85rem 0.15rem;
  border-bottom: 1px solid #f5f4ef;
}

.audit-row:last-child {
  border-bottom: none;
}

.audit-avatar {
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.85rem;
}

.audit-avatar.is-mfa {
  background: #e8efe6;
  color: #3d4f44;
}

.audit-avatar.is-audit {
  background: #f0efe9;
  color: #5c5c5c;
}

.audit-row__main {
  min-width: 0;
}

.audit-row__title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #1c1c1c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.audit-row__sub {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: #8a8a8a;
  text-transform: capitalize;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.audit-row__meta {
  min-width: 0;
  text-align: left;
}

.audit-row__date {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #1c1c1c;
}

.audit-row__ip {
  display: block;
  margin-top: 0.15rem;
  font-size: 0.72rem;
  color: #9a9a9a;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.audit-row__type {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.65rem;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.audit-row__type.is-mfa {
  background: #e8efe6;
  color: #3d4f44;
}

.audit-row__type.is-audit {
  background: #f0efe9;
  color: #5c5c5c;
}

.audit-empty {
  padding: 2.5rem 1rem;
  text-align: center;
  color: #8a8a8a;
  font-size: 0.88rem;
}

.audit-empty i {
  display: block;
  margin-bottom: 0.55rem;
  font-size: 1.25rem;
}

.audit-pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f0efe9;
  font-size: 0.8rem;
  color: #8a8a8a;
}

.audit-pager__btn {
  border: 1px solid #ebeae4;
  background: #fff;
  border-radius: 9999px;
  padding: 0.4rem 0.85rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: #1c1c1c;
  cursor: pointer;
}

.audit-pager__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.audit-field {
  display: grid;
  gap: 0.4rem;
  margin-bottom: 0.85rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: #8a8a8a;
}

.audit-field input {
  width: 100%;
  border: none;
  outline: none;
  border-radius: 0.9rem;
  background: #f3f2ed;
  padding: 0.85rem 0.95rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #1c1c1c;
}

.audit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 0.35rem;
}

.audit-btn {
  border-radius: 9999px;
  padding: 0.75rem 1.15rem;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
}

.audit-btn--primary {
  background: #1c1c1c;
  color: #fff;
  border-color: #1c1c1c;
}

.audit-btn--ghost {
  background: #fff;
  color: #1c1c1c;
  border-color: #dddcd6;
}

.audit-meter + .audit-meter {
  margin-top: 1rem;
}

.audit-meter__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.45rem;
  font-size: 0.82rem;
  color: #6b6b6b;
}

.audit-meter__head strong {
  color: #1c1c1c;
  font-size: 0.9rem;
}

.audit-meter__track {
  height: 0.45rem;
  border-radius: 9999px;
  background: #f0efe9;
  overflow: hidden;
}

.audit-meter__fill {
  height: 100%;
  border-radius: 9999px;
  background: #3d4f44;
  transition: width 0.3s ease;
}

.audit-meter__fill.is-slate {
  background: #1c1c1c;
}

.audit-meter__fill.is-soft {
  background: #a3b18a;
}

@media (max-width: 720px) {
  .audit-row {
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-areas:
      "avatar main type"
      "avatar meta type";
  }

  .audit-avatar { grid-area: avatar; }
  .audit-row__main { grid-area: main; }
  .audit-row__meta { grid-area: meta; }
  .audit-row__type { grid-area: type; align-self: start; }

  .audit-search {
    width: 100%;
  }
}
</style>
