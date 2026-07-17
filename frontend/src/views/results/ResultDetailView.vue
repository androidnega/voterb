<template>
  <div class="admin-page result-detail" v-if="result">
    <header class="result-hero">
      <button type="button" class="result-back" @click="$router.push('/results')">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        Results
      </button>

      <div class="result-hero__row">
        <div class="result-hero__copy">
          <p class="result-eyebrow">Election results</p>
          <h1 class="result-title">{{ result.election?.title || 'Results' }}</h1>
          <div class="result-meta">
            <span class="result-status" :data-status="result.status">{{ statusLabel(result.status) }}</span>
            <span>Turnout {{ result.turnout_percentage || 0 }}%</span>
            <span v-if="result.certified_at">Certified {{ formatDate(result.certified_at) }}</span>
            <span v-if="result.published_at">Published {{ formatDate(result.published_at) }}</span>
          </div>
        </div>

        <div class="result-hero__actions">
          <button
            v-if="result.status === 'generated' && canCertify"
            type="button"
            class="btn btn-primary"
            @click="openCeremony"
          >
            <i class="fas fa-stamp"></i>
            Certify
          </button>
          <button
            v-if="result.status === 'certified' && canManageResults"
            type="button"
            class="btn btn-primary"
            @click="publish"
          >
            <i class="fas fa-globe"></i>
            Publish
          </button>
        </div>
      </div>
    </header>

    <section
      v-if="evidence && (result.status === 'certified' || result.status === 'published')"
      class="cert-seal"
    >
      <div class="cert-seal__head">
        <span class="cert-seal__icon" aria-hidden="true">
          <i class="fas fa-shield-alt"></i>
        </span>
        <div>
          <p class="cert-seal__eyebrow">Official certification</p>
          <h2 class="cert-seal__title">Certified by {{ certifiedByLabel }}</h2>
          <p class="cert-seal__sub">{{ formatDate(evidence.certified_at || result.certified_at) }}</p>
        </div>
      </div>

      <div class="cert-seal__grid">
        <figure class="cert-media">
          <figcaption>Photo</figcaption>
          <img v-if="evidence.photo" :src="evidence.photo" alt="Certifier" />
          <span v-else class="cert-empty">—</span>
        </figure>
        <figure class="cert-media">
          <figcaption>Signature</figcaption>
          <img v-if="evidence.signature" :src="evidence.signature" alt="Signature" class="is-sig" />
          <span v-else class="cert-empty">—</span>
        </figure>
        <div class="cert-facts">
          <div>
            <span>Location</span>
            <strong v-if="evidence.location">
              {{ evidence.location.lat }}, {{ evidence.location.lng }}
              <em>({{ evidence.location.source || 'gps' }})</em>
            </strong>
            <strong v-else>—</strong>
          </div>
          <div>
            <span>IP address</span>
            <strong>{{ evidence.ip_address || '—' }}</strong>
          </div>
          <div>
            <span>Device fingerprint</span>
            <strong class="mono">{{ evidence.device_fingerprint || '—' }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section v-if="featuredPosition" class="result-panel">
      <div class="result-panel__head">
        <div>
          <h2>Analytics</h2>
          <p>{{ featuredPosition.title }} — vote breakdown and turnout</p>
        </div>
        <select
          v-if="standings.length > 1"
          v-model="selectedPositionUuid"
          class="result-select"
        >
          <option v-for="pos in standings" :key="pos.uuid" :value="pos.uuid">{{ pos.title }}</option>
        </select>
      </div>
      <div class="results-charts">
        <div class="results-chart-card">
          <h3>Candidate comparison</h3>
          <HorizontalBarChart
            :labels="chartLabels"
            :data="chartVotes"
            aria-label="Candidate comparison horizontal bar chart"
          />
        </div>
        <div class="results-chart-card">
          <h3>Vote share</h3>
          <DonutChart
            :labels="chartLabels"
            :data="chartVotes"
            aria-label="Vote share donut chart"
          />
        </div>
        <div class="results-chart-card results-chart-card--wide">
          <h3>Turnout trend</h3>
          <AreaChart
            :labels="turnoutTrend.labels"
            :data="turnoutTrend.turnout"
            label="Turnout %"
            aria-label="Turnout trend area chart"
          />
        </div>
      </div>
    </section>

    <section class="standings">
      <article v-for="pos in standings" :key="pos.uuid" class="standing-card">
        <header class="standing-card__head">
          <h2>{{ pos.title }}</h2>
          <p>Max votes {{ pos.max_votes_allowed }}</p>
        </header>
        <ul class="standing-list">
          <li
            v-for="candidate in pos.candidates"
            :key="candidate.uuid"
            :class="{ 'is-winner': candidate.rank === 1 }"
          >
            <span class="standing-rank">{{ candidate.rank }}</span>
            <span class="standing-name">{{ candidate.full_name }}</span>
            <span class="standing-votes">{{ candidate.votes }} votes</span>
            <span class="standing-pct">{{ candidate.percentage }}%</span>
          </li>
        </ul>
      </article>
    </section>

    <section class="result-panel integrity">
      <h2>Integrity</h2>
      <div class="integrity-grid">
        <div><i class="fas fa-check-circle"></i> Vote hashes verified</div>
        <div><i class="fas fa-check-circle"></i> SVT consistency</div>
        <div><i class="fas fa-check-circle"></i> No duplicate votes</div>
        <div><i class="fas fa-users"></i> Eligible {{ integrity.eligible_voters }}</div>
        <div><i class="fas fa-flag"></i> Votes cast {{ integrity.votes_cast }}</div>
        <div><i class="fas fa-percentage"></i> Turnout {{ integrity.turnout_percentage }}%</div>
      </div>
      <p class="integrity-hash mono">Hash {{ result.result_hash?.slice(0, 24) }}…</p>
    </section>
  </div>

  <div v-else class="admin-page result-loading">
    <i class="fas fa-spinner fa-spin"></i>
    <p>Loading results…</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { resultsApi } from '@/api/results'
import { electionApi } from '@/api/elections'
import { usePageHeading } from '@/composables/usePageHeading'
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

const statusLabel = (status) => ({
  generated: 'Generated',
  pending_certification: 'Pending certification',
  certified: 'Certified',
  published: 'Published',
  archived: 'Archived',
})[status] || status

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
  return new Date(date).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
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
.result-detail {
  display: grid;
  gap: 1.1rem;
  max-width: 56rem;
}

.result-hero,
.result-panel,
.cert-seal,
.standing-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.1rem;
}

