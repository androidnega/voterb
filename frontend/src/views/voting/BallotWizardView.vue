<template>
  <div class="ballot-page">
    <header class="ballot-head">
      <div>
        <p class="ballot-eyebrow">Cast your vote</p>
        <h1 class="ballot-title">{{ electionTitle }}</h1>
      </div>
      <span v-if="positions.length" class="ballot-step">
        Step {{ activeStepIndex + 1 }} of {{ positions.length }}
      </span>
    </header>

    <div v-if="loading" class="ballot-state">
      <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
      <span>Loading ballot…</span>
    </div>

    <div v-else-if="positions.length === 0" class="ballot-state">
      <p>No positions available for this election.</p>
    </div>

    <div v-else class="ballot-body">
      <div class="ballot-tabs">
        <button
          v-for="(pos, idx) in positions"
          :key="pos.uuid"
          type="button"
          class="ballot-tab"
          :class="{ 'is-active': activeStepIndex === idx }"
          @click="activeStep = String(idx)"
        >
          {{ pos.title }}
        </button>
      </div>

      <article class="ballot-card">
        <h2 class="ballot-card__title">{{ currentPosition.title }}</h2>
        <p v-if="currentPosition.description" class="ballot-card__desc">{{ currentPosition.description }}</p>
        <p class="ballot-card__hint">
          Select up to {{ currentPosition.max_votes_allowed }} candidate{{ currentPosition.max_votes_allowed === 1 ? '' : 's' }}.
        </p>

        <div class="candidate-grid">
          <button
            v-for="candidate in currentPosition.candidates"
            :key="candidate.uuid"
            type="button"
            class="candidate-card"
            :class="{ 'is-selected': isSelected(currentPosition.uuid, candidate.uuid) }"
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
          <button type="button" class="ballot-nav__btn" :disabled="activeStepIndex === 0" @click="prevStep">
            Back
          </button>
          <button type="button" class="ballot-nav__btn ballot-nav__btn--primary" @click="nextStep">
            {{ activeStepIndex === positions.length - 1 ? 'Review & submit' : 'Next' }}
          </button>
        </div>
      </article>
    </div>

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
      <div class="review-actions">
        <button type="button" class="ballot-nav__btn" @click="showReview = false">Go back</button>
        <button type="button" class="ballot-nav__btn ballot-nav__btn--primary" :disabled="submitting" @click="submitVote">
          {{ submitting ? 'Submitting…' : 'Submit vote' }}
        </button>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'
import { resolveMediaUrl } from '@/utils/media'
import Dialog from 'primevue/dialog'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid

const electionTitle = ref('Ballot')
const positions = ref([])
const activeStep = ref('0')
const selections = ref({})
const showReview = ref(false)
const submitting = ref(false)
const loading = ref(true)
const brokenPhotos = ref(new Set())

const activeStepIndex = computed(() => parseInt(activeStep.value, 10) || 0)
const currentPosition = computed(() => positions.value[activeStepIndex.value] || { candidates: [] })

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

const fetchBallot = async () => {
  loading.value = true
  try {
    const response = await votingApi.getBallot(electionUuid)
    positions.value = response.data.positions || []
    electionTitle.value = response.data.election_title || 'Ballot'
    positions.value.forEach((pos) => {
      if (!selections.value[pos.uuid]) selections.value[pos.uuid] = []
    })
  } catch (error) {
    console.error('Failed to load ballot:', error)
    alert(error.response?.data?.error || 'Failed to load ballot. Please try again.')
    router.push(`/vote/${electionUuid}`)
  } finally {
    loading.value = false
  }
}

const isSelected = (posUuid, candidateUuid) => selections.value[posUuid]?.includes(candidateUuid) || false

const toggleCandidate = (posUuid, candidateUuid, maxVotes) => {
  const selected = [...(selections.value[posUuid] || [])]
  const index = selected.indexOf(candidateUuid)
  if (index > -1) {
    selected.splice(index, 1)
  } else {
    if (selected.length >= maxVotes) {
      alert(`You can only select up to ${maxVotes} candidate(s) for this position.`)
      return
    }
    selected.push(candidateUuid)
  }
  selections.value = { ...selections.value, [posUuid]: selected }
}

