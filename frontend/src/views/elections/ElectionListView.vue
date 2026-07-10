<template>
  <div class="p-4 sm:p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">Elections</h1>
        <p class="text-gray-500 text-sm mt-1">Manage and monitor all elections across your institution.</p>
      </div>
      <Button label="New Election" icon="pi pi-plus" @click="showCreateDialog = true" class="shadow-sm" />
    </div>

    <!-- Stats Cards (compact) -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Total</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">{{ stats.total }}</p>
          </div>
          <div class="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-calendar text-indigo-500 text-lg"></i>
          </div>
        </div>
        <div class="mt-3 h-1 w-full bg-indigo-100 rounded-full overflow-hidden">
          <div class="h-full bg-indigo-500 rounded-full" style="width: 100%"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Active</p>
            <p class="text-2xl font-bold text-emerald-600 mt-1">{{ stats.active }}</p>
          </div>
          <div class="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-check-circle text-emerald-500 text-lg"></i>
          </div>
        </div>
        <div class="mt-3 h-1 w-full bg-emerald-100 rounded-full overflow-hidden">
          <div class="h-full bg-emerald-500 rounded-full" :style="{ width: stats.total ? (stats.active/stats.total*100)+'%' : '0%' }"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Scheduled</p>
            <p class="text-2xl font-bold text-amber-600 mt-1">{{ stats.scheduled }}</p>
          </div>
          <div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-clock text-amber-500 text-lg"></i>
          </div>
        </div>
        <div class="mt-3 h-1 w-full bg-amber-100 rounded-full overflow-hidden">
          <div class="h-full bg-amber-500 rounded-full" :style="{ width: stats.total ? (stats.scheduled/stats.total*100)+'%' : '0%' }"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Closed</p>
            <p class="text-2xl font-bold text-slate-600 mt-1">{{ stats.closed }}</p>
          </div>
          <div class="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center">
            <i class="pi pi-archive text-slate-500 text-lg"></i>
          </div>
        </div>
        <div class="mt-3 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
          <div class="h-full bg-slate-500 rounded-full" :style="{ width: stats.total ? (stats.closed/stats.total*100)+'%' : '0%' }"></div>
        </div>
      </div>
    </div>

    <!-- Search & Actions -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <div class="relative flex-1 min-w-[200px]">
        <i class="pi pi-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
        <input 
          v-model="searchQuery" 
          type="text"
          placeholder="Search by title or description..." 
          class="w-full pl-9 pr-10 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-gray-50 hover:bg-white transition-colors duration-200 text-sm"
          @input="filterElections"
        />
        <i 
          v-if="searchQuery" 
          class="pi pi-times absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 cursor-pointer hover:text-gray-600 transition-colors"
          @click="clearSearch"
        ></i>
      </div>
      <Button 
        label="Refresh" 
        icon="pi pi-refresh" 
        severity="secondary" 
        size="small" 
        @click="fetchElections" 
        class="text-sm border-gray-200"
      />
    </div>

    <!-- Results Count -->
    <div class="flex items-center justify-between text-sm text-gray-500 mb-3">
      <span>{{ filteredElections.length }} election{{ filteredElections.length !== 1 ? 's' : '' }} found</span>
      <span v-if="searchQuery" class="text-xs text-gray-400">Filtered by "{{ searchQuery }}"</span>
    </div>

    <!-- Premium Table -->
    <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm hidden sm:block">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="text-left py-4 px-6 font-semibold text-gray-600 text-xs uppercase tracking-wider">Title</th>
            <th class="text-left py-4 px-6 font-semibold text-gray-600 text-xs uppercase tracking-wider">Type</th>
            <th class="text-left py-4 px-6 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
            <th class="text-left py-4 px-6 font-semibold text-gray-600 text-xs uppercase tracking-wider">Start Date</th>
            <th class="text-left py-4 px-6 font-semibold text-gray-600 text-xs uppercase tracking-wider">End Date</th>
            <th class="text-center py-4 px-6 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="election in filteredElections" 
            :key="election.uuid"
            class="border-b border-gray-50 hover:bg-emerald-50/30 transition-colors duration-150"
          >
            <td class="py-4 px-6">
              <div class="font-medium text-gray-800">{{ election.title }}</div>
              <div class="text-xs text-gray-400 truncate max-w-xs">{{ election.description || '—' }}</div>
            </td>
            <td class="py-4 px-6">
              <Badge :value="election.election_type" severity="info" class="capitalize" />
            </td>
            <td class="py-4 px-6">
              <Badge :value="election.status" :severity="getStatusSeverity(election.status)" class="capitalize" />
            </td>
            <td class="py-4 px-6 text-gray-600">{{ formatDate(election.start_date) }}</td>
            <td class="py-4 px-6 text-gray-600">{{ formatDate(election.end_date) }}</td>
            <td class="py-4 px-6 text-center">
              <div class="flex items-center justify-center gap-1">
                <Button 
                  icon="pi pi-eye" 
                  size="small" 
                  severity="secondary" 
                  text 
                  rounded
                  @click="viewElection(election.uuid)" 
                  tooltip="View Details"
                />
                <Button 
                  icon="pi pi-pencil" 
                  size="small" 
                  severity="secondary" 
                  text 
                  rounded
                  @click="editElection(election.uuid)" 
                  tooltip="Edit"
                />
                <Button 
                  icon="pi pi-trash" 
                  size="small" 
                  severity="danger" 
                  text 
                  rounded
                  @click="confirmDelete(election)" 
                  tooltip="Delete"
                />
              </div>
            </td>
          </tr>
          <tr v-if="filteredElections.length === 0 && !loading">
            <td colspan="6" class="py-16 text-center text-gray-400">
              <i class="pi pi-inbox text-4xl block mb-3 text-gray-200"></i>
              No elections found. Click "New Election" to get started.
            </td>
          </tr>
        </tbody>
      </table>
      <!-- Pagination (simple) -->
      <div class="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-gray-50/50 text-sm">
        <span class="text-gray-500">{{ filteredElections.length }} items</span>
        <div class="flex items-center gap-2">
          <button class="px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-100 disabled:opacity-50" disabled>
            <i class="pi pi-chevron-left text-xs"></i>
          </button>
          <span class="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg font-medium">1</span>
          <button class="px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-100 disabled:opacity-50" disabled>
            <i class="pi pi-chevron-right text-xs"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Cards -->
    <div class="sm:hidden">
      <div v-if="filteredElections.length === 0 && !loading" class="text-center py-12">
        <i class="pi pi-inbox text-4xl text-gray-300 block mb-3"></i>
        <p class="text-gray-500 text-sm">No elections found.</p>
      </div>
      <div v-for="election in filteredElections" :key="election.uuid" class="bg-white rounded-xl border border-gray-100 p-4 mb-3 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="font-semibold text-gray-800 truncate">{{ election.title }}</div>
            <div class="text-xs text-gray-400 truncate">{{ election.description || '—' }}</div>
          </div>
          <Badge :value="election.status" :severity="getStatusSeverity(election.status)" class="capitalize ml-2 flex-shrink-0" />
        </div>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
          <span><span class="font-medium">Type:</span> {{ election.election_type }}</span>
          <span><span class="font-medium">Start:</span> {{ formatDate(election.start_date) }}</span>
          <span><span class="font-medium">End:</span> {{ formatDate(election.end_date) }}</span>
        </div>
        <div class="flex items-center gap-2 mt-3">
          <Button icon="pi pi-eye" size="small" severity="secondary" text @click="viewElection(election.uuid)" />
          <Button icon="pi pi-pencil" size="small" severity="secondary" text @click="editElection(election.uuid)" />
          <Button icon="pi pi-trash" size="small" severity="danger" text @click="confirmDelete(election)" />
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <i class="pi pi-spin pi-spinner text-2xl text-emerald-600"></i>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreateDialog" header="Create New Election" :modal="true" class="w-full max-w-lg">
      <CreateElectionForm @success="onElectionCreated" @cancel="showCreateDialog = false" />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { electionApi } from '@/api/elections'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import CreateElectionForm from '@/components/elections/CreateElectionForm.vue'

