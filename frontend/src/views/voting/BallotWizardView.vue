<template>
  <div class="ballot-page">
    <BallotWizardSkeleton
      v-if="loading || showSkeleton"
      :hint="showSlowHint ? slowHint : ''"
    />

    <FriendlyLoadState
      v-else-if="error"
      tone="error"
      title="Couldn’t open your ballot"
      :message="error"
      action-label="Try again"
      @action="fetchBallot"
    />

    <template v-else>
      <header class="ballot-head">
        <div>
          <p class="ballot-eyebrow">Cast your vote</p>
          <h1 class="ballot-title">{{ electionTitle }}</h1>
        </div>
        <span v-if="positions.length" class="ballot-step">
          Step {{ activeStepIndex + 1 }} of {{ positions.length }}
        </span>
      </header>

      <div v-if="positions.length === 0" class="ballot-state">
        <FriendlyLoadState
          tone="empty"
          title="Nothing to vote on yet"
          message="This ballot doesn’t have any positions right now."
          action-label="Go back"
          icon="far fa-folder-open"
          @action="$router.push(`/vote/${electionUuid}`)"
        />
      </div>

      <div v-else class="ballot-body">
        <div class="ballot-tabs">
          <button
            v-for="(pos, idx) in positions"
            :key="pos.uuid"
            type="button"
            class="ballot-tab"
            :class="{
              'is-active': activeStepIndex === idx && phase === 'select',
              'is-sealed': sealedIds.has(pos.uuid),
            }"
            :disabled="phase === 'ceremony'"
            @click="goToStep(idx)"
          >
            <i v-if="sealedIds.has(pos.uuid)" class="fas fa-check" aria-hidden="true"></i>
            {{ pos.title }}
          </button>
        </div>

        <article v-if="phase === 'ceremony'" class="ballot-card ballot-card--ceremony">
          <BallotBoxCeremony
            :position-title="ceremonyMeta.positionTitle"
            :candidate-label="ceremonyMeta.candidateLabel"
            :next-title="ceremonyMeta.nextTitle"
            :is-last="ceremonyMeta.isLast"
            :sealed-count="sealedIds.size"
            @continue="finishCeremony"
          />
        </article>

        <article v-else class="ballot-card">
          <div class="ballot-card__top">
            <div>
              <h2 class="ballot-card__title">{{ currentPosition.title }}</h2>
              <p v-if="currentPosition.description" class="ballot-card__desc">{{ currentPosition.description }}</p>
              <p class="ballot-card__hint">
                Select up to {{ currentPosition.max_votes_allowed }} candidate{{ currentPosition.max_votes_allowed === 1 ? '' : 's' }}.
              </p>
            </div>
            <span v-if="isCurrentSealed" class="ballot-sealed-pill">
              <i class="fas fa-lock" aria-hidden="true"></i>
              Sealed
            </span>
          </div>

          <div class="candidate-grid">
            <button
              v-for="candidate in currentPosition.candidates"
              :key="candidate.uuid"
              type="button"
              class="candidate-card"
              :class="{ 'is-selected': isSelected(currentPosition.uuid, candidate.uuid) }"
              :disabled="isCurrentSealed"
              @click="toggleCandidate(currentPosition.uuid, candidate.uuid, currentPosition.max_votes_allowed)"
            >
              <div class="candidate-card__photo-wrap">
                <img
                  v-if="photoUrl(candidate)"
                  :src="photoUrl(candidate)"
                  :alt="candidate.full_name"
                  class="candidate-card__photo"
                  loading="lazy"
                  @error="onPhotoError(candidate.uuid)"
                />
                <div v-else class="candidate-card__fallback" aria-hidden="true">
                  {{ initials(candidate.full_name) }}
                </div>
                <span v-if="isSelected(currentPosition.uuid, candidate.uuid)" class="candidate-card__check">
                  <i class="fas fa-check" aria-hidden="true"></i>
                </span>
              </div>
              <div class="candidate-card__copy">
                <p class="candidate-card__name">{{ candidate.full_name }}</p>
                <p v-if="candidate.department" class="candidate-card__meta">{{ candidate.department }}</p>
              </div>
              <span v-if="candidate.ballot_number" class="candidate-card__badge">#{{ candidate.ballot_number }}</span>
            </button>
          </div>

          <div class="ballot-nav">
            <button
              type="button"
              class="ballot-nav__btn"
              :disabled="activeStepIndex === 0 || phase === 'ceremony'"
              @click="prevStep"
            >
              Back
            </button>
            <button
              type="button"
              class="ballot-nav__btn ballot-nav__btn--primary"
              :disabled="!canSealCurrent"
              @click="sealCurrentPosition"
            >
              {{ primaryActionLabel }}
            </button>
          </div>
          <p v-if="submitError && !showReview" class="ballot-soft-error">{{ submitError }}</p>
        </article>
      </div>
    </template>

    <Dialog v-model:visible="showReview" header="Review your vote" :modal="true" class="w-full max-w-lg">
      <div class="review-list">
        <div v-for="pos in positions" :key="pos.uuid" class="review-item">
          <p class="review-item__pos">{{ pos.title }}</p>
          <div v-if="getSelections(pos.uuid).length === 0" class="review-item__empty">No selection</div>
          <div v-else class="review-picks">
            <div v-for="candidate in getSelections(pos.uuid)" :key="candidate.uuid" class="review-pick">
              <img
                v-if="photoUrl(candidate)"
                :src="photoUrl(candidate)"
                :alt="candidate.full_name"
                class="review-pick__photo"
              />
              <span v-else class="review-pick__fallback">{{ initials(candidate.full_name) }}</span>
              <span>{{ candidate.full_name }}</span>
            </div>
          </div>
        </div>
      </div>
      <p v-if="submitError" class="review-error">{{ submitError }}</p>
      <div class="review-actions">
        <button type="button" class="ballot-nav__btn" :disabled="submitting" @click="showReview = false">Go back</button>
        <button type="button" class="ballot-nav__btn ballot-nav__btn--primary" :disabled="submitting" @click="submitVote">
          {{ submitting ? (submitSlow ? 'Still working…' : 'Submitting…') : 'Submit vote' }}
        </button>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'
