<template>
  <div class="audit-page">
    <header class="audit-hero">
      <div>
        <h1 class="audit-hero__title">Voter audit trail</h1>
        <p class="audit-hero__sub">
          Device, location, and presence records for voters who cast a ballot.
          Ballot choices are never shown.
        </p>
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
          @click="activeChip = chip.key"
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
          placeholder="Search voter, IP, or receipt…"
          @keyup.enter="applyLocalFilter"
        />
      </div>
    </section>

    <section class="audit-grid">
      <article class="audit-card audit-card--list">
        <div class="audit-list-head">
          <h2>Recent votes</h2>
          <span>{{ filteredLogs.length }} records</span>
        </div>

        <div v-if="loading && !displayLogs.length" class="audit-empty">
          <i class="fas fa-spinner fa-spin"></i>
          Loading voter audits…
        </div>

        <ul v-else-if="displayLogs.length" class="audit-list">
          <li
            v-for="log in displayLogs"
            :key="log.audit_id"
            class="audit-row"
            :class="{ 'is-selected': selectedId === log.audit_id }"
            role="button"
            tabindex="0"
            @click="openDetail(log.audit_id)"
            @keydown.enter="openDetail(log.audit_id)"
          >
            <div class="audit-avatar is-audit">
              <i class="fas fa-user-check"></i>
            </div>
            <div class="audit-row__main">
              <p class="audit-row__title">{{ log.user_display || log.user_email || 'Voter' }}</p>
              <p class="audit-row__sub">
                {{ log.election_title || 'Election' }}
                <span v-if="log.operating_system"> · {{ log.operating_system }}</span>
              </p>
            </div>
            <div class="audit-row__meta">
              <span class="audit-row__date">{{ formatDate(log.timestamp) }}</span>
              <span class="audit-row__ip">{{ log.ip_address || '—' }}</span>
            </div>
            <span class="audit-row__type is-audit">
              {{ log.has_presence_photo ? 'photo' : 'vote' }}
            </span>
          </li>
        </ul>

        <div v-else class="audit-empty">
          <i class="fas fa-inbox"></i>
          No voter audits yet. Records appear after a ballot is submitted.
        </div>

        <div v-if="totalPages > 1" class="audit-pager">
          <button type="button" class="audit-pager__btn" :disabled="page <= 1" @click="setPage(page - 1)">Prev</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button type="button" class="audit-pager__btn" :disabled="page >= totalPages" @click="setPage(page + 1)">Next</button>
        </div>
      </article>

      <aside class="audit-side">
        <article v-if="detailLoading" class="audit-card audit-detail">
          <div class="audit-empty">
            <i class="fas fa-spinner fa-spin"></i>
            Loading details…
          </div>
        </article>

        <article v-else-if="detail" class="audit-card audit-detail">
          <div class="audit-detail__head">
            <div>
              <p class="audit-detail__eyebrow">Vote cast</p>
              <h2 class="audit-card__title">{{ detail.user_display || detail.user_email }}</h2>
              <p class="audit-card__hint">{{ detail.election_title || 'Election' }}</p>
            </div>
            <button type="button" class="audit-icon-btn audit-icon-btn--sm" title="Close" @click="closeDetail">
              <i class="fas fa-times"></i>
            </button>
          </div>

          <div v-if="detail.presence_photo_url" class="audit-presence">
            <img :src="detail.presence_photo_url" alt="Voter presence photo for audit" />
            <p>
              Presence photo
              <span v-if="detail.presence_captured_at">· {{ formatDate(detail.presence_captured_at) }}</span>
            </p>
          </div>
          <div v-else class="audit-presence audit-presence--empty">
            <i class="fas fa-camera"></i>
            <span>No presence photo attached</span>
          </div>

          <dl class="audit-facts">
            <div>
              <dt>Receipt</dt>
              <dd>{{ detail.confirmation_code || '—' }}</dd>
            </div>
            <div>
              <dt>IP address</dt>
              <dd>{{ detail.ip_address || detail.location?.ip_address || '—' }}</dd>
            </div>
            <div>
              <dt>When</dt>
              <dd>{{ formatDate(detail.timestamp) }}</dd>
            </div>
            <div>
              <dt>Device</dt>
              <dd>{{ detail.device?.device_type || detail.device_type || '—' }}</dd>
            </div>
            <div>
              <dt>Operating system</dt>
              <dd>{{ detail.device?.operating_system || detail.operating_system || '—' }}</dd>
            </div>
            <div>
              <dt>Browser</dt>
              <dd>
                {{
                  [detail.device?.browser_name, detail.device?.browser_version].filter(Boolean).join(' ')
                    || '—'
                }}
              </dd>
            </div>
            <div>
              <dt>Fingerprint</dt>
              <dd class="audit-mono">{{ detail.device?.browser_fingerprint || '—' }}</dd>
            </div>
            <div>
              <dt>Location</dt>
              <dd>{{ formatLocation(detail.location) }}</dd>
            </div>
            <div>
              <dt>Timezone</dt>
              <dd>{{ detail.device?.timezone || '—' }}</dd>
            </div>
            <div>
              <dt>Hints source</dt>
              <dd>{{ detail.device?.hints_source || '—' }}</dd>
            </div>
          </dl>

          <details class="audit-ua">
            <summary>User agent</summary>
            <p>{{ detail.user_agent || detail.device?.user_agent || '—' }}</p>
          </details>

          <p class="audit-secrecy">
            <i class="fas fa-shield-alt"></i>
            Ballot secrecy preserved — this record never includes who the voter selected.
          </p>
        </article>

        <article v-else class="audit-card">
          <h2 class="audit-card__title">Inspection</h2>
          <p class="audit-card__hint">Select a vote audit to view device fingerprint, IP, location, and presence photo.</p>

          <div class="audit-meter">
            <div class="audit-meter__head">
              <span>Loaded</span>
              <strong>{{ derivedStats.total }}</strong>
            </div>
            <div class="audit-meter__track">
              <div class="audit-meter__fill" :style="{ width: '100%' }"></div>
            </div>
          </div>
          <div class="audit-meter">
            <div class="audit-meter__head">
              <span>With presence photo</span>
              <strong>{{ derivedStats.withPhoto }}</strong>
            </div>
            <div class="audit-meter__track">
              <div class="audit-meter__fill is-slate" :style="{ width: `${photoPct}%` }"></div>
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
      </aside>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { auditApi } from '@/api/audit'
