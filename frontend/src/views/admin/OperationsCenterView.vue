<template>
  <div class="admin-page">
    <PageHeader :loading="loading" @refresh="fetchAll" />

    <div class="kpi-strip">
      <div class="kpi-item">
        <p class="kpi-label">Total users</p>
        <p class="kpi-value">{{ overview.total_users || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Active sessions</p>
        <p class="kpi-value is-ok">{{ overview.active_sessions || 0 }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Active queue</p>
        <p class="kpi-value is-info">{{ queues.active_tasks || 0 }}</p>
        <p class="kpi-hint">Background jobs</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">System status</p>
        <p class="kpi-value" :class="health.status === 'healthy' ? 'is-ok' : 'is-danger'">
          {{ health.status === 'healthy' ? 'Healthy' : (health.status || 'Unknown') }}
        </p>
      </div>
    </div>

    <div class="ops-columns page-section">
      <section class="ops-block">
        <h2 class="ops-block__title">System health</h2>
        <p class="ops-block__sub">Service availability</p>
        <dl class="metric-list">
          <div class="metric-row">
            <dt>Overall</dt>
            <dd><span class="admin-badge" :class="health.status === 'healthy' ? 'success' : 'danger'">{{ health.status || 'unknown' }}</span></dd>
          </div>
          <div v-for="(status, service) in health.services || {}" :key="service" class="metric-row">
            <dt class="capitalize">{{ service }}</dt>
            <dd><span class="admin-badge" :class="status === 'healthy' ? 'success' : 'danger'">{{ status }}</span></dd>
          </div>
        </dl>
        <p class="ops-block__foot">Last checked: {{ formatTime(health.timestamp) }}</p>
      </section>

      <section class="ops-block">
        <h2 class="ops-block__title">Infrastructure</h2>
        <p class="ops-block__sub">Runtime resources</p>
        <dl class="metric-list">
          <div class="metric-row"><dt>CPU usage</dt><dd><strong>{{ infra.cpu?.percent || 0 }}%</strong></dd></div>
          <div class="metric-row"><dt>Memory usage</dt><dd><strong>{{ infra.memory?.percent || 0 }}%</strong></dd></div>
          <div class="metric-row"><dt>DB connections</dt><dd><strong>{{ infra.database?.connections || 0 }}</strong></dd></div>
          <div class="metric-row"><dt>Redis clients</dt><dd><strong>{{ infra.redis?.clients || 0 }}</strong></dd></div>
        </dl>
        <p class="ops-block__foot">Uptime: {{ formatUptime(infra.uptime) }}</p>
      </section>

      <section class="ops-block">
        <h2 class="ops-block__title">Queue status</h2>
        <p class="ops-block__sub">Background job throughput</p>
        <dl class="metric-list">
          <div class="metric-row"><dt>Active</dt><dd><strong>{{ queues.active_tasks || 0 }}</strong></dd></div>
          <div class="metric-row"><dt>Scheduled</dt><dd><strong>{{ queues.scheduled_tasks || 0 }}</strong></dd></div>
          <div class="metric-row"><dt>Reserved</dt><dd><strong>{{ queues.reserved_tasks || 0 }}</strong></dd></div>
          <div class="metric-row"><dt>Celery</dt><dd><strong>{{ queues.celery_enabled ? 'Enabled' : 'Off' }}</strong></dd></div>
        </dl>
      </section>
    </div>

    <div class="section-toolbar">
      <div>
        <h2 class="section-toolbar__title">Recent system logs</h2>
        <p class="section-toolbar__sub">Latest platform events</p>
      </div>
    </div>

    <section class="table-surface">
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
import { ref, onMounted } from 'vue'
import { operationsApi } from '@/api/operations'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
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
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  return `${d}d ${h}h ${m}m`
}
const logBadge = (l) => l === 'error' ? 'danger' : l === 'warning' ? 'warning' : 'info'

onMounted(fetchAll)
</script>

<style scoped>
.ops-columns {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (min-width: 900px) {
  .ops-columns {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.ops-block__title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--vb-ink);
}

.ops-block__sub {
  margin: 0.2rem 0 0.85rem;
  font-size: 0.78rem;
  color: var(--vb-muted);
}

.ops-block__foot {
  margin: 0.75rem 0 0;
  font-size: 0.72rem;
  color: var(--vb-muted);
}

.metric-list {
  margin: 0;
  padding: 0;
}

.metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--vb-line);
  font-size: 0.84rem;
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-row dt {
  margin: 0;
  color: var(--vb-muted);
}

.metric-row dd {
  margin: 0;
  color: var(--vb-ink);
}

.metric-row strong {
  font-weight: 800;
}

.capitalize {
  text-transform: capitalize;
}
</style>
