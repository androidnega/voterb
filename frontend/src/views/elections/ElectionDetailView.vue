<template>
  <div v-if="election" class="admin-page election-detail">
    <button type="button" class="btn-back page-section" @click="router.push('/elections')">
      <i class="fas fa-arrow-left"></i>
      Back to elections
    </button>

    <PageHeader
      :title="election.title"
      :subtitle="election.description || 'No description provided.'"
      icon="fas fa-landmark"
      icon-tone="tone-teal"
      :show-refresh="false"
    >
      <template #actions>
        <span class="admin-badge detail-status" :class="statusBadge(election.status)">
          <span v-if="election.status === 'open'" class="live-dot"></span>
          {{ election.status }}
        </span>
        <div class="action-toolbar">
          <button
            v-if="canOpenMonitor"
            type="button"
            class="btn btn-ghost"
            @click="router.push(`/monitor/${election.uuid}`)"
          >
            <i class="fas fa-tv"></i>
            Monitor
          </button>
          <button
            v-if="canManageElections && election.status === 'draft'"
            type="button"
            class="btn btn-ghost"
            @click="updateStatus('scheduled')"
          >
            <i class="fas fa-calendar-plus"></i>
            Schedule
          </button>
          <button
            v-if="canManageElections && election.status === 'scheduled'"
            type="button"
            class="btn btn-primary"
            @click="openElection"
          >
            <i class="fas fa-play"></i>
            Open
          </button>
          <button
            v-if="canManageElections && (election.status === 'open' || election.status === 'paused')"
            type="button"
            class="btn btn-danger"
            @click="closeElection"
          >
            <i class="fas fa-stop"></i>
            Close
          </button>
          <button
            v-if="canManageElections && election.status === 'closed' && !resultExists"
            type="button"
            class="btn btn-primary"
            :disabled="isGenerating"
            @click="generateResults"
          >
            <i class="fas fa-cog" :class="{ 'fa-spin': isGenerating }"></i>
            Generate results
          </button>
          <button
            v-if="resultExists"
            type="button"
            class="btn btn-primary"
            @click="router.push(`/results/${election.uuid}`)"
          >
            <i class="fas fa-chart-bar"></i>
            View results
          </button>
        </div>
      </template>
    </PageHeader>

    <div v-if="!canManageElections" class="access-notice page-section">
      <i class="fas fa-eye"></i>
      <span>View-only — election management is handled by the Election Committee.</span>
    </div>

    <div class="stat-grid page-section">
      <StatCard
        label="Status"
        :value="election.status"
        :hint="formatType(election.election_type)"
        icon="fas fa-flag"
        tone="tone-slate"
      />
      <StatCard
        label="Voters"
        :value="voterCount"
        hint="Registered"
        icon="fas fa-users"
        tone="tone-blue"
        value-tone="text-blue-700"
      />
      <StatCard
        label="Votes cast"
        :value="election.votes_cast ?? 0"
        :hint="`${election.unique_voters ?? 0} unique voters`"
        icon="fas fa-check-double"
        tone="tone-teal"
        value-tone="text-teal-700"
      />
      <StatCard
        label="Turnout"
        :value="`${turnoutPct}%`"
        :hint="scheduleHint"
        icon="fas fa-chart-line"
        tone="tone-amber"
        value-tone="text-amber-700"
      />
    </div>

    <section v-if="showElectionCharts" class="page-section">
      <div class="section-head">
        <h2 class="section-title">Live results snapshot</h2>
        <p class="section-subtitle">Vote totals and turnout for {{ chartPosition?.title || 'this election' }}</p>
      </div>
      <div class="election-charts">
        <DataPanel title="Candidate performance" subtitle="Votes per candidate">
          <BarChart
            :labels="candidateLabels"
            :data="candidateVotes"
            aria-label="Candidate performance bar chart"
          />
        </DataPanel>
        <DataPanel title="Vote distribution" subtitle="Share of votes in this race">
          <DonutChart
            :labels="candidateLabels"
            :data="candidateVotes"
            aria-label="Vote distribution donut chart"
          />
        </DataPanel>
        <DataPanel title="Turnout trend" subtitle="Participation over the voting window">
          <AreaChart
            :labels="turnoutTrend.labels"
            :data="turnoutTrend.turnout"
            label="Turnout %"
            aria-label="Turnout trend area chart"
          />
        </DataPanel>
      </div>
    </section>

    <TabNav v-model="activeTab" :tabs="tabItems" class="page-section" />

    <DataPanel
      :title="activePanel.title"
      :subtitle="activePanel.subtitle"
      :no-padding="activeTab !== 'positions'"
    >
      <template v-if="canManageElections && activeTab === 'positions'" #header>
        <button type="button" class="btn btn-primary" @click="showPositionDialog = true">
          <i class="fas fa-plus"></i>
          Add position
        </button>
      </template>

      <!-- Positions -->
      <div v-if="activeTab === 'positions'">
        <div v-if="loadingPositions" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <p>Loading positions…</p>
        </div>
        <div v-else class="admin-table-wrap">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Max votes</th>
                <th>Order</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="position in positions" :key="position.uuid">
                <td><span class="cell-title">{{ position.title }}</span></td>
                <td class="mono">{{ position.max_votes_allowed }}</td>
                <td class="mono">{{ position.display_order }}</td>
                <td>
                  <span class="admin-badge" :class="position.is_active ? 'success' : 'neutral'">
                    {{ position.is_active ? 'Yes' : 'No' }}
                  </span>
                </td>
              </tr>
              <tr v-if="positions.length === 0">
                <td colspan="4">
                  <EmptyState
                    icon="fas fa-list"
                    title="No positions yet"
                    message="Add positions before registering candidates."
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Candidates -->
      <div v-else-if="activeTab === 'candidates'" class="tab-panel-body">
        <CandidateManager
          :election-uuid="route.params.uuid"
          :readonly="!canManageElections"
          @updated="candidateCount = $event"
        />
      </div>

      <!-- Voters -->
      <div v-else-if="activeTab === 'voters'">
        <VoterManager :election-uuid="route.params.uuid" :readonly="!canManageElections" />
      </div>
    </DataPanel>

    <Dialog v-model:visible="showPositionDialog" header="Add position" :modal="true" class="w-full max-w-md">
      <form class="dialog-form" @submit.prevent="createPosition">
        <div>
          <label>Title</label>
          <InputText v-model="newPosition.title" class="w-full" required />
        </div>
        <div class="form-grid">
          <div>
            <label>Max votes allowed</label>
            <InputNumber v-model="newPosition.max_votes_allowed" class="w-full" :min="1" />
          </div>
          <div>
            <label>Display order</label>
            <InputNumber v-model="newPosition.display_order" class="w-full" :min="0" />
          </div>
        </div>
        <label class="toggle-row">
          <div>
            <span class="toggle-title">Active</span>
            <span class="toggle-desc">Position is visible on the ballot</span>
          </div>
          <Checkbox v-model="newPosition.is_active" binary />
        </label>
        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" @click="showPositionDialog = false">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="loadingPosition">
            <i v-if="loadingPosition" class="fas fa-spinner fa-spin"></i>
            Create
          </button>
        </div>
      </form>
    </Dialog>
  </div>

  <div v-else class="admin-page">
    <div class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading election…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { electionApi } from '@/api/elections'
