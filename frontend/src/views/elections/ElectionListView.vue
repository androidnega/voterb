<template>
  <Transition name="page-fade" appear>
    <div class="admin-page">
      <PageHeader
        :loading="loading"
        @refresh="fetchElections"
      >
        <template #actions>
          <button
            v-if="canCreateElections"
            type="button"
            class="btn btn-primary"
            @click="showCreateDialog = true"
          >
            <i class="fas fa-plus"></i>
            New Election
          </button>
          <button
            type="button"
            class="btn btn-ghost"
            :disabled="loading"
            @click="fetchElections"
          >
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            <span>Refresh</span>
          </button>
        </template>
      </PageHeader>

      <div v-if="!canCreateElections" class="access-notice page-section">
        <i class="fas fa-eye"></i>
        <span>View-only — you can monitor elections but cannot create or modify them.</span>
      </div>
      <div v-else-if="authStore.isMainEC" class="access-notice page-section is-info">
        <i class="fas fa-info-circle"></i>
        <span>
          You manage institutional elections. Sub EC category elections are visible here but
          read-only.
        </span>
      </div>
      <div v-else-if="authStore.isSubEC" class="access-notice page-section is-info">
        <i class="fas fa-info-circle"></i>
        <span>
          You manage faculty/department elections for your Sub EC scope. Institutional
          elections are not shown here.
        </span>
      </div>

      <div class="election-kpis">
        <div
          v-for="card in statCards"
          :key="card.label"
          class="ekpi-card"
          :class="`ekpi-card--${card.tone}`"
        >
          <span class="ekpi-card__icon">
            <i :class="card.icon"></i>
          </span>
          <div class="ekpi-card__body">
            <span class="ekpi-card__value">{{ loading ? '—' : card.value }}</span>
            <span class="ekpi-card__label">{{ card.label }}</span>
          </div>
          <span v-if="card.hint" class="ekpi-card__hint">{{ card.hint }}</span>
        </div>
      </div>

      <div class="filter-bar page-section">
        <select v-model="statusFilter" class="filter-select">
          <option value="">All statuses</option>
          <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <button type="button" class="btn btn-ghost" @click="clearFilters">Clear</button>
        <span class="filter-meta">{{ panelSubtitle }}</span>
        <span v-if="hasActiveFilters" class="filter-tag">
          <i class="fas fa-filter"></i>
          Filtered
        </span>
      </div>

      <Transition name="content-fade" mode="out-in">
        <div v-if="loading" key="load" class="loading-state page-section">
          <i class="fas fa-spinner fa-spin"></i>
          <p>Loading elections…</p>
        </div>

        <div v-else-if="!sortedElections.length" key="empty" class="page-section">
          <EmptyState
            icon="fas fa-calendar-xmark"
            title="No elections found"
            :message="emptyMessage"
          />
        </div>

        <div v-else key="cards" class="election-grid page-section">
          <article
            v-for="election in sortedElections"
            :key="election.uuid"
            class="election-card"
            :class="{ 'is-live': election.status === 'open' }"
            @click="viewElection(election.uuid)"
          >
            <header class="election-card__head">
              <span class="status-chip" :data-status="election.status">
                <span v-if="election.status === 'open'" class="live-dot" aria-hidden="true"></span>
                {{ election.status }}
              </span>
              <span class="owner-label">
                {{ election.owner_type === 'sub' ? (election.owner_ec_unit_name || 'Sub EC') : 'Institutional' }}
              </span>
            </header>

            <div class="election-card__body">
              <h3 class="election-card__title">{{ election.title }}</h3>
              <p class="election-card__desc">
                {{ election.description || 'No description provided.' }}
              </p>
            </div>

            <div class="election-card__meta-stack">
              <div class="election-card__meta">
                <i class="far fa-calendar" aria-hidden="true"></i>
                <span>{{ formatPeriod(election.start_date, election.end_date) }}</span>
              </div>
              <div class="election-card__meta">
                <i class="fas fa-address-book" aria-hidden="true"></i>
                <span>{{ registerSummary(election) }}</span>
              </div>
              <div class="election-card__meta">
                <i class="fas fa-broadcast-tower" aria-hidden="true"></i>
                <span>{{ channelSummary(election) }}</span>
              </div>
            </div>

            <ElectionCountdown
              v-if="['open', 'paused'].includes(election.status) && election.end_date"
              :election="election"
              label="Voting ends in"
              :beep="false"
            />

            <footer class="election-card__foot" @click.stop>
              <button type="button" class="card-link" @click="viewElection(election.uuid)">
                Open
                <i class="fas fa-arrow-right"></i>
              </button>
              <div class="card-tools">
                <router-link
                  v-if="['open', 'paused', 'closed'].includes(election.status)"
                  :to="`/monitor/${election.uuid}`"
                  class="tool-btn"
                  title="Monitor room"
                >
                  <i class="fas fa-tv"></i>
                </router-link>
                <button
                  v-if="canEditElection(election)"
                  type="button"
                  class="tool-btn"
                  title="Edit"
                  @click="editElection(election.uuid)"
                >
                  <i class="fas fa-pen"></i>
                </button>
                <button
                  v-if="canEditElection(election)"
                  type="button"
                  class="tool-btn is-danger"
                  title="Delete"
                  @click="confirmDelete(election)"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </footer>
          </article>
        </div>
      </Transition>

      <p v-if="!loading && sortedElections.length" class="grid-foot">
        <span>{{ sortedElections.length }} election{{ sortedElections.length === 1 ? '' : 's' }}</span>
        <span v-if="stats.active" class="grid-foot-live">
          <span class="live-indicator"></span>
          {{ stats.active }} live
        </span>
      </p>

      <Dialog
        v-model:visible="showCreateDialog"
        header="Create election"
        :modal="true"
        :dismissableMask="true"
        :draggable="false"
        class="create-election-dialog"
        :style="{ width: 'min(34rem, calc(100vw - 2rem))' }"
        :breakpoints="{ '640px': 'calc(100vw - 1.25rem)' }"
      >
        <CreateElectionForm
          @success="onElectionCreated"
          @pending-approval="onElectionPendingApproval"
          @cancel="showCreateDialog = false"
        />
      </Dialog>

      <GovernanceSubmittedModal
        v-model:visible="showGovernanceModal"
        :message="governanceMessage"
      />
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { electionApi } from '@/api/elections'
import Dialog from 'primevue/dialog'
import PageHeader from '@/components/admin/PageHeader.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import GovernanceSubmittedModal from '@/components/admin/GovernanceSubmittedModal.vue'
import CreateElectionForm from '@/components/elections/CreateElectionForm.vue'
import ElectionCountdown from '@/components/student/ElectionCountdown.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const canCreateElections = computed(() => authStore.isElectionManager)
const canManageElection = (election) => !!election?.can_manage
const canEditElection = (election) =>
  canManageElection(election) && ['draft', 'scheduled'].includes(election?.status)
