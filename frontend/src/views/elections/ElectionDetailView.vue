<template>
  <div v-if="election" class="admin-page election-detail">
    <button type="button" class="btn-back page-section" @click="router.push('/elections')">
      <i class="fas fa-arrow-left"></i>
      Back to elections
    </button>

    <PageHeader :show-refresh="false">
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
            v-if="canManageElections && ['draft', 'scheduled'].includes(election.status)"
            type="button"
            class="btn btn-primary"
            @click="openElection"
          >
            <i class="fas fa-play"></i>
            Start election
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

    <div v-if="!canManageElections && election" class="access-notice page-section">
      <i class="fas fa-eye"></i>
      <span v-if="election.owner_type === 'sub' && authStore.isMainEC">
        View-only — this is a Sub EC election. Main EC can monitor it but cannot make changes.
      </span>
      <span v-else>
        View-only — election management is handled by the owning Electoral Commission.
      </span>
    </div>

    <ElectionCountdown
      v-if="['open', 'paused'].includes(election.status) && election.end_date"
      :election="election"
      label="Voting ends in"
      :beep="false"
      class="page-section election-end-countdown"
    />

    <section
      v-if="canManageElections && election.status === 'draft'"
      class="roadmap page-section"
      aria-label="Election setup roadmap"
    >
      <header class="roadmap__head">
        <p class="roadmap__eyebrow">Setup roadmap</p>
        <h2 class="roadmap__title">Get this election ready</h2>
      </header>

      <ol class="roadmap__track">
        <li
          class="roadmap__step"
          :class="roadmapStepClass(0)"
        >
          <span class="roadmap__marker" aria-hidden="true">
            <i v-if="positions.length" class="fas fa-check"></i>
            <span v-else>1</span>
          </span>
          <div class="roadmap__copy">
            <strong>Positions</strong>
            <p>Define offices on the ballot</p>
          </div>
        </li>
        <li
          class="roadmap__step"
          :class="roadmapStepClass(1)"
        >
          <span class="roadmap__marker" aria-hidden="true">
            <i v-if="candidateCount > 0" class="fas fa-check"></i>
            <span v-else>2</span>
          </span>
          <div class="roadmap__copy">
            <strong>Candidates</strong>
            <p>Add and approve nominees</p>
          </div>
        </li>
        <li
          class="roadmap__step"
          :class="roadmapStepClass(2)"
        >
          <span class="roadmap__marker" aria-hidden="true">
            <i v-if="election.register" class="fas fa-check"></i>
            <span v-else>3</span>
          </span>
          <div class="roadmap__copy">
            <strong>Voters</strong>
            <p>Link an approved register</p>
          </div>
        </li>
        <li
          class="roadmap__step"
          :class="roadmapStepClass(3)"
        >
          <span class="roadmap__marker" aria-hidden="true">4</span>
          <div class="roadmap__copy">
            <strong>Launch</strong>
            <p>Open voting when ready</p>
          </div>
        </li>
      </ol>
    </section>

    <section
      v-if="canManageElections && ['draft', 'scheduled'].includes(election.status)"
      class="launch-card page-section"
    >
      <div class="launch-card__copy">
        <p class="launch-card__eyebrow">Ready to go live</p>
        <h3>Start this election</h3>
        <p>
          When positions, candidates, and voters are ready, confirm to open voting for eligible students on this election’s register.
        </p>
      </div>
      <div class="launch-card__actions">
        <button
          type="button"
          class="btn btn-primary"
          @click="openElection"
        >
          <i class="fas fa-play"></i>
          Start election
        </button>
      </div>
    </section>

    <section v-if="election.register" class="page-section register-summary">
      <button type="button" class="register-summary-card" @click="openVotersRegister">
        <span class="register-summary-card__icon" aria-hidden="true">
          <i class="fas fa-address-book"></i>
        </span>
        <span class="register-summary-card__body">
          <span class="register-summary-card__label">Voter Register</span>
          <span class="register-summary-card__name">{{ election.register.name }}</span>
          <span class="register-summary-card__meta">
            {{ formatCount(election.register.category_count) }} categories
            ·
            {{ formatCount(election.register.entry_count) }} voters
          </span>
        </span>
        <span class="register-summary-card__action">
          Open Voters
          <i class="fas fa-arrow-right" aria-hidden="true"></i>
        </span>
      </button>
    </section>

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

    <TabNav v-model="activeTab" :tabs="tabItems" />

    <DataPanel
      :title="activePanel.title"
      :subtitle="activePanel.subtitle"
      :no-padding="activeTab !== 'positions'"
      class="election-section-panel"
    >
      <template v-if="canEditElection && activeTab === 'positions'" #header>
        <button type="button" class="btn btn-primary" @click="openPositionDialog">
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
                <th>Votes</th>
                <th>Order</th>
                <th>Who can vote</th>
                <th>On ballot</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="position in positions" :key="position.uuid">
                <td><span class="cell-title">{{ position.title }}</span></td>
                <td class="mono">{{ position.max_votes_allowed }}</td>
                <td class="mono">{{ position.display_order }}</td>
                <td>
                  <span v-if="position.allow_all_voters !== false" class="scope-pill scope-pill--all">
                    All voters
                  </span>
                  <span v-else class="scope-pill-wrap">
                    <span
                      v-for="cat in (position.restricted_categories || [])"
                      :key="cat.uuid"
                      class="scope-pill"
                    >
                      {{ cat.name }}
                    </span>
                    <span
                      v-if="!(position.restricted_categories || []).length"
                      class="scope-pill scope-pill--warn"
                    >
                      Restricted
                    </span>
                  </span>
                </td>
                <td>
                  <span class="admin-badge" :class="position.is_active ? 'success' : 'neutral'">
                    {{ position.is_active ? 'Yes' : 'No' }}
                  </span>
                </td>
              </tr>
              <tr v-if="positions.length === 0">
                <td colspan="5">
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
          :election-status="election.status"
          :readonly="!canEditElection"
          @updated="candidateCount = $event"
        />
      </div>

      <!-- Voters -->
      <div v-else-if="activeTab === 'voters'" class="tab-panel-body">
        <VoterManager
          :election-uuid="route.params.uuid"
          :readonly="!canEditElection || isSubEC"
          :initial-register-uuid="registerDeepLink"
          :open-create-register="openCreateRegister"
          @deep-link-consumed="clearRegisterDeepLink"
        />
      </div>
    </DataPanel>

    <Dialog
      v-model:visible="showPositionDialog"
      header="Add position"
      :modal="true"
      class="w-full max-w-md position-dialog"
    >
      <form class="dialog-form position-form" @submit.prevent="createPosition">
        <div class="field">
          <label for="position-title">Title <span class="req">*</span></label>
          <InputText
            id="position-title"
            v-model="newPosition.title"
            class="w-full"
            required
            autofocus
            placeholder="e.g. President"
          />
        </div>

        <div class="form-grid">
          <div class="field">
            <label for="position-votes">Votes allowed</label>
            <InputNumber
              id="position-votes"
              v-model="newPosition.max_votes_allowed"
              class="w-full"
              :min="1"
              :showButtons="false"
            />
            <p class="field-hint">How many candidates a voter can pick</p>
          </div>
          <div class="field">
            <label for="position-order">Ballot order</label>
            <InputNumber
              id="position-order"
              v-model="newPosition.display_order"
              class="w-full"
              :min="0"
              :showButtons="false"
            />
            <p class="field-hint">Lower numbers appear first</p>
          </div>
        </div>

        <div class="field">
          <div class="field-head">
            <label>Options</label>
          </div>
          <div class="option-stack" role="group" aria-label="Position options">
            <button
              type="button"
              class="option-card"
              :class="{ 'is-selected': newPosition.is_active }"
              :aria-pressed="newPosition.is_active"
              @click="newPosition.is_active = !newPosition.is_active"
            >
              <span class="option-card__copy">
                <strong>Show on ballot</strong>
                <small>Include this position when voting opens</small>
              </span>
              <span class="option-card__switch" aria-hidden="true">
                <span class="option-card__knob"></span>
              </span>
            </button>

            <button
              type="button"
              class="option-card"
              :class="{ 'is-selected': newPosition.allow_all_voters }"
              :aria-pressed="newPosition.allow_all_voters"
              @click="newPosition.allow_all_voters = !newPosition.allow_all_voters"
            >
              <span class="option-card__copy">
                <strong>All voters</strong>
                <small>Everyone on the register can vote here</small>
              </span>
              <span class="option-card__switch" aria-hidden="true">
                <span class="option-card__knob"></span>
              </span>
            </button>
          </div>
        </div>

        <div v-if="!newPosition.allow_all_voters" class="restriction-panel">
          <label for="position-categories">Limit to categories</label>
          <MultiSelect
            id="position-categories"
            v-model="newPosition.restricted_category_uuids"
            :options="categoryOptions"
            optionLabel="label"
            optionValue="uuid"
            placeholder="Select categories"
            display="chip"
            class="w-full"
            :filter="true"
          />
          <p v-if="!categoryOptions.length" class="field-hint field-hint--warn">
            Add a register with categories under Voters first.
          </p>
          <p v-else class="field-hint">Only selected categories can vote for this position.</p>
        </div>

        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" @click="showPositionDialog = false">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="loadingPosition">
            <i v-if="loadingPosition" class="fas fa-spinner fa-spin"></i>
            {{ loadingPosition ? 'Creating…' : 'Create position' }}
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

  <GovernanceSubmittedModal
    v-model:visible="showGovernanceModal"
    :message="governanceMessage"
  />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { electionApi } from '@/api/elections'