import { resultsApi } from '@/api/results'
import { candidateApi } from '@/api/candidates'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import TabNav from '@/components/admin/TabNav.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import CandidateManager from '@/components/elections/CandidateManager.vue'
import VoterManager from '@/components/elections/VoterManager.vue'
import BarChart from '@/components/charts/BarChart.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const canManageElections = computed(() => authStore.isElectionManager)

const canOpenMonitor = computed(() => {
  const status = election.value?.status
  const canView = authStore.isElectionManager || authStore.isAuditor
  return canView && ['open', 'paused', 'closed'].includes(status)
})

const election = ref(null)
const positions = ref([])
const candidateCount = ref(0)
const loadingPositions = ref(false)
const showPositionDialog = ref(false)
const loadingPosition = ref(false)
const activeTab = ref('positions')
const resultExists = ref(false)
const isGenerating = ref(false)
const monitorData = ref(null)

const chartPosition = computed(() => {
  const positions = monitorData.value?.positions || []
  return positions.find((p) => /president/i.test(p.title)) || positions[0] || null
})

const candidateLabels = computed(() => (chartPosition.value?.candidates || []).map((c) => c.full_name))
const candidateVotes = computed(() => (chartPosition.value?.candidates || []).map((c) => c.votes))
const turnoutTrend = computed(() => monitorData.value?.cumulative_turnout || { labels: [], turnout: [] })
const showElectionCharts = computed(() => (election.value?.votes_cast ?? 0) > 0 && chartPosition.value)

const newPosition = ref({
  title: '',
  max_votes_allowed: 1,
  display_order: 0,
  is_active: true,
})

const voterCount = computed(() => election.value?.eligible_voter_count ?? 0)

const turnoutPct = computed(() => {
  const eligible = election.value?.eligible_voter_count ?? 0
  const unique = election.value?.unique_voters ?? 0
  if (!eligible) return 0
  return Math.round((unique / eligible) * 100)
})

const scheduleHint = computed(() => {
  if (!election.value) return ''
  return `${formatDate(election.value.start_date)} – ${formatDate(election.value.end_date)}`
})

