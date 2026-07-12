<template>
  <div class="admin-page">
    <section class="dashboard-hero">
      <div class="hero-content">
        <div class="hero-badge">
          <i class="fas fa-shield-alt"></i>
          <span>Platform Governance</span>
        </div>
        <h1 class="hero-title">Good {{ greeting }}, {{ displayName }}</h1>
        <p class="hero-subtitle">
          Manage users, settings, operations, and platform oversight from here.
        </p>
        <div class="hero-meta">
          <span class="meta-chip">
            <i class="fas fa-calendar-day"></i>
            {{ todayDate }}
          </span>
          <span class="meta-chip">
            <i class="fas fa-user-shield"></i>
            Super Admin
          </span>
        </div>
      </div>

      <div class="hero-visual" aria-hidden="true">
        <svg viewBox="0 0 320 240" class="hero-svg" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="24" y="40" width="272" height="160" rx="16" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="2"/>
          <rect x="44" y="60" width="88" height="56" rx="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
          <circle cx="68" cy="82" r="10" fill="#0F766E"/>
          <rect x="84" y="74" width="36" height="6" rx="3" fill="#CBD5E1"/>
          <rect x="84" y="86" width="28" height="5" rx="2.5" fill="#E2E8F0"/>
          <rect x="148" y="60" width="128" height="24" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
          <rect x="160" y="70" width="48" height="4" rx="2" fill="#94A3B8"/>
          <rect x="148" y="96" width="60" height="48" rx="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
          <rect x="160" y="108" width="36" height="4" rx="2" fill="#64748B"/>
          <rect x="160" y="118" width="24" height="4" rx="2" fill="#CBD5E1"/>
          <rect x="160" y="128" width="30" height="4" rx="2" fill="#CBD5E1"/>
          <rect x="220" y="96" width="56" height="48" rx="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
          <path d="M236 118 L244 126 L260 110" stroke="#0F766E" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          <rect x="44" y="128" width="88" height="52" rx="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
          <circle cx="62" cy="150" r="6" fill="#1E293B"/>
          <circle cx="88" cy="150" r="6" fill="#64748B"/>
          <circle cx="114" cy="150" r="6" fill="#94A3B8"/>
          <rect x="56" y="164" width="64" height="4" rx="2" fill="#E2E8F0"/>
          <path d="M160 168 H260" stroke="#E2E8F0" stroke-width="2" stroke-linecap="round"/>
          <circle cx="248" cy="168" r="8" fill="#0F766E"/>
          <path d="M160 40 L160 24 L200 24" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
          <circle cx="200" cy="24" r="5" fill="#0F766E"/>
        </svg>
      </div>
    </section>

    <div class="stat-grid page-section">
      <StatCard
        v-for="stat in statCards"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :hint="stat.hint"
        :icon="stat.icon"
        :tone="stat.tone"
        :value-tone="stat.valueTone"
      />
    </div>

    <section class="page-section">
      <div class="section-head">
        <h2 class="section-title">Quick access</h2>
        <p class="section-subtitle">Jump to core platform controls</p>
      </div>

      <div class="quick-link-grid">
        <router-link
          v-for="link in quickLinks"
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

    <section class="page-section dashboard-charts">
      <div class="section-head">
        <h2 class="section-title">Platform analytics</h2>
        <p class="section-subtitle">Votes, users, and election distribution</p>
      </div>
      <div class="dashboard-charts">
        <DataPanel title="Platform activity" subtitle="Votes and new users over the last 7 months">
          <LineChart
            :labels="platformActivity.labels"
            :datasets="platformActivity.datasets"
            show-legend
            aria-label="Platform activity line chart"
          />
        </DataPanel>
        <DataPanel title="User growth" subtitle="Total registered users over time">
          <AreaChart
            :labels="userGrowth.labels"
            :data="userGrowth.data"
            label="Total users"
            aria-label="User growth area chart"
          />
        </DataPanel>
        <DataPanel title="Election stats" subtitle="Elections by status">
          <BarChart
            :labels="electionStats.labels"
            :data="electionStats.data"
            label="Elections"
            :empty="!electionStats.labels.length"
            aria-label="Election stats bar chart"
          />
        </DataPanel>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/api/users'
