<template>
  <div>
    <!-- Header with count -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Candidates</span>
        <Badge :value="candidates.length" severity="info" />
      </div>
      <Button label="Add Candidate" icon="pi pi-plus" size="small" @click="showDialog = true" />
    </div>

    <!-- Clean Table -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Name</th>
            <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Department</th>
            <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Position</th>
            <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
            <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Ballot #</th>
            <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="candidate in candidates" 
            :key="candidate.uuid"
            class="border-b border-gray-50 hover:bg-emerald-50/30 transition-colors duration-150"
          >
            <td class="py-3 px-4 font-medium text-gray-800">{{ candidate.full_name }}</td>
            <td class="py-3 px-4 text-gray-600">{{ candidate.department || '—' }}</td>
            <td class="py-3 px-4 text-gray-600">{{ candidate.position?.title || '—' }}</td>
            <td class="py-3 px-4">
              <Badge :value="candidate.status" :severity="getStatusSeverity(candidate.status)" class="capitalize" />
            </td>
            <td class="py-3 px-4 text-gray-600">{{ candidate.ballot_number || '—' }}</td>
            <td class="py-3 px-4 text-center">
              <div class="flex items-center justify-center gap-1">
                <Button 
                  v-if="candidate.status === 'pending'" 
                  icon="pi pi-check" 
                  size="small" 
                  severity="success" 
                  text 
                  rounded
                  tooltip="Approve"
                  @click="approveCandidate(candidate.uuid)" 
                />
                <Button 
                  v-if="candidate.status === 'pending'" 
                  icon="pi pi-times" 
                  size="small" 
                  severity="danger" 
                  text 
                  rounded
                  tooltip="Reject"
                  @click="rejectCandidate(candidate.uuid)" 
                />
                <Button 
                  icon="pi pi-trash" 
                  size="small" 
                  severity="danger" 
                  text 
                  rounded
                  tooltip="Delete"
                  @click="confirmDelete(candidate)" 
                />
              </div>
            </td>
          </tr>
          <tr v-if="candidates.length === 0 && !loading">
            <td colspan="6" class="py-12 text-center text-gray-400">
              <i class="pi pi-users text-3xl block mb-2 text-gray-200"></i>
              No candidates added yet.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Candidate Dialog -->
    <Dialog v-model:visible="showDialog" header="Add Candidate" :modal="true" class="w-full max-w-md">
      <form @submit.prevent="submitCandidate" class="p-1">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Position</label>
            <Dropdown 
              v-model="form.position_uuid" 
              :options="positions" 
              optionLabel="title" 
              optionValue="uuid" 
              placeholder="Select position" 
              class="w-full" 
              required 
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <InputText v-model="form.full_name" class="w-full" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <InputText v-model="form.department" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Manifesto</label>
            <Textarea v-model="form.manifesto" rows="3" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Ballot Number</label>
            <InputNumber v-model="form.ballot_number" class="w-full" :min="1" />
          </div>
          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button label="Cancel" severity="secondary" @click="showDialog = false" />
            <Button label="Add Candidate" type="submit" :loading="submitting" />
          </div>
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { candidateApi } from '@/api/candidates'
import { electionApi } from '@/api/elections'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'

const props = defineProps({
  electionUuid: { type: String, required: true }
})

const candidates = ref([])
const positions = ref([])
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)

const form = ref({
  position_uuid: null,
  full_name: '',
  department: '',
  manifesto: '',
  ballot_number: null
})

const fetchCandidates = async () => {
  loading.value = true
  try {
    const response = await candidateApi.list(props.electionUuid)
    candidates.value = response.data
  } catch (error) {
    console.error('Failed to fetch candidates:', error)
  } finally {
    loading.value = false
  }
}

const fetchPositions = async () => {
  try {
    const response = await electionApi.getPositions(props.electionUuid)
    positions.value = response.data
  } catch (error) {
    console.error('Failed to fetch positions:', error)
  }
}

const getStatusSeverity = (status) => {
  const map = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    withdrawn: 'secondary'
  }
  return map[status] || 'secondary'
}

const submitCandidate = async () => {
  submitting.value = true
  try {
    await candidateApi.create(props.electionUuid, form.value)
    showDialog.value = false
    form.value = { position_uuid: null, full_name: '', department: '', manifesto: '', ballot_number: null }
    await fetchCandidates()
  } catch (error) {
    console.error('Failed to create candidate:', error)
    alert('Failed to create candidate. Please try again.')
  } finally {
    submitting.value = false
  }
}

const approveCandidate = async (candidateUuid) => {
  if (confirm('Approve this candidate?')) {
    try {
      await candidateApi.approve(props.electionUuid, candidateUuid)
      await fetchCandidates()
    } catch (error) {
      console.error('Failed to approve candidate:', error)
      alert('Failed to approve candidate. Please try again.')
    }
  }
}

const rejectCandidate = async (candidateUuid) => {
  if (confirm('Reject this candidate?')) {
    try {
      await candidateApi.reject(props.electionUuid, candidateUuid)
      await fetchCandidates()
    } catch (error) {
      console.error('Failed to reject candidate:', error)
      alert('Failed to reject candidate. Please try again.')
    }
  }
}

const confirmDelete = (candidate) => {
  if (confirm(`Delete candidate "${candidate.full_name}"?`)) {
    deleteCandidate(candidate.uuid)
  }
}

const deleteCandidate = async (candidateUuid) => {
  try {
    await candidateApi.delete(props.electionUuid, candidateUuid)
    await fetchCandidates()
  } catch (error) {
    console.error('Failed to delete candidate:', error)
    alert('Failed to delete candidate. Please try again.')
  }
}

onMounted(() => {
  fetchCandidates()
  fetchPositions()
})
</script>

<style scoped>
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
</style>
