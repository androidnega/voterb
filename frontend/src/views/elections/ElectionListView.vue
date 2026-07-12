<template>
  <Transition name="page-fade" appear>
    <div class="admin-page">
      <PageHeader
        title="Elections"
        :subtitle="canManageElections
          ? 'Create, schedule, and monitor institutional elections.'
          : 'Read-only view of all institutional elections.'"
        icon="fas fa-calendar-check"
        icon-tone="tone-teal"
        :loading="loading"
        @refresh="fetchElections"
      >
        <template #actions>
          <button
            v-if="canManageElections"
            type="button"
            class="btn btn-primary"
            @click="showCreateDialog = true"
          >
            <i class="fas fa-plus"></i>
            New Election
          </button>
        </template>
      </PageHeader>

      <div v-if="!canManageElections" class="access-notice page-section">
        <i class="fas fa-eye"></i>
        <span>View-only — you can monitor elections but cannot create or modify them.</span>
      </div>

      <TransitionGroup name="stat-fade" tag="div" class="stat-grid page-section" appear>
        <StatCard
          v-for="card in statCards"
          :key="card.label"
          :label="card.label"
          :value="loading ? '—' : card.value"
          :hint="card.hint"
          :icon="card.icon"
          :tone="card.tone"
          :value-tone="card.valueTone"
        />
      </TransitionGroup>

      <div class="filter-bar page-section">
        <select v-model="statusFilter" class="filter-select">
          <option value="">All statuses</option>
          <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <button type="button" class="btn btn-ghost" @click="clearFilters">Clear</button>
      </div>

      <DataPanel
        title="All elections"
        :subtitle="panelSubtitle"
        no-padding
      >
        <template #header>
          <span v-if="hasActiveFilters" class="filter-tag">
            <i class="fas fa-filter"></i>
            Filtered
          </span>
        </template>

        <Transition name="content-fade" mode="out-in">
          <div v-if="loading" key="load" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading elections…</p>
          </div>

          <div v-else key="content" class="admin-table-wrap elections-table-wrap">
            <table class="admin-table elections-table">
              <thead>
                <tr>
                  <th class="col-election">Election</th>
                  <th class="col-type">Type</th>
                  <th class="col-status">Status</th>
                  <th class="col-period">Period</th>
                  <th class="col-actions text-center">Actions</th>
                </tr>
              </thead>
              <TransitionGroup v-if="sortedElections.length" tag="tbody" name="row-fade" appear>
                <tr
                  v-for="election in sortedElections"
                  :key="election.uuid"
                  class="election-row"
                  :class="{ 'is-live': election.status === 'open' }"
                >
                  <td class="col-election">
                    <button type="button" class="election-cell" @click="viewElection(election.uuid)">
                      <div class="election-avatar" :class="statusTone(election.status)">
                        <i class="fas fa-landmark"></i>
                      </div>
                      <div class="election-info">
                        <span class="cell-title">{{ election.title }}</span>
                        <span class="cell-sub">{{ election.description || 'No description' }}</span>
                      </div>
                    </button>
                  </td>
                  <td class="col-type">
                    <span class="type-tag">{{ formatType(election.election_type) }}</span>
                  </td>
                  <td class="col-status">
                    <span class="admin-badge" :class="statusBadge(election.status)">
                      <span v-if="election.status === 'open'" class="live-indicator"></span>
                      {{ election.status }}
                    </span>
                  </td>
                  <td class="col-period">
                    <div class="period-stack">
                      <div class="period-line">
                        <span class="period-key">Start</span>
                        <span class="period-val">{{ formatDate(election.start_date) }}</span>
                      </div>
                      <div class="period-line">
                        <span class="period-key">End</span>
                        <span class="period-val">{{ formatDate(election.end_date) }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="col-actions">
                    <div class="action-group">
                      <router-link
                        v-if="['open', 'paused', 'closed'].includes(election.status)"
                        :to="`/monitor/${election.uuid}`"
                        class="admin-icon-btn"
                        :class="{ 'is-accent': election.status === 'open' }"
                        title="Monitor room"
                      >
                        <i class="fas fa-tv"></i>
                      </router-link>
                      <button
                        type="button"
                        class="admin-icon-btn"
                        title="View details"
                        @click="viewElection(election.uuid)"
                      >
                        <i class="fas fa-eye"></i>
                      </button>
                      <button
                        v-if="canManageElections"
                        type="button"
                        class="admin-icon-btn"
                        title="Edit"
                        @click="editElection(election.uuid)"
                      >
                        <i class="fas fa-pen"></i>
                      </button>
                      <button
                        v-if="canManageElections"
                        type="button"
                        class="admin-icon-btn danger"
                        title="Delete"
                        @click="confirmDelete(election)"
                      >
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </TransitionGroup>
              <tbody v-else>
                <tr>
                  <td colspan="5">
                    <EmptyState
                      icon="fas fa-calendar-xmark"
                      title="No elections found"
                      :message="emptyMessage"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Transition>

        <template v-if="!loading && sortedElections.length" #footer>
          <div class="table-foot">
            <span>{{ sortedElections.length }} election{{ sortedElections.length === 1 ? '' : 's' }}</span>
            <span v-if="stats.active" class="table-foot-live">
              <span class="live-indicator"></span>
              {{ stats.active }} live
            </span>
          </div>
        </template>
      </DataPanel>

      <Dialog
        v-model:visible="showCreateDialog"
        header="Create New Election"
        :modal="true"
        class="w-full max-w-lg"
      >
        <CreateElectionForm @success="onElectionCreated" @cancel="showCreateDialog = false" />
      </Dialog>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { electionApi } from '@/api/elections'
import Dialog from 'primevue/dialog'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import CreateElectionForm from '@/components/elections/CreateElectionForm.vue'

const router = useRouter()
const authStore = useAuthStore()
const canManageElections = computed(() => authStore.isElectionManager)

const elections = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const statusFilter = ref('')

const statusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'draft', label: 'Draft' },
  { value: 'paused', label: 'Paused' },
  { value: 'closed', label: 'Closed' },
  { value: 'archived', label: 'Archived' },
]