import { dashboardApi } from '@/api/dashboard'
import { displayUserName } from '@/utils/user'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import LineChart from '@/components/charts/LineChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const authStore = useAuthStore()
const user = computed(() => authStore.user)

const displayName = computed(() => displayUserName(user.value, 'Admin'))

const todayDate = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Morning'
  if (hour < 18) return 'Afternoon'
  return 'Evening'
})

const stats = ref({
  total_users: 0,
  staff_users: 0,
  inactive_users: 0,
})

const platformActivity = ref({ labels: [], datasets: [] })
const userGrowth = ref({ labels: [], data: [] })
const electionStats = ref({ labels: [], data: [] })

const activeUsers = computed(() => Math.max(stats.value.total_users - stats.value.inactive_users, 0))

const statCards = computed(() => {
  const total = stats.value.total_users || 0
  const activePct = total ? Math.round((activeUsers.value / total) * 100) : 0
  const staffPct = total ? Math.round((stats.value.staff_users / total) * 100) : 0

  return [
    {
      label: 'Platform Users',
      value: stats.value.total_users,
      hint: 'All registered accounts',
      icon: 'fas fa-users',
      tone: 'tone-slate',
      valueTone: 'text-slate-900',
    },
    {
      label: 'Active Users',
      value: activeUsers.value,
      hint: `${activePct}% of total`,
      icon: 'fas fa-user-check',
      tone: 'tone-teal',
      valueTone: 'text-teal-700',
    },
    {
      label: 'Staff Accounts',
      value: stats.value.staff_users,
      hint: `${staffPct}% of total`,
      icon: 'fas fa-id-badge',
      tone: 'tone-blue',
      valueTone: 'text-blue-700',
    },
    {
      label: 'System Health',
      value: 'Healthy',
      hint: 'All core services online',
      icon: 'fas fa-heartbeat',
      tone: 'tone-emerald',
      valueTone: 'text-emerald-700',
    },
  ]
})

const quickLinks = [
  {
    path: '/users',
    title: 'User Management',
    description: 'Create accounts, assign roles, activate or deactivate users',
    icon: 'fas fa-users-cog',
    tone: 'tone-slate',
  },
  {
    path: '/settings',
    title: 'System Settings',
    description: 'Configure platform security and notification preferences',
    icon: 'fas fa-sliders-h',
    tone: 'tone-teal',
  },
  {
    path: '/operations',
    title: 'Operations Center',
    description: 'Monitor jobs, queues, and platform runtime health',
    icon: 'fas fa-server',
    tone: 'tone-blue',
  },
  {
    path: '/strongroom',
    title: 'Strongroom',
    description: 'Review custody records and approve vault access requests',
    icon: 'fas fa-shield-alt',
    tone: 'tone-amber',
  },
  {
    path: '/audit',
    title: 'Audit Logs',
    description: 'Inspect security events and administrative activity',
    icon: 'fas fa-clipboard-list',
    tone: 'tone-indigo',
  },
  {
    path: '/fraud',
    title: 'Fraud Monitor',
    description: 'Track suspicious voting patterns and flagged sessions',
    icon: 'fas fa-user-shield',
    tone: 'tone-rose',
  },
]

const fetchStats = async () => {
  try {
    const [usersRes, chartsRes] = await Promise.all([
      usersApi.list(),
      dashboardApi.getSuperAdminDashboard(),
    ])
    const users = usersRes.data || []
    stats.value.total_users = users.length
    stats.value.staff_users = users.filter(
      (u) => u.is_staff || ['admin', 'super_admin', 'auditor'].includes(u.role_name || u.role?.name)
    ).length
    stats.value.inactive_users = users.filter((u) => !u.is_active).length

    const charts = chartsRes.data || {}
    platformActivity.value = {
      labels: charts.platform_activity?.labels || [],
      datasets: charts.platform_activity?.datasets || [],
    }
    userGrowth.value = {
      labels: charts.user_growth?.labels || [],
      data: charts.user_growth?.data || [],
    }
    electionStats.value = {
      labels: charts.election_stats?.labels || [],
      data: charts.election_stats?.data || [],
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

onMounted(fetchStats)
</script>

<style scoped>
.dashboard-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

@media (min-width: 900px) {
  .dashboard-charts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-charts > :last-child {
    grid-column: 1 / -1;
  }
}
</style>
