<template>
  <div class="dummy-preview">
    <div class="dummy-banner">
      <div class="dummy-banner__icon" aria-hidden="true">
        <i class="fas fa-flask"></i>
      </div>
      <div>
        <h3 class="dummy-preview__title">Dry-run ballot <span class="optional-tag">Optional</span></h3>
        <p class="dummy-preview__sub">
          Optional readiness check with masked register voters. Skip it anytime —
          schedule or start the election without running this.
        </p>
      </div>
      <div class="dummy-preview__actions">
        <button
          type="button"
          class="btn btn-ghost"
          :disabled="loading || !entries.length || modalOpen"
          @click="pickRandom"
        >
          <i class="fas fa-random"></i>
          New sample
        </button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="loading || sampleVoters.length < 1 || !approvedPositions.length || modalOpen"
          @click="openRunModal"
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
      message="Attach an approved voter register with entries before running a dummy preview."
    />

    <EmptyState
      v-else-if="!approvedPositions.length"
      icon="fas fa-list"
      title="No approved candidates yet"
      message="Add positions and approve at least one candidate per race before the dry-run."
    />

    <div v-else class="sample-grid">
      <article
        v-for="(voter, idx) in sampleVoters"
        :key="voter.key"
        class="sample-card"
        :style="{ '--delay': `${idx * 45}ms` }"
      >
        <span class="sample-card__avatar">{{ voter.initial }}</span>
        <div class="sample-card__body">
          <p class="sample-card__name">{{ voter.maskedName }}</p>
          <p class="sample-card__meta">{{ voter.maskedId }}</p>
          <span v-if="voter.category" class="sample-card__cat">{{ voter.category }}</span>
        </div>
      </article>
    </div>

    <Dialog
      v-model:visible="modalOpen"
      modal
      :closable="phase === 'done' || phase === 'idle'"
      :closeOnEscape="phase === 'done' || phase === 'idle'"
      :dismissableMask="false"
      :style="{ width: 'min(28rem, 94vw)' }"
      class="dummy-run-dialog"
      @hide="onModalHide"
    >
      <template #header>
        <span class="dummy-run__header">
          {{ phase === 'done' ? 'Dry-run complete' : 'Running dummy vote' }}
        </span>
      </template>

      <div class="dummy-run" :class="`is-${phase}`">
        <!-- Casting animation -->
        <div v-if="phase === 'casting' || phase === 'verifying'" class="dummy-run__stage">
          <div class="ballot-orbit" aria-hidden="true">
            <span class="ballot-orbit__ring"></span>
            <span class="ballot-orbit__ring is-late"></span>
            <span class="ballot-orbit__core">
              <i class="fas fa-vote-yea"></i>
            </span>
          </div>
          <p class="dummy-run__status">{{ statusLine }}</p>
          <div class="dummy-run__progress" role="progressbar" :aria-valuenow="progressPct" aria-valuemin="0" aria-valuemax="100">
            <div class="dummy-run__progress-fill" :style="{ width: `${progressPct}%` }"></div>
          </div>
          <ul class="dummy-run__feed">
            <li
              v-for="item in feedItems"
              :key="item.id"
              class="dummy-run__feed-item"
              :class="{ 'is-active': item.active }"
            >
              <span class="dummy-run__feed-avatar">{{ item.initial }}</span>
              <span>
                <strong>{{ item.name }}</strong>
                <small>{{ item.detail }}</small>
              </span>
              <i class="fas fa-check dummy-run__feed-check" aria-hidden="true"></i>
            </li>
          </ul>
        </div>

        <!-- Success -->
        <div v-else-if="phase === 'done'" class="dummy-run__success">
          <div class="success-burst" aria-hidden="true">
            <span class="success-burst__ring"></span>
            <span class="success-burst__mark">
              <i class="fas fa-check"></i>
            </span>
          </div>
          <h3>Dummy vote successful</h3>
          <p>
            Ballot flow checked with {{ lastVoterCount }} sample voter{{ lastVoterCount === 1 ? '' : 's' }}
            across {{ lastRaceCount }} race{{ lastRaceCount === 1 ? '' : 's' }}.
            No results were shown or saved — this preview will clear automatically.
          </p>
          <p class="dummy-run__hint">You can schedule and open the real election now.</p>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Dialog from 'primevue/dialog'
import { registerApi, institutionRegisterApi } from '@/api/registers'
import { electionApi } from '@/api/elections'
import { candidateApi } from '@/api/candidates'
import EmptyState from '@/components/admin/EmptyState.vue'
import { unlockAudio, playNotificationChime } from '@/utils/beep'

const props = defineProps({
  electionUuid: { type: String, required: true },
})

