<template>
  <div class="candidate-manager">
    <div class="candidate-toolbar">
      <div class="candidate-toolbar__left">
        <span class="candidate-toolbar__title">Candidates</span>
        <span class="candidate-count">{{ candidates.length }}</span>
        <span v-if="isLocked" class="lock-pill" title="Candidates are locked while the election is live or closed">
          <i class="fas fa-lock" aria-hidden="true"></i>
          Locked
        </span>
      </div>
      <button
        v-if="canMutate && !showForm"
        type="button"
        class="btn btn-primary"
        @click="openForm"
      >
        <i class="fas fa-plus"></i>
        Add Candidate
      </button>
    </div>

    <Transition name="form-slide">
      <form
        v-if="canMutate && showForm"
        class="candidate-inline-form"
        @submit.prevent="submitCandidate"
      >
        <div class="candidate-inline-form__head">
          <h3>Add candidate</h3>
          <button type="button" class="form-close" title="Close" @click="closeForm">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="name-photo-row">
          <label class="photo-picker" :class="{ 'photo-picker--has': photoPreview }" title="Profile photo">
            <img v-if="photoPreview" :src="photoPreview" alt="Preview" class="photo-picker__img" />
            <span v-else class="photo-picker__placeholder">
              <i class="fas fa-camera" aria-hidden="true"></i>
            </span>
            <input
              ref="photoInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              @change="onPhotoSelect"
            />
          </label>
          <div class="name-photo-row__fields">
            <label>Full name</label>
            <InputText v-model="form.full_name" class="w-full" required placeholder="Candidate name" />
            <button v-if="photoFile" type="button" class="photo-field__clear" @click="clearPhoto">Remove photo</button>
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
          <label>Manifesto <span class="optional-label">optional</span></label>
          <Textarea v-model="form.manifesto" rows="1" class="w-full manifesto-field" />
        </div>

        <p v-if="submitting && photoFile" class="upload-status">
          <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
          {{ uploadStatusText }}
        </p>

        <div class="candidate-inline-form__actions">
          <button type="button" class="btn btn-ghost" :disabled="submitting" @click="closeForm">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
            {{ submitting ? 'Saving…' : 'Add Candidate' }}
          </button>
        </div>
      </form>
    </Transition>

    <div class="admin-table-wrap">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Photo</th>
            <th>Name</th>
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
            <td>{{ candidate.position?.title || '—' }}</td>
            <td>
              <span class="admin-badge" :class="statusBadgeClass(candidate.status)">{{ candidate.status }}</span>
            </td>
            <td class="mono">{{ candidate.ballot_number || '—' }}</td>
            <td v-if="!readonly">
              <div class="row-actions">
                <template v-if="canMutate">
                  <Button
                    icon="pi pi-pencil"
                    size="small"
                    severity="secondary"
                    text
                    rounded
                    v-tooltip.top="'Edit'"
                    @click="openEdit(candidate)"
                  />
                  <Button
                    v-if="candidate.status === 'pending'"
                    icon="pi pi-check"
                    size="small"
                    severity="success"
                    text
                    rounded
                    v-tooltip.top="'Approve'"
                    @click="approveCandidate(candidate.uuid)"
                  />
                  <Button
                    v-if="candidate.status === 'pending'"
                    icon="pi pi-times"
                    size="small"
                    severity="danger"
                    text
                    rounded
                    v-tooltip.top="'Reject'"
                    @click="rejectCandidate(candidate.uuid)"
                  />
                  <Button
                    icon="pi pi-trash"
                    size="small"
                    severity="danger"
                    text
                    rounded
                    v-tooltip.top="'Delete'"
                    @click="confirmDelete(candidate)"
                  />
                </template>
                <span v-else class="lock-icon" title="Locked">
                  <i class="fas fa-lock" aria-hidden="true"></i>
                </span>
              </div>
            </td>
          </tr>
          <tr v-if="candidates.length === 0 && !loading">
            <td :colspan="readonly ? 5 : 6">
              <EmptyState icon="fas fa-user-tie" title="No candidates" message="Add candidates for each position." />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Dialog
      v-model:visible="showEditDialog"
      header="Edit candidate"
      :modal="true"
      class="w-full max-w-md"
    >
      <form class="dialog-form" @submit.prevent="saveEdit">
        <div class="name-photo-row">
          <label class="photo-picker" :class="{ 'photo-picker--has': editPhotoPreview || editCandidate?.photo }" title="Profile photo">
            <img
              v-if="editPhotoPreview || editCandidate?.photo"
              :src="editPhotoPreview || resolveMediaUrl(editCandidate.photo)"
              alt="Preview"
              class="photo-picker__img"
            />
            <span v-else class="photo-picker__placeholder">
              <i class="fas fa-camera" aria-hidden="true"></i>
            </span>
            <input type="file" accept="image/jpeg,image/png,image/webp" hidden @change="onEditPhotoSelect" />
          </label>
          <div class="name-photo-row__fields">
            <label>Full name</label>
            <InputText v-model="editForm.full_name" class="w-full" required />
          </div>
        </div>
        <div>
          <label>Ballot #</label>
          <InputNumber v-model="editForm.ballot_number" class="w-full" :min="1" />
        </div>
        <div>
          <label>Manifesto</label>
          <Textarea v-model="editForm.manifesto" rows="3" class="w-full" />
        </div>
        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" :disabled="editing" @click="showEditDialog = false">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="editing">
            <i v-if="editing" class="fas fa-spinner fa-spin"></i>
            Save
          </button>
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
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'

