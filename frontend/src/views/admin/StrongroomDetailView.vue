<template>
  <div v-if="election" class="max-w-4xl mx-auto">
    <div class="flex items-center gap-4 mb-6">
      <Button icon="pi pi-arrow-left" severity="secondary" text @click="$router.push('/strongroom')" />
      <h1 class="text-2xl font-bold text-gray-900">{{ election.title }}</h1>
      <Badge :value="election.status" :severity="getStatusSeverity(election.status)" />
    </div>

    <!-- Election Seal -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-6">
      <h2 class="text-sm font-semibold text-gray-900 mb-2">Election Seal</h2>
      <div v-if="election.election_seal" class="bg-gray-50 rounded-lg p-4 font-mono text-sm break-all">
        {{ election.election_seal.seal_hash }}
        <span class="ml-4 text-xs text-gray-500">Status: {{ election.election_seal.status }}</span>
      </div>
      <div v-else class="text-gray-400 text-sm">No election seal generated yet.</div>
    </div>

    <!-- Ballot Seals -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-6">
      <h2 class="text-sm font-semibold text-gray-900 mb-2">Ballot Seals</h2>
      <div v-if="election.ballot_seals && election.ballot_seals.length > 0" class="space-y-2 max-h-60 overflow-y-auto">
        <div v-for="seal in election.ballot_seals" :key="seal.uuid" class="bg-gray-50 rounded-lg p-3 text-xs font-mono break-all">
          {{ seal.seal_hash }}
          <span class="ml-4 text-gray-500">({{ seal.status }})</span>
        </div>
      </div>
      <div v-else class="text-gray-400 text-sm">No ballot seals recorded.</div>
    </div>

    <!-- Custody Records -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <h2 class="text-sm font-semibold text-gray-900 mb-2">Custody Timeline</h2>
      <div v-if="election.custody_records && election.custody_records.length > 0" class="space-y-3">
        <div v-for="record in election.custody_records" :key="record.uuid" class="flex items-start gap-3 border-b border-gray-100 pb-3 last:border-0">
          <div class="w-2 h-2 mt-2 bg-emerald-500 rounded-full flex-shrink-0"></div>
          <div>
            <p class="text-sm text-gray-800">{{ record.action }}</p>
            <div class="text-xs text-gray-400 flex gap-2">
              <span>by {{ record.actor_email || 'System' }}</span>
              <span>•</span>
              <span>{{ formatDate(record.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-gray-400 text-sm">No custody records.</div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">
    <i class="fas fa-spinner fa-spin text-2xl"></i>
    <p class="mt-2">Loading strongroom data...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { strongroomApi } from '@/api/strongroom'
import Button from 'primevue/button'
import Badge from 'primevue/badge'

const route = useRoute()
const router = useRouter()
const election = ref(null)

const fetchDetail = async () => {
  try {
    const response = await strongroomApi.detail(route.params.uuid)
    election.value = response.data
  } catch (error) {
    console.error('Failed to fetch strongroom detail:', error)
    router.push('/strongroom')
  }
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

onMounted(fetchDetail)
</script>