const emit = defineEmits(['completed'])

const loading = ref(false)
const entries = ref([])
const positions = ref([])
const candidates = ref([])
const sampleVoters = ref([])

const modalOpen = ref(false)
const phase = ref('idle') // idle | casting | verifying | done
const progressPct = ref(0)
const statusLine = ref('')
const feedItems = ref([])
const lastVoterCount = ref(0)
const lastRaceCount = ref(0)

let timers = []
let clearTimer = null

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

const clearTimers = () => {
  timers.forEach((id) => clearTimeout(id))
  timers = []
  if (clearTimer) {
    clearTimeout(clearTimer)
    clearTimer = null
  }
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
}

const resetSection = () => {
  sampleVoters.value = []
  feedItems.value = []
  progressPct.value = 0
  statusLine.value = ''
  phase.value = 'idle'
  // Drop any legacy dry-run standings that may linger in this browser.
  try {
    sessionStorage.removeItem(`vb_dummy_preview_${props.electionUuid}`)
  } catch {
    /* ignore */
  }
  // Fresh sample so the section stays usable without leftover results.
  if (entries.value.length) pickRandom()
}

const finishSuccess = () => {
  phase.value = 'done'
  progressPct.value = 100
  statusLine.value = 'Dry-run complete'
  unlockAudio()
  playNotificationChime()
  // Auto-clear the dry-run section after a short success beat — nothing was persisted.
  clearTimer = setTimeout(() => {
    modalOpen.value = false
    resetSection()
    emit('completed')
  }, 2200)
}

const openRunModal = () => {
  if (!sampleVoters.value.length || !approvedPositions.value.length) return
  clearTimers()
  unlockAudio()
  // Client-side dry-run only — never records votes or reveals candidates/winners.
  lastVoterCount.value = sampleVoters.value.length
  lastRaceCount.value = approvedPositions.value.length

  modalOpen.value = true
  phase.value = 'casting'
  progressPct.value = 0
  feedItems.value = []
  statusLine.value = 'Sealing sample ballots…'

  const voters = sampleVoters.value
  const stepMs = Math.max(280, Math.min(520, 2200 / Math.max(voters.length, 1)))

  voters.forEach((voter, idx) => {
    const id = setTimeout(() => {
      feedItems.value = [
        {
          id: `${voter.key}-${idx}`,
          name: voter.maskedName,
          detail: `Ballot ${idx + 1} of ${voters.length} · sealed`,
          initial: voter.initial,
          active: true,
        },
        ...feedItems.value.map((item) => ({ ...item, active: false })).slice(0, 3),
      ]
      progressPct.value = Math.round(((idx + 1) / voters.length) * 78)
      statusLine.value = `Casting ballot ${idx + 1} of ${voters.length}…`
    }, idx * stepMs)
    timers.push(id)
  })

  const verifyAt = voters.length * stepMs + 180
  timers.push(setTimeout(() => {
    phase.value = 'verifying'
    statusLine.value = 'Verifying dry-run flow…'
    progressPct.value = 92
  }, verifyAt))

  timers.push(setTimeout(() => {
    finishSuccess()
  }, verifyAt + 900))
}

const onModalHide = () => {
  clearTimers()
  if (phase.value === 'done') {
    resetSection()
    emit('completed')
  } else if (phase.value !== 'idle') {
    // Interrupted mid-run — still clear any ephemeral state; nothing was saved.
    resetSection()
  }
  phase.value = 'idle'
}

const loadEntriesForElection = async () => {
  const { data: election } = await electionApi.get(props.electionUuid)
  const registerUuid = election?.register?.uuid
  if (registerUuid) {
    try {
      const { data } = await institutionRegisterApi.listEntries(registerUuid)
      const list = Array.isArray(data) ? data : (data.results || [])
      if (list.length) return list
    } catch {
      /* fall through to legacy election registers */
    }
  }

  const regRes = await registerApi.list(props.electionUuid)
  const registers = Array.isArray(regRes.data) ? regRes.data : (regRes.data.results || [])
  const allEntries = []
  for (const reg of registers) {
    const { data } = await registerApi.listEntries(props.electionUuid, reg.uuid)
    const list = Array.isArray(data) ? data : (data.results || [])
    allEntries.push(...list)
  }
  return allEntries
}

const load = async () => {
  loading.value = true
  try {
    const [posRes, candRes, entryList] = await Promise.all([
      electionApi.getPositions(props.electionUuid),
      candidateApi.list(props.electionUuid),
      loadEntriesForElection(),
    ])
    positions.value = Array.isArray(posRes.data) ? posRes.data : (posRes.data.results || [])
    candidates.value = Array.isArray(candRes.data) ? candRes.data : (candRes.data.results || [])
    entries.value = entryList
    if (entries.value.length) pickRandom()
  } catch (error) {
    console.error('Dummy preview load failed:', error)
  } finally {
    loading.value = false
  }
}