import { resultsApi } from '@/api/results'
import { candidateApi } from '@/api/candidates'
import { usePageHeading } from '@/composables/usePageHeading'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import MultiSelect from 'primevue/multiselect'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import TabNav from '@/components/admin/TabNav.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import GovernanceSubmittedModal from '@/components/admin/GovernanceSubmittedModal.vue'
import CandidateManager from '@/components/elections/CandidateManager.vue'
import VoterManager from '@/components/elections/VoterManager.vue'
import ElectionCountdown from '@/components/student/ElectionCountdown.vue'
import { registerApi } from '@/api/registers'
import BarChart from '@/components/charts/BarChart.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { setPageHeading } = usePageHeading()
const canManageElections = computed(() => !!election.value?.can_manage)
const canEditElection = computed(
  () => canManageElections.value && ['draft', 'scheduled'].includes(election.value?.status),
)
const canCreateElections = computed(() => authStore.isElectionManager)
const isSubEC = computed(() => authStore.isSubEC && !authStore.isMainEC)

const canOpenMonitor = computed(() => {
  const status = election.value?.status
  const canView = authStore.isElectionManager || authStore.isAuditor || authStore.isMainEC
  return canView && ['open', 'paused', 'closed'].includes(status)
})

const election = ref(null)

watch(
  election,
  (value) => {
    if (!value) return
    setPageHeading({
      title: value.title,
      subtitle: value.description || 'No description provided.',
    })
  },
  { immediate: true },
)

