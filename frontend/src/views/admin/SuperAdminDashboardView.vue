<template>
  <div class="admin-page">
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

    <div class="sa-grid page-section">
      <DataPanel title="User growth" subtitle="New accounts over the last 7 months">
        <AreaChart
          v-if="!loading"
          :labels="userGrowth.labels"
          :data="userGrowth.new_users"
          label="New users"
          color="#3d4f44"
          height="14rem"
          aria-label="New users over recent months"
        />
        <div v-else class="chart-loading"><i class="fas fa-spinner fa-spin"></i></div>
      </DataPanel>

      <DataPanel title="Role mix" subtitle="Accounts by platform role">
        <DonutChart
          v-if="!loading && roleBreakdown.labels.length"
          :labels="roleBreakdown.labels"
          :data="roleBreakdown.values"
          height="14rem"
          aria-label="Users by role"
        />
        <p v-else-if="loading" class="empty-note">Loading…</p>
        <p v-else class="empty-note">No role data yet.</p>
      </DataPanel>
    </div>

    <div class="sa-grid page-section">
      <DataPanel title="Platform controls" subtitle="Structure and feature posture">
        <ul class="sa-control-list">
          <li>
            <span>Academic faculties</span>
            <strong>{{ loading ? '—' : formatNumber(stats.faculties) }}</strong>
          </li>
          <li>
            <span>Departments</span>
            <strong>{{ loading ? '—' : formatNumber(stats.departments) }}</strong>
          </li>
          <li>
            <span>Levels</span>
            <strong>{{ loading ? '—' : formatNumber(stats.levels) }}</strong>
          </li>
          <li>
            <span>Feature flags on</span>
            <strong>{{ loading ? '—' : `${stats.flags_enabled} / ${stats.flags_total}` }}</strong>
          </li>
          <li>
            <span>Maintenance mode</span>
            <strong :class="stats.maintenance_active ? 'is-warn' : 'is-ok'">
              {{ loading ? '—' : (stats.maintenance_active ? 'Active' : 'Off') }}
            </strong>
          </li>
        </ul>
      </DataPanel>

      <DataPanel title="Recent security activity" subtitle="Latest MFA and login events">
        <ul v-if="!loading && recentActivities.length" class="sa-activity">
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
        <p class="section-subtitle">Platform governance tools</p>
      </div>
      <div class="quick-link-grid">
        <router-link
          v-for="link in shortcuts"
          :key="link.path"
          :to="link.path"
          class="quick-link-card"
        >
          <div class="quick-link-icon tone-slate">
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import AreaChart from '@/components/charts/AreaChart.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'

const REFRESH_MS = 30000

const loading = ref(true)
const errorMessage = ref('')
const stats = ref({
  total_users: 0,
  active_users: 0,
  staff_users: 0,
  student_users: 0,
  faculties: 0,
  departments: 0,
  levels: 0,
  flags_enabled: 0,
  flags_total: 0,
  maintenance_active: false,
})
const roleBreakdown = ref({ labels: [], values: [] })
const userGrowth = ref({ labels: [], new_users: [], cumulative: [] })
const recentActivities = ref([])
const shortcuts = ref([])

const formatNumber = (value) => {
  const n = Number(value) || 0
  return new Intl.NumberFormat('en-US').format(n)
}

const statCards = computed(() => [
  {
    label: 'Total users',
    value: formatNumber(stats.value.total_users),
    hint: `${formatNumber(stats.value.active_users)} active`,
    icon: 'fas fa-users',
    tone: 'tone-slate',
  },
  {
    label: 'Staff accounts',
    value: formatNumber(stats.value.staff_users),
    hint: 'Admins & auditors',
    icon: 'fas fa-user-tie',
    tone: 'tone-teal',
  },
  {
    label: 'Students',
    value: formatNumber(stats.value.student_users),
    hint: 'Student role accounts',
    icon: 'fas fa-user-graduate',
    tone: 'tone-blue',
  },
  {
    label: 'Departments',
    value: formatNumber(stats.value.departments),
    hint: `${formatNumber(stats.value.faculties)} faculties`,
    icon: 'fas fa-university',
    tone: 'tone-amber',
  },
])

const applyDashboardData = (data) => {
  stats.value = { ...stats.value, ...(data.stats || {}) }
  roleBreakdown.value = {
    labels: data.role_breakdown?.labels || [],
    values: data.role_breakdown?.values || [],
  }
  userGrowth.value = {
    labels: data.user_growth?.labels || [],
    new_users: data.user_growth?.new_users || [],
    cumulative: data.user_growth?.cumulative || [],
  }
  recentActivities.value = data.recent_activities || []
  shortcuts.value = data.shortcuts || []
}

const fetchDashboard = async (options = {}) => {
  const { silent = false } = options
  if (!silent) {
    loading.value = true
    errorMessage.value = ''
  }
  try {
    const { data } = await dashboardApi.getSuperAdminDashboard()
    applyDashboardData(data)
    if (!silent) loading.value = false
  } catch (error) {
    console.error('Failed to load super admin dashboard:', error)
    if (!silent) {
      errorMessage.value = error.response?.data?.error || 'Failed to load platform dashboard.'
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

.soft-btn--inline {
  margin-top: 0;
}

.sa-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

@media (min-width: 900px) {
  .sa-grid {
    grid-template-columns: 1.35fr 1fr;
    gap: 1rem;
  }
}

.chart-loading,
.empty-note {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 8rem;
  color: var(--vb-muted);
  font-size: 0.85rem;
}

.sa-control-list,
.sa-activity {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sa-control-list li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
  font-size: 0.86rem;
  color: var(--vb-muted);
}

.sa-control-list li:last-child {
  border-bottom: none;
}

.sa-control-list strong {
  color: var(--vb-ink);
  font-weight: 800;
}

.sa-control-list strong.is-ok {
  color: var(--vb-positive, #3d4f44);
}

.sa-control-list strong.is-warn {
  color: #b45309;
}

.sa-activity li {
  display: flex;
  gap: 0.65rem;
  align-items: flex-start;
}

.sa-activity i {
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

.sa-activity p {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--vb-ink);
}

.sa-activity span {
  font-size: 0.72rem;
  color: var(--vb-muted);
}

.section-head {
  margin-bottom: 0.85rem;
}

.section-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.section-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--vb-muted);
}

.quick-link-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

@media (min-width: 720px) {
  .quick-link-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1100px) {
  .quick-link-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.quick-link-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.05rem;
  border-radius: 1.15rem;
  background: #fff;
  box-shadow: var(--vb-card-shadow);
  text-decoration: none;
  color: inherit;
}

.quick-link-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--vb-accent-soft);
  color: var(--vb-accent);
}

.quick-link-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.quick-link-desc {
  margin: 0.15rem 0 0;
  font-size: 0.75rem;
  color: var(--vb-muted);
}

.quick-link-arrow {
  margin-left: auto;
  color: #c5c2b6;
  font-size: 0.75rem;
}
</style>