const props = defineProps({
  electionUuid: { type: String, required: true },
  readonly: { type: Boolean, default: false },
  electionStatus: { type: String, default: 'draft' },
})

const emit = defineEmits(['updated'])

const MAX_PHOTO_MB = 5
const LOCKED_STATUSES = new Set(['open', 'paused', 'closed', 'archived'])

const candidates = ref([])
const positions = ref([])
const loading = ref(false)
const submitting = ref(false)
const showForm = ref(false)
const photoFile = ref(null)
const photoPreview = ref(null)
const photoInput = ref(null)

const showEditDialog = ref(false)
const editCandidate = ref(null)
const editForm = ref({ full_name: '', manifesto: '', ballot_number: null })
const editPhotoFile = ref(null)
const editPhotoPreview = ref(null)
const editing = ref(false)

const form = ref({
  position_uuid: null,
  full_name: '',
  manifesto: '',
  ballot_number: null,
})

const isLocked = computed(() => LOCKED_STATUSES.has(props.electionStatus))
const canMutate = computed(() => !props.readonly && !isLocked.value)

const uploadStatusText = computed(() =>
  uploadQueue.size > 1 ? 'Queued — uploading photo…' : 'Uploading photo…'
)

const resetForm = () => {
  form.value = {
    position_uuid: null,
    full_name: '',
    manifesto: '',
    ballot_number: null,
  }
}

const clearPhoto = () => {
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoFile.value = null
  photoPreview.value = null
  if (photoInput.value) photoInput.value.value = ''
}

const openForm = () => {
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false
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
  if (!form.value.position_uuid) {
    alert('Please select a position.')
    return
  }
  submitting.value = true
  try {
    await candidateApi.create(props.electionUuid, form.value, photoFile.value)
    closeForm()
    await fetchCandidates()
  } catch (error) {
    console.error('Failed to create candidate:', error)
    alert('Failed to create candidate. Please try again.')
  } finally {
    submitting.value = false
  }
}

const openEdit = (candidate) => {
  editCandidate.value = candidate
  editForm.value = {
    full_name: candidate.full_name || '',
    manifesto: candidate.manifesto || '',
    ballot_number: candidate.ballot_number,
  }
  if (editPhotoPreview.value) URL.revokeObjectURL(editPhotoPreview.value)
  editPhotoFile.value = null
  editPhotoPreview.value = null
  showEditDialog.value = true
}

const onEditPhotoSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  if (file.size > MAX_PHOTO_MB * 1024 * 1024) {
    alert(`Image must be under ${MAX_PHOTO_MB} MB`)
    return
  }
  if (editPhotoPreview.value) URL.revokeObjectURL(editPhotoPreview.value)
  editPhotoFile.value = file
  editPhotoPreview.value = URL.createObjectURL(file)
}

