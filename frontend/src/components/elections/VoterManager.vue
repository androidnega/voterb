<template>
  <div class="voter-manager">
    <div class="voter-toolbar">
      <div class="voter-search">
        <i class="fas fa-search" aria-hidden="true"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by index or name…"
          autocomplete="off"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="voter-search-clear"
          title="Clear search"
          @click="searchQuery = ''"
        >
          <i class="fas fa-times" aria-hidden="true"></i>
        </button>
      </div>
      <div v-if="!readonly" class="voter-actions">
        <Button label="Add" icon="pi pi-plus" size="small" @click="showAddDialog = true" />
        <Button label="Import" icon="pi pi-upload" size="small" severity="secondary" @click="showImportDialog = true" />
      </div>
    </div>

    <p v-if="searchQuery" class="voter-search-meta">
      {{ filteredVoters.length }} of {{ voters.length }} voters
    </p>

    <div class="admin-table-wrap voter-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Index</th>
            <th>First name</th>
            <th>Last name</th>
            <th>Verified by</th>
            <th v-if="!readonly" class="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="voter in filteredVoters" :key="voter.uuid">
            <td><span class="cell-title mono">{{ formatIndexDisplay(voter.user.index_number) }}</span></td>
            <td>{{ voter.user.first_name || '—' }}</td>
            <td>{{ voter.user.last_name || '—' }}</td>
            <td class="text-muted">{{ verifiedByLabel(voter) }}</td>
            <td v-if="!readonly">
              <div class="row-actions">
                <button
                  type="button"
                  class="admin-icon-btn danger"
                  title="Remove"
                  @click="confirmRemove(voter)"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredVoters.length === 0 && !loading">
            <td :colspan="readonly ? 4 : 5">
              <EmptyState
                :icon="searchQuery ? 'fas fa-search' : 'fas fa-user-plus'"
                :title="searchQuery ? 'No matches' : 'No eligible voters'"
                :message="searchQuery ? 'Try a different index or name.' : 'Add voters using the buttons above or import a CSV.'"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Dialog v-model:visible="showAddDialog" header="Add voter" :modal="true" class="w-full max-w-md">
      <form @submit.prevent="addVoter" class="dialog-form">
        <div>
          <label>Index number</label>
          <InputText
            v-model="identifier"
            class="w-full"
            placeholder="e.g. SC2021PL001"
            required
          />
          <p class="field-hint">
            Enter the student's index. Slashes are optional. New indexes are added automatically.
          </p>
        </div>
        <p v-if="addError" class="form-error">{{ addError }}</p>
        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" @click="closeAddDialog" />
          <Button label="Add" type="submit" :loading="submitting" />
        </div>
      </form>
    </Dialog>

    <Dialog v-model:visible="showImportDialog" header="Import voters (CSV)" :modal="true" class="w-full max-w-md">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">CSV file</label>
          <FileUpload mode="basic" accept=".csv" :maxFileSize="1048576" @select="onFileSelect" />
          <p class="text-xs text-gray-400 mt-1">CSV must have an <strong>index_number</strong> column</p>
          <p class="text-xs text-gray-400 mt-1">Example: index_number,first_name,last_name<br>SC2021PL001,Abena,Mensah</p>
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
import { ref, computed, onMounted } from 'vue'
import { eligibilityApi } from '@/api/eligibility'
import { parseApiError } from '@/utils/apiError'
import { formatIndexDisplay, normalizeIndex } from '@/utils/index'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import FileUpload from 'primevue/fileupload'
import EmptyState from '@/components/admin/EmptyState.vue'

const props = defineProps({
  electionUuid: { type: String, required: true },
  readonly: { type: Boolean, default: false },
})

const voters = ref([])
const loading = ref(false)
const searchQuery = ref('')
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const identifier = ref('')
const submitting = ref(false)
const addError = ref('')
const importing = ref(false)
const selectedFile = ref(null)

const filteredVoters = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return voters.value

  const qIndex = normalizeIndex(q)
  return voters.value.filter((voter) => {
    const user = voter.user || {}
    const index = normalizeIndex(user.index_number)
    const first = (user.first_name || '').toLowerCase()
    const last = (user.last_name || '').toLowerCase()
    const full = `${first} ${last}`.trim()

    return (
      index.includes(qIndex)
      || first.includes(q)
      || last.includes(q)
      || full.includes(q)
    )
  })
})

const verifiedByLabel = (voter) => {
  const by = voter.verified_by
  if (!by) return '—'
  if (by.email) return by.email
  return formatIndexDisplay(by.index_number)
}

const normalizeIdentifierInput = (value) => {
  const trimmed = value.trim()
  if (!trimmed) return ''
  if (trimmed.includes('/')) return trimmed
  const match = trimmed.match(/^([A-Za-z]{2,})(\d{4})([A-Za-z]{2,})(\d+)$/i)
  if (match) {
    return `${match[1].toUpperCase()}/${match[2]}/${match[3].toUpperCase()}/${match[4]}`
  }
  return trimmed
}

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
  const normalized = normalizeIdentifierInput(identifier.value)
  if (!normalized) return
  submitting.value = true
  addError.value = ''
  try {
    await eligibilityApi.add(props.electionUuid, { user_identifier: normalized })
    closeAddDialog()
    await fetchVoters()
  } catch (error) {
    console.error('Failed to add voter:', error)
    addError.value = parseApiError(
      error,
      'Could not add this voter. Enter a valid index number.'
    )
  } finally {
    submitting.value = false
  }
}

const closeAddDialog = () => {
  showAddDialog.value = false
  identifier.value = ''
  addError.value = ''
}

const confirmRemove = (voter) => {
  const label = formatIndexDisplay(voter.user.index_number) || 'this voter'
  if (confirm(`Remove ${label} from eligible voters?`)) {
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
.voter-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  background: #fafbfc;
}

.voter-search {
  position: relative;
  flex: 1;
  min-width: 11rem;
}

.voter-search i.fa-search {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 0.72rem;
  pointer-events: none;
}

.voter-search input {
  width: 100%;
  height: 2rem;
  padding: 0 1.85rem 0 1.85rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  font-size: 0.78rem;
  color: #334155;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.voter-search input:focus {
  outline: none;
  border-color: #5eead4;
  box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.12);
}

.voter-search input::placeholder {
  color: #94a3b8;
}

.voter-search-clear {
  position: absolute;
  right: 0.35rem;
  top: 50%;
  transform: translateY(-50%);
  width: 1.35rem;
  height: 1.35rem;
  border: none;
  border-radius: 9999px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.6rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voter-search-clear:hover {
  background: #e2e8f0;
  color: #334155;
}

.voter-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.voter-search-meta {
  margin: 0;
  padding: 0.35rem 1rem 0;
  font-size: 0.72rem;
  color: #94a3b8;
}

.voter-table-wrap {
  border-top: none;
}

.field-hint {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  color: #94a3b8;
  line-height: 1.4;
}

.form-error {
  margin: 0;
  font-size: 0.8125rem;
  color: #dc2626;
  line-height: 1.4;
}
</style>
