<template>
  <div
    ref="monitorContainer"
    class="monitor-room"
    :class="{ 'is-fullscreen': isFullscreen }"
    :style="themeStyle"
  >
    <!-- Header -->
    <header class="monitor-header">
      <div class="header-main">
        <div class="header-left">
          <button type="button" class="header-btn" title="Exit monitor" @click="exitMonitor">
            <i class="fas fa-arrow-left"></i>
          </button>
          <div class="header-titles">
            <p class="header-eyebrow">Election Monitor Room</p>
            <div class="header-title-row">
              <h1 class="header-title">{{ electionTitle }}</h1>
              <span v-if="electionStatus" class="status-badge">
                <span class="status-dot"></span>
                {{ statusLabel }}
              </span>
            </div>
          </div>
        </div>

        <div class="header-stats">
          <div class="header-stat">
            <span class="header-stat-label">Turnout</span>
            <span class="header-stat-value">{{ turnout }}%</span>
          </div>
          <div class="header-stat">
            <span class="header-stat-label">Voted</span>
            <span class="header-stat-value">{{ uniqueVoters }} / {{ eligibleVoters }}</span>
          </div>
          <div class="header-stat">
            <span class="header-stat-label">Closes In</span>
            <span class="header-stat-value countdown">{{ countdown }}</span>
          </div>
          <div class="header-stat">
            <span class="header-stat-label">Feed</span>
            <span class="header-stat-value feed-live">
              <span class="live-dot"></span> Live
            </span>
          </div>
        </div>

        <div class="header-actions">
          <button
            type="button"
            class="header-icon-btn"
            :title="isMonokai ? 'Switch to Normal theme' : 'Switch to Monokai theme'"
            @click="toggleTheme"
          >
            <i class="fas fa-cog"></i>
          </button>
          <button
            type="button"
            class="header-icon-btn"
            :class="{ spinning: refreshing }"
            title="Refresh data"
            @click="manualRefresh"
          >
            <i class="fas fa-sync-alt"></i>
          </button>
          <button
            type="button"
            class="header-icon-btn"
            :title="isFullscreen ? 'Exit full screen' : 'Full screen (F11)'"
            @click="toggleFullscreen"
          >
            <i :class="isFullscreen ? 'fas fa-compress' : 'fas fa-expand'"></i>
          </button>
        </div>
      </div>
    </header>

    <div v-if="loadError" class="monitor-error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ loadError }}</p>
      <div class="monitor-error-actions">
        <button type="button" @click="fetchMonitorData">Retry</button>
        <button v-if="needsLogin" type="button" class="monitor-login-btn" @click="goToLogin">
          Log in again
        </button>
      </div>
    </div>

    <div v-else-if="loading" class="monitor-loading">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading live data…</p>
    </div>

    <template v-else>
      <!-- Position navigation -->
      <nav class="position-nav">
        <div class="position-nav-scroll">
          <button
            v-for="pos in positions"
            :key="pos.uuid"
            type="button"
            class="position-tab"
            :class="{ active: currentPosition?.uuid === pos.uuid }"
            @click="switchPosition(pos.uuid)"
          >
            <i v-if="/president/i.test(pos.title)" class="fas fa-star position-star"></i>
            <span class="position-tab-title">{{ pos.title }}</span>
            <span v-if="pos.leader" class="position-tab-pct">{{ pos.leader.percentage }}%</span>
          </button>
        </div>
      </nav>

      <main class="monitor-body">
        <!-- Left: featured race + candidate grid -->
        <div class="monitor-pane monitor-pane-left">
          <section class="panel featured-section">
            <div class="featured-top">
              <div>
                <p class="panel-eyebrow">Featured Race</p>
                <h2 class="featured-title">{{ currentPositionTitle }}</h2>
                <p class="featured-sub">
                  {{ selectedPositionVotes }} position votes
                  <span v-if="leader"> · Live leader: {{ leader.full_name }}</span>
                </p>
              </div>
              <div class="ballots-submitted">
                <span class="ballots-label">Ballots Submitted</span>
                <span class="ballots-value">{{ uniqueVoters }}</span>
              </div>
            </div>

            <!-- Leader hero card -->
            <div v-if="leader" class="leader-hero">
                <img
                  v-if="leader.photo_url"
                  :src="resolveMediaUrl(leader.photo_url)"
                  :alt="leader.full_name"
                  class="leader-hero-photo"
                />
              <div v-else class="leader-hero-photo leader-hero-photo--placeholder">
                {{ leader.full_name?.charAt(0) }}
              </div>
              <div class="leader-hero-body">
                <div class="leader-hero-top">
                  <span class="leading-badge">LEADING</span>
                  <span class="leader-hero-name">{{ leader.full_name }}</span>
                </div>
                <div class="leader-hero-stats">
                  <span class="leader-hero-pct">{{ leader.percentage }}%</span>
                  <span class="leader-hero-votes">{{ leader.votes }} votes</span>
                </div>
                <div class="leader-hero-bar-track">
                  <div
                    class="leader-hero-bar-fill"
                    :style="{ width: `${leader.percentage}%` }"
                  ></div>
                </div>
              </div>
            </div>

            <!-- Candidate grid -->
            <div class="candidate-grid">
              <div
                v-for="(candidate, index) in gridCandidates"
                :key="candidate.uuid"
                class="candidate-card"
                :class="{ 'is-leader': index === 0 && candidate.votes > 0 }"
              >
                <img
                  v-if="candidate.photo_url"
                  :src="resolveMediaUrl(candidate.photo_url)"
                  :alt="candidate.full_name"
                  class="candidate-card-photo"
                />
                <div v-else class="candidate-card-photo candidate-card-photo--placeholder">
                  {{ candidate.full_name?.charAt(0) }}
                </div>
                <div class="candidate-card-body">
                  <span class="candidate-card-name">{{ candidate.full_name }}</span>
                  <div class="candidate-card-stats">
                    <span class="candidate-card-pct">{{ candidate.percentage }}%</span>
                    <span class="candidate-card-votes">{{ candidate.votes }} votes</span>
                  </div>
                  <div class="candidate-card-bar-track">
                    <div
                      class="candidate-card-bar-fill"
                      :class="{ 'is-leader': index === 0 }"
                      :style="{ width: `${candidate.percentage}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="sortedCandidates.length === 0" class="standings-empty">
              No candidates for this position
            </div>
          </section>
        </div>

        <!-- Right: position analytics -->
        <aside class="monitor-pane monitor-pane-right">
          <section class="panel charts-panel">
            <div class="charts-panel-header">
              <div>
                <p class="panel-eyebrow">Live Analytics</p>
                <h3 class="charts-panel-title">{{ currentPositionTitle }}</h3>
              </div>
              <span class="charts-updated">Updated {{ lastUpdated }}</span>
            </div>

            <div class="charts-grid">
              <div class="chart-card">
                <div class="chart-card-head">
                  <span class="chart-card-icon"><i class="fas fa-chart-pie"></i></span>
                  <div>
                    <p class="chart-card-label">Vote Distribution</p>
                    <p class="chart-card-hint">Share of votes in this race</p>
                  </div>
                </div>
                <div class="chart-wrap chart-wrap-sm">
                  <DonutChart
                    :labels="chartCandidateLabels"
                    :data="chartCandidateVotes"
                    :theme="chartTheme"
                    :theme-container="monitorContainer"
                    height="9.5rem"
                    legend-position="bottom"
                    empty-text="Awaiting votes"
                    aria-label="Vote distribution donut chart"
                  />
                </div>
              </div>

              <div class="chart-card">
                <div class="chart-card-head">
                  <span class="chart-card-icon"><i class="fas fa-chart-bar"></i></span>
                  <div>
                    <p class="chart-card-label">Candidate Performance</p>
                    <p class="chart-card-hint">Total votes per candidate</p>
                  </div>
                </div>
                <div class="chart-wrap chart-wrap-sm">
                  <BarChart
                    :labels="chartCandidateLabels"
                    :data="chartCandidateVotes"
                    :theme="chartTheme"
                    :theme-container="monitorContainer"
                    height="9.5rem"
                    empty-text="Awaiting votes"
                    aria-label="Candidate performance bar chart"
                  />
                </div>
              </div>

              <div class="chart-card">
                <div class="chart-card-head">
                  <span class="chart-card-icon"><i class="fas fa-chart-line"></i></span>
                  <div>
                    <p class="chart-card-label">Votes Per Hour</p>
                    <p class="chart-card-hint">Votes arriving each hour</p>
                  </div>
                </div>
                <div class="chart-wrap chart-wrap-sm">
                  <LineChart
                    :labels="hourlyTrend.labels"
                    :datasets="momentumDatasets"
                    :theme="chartTheme"
                    :theme-container="monitorContainer"
                    height="9.5rem"
                    show-legend
                    empty-text="Awaiting votes"
                    aria-label="Votes per hour line chart"
                  />
                </div>
              </div>

              <div class="chart-card">
                <div class="chart-card-head">
                  <span class="chart-card-icon"><i class="fas fa-users"></i></span>
                  <div>
                    <p class="chart-card-label">Turnout Progress</p>
                    <p class="chart-card-hint">Voter participation over time</p>
                  </div>
                </div>
                <div class="chart-wrap chart-wrap-sm">
                  <AreaChart
                    :labels="turnoutLabels"
                    :data="turnoutData"
                    label="Turnout %"
                    :theme="chartTheme"
                    :theme-container="monitorContainer"
                    height="9.5rem"
                    aria-label="Turnout progress area chart"
                  />
                </div>
              </div>
            </div>
          </section>
        </aside>
      </main>

      <!-- Live ticker footer -->
      <footer class="live-ticker">
        <div class="ticker-label">
          <span class="live-dot"></span>
          Live Positions
        </div>
        <div class="ticker-track">
          <div class="ticker-content">
            <span
              v-for="(item, i) in tickerItems"
              :key="`${item.position}-${i}`"
              class="ticker-item"
            >
              {{ item.position }} — {{ item.leader }} {{ item.percentage }}%
            </span>
            <span
              v-for="(item, i) in tickerItems"
              :key="`dup-${item.position}-${i}`"
              class="ticker-item"
              aria-hidden="true"
            >
              {{ item.position }} — {{ item.leader }} {{ item.percentage }}%
            </span>
          </div>
        </div>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { resultsApi } from '@/api/results'
