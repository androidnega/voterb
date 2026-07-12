<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p class="text-gray-500 text-sm mt-1">View all system activity and security events.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchLogs" />
    </div>

    <!-- Filter Bar -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <span class="text-sm font-medium text-gray-700">Filters:</span>
      <InputText v-model="filters.event" placeholder="Event type" class="w-48" @keyup.enter="fetchLogs" />
      <InputText v-model="filters.user" placeholder="User UUID" class="w-48" @keyup.enter="fetchLogs" />
      <Button label="Apply" icon="pi pi-search" size="small" @click="fetchLogs" />
      <Button label="Clear" icon="pi pi-times" severity="secondary" size="small" @click="clearFilters" />
    </div>

    <!-- Logs Table -->
    <div class="admin-table-wrap">
      <table class="admin-table">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Timestamp</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">User</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Event</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">IP</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Metadata</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.uuid || log.audit_id" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
              <td class="py-3 px-4 text-gray-600">{{ formatDate(log.created_at || log.timestamp) }}</td>
              <td class="py-3 px-4 text-gray-800">{{ log.user?.email || 'System' }}</td>
              <td class="py-3 px-4">
                <Badge :value="log.event_type" severity="info" />
              </td>
              <td class="py-3 px-4 font-mono text-xs">{{ log.ip_address || '—' }}</td>
              <td class="py-3 px-4">
                <pre v-if="log.metadata && Object.keys(log.metadata).length" class="bg-gray-50 p-1 rounded text-xs overflow-auto max-h-12">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
                <span v-else class="text-gray-400">—</span>
              </td>
            </tr>
            <tr v-if="logs.length === 0 && !loading">
              <td colspan="5" class="py-12 text-center text-gray-400">
                <i class="fas fa-list-ul text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No logs found.</p>
              </td>
            </tr>
          </tbody>
        </table>
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
const loading = ref(false)
const filters = ref({ user: '', event: '' })

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.user) params.user = filters.value.user
    if (filters.value.event) params.event = filters.value.event
    const response = await auditApi.getCombined(params)
    logs.value = response.data
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  } finally {
    loading.value = false
  }
}

const clearFilters = () => {
  filters.value = { user: '', event: '' }
  fetchLogs()
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(fetchLogs)
</script>
