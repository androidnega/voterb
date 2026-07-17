<template>
  <div class="dummy-preview">
    <div class="dummy-banner">
      <div class="dummy-banner__icon" aria-hidden="true">
        <i class="fas fa-flask"></i>
      </div>
      <div>
        <h3 class="dummy-preview__title">Dry-run ballot</h3>
        <p class="dummy-preview__sub">
          Simulate votes with five masked register voters. Nothing is written to the database — results stay in this browser only.
        </p>
      </div>
      <div class="dummy-preview__actions">
        <button type="button" class="btn btn-ghost" :disabled="loading || !entries.length" @click="pickRandom">
          <i class="fas fa-random"></i>
          New sample
        </button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="loading || sampleVoters.length < 1 || !approvedPositions.length"
          @click="runDummyVote"
        >
          <i class="fas fa-play"></i>
          Run dummy vote
        </button>
      </div>
    </div>

    <div v-if="loading" class="dummy-preview__loading">
      <i class="fas fa-spinner fa-spin"></i> Loading register…
    </div>

    <EmptyState
      v-else-if="!entries.length"
      icon="fas fa-users"
      title="No register voters"
      message="Import voters into a register category before running a dummy preview."
    />

    <template v-else>
      <div class="sample-grid">
        <article
          v-for="(voter, idx) in sampleVoters"
          :key="voter.key"
          class="sample-card"
          :style="{ '--delay': `${idx * 40}ms` }"
        >
          <span class="sample-card__avatar">{{ voter.initial }}</span>
          <div class="sample-card__body">
            <p class="sample-card__name">{{ voter.maskedName }}</p>
            <p class="sample-card__meta">{{ voter.maskedId }}</p>
            <span v-if="voter.category" class="sample-card__cat">{{ voter.category }}</span>
          </div>
        </article>
      </div>

      <div v-if="previewResults" class="preview-results">
        <div class="preview-results__head">
          <div>
            <h4>Preview standings</h4>
            <p class="preview-note">
              Simulated {{ previewResults.voter_count }} ballots · sessionStorage only
            </p>
          </div>
          <button type="button" class="btn btn-ghost" @click="clearResults">Clear</button>
        </div>

        <div v-for="pos in previewResults.positions" :key="pos.uuid" class="preview-position">
          <h5>{{ pos.title }}</h5>
          <div class="preview-rows">
            <div v-for="c in pos.candidates" :key="c.uuid" class="preview-row">
              <span class="preview-rank" :class="{ 'is-top': c.rank === 1 }">{{ c.rank }}</span>
              <div class="preview-row__main">
                <div class="preview-row__top">
                  <strong>{{ c.full_name }}</strong>
                  <span class="mono">{{ c.votes }} · {{ c.percentage }}%</span>
                </div>
                <div class="preview-bar" aria-hidden="true">
                  <span class="preview-bar__fill" :style="{ width: `${Math.max(c.percentage, 2)}%` }"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { registerApi } from '@/api/registers'
import { electionApi } from '@/api/elections'
import { candidateApi } from '@/api/candidates'
import EmptyState from '@/components/admin/EmptyState.vue'

const props = defineProps({
  electionUuid: { type: String, required: true },
})

const STORAGE_KEY = computed(() => `vb_dummy_preview_${props.electionUuid}`)

const loading = ref(false)
const entries = ref([])
const positions = ref([])
const candidates = ref([])
const sampleVoters = ref([])
const previewResults = ref(null)

const approvedPositions = computed(() => {
  return positions.value
    .map((pos) => ({
      ...pos,
      candidates: candidates.value.filter(
        (c) => c.position?.uuid === pos.uuid && c.status === 'approved',
      ),
    }))
    .filter((pos) => pos.candidates.length > 0)
})

const maskName = (name) => {
  const parts = (name || 'Voter').trim().split(/\s+/)
  return parts
    .map((p, i) => (i === 0 ? `${p.slice(0, 1)}***` : `${p.slice(0, 1)}.`))
    .join(' ')
}

const maskId = (id) => {
  const s = String(id || '')
  if (s.length <= 4) return '****'
  return `${s.slice(0, 2)}***${s.slice(-2)}`
}

const shuffle = (arr) => {
  const copy = [...arr]
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

const pickRandom = () => {
  const pool = shuffle(entries.value)
  sampleVoters.value = pool.slice(0, 5).map((entry, idx) => ({
    key: `${entry.uuid || entry.voter_id}-${idx}`,
    maskedName: maskName(entry.full_name),
    maskedId: maskId(entry.voter_id),
    category: entry.category?.name || '',
    initial: (entry.full_name || 'V').charAt(0).toUpperCase(),
    categoryUuid: entry.category?.uuid || null,
  }))
  persist()
}

const runDummyVote = () => {
  const voters = sampleVoters.value
  const races = approvedPositions.value
  if (!voters.length || !races.length) return

  const standings = races.map((pos) => {
    const tallies = Object.fromEntries(pos.candidates.map((c) => [c.uuid, 0]))
    voters.forEach((voter) => {
      if (pos.allow_all_voters === false) {
        const allowed = (pos.restricted_categories || []).map((c) => c.uuid)
        if (allowed.length && voter.categoryUuid && !allowed.includes(voter.categoryUuid)) {
          return
        }
        if (allowed.length && !voter.categoryUuid) return
      }
      const pick = pos.candidates[Math.floor(Math.random() * pos.candidates.length)]
      if (pick) tallies[pick.uuid] += 1
    })
    const total = Object.values(tallies).reduce((a, b) => a + b, 0) || 1
    const ranked = pos.candidates
      .map((c) => ({
        uuid: c.uuid,
        full_name: c.full_name,
        votes: tallies[c.uuid] || 0,
        percentage: Math.round(((tallies[c.uuid] || 0) / total) * 1000) / 10,
      }))
      .sort((a, b) => b.votes - a.votes)
      .map((c, idx) => ({ ...c, rank: idx + 1 }))
    return {
      uuid: pos.uuid,
      title: pos.title,
      candidates: ranked,
    }
  })

  previewResults.value = {
    voter_count: voters.length,
    positions: standings,
    generated_at: new Date().toISOString(),
  }
  persist()
}

const clearResults = () => {
  previewResults.value = null
  persist()
}

const persist = () => {
  try {
    sessionStorage.setItem(
      STORAGE_KEY.value,
      JSON.stringify({
        sampleVoters: sampleVoters.value,
        previewResults: previewResults.value,
      }),
    )
  } catch {
    /* ignore quota */
  }
}

const restore = () => {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY.value)
    if (!raw) return
    const data = JSON.parse(raw)
    sampleVoters.value = data.sampleVoters || []
    previewResults.value = data.previewResults || null
  } catch {
    /* ignore */
  }
}