import { electionApi } from '@/api/elections'
import { useAuthStore } from '@/stores/auth'
import { useMonitorTheme } from '@/composables/useMonitorTheme'
import { resolveMediaUrl } from '@/utils/media'
import DonutChart from '@/components/charts/DonutChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import LineChart from '@/components/charts/LineChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const electionUuid = computed(() => route.params.uuid)

const { isMonokai, themeStyle, toggleTheme } = useMonitorTheme()

const monitorContainer = ref(null)
const isFullscreen = ref(false)
const loading = ref(true)
const refreshing = ref(false)
const loadError = ref('')
const needsLogin = ref(false)

const electionTitle = ref('Election Monitor')
const electionStatus = ref('')
const electionEndDate = ref(null)
const totalVotes = ref(0)
const turnout = ref(0)
const uniqueVoters = ref(0)
const eligibleVoters = ref(0)
const lastUpdated = ref('—')
const countdown = ref('—')

const currentPosition = ref(null)
const positions = ref([])
const candidates = ref([])
const leader = ref(null)
const selectedPositionVotes = ref(0)
const hourlyTrend = ref({ labels: [], datasets: [] })
const cumulativeTurnout = ref({ labels: [], turnout: [] })

let countdownInterval = null
let refreshInterval = null

const sortedCandidates = computed(() => [...candidates.value].sort((a, b) => b.votes - a.votes))
const gridCandidates = computed(() => sortedCandidates.value)
const currentPositionTitle = computed(() => currentPosition.value?.title || 'President')
const chartTheme = computed(() => (isMonokai.value ? 'monokai' : 'normal'))
const chartCandidateLabels = computed(() => sortedCandidates.value.map((c) => c.full_name))
const chartCandidateVotes = computed(() => sortedCandidates.value.map((c) => c.votes))
const momentumDatasets = computed(() =>
  (hourlyTrend.value.datasets || []).map((series) => ({
    label: series.full_name,
    data: series.data || [],
  }))
)
const turnoutLabels = computed(() => cumulativeTurnout.value.labels || [])
const turnoutData = computed(() => cumulativeTurnout.value.turnout || [])

