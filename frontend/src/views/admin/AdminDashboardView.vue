<template>
  <div class="admin-page soft-dash">
    <div v-if="errorMessage" class="soft-alert">
      <span>{{ errorMessage }}</span>
      <button type="button" class="soft-btn" @click="fetchDashboard">Retry</button>
    </div>

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
          <div class="period-select">
            <span>Last 7 days</span>
            <i class="fas fa-chevron-down"></i>
          </div>
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
            height="11.5rem"
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
            height="9.5rem"
            aria-label="Turnout percentage"
          />
          <div v-else class="chart-loading"><i class="fas fa-spinner fa-spin"></i></div>
        </div>
      </article>

      <article class="soft-card profile-card">
        <div class="profile-card__avatar">{{ userInitial }}</div>
        <h3 class="profile-card__name">{{ userDisplayName }}</h3>
        <p class="profile-card__email">{{ userEmail || context.role_label }}</p>
        <div class="profile-card__stats">
          <div>
            <strong>{{ loading ? '—' : formatNumber(stats.total_elections) }}</strong>
            <span>Elections</span>
          </div>
          <div>
            <strong>{{ loading ? '—' : formatNumber(stats.total_voters) }}</strong>
            <span>Students</span>
          </div>
          <div>
            <strong>{{ loading ? '—' : formatNumber(stats.active_elections) }}</strong>
            <span>Live</span>
          </div>
        </div>
      </article>
    </section>

    <!-- Row 3: actions & activity -->
    <section class="bottom-row">
      <article class="soft-card cta-card">
        <div class="cta-card__copy">
          <h2 class="soft-card__title">Election workspace</h2>
          <p class="cta-card__text">
            {{ liveElectionCopy }}
          </p>
          <router-link to="/elections" class="soft-btn">
            Manage elections
            <span aria-hidden="true">+</span>
          </router-link>
        </div>
        <div class="cta-card__art" aria-hidden="true">
          <div class="ballot-stack ballot-stack--back"></div>
          <div class="ballot-stack ballot-stack--mid"></div>
          <div class="ballot-stack ballot-stack--front">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </article>

      <article class="soft-card transfers-card">
        <div class="transfers-card__head">
          <h2 class="soft-card__title">Recent activity</h2>
        </div>
        <ul v-if="!loading && recentActivities.length" class="transfer-list">
          <li v-for="(item, idx) in recentActivities.slice(0, 4)" :key="`${item.time}-${idx}`" class="transfer-item">
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

      <article class="soft-card security-card">
        <div class="security-card__icon" aria-hidden="true">
          <i class="fas fa-fingerprint"></i>
        </div>
        <h2 class="soft-card__title">Keep ballots safe</h2>
        <p class="security-card__text">
          Review vault seals and strongroom integrity to protect election outcomes.
        </p>
        <router-link to="/strongroom" class="soft-btn">
          Open strongroom
        </router-link>
      </article>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import { useAuthStore } from '@/stores/auth'
import { displayUserName } from '@/utils/user'
import AreaChart from '@/components/charts/AreaChart.vue'
import GaugeChart from '@/components/charts/GaugeChart.vue'

const REFRESH_MS = 30000

const authStore = useAuthStore()
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

const userDisplayName = computed(() => {
  if (context.value.display_name && context.value.display_name !== '…') {
    return context.value.display_name
  }
  return displayUserName(authStore.user)
})

const userEmail = computed(() => authStore.user?.email || '')
const userInitial = computed(() => userDisplayName.value.charAt(0).toUpperCase())

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

const liveElectionCopy = computed(() => {
  const open = liveElections.value.filter((e) => e.status === 'open')
  if (open.length === 1) {
    return `${open[0].title} is live with ${formatNumber(open[0].votes_cast)} votes cast so far.`
  }
  if (open.length > 1) {
    return `${open.length} elections are currently open. Jump in to manage positions, candidates, and voters.`
  }
  if (stats.value.scheduled_elections > 0) {
    return `${stats.value.scheduled_elections} election${stats.value.scheduled_elections === 1 ? '' : 's'} scheduled. Prepare ballots and eligibility lists.`
  }
  return 'Create and manage elections, positions, candidates, and voter lists from one place.'
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
  fetchDashboard()
  refreshTimer = setInterval(() => fetchDashboard({ silent: true }), REFRESH_MS)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.soft-dash {
  max-width: none;
}

.soft-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1.1rem;
  border-radius: 1rem;
  background: #fdeaea;
  color: #9f2f2f;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.soft-card {
  background: #fff;
  border-radius: var(--vb-card-radius, 1.5rem);
  box-shadow: var(--vb-card-shadow);
  padding: 1.25rem 1.35rem;
}

.soft-card__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--vb-ink);
  letter-spacing: -0.02em;
}

.soft-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 1.1rem;
  padding: 0.85rem 1.25rem;
  border-radius: 9999px;
  background: var(--vb-accent);
  color: #fff;
  font-size: 0.84rem;
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
  gap: 1rem;
  margin-bottom: 1rem;
}

.kpi-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (min-width: 1100px) {
  .kpi-row {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-height: 6.5rem;
}

.kpi-card__copy {
  min-width: 0;
  flex: 1;
}

.kpi-card__copy--center {
  text-align: left;
}

.kpi-card__label {
  margin: 0;
  font-size: 0.82rem;
  color: var(--vb-muted);
  font-weight: 500;
}

.kpi-card__value {
  margin: 0.35rem 0 0;
  font-size: 1.55rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink);
  line-height: 1;
}

.kpi-card__icon {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.95rem;
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
  display: flex;
  align-items: flex-end;
  gap: 0.28rem;
  height: 2.6rem;
}