import { usePagination } from '@/composables/usePagination'
import { resolveMediaUrl } from '@/utils/media'

const logs = ref([])
const loading = ref(false)
const searchQuery = ref('')
const activeChip = ref('all')
const selectedId = ref(null)
const detail = ref(null)
const detailLoading = ref(false)

const { page, size, setPage, reset } = usePagination(logs, 8)

const chips = [
  { key: 'all', label: 'All votes', icon: 'fas fa-layer-group' },
  { key: 'photo', label: 'With photo', icon: 'fas fa-camera' },
  { key: 'today', label: 'Today', icon: 'fas fa-sun' },
]

const startOfToday = () => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}

const derivedStats = computed(() => {
  const today = startOfToday()
  let withPhoto = 0
  let todayCount = 0
  for (const log of logs.value) {
    if (log.has_presence_photo) withPhoto += 1
    const ts = new Date(log.timestamp || 0)
    if (ts >= today) todayCount += 1
  }
  return { total: logs.value.length, withPhoto, today: todayCount }
})

const photoPct = computed(() => {
  if (!derivedStats.value.total) return 0
  return Math.round((derivedStats.value.withPhoto / derivedStats.value.total) * 100)
})
const todayPct = computed(() => {
  if (!derivedStats.value.total) return 0
  return Math.round((derivedStats.value.today / derivedStats.value.total) * 100)
})