const statusLabel = computed(() => {
  const s = electionStatus.value
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
})

const tickerItems = computed(() =>
  positions.value
    .filter((p) => p.leader)
    .map((p) => ({
      position: p.title,
      leader: p.leader.full_name,
      percentage: p.leader.percentage,
    }))
)

const applyPositionData = (positionUuid) => {
  const pos = positions.value.find((p) => p.uuid === positionUuid)
  if (!pos) return

  currentPosition.value = pos
  candidates.value = pos.candidates || []
  selectedPositionVotes.value = pos.total_votes || 0
  hourlyTrend.value = pos.hourly_trend || { labels: [], datasets: [] }
  leader.value = pos.leader || (sortedCandidates.value[0]?.votes > 0 ? sortedCandidates.value[0] : null)
}

const switchPosition = (positionUuid) => {
  applyPositionData(positionUuid)
}

const formatTime = (iso) => {
  if (!iso) return new Date().toTimeString().slice(0, 8)
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const resolveErrorMessage = (error) => {
  if (!error?.response) {
    return 'Cannot connect to server. Ensure the backend is running (port 8000) and you are using the app at http://localhost:5173.'
  }
  const status = error.response.status
  const data = error.response.data
  if (status === 401) {
    needsLogin.value = true
    return 'Your session has expired. Please log in again.'
  }
  if (status === 403) {
    return 'You do not have permission to view this monitor room.'
  }
  if (status === 404) {
    return 'Election not found. Check that the monitor URL has a valid election ID.'
  }
  if (data?.error) return data.error
  if (data?.detail) return data.detail
  return 'Failed to load live data.'
}

const ensureAuthReady = async () => {
  if (!authStore.initialized) {
    await authStore.initialize()
  }
  if (!authStore.isAuthenticated || !localStorage.getItem('access_token')) {
    needsLogin.value = true
    loadError.value = 'Please log in to access the election monitor room.'
    loading.value = false
    return false
  }
  return true
}

const fetchLivePayload = async () => {
  const uuid = electionUuid.value
  if (!uuid) {
    throw { response: { status: 404, data: { error: 'Missing election ID in the monitor URL.' } } }
  }
  try {
    return await resultsApi.getLive(uuid)
  } catch (error) {
    if (error.response?.status === 404) {
      return electionApi.getMonitor(uuid)
    }
    throw error
  }
}

const updateCountdown = () => {
  if (!electionEndDate.value) {
    countdown.value = '—'
    return
  }
  const diff = new Date(electionEndDate.value).getTime() - Date.now()
  if (diff <= 0) {
    countdown.value = 'Closed'
    return
  }
  const d = Math.floor(diff / 86400000)
  const h = Math.floor((diff % 86400000) / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  countdown.value = `${d}d ${h}h ${m}m ${s}s`
}

const fetchMonitorData = async (silent = false) => {
  try {
    if (!silent) {
      loadError.value = ''
      needsLogin.value = false
    }

    const ready = await ensureAuthReady()
    if (!ready) return

    const { data } = await fetchLivePayload()

    electionTitle.value = data.election?.title || 'Election Monitor'
    electionStatus.value = data.election?.status || ''
    electionEndDate.value = data.election?.end_date || null
    totalVotes.value = data.stats?.total_votes || 0
    turnout.value = data.stats?.turnout || 0
    uniqueVoters.value = data.stats?.unique_voters || 0
    eligibleVoters.value = data.stats?.eligible_voters || 0
    lastUpdated.value = formatTime(data.updated_at)
    cumulativeTurnout.value = data.cumulative_turnout || { labels: [], turnout: [] }
    positions.value = data.positions || []

    if (positions.value.length > 0) {
      const activeUuid = currentPosition.value?.uuid
      const stillExists = activeUuid && positions.value.some((p) => p.uuid === activeUuid)
      const defaultPos = positions.value.find((p) => /president/i.test(p.title)) || positions.value[0]
      applyPositionData(stillExists ? activeUuid : defaultPos.uuid)
    } else {
      candidates.value = []
      leader.value = null
    }

    updateCountdown()
  } catch (error) {
    console.error('Failed to fetch monitor data:', error)
    if (!silent) {
      loadError.value = resolveErrorMessage(error)
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const manualRefresh = async () => {
  refreshing.value = true
  await fetchMonitorData(true)
}

const toggleFullscreen = async () => {
  try {
    if (!document.fullscreenElement) {
      await monitorContainer.value?.requestFullscreen?.()
    } else {
      await document.exitFullscreen?.()
    }
  } catch {
    isFullscreen.value = !isFullscreen.value
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const handleKeydown = (event) => {
  if (event.key === 'F11') {
    event.preventDefault()
    toggleFullscreen()
  }
}

const exitMonitor = () => {
  if (document.fullscreenElement) document.exitFullscreen?.()
  router.push(`/elections/${electionUuid.value}`)
}

const goToLogin = () => {
  authStore.clearLocalStorage()
  router.push('/login')
}

watch(() => route.params.uuid, () => {
  if (route.params.uuid) fetchMonitorData()
})

onMounted(async () => {
  countdownInterval = setInterval(updateCountdown, 1000)
  refreshInterval = setInterval(() => fetchMonitorData(true), 5000)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeydown)
  await fetchMonitorData()
})

onUnmounted(() => {
  if (countdownInterval) clearInterval(countdownInterval)
  if (refreshInterval) clearInterval(refreshInterval)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.monitor-room {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--mr-bg);
  color: var(--mr-text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  transition: background 0.35s ease, color 0.35s ease;
}

.monitor-room.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  overflow: hidden;
}

/* Header */
.monitor-header {
  flex-shrink: 0;
  padding: 0.85rem 1.25rem;
  background: var(--mr-topbar);
  border-bottom: 1px solid var(--mr-topbar-border);
  backdrop-filter: blur(10px);
}

.header-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1.25rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.header-btn {
  width: 2.1rem;
  height: 2.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border: 1px solid var(--mr-panel-border);
  background: transparent;
  color: var(--mr-muted);
  cursor: pointer;
}

.header-btn:hover {
  background: var(--mr-row);
  color: var(--mr-text);
}

.header-eyebrow {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--mr-muted);
}

.header-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.15rem;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  background: var(--mr-accent-bg);
  border: 1px solid var(--mr-accent-border);
  color: var(--mr-accent-soft);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 9999px;
  background: var(--mr-accent);
}

.header-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.header-stat {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.header-stat-label {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--mr-subtle);
}

.header-stat-value {
  font-size: 0.9rem;
  font-weight: 700;
  font-family: ui-monospace, monospace;
}

.header-stat-value.countdown {
  font-size: 0.8rem;
}

.feed-live {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--mr-accent-soft);
}

.live-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 9999px;
  background: var(--mr-accent);
  animation: live-pulse 1.4s ease-in-out infinite;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(0.85); }
}

.header-actions {
  display: flex;
  gap: 0.4rem;
}

.header-icon-btn {
  width: 2.1rem;
  height: 2.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  border: 1px solid var(--mr-panel-border);
  background: transparent;
  color: var(--mr-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.header-icon-btn:hover {
  background: var(--mr-row);
  color: var(--mr-accent);
  border-color: var(--mr-accent-border);
}

.header-icon-btn.spinning i {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Position nav */
.position-nav {
  flex-shrink: 0;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--mr-panel-border);
  background: var(--mr-topbar);
}

.position-nav-scroll {
  display: flex;
  gap: 0.45rem;
  overflow-x: auto;
  scrollbar-width: none;
}

.position-nav-scroll::-webkit-scrollbar {
  display: none;
}

.position-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.85rem;
  border-radius: 0.55rem;
  border: 1px solid transparent;
  background: var(--mr-row);
  color: var(--mr-muted);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s ease;
}

.position-tab:hover {
  color: var(--mr-text);
  border-color: var(--mr-panel-border);
}

.position-tab.active {
  background: var(--mr-accent-bg);
  border-color: var(--mr-accent-border);
  color: var(--mr-accent-soft);
}

.position-star {
  font-size: 0.6rem;
  color: var(--mr-accent);
}

.position-tab-pct {
  font-family: ui-monospace, monospace;
  font-size: 0.7rem;
  opacity: 0.85;
}

/* Body */
.monitor-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  min-height: 0;
  overflow: hidden;
}

@media (min-width: 768px) {
  .monitor-body {
    flex-direction: row;
    align-items: stretch;
  }
}

.monitor-pane {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  min-height: 0;
}

@media (min-width: 768px) {
  .monitor-pane {
    flex: 1 1 50%;
    width: 50%;
    max-width: 50%;
  }
}

.monitor-pane-left {
  overflow-y: auto;
}

.monitor-pane-right {
  overflow-y: auto;
}

@media (min-width: 768px) {
  .monitor-pane-right {
    border-left: 1px solid var(--mr-panel-border);
    padding-left: 1rem;
  }
}

.panel {
  background: var(--mr-panel);
  border: 1px solid var(--mr-panel-border);
  border-radius: 0.9rem;
  padding: 1rem 1.1rem;
}

.panel-eyebrow {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--mr-muted);
}

/* Featured section */
.featured-top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.featured-title {
  font-size: 1.35rem;
  font-weight: 700;
  margin-top: 0.2rem;
  letter-spacing: -0.02em;
}

.featured-sub {
  font-size: 0.78rem;
  color: var(--mr-muted);
  margin-top: 0.25rem;
}

.ballots-submitted {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
}

.ballots-label {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--mr-subtle);
}

