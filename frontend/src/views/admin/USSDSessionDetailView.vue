<template>
  <div v-if="session" class="max-w-4xl mx-auto">
    <div class="flex items-center gap-4 mb-6">
      <Button icon="pi pi-arrow-left" severity="secondary" text @click="$router.push('/ussd')" />
      <h1 class="text-2xl font-bold text-gray-900">USSD Session Details</h1>
    </div>

    <!-- Info cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs text-gray-500">MSISDN</p>
        <p class="font-mono font-medium">{{ session.msisdn }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs text-gray-500">User</p>
        <p>{{ session.user_email || 'Anonymous' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs text-gray-500">Election</p>
        <p>{{ session.election_title || '—' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs text-gray-500">Status</p>
        <Badge :value="session.status" :severity="getStatusSeverity(session.status)" />
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm col-span-2">
        <p class="text-xs text-gray-500">Current Step</p>
        <p>{{ session.current_step || '—' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm col-span-2">
        <p class="text-xs text-gray-500">State Data</p>
        <pre class="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-24">{{ JSON.stringify(session.state_data, null, 2) }}</pre>
      </div>
    </div>

    <!-- Logs -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-sm font-semibold text-gray-900">Request Logs</h2>
      </div>
      <div v-if="logs.length === 0" class="px-6 py-8 text-center text-gray-400 text-sm">
        No logs available.
      </div>
      <div v-else class="divide-y divide-gray-100">
        <div v-for="log in logs" :key="log.uuid" class="px-6 py-4 hover:bg-gray-50 transition-colors">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <div class="text-xs text-gray-400 font-mono">{{ log.timestamp }}</div>
              <div class="mt-1 text-sm text-gray-700">Request:</div>
              <pre class="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-24">{{ JSON.stringify(log.request_payload, null, 2) }}</pre>
              <div class="mt-2 text-sm text-gray-700">Response:</div>
              <pre class="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-24">{{ log.response_text || '—' }}</pre>
            </div>
            <div class="flex-shrink-0">
              <Badge :value="log.outcome || 'unknown'" :severity="log.outcome === 'success' ? 'success' : 'danger'" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">
    <i class="fas fa-spinner fa-spin text-2xl"></i>
    <p class="mt-2">Loading session...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ussdApi } from '@/api/ussd'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const route = useRoute()
const router = useRouter()
const session = ref(null)
const logs = ref([])

const fetchSession = async () => {
  try {
    const response = await ussdApi.getSession(route.params.uuid)
    session.value = response.data
    // fetch logs
    const logsResponse = await ussdApi.getSessionLogs(route.params.uuid)
    logs.value = logsResponse.data
  } catch (error) {
    console.error('Failed to fetch session:', error)
    router.push('/ussd')
  }
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

onMounted(fetchSession)
</script>
