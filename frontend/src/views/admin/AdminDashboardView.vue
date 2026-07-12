<template>
  <div class="admin-page">
    <div v-if="errorMessage" class="soft-alert">
      <span>{{ errorMessage }}</span>
      <button type="button" class="soft-btn soft-btn--inline" @click="fetchDashboard">Retry</button>
    </div>

    <!-- Atelier Soft template -->
    <div v-if="isAtelier" class="soft-dash">
    <!-- Row 1: KPI cards -->
    <section class="kpi-row">
      <article class="soft-card kpi-card">
        <div class="kpi-card__copy">
          <p class="kpi-card__label">Votes cast</p>
          <p class="kpi-card__value">{{ loading ? '—' : formatNumber(stats.total_votes) }}</p>
        </div>
        <div class="kpi-mini-bars" aria-hidden="true">
          <span
            v-for="(bar, idx) in miniBars"
            :key="idx"
            class="kpi-mini-bars__bar"
            :style="{ height: `${bar}%` }"
          ></span>
        </div>
      </article>

      <article class="soft-card kpi-card">
        <div class="kpi-card__icon kpi-card__icon--sage">
          <i class="fas fa-users"></i>
        </div>
        <div class="kpi-card__copy kpi-card__copy--center">
          <p class="kpi-card__label">Eligible voters</p>
          <p class="kpi-card__value">{{ loading ? '—' : formatNumber(stats.eligible_voters) }}</p>
        </div>
        <svg class="kpi-spark" viewBox="0 0 72 36" aria-hidden="true">
          <polyline
            fill="none"
            stroke="var(--vb-sage)"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            :points="sparkPoints"
          />
        </svg>
      </article>

      <article class="soft-card kpi-card">
        <div class="kpi-card__icon kpi-card__icon--sand">
          <i class="fas fa-user-check"></i>
        </div>
        <div class="kpi-card__copy kpi-card__copy--center">
          <p class="kpi-card__label">Candidates</p>
          <p class="kpi-card__value">{{ loading ? '—' : formatNumber(stats.total_candidates) }}</p>
        </div>
      </article>

      <article class="soft-card kpi-card kpi-card--accent">
        <div class="kpi-card__copy">
          <p class="kpi-card__label">Votes today</p>
          <p class="kpi-card__value">{{ loading ? '—' : formatNumber(stats.votes_today) }}</p>
        </div>
        <svg class="kpi-wave" viewBox="0 0 88 40" aria-hidden="true">
          <path
            d="M2 28 C14 8, 22 34, 34 20 S54 6, 66 22 S80 30, 86 14"
            fill="none"
            stroke="rgba(255,255,255,0.85)"
            stroke-width="2.5"
            stroke-linecap="round"
          />
        </svg>
      </article>
    </section>

    <!-- Row 2: main analytics -->
    <section class="mid-row">
      <article class="soft-card balance-card">
        <div class="balance-card__head">
          <div class="balance-card__title-wrap">
            <h2 class="soft-card__title">Turnout</h2>
            <span class="status-pill" :class="turnoutOnTrack ? 'is-good' : 'is-warn'">
              <span class="status-pill__dot"></span>
              {{ turnoutOnTrack ? 'On track' : 'Needs push' }}
            </span>
          </div>
          <span class="period-select">Last 7 days</span>
        </div>

        <div class="balance-metrics">
          <div class="metric-chip">
            <p class="metric-chip__label">Turnout</p>
            <div class="metric-chip__row">
              <span class="metric-chip__value">{{ loading ? '—' : `${stats.turnout}%` }}</span>
              <span
                v-if="voteTrend !== null"
                class="trend-pill"
                :class="voteTrend >= 0 ? 'is-up' : 'is-down'"
              >
                {{ voteTrend >= 0 ? '+' : '' }}{{ voteTrend }}%
              </span>
            </div>
          </div>
          <div class="metric-chip">
            <p class="metric-chip__label">Unique voters</p>
            <div class="metric-chip__row">
              <span class="metric-chip__value">{{ loading ? '—' : formatNumber(stats.unique_voters) }}</span>
              <span
                v-if="voterShare !== null"
                class="trend-pill is-up"
              >
                {{ voterShare }}%
              </span>
            </div>
          </div>
        </div>

        <div class="balance-chart">
          <AreaChart
            v-if="!loading"
            :labels="chartData.labels"
            :data="chartData.values"
            label="Votes"
            color="#a3b18a"
            :height="chartHeight"
            aria-label="Votes over the last seven days"
          />
          <div v-else class="chart-loading"><i class="fas fa-spinner fa-spin"></i></div>
        </div>
      </article>

      <article class="soft-card gauge-card">
        <p class="kpi-card__label">Participation</p>
        <p class="gauge-card__value">{{ loading ? '—' : formatNumber(stats.unique_voters) }}</p>
        <p class="gauge-card__hint">
          <template v-if="!loading && stats.eligible_voters > 0">
            Turnout is {{ stats.turnout }}% of {{ formatNumber(stats.eligible_voters) }} eligible voters.
          </template>
          <template v-else-if="!loading">
            No eligible voters loaded yet.
          </template>
          <template v-else>Loading participation…</template>
        </p>
        <div class="gauge-card__chart">
          <GaugeChart
            v-if="!loading"
            :value="stats.turnout"
            :max="100"
            color="#a3b18a"
            :center-label="`${Math.round(stats.turnout)}%`"
            :height="gaugeHeight"
            aria-label="Turnout percentage"
          />
          <div v-else class="chart-loading"><i class="fas fa-spinner fa-spin"></i></div>
        </div>
      </article>

      <article class="soft-card live-card">
        <div class="transfers-card__head">
          <h2 class="soft-card__title">Live elections</h2>
        </div>
        <ul v-if="!loading && liveElections.length" class="live-list">
          <li v-for="election in liveElections.slice(0, 4)" :key="election.uuid">
            <div class="live-list__copy">
              <p>{{ election.title }}</p>
              <span>{{ election.status }} · {{ formatNumber(election.votes_cast) }} votes · {{ election.turnout }}%</span>
            </div>
            <router-link
              v-if="election.status === 'open'"
              :to="`/monitor/${election.uuid}`"
              class="live-list__link"
            >
              Monitor
            </router-link>
            <router-link
              v-else
              :to="`/elections/${election.uuid}`"
              class="live-list__link"
            >
              Open
            </router-link>
          </li>
        </ul>
        <p v-else-if="loading" class="empty-note">Loading…</p>
        <p v-else class="empty-note">No open or scheduled elections.</p>
      </article>
    </section>

    <!-- Row 3: activity + shortcuts -->
    <section class="bottom-row">
      <article class="soft-card transfers-card">
        <div class="transfers-card__head">
          <h2 class="soft-card__title">Recent activity</h2>
        </div>
        <ul v-if="!loading && recentActivities.length" class="transfer-list">
          <li v-for="(item, idx) in recentActivities.slice(0, 5)" :key="`${item.time}-${idx}`" class="transfer-item">
            <div class="transfer-item__avatar" :class="`tone-${item.type}`">
              <i :class="item.icon"></i>
            </div>
            <div class="transfer-item__copy">
              <p class="transfer-item__title">{{ item.message }}</p>
              <p class="transfer-item__time">{{ item.time }}</p>
            </div>
            <span class="trend-pill" :class="activityTone(item.type)">
              {{ activityLabel(item.type) }}
            </span>
          </li>
        </ul>
        <div v-else-if="loading" class="chart-loading chart-loading--sm"><i class="fas fa-spinner fa-spin"></i></div>
        <p v-else class="empty-note">No recent activity yet.</p>
      </article>

      <article class="soft-card shortcuts-card">
        <div class="transfers-card__head">
          <h2 class="soft-card__title">Quick actions</h2>
        </div>
        <div class="shortcut-grid">
          <router-link
            v-for="link in dashboardShortcuts"
            :key="link.path"
            :to="link.path"
            class="shortcut-link"
          >
            <span class="shortcut-link__icon" :class="link.tone"><i :class="link.icon"></i></span>
            <span>
              <strong>{{ link.title }}</strong>
              <small>{{ link.description }}</small>
            </span>
          </router-link>
        </div>
      </article>
    </section>
    </div>

    <!-- Operations template -->
    <div v-else class="ops-dash">
      <div class="stat-grid page-section">
        <StatCard
          v-for="card in opsStatCards"
          :key="card.label"
          :label="card.label"
          :value="loading ? '—' : card.value"
          :hint="loading ? 'Loading…' : card.hint"
          :icon="card.icon"
          :tone="card.tone"
        />
      </div>

      <div class="ops-charts page-section">
        <DataPanel title="Voting activity" subtitle="Ballots cast over the last 7 days">
          <AreaChart
            v-if="!loading"
            :labels="chartData.labels"
            :data="chartData.values"
            label="Votes"
            color="#a3b18a"
            height="14rem"
            aria-label="Voting activity over the last seven days"
          />
          <div v-else class="chart-loading"><i class="fas fa-spinner fa-spin"></i></div>
        </DataPanel>

        <DataPanel title="Recent activity" subtitle="Latest authenticated events">
          <ul v-if="!loading && recentActivities.length" class="ops-activity">
            <li v-for="(item, idx) in recentActivities.slice(0, 6)" :key="`${item.time}-${idx}`">
              <i :class="item.icon"></i>
              <div>
                <p>{{ item.message }}</p>
                <span>{{ item.time }}</span>
              </div>
            </li>
          </ul>
          <p v-else-if="loading" class="empty-note">Loading…</p>
          <p v-else class="empty-note">No recent activity yet.</p>
        </DataPanel>
      </div>

      <section class="page-section">
        <div class="section-head">
          <h2 class="section-title">Quick access</h2>
          <p class="section-subtitle">Jump to common election tasks</p>
        </div>
        <div class="quick-link-grid">
          <router-link
            v-for="link in opsQuickLinks"
            :key="link.path"
            :to="link.path"
            class="quick-link-card"
          >
            <div class="quick-link-icon" :class="link.tone">
              <i :class="link.icon"></i>
            </div>
            <div class="quick-link-body">
              <h3 class="quick-link-title">{{ link.title }}</h3>
              <p class="quick-link-desc">{{ link.description }}</p>
            </div>
            <i class="fas fa-arrow-right quick-link-arrow"></i>
          </router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import { useThemeStore } from '@/stores/theme'