.ballots-value {
  font-size: 1.5rem;
  font-weight: 800;
  font-family: ui-monospace, monospace;
  color: var(--mr-accent-soft);
}

/* Leader hero */
.leader-hero {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.75rem;
  background: var(--mr-accent-bg);
  border: 1px solid var(--mr-accent-border);
  margin-bottom: 1rem;
}

.leader-hero-photo {
  width: 4.5rem;
  height: 4.5rem;
  border-radius: 0.65rem;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--mr-accent-border);
}

.leader-hero-photo--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mr-track);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--mr-muted);
}

.leader-hero-body {
  flex: 1;
  min-width: 0;
}

.leader-hero-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.leading-badge {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 0.12rem 0.4rem;
  border-radius: 9999px;
  background: var(--mr-accent);
  color: #0f172a;
}

.leader-hero-name {
  font-size: 1.05rem;
  font-weight: 700;
}

.leader-hero-stats {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-top: 0.35rem;
}

.leader-hero-pct {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--mr-accent-soft);
  font-family: ui-monospace, monospace;
}

.leader-hero-votes {
  font-size: 0.8rem;
  color: var(--mr-muted);
}

.leader-hero-bar-track {
  margin-top: 0.6rem;
  height: 0.55rem;
  border-radius: 9999px;
  background: var(--mr-track);
  overflow: hidden;
}