const canManageElections = canCreateElections

const elections = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const statusFilter = ref('')
const showGovernanceModal = ref(false)
const governanceMessage = ref('')

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
  { label: 'Total', value: stats.value.total, hint: 'All elections', icon: 'fas fa-layer-group', tone: 'slate' },
  { label: 'Open', value: stats.value.active, hint: 'Currently voting', icon: 'fas fa-circle-dot', tone: 'green' },
  { label: 'Scheduled', value: stats.value.scheduled, hint: 'Upcoming', icon: 'fas fa-calendar-day', tone: 'amber' },
  { label: 'Closed', value: stats.value.closed, hint: 'Completed', icon: 'fas fa-flag-checkered', tone: 'blue' },
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
  if (!date) return null
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatPeriod = (start, end) => {
  const a = formatDate(start)
  const b = formatDate(end)
  if (!a && !b) return 'Dates TBA'
  if (a && b) return `${a} – ${b}`
  return a || b
}

const channelSummary = (election) => {
  const parts = []
  if (election.allow_web_voting) parts.push('Web')
  if (election.allow_ussd_voting) parts.push('USSD')
  if (election.allow_sms_notifications) parts.push('SMS')
  return parts.length ? parts.join(' · ') : 'No channels'
}

const registerSummary = (election) => {
  if (!election.register) return 'No register selected'
  const categories = election.register.category_count ?? 0
  const voters = election.register.entry_count ?? election.eligible_voter_count ?? 0
  return `${election.register.name} (${categories} categories · ${voters} voter${voters === 1 ? '' : 's'})`
}