const positions = ref([])
const candidateCount = ref(0)

const roadmapDone = computed(() => ([
  positions.value.length > 0,
  candidateCount.value > 0,
  !!election.value?.register,
  false,
]))

const roadmapActiveIndex = computed(() => {
  const idx = roadmapDone.value.findIndex((done) => !done)
  return idx === -1 ? roadmapDone.value.length - 1 : idx
})

function roadmapStepClass(index) {
  if (roadmapDone.value[index]) return 'is-done'
  if (index === roadmapActiveIndex.value) return 'is-active'
  return 'is-upcoming'
}

const loadingPositions = ref(false)
const showPositionDialog = ref(false)
const loadingPosition = ref(false)
const activeTab = ref('positions')
const resultExists = ref(false)
const isGenerating = ref(false)
const monitorData = ref(null)
const registerDeepLink = ref('')
const openCreateRegister = ref(false)
const showGovernanceModal = ref(false)
const governanceMessage = ref('')

const applyVotersQuery = () => {
  const tab = typeof route.query.tab === 'string' ? route.query.tab : ''
  if (['positions', 'candidates', 'voters'].includes(tab)) {
    activeTab.value = tab
  }
  const voters = route.query.voters
  const register = typeof route.query.register === 'string' ? route.query.register : ''
  const create = route.query.create === '1' || route.query.create === 'true'
  if (voters === 'register' || voters === '1' || register || create) {
    activeTab.value = 'voters'
  }
  registerDeepLink.value = register
  openCreateRegister.value = create
}