import AreaChart from '@/components/charts/AreaChart.vue'
import GaugeChart from '@/components/charts/GaugeChart.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'

const REFRESH_MS = 30000

const themeStore = useThemeStore()
const isAtelier = computed(() => themeStore.isAtelierDashboard)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1200)
const chartHeight = computed(() => (viewportWidth.value < 640 ? '8.5rem' : '11.5rem'))
const gaugeHeight = computed(() => (viewportWidth.value < 640 ? '8rem' : '9.5rem'))

const onResize = () => {
  viewportWidth.value = window.innerWidth
}
const loading = ref(true)
const errorMessage = ref('')

const context = ref({
  display_name: '…',
  role_label: 'Election Committee',
  greeting: 'day',
  today_date: '',
})

const stats = ref({
  total_elections: 0,
  active_elections: 0,
  scheduled_elections: 0,
  closed_elections: 0,
  total_voters: 0,
  eligible_voters: 0,
  unique_voters: 0,
  total_votes: 0,
  total_candidates: 0,
  turnout: 0,
  votes_today: 0,
})

const liveElections = ref([])
const chartData = ref({ labels: [], values: [] })
const recentActivities = ref([])

const turnoutOnTrack = computed(() => Number(stats.value.turnout) >= 40)

const voteTrend = computed(() => {
  const values = chartData.value.values || []
  if (values.length < 4) return null
  const recent = values.slice(-3).reduce((a, b) => a + b, 0)
  const prior = values.slice(0, 3).reduce((a, b) => a + b, 0)
  if (prior === 0) return recent > 0 ? 100 : 0
  return Math.round(((recent - prior) / prior) * 1000) / 10
})

