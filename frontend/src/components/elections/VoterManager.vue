<template>
  <div>
    <!-- Header with animated count -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Eligible Voters</span>
        <Badge 
          :value="voters.length" 
          severity="info" 
          class="transition-all duration-300"
          :class="{ 'scale-110': voters.length > 0 }"
        />
      </div>
      <div class="flex flex-wrap gap-2">
        <Button label="Add Voter" icon="pi pi-plus" size="small" @click="showAddDialog = true" />
        <Button label="Import CSV" icon="pi pi-upload" size="small" severity="secondary" @click="showImportDialog = true" />
      </div>
    </div>

    <!-- Table with horizontal scroll for mobile -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Email</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Index</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">First Name</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Last Name</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Verified By</th>
              <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <transition-group tag="tbody" name="fade" appear>
            <tr 
              v-for="voter in voters" 
              :key="voter.uuid"
              class="border-b border-gray-50 hover:bg-emerald-50/30 transition-colors duration-150"
            >
              <td class="py-3 px-4 font-medium text-gray-800">{{ voter.user.email }}</td>
              <td class="py-3 px-4 text-gray-600">{{ voter.user.index_number || '—' }}</td>
              <td class="py-3 px-4 text-gray-600">{{ voter.user.first_name || '—' }}</td>
              <td class="py-3 px-4 text-gray-600">{{ voter.user.last_name || '—' }}</td>
              <td class="py-3 px-4 text-gray-600">{{ voter.verified_by?.email || '—' }}</td>
              <td class="py-3 px-4 text-center">
                <Button 
                  icon="pi pi-trash" 
                  size="small" 
                  severity="danger" 
                  text 
                  rounded
                  tooltip="Remove"
                  @click="confirmRemove(voter)" 
                />
              </td>
            </tr>
          </transition-group>
          <tbody v-if="voters.length === 0 && !loading">
            <tr>
              <td colspan="6" class="py-12 text-center text-gray-400">
                <i class="pi pi-user-plus text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No eligible voters yet.</p>
                <p class="text-xs text-gray-400 mt-1">Add voters using the "Add Voter" button above.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Voter Dialog -->
    <Dialog v-model:visible="showAddDialog" header="Add Eligible Voter" :modal="true" class="w-full max-w-md">
      <form @submit.prevent="addVoter" class="p-1">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">User Identifier</label>
            <InputText v-model="identifier" class="w-full" placeholder="Email or Index Number" required />
            <p class="text-xs text-gray-400 mt-1">Enter the user's email or index number</p>
          </div>
          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button label="Cancel" severity="secondary" @click="closeAddDialog" />
            <Button label="Add" type="submit" :loading="submitting" />
          </div>
        </div>
      </form>
    </Dialog>

    <!-- Import Dialog -->
    <Dialog v-model:visible="showImportDialog" header="Import Voters (CSV)" :modal="true" class="w-full max-w-md">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">CSV File</label>
          <FileUpload mode="basic" accept=".csv" :maxFileSize="1048576" @select="onFileSelect" />
          <p class="text-xs text-gray-400 mt-1">CSV must have a column: <strong>identifier</strong> (email or index)</p>
          <p class="text-xs text-gray-400 mt-1">Example: identifier<br>student@voterb.com</p>
        </div>
        <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button label="Cancel" severity="secondary" @click="showImportDialog = false" />
          <Button label="Import" :loading="importing" @click="importVoters" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { eligibilityApi } from '@/api/eligibility'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import FileUpload from 'primevue/fileupload'

const props = defineProps({
  electionUuid: { type: String, required: true }
})

const voters = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const identifier = ref('')
const submitting = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

const fetchVoters = async () => {
  loading.value = true
  try {
    const response = await eligibilityApi.list(props.electionUuid)
    voters.value = response.data
  } catch (error) {
    console.error('Failed to fetch voters:', error)
  } finally {
    loading.value = false
  }
}

const addVoter = async () => {
  if (!identifier.value.trim()) return
  submitting.value = true
  try {
    await eligibilityApi.add(props.electionUuid, { user_identifier: identifier.value.trim() })
    identifier.value = ''
    showAddDialog.value = false
    await fetchVoters()
  } catch (error) {
    console.error('Failed to add voter:', error)
    alert(error.response?.data?.error || 'Failed to add voter. Please check the identifier.')
  } finally {
    submitting.value = false
  }
}

const closeAddDialog = () => {
  showAddDialog.value = false
  identifier.value = ''
}

const confirmRemove = (voter) => {
  if (confirm(`Remove ${voter.user.email} from eligible voters?`)) {
    removeVoter(voter.uuid)
  }
}

const removeVoter = async (uuid) => {
  try {
    await eligibilityApi.remove(props.electionUuid, uuid)
    await fetchVoters()
  } catch (error) {
    console.error('Failed to remove voter:', error)
    alert('Failed to remove voter. Please try again.')
  }
}

const onFileSelect = (event) => {
  selectedFile.value = event.files[0]
}

const importVoters = async () => {
  if (!selectedFile.value) {
    alert('Please select a CSV file.')
    return
  }
  importing.value = true
  try {
    const response = await eligibilityApi.import(props.electionUuid, selectedFile.value)
    alert(`Imported ${response.data.created || 0} voters. Errors: ${response.data.errors?.length || 0}`)
    showImportDialog.value = false
    selectedFile.value = null
    await fetchVoters()
  } catch (error) {
    console.error('Failed to import:', error)
    alert('Failed to import. Check file format.')
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  fetchVoters()
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
  transition: background 0.15s, transform 0.2s;
}
tbody tr:hover {
  background: #f0fdf4;
}
tbody td {
  vertical-align: middle;
}
/* Fade animation for rows */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
/* Badge scale on count change */
.badge-animate {
  transition: transform 0.3s ease;
}
</style>