const filteredLogs = computed(() => {
  const today = startOfToday()
  const q = searchQuery.value.trim().toLowerCase()
  return logs.value.filter((log) => {
    if (activeChip.value === 'photo' && !log.has_presence_photo) return false
    if (activeChip.value === 'today') {
      const ts = new Date(log.timestamp || 0)
      if (ts < today) return false
    }
    if (!q) return true
    const hay = [
      log.user_display,
      log.user_email,
      log.election_title,
      log.ip_address,
      log.confirmation_code,
      log.operating_system,
      log.event_type,
    ].join(' ').toLowerCase()
    return hay.includes(q)
  })
})

watch(filteredLogs, () => setPage(1))

const displayLogs = computed(() => {
  const start = (page.value - 1) * size.value
  return filteredLogs.value.slice(start, start + size.value)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredLogs.value.length / size.value) || 1))

watch([activeChip, searchQuery], () => setPage(1))
watch(totalPages, (pages) => {
  if (page.value > pages) setPage(pages)
})

const normalizeLogs = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  return []
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await auditApi.getCombined({ limit: 200 })
    logs.value = normalizeLogs(response.data)
    reset()
  } catch (error) {
    console.error('Failed to fetch voter audits:', error)
    logs.value = []
  } finally {
    loading.value = false
  }
}

const openDetail = async (auditId) => {
  selectedId.value = auditId
  detailLoading.value = true
  detail.value = null
  try {
    const { data } = await auditApi.getVoteDetail(auditId)
    if (data?.presence_photo_url) {
      data.presence_photo_url = resolveMediaUrl(data.presence_photo_url) || data.presence_photo_url
    }
    detail.value = data
  } catch (error) {
    console.error('Failed to load audit detail:', error)
    detail.value = null
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  selectedId.value = null
  detail.value = null
}

const applyLocalFilter = () => setPage(1)

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

const formatLocation = (loc) => {
  if (!loc) return '—'
  const place = [loc.city, loc.region, loc.country].filter(Boolean).join(', ')
  if (place) return place
  if (loc.latitude != null && loc.longitude != null) {
    const acc = loc.accuracy_m != null ? ` (±${Math.round(loc.accuracy_m)}m)` : ''
    return `${Number(loc.latitude).toFixed(5)}, ${Number(loc.longitude).toFixed(5)}${acc}`
  }
  return loc.ip_address || '—'
}

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
  max-width: 36rem;
  line-height: 1.45;
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

.audit-icon-btn--sm {
  width: 2.25rem;
  height: 2.25rem;
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
  min-width: min(100%, 18rem);
  padding: 0.65rem 0.9rem;
  border-radius: 9999px;
  border: 1px solid #ebeae4;
  background: #fff;
}

.audit-search i {
  color: #a3a3a3;
}

.audit-search input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 0.88rem;
  background: transparent;
}

.audit-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(18rem, 0.9fr);
  gap: 1rem;
  align-items: start;
}

.audit-card {
  background: #fff;
  border: 1px solid #ebeae4;
  border-radius: 1.25rem;
  padding: 1.1rem 1.15rem;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.03);
}

.audit-card--list {
  padding: 0.85rem 0.85rem 1rem;
}

.audit-list-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.35rem 0.55rem 0.85rem;
}

.audit-list-head h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.audit-list-head span {
  font-size: 0.75rem;
  color: #8a8a8a;
}

.audit-card__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 750;
  color: #1c1c1c;
}

.audit-card__hint {
  margin: 0.35rem 0 0;
  font-size: 0.82rem;
  color: #8a8a8a;
  line-height: 1.45;
}

.audit-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
}

.audit-row {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.7rem 0.65rem;
  border-radius: 0.9rem;
  cursor: pointer;
  border: 1px solid transparent;
}

.audit-row:hover,
.audit-row.is-selected {
  background: #f7f6f2;
  border-color: #ebeae4;
}

.audit-avatar {
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #edf2ef;
  color: #3d4f44;
}

.audit-row__title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: #1c1c1c;
}