const voterShare = computed(() => {
  if (!stats.value.total_voters) return null
  return Math.round((stats.value.unique_voters / stats.value.total_voters) * 1000) / 10
})

const miniBars = computed(() => {
  const values = chartData.value.values || []
  if (!values.length) return [35, 55, 40, 70, 50]
  const max = Math.max(...values, 1)
  return values.slice(-5).map((v) => Math.max(18, Math.round((v / max) * 100)))
})

const sparkPoints = computed(() => {
  const values = chartData.value.values || []
  const series = values.length ? values : [2, 4, 3, 6, 5, 8, 7]
  const max = Math.max(...series, 1)
  const step = series.length > 1 ? 72 / (series.length - 1) : 72
  return series
    .map((v, i) => {
      const x = i * step
      const y = 32 - (v / max) * 26
      return `${x},${y}`
    })
    .join(' ')
})

const formatNumber = (value) => {
  const n = Number(value) || 0
  return new Intl.NumberFormat('en-US').format(n)
}

const activityTone = (type) => {
  if (type === 'vote' || type === 'election') return 'is-up'
  if (type === 'login') return 'is-neutral'
  return 'is-down'
}

const activityLabel = (type) => {
  if (type === 'vote') return 'Vote'
  if (type === 'election') return 'Election'
  if (type === 'login') return 'Auth'
  return 'Event'
}

