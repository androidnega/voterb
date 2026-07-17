<template>
  <div class="admin-page">
    <PageHeader :loading="loading" @refresh="fetchAll" />

    <div class="kpi-strip">
      <div class="kpi-item">
        <p class="kpi-label">Total alerts</p>
        <p class="kpi-value">{{ stats.total_alerts || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Open alerts</p>
        <p class="kpi-value is-warn">{{ stats.open_alerts || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">High risk</p>
        <p class="kpi-value is-danger">{{ stats.high_risk || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Open cases</p>
        <p class="kpi-value is-info">{{ stats.open_cases || 0 }}</p>
      </div>
    </div>

    <div class="section-toolbar">
      <div>
        <h2 class="section-toolbar__title">{{ activeTab === 'alerts' ? 'Security alerts' : 'Fraud cases' }}</h2>
        <p class="section-toolbar__sub">
          {{ activeTab === 'alerts'
            ? 'Automated detections requiring review'
            : 'Escalated investigations' }}
        </p>
      </div>
      <TabNav v-model="activeTab" :tabs="tabs" />
    </div>

    <div v-if="activeTab === 'alerts' && severityValues.length" class="severity-row">
      <p class="severity-row__label">Severity mix</p>
      <div class="severity-chips">
        <span
          v-for="(label, idx) in severityLabels"
          :key="label"
          class="severity-chip"
          :data-level="label.toLowerCase()"
        >
          {{ label }}
          <strong>{{ severityValues[idx] }}</strong>
        </span>
      </div>
    </div>

    <section v-if="activeTab === 'alerts'" class="table-surface">
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
      <div class="table-surface__foot">
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
      </div>
    </section>

    <section v-else class="table-surface">
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
      <div class="table-surface__foot">
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
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { fraudApi } from '@/api/fraud'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
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

const severityOrder = ['critical', 'high', 'medium', 'low']
const severityLabels = computed(() => {
  const counts = severityOrder.map((level) => alerts.value.filter((a) => a.severity === level).length)
  return severityOrder.filter((_, i) => counts[i] > 0).map((s) => s.charAt(0).toUpperCase() + s.slice(1))
})
const severityValues = computed(() => (
  severityOrder
    .map((level) => alerts.value.filter((a) => a.severity === level).length)
    .filter((count) => count > 0)
))

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

<style scoped>
.severity-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem 1rem;
  margin: -0.35rem 0 1rem;
}

.severity-row__label {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--vb-muted);
}

.severity-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.severity-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 650;
  color: var(--vb-ink);
  background: var(--vb-panel);
}

.severity-chip strong {
  font-weight: 800;
}

.severity-chip[data-level='critical'],
.severity-chip[data-level='high'] {
  background: #fff1f2;
  color: #9f1239;
}

.severity-chip[data-level='medium'] {
  background: #fffbeb;
  color: #b45309;
}

.severity-chip[data-level='low'] {
  background: #eff6ff;
  color: #1d4ed8;
}
</style>