const getSelections = (posUuid) => {
  const selectedUuids = selections.value[posUuid] || []
  const pos = positions.value.find((p) => p.uuid === posUuid)
  if (!pos) return []
  return pos.candidates.filter((c) => selectedUuids.includes(c.uuid))
}

const nextStep = () => {
  const nextIndex = activeStepIndex.value + 1
  if (nextIndex === positions.value.length) {
    const allSelected = positions.value.every((pos) => selections.value[pos.uuid]?.length > 0)
    if (!allSelected) {
      alert('Please select at least one candidate for each position.')
      return
    }
    showReview.value = true
  } else {
    activeStep.value = String(nextIndex)
  }
}

const prevStep = () => {
  const prevIndex = activeStepIndex.value - 1
  if (prevIndex >= 0) activeStep.value = String(prevIndex)
}

const submitVote = async () => {
  submitting.value = true
  try {
    const payload = {
      selections: positions.value.map((pos) => ({
        position_uuid: pos.uuid,
        candidate_uuids: selections.value[pos.uuid] || [],
      })),
    }
    const svtCode = sessionStorage.getItem(`svt:${electionUuid}`)
    if (!svtCode || !/^v-[a-z]{3}-\d{4}$/i.test(svtCode)) {
      alert('Your secure session expired. Please re-enter your SVT.')
      router.push(`/vote/${electionUuid}`)
      return
    }
    await votingApi.submitVote(electionUuid, payload.selections, svtCode)
    sessionStorage.removeItem(`svt:${electionUuid}`)
    router.push(`/vote/${electionUuid}/confirmation`)
  } catch (error) {
    console.error('Submission failed:', error)
    alert(error.response?.data?.error || 'Failed to submit vote. Please try again.')
  } finally {
    submitting.value = false
    showReview.value = false
  }
}

onMounted(() => {
  fetchBallot()
})
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
}

.ballot-tab.is-active {
  background: #1c1917;
  color: #fff;
}

.ballot-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.35rem;
  padding: 1.2rem 1.15rem 1.15rem;
  box-shadow: 0 8px 24px rgba(28, 25, 23, 0.03);
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

.candidate-card:hover {
  border-color: #d6d3d1;
  transform: translateY(-1px);
}

.candidate-card.is-selected {
  border-color: #0f766e;
  background: #ecfdf5;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1);
}

.candidate-card__photo-wrap {
  position: relative;
  width: 3.6rem;
  height: 3.6rem;
  flex-shrink: 0;
}

.candidate-card__photo,
.candidate-card__fallback {
  width: 3.6rem;
  height: 3.6rem;
  border-radius: 9999px;
  object-fit: cover;
  display: block;
  background: #e7e5e4;
}

.candidate-card__fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 800;
  color: #57534e;
  letter-spacing: 0.04em;
}

.candidate-card__check {
  position: absolute;
  right: -0.1rem;
  bottom: -0.1rem;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 9999px;
  background: #0f766e;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.55rem;
  border: 2px solid #fff;
}

.candidate-card__name {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 800;
  color: #1c1917;
}

.candidate-card__meta {
  margin: 0.2rem 0 0;
  font-size: 0.75rem;
  color: #78716c;
}

.candidate-card__badge {
  font-size: 0.72rem;
  font-weight: 800;
  color: #0f766e;
  background: #fff;
  border: 1px solid #bbf7d0;
  border-radius: 9999px;
  padding: 0.25rem 0.5rem;
}

.ballot-nav {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1.15rem;
}

.ballot-nav__btn {
  border: 1px solid #e7e5e4;
  background: #fff;
  color: #44403c;
  border-radius: 0.9rem;
  padding: 0.7rem 1rem;
  font-size: 0.84rem;
  font-weight: 700;
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

.review-list {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.review-item__pos {
  margin: 0 0 0.45rem;
  font-weight: 800;
  color: #1c1917;
}

.review-item__empty {
  font-size: 0.82rem;
  color: #a8a29e;
}

.review-picks {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.review-pick {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.86rem;
  color: #44403c;
}

.review-pick__photo,
.review-pick__fallback {
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 9999px;
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
