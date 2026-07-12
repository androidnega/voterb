<template>
  <div class="admin-page">
    <PageHeader
      title="Audit Logs"
      subtitle="Unified security, MFA, and system activity trail for compliance review."
      icon="fas fa-clipboard-list"
      icon-tone="tone-indigo"
      :loading="loading"
      @refresh="fetchLogs"
    />

    <div class="stat-grid page-section">
      <StatCard label="Total events" :value="derivedStats.total" icon="fas fa-database" tone="tone-slate" />
      <StatCard label="Today" :value="derivedStats.today" icon="fas fa-sun" tone="tone-teal" value-tone="text-teal-700" />
      <StatCard label="MFA events" :value="derivedStats.mfa" icon="fas fa-key" tone="tone-blue" value-tone="text-blue-700" />
      <StatCard label="Audit events" :value="derivedStats.audit" icon="fas fa-file-alt" tone="tone-indigo" value-tone="text-indigo-700" />
    </div>

    <div class="audit-layout page-section">
      <DataPanel title="Event mix" subtitle="Breakdown of loaded activity">
        <DonutChart
          :labels="chartLabels"
          :data="chartValues"
          :empty="!chartValues.some((v) => v > 0)"
          height="14rem"
          empty-text="No events to chart"
          aria-label="Audit event type breakdown"
        />
      </DataPanel>

      <div class="audit-filters">
        <div class="filter-bar">
          <div class="filter-input-wrap">
            <i class="fas fa-search"></i>
            <input v-model="filters.event_type" type="text" placeholder="Filter by event type…" @keyup.enter="applyFilters" />
          </div>
          <div class="filter-input-wrap">
            <i class="fas fa-user"></i>
            <input v-model="filters.user" type="text" placeholder="User email…" @keyup.enter="applyFilters" />
          </div>
          <button type="button" class="btn btn-primary" @click="applyFilters"><i class="fas fa-filter"></i> Apply</button>
          <button type="button" class="btn btn-ghost" @click="clearFilters">Clear</button>
        </div>
      </div>
    </div>

    <DataPanel title="Activity log" subtitle="Most recent events first" no-padding>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>User</th>
              <th>Event</th>
              <th>IP</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in paginated" :key="log.uuid || `${log.type}-${log.timestamp}-${log.event_type}`">
              <td><span class="admin-badge" :class="log.type === 'mfa' ? 'info' : 'neutral'">{{ log.type }}</span></td>
              <td>{{ log.user?.email || log.user || 'System' }}</td>
              <td class="mono">{{ log.event_type }}</td>
              <td class="text-muted">{{ log.ip_address || '—' }}</td>
              <td class="text-muted">{{ formatDate(log.timestamp || log.created_at) }}</td>
            </tr>
            <tr v-if="!loading && logs.length === 0">
              <td colspan="5">
                <EmptyState icon="fas fa-clipboard-list" title="No logs found" message="Try adjusting your filters or check back later." />
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { auditApi } from '@/api/audit'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'
import DonutChart from '@/components/charts/DonutChart.vue'

const logs = ref([])
const loading = ref(false)
const filters = ref({ event_type: '', user: '' })

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize, reset } = usePagination(logs, 15)

const startOfToday = () => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}

const derivedStats = computed(() => {
  const today = startOfToday()
  let mfa = 0
  let audit = 0
  let todayCount = 0
  for (const log of logs.value) {
    if (log.type === 'mfa') mfa += 1
    else audit += 1
    const ts = new Date(log.timestamp || log.created_at || 0)
    if (ts >= today) todayCount += 1
  }
  return {
    total: logs.value.length,
    today: todayCount,
    mfa,
    audit,
  }
})

const chartLabels = computed(() => ['MFA', 'Audit'])
const chartValues = computed(() => [derivedStats.value.mfa, derivedStats.value.audit])

const normalizeLogs = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.logs)) return payload.logs
  return []
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.event_type) params.event_type = filters.value.event_type
    if (filters.value.user) params.user = filters.value.user
    const response = await auditApi.getCombined(params)
    logs.value = normalizeLogs(response.data)
    reset()
  } catch (error) {
    console.error('Failed to fetch logs:', error)
    logs.value = []
  } finally {
    loading.value = false
  }
}

const applyFilters = () => fetchLogs()
const clearFilters = () => {
  filters.value = { event_type: '', user: '' }
  fetchLogs()
}
const formatDate = (date) => (
  date
    ? new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
    : '—'
)

onMounted(fetchLogs)
</script>

<style scoped>
.audit-layout {
  display: grid;
  gap: 1rem;
}

@media (min-width: 900px) {
  .audit-layout {
    grid-template-columns: 0.9fr 1.1fr;
    align-items: start;
  }
}

.audit-filters .filter-bar {
  margin-bottom: 0;
}
</style>