const clearFilters = () => {
  statusFilter.value = ''
}

const viewElection = (uuid) => router.push(`/elections/${uuid}`)
const editElection = (uuid) => router.push(`/elections/${uuid}`)

const confirmDelete = (election) => {
  const votes = election.votes_cast || 0
  const message =
    votes > 0
      ? `Delete "${election.title}"?\n\nThis permanently removes the election, ${votes} vote record(s), SVT tokens, candidates, and related data. This cannot be undone.`
      : `Delete "${election.title}"?\n\nPositions, candidates, and eligibility for this election will also be removed.`
  if (confirm(message)) deleteElection(election.uuid)
}

const deleteElection = async (uuid) => {
  try {
    await electionApi.delete(uuid)
    await fetchElections()
  } catch (error) {
    console.error('Failed to delete election:', error)
    const detail =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      (error.response?.status === 403
        ? 'You do not have permission to delete elections.'
        : 'Failed to delete election. Please try again.')
    alert(detail)
  }
}

const onElectionCreated = (election) => {
  showCreateDialog.value = false
  fetchElections()
  if (election?.uuid) {
    router.push({
      path: `/elections/${election.uuid}`,
      query: { tab: 'positions' },
    })
  }
}

const onElectionPendingApproval = (decision) => {
  showCreateDialog.value = false
  governanceMessage.value =
    decision?.message
    || 'Submitted for approval. Your approval is recorded; the other institutional EC member must also approve before enrollment.'
  showGovernanceModal.value = true
}

onMounted(() => {
  fetchElections()
  if (canCreateElections.value && (route.query.create === '1' || route.query.create === 'true')) {
    showCreateDialog.value = true
  }
})
</script>

<style scoped>
.election-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.35rem;
}

@media (max-width: 900px) {
  .election-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 460px) {
  .election-kpis {
    grid-template-columns: 1fr;
  }
}

.ekpi-card {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  background: #fff;
  border: 1px solid #ebeae4;
  overflow: hidden;
  box-shadow: none;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.ekpi-card::before {
  content: none;
  display: none;
}

.ekpi-card:hover {
  border-color: #d6d3d1;
  background: #fcfcfb;
  box-shadow: none;
  transform: none;
}

.ekpi-card__icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.6rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  background: #f7f6f2;
  color: #8a8a8a;
  flex-shrink: 0;
}

.ekpi-card__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.ekpi-card__value {
  font-size: 1.45rem;
  font-weight: 750;
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: #1c1c1c;
  font-variant-numeric: tabular-nums;
}

.ekpi-card__label {
  margin-top: 0.12rem;
  font-size: 0.74rem;
  font-weight: 600;
  color: #8a8a8a;
}

.ekpi-card__hint {
  display: none;
}