import { resolveMediaUrl } from '@/utils/media'
import { useFriendlyLoad } from '@/composables/useFriendlyLoad'
import { friendlyActionError } from '@/utils/friendlyFeedback'
import { clearSvtSession, readSvtSession } from '@/utils/svtSession'
import BallotWizardSkeleton from '@/components/student/BallotWizardSkeleton.vue'
import FriendlyLoadState from '@/components/student/FriendlyLoadState.vue'
import BallotBoxCeremony from '@/components/voting/BallotBoxCeremony.vue'
import Dialog from 'primevue/dialog'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid
const DRAFT_KEY = `ballot_draft:${electionUuid}`

const electionTitle = ref('Ballot')
const positions = ref([])
const activeStep = ref('0')
const selections = ref({})
const sealedIds = ref(new Set())
const phase = ref('select') // select | ceremony
const ceremonyMeta = ref({
  positionTitle: '',
  candidateLabel: '',
  nextTitle: '',
  isLast: false,
})
const showReview = ref(false)
const submitting = ref(false)
const submitError = ref('')
const submitSlow = ref(false)
const brokenPhotos = ref(new Set())
let submitSlowTimer = null

const {
  loading,
  showSkeleton,
  showSlowHint,
  slowHint,
  error,
  begin,
  succeed,
  fail,
} = useFriendlyLoad({ subject: 'your ballot', skeletonDelayMs: 0 })

const activeStepIndex = computed(() => parseInt(activeStep.value, 10) || 0)
const currentPosition = computed(() => positions.value[activeStepIndex.value] || { candidates: [] })
const isCurrentSealed = computed(() => sealedIds.value.has(currentPosition.value?.uuid))
const canSealCurrent = computed(() => {
  if (phase.value !== 'select') return false
  if (isCurrentSealed.value) return true
  return (selections.value[currentPosition.value?.uuid] || []).length > 0
})
const primaryActionLabel = computed(() => {
  if (isCurrentSealed.value) {
    return activeStepIndex.value === positions.value.length - 1 ? 'Review & submit' : 'Continue'
  }
  return activeStepIndex.value === positions.value.length - 1 ? 'Seal & review' : 'Seal ballot'
})

function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
}

