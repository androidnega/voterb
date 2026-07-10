<template>
  <div class="p-4 sm:p-6 max-w-7xl mx-auto">
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Results</h1>
        <p class="text-gray-500 text-sm mt-1">View and manage election results.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchResults" />
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Total</p>
        <p class="text-xl font-bold text-gray-900">{{ stats.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Pending</p>
        <p class="text-xl font-bold text-amber-600">{{ stats.pending }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Certified</p>
        <p class="text-xl font-bold text-blue-600">{{ stats.certified }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Published</p>
        <p class="text-xl font-bold text-emerald-600">{{ stats.published }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Election</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Turnout</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Certified By</th>
              <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in results" :key="result.uuid" class="border-b border-gray-50 hover:bg-emerald-50/30 transition-colors duration-150">
              <td class="py-3 px-4 font-medium text-gray-800">{{ result.election.title }}</td>
              <td class="py-3 px-4">
                <Badge :value="result.status" :severity="getStatusSeverity(result.status)" class="capitalize" />
              </td>
              <td class="py-3 px-4 text-gray-600">{{ result.turnout_percentage || 0 }}%</td>
              <td class="py-3 px-4 text-gray-600">{{ result.certified_by?.email || '—' }}</td>
              <td class="py-3 px-4 text-center">
                <div class="flex items-center justify-center gap-1">
                  <Button icon="pi pi-eye" size="small" severity="secondary" text rounded @click="viewResult(result.election.uuid)" tooltip="View" />
                  <Button v-if="result.status === 'generated' && isSuperAdmin" icon="pi pi-check" size="small" severity="success" text rounded @click="certifyResult(result.election.uuid)" tooltip="Certify" />
                  <Button v-if="result.status === 'certified' && isSuperAdmin" icon="pi pi-globe" size="small" severity="info" text rounded @click="publishResult(result.election.uuid)" tooltip="Publish" />
                </div>
              </td>
            </tr>
            <tr v-if="results.length === 0 && !loading">
              <td colspan="5" class="py-12 text-center text-gray-400">
                <i class="pi pi-inbox text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No results available.</p>
                <p class="text-xs text-gray-400 mt-1">Generate results after closing an election.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { resultsApi } from '@/api/results'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const router = useRouter()
const authStore = useAuthStore()
const results = ref([])
const loading = ref(false)
const isSuperAdmin = computed(() => authStore.roleName === 'super_admin' || !!authStore.user?.is_superuser)

const stats = computed(() => {
  const total = results.value.length
  const pending = results.value.filter(r => r.status === 'generated' || r.status === 'pending_certification').length
  const certified = results.value.filter(r => r.status === 'certified').length
  const published = results.value.filter(r => r.status === 'published').length
  return { total, pending, certified, published }
})

const fetchResults = async () => {
  loading.value = true
  try {
    const response = await resultsApi.list()
    results.value = response.data
  } catch (error) {
    console.error('Failed to fetch results:', error)
  } finally {
    loading.value = false
  }
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

const viewResult = (uuid) => {
  router.push(`/results/${uuid}`)
}

const certifyResult = async (uuid) => {
  if (confirm('Certify these results?')) {
    try {
      await resultsApi.certify(uuid)
      await fetchResults()
    } catch (error) {
      console.error('Failed to certify:', error)
      alert('Failed to certify. Please try again.')
    }
  }
}

const publishResult = async (uuid) => {
  if (confirm('Publish these results to students?')) {
    try {
      await resultsApi.publish(uuid)
      await fetchResults()
    } catch (error) {
      console.error('Failed to publish:', error)
      alert('Failed to publish. Please try again.')
    }
  }
}

onMounted(() => {
  fetchResults()
})
</script>