const opsStatCards = computed(() => [
  {
    label: 'Votes Cast',
    value: formatNumber(stats.value.total_votes),
    hint: `${formatNumber(stats.value.unique_voters)} unique voters`,
    icon: 'fas fa-check-double',
    tone: 'tone-teal',
  },
  {
    label: 'Turnout',
    value: `${stats.value.turnout}%`,
    hint: `${formatNumber(stats.value.eligible_voters)} eligible`,
    icon: 'fas fa-chart-line',
    tone: 'tone-amber',
  },
  {
    label: 'Eligible Voters',
    value: formatNumber(stats.value.eligible_voters),
    hint: `${formatNumber(stats.value.total_voters)} students`,
    icon: 'fas fa-users',
    tone: 'tone-blue',
  },
  {
    label: 'Active Elections',
    value: formatNumber(stats.value.active_elections),
    hint: `${formatNumber(stats.value.total_elections)} total`,
    icon: 'fas fa-calendar-check',
    tone: 'tone-slate',
  },
])

const opsQuickLinks = computed(() => {
  const links = [
    { path: '/elections', title: 'Manage Elections', description: 'Positions, candidates, and voters', icon: 'fas fa-calendar-check', tone: 'tone-teal' },
    { path: '/results', title: 'Results & Certification', description: 'Generate and publish results', icon: 'fas fa-chart-bar', tone: 'tone-blue' },
    { path: '/strongroom', title: 'Strongroom', description: 'Seals and vault integrity', icon: 'fas fa-shield-alt', tone: 'tone-amber' },
    { path: '/fraud', title: 'Fraud Monitor', description: 'Suspicious voting alerts', icon: 'fas fa-user-shield', tone: 'tone-rose' },
  ]
  const openElection = liveElections.value.find((e) => e.status === 'open')
  if (openElection) {
    links.unshift({
      path: `/monitor/${openElection.uuid}`,
      title: 'Live Monitor Room',
      description: 'Real-time turnout & votes',
      icon: 'fas fa-tv',
      tone: 'tone-emerald',
    })
  }
  return links
})

const dashboardShortcuts = computed(() => opsQuickLinks.value.slice(0, 4))

const applyDashboardData = (data) => {
  if (data.context) {
    context.value = { ...context.value, ...data.context }
  }
  stats.value = { ...stats.value, ...data.stats }
  liveElections.value = data.live_elections || []
  recentActivities.value = data.recent_activities || []
  chartData.value = {
    labels: data.chart_data?.labels || [],
    values: data.chart_data?.values || [],
  }
}

const fetchDashboard = async (options = {}) => {
  const { silent = false } = options
  if (!silent) {
    loading.value = true
    errorMessage.value = ''
  }
  try {
    const { data } = await dashboardApi.getAdminDashboard()
    applyDashboardData(data)
    if (!silent) loading.value = false
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    if (!silent) {
      const status = error.response?.status
      if (status === 404) {
        errorMessage.value = 'Dashboard API not found. Restart the Django server.'
      } else if (status === 403 || status === 401) {
        errorMessage.value = 'Session expired. Please sign in again.'
      } else if (!error.response) {
        errorMessage.value = 'Cannot reach the backend. Make sure it is running on port 8000.'
      } else {
        errorMessage.value = error.response?.data?.error || 'Failed to load dashboard data.'
      }
      loading.value = false
    }
  }
}

let refreshTimer = null