const stats = computed(() => ({
  total: elections.value.length,
  active: elections.value.filter((e) => e.status === 'open').length,
  scheduled: elections.value.filter((e) => e.status === 'scheduled').length,
  closed: elections.value.filter((e) => e.status === 'closed' || e.status === 'archived').length,
}))

const statCards = computed(() => [
  {
    label: 'Total',
    value: stats.value.total,
    hint: 'All elections',
    icon: 'fas fa-layer-group',
    tone: 'tone-slate',
    valueTone: 'text-slate-900',
  },
  {
    label: 'Open',
    value: stats.value.active,
    hint: 'Currently voting',
    icon: 'fas fa-signal',
    tone: 'tone-teal',
    valueTone: 'text-teal-700',
  },
  {
    label: 'Scheduled',
    value: stats.value.scheduled,
    hint: 'Upcoming',
    icon: 'fas fa-clock',
    tone: 'tone-amber',
    valueTone: 'text-amber-700',
  },
  {
    label: 'Closed',
    value: stats.value.closed,
    hint: 'Completed',
    icon: 'fas fa-archive',
    tone: 'tone-indigo',
    valueTone: 'text-indigo-700',
  },
])

const filteredElections = computed(() => {
  let list = elections.value
  if (statusFilter.value) {
    list = list.filter((e) => e.status === statusFilter.value)
  }
  return list
})

const STATUS_ORDER = { open: 0, paused: 1, scheduled: 2, draft: 3, closed: 4, archived: 5 }

const sortedElections = computed(() =>
  [...filteredElections.value].sort((a, b) => {
    const orderDiff = (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9)
    if (orderDiff !== 0) return orderDiff
    return new Date(b.start_date || 0) - new Date(a.start_date || 0)
  })
)

const hasActiveFilters = computed(() => !!statusFilter.value)

const panelSubtitle = computed(() => {
  if (loading.value) return 'Loading…'
  const n = sortedElections.value.length
  return `${n} election${n === 1 ? '' : 's'} · open first`
})

const emptyMessage = computed(() => {
  if (hasActiveFilters.value) return 'Try adjusting your status filter.'
  if (canManageElections.value) return 'Create your first election to get started.'
  return 'No elections available.'
})