.leader-hero-bar-fill {
  height: 100%;
  border-radius: 9999px;
  background: linear-gradient(90deg, var(--mr-accent), var(--mr-accent-soft));
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Candidate grid */
.candidate-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.65rem;
}

@media (min-width: 1024px) {
  .candidate-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.candidate-card {
  display: flex;
  gap: 0.65rem;
  padding: 0.75rem;
  border-radius: 0.65rem;
  background: var(--mr-row);
  border: 1px solid var(--mr-panel-border);
}

.candidate-card.is-leader {
  border-color: var(--mr-accent-border);
}

.candidate-card-photo {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.5rem;
  object-fit: cover;
  flex-shrink: 0;
}

.candidate-card-photo--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mr-track);
  font-weight: 700;
  color: var(--mr-muted);
}

.candidate-card-body {
  flex: 1;
  min-width: 0;
}

.candidate-card-name {
  font-size: 0.78rem;
  font-weight: 600;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.candidate-card-stats {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.2rem;
  font-size: 0.72rem;
  font-family: ui-monospace, monospace;
}

.candidate-card-pct {
  color: var(--mr-accent-soft);
  font-weight: 700;
}

.candidate-card-votes {
  color: var(--mr-muted);
}

.candidate-card-bar-track {
  margin-top: 0.35rem;
  height: 0.3rem;
  border-radius: 9999px;
  background: var(--mr-track);
  overflow: hidden;
}

.candidate-card-bar-fill {
  height: 100%;
  border-radius: 9999px;
  background: var(--mr-subtle);
  transition: width 0.6s ease;
}

.candidate-card-bar-fill.is-leader {
  background: linear-gradient(90deg, var(--mr-accent), var(--mr-accent-soft));
}

/* Charts */
.charts-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.charts-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.charts-panel-title {
  font-size: 1rem;
  font-weight: 700;
  margin-top: 0.15rem;
}

.charts-updated {
  font-size: 0.68rem;
  color: var(--mr-subtle);
  font-family: ui-monospace, monospace;
  white-space: nowrap;
}

.charts-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--mr-muted);
  font-size: 0.85rem;
}

