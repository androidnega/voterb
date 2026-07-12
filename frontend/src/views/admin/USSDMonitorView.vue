<template>
  <div class="admin-page">
    <PageHeader
      title="USSD Monitor"
      subtitle="Live view of USSD voting sessions, steps, and channel errors."
      icon="fas fa-mobile-alt"
      icon-tone="tone-blue"
      :loading="loading"
      @refresh="fetchAll"
    />

    <div class="stat-grid page-section">
      <StatCard label="Total Sessions" :value="stats.total_sessions || 0" icon="fas fa-phone" tone="tone-slate" />
      <StatCard label="Active" :value="stats.active_sessions || 0" icon="fas fa-signal" tone="tone-teal" value-tone="text-teal-700" />
      <StatCard label="Completed" :value="stats.completed_sessions || 0" icon="fas fa-check-circle" tone="tone-blue" value-tone="text-blue-700" />
      <StatCard label="Errors" :value="stats.error_sessions || 0" icon="fas fa-times-circle" tone="tone-rose" value-tone="text-rose-700" />
    </div>

    <div class="ussd-layout page-section">
      <DataPanel title="Session status" subtitle="Channel funnel from live stats">
        <DonutChart
          :labels="chartLabels"
          :data="chartValues"
          :empty="!chartValues.some((v) => v > 0)"
          height="13rem"
          empty-text="No USSD sessions yet"
          aria-label="USSD session status breakdown"
        />
      </DataPanel>

      <DataPanel title="Session feed" subtitle="Auto-refreshes every 15s" no-padding>
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
        <template #footer>
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
        </template>
      </DataPanel>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ussdApi } from '@/api/ussd'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'
import DonutChart from '@/components/charts/DonutChart.vue'

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

const chartLabels = computed(() => statusSeries.value.map((row) => row.label))
const chartValues = computed(() => statusSeries.value.map((row) => row.value))

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
.ussd-layout {
  display: grid;
  gap: 1rem;
}

@media (min-width: 1000px) {
  .ussd-layout {
    grid-template-columns: 0.85fr 1.15fr;
    align-items: start;
  }
}
</style>