onMounted(() => {
  onResize()
  window.addEventListener('resize', onResize)
  fetchDashboard()
  refreshTimer = setInterval(() => fetchDashboard({ silent: true }), REFRESH_MS)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.soft-dash,
.ops-dash {
  max-width: none;
  width: 100%;
}

.ops-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

@media (min-width: 900px) {
  .ops-charts {
    grid-template-columns: 1.4fr 1fr;
    gap: 1rem;
  }
}

.ops-activity {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.ops-activity li {
  display: flex;
  gap: 0.65rem;
  align-items: flex-start;
  min-width: 0;
}

.ops-activity i {
  width: 2rem;
  height: 2rem;
  border-radius: 9999px;
  background: var(--vb-accent-soft);
  color: var(--vb-accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.ops-activity p {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--vb-ink);
  overflow-wrap: anywhere;
}

.ops-activity span {
  font-size: 0.72rem;
  color: var(--vb-muted);
}

.soft-btn--inline {
  margin-top: 0;
}

.soft-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border-radius: 1rem;
  background: #fdeaea;
  color: #9f2f2f;
  margin-bottom: 0.85rem;
  font-size: 0.84rem;
}

.soft-card {
  background: #fff;
  border-radius: 1.25rem;
  box-shadow: var(--vb-card-shadow);
  padding: 1rem 1.05rem;
  min-width: 0;
}

.soft-card__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  color: var(--vb-ink);
  letter-spacing: -0.02em;
}

.soft-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  margin-top: 1rem;
  padding: 0.75rem 1.15rem;
  border-radius: 9999px;
  background: var(--vb-accent);
  color: #fff;
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease;
}

.soft-btn:hover {
  background: var(--vb-accent-hover);
  transform: translateY(-1px);
}

.kpi-row,
.mid-row,
.bottom-row {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.kpi-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-height: 4.5rem;
  padding: 0.85rem 0.8rem;
}

.kpi-card__copy {
  min-width: 0;
  flex: 1;
}

.kpi-card__label {
  margin: 0;
  font-size: 0.78rem;
  color: var(--vb-muted);
  font-weight: 500;
}

.kpi-card__value {
  margin: 0.3rem 0 0;
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink);
  line-height: 1;
}

.kpi-card__icon {
  width: 2.15rem;
  height: 2.15rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.8rem;
}

.kpi-card__icon--sage {
  background: #e8efe6;
  color: var(--vb-accent);
}

.kpi-card__icon--sand {
  background: #f3efe6;
  color: #8a7355;
}

.kpi-card--accent {
  background: var(--vb-accent);
  color: #fff;
}

.kpi-card--accent .kpi-card__label {
  color: rgba(255, 255, 255, 0.72);
}

.kpi-card--accent .kpi-card__value {
  color: #fff;
}

.kpi-mini-bars {
  display: none;
  align-items: flex-end;
  gap: 0.22rem;
  height: 2rem;
}

.kpi-mini-bars__bar {
  width: 0.32rem;
  border-radius: 9999px;
  background: var(--vb-sage);
}

.kpi-mini-bars__bar:nth-child(odd) {
  background: var(--vb-accent);
}

.kpi-spark,
.kpi-wave {
  display: none;
  width: 3.1rem;
  height: 1.6rem;
  flex-shrink: 0;
}

.mid-row,
.bottom-row {
  grid-template-columns: 1fr;
}

.balance-card__head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.45rem;
  margin-bottom: 0.85rem;
}

.balance-card__title-wrap {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: var(--vb-muted);
}

.status-pill__dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 9999px;
  background: var(--vb-sage);
}

.status-pill.is-warn .status-pill__dot {
  background: #d4a017;
}

.period-select {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: var(--vb-muted);
  font-weight: 600;
}

.balance-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
  margin-bottom: 0.65rem;
}

.metric-chip {
  background: #f7f6f2;
  border-radius: 0.9rem;
  padding: 0.7rem 0.75rem;
  min-width: 0;
}

.metric-chip__label {
  margin: 0;
  font-size: 0.75rem;
  color: var(--vb-muted);
}

.metric-chip__row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.35rem;
  flex-wrap: wrap;
}

.metric-chip__value {
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink);
}

.trend-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.18rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.trend-pill.is-up {
  background: var(--vb-positive-bg);
  color: var(--vb-positive);
}

