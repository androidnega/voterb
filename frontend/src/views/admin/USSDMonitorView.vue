<template>
  <div class="admin-page">
    <PageHeader :loading="loading" @refresh="fetchAll" />

    <div class="kpi-strip">
      <div class="kpi-item">
        <p class="kpi-label">Total sessions</p>
        <p class="kpi-value">{{ stats.total_sessions || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Active</p>
        <p class="kpi-value is-ok">{{ stats.active_sessions || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Completed</p>
        <p class="kpi-value is-info">{{ stats.completed_sessions || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Errors</p>
        <p class="kpi-value is-danger">{{ stats.error_sessions || 0 }}</p>
      </div>
    </div>

    <div class="section-toolbar">
      <div>
        <h2 class="section-toolbar__title">Session feed</h2>
        <p class="section-toolbar__sub">Auto-refreshes every 15s</p>
      </div>
      <div v-if="statusSeries.length" class="severity-chips">
        <span
          v-for="row in statusSeries"
          :key="row.label"
          class="status-chip"
        >
          {{ row.label }}
          <strong>{{ row.value }}</strong>
        </span>
      </div>
    </div>

    <section class="table-surface">
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>MSISDN</th>
              <th>User</th>
              <th>Election</th>
              <th>Status</th>
              <th>Step</th>
              <th>Created</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="session in paginated" :key="session.uuid">
              <td class="mono">{{ session.msisdn }}</td>
              <td>{{ session.user_email || '—' }}</td>
              <td>{{ session.election_title || '—' }}</td>
              <td><span class="admin-badge" :class="statusBadge(session.status)">{{ session.status }}</span></td>
              <td>{{ session.current_step || '—' }}</td>
              <td class="text-muted">{{ formatDate(session.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button type="button" class="admin-icon-btn" title="View session" @click="viewSession(session.uuid)">
                    <i class="fas fa-eye"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && sessions.length === 0">
              <td colspan="7">
                <EmptyState icon="fas fa-mobile-alt" title="No USSD sessions" message="Sessions will appear when voters use the USSD channel." />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="table-surface__foot">
        <TablePagination
          :page="page"
          :page-size="size"
          :total="total"
          :total-pages="totalPages"
          :from="from"
          :to="to"
          @update:page="setPage"
          @update:page-size="setPageSize"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ussdApi } from '@/api/ussd'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'

const REFRESH_MS = 15000
const router = useRouter()
const sessions = ref([])
const stats = ref({})
const loading = ref(false)
let refreshTimer = null

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize } = usePagination(sessions, 10)

const statusSeries = computed(() => ([
  { label: 'Active', value: stats.value.active_sessions || 0 },
  { label: 'Completed', value: stats.value.completed_sessions || 0 },
  { label: 'Errors', value: stats.value.error_sessions || 0 },
  { label: 'Expired', value: stats.value.expired_sessions || 0 },
]).filter((row) => row.value > 0))

const fetchAll = async (options = {}) => {
  const { silent = false } = options
  if (!silent) loading.value = true
  try {
    const [statsRes, sessionsRes] = await Promise.all([ussdApi.getStats(), ussdApi.listSessions()])
    stats.value = statsRes.data || {}
    const payload = sessionsRes.data
    sessions.value = Array.isArray(payload) ? payload : (payload?.results || [])
  } catch (error) {
    console.error('Failed to fetch USSD data:', error)
  } finally {
    if (!silent) loading.value = false
  }
}

const formatDate = (date) => date ? new Date(date).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
const statusBadge = (s) => ({ active: 'success', completed: 'info', expired: 'warning', error: 'danger' }[s] || 'neutral')
const viewSession = (uuid) => router.push(`/ussd/${uuid}`)

onMounted(() => {
  fetchAll()
  refreshTimer = setInterval(() => fetchAll({ silent: true }), REFRESH_MS)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.severity-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 650;
  background: var(--vb-panel);
  color: var(--vb-ink);
}

.status-chip strong {
  font-weight: 800;
}
</style>