const router = useRouter()
const elections = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const searchQuery = ref('')

const stats = computed(() => {
  const total = elections.value.length
  const active = elections.value.filter(e => e.status === 'open').length
  const scheduled = elections.value.filter(e => e.status === 'scheduled').length
  const closed = elections.value.filter(e => e.status === 'closed' || e.status === 'archived').length
  return { total, active, scheduled, closed }
})

const filteredElections = computed(() => {
  if (!searchQuery.value) return elections.value
  const q = searchQuery.value.toLowerCase()
  return elections.value.filter(e => 
    e.title.toLowerCase().includes(q) || 
    e.description?.toLowerCase().includes(q)
  )
})

const fetchElections = async () => {
  loading.value = true
  try {
    const response = await electionApi.list()
    elections.value = response.data
  } catch (error) {
    console.error('Failed to fetch elections:', error)
  } finally {
    loading.value = false
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

const filterElections = () => {}

const clearSearch = () => {
  searchQuery.value = ''
}

const viewElection = (uuid) => {
  router.push(`/elections/${uuid}`)
}

const editElection = (uuid) => {
  router.push(`/elections/${uuid}`)
}

const confirmDelete = (election) => {
  if (confirm(`Delete "${election.title}"?`)) {
    deleteElection(election.uuid)
  }
}

const deleteElection = async (uuid) => {
  try {
    await electionApi.delete(uuid)
    await fetchElections()
  } catch (error) {
    console.error('Failed to delete election:', error)
    alert('Failed to delete election. Please try again.')
  }
}

const onElectionCreated = () => {
  showCreateDialog.value = false
  fetchElections()
}

onMounted(() => {
  fetchElections()
})
</script>

<style scoped>
/* Clean table design */
table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
}
thead th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #e9edf2;
}
tbody tr {
  transition: background 0.15s;
}
tbody tr:hover {
  background: #f0fdf4;
}
tbody td {
  vertical-align: middle;
}
/* Badge styling */
:deep(.p-badge) {
  font-weight: 500;
  font-size: 0.65rem;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
}
/* Custom pagination */
.pagination button:hover {
  background: #f1f5f9;
}
.pagination .active {
  background: #e6f7ee;
  color: #0f7d3e;
  border-color: #0f7d3e;
}
</style>
