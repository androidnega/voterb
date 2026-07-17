<template>
  <div class="admin-page">
    <div class="auditor-banner page-section">
      <div>
        <p class="auditor-banner__eyebrow">Auditor mode</p>
        <h2 class="auditor-banner__title">View-only election oversight</h2>
        <p class="auditor-banner__copy">
          You can review elections, results, strongroom seals, and the audit trail.
          Management actions are reserved for the Election Committee.
        </p>
      </div>
      <i class="fas fa-eye auditor-banner__icon" aria-hidden="true"></i>
    </div>

    <div v-if="errorMessage" class="soft-alert">
      <span>{{ errorMessage }}</span>
      <button type="button" class="soft-btn soft-btn--inline" @click="fetchDashboard">Retry</button>
    </div>

    <div class="stat-grid page-section">
      <StatCard
        v-for="card in statCards"
        :key="card.label"
        :label="card.label"
        :value="loading ? '—' : card.value"
        :hint="loading ? 'Loading…' : card.hint"
        :icon="card.icon"
        :tone="card.tone"
      />
    </div>

    <div class="ec-grid page-section">
      <DataPanel title="Voting activity" subtitle="Votes cast over the last 7 days">
        <div v-if="loading" class="skeleton-block"></div>
        <AreaChart
          v-else
          :labels="chartData.labels"
          :data="chartData.values"
          :theme="appChartTheme"
          label="Votes"
          height="14rem"
          aria-label="Votes over recent days"
        />
      </DataPanel>

      <DataPanel title="Recent activity" subtitle="Latest security and auth events">
        <div v-if="loading" class="skeleton-block"></div>
        <div v-else-if="recentActivities.length" class="activity-scroll">
          <ul class="activity-list">
            <li v-for="(item, idx) in recentActivities.slice(0, 5)" :key="`${item.time}-${idx}`">
              <i :class="item.icon"></i>
              <div>
                <p>{{ item.message }}</p>
                <span>{{ item.time }}</span>
              </div>
            </li>
          </ul>
        </div>
        <p v-else class="empty-note">No recent activity yet.</p>
      </DataPanel>
    </div>

    <QuickAccessSection
      title="Quick access"
      subtitle="Auditor review tools"
      :links="shortcuts"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { dashboardApi } from '@/api/dashboard'
import { useThemeStore } from '@/stores/theme'
import AreaChart from '@/components/charts/AreaChart.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import QuickAccessSection from '@/components/admin/QuickAccessSection.vue'

const themeStore = useThemeStore()
const { theme: uiTheme } = storeToRefs(themeStore)
const appChartTheme = computed(() => `app-${uiTheme.value}`)

const REFRESH_MS = 30000
const loading = ref(true)
const errorMessage = ref('')
const stats = ref({
  total_elections: 0,
  active_elections: 0,
  eligible_voters: 0,
  unique_voters: 0,
  turnout: 0,
  total_votes: 0,
})
const chartData = ref({ labels: [], values: [] })
const recentActivities = ref([])

const shortcuts = [
  { path: '/elections', title: 'Elections', description: 'Review election cycles', icon: 'fas fa-calendar-check' },
  { path: '/results', title: 'Results', description: 'Inspect standings', icon: 'fas fa-chart-bar' },
  { path: '/strongroom', title: 'Strongroom', description: 'Seal custody checks', icon: 'fas fa-shield-alt' },
  { path: '/audit', title: 'Audit', description: 'Security event trail', icon: 'fas fa-clipboard-list' },
]

const formatNumber = (value) => new Intl.NumberFormat('en-US').format(Number(value) || 0)

const statCards = computed(() => [
  {
    label: 'Open elections',
    value: formatNumber(stats.value.active_elections),
    hint: `${formatNumber(stats.value.total_elections)} total`,
    icon: 'fas fa-play-circle',
    tone: 'tone-teal',
  },
  {
    label: 'Turnout',
    value: `${stats.value.turnout || 0}%`,
    hint: `${formatNumber(stats.value.unique_voters)} of ${formatNumber(stats.value.eligible_voters)} eligible`,
    icon: 'fas fa-percentage',
    tone: 'tone-slate',
  },
  {
    label: 'Votes cast',
    value: formatNumber(stats.value.total_votes),
    hint: 'All recorded ballots',
    icon: 'fas fa-check-double',
    tone: 'tone-blue',
  },
  {
    label: 'Eligible voters',
    value: formatNumber(stats.value.eligible_voters),
    hint: 'Across open cycles',
    icon: 'fas fa-users',
    tone: 'tone-amber',
  },
])

const fetchDashboard = async (options = {}) => {
  const { silent = false } = options
  if (!silent) {
    loading.value = true
    errorMessage.value = ''
  }
  try {
    const { data } = await dashboardApi.getAdminDashboard()
    stats.value = { ...stats.value, ...(data.stats || {}) }
    chartData.value = {
      labels: data.chart_data?.labels || [],
      values: data.chart_data?.values || [],
    }
    recentActivities.value = data.recent_activities || []
  } catch (error) {
    console.error('Failed to load auditor dashboard:', error)
    if (!silent) {
      errorMessage.value = error.response?.data?.error || 'Failed to load auditor dashboard.'
    }
  } finally {
    if (!silent) loading.value = false
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
.auditor-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.15rem 1.25rem;
  border-radius: 1.25rem;
  background: color-mix(in srgb, var(--vb-accent-soft) 70%, #fff);
  border: 1px solid color-mix(in srgb, var(--vb-accent) 18%, transparent);
  margin-bottom: 0.85rem;
}

.auditor-banner__eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 750;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vb-accent);
}

.auditor-banner__title {
  margin: 0.25rem 0 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.auditor-banner__copy {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: var(--vb-muted);
  max-width: 36rem;
  line-height: 1.45;
}

.auditor-banner__icon {
  font-size: 1.4rem;
  color: var(--vb-accent);
  opacity: 0.7;
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

.ec-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

@media (min-width: 900px) {
  .ec-grid {
    grid-template-columns: 1.35fr 1fr;
  }
}

.skeleton-block {
  min-height: 10rem;
  border-radius: 1rem;
  background: linear-gradient(90deg, #efeee8 25%, #f7f6f2 50%, #efeee8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.empty-note {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 8rem;
  color: var(--vb-muted);
  font-size: 0.85rem;
}

.activity-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.activity-scroll {
  max-height: 8.75rem;
  overflow-y: auto;
  padding-right: 0.25rem;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--vb-muted) 45%, transparent) transparent;
}

.activity-list li {
  display: flex;
  gap: 0.65rem;
  align-items: flex-start;
}

.activity-list i {
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

.activity-list p {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--vb-ink);
}

.activity-list span {
  font-size: 0.72rem;
  color: var(--vb-muted);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
