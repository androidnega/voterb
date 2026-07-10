<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p class="text-gray-500 text-sm mt-1">View all security and system logs.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchAll" />
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Logs</p>
        <p class="text-xl font-bold text-gray-900">{{ stats.total_logs }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Today</p>
        <p class="text-xl font-bold text-emerald-600">{{ stats.today_logs }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">MFA Logs</p>
        <p class="text-xl font-bold text-blue-600">{{ stats.mfa_count }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Audit Logs</p>
        <p class="text-xl font-bold text-purple-600">{{ stats.audit_count }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <div class="relative flex-1 min-w-[150px]">
        <InputText v-model="filters.event_type" placeholder="Filter by event type..." class="w-full" />
      </div>
      <div class="relative flex-1 min-w-[150px]">
        <InputText v-model="filters.user" placeholder="User email..." class="w-full" />
      </div>
      <div class="flex gap-2">
        <Button label="Apply" icon="pi pi-search" @click="applyFilters" />
        <Button label="Clear" severity="secondary" @click="clearFilters" />
      </div>
    </div>

    <!-- Logs Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Type</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">User</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Event</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">IP</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.uuid" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
              <td class="py-3 px-4">
                <Badge :value="log.type" :severity="log.type === 'mfa' ? 'info' : 'secondary'" />
              </td>
              <td class="py-3 px-4">{{ log.user?.email || 'System' }}</td>
              <td class="py-3 px-4 font-mono text-xs">{{ log.event_type }}</td>
              <td class="py-3 px-4">{{ log.ip_address || '—' }}</td>
              <td class="py-3 px-4 text-gray-600">{{ formatDate(log.timestamp) }}</td>
            </tr>
            <tr v-if="logs.length === 0 && !loading">
              <td colspan="5" class="py-12 text-center text-gray-400">
                <i class="fas fa-clipboard-list text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No logs found.</p>
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
import { auditApi } from '@/api/audit'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import InputText from 'primevue/inputtext'

const logs = ref([])
const stats = ref({})
const loading = ref(false)
const filters = ref({
  event_type: '',
  user: '',
  start_date: '',
  end_date: ''
})

const fetchStats = async () => {
  try {
    const response = await auditApi.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.event_type) params.event_type = filters.value.event_type
    if (filters.value.user) params.user = filters.value.user
    const response = await auditApi.getCombinedLogs(params)
    logs.value = response.data
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  } finally {
    loading.value = false
  }
}

const fetchAll = async () => {
  await Promise.all([fetchStats(), fetchLogs()])
}

const applyFilters = () => {
  fetchLogs()
}

const clearFilters = () => {
  filters.value = { event_type: '', user: '', start_date: '', end_date: '' }
  fetchLogs()
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(fetchAll)
</script>
