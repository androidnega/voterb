<template>
  <div class="admin-page">
    <PageHeader
      title="Fraud Monitor"
      subtitle="Track security alerts and investigate flagged activity across the platform."
      icon="fas fa-user-shield"
      icon-tone="tone-rose"
      :loading="loading"
      @refresh="fetchAll"
    />

    <div class="stat-grid stat-grid-5 page-section">
      <StatCard label="Total Alerts" :value="stats.total_alerts" icon="fas fa-bell" tone="tone-slate" />
      <StatCard label="Open Alerts" :value="stats.open_alerts" icon="fas fa-exclamation-circle" tone="tone-amber" value-tone="text-amber-700" />
      <StatCard label="High Risk" :value="stats.high_risk" icon="fas fa-radiation" tone="tone-rose" value-tone="text-rose-700" />
      <StatCard label="Total Cases" :value="stats.total_cases" icon="fas fa-folder-open" tone="tone-indigo" value-tone="text-indigo-700" />
      <StatCard label="Open Cases" :value="stats.open_cases" icon="fas fa-search" tone="tone-blue" value-tone="text-blue-700" />
    </div>

    <TabNav v-model="activeTab" :tabs="tabs" class="page-section" />

    <DataPanel v-if="activeTab === 'alerts'" title="Security alerts" subtitle="Automated detections requiring review" no-padding>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Severity</th>
              <th>User</th>
              <th>Status</th>
              <th>Detected</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="alert in paginatedAlerts" :key="alert.uuid">
              <td>{{ formatAlertType(alert.alert_type) }}</td>
              <td><span class="admin-badge" :class="severityBadge(alert.severity)">{{ alert.severity }}</span></td>
              <td>{{ alert.user?.email || 'Unknown' }}</td>
              <td><span class="admin-badge" :class="statusBadge(alert.status)">{{ alert.status }}</span></td>
              <td class="text-muted">{{ formatDate(alert.detected_at) }}</td>
              <td>
                <div class="row-actions">
                  <button v-if="alert.status === 'open'" type="button" class="admin-icon-btn" title="Resolve" @click="resolveAlert(alert.uuid)"><i class="fas fa-check"></i></button>
                  <button v-if="alert.status === 'open'" type="button" class="admin-icon-btn" title="Escalate" @click="escalateAlert(alert.uuid)"><i class="fas fa-arrow-up"></i></button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && alerts.length === 0">
              <td colspan="6"><EmptyState icon="fas fa-shield-alt" title="No alerts" message="Security alerts will appear here when detected." /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <TablePagination
          :page="alertsPage"
          :page-size="alertsPageSize"
          :total="alertsTotal"
          :total-pages="alertsTotalPages"
          :from="alertsFrom"
          :to="alertsTo"
          @update:page="setAlertsPage"
          @update:page-size="setAlertsPageSize"
        />
      </template>
    </DataPanel>

    <DataPanel v-else title="Fraud cases" subtitle="Escalated investigations" no-padding>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Alert</th>
              <th>Status</th>
              <th>Investigator</th>
              <th>Created</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fraudCase in paginatedCases" :key="fraudCase.uuid">
              <td class="mono">{{ fraudCase.uuid.slice(0, 8) }}</td>
              <td>{{ fraudCase.alert?.alert_type || 'Unknown' }}</td>
              <td><span class="admin-badge" :class="statusBadge(fraudCase.status)">{{ fraudCase.status }}</span></td>
              <td>{{ fraudCase.investigator?.email || 'Unassigned' }}</td>
              <td class="text-muted">{{ formatDate(fraudCase.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button v-if="fraudCase.status === 'open'" type="button" class="admin-icon-btn" title="Resolve" @click="resolveCase(fraudCase.uuid)"><i class="fas fa-check"></i></button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && cases.length === 0">
              <td colspan="6"><EmptyState icon="fas fa-folder-open" title="No cases" message="Escalated fraud cases will appear here." /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <TablePagination
          :page="casesPage"
          :page-size="casesPageSize"
          :total="casesTotal"
          :total-pages="casesTotalPages"
          :from="casesFrom"
          :to="casesTo"
          @update:page="setCasesPage"
          @update:page-size="setCasesPageSize"
        />
      </template>
    </DataPanel>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { fraudApi } from '@/api/fraud'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TabNav from '@/components/admin/TabNav.vue'
import TablePagination from '@/components/admin/TablePagination.vue'

const stats = ref({ total_alerts: 0, open_alerts: 0, high_risk: 0, total_cases: 0, open_cases: 0 })
const alerts = ref([])
const cases = ref([])
const loading = ref(false)
const activeTab = ref('alerts')

const {
  page: alertsPage,
  size: alertsPageSize,
  total: alertsTotal,
  totalPages: alertsTotalPages,
  paginated: paginatedAlerts,
  from: alertsFrom,
  to: alertsTo,
  setPage: setAlertsPage,
  setPageSize: setAlertsPageSize,
  reset: resetAlertsPage,
} = usePagination(alerts, 10)

const {
  page: casesPage,
  size: casesPageSize,
  total: casesTotal,
  totalPages: casesTotalPages,
  paginated: paginatedCases,
  from: casesFrom,
  to: casesTo,
  setPage: setCasesPage,
  setPageSize: setCasesPageSize,
  reset: resetCasesPage,
} = usePagination(cases, 10)

watch(activeTab, () => {
  resetAlertsPage()
  resetCasesPage()
})

const tabs = computed(() => [
  { key: 'alerts', label: 'Alerts', icon: 'fas fa-bell', count: alerts.value.length },
  { key: 'cases', label: 'Cases', icon: 'fas fa-folder-open', count: cases.value.length },
])

const fetchAll = async () => {
  loading.value = true
  try {
    const [statsRes, alertsRes, casesRes] = await Promise.all([
      fraudApi.getStats(),
      fraudApi.listAlerts(),
      fraudApi.listCases(),
    ])
    stats.value = statsRes.data
    alerts.value = alertsRes.data
    cases.value = casesRes.data
  } catch (error) {
    console.error('Failed to fetch fraud data:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => date ? new Date(date).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'

const formatAlertType = (type) => ({
  login_attempts: 'Login Attempts', svt_requests: 'SVT Requests', voting_pattern: 'Suspicious Voting',
  duplicate_device: 'Duplicate Device', impossible_travel: 'Impossible Travel', suspicious_activity: 'Suspicious Activity',
}[type] || type)

const severityBadge = (s) => ({ low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }[s] || 'neutral')
const statusBadge = (s) => ({ open: 'warning', investigating: 'info', resolved: 'success', dismissed: 'neutral', escalated: 'danger' }[s] || 'neutral')

const resolveAlert = async (uuid) => {
  if (!confirm('Resolve this alert?')) return
  try { await fraudApi.resolveAlert(uuid); await fetchAll() } catch { alert('Failed to resolve alert.') }
}
const escalateAlert = async (uuid) => {
  if (!confirm('Escalate to a fraud case?')) return
  try { await fraudApi.escalateAlert(uuid); await fetchAll() } catch { alert('Failed to escalate alert.') }
}
const resolveCase = async (uuid) => {
  if (!confirm('Resolve this case?')) return
  try { await fraudApi.resolveCase(uuid); await fetchAll() } catch { alert('Failed to resolve case.') }
}

onMounted(fetchAll)
</script>