.audit-row__sub {
  margin: 0.15rem 0 0;
  font-size: 0.75rem;
  color: #8a8a8a;
}

.audit-row__meta {
  display: grid;
  gap: 0.15rem;
  text-align: right;
}

.audit-row__date {
  font-size: 0.72rem;
  font-weight: 600;
  color: #5c5c5c;
}

.audit-row__ip {
  font-size: 0.68rem;
  color: #a3a3a3;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.audit-row__type {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  background: #edf2ef;
  color: #3d4f44;
}

.audit-empty {
  display: grid;
  place-items: center;
  gap: 0.55rem;
  padding: 2.5rem 1rem;
  color: #8a8a8a;
  font-size: 0.88rem;
}

.audit-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 0.85rem 0.4rem 0.2rem;
  font-size: 0.8rem;
  color: #6b6b6b;
}

.audit-pager__btn {
  border: 1px solid #ebeae4;
  background: #fff;
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
}

.audit-pager__btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.audit-side {
  display: grid;
  gap: 1rem;
}

.audit-detail__head {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
  margin-bottom: 0.85rem;
}

.audit-detail__eyebrow {
  margin: 0 0 0.25rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
}

.audit-presence {
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid #ebeae4;
  background: #f7f6f2;
  margin-bottom: 1rem;
}

.audit-presence img {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
}

.audit-presence p {
  margin: 0;
  padding: 0.55rem 0.75rem;
  font-size: 0.72rem;
  color: #6b6b6b;
}

.audit-presence--empty {
  display: grid;
  place-items: center;
  gap: 0.4rem;
  min-height: 8rem;
  color: #a3a3a3;
  font-size: 0.8rem;
}

.audit-facts {
  display: grid;
  gap: 0.65rem;
  margin: 0;
}

.audit-facts > div {
  display: grid;
  grid-template-columns: 7.5rem 1fr;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.audit-facts dt {
  margin: 0;
  color: #8a8a8a;
  font-weight: 600;
}

.audit-facts dd {
  margin: 0;
  color: #1c1c1c;
  font-weight: 600;
  word-break: break-word;
}

.audit-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.68rem;
  font-weight: 500 !important;
  line-height: 1.4;
}

.audit-ua {
  margin-top: 0.9rem;
  border-top: 1px solid #f0efe9;
  padding-top: 0.75rem;
  font-size: 0.78rem;
  color: #6b6b6b;
}

.audit-ua summary {
  cursor: pointer;
  font-weight: 650;
}

.audit-ua p {
  margin: 0.45rem 0 0;
  word-break: break-word;
  line-height: 1.4;
}

.audit-secrecy {
  margin: 1rem 0 0;
  display: flex;
  gap: 0.45rem;
  align-items: flex-start;
  font-size: 0.72rem;
  line-height: 1.4;
  color: #0f766e;
  background: #f0fdf9;
  border: 1px solid #ccfbf1;
  border-radius: 0.75rem;
  padding: 0.65rem 0.75rem;
}

.audit-meter {
  margin-top: 0.95rem;
}

.audit-meter__head {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  margin-bottom: 0.35rem;
  color: #6b6b6b;
}

.audit-meter__track {
  height: 0.4rem;
  border-radius: 999px;
  background: #f0efe9;
  overflow: hidden;
}

.audit-meter__fill {
  height: 100%;
  background: #3d4f44;
  border-radius: 999px;
}

.audit-meter__fill.is-slate {
  background: #8a7355;
}

.audit-meter__fill.is-soft {
  background: #a3b18a;
}

@media (max-width: 960px) {
  .audit-grid {
    grid-template-columns: 1fr;
  }

  .audit-row {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      "avatar main"
      "avatar meta"
      "type type";
  }

  .audit-avatar { grid-area: avatar; }
  .audit-row__main { grid-area: main; }
  .audit-row__meta { grid-area: meta; text-align: left; }
  .audit-row__type { grid-area: type; justify-self: start; }
}
</style>