.kpi-mini-bars__bar {
  width: 0.42rem;
  border-radius: 9999px;
  background: var(--vb-sage);
}

.kpi-mini-bars__bar:nth-child(odd) {
  background: var(--vb-accent);
}

.kpi-spark,
.kpi-wave {
  width: 4.5rem;
  height: 2.25rem;
  flex-shrink: 0;
}

.mid-row {
  grid-template-columns: 1fr;
}

@media (min-width: 1100px) {
  .mid-row {
    grid-template-columns: 1.45fr 0.85fr 0.85fr;
  }
}

.balance-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.balance-card__title-wrap {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: var(--vb-muted);
}

.status-pill__dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 9999px;
  background: var(--vb-sage);
}

.status-pill.is-warn .status-pill__dot {
  background: #d4a017;
}

.period-select {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  color: var(--vb-muted);
  font-weight: 600;
}

.balance-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.metric-chip {
  background: #f7f6f2;
  border-radius: 1.15rem;
  padding: 0.9rem 1rem;
}

.metric-chip__label {
  margin: 0;
  font-size: 0.78rem;
  color: var(--vb-muted);
}

.metric-chip__row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-top: 0.45rem;
  flex-wrap: wrap;
}

.metric-chip__value {
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink);
}

.trend-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  font-size: 0.7rem;
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
  margin-top: 0.35rem;
}

.gauge-card__value {
  margin: 0.35rem 0 0;
  font-size: 1.7rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.gauge-card__hint {
  margin: 0.55rem 0 0;
  font-size: 0.84rem;
  color: var(--vb-muted);
  line-height: 1.45;
  max-width: 16rem;
}

.gauge-card__chart {
  margin-top: 0.5rem;
}

.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  justify-content: center;
  padding-top: 1.6rem;
  padding-bottom: 1.4rem;
}

.profile-card__avatar {
  width: 4.75rem;
  height: 4.75rem;
  border-radius: 9999px;
  background: linear-gradient(145deg, #d8e0cf, #a3b18a);
  color: var(--vb-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 800;
  box-shadow: inset 0 0 0 4px #fff, 0 10px 24px rgba(61, 79, 68, 0.12);
}

.profile-card__name {
  margin: 0.9rem 0 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.profile-card__email {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--vb-muted);
}

.profile-card__stats {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-top: 1.35rem;
  padding-top: 1rem;
  border-top: 1px solid var(--vb-line);
}

.profile-card__stats strong {
  display: block;
  font-size: 1rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.profile-card__stats span {
  font-size: 0.72rem;
  color: var(--vb-muted);
}

.bottom-row {
  grid-template-columns: 1fr;
}

@media (min-width: 1100px) {
  .bottom-row {
    grid-template-columns: 1.2fr 1fr 0.9fr;
  }
}

.cta-card {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 1rem;
  align-items: center;
  min-height: 15rem;
  overflow: hidden;
}

@media (max-width: 640px) {
  .cta-card {
    grid-template-columns: 1fr;
  }
}

.cta-card__text {
  margin: 0.65rem 0 0;
  font-size: 0.88rem;
  color: var(--vb-muted);
  line-height: 1.5;
  max-width: 18rem;
}

.cta-card__art {
  position: relative;
  height: 10rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ballot-stack {
  position: absolute;
  width: 7.5rem;
  height: 4.6rem;
  border-radius: 0.9rem;
  transform: rotate(-18deg);
  box-shadow: 0 12px 24px rgba(28, 28, 28, 0.12);
}

.ballot-stack--back {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(61, 79, 68, 0.15);
  transform: translate(-1.4rem, -0.8rem) rotate(-28deg);
}

.ballot-stack--mid {
  background: #a3b18a;
  transform: translate(0.2rem, 0.1rem) rotate(-12deg);
}

.ballot-stack--front {
  background: #1f2a36;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.85rem 1rem;
  transform: translate(1.5rem, 0.85rem) rotate(8deg);
}

.ballot-stack--front span {
  display: block;
  height: 0.35rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.35);
}

.ballot-stack--front span:nth-child(2) {
  width: 70%;
}

.ballot-stack--front span:nth-child(3) {
  width: 45%;
}

.transfers-card__head {
  margin-bottom: 0.85rem;
}

.transfer-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.transfer-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.transfer-item__avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0efe9;
  color: var(--vb-accent);
  flex-shrink: 0;
  font-size: 0.8rem;
}

.transfer-item__avatar.tone-vote {
  background: #e8efe6;
}

.transfer-item__avatar.tone-login {
  background: #f3efe6;
  color: #8a7355;
}

.transfer-item__copy {
  min-width: 0;
  flex: 1;
}

.transfer-item__title {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--vb-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.transfer-item__time {
  margin: 0.15rem 0 0;
  font-size: 0.72rem;
  color: var(--vb-muted);
}

.security-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  justify-content: center;
  padding: 1.75rem 1.35rem;
}

.security-card__icon {
  width: 4rem;
  height: 4rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0efe9;
  color: var(--vb-accent);
  font-size: 1.55rem;
  margin-bottom: 0.85rem;
}

.security-card__text {
  margin: 0.55rem 0 0;
  font-size: 0.86rem;
  color: var(--vb-muted);
  line-height: 1.5;
  max-width: 14rem;
}

.empty-note {
  margin: 1.5rem 0;
  text-align: center;
  color: var(--vb-muted);
  font-size: 0.85rem;
}

.chart-loading {
  height: 10rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--vb-accent);
}

.chart-loading--sm {
  height: 6rem;
}
</style>
