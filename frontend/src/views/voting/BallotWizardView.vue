<template>
  <div class="max-w-3xl mx-auto">
      <div class="mb-6 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">Cast Your Vote</h1>
        <span class="text-sm text-gray-500">Step {{ activeStepIndex + 1 }} of {{ positions.length }}</span>
      </div>

      <!-- Simple Stepper -->
      <div v-if="positions.length === 0" class="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <p class="text-gray-500">No positions available for this election.</p>
      </div>

      <div v-else>
        <div class="flex space-x-2 mb-6 overflow-x-auto">
          <button
            v-for="(pos, idx) in positions"
            :key="pos.uuid"
            @click="activeStep = String(idx)"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
            :class="activeStepIndex === idx ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
          >
            {{ pos.title }}
          </button>
        </div>

        <!-- Current Position -->
        <div class="bg-white rounded-xl border border-gray-200 p-6">
          <h2 class="text-lg font-semibold text-gray-900">{{ currentPosition.title }}</h2>
          <p class="text-sm text-gray-500">{{ currentPosition.description }}</p>
          <p class="text-sm text-gray-400 mt-1">Select up to {{ currentPosition.max_votes_allowed }} candidate(s).</p>

          <div class="mt-4 space-y-3">
            <div
              v-for="candidate in currentPosition.candidates"
              :key="candidate.uuid"
              class="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-green-200 transition-colors cursor-pointer"
              @click="toggleCandidate(currentPosition.uuid, candidate.uuid, currentPosition.max_votes_allowed)"
              :class="{
                'border-green-500 bg-green-50': isSelected(currentPosition.uuid, candidate.uuid)
              }"
            >
              <input
                type="checkbox"
                :id="candidate.uuid"
                :checked="isSelected(currentPosition.uuid, candidate.uuid)"
                @change="toggleCandidate(currentPosition.uuid, candidate.uuid, currentPosition.max_votes_allowed)"
                class="w-4 h-4 text-green-600 rounded focus:ring-green-500"
              />
              <label :for="candidate.uuid" class="ml-3 flex-1 cursor-pointer">
                <span class="font-medium text-gray-900">{{ candidate.full_name }}</span>
                <span class="block text-sm text-gray-500">{{ candidate.department }}</span>
              </label>
              <Badge v-if="candidate.ballot_number" :value="'#' + candidate.ballot_number" severity="info" />
            </div>
          </div>

          <div class="mt-6 flex justify-between">
            <button
              @click="prevStep"
              :disabled="activeStepIndex === 0"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>
            <button
              @click="nextStep"
              class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
            >
              {{ activeStepIndex === positions.length - 1 ? 'Review & Submit' : 'Next' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Review Modal -->
      <Dialog v-model:visible="showReview" header="Review Your Vote" :modal="true" class="w-full max-w-lg">
        <div class="space-y-4">
          <div v-for="pos in positions" :key="pos.uuid" class="border-b border-gray-100 pb-3">
            <p class="font-medium text-gray-900">{{ pos.title }}</p>
            <p v-if="getSelections(pos.uuid).length === 0" class="text-sm text-gray-400">No selection</p>
            <p v-else v-for="candidate in getSelections(pos.uuid)" :key="candidate.uuid" class="text-sm text-gray-600">
              {{ candidate.full_name }}
            </p>
          </div>
        </div>
        <div class="mt-6 flex justify-end space-x-3">
          <button @click="showReview = false" class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
            Go Back
          </button>
          <button @click="submitVote" :disabled="submitting" class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50">
            {{ submitting ? 'Submitting...' : 'Submit Vote' }}
          </button>
        </div>
      </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid

const positions = ref([])
const activeStep = ref('0')
const selections = ref({}) // { position_uuid: [candidate_uuid, ...] }
const showReview = ref(false)
const submitting = ref(false)

const activeStepIndex = computed(() => parseInt(activeStep.value))
const currentPosition = computed(() => positions.value[activeStepIndex.value] || {})

const fetchBallot = async () => {
  try {
    const response = await votingApi.getBallot(electionUuid)
    positions.value = response.data.positions || []
    // Initialize selections
    positions.value.forEach(pos => {
      if (!selections.value[pos.uuid]) {
        selections.value[pos.uuid] = []
      }
    })
  } catch (error) {
    console.error('Failed to load ballot:', error)
    alert('Failed to load ballot. Please try again.')
    router.push(`/vote/${electionUuid}`)
  }
}

const isSelected = (posUuid, candidateUuid) => {
  return selections.value[posUuid]?.includes(candidateUuid) || false
}

const toggleCandidate = (posUuid, candidateUuid, maxVotes) => {
  const selected = selections.value[posUuid] || []
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
  const pos = positions.value.find(p => p.uuid === posUuid)
  if (!pos) return []
  return pos.candidates.filter(c => selectedUuids.includes(c.uuid))
}

const nextStep = () => {
  const nextIndex = activeStepIndex.value + 1
  if (nextIndex === positions.value.length) {
    // Check if all positions have at least one selection
    const allSelected = positions.value.every(pos => selections.value[pos.uuid]?.length > 0)
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
  if (prevIndex >= 0) {
    activeStep.value = String(prevIndex)
  }
}

const submitVote = async () => {
  submitting.value = true
  try {
    const payload = {
      selections: positions.value.map(pos => ({
        position_uuid: pos.uuid,
        candidate_uuids: selections.value[pos.uuid] || []
      }))
    }
    // Get SVT code from user (in a real flow, we'd store it)
    const svtCode = prompt('Enter your 6-digit SVT code again to confirm:')
    if (!svtCode || svtCode.length !== 6) {
      alert('Valid SVT code required.')
      submitting.value = false
      return
    }
    await votingApi.submitVote(electionUuid, payload.selections, svtCode)
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