const saveEdit = async () => {
  if (!editCandidate.value) return
  editing.value = true
  try {
    await candidateApi.update(
      props.electionUuid,
      editCandidate.value.uuid,
      {
        full_name: editForm.value.full_name,
        manifesto: editForm.value.manifesto,
        ballot_number: editForm.value.ballot_number,
      },
      editPhotoFile.value,
    )
    showEditDialog.value = false
    await fetchCandidates()
  } catch (error) {
    console.error('Failed to update candidate:', error)
    alert('Failed to update candidate. Please try again.')
  } finally {
    editing.value = false
  }
}

const approveCandidate = async (candidateUuid) => {
  if (!confirm('Approve this candidate?')) return
  try {
    await candidateApi.approve(props.electionUuid, candidateUuid)
    await fetchCandidates()
  } catch (error) {
    console.error('Failed to approve candidate:', error)
    alert('Failed to approve candidate. Please try again.')
  }
}

const rejectCandidate = async (candidateUuid) => {
  if (!confirm('Reject this candidate?')) return
  try {
    await candidateApi.reject(props.electionUuid, candidateUuid)
    await fetchCandidates()
  } catch (error) {
    console.error('Failed to reject candidate:', error)
    alert('Failed to reject candidate. Please try again.')
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
.candidate-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.candidate-toolbar__left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.candidate-toolbar__title {
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--vb-ink, #1c1c1c);
}

.candidate-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.45rem;
  height: 1.45rem;
  padding: 0 0.4rem;
  border-radius: 9999px;
  background: #fff8eb;
  color: #b45309;
  font-size: 0.72rem;
  font-weight: 750;
}

.lock-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #c2410c;
  font-size: 0.72rem;
  font-weight: 750;
}

.lock-icon {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.85rem;
}

.candidate-inline-form,
.dialog-form {
  display: grid;
  gap: 0.75rem;
}

.candidate-inline-form {
  margin-bottom: 1.1rem;
  padding: 1.1rem 1.15rem;
  background:
    linear-gradient(180deg, #fffefb 0%, var(--vb-panel, #f7f6f2) 100%);
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 1.1rem;
  box-shadow: 0 8px 24px rgba(28, 28, 28, 0.04);
}

.candidate-inline-form__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.candidate-inline-form__head h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.form-close {
  width: 1.85rem;
  height: 1.85rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 0.55rem;
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  cursor: pointer;
  transition: all 0.15s ease;
}

.form-close:hover {
  background: #fff;
  border-color: var(--vb-line, #ebeae4);
  color: var(--vb-ink, #1c1c1c);
}

.candidate-inline-form label,
.dialog-form label {
  display: block;
  margin-bottom: 0.28rem;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}

.candidate-inline-form__actions,
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.35rem;
}

.name-photo-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.name-photo-row__fields {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.photo-picker {
  flex-shrink: 0;
  width: 3.25rem;
  height: 3.25rem;
  margin-top: 1.2rem;
  border-radius: 0.85rem;
  border: 1.5px dashed var(--vb-accent-border, #c5d4bc);
  background: #fff;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.photo-picker:hover {
  border-color: var(--vb-accent, #3d4f44);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.12));
}

.photo-picker--has {
  border-style: solid;
  border-color: var(--vb-accent-border, #c5d4bc);
}

.photo-picker__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-picker__placeholder {
  color: var(--vb-muted, #8a8a8a);
}

.photo-field__clear {
  align-self: flex-start;
  font-size: 0.68rem;
  font-weight: 700;
  color: #be123c;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.optional-label {
  font-weight: 560;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.7rem;
}

.manifesto-field {
  resize: vertical;
  min-height: 2.35rem;
}

.upload-status {
  margin: 0;
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.candidate-photo {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.7rem;
  object-fit: cover;
  border: 1px solid var(--vb-line, #ebeae4);
}

.candidate-photo--fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff8eb;
  color: #b45309;
  font-size: 0.75rem;
  font-weight: 800;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
}

.form-slide-enter-active,
.form-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.form-slide-enter-from,
.form-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 560px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