.result-hero {
  padding: 1.15rem 1.25rem 1.25rem;
  display: grid;
  gap: 0.95rem;
}

.result-back {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  width: fit-content;
  border: none;
  background: transparent;
  color: #78716c;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.result-hero__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
}

.result-eyebrow {
  margin: 0;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.result-title {
  margin: 0.2rem 0 0;
  font-size: clamp(1.25rem, 3vw, 1.55rem);
  font-weight: 750;
  letter-spacing: -0.03em;
  color: #1c1917;
  line-height: 1.2;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.85rem;
  margin-top: 0.55rem;
  font-size: 0.78rem;
  color: #78716c;
}

.result-status {
  display: inline-flex;
  align-items: center;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: #f5f5f4;
  color: #57534e;
  border: 1px solid #e7e5e4;
}

.result-status[data-status='certified'] {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.result-status[data-status='published'] {
  background: #ecfdf5;
  border-color: #bbf7d0;
  color: #0f766e;
}

.result-status[data-status='generated'],
.result-status[data-status='pending_certification'] {
  background: #fff7ed;
  border-color: #fed7aa;
  color: #c2410c;
}

.result-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.cert-seal {
  padding: 1.15rem 1.25rem 1.25rem;
  display: grid;
  gap: 1rem;
  background:
    linear-gradient(180deg, #f4fbf8 0%, #fff 38%);
  border-color: #d1fae5;
}

.cert-seal__head {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
}

.cert-seal__icon {
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 0.75rem;
  display: grid;
  place-items: center;
  background: #ecfdf5;
  color: #0f766e;
  border: 1px solid #d1fae5;
  flex-shrink: 0;
}

.cert-seal__eyebrow {
  margin: 0;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
}

.cert-seal__title {
  margin: 0.15rem 0 0;
  font-size: 1.05rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: #134e4a;
}

.cert-seal__sub {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
  color: #78716c;
}

.cert-seal__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
}

@media (min-width: 800px) {
  .cert-seal__grid {
    grid-template-columns: 0.9fr 0.9fr 1.2fr;
  }
}

.cert-media {
  margin: 0;
  display: grid;
  gap: 0.4rem;
}

.cert-media figcaption,
.cert-facts span {
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #a8a29e;
}

.cert-media img {
  width: 100%;
  max-height: 11rem;
  object-fit: cover;
  border-radius: 0.8rem;
  border: 1px solid #ebe8e2;
  background: #fff;
}

.cert-media img.is-sig {
  object-fit: contain;
  background: #fff;
  max-height: 8rem;
  padding: 0.5rem;
}

.cert-empty {
  display: grid;
  place-items: center;
  min-height: 6rem;
  border-radius: 0.8rem;
  border: 1px dashed #e7e5e4;
  color: #a8a29e;
}

.cert-facts {
  display: grid;
  gap: 0.75rem;
  align-content: start;
}

.cert-facts div {
  display: grid;
  gap: 0.2rem;
}

.cert-facts strong {
  font-size: 0.84rem;
  font-weight: 650;
  color: #1c1917;
  word-break: break-word;
  line-height: 1.4;
}

.cert-facts em {
  font-style: normal;
  color: #a8a29e;
  font-weight: 500;
  font-size: 0.74rem;
}

.result-panel {
  padding: 1.15rem 1.25rem 1.25rem;
}

.result-panel__head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.result-panel h2 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: #1c1917;
}

.result-panel__head p {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: #78716c;
}

.result-select {
  border: 1px solid #ebe8e2;
  border-radius: 0.65rem;
  background: #fff;
  color: #44403c;
  font-size: 0.8rem;
  padding: 0.45rem 0.7rem;
}

.results-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
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
  min-height: 13rem;
  padding: 0.85rem;
  border-radius: 0.9rem;
  background: #fafaf8;
  border: 1px solid #f0efea;
}

