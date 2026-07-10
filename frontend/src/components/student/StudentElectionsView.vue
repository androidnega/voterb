<template>
  <div>
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Eligible Elections</h2>
      <p class="text-sm text-gray-500 mt-1">Elections you can vote in right now.</p>
    </div>

    <div v-if="loading" class="text-center py-12">
      <i class="pi pi-spin pi-spinner text-3xl text-emerald-600"></i>
      <p class="text-gray-500 mt-2">Loading elections...</p>
    </div>

    <div v-else-if="error" class="text-center py-12 bg-red-50 rounded-xl border border-red-200 p-6">
      <p class="text-red-600">{{ error }}</p>
      <button
        @click="fetchEligibleElections"
        class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
      >
        Retry
      </button>
    </div>

    <div v-else-if="elections.length === 0" class="text-center py-12 bg-white rounded-xl border border-gray-200">
      <i class="pi pi-inbox text-4xl text-gray-300 block mb-3"></i>
      <p class="text-gray-500 text-sm">You are not eligible for any active elections right now.</p>
      <p class="text-gray-400 text-xs mt-1">Check back later or contact your election officer.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="election in elections"
        :key="election.uuid"
        class="bg-white rounded-xl border border-gray-200 hover:border-emerald-200 transition-colors duration-200 p-6 flex flex-col"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="text-lg font-semibold text-gray-900 truncate">{{ election.title }}</h3>
            <p class="text-sm text-gray-500 mt-1 line-clamp-2">
              {{ election.description || 'No description provided.' }}
            </p>
          </div>
          <span class="px-2 py-1 text-xs rounded-full bg-emerald-100 text-emerald-800 capitalize shrink-0">
            {{ election.status }}
          </span>
        </div>

        <div class="mt-4 space-y-1 text-sm text-gray-600">
          <div class="flex items-center">
            <i class="pi pi-calendar mr-2 text-gray-400"></i>
            {{ formatDate(election.start_date) }} – {{ formatDate(election.end_date) }}
          </div>
          <div class="flex items-center">
            <i class="pi pi-users mr-2 text-gray-400"></i>
            {{ election.voter_count || 0 }} eligible voters
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-gray-100 flex justify-end">
          <button
            @click="startVoting(election.uuid)"
            :disabled="election.status !== 'open'"
            class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Vote Now
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'

const router = useRouter()
const elections = ref([])
const loading = ref(true)
const error = ref(null)

const formatDate = (date) => {
  if (!date) return 'TBA'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const fetchEligibleElections = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await votingApi.getEligibleElections()
    elections.value = response.data || []
  } catch (err) {
    console.error('Failed to fetch elections:', err)
    error.value = err.response?.data?.error || 'Failed to load elections. Please try again.'
  } finally {
    loading.value = false
  }
}

const startVoting = (electionUuid) => {
  router.push(`/vote/${electionUuid}`)
}

onMounted(() => {
  fetchEligibleElections()
})
</script>
