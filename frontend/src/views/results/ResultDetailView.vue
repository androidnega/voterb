<template>
  <div class="p-4 sm:p-6 max-w-7xl mx-auto" v-if="result">
    <div class="flex flex-wrap items-center justify-end gap-2 mb-6">
      <Button label="Back" icon="pi pi-arrow-left" severity="secondary" size="small" @click="$router.push('/results')" />
      <Button
        v-if="result.status === 'generated' && canCertify"
        label="Certify"
        icon="pi pi-check"
        severity="success"
        size="small"
        @click="openCeremony"
      />
      <Button v-if="result.status === 'certified' && canManageResults" label="Publish" icon="pi pi-globe" severity="info" size="small" @click="publish" />
    </div>

    <!-- Status -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-6">
      <div class="flex flex-wrap items-center gap-4">
        <span class="text-sm font-medium text-gray-700">Status:</span>
        <Badge :value="result.status" :severity="getStatusSeverity(result.status)" class="capitalize" />
        <span class="text-sm text-gray-500">| Turnout: {{ result.turnout_percentage || 0 }}%</span>
        <span v-if="result.certified_at" class="text-sm text-gray-500">| Certified: {{ formatDate(result.certified_at) }}</span>
        <span v-if="result.published_at" class="text-sm text-gray-500">| Published: {{ formatDate(result.published_at) }}</span>
      </div>
    </div>

    <section v-if="featuredPosition" class="mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Results analytics</h2>
            <p class="text-sm text-gray-500">{{ featuredPosition.title }} — vote breakdown and turnout</p>
          </div>
          <select
            v-if="standings.length > 1"
            v-model="selectedPositionUuid"
            class="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700"
          >
            <option v-for="pos in standings" :key="pos.uuid" :value="pos.uuid">{{ pos.title }}</option>
          </select>
        </div>
        <div class="results-charts">
          <div class="results-chart-card">
            <h3 class="text-sm font-medium text-gray-700 mb-2">Candidate comparison</h3>
            <HorizontalBarChart
              :labels="chartLabels"
              :data="chartVotes"
              aria-label="Candidate comparison horizontal bar chart"
            />
          </div>
          <div class="results-chart-card">
            <h3 class="text-sm font-medium text-gray-700 mb-2">Vote share</h3>
            <DonutChart
              :labels="chartLabels"
              :data="chartVotes"
              aria-label="Vote share donut chart"
            />
          </div>
          <div class="results-chart-card results-chart-card--wide">
            <h3 class="text-sm font-medium text-gray-700 mb-2">Turnout trend</h3>
            <AreaChart
              :labels="turnoutTrend.labels"
              :data="turnoutTrend.turnout"
              label="Turnout %"
              aria-label="Turnout trend area chart"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Positions Results -->
    <div class="space-y-6">
      <div v-for="pos in standings" :key="pos.uuid" class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">{{ pos.title }}</h2>
          <p class="text-xs text-gray-500">Max Votes: {{ pos.max_votes_allowed }}</p>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="(candidate, idx) in pos.candidates" :key="candidate.uuid" class="px-6 py-4 flex items-center justify-between hover:bg-emerald-50/30 transition-colors">
            <div class="flex items-center gap-4">
              <span class="text-sm font-medium text-gray-400 w-6">{{ candidate.rank }}</span>
              <div>
                <span class="font-medium text-gray-900">{{ candidate.full_name }}</span>
              </div>
            </div>
            <div class="flex items-center gap-6">
              <span class="text-sm text-gray-600">{{ candidate.votes }} votes</span>
              <span class="text-sm font-semibold text-emerald-600 w-16 text-right">{{ candidate.percentage }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Integrity Report -->
    <div class="mt-6 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Integrity Report</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        <div class="flex items-center gap-2">
          <i class="pi pi-check-circle text-emerald-500"></i>
          <span>Vote hashes verified</span>
        </div>
        <div class="flex items-center gap-2">
          <i class="pi pi-check-circle text-emerald-500"></i>
          <span>SVT consistency</span>
        </div>
        <div class="flex items-center gap-2">
          <i class="pi pi-check-circle text-emerald-500"></i>
          <span>No duplicate votes</span>
        </div>
        <div class="flex items-center gap-2">
          <i class="pi pi-users text-blue-500"></i>
          <span>Eligible: {{ integrity.eligible_voters }}</span>
        </div>
        <div class="flex items-center gap-2">
          <i class="pi pi-flag text-blue-500"></i>
          <span>Votes cast: {{ integrity.votes_cast }}</span>
        </div>
        <div class="flex items-center gap-2">
          <i class="pi pi-percentage text-blue-500"></i>
          <span>Turnout: {{ integrity.turnout_percentage }}%</span>
        </div>
      </div>
      <div class="mt-3 text-xs text-gray-400">
        Hash: {{ result.result_hash?.slice(0, 16) }}...
      </div>
    </div>

    <!-- Certification evidence -->
    <div
      v-if="evidence && (result.status === 'certified' || result.status === 'published')"
      class="mt-6 bg-white rounded-xl border border-gray-200 p-6 shadow-sm"
    >
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Certification evidence</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div>
          <p class="text-xs text-gray-500 mb-1">Certifier photo</p>
          <img
            v-if="evidence.photo"
            :src="evidence.photo"
            alt="Certifier"
            class="rounded-lg border border-gray-200 max-h-48 object-cover"
          />
          <p v-else class="text-gray-400">—</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1">Signature</p>
          <img
            v-if="evidence.signature"
            :src="evidence.signature"
            alt="Signature"
            class="rounded-lg border border-gray-200 bg-white max-h-32"
          />
          <p v-else class="text-gray-400">—</p>
        </div>
        <div class="space-y-1">
          <p><span class="text-gray-500">Location:</span>
            <span v-if="evidence.location">
              {{ evidence.location.lat }}, {{ evidence.location.lng }}
              <span class="text-xs text-gray-400">({{ evidence.location.source || 'gps' }})</span>
            </span>
            <span v-else>—</span>
          </p>
          <p><span class="text-gray-500">IP address:</span> {{ evidence.ip_address || '—' }}</p>
          <p class="break-all"><span class="text-gray-500">Device fingerprint:</span> {{ evidence.device_fingerprint || '—' }}</p>
          <p><span class="text-gray-500">Certified by:</span> {{ certifiedByLabel }}</p>
          <p><span class="text-gray-500">Certified at:</span> {{ formatDate(evidence.certified_at || result.certified_at) }}</p>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="p-6 text-center text-gray-500">
    <i class="pi pi-spin pi-spinner text-2xl"></i>
    <p class="mt-2">Loading results...</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { resultsApi } from '@/api/results'
import { electionApi } from '@/api/elections'
import { usePageHeading } from '@/composables/usePageHeading'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import HorizontalBarChart from '@/components/charts/HorizontalBarChart.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { setPageHeading } = usePageHeading()
const result = ref(null)

watch(
  result,
  (value) => {
    if (!value?.election) return
    setPageHeading({
      title: value.election.title,
      subtitle: 'Results for this election.',
    })
  },
  { immediate: true },
)
const loading = ref(true)
const monitorData = ref(null)
const selectedPositionUuid = ref(null)
const canManageResults = computed(() => authStore.isElectionManager)
const canCertify = computed(() => authStore.isElectionManager)
const evidence = computed(() => {
  const raw = result.value?.certification_evidence
  return raw && typeof raw === 'object' && Object.keys(raw).length ? raw : null
})

const certifiedByLabel = computed(() => {
  const r = result.value
  if (!r) return '—'
  return (
    r.certified_by_email
    || r.certified_by?.email
    || r.certified_by_name
    || r.certified_by?.display_name
    || evidence.value?.certified_by
    || '—'
  )
})

const standings = computed(() => {
  if (!result.value?.standings) return []
  return result.value.standings.positions || []
})

const featuredPosition = computed(() => {
  if (!standings.value.length) return null
  if (selectedPositionUuid.value) {
    return standings.value.find((p) => p.uuid === selectedPositionUuid.value) || standings.value[0]
  }
  return standings.value.find((p) => /president/i.test(p.title)) || standings.value[0]
})

const chartLabels = computed(() => (featuredPosition.value?.candidates || []).map((c) => c.full_name))
const chartVotes = computed(() => (featuredPosition.value?.candidates || []).map((c) => c.votes))
const turnoutTrend = computed(() => monitorData.value?.cumulative_turnout || { labels: [], turnout: [] })

const integrity = computed(() => {
  return result.value?.integrity_report || {}
})

const fetchMonitorTrend = async (electionUuid) => {
  if (!electionUuid) return
  try {
    const { data } = await electionApi.getMonitor(electionUuid)
    monitorData.value = data
  } catch (error) {
    console.error('Failed to fetch turnout trend:', error)
  }
}

const fetchResult = async () => {
  loading.value = true
  try {
    const response = await resultsApi.preview(route.params.uuid)
    result.value = response.data
    const positions = response.data?.standings?.positions || []
    const defaultPos = positions.find((p) => /president/i.test(p.title)) || positions[0]
    selectedPositionUuid.value = defaultPos?.uuid || null
    await fetchMonitorTrend(response.data?.election?.uuid)
  } catch (error) {
    console.error('Failed to fetch result:', error)
    router.push('/results')
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusSeverity = (status) => {
  const map = {
    generated: 'warning',
    pending_certification: 'warning',
    certified: 'info',
    published: 'success',
    archived: 'danger'
  }
  return map[status] || 'secondary'
}

const openCeremony = () => {
  router.push(`/results/${route.params.uuid}/certify`)
}

const publish = async () => {
  if (confirm('Publish these results to students?')) {
    try {
      await resultsApi.publish(route.params.uuid)
      await fetchResult()
    } catch (error) {
      console.error('Failed to publish:', error)
      alert('Failed to publish. Please try again.')
    }
  }
}

onMounted(() => {
  fetchResult()
})
</script>

<style scoped>
.results-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}

@media (min-width: 900px) {
  .results-charts {
    grid-template-columns: 1.2fr 1fr;
  }

  .results-chart-card--wide {
    grid-column: 1 / -1;
  }
}

.results-chart-card {
  min-height: 14rem;
}
</style>
