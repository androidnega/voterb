<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Operations Center</h1>
        <p class="text-gray-500 text-sm mt-1">Monitor platform health, performance, and system status.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchAll" />
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Users</p>
        <p class="text-xl font-bold text-gray-900">{{ overview.total_users || 0 }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
        <p class="text-xs font-medium text-gray-400 uppercase">Active Elections</p>
        <p class="text-xl font-bold text-emerald-600">{{ overview.active_elections || 0 }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Votes</p>
        <p class="text-xl font-bold text-blue-600">{{ overview.total_votes || 0 }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
        <p class="text-xs font-medium text-gray-400 uppercase">Active Sessions</p>
        <p class="text-xl font-bold text-purple-600">{{ overview.active_sessions || 0 }}</p>
      </div>
    </div>

    <!-- Health & Infrastructure -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- Health -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">System Health</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2 border-b border-gray-100">
            <span class="text-sm text-gray-600">Overall Status</span>
            <Badge :value="health.status || 'unknown'" :severity="health.status === 'healthy' ? 'success' : 'danger'" />
          </div>
          <div v-for="(status, service) in health.services || {}" :key="service" class="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
            <span class="text-sm text-gray-600 capitalize">{{ service }}</span>
            <Badge :value="status" :severity="status === 'healthy' ? 'success' : 'danger'" />
          </div>
        </div>
        <div class="mt-4 text-xs text-gray-400">
          Last checked: {{ formatTime(health.timestamp) }}
        </div>
      </div>

      <!-- Infrastructure -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">Infrastructure</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2 border-b border-gray-100">
            <span class="text-sm text-gray-600">CPU Usage</span>
            <span class="text-sm font-medium">{{ infra.cpu?.percent || 0 }}%</span>
          </div>
          <div class="flex items-center justify-between py-2 border-b border-gray-100">
            <span class="text-sm text-gray-600">Memory Usage</span>
            <span class="text-sm font-medium">{{ infra.memory?.percent || 0 }}%</span>
          </div>
          <div class="flex items-center justify-between py-2 border-b border-gray-100">
            <span class="text-sm text-gray-600">Database Connections</span>
            <span class="text-sm font-medium">{{ infra.database?.connections || 0 }}</span>
          </div>
          <div class="flex items-center justify-between py-2 last:border-0">
            <span class="text-sm text-gray-600">Redis Clients</span>
            <span class="text-sm font-medium">{{ infra.redis?.clients || 0 }}</span>
          </div>
        </div>
        <div class="mt-4 text-xs text-gray-400">
          Uptime: {{ formatUptime(infra.uptime) }}
        </div>
      </div>
    </div>

    <!-- Queue Status -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-6">
      <h2 class="text-sm font-semibold text-gray-900 mb-4">Queue Status</h2>
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-gray-50 rounded-lg p-4 text-center">
          <p class="text-xs text-gray-500">Active Tasks</p>
          <p class="text-2xl font-bold text-gray-900">{{ queues.active_tasks || 0 }}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 text-center">
          <p class="text-xs text-gray-500">Scheduled Tasks</p>
          <p class="text-2xl font-bold text-gray-900">{{ queues.scheduled_tasks || 0 }}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 text-center">
          <p class="text-xs text-gray-500">Reserved Tasks</p>
          <p class="text-2xl font-bold text-gray-900">{{ queues.reserved_tasks || 0 }}</p>
        </div>
      </div>
      <div class="mt-3 text-xs text-gray-400">
        Celery: {{ queues.celery_enabled ? 'Enabled' : 'Not configured' }}
      </div>
    </div>

    <!-- System Logs -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-sm font-semibold text-gray-900">Recent System Logs</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Level</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Timestamp</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Source</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Message</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.timestamp + log.message" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
              <td class="py-3 px-4">
                <Badge :value="log.level" :severity="log.level === 'error' ? 'danger' : log.level === 'warning' ? 'warning' : 'info'" />
              </td>
              <td class="py-3 px-4 text-gray-600">{{ formatTime(log.timestamp) }}</td>
              <td class="py-3 px-4 text-gray-600">{{ log.source }}</td>
              <td class="py-3 px-4 text-gray-800">{{ log.message }}</td>
            </tr>
            <tr v-if="logs.length === 0 && !loading">
              <td colspan="4" class="py-12 text-center text-gray-400">
                <i class="fas fa-terminal text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No logs available.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { operationsApi } from '@/api/operations'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const overview = ref({})
const health = ref({})
const infra = ref({})
const queues = ref({})
const logs = ref([])
const loading = ref(false)

const fetchAll = async () => {
  loading.value = true
  try {
    const [overviewRes, healthRes, infraRes, queuesRes, logsRes] = await Promise.all([
      operationsApi.getOverview(),
      operationsApi.getHealth(),
      operationsApi.getInfrastructure(),
      operationsApi.getQueues(),
      operationsApi.getLogs()
    ])
    overview.value = overviewRes.data
    health.value = healthRes.data
    infra.value = infraRes.data
    queues.value = queuesRes.data
    logs.value = logsRes.data
  } catch (error) {
    console.error('Failed to fetch operations data:', error)
  } finally {
    loading.value = false
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return '—'
  return new Date(timestamp).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatUptime = (seconds) => {
  if (!seconds) return '—'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${days}d ${hours}h ${minutes}m`
}

onMounted(fetchAll)
</script>