const fetchElections = async () => {
  loading.value = true
  try {
    const { data } = await electionApi.list()
    elections.value = data
  } catch (error) {
    console.error('Failed to fetch elections:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return 'TBA'
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatType = (type) => (type || '—').replace(/_/g, ' ')

const statusBadge = (status) => {
  const map = {
    draft: 'neutral',
    scheduled: 'info',
    open: 'success',
    paused: 'warning',
    closed: 'danger',
    archived: 'neutral',
  }
  return map[status] || 'neutral'
}

const statusTone = (status) => {
  const map = {
    open: 'tone-teal',
    scheduled: 'tone-blue',
    draft: 'tone-slate',
    paused: 'tone-amber',
    closed: 'tone-indigo',
    archived: 'tone-slate',
  }
  return map[status] || 'tone-slate'
}

const clearFilters = () => {
  statusFilter.value = ''
}

const viewElection = (uuid) => router.push(`/elections/${uuid}`)
const editElection = (uuid) => router.push(`/elections/${uuid}`)

const confirmDelete = (election) => {
  if (confirm(`Delete "${election.title}"?`)) deleteElection(election.uuid)
}

const deleteElection = async (uuid) => {
  try {
    await electionApi.delete(uuid)
    await fetchElections()
  } catch (error) {
    console.error('Failed to delete election:', error)
    alert('Failed to delete election. Please try again.')
  }
}

const onElectionCreated = () => {
  showCreateDialog.value = false
  fetchElections()
}

onMounted(fetchElections)
</script>

<style scoped>
.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.65rem;
  border-radius: 9999px;
  background: #ecfdf5;
  color: #0f766e;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.elections-table-wrap {
  /* scroll + max-height from .admin-table-wrap */
}

.elections-table {
  table-layout: fixed;
}

.elections-table thead th {
  padding: 0.75rem 1.25rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  /* sticky + scroll from global .admin-table-wrap / .admin-table */
}

.elections-table tbody td {
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid #f1f5f9;
}

.elections-table tbody tr:last-child td {
  border-bottom: none;
}

.col-election { width: 38%; }
.col-type { width: 14%; }
.col-status { width: 12%; }
.col-period { width: 20%; }
.col-actions { width: 16%; }

.election-row {
  transition: background 0.15s ease;
}

.election-row.is-live {
  background: #fafefd;
}

.election-row.is-live td:first-child {
  box-shadow: inset 3px 0 0 #14b8a6;
}

.election-row:hover {
  background: #f8fafc;
}

.election-row.is-live:hover {
  background: #f0fdfa;
}

.election-cell {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
}

.election-avatar {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.election-info {
  min-width: 0;
  flex: 1;
}

.election-cell:hover .cell-title {
  color: #0f766e;
}

.election-info .cell-sub {
  display: block;
  margin-top: 0.15rem;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.type-tag {
  display: inline-block;
  padding: 0.25rem 0.55rem;
  border-radius: 0.45rem;
  background: #f8fafc;
  border: 1px solid #eef2f7;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  text-transform: capitalize;
  white-space: nowrap;
}

.period-stack {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.period-line {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.78rem;
}

.period-key {
  width: 2.25rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #94a3b8;
}

.period-val {
  color: #334155;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.elections-table .admin-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.live-indicator {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 9999px;
  background: currentColor;
  flex-shrink: 0;
}

.action-group {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  padding: 0.2rem;
  background: #fafbfc;
  border: 1px solid #f1f5f9;
  border-radius: 0.65rem;
}

.col-actions .row-actions,
.col-actions {
  text-align: center;
}

.action-group .admin-icon-btn {
  width: 1.85rem;
  height: 1.85rem;
  font-size: 0.75rem;
}

.action-group .admin-icon-btn.is-accent {
  color: #0f766e;
  background: #ecfdf5;
  border-color: #d1fae5;
}

.action-group .admin-icon-btn.is-accent:hover {
  background: #d1fae5;
  color: #047857;
}

.table-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  font-size: 0.78rem;
  color: #64748b;
}

.table-foot-live {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: #0f766e;
  font-weight: 600;
}

.table-foot-live .live-indicator {
  background: #34d399;
}

@media (max-width: 900px) {
  .elections-table {
    table-layout: auto;
  }

  .col-election,
  .col-type,
  .col-status,
  .col-period,
  .col-actions {
    width: auto;
  }
}

@media (max-width: 768px) {
  .elections-table thead {
    display: none;
  }

  .elections-table tbody tr {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.5rem 1rem;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #f1f5f9;
  }

  .elections-table tbody td {
    border: none;
    padding: 0;
  }

  .elections-table tbody td.col-election {
    grid-column: 1 / -1;
  }

  .elections-table tbody td.col-period {
    grid-column: 1;
  }

  .elections-table tbody td.col-actions {
    grid-column: 1 / -1;
    padding-top: 0.35rem;
  }

  .action-group {
    width: 100%;
    justify-content: flex-start;
  }

  .election-row.is-live td:first-child {
    box-shadow: none;
  }

  .election-row.is-live {
    border-left: 3px solid #14b8a6;
    padding-left: calc(1.25rem - 3px);
  }
}

/* Animations */
.page-fade-enter-active {
  transition: opacity 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
}

.stat-fade-enter-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.stat-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.content-fade-enter-active,
.content-fade-leave-active {
  transition: opacity 0.2s ease;
}

.content-fade-enter-from,
.content-fade-leave-to {
  opacity: 0;
}

.row-fade-enter-active {
  transition: opacity 0.25s ease;
}

.row-fade-enter-from {
  opacity: 0;
}

.row-fade-move {
  transition: transform 0.25s ease;
}
</style>
