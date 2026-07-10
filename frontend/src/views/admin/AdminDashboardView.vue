<template>
  <div>
    <div v-if="errorMessage" class="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center justify-between gap-4">
      <span>{{ errorMessage }}</span>
      <button @click="fetchDashboard" class="shrink-0 px-3 py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-700">
        Retry
      </button>
    </div>

    <!-- Hero -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 p-6 sm:p-8 mb-8 text-white">
      <div class="relative z-10">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 class="text-2xl sm:text-3xl font-bold tracking-tight">Good {{ greeting }}, {{ userName }}</h1>
            <p class="text-emerald-100 mt-1 text-sm">Here's what's happening with your elections today.</p>
          </div>
          <div class="mt-4 sm:mt-0">
            <span class="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg border border-white/30 text-sm font-medium">
              <i class="pi pi-calendar mr-2"></i>
              {{ todayDate }}
            </span>
          </div>
        </div>
      </div>
      <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-12 translate-x-12"></div>
      <div class="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-12 -translate-x-12"></div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Elections</p>
            <p class="text-2xl font-bold text-gray-900 mt-1">{{ stats.total_elections }}</p>
          </div>
          <div class="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-calendar text-indigo-500 text-xl"></i>
          </div>
        </div>
        <div class="mt-3 h-1.5 w-full bg-indigo-100 rounded-full overflow-hidden">
          <div class="h-full bg-indigo-500 rounded-full" style="width: 100%"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Active</p>
            <p class="text-2xl font-bold text-emerald-600 mt-1">{{ stats.active_elections }}</p>
          </div>
          <div class="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-check-circle text-emerald-500 text-xl"></i>
          </div>
        </div>
        <div class="mt-3 h-1.5 w-full bg-emerald-100 rounded-full overflow-hidden">
          <div class="h-full bg-emerald-500 rounded-full" :style="{ width: stats.total_elections ? (stats.active_elections/stats.total_elections*100)+'%' : '0%' }"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Voters</p>
            <p class="text-2xl font-bold text-purple-600 mt-1">{{ stats.total_voters }}</p>
          </div>
          <div class="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-users text-purple-500 text-xl"></i>
          </div>
        </div>
        <div class="mt-3 h-1.5 w-full bg-purple-100 rounded-full overflow-hidden">
          <div class="h-full bg-purple-500 rounded-full" style="width: 100%"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Turnout</p>
            <p class="text-2xl font-bold text-amber-600 mt-1">{{ stats.turnout }}%</p>
          </div>
          <div class="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-chart-bar text-amber-500 text-xl"></i>
          </div>
        </div>
        <div class="mt-3 h-1.5 w-full bg-amber-100 rounded-full overflow-hidden">
          <div class="h-full bg-amber-500 rounded-full" :style="{ width: stats.turnout + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Chart & Activity Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Chart (2/3) -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">Voting Activity (Last 7 Days)</h2>
        <div v-if="loading" class="flex justify-center items-center h-64">
          <i class="pi pi-spin pi-spinner text-2xl text-emerald-600"></i>
        </div>
        <div v-else class="chart-wrap space-y-3">
          <div
            v-for="(label, index) in chartData.labels"
            :key="label"
            class="flex items-center gap-3 text-sm"
          >
            <span class="w-10 shrink-0 text-gray-500">{{ label }}</span>
            <div class="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full bg-emerald-500 rounded-full transition-all"
                :style="{ width: barWidth(index) }"
              />
            </div>
            <span class="w-8 text-right text-gray-700 font-medium">{{ chartValues[index] ?? 0 }}</span>
          </div>
          <p v-if="chartData.labels.length === 0" class="text-sm text-gray-400 text-center py-8">
            No voting activity yet
          </p>
        </div>
      </div>

      <!-- Recent Activity (1/3) -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-gray-900">Recent Activity</h2>
          <span class="text-xs text-gray-400">Last 7 days</span>
        </div>
        <div v-if="activities.length === 0" class="text-center py-10">
          <i class="pi pi-inbox text-4xl text-gray-200 block mb-3"></i>
          <p class="text-sm text-gray-500">No recent activity</p>
        </div>
        <div v-else class="space-y-4 max-h-80 overflow-y-auto">
          <div v-for="(activity, idx) in activities" :key="idx" class="flex items-start gap-3 border-b border-gray-50 pb-3 last:border-0">
            <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" :class="{
              'bg-emerald-50 text-emerald-600': activity.type === 'vote',
              'bg-blue-50 text-blue-600': activity.type === 'login' || activity.type === 'election',
              'bg-amber-50 text-amber-600': activity.type === 'user'
            }">
              <i :class="activity.icon" class="text-sm"></i>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-800 truncate">{{ activity.message }}</p>
              <p class="text-xs text-gray-400">{{ activity.time }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { dashboardApi } from '@/api/dashboard'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const loading = ref(true)
const errorMessage = ref('')
const stats = ref({
  total_elections: 0,
  active_elections: 0,
  total_voters: 0,
  turnout: 0
})
const activities = ref([])
const chartData = ref({
  labels: [],
  datasets: [
    {
      label: 'Votes',
      backgroundColor: '#10b981',
      borderColor: '#059669',
      borderWidth: 1,
      data: []
    }
  ]
})

const chartValues = computed(() => chartData.value.datasets[0]?.data || [])

const maxChartValue = computed(() => {
  const values = chartValues.value
  if (!values.length) return 1
  return Math.max(...values, 1)
})

const barWidth = (index) => {
  const value = chartValues.value[index] ?? 0
  return `${Math.round((value / maxChartValue.value) * 100)}%`
}

const userName = computed(() => {
  if (user.value?.first_name) return user.value.first_name
  return user.value?.email?.split('@')[0] || 'Admin'
})

const todayDate = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Morning'
  if (hour < 18) return 'Afternoon'
  return 'Evening'
})

const fetchDashboard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await dashboardApi.getAdminDashboard()
    const data = response.data
    stats.value = data.stats
    activities.value = data.recent_activities || []
    chartData.value = {
      labels: data.chart_data?.labels || [],
      datasets: [
        {
          label: 'Votes',
          backgroundColor: '#10b981',
          borderColor: '#059669',
          borderWidth: 1,
          data: data.chart_data?.values || []
        }
      ]
    }
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    const status = error.response?.status
    if (status === 404) {
      errorMessage.value = 'Dashboard API not found. Restart the Django server.'
    } else if (status === 403 || status === 401) {
      errorMessage.value = 'Session expired or insufficient permissions. Please sign in again.'
    } else if (!error.response) {
      errorMessage.value = 'Cannot reach the backend. Make sure it is running on port 8000.'
    } else {
      errorMessage.value = error.response?.data?.error || 'Failed to load dashboard data.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>

<style scoped>
.chart-wrap {
  position: relative;
  width: 100%;
  height: 16rem; /* fixed — prevents Chart.js infinite resize */
  max-height: 16rem;
  overflow: hidden;
}

.chart-wrap :deep(.p-chart) {
  position: relative;
  width: 100% !important;
  height: 100% !important;
}

.chart-wrap :deep(canvas) {
  max-height: 16rem !important;
}
</style>
