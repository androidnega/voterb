<template>
  <div class="p-4 sm:p-6 max-w-7xl mx-auto" v-if="election">
    <!-- Header -->
    <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div>
        <div class="flex items-center gap-3 flex-wrap">
          <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">{{ election.title }}</h1>
          <Badge :value="election.status" :severity="getStatusSeverity(election.status)" class="capitalize" />
          <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{{ election.status }}</span>
        </div>
        <p class="text-gray-500 text-sm mt-1">{{ election.description || 'No description provided.' }}</p>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap gap-2">
        <!-- Back Button -->
        <Button 
          label="Back" 
          icon="pi pi-arrow-left" 
          severity="secondary" 
          size="small"
          class="!bg-gray-200 !text-gray-700 hover:!bg-gray-300 !border-gray-300"
          @click="$router.push('/elections')" 
        />

        <!-- Schedule Button -->
        <Button 
          v-if="election.status === 'draft'" 
          label="Schedule" 
          icon="pi pi-calendar-plus" 
          severity="info" 
          size="small"
          class="!bg-blue-600 !text-white hover:!bg-blue-700 !border-blue-600"
          @click="updateStatus('scheduled')" 
        />

        <!-- Open Button -->
        <Button 
          v-if="election.status === 'scheduled'" 
          label="Open" 
          icon="pi pi-play" 
          severity="success" 
          size="small"
          class="!bg-emerald-600 !text-white hover:!bg-emerald-700 !border-emerald-600"
          @click="openElection" 
        />

        <!-- Close Button -->
        <Button 
          v-if="election.status === 'open' || election.status === 'paused'" 
          label="Close Election" 
          icon="pi pi-stop" 
          severity="danger" 
          size="small"
          @click="closeElection" 
          class="!bg-red-600 !text-white hover:!bg-red-700 !border-red-600 !shadow-sm"
        />

        <!-- Generate Results Button -->
        <Button 
          v-if="election.status === 'closed' && !resultExists" 
          label="Generate Results" 
          icon="pi pi-cog" 
          severity="info" 
          size="small"
          @click="generateResults" 
          :loading="isGenerating"
          class="!bg-indigo-600 !text-white hover:!bg-indigo-700 !border-indigo-600 !shadow-sm"
        />

        <!-- View Results Button -->
        <Button 
          v-if="resultExists" 
          label="View Results" 
          icon="pi pi-chart-bar" 
          severity="success" 
          size="small"
          @click="$router.push(`/results/${election.uuid}`)"
          class="!bg-emerald-600 !text-white hover:!bg-emerald-700 !border-emerald-600 !shadow-sm"
        />

        <!-- Debug: Show status info -->
        <span class="text-xs text-gray-400 self-center hidden lg:inline-block">
          Status: {{ election.status }}
        </span>
      </div>
    </div>

    <!-- Info Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-3 shadow-sm hover:shadow transition-shadow duration-200">
        <div class="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
          <i class="pi pi-calendar text-blue-600 text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-gray-500">Created</p>
          <p class="text-sm font-medium text-gray-900">{{ formatDate(election.created_at) }}</p>
        </div>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-3 shadow-sm hover:shadow transition-shadow duration-200">
        <div class="w-10 h-10 bg-green-50 rounded-full flex items-center justify-center">
          <i class="pi pi-tag text-green-600 text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-gray-500">Type</p>
          <p class="text-sm font-medium text-gray-900 capitalize">{{ election.election_type }}</p>
        </div>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-3 shadow-sm hover:shadow transition-shadow duration-200">
        <div class="w-10 h-10 bg-purple-50 rounded-full flex items-center justify-center">
          <i class="pi pi-users text-purple-600 text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-gray-500">Voters</p>
          <p class="text-sm font-medium text-gray-900">{{ voterCount }}</p>
        </div>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-3 shadow-sm hover:shadow transition-shadow duration-200">
        <div class="w-10 h-10 bg-orange-50 rounded-full flex items-center justify-center">
          <i class="pi pi-clock text-orange-600 text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-gray-500">Dates</p>
          <p class="text-sm font-medium text-gray-900">{{ formatDate(election.start_date) }} – {{ formatDate(election.end_date) }}</p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="border-b border-gray-200 px-4">
        <div class="flex -mb-px">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            class="py-3 px-4 text-sm font-medium transition-colors duration-200 border-b-2"
            :class="activeTab === tab.key 
              ? 'border-emerald-600 text-emerald-700' 
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
          >
            <i :class="tab.icon" class="mr-2"></i>
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div class="p-4 sm:p-6">
        <!-- Positions -->
        <div v-if="activeTab === 'positions'">
          <div class="flex justify-end mb-4">
            <Button 
              label="Add Position" 
              icon="pi pi-plus" 
              size="small" 
              @click="showPositionDialog = true" 
              class="!bg-emerald-600 !text-white hover:!bg-emerald-700 !border-emerald-600 !shadow-sm"
            />
          </div>
          <DataTable :value="positions" :loading="loadingPositions" stripedRows responsiveLayout="scroll" size="small">
            <Column field="title" header="Title" sortable></Column>
            <Column field="max_votes_allowed" header="Max Votes" style="width:100px"></Column>
            <Column field="display_order" header="Order" style="width:80px"></Column>
            <Column field="is_active" header="Active" style="width:80px">
              <template #body="{ data }">
                <i :class="data.is_active ? 'pi pi-check-circle text-emerald-500' : 'pi pi-times-circle text-red-500'"></i>
              </template>
            </Column>
            <template #empty>
              <div class="text-center py-8 text-gray-500">No positions added yet.</div>
            </template>
          </DataTable>
        </div>

        <!-- Candidates -->
        <div v-if="activeTab === 'candidates'">
          <CandidateManager :election-uuid="route.params.uuid" />
        </div>

        <!-- Voters -->
        <div v-if="activeTab === 'voters'">
          <VoterManager :election-uuid="route.params.uuid" />
        </div>
      </div>
    </div>

    <!-- Add Position Dialog -->
    <Dialog v-model:visible="showPositionDialog" header="Add Position" :modal="true" class="w-full max-w-md">
      <form @submit.prevent="createPosition" class="p-1">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <InputText v-model="newPosition.title" class="w-full" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Max Votes Allowed</label>
            <InputNumber v-model="newPosition.max_votes_allowed" class="w-full" :min="1" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Display Order</label>
            <InputNumber v-model="newPosition.display_order" class="w-full" :min="0" />
          </div>
          <div class="flex items-center gap-2">
            <Checkbox v-model="newPosition.is_active" binary />
            <label class="text-sm text-gray-700">Active</label>
          </div>
          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button label="Cancel" severity="secondary" @click="showPositionDialog = false" class="!border-gray-300" />
            <Button label="Create" type="submit" :loading="loadingPosition" class="!bg-emerald-600 !text-white hover:!bg-emerald-700 !border-emerald-600" />
          </div>
        </div>
      </form>
    </Dialog>
  </div>
  <div v-else class="p-6 text-center text-gray-500">
    <i class="pi pi-spin pi-spinner text-2xl"></i>
    <p class="mt-2">Loading election...</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { electionApi } from '@/api/elections'
