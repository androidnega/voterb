<template>
  <div>
    <div v-if="errorMessage" class="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center justify-between gap-4">
      <span>{{ errorMessage }}</span>
      <button @click="fetchDashboard" class="shrink-0 px-3 py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-700">
        Retry
      </button>
    </div>

    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-700 to-blue-800 p-6 sm:p-8 mb-8 text-white">
      <div class="relative z-10">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 class="text-2xl sm:text-3xl font-bold tracking-tight">Good {{ context.greeting }}, {{ context.display_name }}</h1>
            <p class="text-slate-200 mt-1 text-sm">{{ context.role_label }} – read-only election oversight and verification.</p>
          </div>
          <div class="mt-4 sm:mt-0">
            <span class="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg border border-white/30 text-sm font-medium">
              <i class="fas fa-calendar-alt mr-2"></i>
              {{ context.today_date }}
            </span>
          </div>
        </div>
      </div>
      <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-12 translate-x-12"></div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Elections</p>
        <p class="text-2xl font-bold text-gray-900 mt-1">{{ stats.total_elections }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Active</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1">{{ stats.active_elections }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Registered Voters</p>
        <p class="text-2xl font-bold text-purple-600 mt-1">{{ stats.total_voters }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Turnout</p>
        <p class="text-2xl font-bold text-amber-600 mt-1">{{ stats.turnout }}%</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div v-if="loading" class="flex justify-center items-center h-48">
          <i class="pi pi-spin pi-spinner text-2xl text-blue-600"></i>
        </div>
        <div v-else-if="activities.length === 0" class="text-center py-10 text-sm text-gray-500">
          No recent activity
        </div>
        <div v-else class="space-y-4 max-h-80 overflow-y-auto">
          <div v-for="(activity, idx) in activities" :key="idx" class="flex items-start gap-3 border-b border-gray-50 pb-3 last:border-0">
            <div class="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
              <i :class="activity.icon" class="text-sm"></i>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-800 truncate">{{ activity.message }}</p>
              <p class="text-xs text-gray-400">{{ activity.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">Quick Access</h2>
        <div class="space-y-2">
          <RouterLink
            v-for="link in quickLinks"
            :key="link.path"
            :to="link.path"
            class="flex items-center gap-3 rounded-lg border border-gray-100 px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <i :class="link.icon" class="text-blue-600 w-5 text-center"></i>
            <span>{{ link.label }}</span>
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { dashboardApi } from '@/api/dashboard'

const loading = ref(true)
const errorMessage = ref('')
const context = ref({
  display_name: '…',
  role_label: 'Auditor',
  greeting: 'day',
  today_date: '',
})

const stats = ref({
  total_elections: 0,
  active_elections: 0,
  total_voters: 0,
  turnout: 0,
})
const activities = ref([])

const quickLinks = [
  { path: '/elections', label: 'View Elections', icon: 'fas fa-calendar-check' },
  { path: '/results', label: 'View Results', icon: 'fas fa-chart-bar' },
  { path: '/strongroom', label: 'Strongroom', icon: 'fas fa-shield-alt' },
  { path: '/audit', label: 'Audit Logs', icon: 'fas fa-clipboard-list' },
]

const fetchDashboard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await dashboardApi.getAdminDashboard()
    const data = response.data
    if (data.context) {
      context.value = { ...context.value, ...data.context }
    }
    stats.value = data.stats
    activities.value = data.recent_activities || []
  } catch (error) {
    console.error('Failed to load auditor dashboard:', error)
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