function photoUrl(candidate) {
  if (!candidate?.photo || brokenPhotos.value.has(candidate.uuid)) return ''
  return resolveMediaUrl(candidate.photo)
}

function onPhotoError(uuid) {
  const next = new Set(brokenPhotos.value)
  next.add(uuid)
  brokenPhotos.value = next
}

function clearSubmitSlow() {
  submitSlow.value = false
  if (submitSlowTimer) {
    clearTimeout(submitSlowTimer)
    submitSlowTimer = null
  }
}

function persistDraft() {
  try {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({
      selections: selections.value,
      sealed: [...sealedIds.value],
      activeStep: activeStep.value,
      electionTitle: electionTitle.value,
      saved_at: new Date().toISOString(),
    }))
  } catch {
    // ignore quota / private mode
  }
}

function restoreDraft() {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const data = JSON.parse(raw)
    if (data?.selections && typeof data.selections === 'object') {
      selections.value = data.selections
    }
    if (Array.isArray(data?.sealed)) {
      sealedIds.value = new Set(data.sealed)
    }
    if (data?.activeStep != null) activeStep.value = String(data.activeStep)
  } catch {
    // ignore
  }
}

function clearDraft() {
  sessionStorage.removeItem(DRAFT_KEY)
}

const fetchBallot = async () => {
  begin()
  try {
    const { data: session } = await votingApi.getSvtSession(electionUuid)
    if (session?.status !== 'validated') {
      clearSvtSession(electionUuid)
      clearDraft()
      succeed()
      await router.replace(`/vote/${electionUuid}`)
      return
    }
    const response = await votingApi.getBallot(electionUuid)
    positions.value = response.data.positions || []
    electionTitle.value = response.data.election_title || 'Ballot'
    restoreDraft()
    positions.value.forEach((pos) => {
      if (!selections.value[pos.uuid]) selections.value[pos.uuid] = []
    })
    // Drop sealed markers for positions that no longer exist
    sealedIds.value = new Set(
      [...sealedIds.value].filter((id) => positions.value.some((p) => p.uuid === id)),
    )
    persistDraft()
    succeed()
  } catch (err) {
    console.error('Failed to load ballot:', err)
    positions.value = []
    fail(err)
  }
}

const isSelected = (posUuid, candidateUuid) => selections.value[posUuid]?.includes(candidateUuid) || false

const toggleCandidate = (posUuid, candidateUuid, maxVotes) => {
  if (sealedIds.value.has(posUuid)) return
  const selected = [...(selections.value[posUuid] || [])]
  const index = selected.indexOf(candidateUuid)
  if (index > -1) {
    selected.splice(index, 1)
  } else if (selected.length < maxVotes) {
    selected.push(candidateUuid)
  } else {
    submitError.value = `You can select up to ${maxVotes} candidate${maxVotes === 1 ? '' : 's'} for this position.`
    return
  }
  selections.value = { ...selections.value, [posUuid]: selected }
  if (submitError.value) submitError.value = ''
  persistDraft()
}

const getSelections = (posUuid) => {
  const selectedUuids = selections.value[posUuid] || []
  const pos = positions.value.find((p) => p.uuid === posUuid)
  if (!pos) return []
  return pos.candidates.filter((c) => selectedUuids.includes(c.uuid))
}

function goToStep(idx) {
  if (phase.value === 'ceremony') return
  if (idx < 0 || idx >= positions.value.length) return
  // Only allow jumping to sealed positions or the first unsealed
  const firstOpen = positions.value.findIndex((p) => !sealedIds.value.has(p.uuid))
  if (idx > firstOpen && firstOpen >= 0 && !sealedIds.value.has(positions.value[idx].uuid)) {
    return
  }
  activeStep.value = String(idx)
  persistDraft()
}