const clearRegisterDeepLink = () => {
  registerDeepLink.value = ''
  openCreateRegister.value = false
  if (route.query.voters || route.query.register || route.query.create) {
    const query = { ...route.query }
    delete query.voters
    delete query.register
    delete query.create
    router.replace({ path: route.path, query })
  }
}

const openVotersRegister = () => {
  const registerUuid = election.value?.register?.uuid
  if (!registerUuid) {
    activeTab.value = 'voters'
    return
  }
  router.push({
    path: `/elections/${election.value.uuid}`,
    query: { voters: 'register', register: registerUuid },
  })
}

const formatCount = (value) => {
  const n = Number(value || 0)
  return Number.isFinite(n) ? n.toLocaleString() : '0'
}

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
  allow_all_voters: true,
  restricted_category_uuids: [],
})

const categoryOptions = ref([])

const resetPositionForm = () => {
  newPosition.value = {
    title: '',
    max_votes_allowed: 1,
    display_order: 0,
    is_active: true,
    allow_all_voters: true,
    restricted_category_uuids: [],
  }
}

const loadCategoryOptions = async () => {
  try {
    const { data } = await registerApi.list(route.params.uuid)
    const registers = Array.isArray(data) ? data : (data.results || [])
    const options = []
    for (const reg of registers) {
      for (const cat of reg.categories || []) {
        options.push({
          uuid: cat.uuid,
          label: `${reg.name} · ${cat.name}`,
        })
      }
    }
    categoryOptions.value = options
  } catch (error) {
    console.error('Failed to load categories:', error)
    categoryOptions.value = []
  }
}

const openPositionDialog = async () => {
  resetPositionForm()
  newPosition.value.display_order = positions.value.length
  await loadCategoryOptions()
  showPositionDialog.value = true
}

const voterCount = computed(() => election.value?.eligible_voter_count ?? 0)

const tabItems = computed(() => {
  const tabs = [
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
  ]
  return tabs
})

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
    const { data } = await resultsApi.preview(route.params.uuid)
    resultExists.value = data?.exists !== false && !!data?.uuid
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

const handleGovernanceResponse = (response, fallbackMessage) => {
  const data = response?.data
  const status = response?.status
  if (status === 202 || data?.status === 'pending') {
    governanceMessage.value =
      data?.message
      || fallbackMessage
      || 'Submitted for approval. Your approval is recorded; the other institutional EC member must also approve before enrollment.'
    showGovernanceModal.value = true
    return true
  }
  return false
}

const openElection = async () => {
  if (!confirm('Start this election now? Eligible voters will be able to cast ballots.')) return
  try {
    const response = await electionApi.open(election.value.uuid)
    if (handleGovernanceResponse(response)) return
    await fetchElection()
  } catch (error) {
    console.error('Failed to open election:', error)
    const data = error.response?.data
    alert(
      data?.error ||
      data?.detail ||
      data?.title?.[0] ||
      'Failed to open election. Please check readiness.',
    )
  }
}

const closeElection = async () => {
  if (!confirm('Are you sure you want to close this election?')) return
  try {
    const response = await electionApi.close(election.value.uuid)
    if (handleGovernanceResponse(response)) return
    await fetchElection()
  } catch (error) {
    console.error('Failed to close election:', error)
    alert(error.response?.data?.detail || 'Failed to close election. Please try again.')
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
    const data = error.response?.data
    alert(
      data?.error ||
      data?.detail ||
      'Failed to generate results. Please try again.',
    )
  } finally {
    isGenerating.value = false
  }
}

const createPosition = async () => {
  if (!newPosition.value.allow_all_voters && !(newPosition.value.restricted_category_uuids || []).length) {
    alert('Select at least one category, or turn on “All voters”.')
    return
  }
  loadingPosition.value = true
  try {
    const payload = {
      title: newPosition.value.title,
      max_votes_allowed: newPosition.value.max_votes_allowed,
      display_order: newPosition.value.display_order,
      is_active: newPosition.value.is_active,
      allow_all_voters: newPosition.value.allow_all_voters,
      restricted_category_uuids: newPosition.value.allow_all_voters
        ? []
        : newPosition.value.restricted_category_uuids,
    }
    await electionApi.createPosition(route.params.uuid, payload)
    showPositionDialog.value = false
    resetPositionForm()
    await fetchPositions()
  } catch (error) {
    console.error('Failed to create position:', error)
    const data = error.response?.data
    const detail =
      data?.restricted_category_uuids?.[0] ||
      data?.title?.[0] ||
      data?.detail ||
      data?.error ||
      (typeof data === 'string' ? data : null) ||
      'Failed to create position. Please try again.'
    alert(detail)
  } finally {
    loadingPosition.value = false
  }
}

