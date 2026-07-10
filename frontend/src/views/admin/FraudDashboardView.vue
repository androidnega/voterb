<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Fraud Monitoring</h1>
        <p class="text-gray-500 text-sm mt-1">Detect and investigate security incidents.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchAll" />
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Alerts</p>
        <p class="text-xl font-bold text-gray-900">{{ stats.total_alerts }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Open Alerts</p>
        <p class="text-xl font-bold text-amber-600">{{ stats.open_alerts }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">High Risk</p>
        <p class="text-xl font-bold text-red-600">{{ stats.high_risk }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Cases</p>
        <p class="text-xl font-bold text-purple-600">{{ stats.total_cases }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Open Cases</p>
        <p class="text-xl font-bold text-blue-600">{{ stats.open_cases }}</p>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="flex border-b border-gray-200 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        class="py-3 px-4 text-sm font-medium transition-colors duration-200 border-b-2"
        :class="activeTab === tab.key 
          ? 'border-emerald-600 text-emerald-700' 
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
      >
        <i :class="tab.icon" class="mr-2"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div v-if="activeTab === 'alerts'">
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Type</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Severity</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">User</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Detected</th>
                <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alert in alerts" :key="alert.uuid" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
                <td class="py-3 px-4">{{ formatAlertType(alert.alert_type) }}</td>
                <td class="py-3 px-4">
                  <Badge :value="alert.severity" :severity="getSeverityBadge(alert.severity)" />
                </td>
                <td class="py-3 px-4 text-gray-600">{{ alert.user?.email || 'Unknown' }}</td>
                <td class="py-3 px-4">
                  <Badge :value="alert.status" :severity="getStatusSeverity(alert.status)" />
                </td>
                <td class="py-3 px-4 text-gray-600">{{ formatDate(alert.detected_at) }}</td>
                <td class="py-3 px-4 text-center">
                  <div class="flex items-center justify-center gap-1">
                    <Button icon="pi pi-eye" size="small" severity="secondary" text rounded @click="viewAlert(alert.uuid)" tooltip="View" />
                    <Button v-if="alert.status === 'open'" icon="pi pi-check" size="small" severity="success" text rounded @click="resolveAlert(alert.uuid)" tooltip="Resolve" />
                    <Button v-if="alert.status === 'open'" icon="pi pi-arrow-up" size="small" severity="warning" text rounded @click="escalateAlert(alert.uuid)" tooltip="Escalate to Case" />
                  </div>
                </td>
              </tr>
              <tr v-if="alerts.length === 0 && !loading">
                <td colspan="6" class="py-12 text-center text-gray-400">
                  <i class="fas fa-shield-alt text-4xl block mb-3 text-gray-200"></i>
                  <p class="text-sm">No security alerts found.</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'cases'">
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Case ID</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Alert</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Investigator</th>
                <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Created</th>
                <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="fraudCase in cases" :key="fraudCase.uuid" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
                <td class="py-3 px-4 font-mono text-xs text-gray-600">{{ fraudCase.uuid.slice(0, 8) }}</td>
                <td class="py-3 px-4 text-gray-600">{{ fraudCase.alert?.alert_type || 'Unknown' }}</td>
                <td class="py-3 px-4">
                  <Badge :value="fraudCase.status" :severity="getStatusSeverity(fraudCase.status)" />
                </td>
                <td class="py-3 px-4 text-gray-600">{{ fraudCase.investigator?.email || 'Unassigned' }}</td>
                <td class="py-3 px-4 text-gray-600">{{ formatDate(fraudCase.created_at) }}</td>
                <td class="py-3 px-4 text-center">
                  <Button icon="pi pi-eye" size="small" severity="secondary" text rounded @click="viewCase(fraudCase.uuid)" tooltip="View" />
                  <Button v-if="fraudCase.status === 'open'" icon="pi pi-check" size="small" severity="success" text rounded @click="resolveCase(fraudCase.uuid)" tooltip="Resolve" />
                </td>
              </tr>
              <tr v-if="cases.length === 0 && !loading">
                <td colspan="6" class="py-12 text-center text-gray-400">
                  <i class="fas fa-folder-open text-4xl block mb-3 text-gray-200"></i>
                  <p class="text-sm">No fraud cases found.</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fraudApi } from '@/api/fraud'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const router = useRouter()
const stats = ref({ total_alerts: 0, open_alerts: 0, high_risk: 0, total_cases: 0, open_cases: 0, recent_alerts: 0 })
const alerts = ref([])
const cases = ref([])
const loading = ref(false)
const activeTab = ref('alerts')

const tabs = [
  { key: 'alerts', label: 'Security Alerts', icon: 'fas fa-bell' },
  { key: 'cases', label: 'Fraud Cases', icon: 'fas fa-folder-open' }
]

const fetchStats = async () => {
  try {
    const response = await fraudApi.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchAlerts = async () => {
  try {
    const response = await fraudApi.listAlerts()
    alerts.value = response.data
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
  }
}

const fetchCases = async () => {
  try {
    const response = await fraudApi.listCases()
    cases.value = response.data
  } catch (error) {
    console.error('Failed to fetch cases:', error)
  }
}

const fetchAll = async () => {
  loading.value = true
  await Promise.all([fetchStats(), fetchAlerts(), fetchCases()])
  loading.value = false
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatAlertType = (type) => {
  const map = {
    login_attempts: 'Login Attempts',
    svt_requests: 'SVT Requests',
    voting_pattern: 'Suspicious Voting',
    duplicate_device: 'Duplicate Device',
    impossible_travel: 'Impossible Travel',
    suspicious_activity: 'Suspicious Activity'
  }
  return map[type] || type
}

const getSeverityBadge = (severity) => {
  const map = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[severity] || 'secondary'
}

const getStatusSeverity = (status) => {
  const map = {
    open: 'warning',
    investigating: 'info',
    resolved: 'success',
    dismissed: 'secondary',
    escalated: 'danger'
  }
  return map[status] || 'secondary'
}

const viewAlert = (uuid) => {
  router.push(`/fraud/alerts/${uuid}`)
}

const viewCase = (uuid) => {
  router.push(`/fraud/cases/${uuid}`)
}

const resolveAlert = async (uuid) => {
  if (confirm('Resolve this alert?')) {
    try {
      await fraudApi.resolveAlert(uuid)
      await fetchAlerts()
      await fetchStats()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
      alert('Failed to resolve alert. Please try again.')
    }
  }
}

const escalateAlert = async (uuid) => {
  if (confirm('Escalate this alert to a fraud case?')) {
    try {
      await fraudApi.escalateAlert(uuid)
      await fetchAll()
    } catch (error) {
      console.error('Failed to escalate alert:', error)
      alert('Failed to escalate alert. Please try again.')
    }
  }
}

const resolveCase = async (uuid) => {
  if (confirm('Resolve this fraud case?')) {
    try {
      await fraudApi.resolveCase(uuid)
      await fetchAll()
    } catch (error) {
      console.error('Failed to resolve case:', error)
      alert('Failed to resolve case. Please try again.')
    }
  }
}

onMounted(fetchAll)
</script>