.charts-empty i {
  font-size: 1.75rem;
  opacity: 0.4;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
  flex: 1;
  min-height: 0;
}

@media (min-width: 640px) {
  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.chart-card {
  background: var(--mr-row);
  border: 1px solid var(--mr-panel-border);
  border-radius: 0.7rem;
  padding: 0.7rem 0.8rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-card-head {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
  margin-bottom: 0.4rem;
}

.chart-card-icon {
  width: 1.65rem;
  height: 1.65rem;
  border-radius: 0.4rem;
  background: var(--mr-accent-bg);
  border: 1px solid var(--mr-accent-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mr-accent-soft);
  font-size: 0.7rem;
  flex-shrink: 0;
}

.chart-card-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--mr-text);
  line-height: 1.2;
}

.chart-card-hint {
  font-size: 0.6rem;
  color: var(--mr-subtle);
  margin-top: 0.1rem;
}

.chart-wrap {
  position: relative;
  width: 100%;
  flex: 1;
}

.chart-wrap-sm {
  height: 9.5rem;
  min-height: 9.5rem;
  position: relative;
}

.chart-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.55);
  border-radius: 0.5rem;
  color: var(--mr-subtle);
  font-size: 0.75rem;
  pointer-events: none;
}

/* Live ticker */
.live-ticker {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.55rem 1.25rem;
  background: var(--mr-topbar);
  border-top: 1px solid var(--mr-topbar-border);
  overflow: hidden;
}