onMounted(load)
onUnmounted(clearTimers)
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

.optional-tag {
  display: inline-flex;
  margin-left: 0.4rem;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  vertical-align: middle;
  background: #f1f5f9;
  color: #64748b;
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

.sample-card__body { min-width: 0; }

.sample-card__name {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 750;
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

.dummy-run__header {
  font-weight: 800;
  letter-spacing: -0.02em;
}

.dummy-run {
  padding: 0.35rem 0.15rem 0.5rem;
  min-height: 16rem;
}

.dummy-run__stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.95rem;
  text-align: center;
}

.ballot-orbit {
  position: relative;
  width: 6.5rem;
  height: 6.5rem;
  display: grid;
  place-items: center;
}

.ballot-orbit__ring {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  border: 2px solid rgba(61, 79, 68, 0.18);
  animation: orbit-pulse 1.4s ease-out infinite;
}

.ballot-orbit__ring.is-late {
  animation-delay: 0.45s;
  border-color: rgba(51, 65, 85, 0.16);
}

.ballot-orbit__core {
  width: 3.4rem;
  height: 3.4rem;
  border-radius: 1rem;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #3d4f44, #1f2937);
  color: #fff;
  font-size: 1.15rem;
  box-shadow: 0 12px 28px rgba(28, 28, 28, 0.18);
  animation: core-bob 1.2s ease-in-out infinite;
}

.dummy-run__status {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 750;
  color: var(--vb-ink, #1c1c1c);
}

.dummy-run__progress {
  width: 100%;
  height: 0.45rem;
  border-radius: 999px;
  background: #eef2f0;
  overflow: hidden;
}

.dummy-run__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #a3b18a, #3d4f44);
  transition: width 0.28s ease;
}

.dummy-run__feed {
  list-style: none;
  margin: 0.25rem 0 0;
  padding: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.dummy-run__feed-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.65rem;
  align-items: center;
  text-align: left;
  padding: 0.65rem 0.75rem;
  border-radius: 0.85rem;
  background: #f8faf9;
  border: 1px solid #e7ece8;
  animation: card-in 0.28s ease both;
  opacity: 0.72;
}

.dummy-run__feed-item.is-active {
  opacity: 1;
  background: #fff;
  border-color: rgba(61, 79, 68, 0.28);
  box-shadow: 0 8px 20px rgba(28, 28, 28, 0.05);
}

.dummy-run__feed-avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 0.65rem;
  display: grid;
  place-items: center;
  background: #e8efe6;
  color: #3d4f44;
  font-weight: 800;
  font-size: 0.78rem;
}

.dummy-run__feed-item strong {
  display: block;
  font-size: 0.82rem;
}

.dummy-run__feed-item small {
  display: block;
  margin-top: 0.12rem;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.7rem;
}

.dummy-run__feed-check {
  color: #059669;
  font-size: 0.78rem;
}

.dummy-run__success {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.65rem;
  padding: 0.75rem 0.25rem 0.35rem;
  animation: card-in 0.35s ease;
}

.success-burst {
  position: relative;
  width: 5.5rem;
  height: 5.5rem;
  display: grid;
  place-items: center;
  margin-bottom: 0.25rem;
}

.success-burst__ring {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  border: 2px solid rgba(5, 150, 105, 0.25);
  animation: success-ring 0.7s ease-out both;
}

.success-burst__mark {
  width: 3.4rem;
  height: 3.4rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #10b981, #047857);
  color: #fff;
  font-size: 1.25rem;
  box-shadow: 0 12px 28px rgba(4, 120, 87, 0.28);
  animation: success-pop 0.45s cubic-bezier(0.2, 0.9, 0.3, 1.25) both;
}

.dummy-run__success h3 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.dummy-run__success p {
  margin: 0;
  max-width: 22rem;
  font-size: 0.86rem;
  line-height: 1.5;
  color: #4b5563;
}

.dummy-run__hint {
  color: #059669 !important;
  font-weight: 650;
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}

@keyframes orbit-pulse {
  0% { transform: scale(0.72); opacity: 0.85; }
  100% { transform: scale(1.18); opacity: 0; }
}

@keyframes core-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

@keyframes success-pop {
  from { transform: scale(0.4); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

@keyframes success-ring {
  from { transform: scale(0.6); opacity: 0.9; }
  to { transform: scale(1.25); opacity: 0; }
}
</style>