.results-chart-card h3 {
  margin: 0 0 0.55rem;
  font-size: 0.74rem;
  font-weight: 700;
  color: #78716c;
}

.standings {
  display: grid;
  gap: 0.85rem;
}

.standing-card__head {
  padding: 0.95rem 1.15rem;
  border-bottom: 1px solid #f0efea;
}

.standing-card__head h2 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 750;
  color: #1c1917;
}

.standing-card__head p {
  margin: 0.15rem 0 0;
  font-size: 0.72rem;
  color: #a8a29e;
}

.standing-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.standing-list li {
  display: grid;
  grid-template-columns: 1.5rem 1fr auto auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.8rem 1.15rem;
  border-top: 1px solid #f5f5f4;
}

.standing-list li:first-child {
  border-top: none;
}

.standing-list li.is-winner {
  background: #f4fbf8;
}

.standing-rank {
  font-size: 0.78rem;
  font-weight: 700;
  color: #a8a29e;
}

.standing-name {
  font-size: 0.88rem;
  font-weight: 650;
  color: #1c1917;
}

.standing-votes {
  font-size: 0.78rem;
  color: #78716c;
}

.standing-pct {
  font-size: 0.82rem;
  font-weight: 750;
  color: #0f766e;
  min-width: 3.2rem;
  text-align: right;
}

.integrity h2 {
  margin-bottom: 0.85rem;
}

.integrity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  gap: 0.65rem;
  font-size: 0.82rem;
  color: #44403c;
}

.integrity-grid div {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.65rem 0.75rem;
  border-radius: 0.7rem;
  background: #fafaf8;
  border: 1px solid #f0efea;
}

.integrity-grid i {
  color: #0f766e;
  font-size: 0.78rem;
}

.integrity-hash {
  margin: 0.85rem 0 0;
  font-size: 0.72rem;
  color: #a8a29e;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.result-loading {
  display: grid;
  justify-items: center;
  gap: 0.55rem;
  padding: 3rem 1rem;
  color: #78716c;
}
</style>
