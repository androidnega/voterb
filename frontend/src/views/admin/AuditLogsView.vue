<template>
  <div class="admin-page">
    <PageHeader
      title="Audit Logs"
      subtitle="Unified security, MFA, and system activity trail for compliance review."
      icon="fas fa-clipboard-list"
      icon-tone="tone-indigo"
      :loading="loading"
      @refresh="fetchAll"
    />

    <div class="stat-grid page-section">
      <StatCard label="Total Logs" :value="stats.total_logs || 0" icon="fas fa-database" tone="tone-slate" />
      <StatCard label="Today" :value="stats.today_logs || 0" icon="fas fa-sun" tone="tone-teal" value-tone="text-teal-700" />
      <StatCard label="MFA Events" :value="stats.mfa_count || 0" icon="fas fa-key" tone="tone-blue" value-tone="text-blue-700" />
      <StatCard label="Audit Events" :value="stats.audit_count || 0" icon="fas fa-file-alt" tone="tone-indigo" value-tone="text-indigo-700" />
    </div>

    <div class="filter-bar page-section">
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
            <tr v-for="log in paginated" :key="log.uuid">
              <td><span class="admin-badge" :class="log.type === 'mfa' ? 'info' : 'neutral'">{{ log.type }}</span></td>
              <td>{{ log.user?.email || 'System' }}</td>
              <td class="mono">{{ log.event_type }}</td>
              <td class="text-muted">{{ log.ip_address || '—' }}</td>
              <td class="text-muted">{{ formatDate(log.timestamp) }}</td>
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
import { ref, onMounted } from 'vue'
import { auditApi } from '@/api/audit'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'

const logs = ref([])
const stats = ref({})
const loading = ref(false)
const filters = ref({ event_type: '', user: '' })

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize, reset } = usePagination(logs, 15)

const fetchStats = async () => {
  try {
    const response = await auditApi.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch audit stats:', error)
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
    reset()
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  } finally {
    loading.value = false
  }
}

const fetchAll = async () => {
  await Promise.all([fetchStats(), fetchLogs()])
}

const applyFilters = () => fetchLogs()
const clearFilters = () => { filters.value = { event_type: '', user: '' }; fetchLogs() }
const formatDate = (date) => date ? new Date(date).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'

onMounted(fetchAll)
</script>
