<template>
  <div>
    <!-- Header with count -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Candidates</span>
        <Badge :value="candidates.length" severity="info" />
      </div>
      <Button v-if="!readonly" label="Add Candidate" icon="pi pi-plus" size="small" @click="showDialog = true" />
    </div>

    <div class="admin-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Photo</th>
            <th>Name</th>
            <th>Department</th>
            <th>Position</th>
            <th>Status</th>
            <th>Ballot #</th>
            <th v-if="!readonly" class="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="candidate in candidates" :key="candidate.uuid">
            <td>
              <img
                v-if="candidate.photo"
                :src="resolveMediaUrl(candidate.photo)"
                :alt="candidate.full_name"
                class="candidate-photo"
              />
              <div v-else class="candidate-photo candidate-photo--fallback">
                {{ candidate.full_name?.charAt(0) }}
              </div>
            </td>
            <td><span class="cell-title">{{ candidate.full_name }}</span></td>
            <td>{{ candidateDepartment(candidate) }}</td>
            <td>{{ candidate.position?.title || '—' }}</td>
            <td>
              <span class="admin-badge" :class="statusBadgeClass(candidate.status)">{{ candidate.status }}</span>
            </td>
            <td class="mono">{{ candidate.ballot_number || '—' }}</td>
            <td v-if="!readonly">
              <div class="row-actions">
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
            <td :colspan="readonly ? 6 : 7">
              <EmptyState icon="fas fa-user-tie" title="No candidates" message="Add candidates for each position." />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Candidate Dialog -->
    <Dialog
      v-model:visible="showDialog"
      header="Add Candidate"
      :modal="true"
      class="candidate-dialog w-full max-w-md"
      :draggable="false"
    >
      <form @submit.prevent="submitCandidate" class="dialog-form candidate-form">
        <div class="photo-field">
          <label class="photo-picker" :class="{ 'photo-picker--has': photoPreview }">
            <img v-if="photoPreview" :src="photoPreview" alt="Preview" class="photo-picker__img" />
            <span v-else class="photo-picker__placeholder">
              <i class="fas fa-camera" aria-hidden="true"></i>
              <span>Photo</span>
            </span>
            <input
              ref="photoInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              @change="onPhotoSelect"
            />
          </label>
          <div class="photo-field__meta">
            <span class="photo-field__label">Profile photo</span>
            <span class="photo-field__hint">JPG or PNG, max 5 MB</span>
            <button v-if="photoFile" type="button" class="photo-field__clear" @click="clearPhoto">Remove</button>
          </div>
        </div>

        <div class="form-grid">
          <div>
            <label>Position</label>
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
            <label>Ballot #</label>
            <InputNumber v-model="form.ballot_number" class="w-full" :min="1" />
          </div>
        </div>

        <div>
          <label>Full name</label>
          <InputText v-model="form.full_name" class="w-full" required />
        </div>

        <FacultyDepartmentSelect
          v-model:faculty-uuid="form.faculty_uuid"
          v-model:department-uuid="form.department_uuid"
          required
        />

        <div>
          <label>Manifesto</label>
          <Textarea v-model="form.manifesto" rows="2" class="w-full manifesto-field" />
        </div>

        <p v-if="submitting && photoFile" class="upload-status">
          <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
          {{ uploadStatusText }}
        </p>

        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" @click="closeDialog" />
          <Button label="Add Candidate" type="submit" :loading="submitting" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { candidateApi } from '@/api/candidates'
import { resolveMediaUrl } from '@/utils/media'
import { electionApi } from '@/api/elections'
import { uploadQueue } from '@/utils/uploadQueue'
import EmptyState from '@/components/admin/EmptyState.vue'
import FacultyDepartmentSelect from '@/components/academic/FacultyDepartmentSelect.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'

const props = defineProps({
  electionUuid: { type: String, required: true },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['updated'])

const MAX_PHOTO_MB = 5

const candidates = ref([])
const positions = ref([])
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const photoFile = ref(null)
const photoPreview = ref(null)
const photoInput = ref(null)

const form = ref({
  position_uuid: null,
  full_name: '',
  faculty_uuid: null,
  department_uuid: null,
  manifesto: '',
  ballot_number: null,
})

const uploadStatusText = computed(() =>
  uploadQueue.size > 1 ? 'Queued — uploading photo…' : 'Uploading photo…'
)

const resetForm = () => {
  form.value = {
    position_uuid: null,
    full_name: '',
    faculty_uuid: null,
    department_uuid: null,
    manifesto: '',
    ballot_number: null,
  }
}

const candidateDepartment = (candidate) =>
  candidate.academic_department?.name || candidate.department || '—'

const clearPhoto = () => {
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoFile.value = null
  photoPreview.value = null
  if (photoInput.value) photoInput.value.value = ''
}

const closeDialog = () => {
  showDialog.value = false
  clearPhoto()
  resetForm()
}

const onPhotoSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  if (file.size > MAX_PHOTO_MB * 1024 * 1024) {
    alert(`Image must be under ${MAX_PHOTO_MB} MB`)
    clearPhoto()
    return
  }

  photoFile.value = file
  photoPreview.value = URL.createObjectURL(file)
}

const fetchCandidates = async () => {
  loading.value = true
  try {
    const response = await candidateApi.list(props.electionUuid)
    candidates.value = response.data
    emit('updated', candidates.value.length)
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

const statusBadgeClass = (status) => {
  const map = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    withdrawn: 'neutral',
  }
  return map[status] || 'neutral'
}

const submitCandidate = async () => {
  if (!form.value.department_uuid) {
    alert('Please select a faculty and department.')
    return
  }

  submitting.value = true
  try {
    await candidateApi.create(props.electionUuid, form.value, photoFile.value)
    closeDialog()
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
.candidate-photo {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 9999px;
  object-fit: cover;
  border: 1px solid #e2e8f0;
}

.candidate-photo--fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
}

.candidate-form {
  gap: 0.65rem;
}

.photo-field {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.photo-picker {
  flex-shrink: 0;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 0.5rem;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s, background 0.15s;
}

.photo-picker:hover {
  border-color: #94a3b8;
  background: #f1f5f9;
}

.photo-picker--has {
  border-style: solid;
}

.photo-picker__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-picker__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  color: #64748b;
  font-size: 0.6rem;
  font-weight: 600;
}

.photo-picker__placeholder i {
  font-size: 0.85rem;
}

.photo-field__meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.photo-field__label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #334155;
}

.photo-field__hint {
  font-size: 0.72rem;
  color: #94a3b8;
}

.photo-field__clear {
  align-self: flex-start;
  margin-top: 0.15rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #dc2626;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.photo-field__clear:hover {
  text-decoration: underline;
}

.manifesto-field {
  resize: vertical;
  min-height: 3.5rem;
  max-height: 6rem;
}

.upload-status {
  margin: 0;
  font-size: 0.75rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
</style>

<style>
.candidate-dialog .p-dialog-content {
  padding: 0.75rem 1rem 1rem;
}

.candidate-dialog .p-dialog-header {
  padding: 0.85rem 1rem 0.5rem;
}
</style>