.trend-pill.is-down {
  background: var(--vb-negative-bg);
  color: var(--vb-negative);
}

.trend-pill.is-neutral {
  background: #f0efe9;
  color: #6b6b6b;
}

.balance-chart {
  margin-top: 0.25rem;
  min-width: 0;
}

.gauge-card__value {
  margin: 0.3rem 0 0;
  font-size: 1.45rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.gauge-card__hint {
  margin: 0.45rem 0 0;
  font-size: 0.82rem;
  color: var(--vb-muted);
  line-height: 1.45;
  max-width: none;
}

.gauge-card__chart {
  margin-top: 0.35rem;
}

.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  justify-content: center;
  padding: 1.25rem 1rem;
}

.profile-card__avatar {
  width: 4rem;
  height: 4rem;
  border-radius: 9999px;
  background: linear-gradient(145deg, #d8e0cf, #a3b18a);
  color: var(--vb-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 800;
  box-shadow: inset 0 0 0 3px #fff, 0 8px 18px rgba(61, 79, 68, 0.1);
}

.profile-card__name {
  margin: 0.75rem 0 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--vb-ink);
  overflow-wrap: anywhere;
}

.profile-card__email {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
  color: var(--vb-muted);
  overflow-wrap: anywhere;
}

.profile-card__stats {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.35rem;
  margin-top: 1.1rem;
  padding-top: 0.9rem;
  border-top: 1px solid var(--vb-line);
}

.profile-card__stats strong {
  display: block;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.profile-card__stats span {
  font-size: 0.68rem;
  color: var(--vb-muted);
}

.cta-card {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.9rem;
  align-items: center;
  padding: 1.15rem 1.1rem;
  overflow: hidden;
}

.cta-card__copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.cta-card__text {
  margin: 0;
  font-size: 0.86rem;
  color: var(--vb-muted);
  line-height: 1.5;
  max-width: none;
}

.soft-btn--cta {
  margin-top: 0.35rem;
  width: auto;
}

.cta-card__art {
  position: relative;
  height: 6.75rem;
  min-height: 6.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  order: -1;
  width: 100%;
  max-width: 13rem;
  justify-self: center;
}

.ballot-stack {
  position: absolute;
  width: 5.75rem;
  height: 3.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 8px 16px rgba(28, 28, 28, 0.1);
}

.ballot-stack--back {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(61, 79, 68, 0.15);
  transform: translate(-0.9rem, -0.4rem) rotate(-24deg);
}

.ballot-stack--mid {
  background: #a3b18a;
  transform: translate(0.1rem, 0) rotate(-8deg);
}

.ballot-stack--front {
  background: #1f2a36;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.65rem 0.8rem;
  transform: translate(0.95rem, 0.5rem) rotate(8deg);
}

.ballot-stack--front span {
  display: block;
  height: 0.28rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.35);
}

.ballot-stack--front span:nth-child(2) { width: 70%; }
.ballot-stack--front span:nth-child(3) { width: 45%; }

.transfers-card__head {
  margin-bottom: 0.75rem;
}

.live-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.live-list li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.live-list__copy {
  min-width: 0;
  flex: 1;
}

.live-list__copy p {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--vb-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.live-list__copy span {
  display: block;
  margin-top: 0.15rem;
  font-size: 0.72rem;
  color: var(--vb-muted);
  text-transform: capitalize;
}

.live-list__link {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--vb-accent);
  text-decoration: none;
}

.shortcut-grid {
  display: grid;
  gap: 0.65rem;
}

.shortcut-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 0.75rem;
  border-radius: 1rem;
  background: #f7f6f2;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}

.shortcut-link__icon {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.8rem;
}

.shortcut-link strong {
  display: block;
  font-size: 0.84rem;
  color: var(--vb-ink);
}

.shortcut-link small {
  display: block;
  margin-top: 0.1rem;
  font-size: 0.72rem;
  color: var(--vb-muted);
}

.transfer-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.transfer-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}

.transfer-item__avatar {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0efe9;
  color: var(--vb-accent);
  flex-shrink: 0;
  font-size: 0.75rem;
}