const load = async () => {
  loading.value = true
  try {
    const [regRes, posRes, candRes] = await Promise.all([
      registerApi.list(props.electionUuid),
      electionApi.getPositions(props.electionUuid),
      candidateApi.list(props.electionUuid),
    ])
    const registers = Array.isArray(regRes.data) ? regRes.data : (regRes.data.results || [])
    positions.value = Array.isArray(posRes.data) ? posRes.data : (posRes.data.results || [])
    candidates.value = Array.isArray(candRes.data) ? candRes.data : (candRes.data.results || [])

    const allEntries = []
    for (const reg of registers) {
      const { data } = await registerApi.listEntries(props.electionUuid, reg.uuid)
      const list = Array.isArray(data) ? data : (data.results || [])
      allEntries.push(...list)
    }
    entries.value = allEntries
    restore()
    if (!sampleVoters.value.length && entries.value.length) pickRandom()
  } catch (error) {
    console.error('Dummy preview load failed:', error)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.dummy-preview {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.dummy-banner {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.85rem 1rem;
  align-items: start;
  padding: 1rem 1.1rem;
  border-radius: 1.15rem;
  background:
    linear-gradient(135deg, rgba(51, 65, 85, 0.06), rgba(61, 79, 68, 0.08)),
    #fff;
  border: 1px solid var(--vb-line, #ebeae4);
}

.dummy-banner__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.8rem;
  display: grid;
  place-items: center;
  background: #334155;
  color: #fff;
  font-size: 0.9rem;
}

.dummy-preview__title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--vb-ink, #1c1c1c);
}

.dummy-preview__sub {
  margin: 0.3rem 0 0;
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
  line-height: 1.45;
  max-width: 36rem;
}

.dummy-preview__actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

@media (min-width: 860px) {
  .dummy-banner {
    grid-template-columns: auto 1fr auto;
    align-items: center;
  }

  .dummy-preview__actions {
    grid-column: auto;
    justify-content: flex-end;
  }
}

.dummy-preview__loading {
  padding: 2rem;
  text-align: center;
  color: var(--vb-muted, #8a8a8a);
}

.sample-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
}

@media (min-width: 640px) {
  .sample-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 960px) {
  .sample-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

.sample-card {
  display: flex;
  gap: 0.7rem;
  align-items: flex-start;
  padding: 0.85rem;
  border-radius: 1rem;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  animation: card-in 0.28s ease both;
  animation-delay: var(--delay, 0ms);
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.sample-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(28, 28, 28, 0.05);
}

.sample-card__avatar {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.75rem;
  background: linear-gradient(145deg, var(--vb-sage-soft, #d8e0cf), var(--vb-accent-soft, #e8efe6));
  color: var(--vb-accent, #3d4f44);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  flex-shrink: 0;
}

.sample-card__body {
  min-width: 0;
}

.sample-card__name {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.sample-card__meta {
  margin: 0.15rem 0 0;
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.sample-card__cat {
  display: inline-flex;
  margin-top: 0.4rem;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
  font-size: 0.66rem;
  font-weight: 700;
  color: var(--vb-muted, #8a8a8a);
}

.preview-results {
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
  padding: 1rem 1.1rem;
  border-radius: 1.15rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
  animation: card-in 0.28s ease;
}

.preview-results__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
}

.preview-results__head h4 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.preview-note {
  margin: 0.25rem 0 0;
  font-size: 0.74rem;
  color: var(--vb-muted, #8a8a8a);
}

.preview-position h5 {
  margin: 0 0 0.55rem;
  font-size: 0.82rem;
  font-weight: 750;
  color: var(--vb-ink, #1c1c1c);
}

.preview-rows {
  display: grid;
  gap: 0.55rem;
}

.preview-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.65rem;
  align-items: center;
  padding: 0.65rem 0.75rem;
  border-radius: 0.85rem;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
}

.preview-rank {
  width: 1.65rem;
  height: 1.65rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 800;
}

.preview-rank.is-top {
  background: var(--vb-accent, #3d4f44);
  color: #fff;
}

.preview-row__main {
  min-width: 0;
}

.preview-row__top {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: baseline;
  margin-bottom: 0.35rem;
}

.preview-row__top strong {
  font-size: 0.84rem;
  font-weight: 750;
}

.preview-row__top .mono {
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
  font-variant-numeric: tabular-nums;
}

.preview-bar {
  height: 0.35rem;
  border-radius: 999px;
  background: var(--vb-panel, #f7f6f2);
  overflow: hidden;
}

.preview-bar__fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--vb-gradient-from, #a3b18a), var(--vb-gradient-to, #3d4f44));
  transition: width 0.45s ease;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
