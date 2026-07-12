<template>
  <div class="admin-page">
    <PageHeader
      title="Operations Center"
      subtitle="Platform health, infrastructure metrics, queues, and system logs."
      icon="fas fa-server"
      icon-tone="tone-slate"
      :loading="loading"
      @refresh="fetchAll"
    />

    <div class="stat-grid page-section">
      <StatCard label="Total Users" :value="overview.total_users || 0" icon="fas fa-users" tone="tone-slate" />
      <StatCard label="Active Sessions" :value="overview.active_sessions || 0" icon="fas fa-plug" tone="tone-teal" value-tone="text-teal-700" />
      <StatCard label="Active Queue" :value="queues.active_tasks || 0" hint="Background jobs" icon="fas fa-tasks" tone="tone-blue" value-tone="text-blue-700" />
      <StatCard
        label="System Status"
        :value="health.status === 'healthy' ? 'Healthy' : 'Degraded'"
        icon="fas fa-heartbeat"
        :tone="health.status === 'healthy' ? 'tone-teal' : 'tone-rose'"
        :value-tone="health.status === 'healthy' ? 'text-teal-700' : 'text-rose-700'"
      />
    </div>

    <div class="ops-grid page-section">
      <DataPanel title="System health" subtitle="Service availability">
        <div class="metric-card-grid">
          <div class="metric-row">
            <span>Overall</span>
            <span class="admin-badge" :class="health.status === 'healthy' ? 'success' : 'danger'">{{ health.status || 'unknown' }}</span>
          </div>
          <div v-for="(status, service) in health.services || {}" :key="service" class="metric-row">
            <span class="capitalize">{{ service }}</span>
            <span class="admin-badge" :class="status === 'healthy' ? 'success' : 'danger'">{{ status }}</span>
          </div>
        </div>
        <p class="panel-foot">Last checked: {{ formatTime(health.timestamp) }}</p>
      </DataPanel>

      <DataPanel title="Infrastructure" subtitle="Runtime resources">
        <div class="metric-card-grid">
          <div class="metric-row"><span>CPU Usage</span><strong>{{ infra.cpu?.percent || 0 }}%</strong></div>
          <div class="metric-row"><span>Memory Usage</span><strong>{{ infra.memory?.percent || 0 }}%</strong></div>
          <div class="metric-row"><span>DB Connections</span><strong>{{ infra.database?.connections || 0 }}</strong></div>
          <div class="metric-row"><span>Redis Clients</span><strong>{{ infra.redis?.clients || 0 }}</strong></div>
        </div>
        <p class="panel-foot">Uptime: {{ formatUptime(infra.uptime) }}</p>
      </DataPanel>

      <DataPanel title="Queue status" subtitle="Background job throughput">
        <div class="metric-card-grid">
          <div class="metric-row"><span>Active</span><strong>{{ queues.active_tasks || 0 }}</strong></div>
          <div class="metric-row"><span>Scheduled</span><strong>{{ queues.scheduled_tasks || 0 }}</strong></div>
          <div class="metric-row"><span>Reserved</span><strong>{{ queues.reserved_tasks || 0 }}</strong></div>
          <div class="metric-row"><span>Celery</span><strong>{{ queues.celery_enabled ? 'Enabled' : 'Off' }}</strong></div>
        </div>
      </DataPanel>
    </div>

    <DataPanel title="Recent system logs" subtitle="Latest platform events" no-padding class="page-section">
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Level</th>
              <th>Timestamp</th>
              <th>Source</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, idx) in paginated" :key="`${log.timestamp}-${idx}`">
              <td><span class="admin-badge" :class="logBadge(log.level)">{{ log.level }}</span></td>
              <td class="text-muted">{{ formatTime(log.timestamp) }}</td>
              <td>{{ log.source }}</td>
              <td>{{ log.message }}</td>
            </tr>
            <tr v-if="!loading && logs.length === 0">
              <td colspan="4"><EmptyState icon="fas fa-terminal" title="No system logs" /></td>
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
import { operationsApi } from '@/api/operations'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'

const overview = ref({})
const health = ref({})
const infra = ref({})
const queues = ref({})
const logs = ref([])
const loading = ref(false)

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize } = usePagination(logs, 10)

const fetchAll = async () => {
  loading.value = true
  try {
    const [overviewRes, healthRes, infraRes, queuesRes, logsRes] = await Promise.all([
      operationsApi.getOverview(),
      operationsApi.getHealth(),
      operationsApi.getInfrastructure(),
      operationsApi.getQueues(),
      operationsApi.getLogs(),
    ])
    overview.value = overviewRes.data
    health.value = healthRes.data
    infra.value = infraRes.data
    queues.value = queuesRes.data
    logs.value = logsRes.data
  } catch (error) {
    console.error('Failed to fetch operations data:', error)
  } finally {
    loading.value = false
  }
}

const formatTime = (ts) => ts ? new Date(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'
const formatUptime = (s) => {
  if (!s) return '—'
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60)
  return `${d}d ${h}h ${m}m`
}
const logBadge = (l) => l === 'error' ? 'danger' : l === 'warning' ? 'warning' : 'info'

onMounted(fetchAll)
</script>