function sealCurrentPosition() {
  const pos = currentPosition.value
  if (!pos?.uuid) return

  if (sealedIds.value.has(pos.uuid)) {
    // Already sealed — advance or review
    if (activeStepIndex.value >= positions.value.length - 1) {
      openReviewIfReady()
    } else {
      activeStep.value = String(activeStepIndex.value + 1)
      persistDraft()
    }
    return
  }

  const picks = getSelections(pos.uuid)
  if (!picks.length) {
    submitError.value = 'Select at least one candidate before sealing this ballot.'
    return
  }

  submitError.value = ''
  const nextIdx = activeStepIndex.value + 1
  const isLast = nextIdx >= positions.value.length
  ceremonyMeta.value = {
    positionTitle: pos.title,
    candidateLabel: picks.map((c) => c.full_name).join(', '),
    nextTitle: isLast ? 'Review' : (positions.value[nextIdx]?.title || 'Next'),
    isLast,
  }

  const next = new Set(sealedIds.value)
  next.add(pos.uuid)
  sealedIds.value = next
  persistDraft()
  phase.value = 'ceremony'
}

function finishCeremony() {
  phase.value = 'select'
  if (ceremonyMeta.value.isLast) {
    openReviewIfReady()
    return
  }
  const nextIdx = Math.min(activeStepIndex.value + 1, positions.value.length - 1)
  activeStep.value = String(nextIdx)
  persistDraft()
}

function openReviewIfReady() {
  const allSelected = positions.value.every((pos) => selections.value[pos.uuid]?.length > 0)
  const allSealed = positions.value.every((pos) => sealedIds.value.has(pos.uuid))
  if (!allSelected || !allSealed) {
    submitError.value = 'Please seal every position before submitting.'
    const missing = positions.value.findIndex((pos) => !sealedIds.value.has(pos.uuid))
    if (missing >= 0) activeStep.value = String(missing)
    return
  }
  submitError.value = ''
  showReview.value = true
}

const prevStep = () => {
  if (phase.value === 'ceremony') return
  const prevIndex = activeStepIndex.value - 1
  if (prevIndex >= 0) {
    activeStep.value = String(prevIndex)
    persistDraft()
  }
}

const submitVote = async () => {
  submitting.value = true
  submitError.value = ''
  clearSubmitSlow()
  submitSlowTimer = setTimeout(() => {
    submitSlow.value = true
  }, 3500)
  try {
    const payload = {
      selections: positions.value.map((pos) => ({
        position_uuid: pos.uuid,
        candidate_uuids: selections.value[pos.uuid] || [],
      })),
    }
    const session = readSvtSession(electionUuid)
    const svtCode = session?.code || ''
    const { data } = await votingApi.submitVote(electionUuid, payload.selections, svtCode || undefined)
    const code = data?.confirmation_code || ''
    if (code) sessionStorage.setItem(`vote_confirm:${electionUuid}`, code)
    clearSvtSession(electionUuid)
    clearDraft()
    showReview.value = false
    await router.push({
      path: `/vote/${electionUuid}/confirmation`,
      query: code ? { code } : {},
    })
  } catch (err) {
    console.error('Submission failed:', err)
    const msg = friendlyActionError(err, 'We couldn’t submit your vote. Please try again.')
    submitError.value = msg
    if (/expired|token|secure session/i.test(msg)) {
      clearSvtSession(electionUuid)
      clearDraft()
      showReview.value = false
      router.push(`/vote/${electionUuid}`)
    }
  } finally {
    clearSubmitSlow()
    submitting.value = false
  }
}

watch([selections, sealedIds, activeStep], persistDraft, { deep: true })

onMounted(fetchBallot)
onUnmounted(clearSubmitSlow)
</script>

<style scoped>
.ballot-page {
  width: min(46rem, 100%);
  margin: 0 auto;
  padding: 0.35rem 0 2rem;
}

.ballot-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.15rem;
}

.ballot-eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.ballot-title {
  margin: 0.25rem 0 0;
  font-size: clamp(1.35rem, 3vw, 1.7rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.ballot-step {
  font-size: 0.8rem;
  font-weight: 700;
  color: #78716c;
  white-space: nowrap;
}

.ballot-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  min-height: 12rem;
  border-radius: 1.25rem;
  background: #fff;
  border: 1px solid #ebe8e2;
  color: #78716c;
  font-size: 0.9rem;
}

.ballot-tabs {
  display: flex;
  gap: 0.45rem;
  overflow-x: auto;
  padding-bottom: 0.35rem;
  margin-bottom: 0.85rem;
  scrollbar-width: none;
}

.ballot-tabs::-webkit-scrollbar {
  display: none;
}

.ballot-tab {
  border: none;
  border-radius: 9999px;
  padding: 0.55rem 0.95rem;
  background: #ebe8e2;
  color: #57534e;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.ballot-tab i {
  font-size: 0.65rem;
  color: #0f766e;
}

.ballot-tab.is-active {
  background: #1c1917;
  color: #fff;
}

.ballot-tab.is-active i {
  color: #6ee7b7;
}

.ballot-tab.is-sealed:not(.is-active) {
  background: #ecfdf5;
  color: #0f766e;
}

.ballot-tab:disabled {
  cursor: default;
  opacity: 0.75;
}

.ballot-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.35rem;
  padding: 1.2rem 1.15rem 1.15rem;
  box-shadow: 0 4px 16px rgba(28, 25, 23, 0.03);
}