import { resultsApi } from '@/api/results'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import CandidateManager from '@/components/elections/CandidateManager.vue'
import VoterManager from '@/components/elections/VoterManager.vue'

const route = useRoute()
const router = useRouter()

const election = ref(null)
const positions = ref([])
const loadingPositions = ref(false)
const showPositionDialog = ref(false)
const loadingPosition = ref(false)
const activeTab = ref('positions')
const resultExists = ref(false)
const isGenerating = ref(false)

const newPosition = ref({
  title: '',
  max_votes_allowed: 1,
  display_order: 0,
  is_active: true
})

const tabs = [
  { key: 'positions', label: 'Positions', icon: 'pi pi-list' },
  { key: 'candidates', label: 'Candidates', icon: 'pi pi-users' },
  { key: 'voters', label: 'Voters', icon: 'pi pi-user-plus' }
]

const voterCount = computed(() => 0) // placeholder

const fetchElection = async () => {
  try {
    const response = await electionApi.get(route.params.uuid)
    election.value = response.data
    await checkResultExists()
  } catch (error) {
    console.error('Failed to fetch election:', error)
    router.push('/elections')
  }
}

const fetchPositions = async () => {
  loadingPositions.value = true
  try {
    const response = await electionApi.getPositions(route.params.uuid)
    positions.value = response.data
  } catch (error) {
    console.error('Failed to fetch positions:', error)
  } finally {
    loadingPositions.value = false
  }
}

const checkResultExists = async () => {
  try {
    await resultsApi.preview(route.params.uuid)
    resultExists.value = true
  } catch (error) {
    resultExists.value = false
  }
}

const formatDate = (date) => {
  if (!date) return 'TBA'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
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

const updateStatus = async (newStatus) => {
  try {
    await electionApi.update(election.value.uuid, { status: newStatus })
    await fetchElection()
  } catch (error) {
    console.error('Failed to update status:', error)
    alert('Failed to update status. Please try again.')
  }
}

const openElection = async () => {
  try {
    await electionApi.open(election.value.uuid)
    await fetchElection()
  } catch (error) {
    console.error('Failed to open election:', error)
    alert('Failed to open election. Please check readiness.')
  }
}

const closeElection = async () => {
  if (confirm('Are you sure you want to close this election?')) {
    try {
      await electionApi.close(election.value.uuid)
      await fetchElection()
    } catch (error) {
      console.error('Failed to close election:', error)
      alert('Failed to close election. Please try again.')
    }
  }
}

const generateResults = async () => {
  if (!confirm('Generate results for this election?')) return
  
  isGenerating.value = true
  try {
    await resultsApi.generate(route.params.uuid)
    resultExists.value = true
    router.push(`/results/${route.params.uuid}`)
  } catch (error) {
    console.error('Failed to generate results:', error)
    alert('Failed to generate results. Please try again.')
  } finally {
    isGenerating.value = false
  }
}

const createPosition = async () => {
  loadingPosition.value = true
  try {
    await electionApi.createPosition(route.params.uuid, newPosition.value)
    showPositionDialog.value = false
    newPosition.value = { title: '', max_votes_allowed: 1, display_order: 0, is_active: true }
    await fetchPositions()
  } catch (error) {
    console.error('Failed to create position:', error)
    alert('Failed to create position. Please try again.')
  } finally {
    loadingPosition.value = false
  }
}

onMounted(() => {
  fetchElection()
  fetchPositions()
})
</script>

<style scoped>
button {
  background: transparent;
  cursor: pointer;
  font-size: 0.875rem;
}
button:focus-visible {
  outline: 2px solid #0f7d3e;
  outline-offset: -2px;
  border-radius: 0;
}
.pi {
  font-size: 0.875rem;
}
.p-button {
  color: inherit;
}
</style>