const tabItems = computed(() => [
  {
    key: 'positions',
    label: 'Positions',
    icon: 'fas fa-list',
    count: positions.value.length,
    tone: 'indigo',
  },
  {
    key: 'candidates',
    label: 'Candidates',
    icon: 'fas fa-user-tie',
    count: candidateCount.value,
    tone: 'amber',
  },
  {
    key: 'voters',
    label: 'Voters',
    icon: 'fas fa-user-check',
    count: voterCount.value,
    tone: 'teal',
  },
])

const activePanel = computed(() => {
  const map = {
    positions: { title: 'Positions', subtitle: 'Ballot positions and vote limits' },
    candidates: { title: 'Candidates', subtitle: 'Approved and pending candidates' },
    voters: { title: '', subtitle: '' },
  }
  return map[activeTab.value] || map.positions
})

const fetchMonitorCharts = async () => {
  if (!election.value || !(election.value.votes_cast > 0)) return
  try {
    const { data } = await electionApi.getMonitor(route.params.uuid)
    monitorData.value = data
  } catch (error) {
    console.error('Failed to fetch monitor charts:', error)
  }
}

const fetchElection = async () => {
  try {
    const response = await electionApi.get(route.params.uuid)
    election.value = response.data
    await checkResultExists()
    await fetchMonitorCharts()
  } catch (error) {
    console.error('Failed to fetch election:', error)
    router.push('/elections')
  }
}

const fetchPositions = async () => {
  loadingPositions.value = true
  try {
    const response = await electionApi.getPositions(route.params.uuid)
    positions.value = response.data
  } catch (error) {
    console.error('Failed to fetch positions:', error)
  } finally {
    loadingPositions.value = false
  }
}

const fetchCandidateCount = async () => {
  try {
    const { data } = await candidateApi.list(route.params.uuid)
    candidateCount.value = Array.isArray(data) ? data.length : 0
  } catch (error) {
    console.error('Failed to fetch candidate count:', error)
    candidateCount.value = 0
  }
}

const checkResultExists = async () => {
  try {
    await resultsApi.preview(route.params.uuid)
    resultExists.value = true
  } catch {
    resultExists.value = false
  }
}

const formatDate = (date) => {
  if (!date) return 'TBA'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatType = (type) => (type || 'general').replace(/_/g, ' ')

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

const updateStatus = async (newStatus) => {
  try {
    await electionApi.update(election.value.uuid, { status: newStatus })
    await fetchElection()
  } catch (error) {
    console.error('Failed to update status:', error)
    alert('Failed to update status. Please try again.')
  }
}

const openElection = async () => {
  try {
    await electionApi.open(election.value.uuid)
    await fetchElection()
  } catch (error) {
    console.error('Failed to open election:', error)
    alert('Failed to open election. Please check readiness.')
  }
}

const closeElection = async () => {
  if (!confirm('Are you sure you want to close this election?')) return
  try {
    await electionApi.close(election.value.uuid)
    await fetchElection()
  } catch (error) {
    console.error('Failed to close election:', error)
    alert('Failed to close election. Please try again.')
  }
}

const generateResults = async () => {
  if (!confirm('Generate results for this election?')) return
  isGenerating.value = true
  try {
    await resultsApi.generate(route.params.uuid)
    resultExists.value = true
    router.push(`/results/${route.params.uuid}`)
  } catch (error) {
    console.error('Failed to generate results:', error)
    alert('Failed to generate results. Please try again.')
  } finally {
    isGenerating.value = false
  }
}

const createPosition = async () => {
  loadingPosition.value = true
  try {
    await electionApi.createPosition(route.params.uuid, newPosition.value)
    showPositionDialog.value = false
    newPosition.value = { title: '', max_votes_allowed: 1, display_order: 0, is_active: true }
    await fetchPositions()
  } catch (error) {
    console.error('Failed to create position:', error)
    alert('Failed to create position. Please try again.')
  } finally {
    loadingPosition.value = false
  }
}

onMounted(() => {
  fetchElection()
  fetchPositions()
  fetchCandidateCount()
})
</script>

<style scoped>
.election-detail .btn-back {
  margin-bottom: 0;
}

.action-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.detail-status {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-right: 0.25rem;
}

.live-dot {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 9999px;
  background: currentColor;
}

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.65rem 0.95rem;
  border-radius: 0.65rem;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #fecaca;
  background: #fff;
  color: #be123c;
  transition: all 0.15s ease;
}

.btn-danger:hover:not(:disabled) {
  background: #fff1f2;
  border-color: #fca5a5;
}

.tab-panel-body {
  padding: 1.25rem;
}

:deep(.tab-nav) {
  margin-bottom: 0;
}

:deep(.p-inputtext),
:deep(.p-inputnumber-input) {
  width: 100%;
}

.election-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

@media (min-width: 900px) {
  .election-charts {
    grid-template-columns: 1.2fr 1fr;
  }

  .election-charts > :last-child {
    grid-column: 1 / -1;
  }
}
</style>