.ballot-card--ceremony {
  padding: 1rem 0.85rem 1.15rem;
}

.ballot-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.ballot-card__title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: #1c1917;
}

.ballot-card__desc,
.ballot-card__hint {
  margin: 0.35rem 0 0;
  font-size: 0.84rem;
  color: #78716c;
}

.ballot-sealed-pill {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.7rem;
  font-weight: 700;
  color: #0f766e;
  background: #ecfdf5;
  border: 1px solid #bbf7d0;
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
}

.candidate-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
  margin-top: 1rem;
}

@media (min-width: 640px) {
  .candidate-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.candidate-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: center;
  text-align: left;
  width: 100%;
  padding: 0.75rem;
  border-radius: 1.15rem;
  border: 1px solid #ebe8e2;
  background: #fafaf9;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.candidate-card:hover:not(:disabled) {
  border-color: #d6d3d1;
  transform: translateY(-1px);
}

.candidate-card:disabled {
  cursor: default;
  opacity: 0.85;
}

.candidate-card.is-selected {
  border-color: #34d399;
  background: #f0fdf9;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.12);
}

.candidate-card__photo-wrap {
  position: relative;
  width: 3.1rem;
  height: 3.1rem;
  border-radius: 999px;
  overflow: hidden;
  background: #e7e5e4;
  flex-shrink: 0;
}

.candidate-card__photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.candidate-card__fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  font-size: 0.78rem;
  font-weight: 800;
  color: #57534e;
}

.candidate-card__check {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 1.15rem;
  height: 1.15rem;
  border-radius: 999px;
  background: #0f766e;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 0.55rem;
  border: 2px solid #fff;
}

.candidate-card__name {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 750;
  color: #1c1917;
}

.candidate-card__meta {
  margin: 0.15rem 0 0;
  font-size: 0.74rem;
  color: #a8a29e;
}

.candidate-card__badge {
  font-size: 0.72rem;
  font-weight: 750;
  color: #78716c;
  background: #fff;
  border: 1px solid #e7e5e4;
  border-radius: 999px;
  padding: 0.2rem 0.45rem;
}

.ballot-nav {
  display: flex;
  justify-content: space-between;
  gap: 0.65rem;
  margin-top: 1.15rem;
}

.ballot-nav__btn {
  border: 1px solid #e7e5e4;
  background: #fff;
  color: #1c1917;
  font-size: 0.84rem;
  font-weight: 700;
  padding: 0.7rem 1rem;
  border-radius: 0.85rem;
  cursor: pointer;
}

.ballot-nav__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ballot-nav__btn--primary {
  background: #1c1917;
  border-color: #1c1917;
  color: #fff;
}

.ballot-soft-error,
.review-error {
  margin: 0.85rem 0 0;
  font-size: 0.78rem;
  line-height: 1.45;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #f5e6d3;
  border-radius: 0.7rem;
  padding: 0.65rem 0.75rem;
}

.review-list {
  display: grid;
  gap: 0.85rem;
}

.review-item__pos {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  font-weight: 750;
  color: #78716c;
}

.review-item__empty {
  font-size: 0.84rem;
  color: #a8a29e;
}

.review-picks {
  display: grid;
  gap: 0.45rem;
}

.review-pick {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.88rem;
  font-weight: 650;
  color: #1c1917;
}

.review-pick__photo,
.review-pick__fallback {
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 999px;
  object-fit: cover;
}

.review-pick__fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e7e5e4;
  font-size: 0.62rem;
  font-weight: 800;
}

.review-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.55rem;
  margin-top: 1.15rem;
}
</style>
