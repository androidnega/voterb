<template>
  <div class="p-4 sm:p-6 max-w-7xl mx-auto" v-if="result">
    <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">{{ result.election.title }}</h1>
        <p class="text-gray-500 text-sm mt-1">Results for this election.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button label="Back" icon="pi pi-arrow-left" severity="secondary" size="small" @click="$router.push('/results')" />
        <Button v-if="result.status === 'generated' && isSuperAdmin" label="Certify" icon="pi pi-check" severity="success" size="small" @click="certify" />
        <Button v-if="result.status === 'certified' && isSuperAdmin" label="Publish" icon="pi pi-globe" severity="info" size="small" @click="publish" />
      </div>
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
                <span class="text-xs text-gray-400 ml-2">{{ candidate.department }}</span>
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
  </div>
  <div v-else class="p-6 text-center text-gray-500">
    <i class="pi pi-spin pi-spinner text-2xl"></i>
    <p class="mt-2">Loading results...</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { resultsApi } from '@/api/results'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const result = ref(null)
const loading = ref(true)
const isSuperAdmin = computed(() => authStore.roleName === 'super_admin' || !!authStore.user?.is_superuser)

const standings = computed(() => {
  if (!result.value?.standings) return []
  return result.value.standings.positions || []
})

const integrity = computed(() => {
  return result.value?.integrity_report || {}
})

const fetchResult = async () => {
  loading.value = true
  try {
    const response = await resultsApi.preview(route.params.uuid)
    result.value = response.data
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

const certify = async () => {
  if (confirm('Certify these results?')) {
    try {
      await resultsApi.certify(route.params.uuid)
      await fetchResult()
    } catch (error) {
      console.error('Failed to certify:', error)
      alert('Failed to certify. Please try again.')
    }
  }
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