onMounted(() => {
  applyVotersQuery()
  fetchElection()
  fetchPositions()
  fetchCandidateCount()
})

watch(
  () => [route.query.voters, route.query.register, route.query.create],
  () => applyVotersQuery(),
)
</script>

<style scoped>
.roadmap {
  display: grid;
  gap: 1rem;
  padding: 1.15rem 1.2rem 1.25rem;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 1.15rem;
}

.roadmap__head {
  display: grid;
  gap: 0.2rem;
}

.roadmap__eyebrow {
  margin: 0;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.roadmap__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 750;
  letter-spacing: -0.025em;
  color: var(--vb-ink, #1c1c1c);
}

.roadmap__track {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  position: relative;
}

.roadmap__track::before {
  content: '';
  position: absolute;
  top: 1.05rem;
  left: 7%;
  right: 7%;
  height: 1px;
  background: #ebe8e2;
  z-index: 0;
}

.roadmap__step {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  gap: 0.65rem;
  text-align: center;
  padding: 0 0.35rem;
}

.roadmap__marker {
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  font-size: 0.72rem;
  font-weight: 750;
  background: #fff;
  border: 1.5px solid #e7e5e4;
  color: #a8a29e;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.roadmap__copy {
  display: grid;
  gap: 0.15rem;
  min-width: 0;
}

.roadmap__copy strong {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: -0.015em;
  color: #78716c;
}

.roadmap__copy p {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.35;
  color: #a8a29e;
}

.roadmap__step.is-done .roadmap__marker {
  background: #0f766e;
  border-color: #0f766e;
  color: #fff;
}

.roadmap__step.is-done .roadmap__copy strong {
  color: #134e4a;
}

.roadmap__step.is-active .roadmap__marker {
  background: #1c1917;
  border-color: #1c1917;
  color: #fff;
  box-shadow: 0 0 0 4px rgba(28, 25, 23, 0.08);
}

.roadmap__step.is-active .roadmap__copy strong {
  color: #1c1917;
}

.roadmap__step.is-active .roadmap__copy p {
  color: #78716c;
}

.launch-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.15rem 1.25rem;
  border-radius: 1.15rem;
  background: #fff;
  border: 1px solid #ebeae4;
}

.launch-card__copy {
  min-width: min(100%, 18rem);
  flex: 1;
}