.ticker-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--mr-accent-soft);
  white-space: nowrap;
  flex-shrink: 0;
}

.ticker-track {
  flex: 1;
  overflow: hidden;
  mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent);
}

.ticker-content {
  display: inline-flex;
  gap: 2.5rem;
  white-space: nowrap;
  animation: ticker-scroll 40s linear infinite;
}

.ticker-item {
  font-size: 0.75rem;
  color: var(--mr-muted);
}

.ticker-item::after {
  content: ' ·';
  margin-left: 2.5rem;
  opacity: 0.4;
}

@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.standings-empty {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--mr-muted);
  font-size: 0.85rem;
}

.monitor-error,
.monitor-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 1.5rem;
  color: var(--mr-muted);
  flex: 1;
}

.monitor-error i { color: #f87171; font-size: 1.5rem; }

.monitor-error button {
  margin-top: 0.5rem;
  padding: 0.55rem 1.1rem;
  border-radius: 0.5rem;
  border: none;
  background: var(--mr-accent);
  color: #0f172a;
  font-weight: 600;
  cursor: pointer;
}

.monitor-error-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}

.monitor-login-btn {
  background: transparent !important;
  border: 1px solid var(--mr-accent-border) !important;
  color: var(--mr-accent-soft) !important;
}

.monitor-loading i { font-size: 1.75rem; color: var(--mr-accent); }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--mr-scrollbar-track); }
::-webkit-scrollbar-thumb { background: var(--mr-scrollbar-thumb); border-radius: 2px; }
</style>
