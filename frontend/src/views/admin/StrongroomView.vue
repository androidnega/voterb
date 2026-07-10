<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Strongroom</h1>
        <p class="text-gray-500 text-sm mt-1">Integrity vault – view election seals and custody records.</p>
      </div>
      <Button label="Refresh" icon="pi pi-refresh" severity="secondary" size="small" @click="fetchData" />
    </div>

    <!-- Elections List -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Election</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Election Seal</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Ballot Seals</th>
              <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="election in elections" :key="election.uuid" class="border-b border-gray-50 hover:bg-emerald-50/30 transition-colors duration-150">
              <td class="py-3 px-4 font-medium text-gray-800">{{ election.title }}</td>
              <td class="py-3 px-4">
                <Badge :value="election.status" :severity="getStatusSeverity(election.status)" class="capitalize" />
              </td>
              <td class="py-3 px-4">
                <span v-if="election.election_seal" class="text-emerald-600">
                  <i class="fas fa-shield-alt"></i> {{ election.election_seal.seal_hash.slice(0, 16) }}...
                </span>
                <span v-else class="text-gray-400">Not generated</span>
              </td>
              <td class="py-3 px-4 text-gray-600">{{ election.ballot_seals?.length || 0 }}</td>
              <td class="py-3 px-4 text-center">
                <Button icon="pi pi-eye" size="small" severity="secondary" text rounded @click="viewElection(election.uuid)" tooltip="View Details" />
                <Button icon="pi pi-lock" size="small" severity="warning" text rounded @click="lockElection(election.uuid)" tooltip="Lock Election" />
              </td>
            </tr>
            <tr v-if="elections.length === 0 && !loading">
              <td colspan="5" class="py-12 text-center text-gray-400">
                <i class="fas fa-inbox text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No elections found.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { strongroomApi } from '@/api/strongroom'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const router = useRouter()
const elections = ref([])
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const response = await strongroomApi.list()
    elections.value = response.data
  } catch (error) {
    console.error('Failed to fetch strongroom data:', error)
  } finally {
    loading.value = false
  }
}

const getStatusSeverity = (status) => {
  const map = {
    draft: 'secondary',
    scheduled: 'info',
    open: 'success',
    paused: 'warning',
    closed: 'danger',
    archived: 'danger'
  }
  return map[status] || 'secondary'
}

const viewElection = (uuid) => {
  router.push(`/strongroom/${uuid}`)
}

const lockElection = async (uuid) => {
  if (confirm('Lock this election for custody?')) {
    try {
      await strongroomApi.lock(uuid)
      await fetchData()
    } catch (error) {
      console.error('Failed to lock election:', error)
      alert('Failed to lock election. Please try again.')
    }
  }
}

onMounted(fetchData)
</script>
