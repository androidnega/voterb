<template>
  <div v-if="result" class="max-w-4xl mx-auto">
    <!-- Back button -->
    <button 
      @click="$router.push('/student')" 
      class="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
    >
      <i class="fas fa-arrow-left"></i> Back to Dashboard
    </button>

    <!-- Result Header -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-6">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ result.election.title }}</h1>
          <p class="text-gray-500 text-sm mt-1">{{ result.election.description }}</p>
        </div>
        <Badge value="Official Results" severity="success" class="text-sm" />
      </div>
      <div class="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-600">
        <span><i class="fas fa-calendar-check mr-1"></i> Published: {{ formatDate(result.published_at) }}</span>
        <span><i class="fas fa-percentage mr-1"></i> Turnout: {{ result.turnout_percentage || 0 }}%</span>
        <span><i class="fas fa-users mr-1"></i> Verified by: {{ result.certified_by?.email || 'Election Commission' }}</span>
      </div>
    </div>

    <!-- Positions -->
    <div class="space-y-6">
      <div v-for="pos in standings" :key="pos.uuid" class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">{{ pos.title }}</h2>
          <p class="text-xs text-gray-500">Max votes: {{ pos.max_votes_allowed }}</p>
        </div>
        <div class="divide-y divide-gray-100">
          <!-- Winner badge -->
          <div v-for="(candidate, idx) in pos.candidates" :key="candidate.uuid" 
            class="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            :class="{ 'bg-emerald-50': candidate.rank === 1 }"
          >
            <div class="flex items-center gap-4">
              <span class="text-sm font-medium text-gray-400 w-6">{{ candidate.rank }}</span>
              <div>
                <span class="font-medium text-gray-900">{{ candidate.full_name }}</span>
                <span class="text-xs text-gray-400 ml-2">{{ candidate.department }}</span>
                <span v-if="candidate.rank === 1" class="ml-2 text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Winner</span>
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

    <!-- Integrity Seal -->
    <div class="mt-6 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center gap-3">
        <i class="fas fa-shield-alt text-emerald-600 text-xl"></i>
        <div>
          <p class="text-sm font-medium text-gray-900">Verified by VoterB Integrity System</p>
          <p class="text-xs text-gray-400">Result hash: {{ result.result_hash?.slice(0, 20) }}...</p>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">
    <i class="fas fa-spinner fa-spin text-2xl"></i>
    <p class="mt-2">Loading results...</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { resultsApi } from '@/api/results'
import Badge from 'primevue/badge'

const route = useRoute()
const result = ref(null)

const standings = computed(() => {
  if (!result.value?.standings) return []
  return result.value.standings.positions || []
})

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const fetchResult = async () => {
  try {
    const response = await resultsApi.getPublishedDetail(route.params.uuid)
    result.value = response.data
  } catch (error) {
    console.error('Failed to fetch result:', error)
  }
}

onMounted(() => {
  fetchResult()
})
</script>