.transfer-item__avatar.tone-vote { background: #e8efe6; }
.transfer-item__avatar.tone-login { background: #f3efe6; color: #8a7355; }

.transfer-item__copy {
  min-width: 0;
  flex: 1;
}

.transfer-item__title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--vb-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.transfer-item__time {
  margin: 0.12rem 0 0;
  font-size: 0.7rem;
  color: var(--vb-muted);
}

.security-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  justify-content: center;
  padding: 1.35rem 1.1rem;
}

.security-card__icon {
  width: 3.4rem;
  height: 3.4rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0efe9;
  color: var(--vb-accent);
  font-size: 1.3rem;
  margin-bottom: 0.7rem;
}

.security-card__text {
  margin: 0.45rem 0 0;
  font-size: 0.84rem;
  color: var(--vb-muted);
  line-height: 1.5;
  max-width: 18rem;
}

.security-card .soft-btn {
  width: 100%;
  max-width: 16rem;
}

.empty-note {
  margin: 1.25rem 0;
  text-align: center;
  color: var(--vb-muted);
  font-size: 0.84rem;
}

.chart-loading {
  height: 8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--vb-accent);
}

.chart-loading--sm {
  height: 5rem;
}

@media (min-width: 480px) {
  .kpi-mini-bars {
    display: flex;
  }

  .kpi-spark,
  .kpi-wave {
    display: block;
  }

  .kpi-card {
    gap: 0.7rem;
    min-height: 5rem;
    padding: 0.95rem 1rem;
  }

  .kpi-card__value {
    font-size: 1.35rem;
  }

  .kpi-card__icon {
    width: 2.4rem;
    height: 2.4rem;
    font-size: 0.88rem;
  }

  .metric-chip {
    border-radius: 1rem;
    padding: 0.8rem 0.9rem;
  }

  .metric-chip__value {
    font-size: 1.2rem;
  }
}

@media (min-width: 640px) {
  .soft-card {
    border-radius: var(--vb-card-radius, 1.5rem);
    padding: 1.2rem 1.25rem;
  }

  .soft-card__title {
    font-size: 1.05rem;
  }

  .kpi-row,
  .mid-row,
  .bottom-row {
    gap: 0.9rem;
    margin-bottom: 1rem;
  }

  .kpi-card {
    min-height: 5.75rem;
    gap: 0.85rem;
  }

  .kpi-card__value {
    font-size: 1.45rem;
  }

  .balance-card__head {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .metric-chip__value {
    font-size: 1.3rem;
  }

  .cta-card {
    grid-template-columns: minmax(0, 1.35fr) minmax(7rem, 0.8fr);
    gap: 1.15rem 1.35rem;
    padding: 1.3rem 1.4rem;
  }

  .cta-card__art {
    order: 0;
    height: 8rem;
    min-height: 8rem;
    max-width: none;
    justify-self: stretch;
  }

  .ballot-stack {
    width: 6.5rem;
    height: 4rem;
  }

  .cta-card__text {
    max-width: 26rem;
  }

  .soft-btn--cta {
    width: auto;
  }

  .security-card .soft-btn {
    width: auto;
  }

  .chart-loading {
    height: 10rem;
  }
}

@media (min-width: 900px) {
  .mid-row {
    grid-template-columns: 1fr 1fr;
  }

  .mid-row .balance-card {
    grid-column: 1 / -1;
  }
}

@media (min-width: 1100px) {
  .kpi-row {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
  }

  .mid-row {
    grid-template-columns: 1.45fr 0.85fr 0.85fr;
    gap: 1rem;
  }

  .mid-row .balance-card {
    grid-column: auto;
  }

  .bottom-row {
    grid-template-columns: 1.35fr 1fr;
    gap: 1rem;
  }

  .kpi-card {
    min-height: 6.25rem;
  }

  .kpi-card__value {
    font-size: 1.55rem;
  }

  .gauge-card__value {
    font-size: 1.7rem;
  }

  .profile-card {
    padding-top: 1.5rem;
    padding-bottom: 1.35rem;
  }

  .profile-card__avatar {
    width: 4.75rem;
    height: 4.75rem;
    font-size: 1.6rem;
  }
}

@media (max-width: 479px) {
  .soft-alert {
    flex-direction: column;
    align-items: stretch;
  }

  .transfer-item .trend-pill {
    display: none;
  }
}
</style>
