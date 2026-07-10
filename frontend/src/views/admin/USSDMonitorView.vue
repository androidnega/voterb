<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">USSD Monitor</h1>
        <p class="text-gray-500 text-sm mt-1">Monitor USSD sessions and requests.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchAll" />
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Sessions</p>
        <p class="text-xl font-bold text-gray-900">{{ stats.total_sessions }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Active</p>
        <p class="text-xl font-bold text-emerald-600">{{ stats.active_sessions }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Completed</p>
        <p class="text-xl font-bold text-blue-600">{{ stats.completed_sessions }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Errors</p>
        <p class="text-xl font-bold text-red-600">{{ stats.error_sessions }}</p>
      </div>
    </div>

    <!-- Sessions Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">MSISDN</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">User</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Election</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Step</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Created</th>
              <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="session in sessions" :key="session.uuid" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
              <td class="py-3 px-4 font-mono text-xs">{{ session.msisdn }}</td>
              <td class="py-3 px-4">{{ session.user_email || '—' }}</td>
              <td class="py-3 px-4">{{ session.election_title || '—' }}</td>
              <td class="py-3 px-4">
                <Badge :value="session.status" :severity="getStatusSeverity(session.status)" />
              </td>
              <td class="py-3 px-4">{{ session.current_step || '—' }}</td>
              <td class="py-3 px-4 text-gray-600">{{ formatDate(session.created_at) }}</td>
              <td class="py-3 px-4 text-center">
                <Button icon="pi pi-eye" size="small" severity="secondary" text rounded @click="viewSession(session.uuid)" tooltip="View" />
              </td>
            </tr>
            <tr v-if="sessions.length === 0 && !loading">
              <td colspan="7" class="py-12 text-center text-gray-400">
                <i class="fas fa-phone text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No USSD sessions found.</p>
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
import { useRouter } from 'vue-router'
import { ussdApi } from '@/api/ussd'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const router = useRouter()
const sessions = ref([])
const stats = ref({})
const loading = ref(false)

const fetchStats = async () => {
  try {
    const response = await ussdApi.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch USSD stats:', error)
  }
}

const fetchSessions = async () => {
  loading.value = true
  try {
    const response = await ussdApi.listSessions()
    sessions.value = response.data
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  } finally {
    loading.value = false
  }
}

const fetchAll = async () => {
  await Promise.all([fetchStats(), fetchSessions()])
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusSeverity = (status) => {
  const map = {
    active: 'success',
    completed: 'info',
    expired: 'warning',
    error: 'danger'
  }
  return map[status] || 'secondary'
}

const viewSession = (uuid) => {
  router.push(`/ussd/${uuid}`)
}

onMounted(fetchAll)
</script>