.ekpi-card--slate,
.ekpi-card--green,
.ekpi-card--amber,
.ekpi-card--blue {
  --ekpi-accent: #8a8a8a;
  --ekpi-soft: #f7f6f2;
  --ekpi-border: #ebeae4;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}

.filter-meta {
  margin-left: auto;
  font-size: 0.78rem;
  color: var(--vb-muted, #8a8a8a);
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.6rem;
  border-radius: 9999px;
  background: #f7f6f2;
  color: #5c5c5c;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.election-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18.5rem, 1fr));
  gap: 0.85rem;
}

.election-card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 13.5rem;
  padding: 1.1rem 1.15rem 0.95rem;
  background: #fff;
  border: 1px solid #ebeae4;
  border-radius: 0.9rem;
  box-shadow: none;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.election-card::before,
.election-card::after {
  content: none !important;
  display: none !important;
}

.election-card:hover {
  border-color: #d6d3d1;
  background: #fcfcfb;
}

.election-card.is-live {
  border-color: #ebeae4;
}

.election-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.owner-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #8a8a8a;
  letter-spacing: 0.01em;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.66rem;
  font-weight: 650;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #8a8a8a;
  background: none;
  padding: 0;
}

.status-chip[data-status='open'],
.status-chip[data-status='scheduled'],
.status-chip[data-status='paused'],
.status-chip[data-status='closed'],
.status-chip[data-status='archived'],
.status-chip[data-status='draft'] {
  color: #8a8a8a;
}

.status-chip[data-status='open'] {
  color: #1c1c1c;
}

.live-dot {
  width: 0.3rem;
  height: 0.3rem;
  border-radius: 9999px;
  background: currentColor;
}

.election-card__body {
  display: grid;
  gap: 0.35rem;
  flex: 1;
}

.election-card__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.3;
  color: #1c1c1c;
}

.election-card__desc {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #8a8a8a;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.election-card__meta-stack {
  display: grid;
  gap: 0.3rem;
  margin-top: 0.9rem;
}

.election-card__meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.74rem;
  font-weight: 500;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}

.election-card__meta i {
  width: 0.85rem;
  font-size: 0.72rem;
  color: #b0b0b0;
}

.election-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 0.9rem;
  padding-top: 0.8rem;
  border-top: 1px solid #f0efea;
}

.card-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: none;
  background: transparent;
  padding: 0;
  font-size: 0.8rem;
  font-weight: 650;
  color: #1c1c1c;
  cursor: pointer;
}

.card-link i {
  font-size: 0.65rem;
  color: #8a8a8a;
  transition: transform 0.15s ease, color 0.15s ease;
}

.election-card:hover .card-link i {
  transform: translateX(2px);
  color: #1c1c1c;
}

.card-tools {
  display: inline-flex;
  align-items: center;
  gap: 0.1rem;
}

.tool-btn {
  width: 1.7rem;
  height: 1.7rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 0.45rem;
  background: transparent;
  color: #b0b0b0;
  font-size: 0.7rem;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.tool-btn:hover {
  background: #f7f6f2;
  color: #1c1c1c;
}

.tool-btn.is-danger:hover {
  background: #fdeaea;
  color: #c45c5c;
}

.grid-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: var(--vb-muted, #8a8a8a);
}

.grid-foot-live {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--vb-accent, #3d4f44);
  font-weight: 650;
}

.grid-foot-live .live-indicator {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 9999px;
  background: var(--vb-accent, #3d4f44);
}

.page-fade-enter-active {
  transition: opacity 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
}

.content-fade-enter-active,
.content-fade-leave-active {
  transition: opacity 0.2s ease;
}

.content-fade-enter-from,
.content-fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .filter-meta {
    width: 100%;
    margin-left: 0;
  }

  .election-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
/* Dialog is teleported to body — unscoped styles required */
.create-election-dialog.p-dialog {
  border-radius: 1.15rem;
  overflow: hidden;
  border: 1px solid var(--vb-line, #ebeae4);
  box-shadow: 0 24px 64px rgba(28, 28, 28, 0.16);
}

.create-election-dialog .p-dialog-header {
  padding: 1.05rem 1.25rem 0.85rem;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
}

.create-election-dialog .p-dialog-title {
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: var(--vb-ink, #1c1c1c);
}

.create-election-dialog .p-dialog-header-icons {
  gap: 0.15rem;
}

.create-election-dialog .p-dialog-header-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.55rem;
  color: var(--vb-muted, #8a8a8a);
}

.create-election-dialog .p-dialog-header-icon:enabled:hover {
  background: var(--vb-panel, #f7f6f2);
  color: var(--vb-ink, #1c1c1c);
}

.create-election-dialog .p-dialog-content {
  padding: 1rem 1.25rem 1.2rem;
  background: #fff;
  overflow: visible;
}
</style>