.launch-card__eyebrow {
  margin: 0 0 0.25rem;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.launch-card__copy h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: var(--vb-ink, #1c1c1c);
}

.launch-card__copy p {
  margin: 0.3rem 0 0;
  font-size: 0.84rem;
  line-height: 1.45;
  color: var(--vb-muted, #8a8a8a);
  max-width: 36rem;
}

.launch-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

@media (max-width: 800px) {
  .roadmap__track {
    grid-template-columns: 1fr;
    gap: 0.55rem;
  }

  .roadmap__track::before {
    display: none;
  }

  .roadmap__step {
    grid-template-columns: auto 1fr;
    justify-items: start;
    text-align: left;
    align-items: center;
    gap: 0.75rem;
    padding: 0.7rem 0.8rem;
    border: 1px solid #ebe8e2;
    border-radius: 0.85rem;
    background: #fafaf8;
  }

  .roadmap__step.is-active {
    background: #fff;
    border-color: #d6d3d1;
  }

  .roadmap__step.is-done {
    background: #f0fdf9;
    border-color: #d1fae5;
  }
}
.election-detail .btn-back {
  margin-bottom: 0;
}

.register-summary {
  margin-bottom: 0.25rem;
}

.register-summary-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.9rem;
  align-items: center;
  width: 100%;
  text-align: left;
  padding: 1rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: var(--vb-surface, #fff);
  color: var(--vb-ink, #1c1c1c);
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    transform 0.16s ease;
}

.register-summary-card:hover {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 8px 22px rgba(61, 79, 68, 0.1);
  transform: translateY(-1px);
}

.register-summary-card__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--vb-panel, #f7f6f2);
  color: var(--vb-accent, #3d4f44);
}

.register-summary-card__body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.register-summary-card__label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--vb-muted, #8a8a8a);
}

.register-summary-card__name {
  font-size: 1rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: var(--vb-accent, #3d4f44);
  text-decoration: underline;
  text-underline-offset: 0.18em;
  text-decoration-color: var(--vb-accent-border, #c5d4bc);
}

.register-summary-card__meta {
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
  font-variant-numeric: tabular-nums;
}

.register-summary-card__action {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vb-muted, #8a8a8a);
  white-space: nowrap;
}

.register-summary-card:hover .register-summary-card__action {
  color: var(--vb-accent, #3d4f44);
}

@media (max-width: 560px) {
  .register-summary-card {
    grid-template-columns: auto 1fr;
  }

  .register-summary-card__action {
    grid-column: 2;
  }
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
  padding: 1.15rem 1.25rem 1.35rem;
}

:deep(.section-switch) {
  margin-bottom: 1rem;
}

.election-section-panel {
  margin-top: 0;
}

:deep(.p-inputtext),
:deep(.p-inputnumber-input),
:deep(.p-multiselect) {
  width: 100%;
}

.position-form {
  gap: 0.9rem;
}

.position-form .form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem;
}

@media (max-width: 520px) {
  .position-form .form-grid {
    grid-template-columns: 1fr;
  }
}

.position-form .field label {
  display: block;
  margin-bottom: 0.3rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}

.position-form .field-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.45rem;
}

.position-form .field-head label {
  margin-bottom: 0;
}

.position-form .req {
  color: #b45309;
}

.position-form .field-hint {
  margin: 0.35rem 0 0;
  font-size: 0.7rem;
  line-height: 1.35;
  color: var(--vb-muted, #8a8a8a);
}

.position-form .field-hint--warn {
  color: #b45309;
}

.option-stack {
  display: grid;
  gap: 0.45rem;
}

.option-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  text-align: left;
  padding: 0.7rem 0.8rem;
  border-radius: 0.85rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.option-card:hover {
  border-color: var(--vb-accent-border, #c5d4bc);
  background: #fcfcfb;
}

.option-card.is-selected {
  border-color: var(--vb-accent-border, #c5d4bc);
  background: var(--vb-accent-soft, #e8efe6);
  box-shadow: inset 0 0 0 1px var(--vb-accent-border, #c5d4bc);
}

.option-card__copy {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.option-card__copy strong {
  font-size: 0.82rem;
  font-weight: 750;
  color: var(--vb-ink, #1c1c1c);
}

.option-card__copy small {
  font-size: 0.7rem;
  line-height: 1.3;
  color: var(--vb-muted, #8a8a8a);
}

.option-card__switch {
  width: 2rem;
  height: 1.15rem;
  border-radius: 999px;
  background: #e7e5e4;
  padding: 0.12rem;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  transition: background 0.15s ease;
}

.option-card.is-selected .option-card__switch {
  background: var(--vb-accent, #3d4f44);
}

.option-card__knob {
  width: 0.9rem;
  height: 0.9rem;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.15);
  transition: transform 0.15s ease;
}

.option-card.is-selected .option-card__knob {
  transform: translateX(0.85rem);
}

.restriction-panel {
  padding: 0.85rem 0.95rem;
  border-radius: 0.9rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
}

.restriction-panel label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}

.position-dialog :deep(.p-inputtext),
.position-dialog :deep(.p-inputnumber-input),
.position-dialog :deep(.p-multiselect) {
  border-radius: 0.75rem;
  border-color: var(--vb-line, #ebeae4);
}

.position-dialog :deep(.p-inputtext:enabled:focus),
.position-dialog :deep(.p-inputnumber-input:enabled:focus),
.position-dialog :deep(.p-multiselect:not(.p-disabled).p-focus) {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.14));
}

.scope-pill-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.scope-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  background: var(--vb-accent-soft, #e8efe6);
  color: var(--vb-accent, #3d4f44);
  font-size: 0.7rem;
  font-weight: 700;
}

.scope-pill--all {
  background: #f1f5f9;
  color: #475569;
}

.scope-pill--warn {
  background: #fff7ed;
  color: #c2410c;
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
