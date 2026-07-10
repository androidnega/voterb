<template>
  <div>
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Published Results</h2>
      <p class="text-sm text-gray-500 mt-1">View official election results from certified elections.</p>
    </div>

    <div v-if="loading" class="text-center py-12">
      <i class="fas fa-spinner fa-spin text-3xl text-emerald-600"></i>
      <p class="text-gray-500 mt-2">Loading results...</p>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
      {{ error }}
    </div>

    <div v-else-if="results.length === 0" class="text-center py-12 bg-white rounded-xl border border-gray-200">
      <i class="fas fa-inbox text-4xl text-gray-300 block mb-3"></i>
      <p class="text-gray-500 text-sm">No published results available.</p>
      <p class="text-xs text-gray-400 mt-1">Check back later after elections are certified and published.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div 
        v-for="result in results" 
        :key="result.uuid"
        class="bg-white rounded-xl border border-gray-200 hover:border-emerald-200 hover:shadow-md transition-all duration-200 p-6 cursor-pointer"
        @click="viewResult(result.election.uuid)"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-semibold text-gray-900 truncate">{{ result.election.title }}</h3>
            <p class="text-sm text-gray-500 truncate">{{ result.election.description || 'No description' }}</p>
          </div>
          <Badge value="Published" severity="success" class="flex-shrink-0 ml-2" />
        </div>

        <div class="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-600">
          <span><i class="fas fa-users mr-1 text-gray-400"></i>Turnout: {{ result.turnout_percentage || 0 }}%</span>
          <span><i class="fas fa-calendar-check mr-1 text-gray-400"></i>{{ formatDate(result.published_at) }}</span>
        </div>

        <div class="mt-4 pt-4 border-t border-gray-100 flex justify-end">
          <span class="text-sm text-emerald-600 font-medium hover:text-emerald-700">View Results →</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { resultsApi } from '@/api/results'
import Badge from 'primevue/badge'

const router = useRouter()
const results = ref([])
const loading = ref(true)
const error = ref(null)

const fetchPublishedResults = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await resultsApi.getPublished()
    results.value = response.data
  } catch (err) {
    console.error('Failed to fetch published results:', err)
    error.value = 'Could not load results. Please try again later.'
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const viewResult = (uuid) => {
  router.push(`/student/results/${uuid}`)
}

onMounted(() => {
  fetchPublishedResults()
})
</script>
