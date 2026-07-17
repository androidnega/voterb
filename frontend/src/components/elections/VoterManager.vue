<template>
    <div class="voter-manager" :class="{ 'is-readonly': readonly }">
    <aside v-if="!readonly" class="vm-rail" aria-label="Voter sections">
      <button
        type="button"
        class="vm-rail__item"
        :class="{ 'is-active': activePane === 'registers' }"
        @click="activePane = 'registers'"
      >
        <span class="vm-rail__icon" aria-hidden="true"><i class="fas fa-folder-open"></i></span>
        <span class="vm-rail__copy">
          <strong>Registers</strong>
          <small>Lists & categories</small>
        </span>
      </button>
      <button
        type="button"
        class="vm-rail__item"
        :class="{ 'is-active': activePane === 'entries' }"
        :disabled="!selectedRegister"
        @click="activePane = 'entries'"
      >
        <span class="vm-rail__icon" aria-hidden="true"><i class="fas fa-list"></i></span>
        <span class="vm-rail__copy">
          <strong>Entries</strong>
          <small>Import & browse</small>
        </span>
      </button>
      <button
        type="button"
        class="vm-rail__item"
        :class="{ 'is-active': activePane === 'eligible' }"
        @click="activePane = 'eligible'"
      >
        <span class="vm-rail__icon" aria-hidden="true"><i class="fas fa-user-check"></i></span>
        <span class="vm-rail__copy">
          <strong>Eligible</strong>
          <small>Synced voters</small>
        </span>
      </button>
    </aside>

    <div class="vm-main">

    <!-- Registers pane -->
    <div v-if="!readonly && activePane === 'registers'" class="vm-pane">
      <div class="voter-toolbar">
        <p class="vm-lead">
          Create registers and categories, then import voter CSVs into a category.
        </p>
        <button
          v-if="!readonly"
          type="button"
          class="btn btn-primary"
          @click="openRegisterDialog()"
        >
          <i class="fas fa-plus"></i>
          New register
        </button>
      </div>

      <div v-if="loadingRegisters" class="vm-loading">
        <i class="fas fa-spinner fa-spin"></i> Loading registers…
      </div>

      <div v-else-if="!registers.length" class="page-section">
        <EmptyState
          icon="fas fa-folder-open"
          title="No voter registers"
          message="Create a register (e.g. Main Roll) then add categories before importing voters."
        />
      </div>

      <div v-else class="register-grid">
        <article
          v-for="reg in registers"
          :key="reg.uuid"
          class="register-card"
          :class="{ 'is-selected': selectedRegister?.uuid === reg.uuid }"
          @click="selectRegister(reg)"
        >
          <div class="register-card__accent" aria-hidden="true"></div>
          <header class="register-card__head">
            <div class="register-card__identity">
              <span class="register-card__glyph">
                <i class="fas fa-address-book" aria-hidden="true"></i>
              </span>
              <div>
                <h3>{{ reg.name }}</h3>
                <span class="register-card__meta">
                  {{ reg.category_count || 0 }} categories · {{ reg.entry_count || 0 }} voters
                </span>
              </div>
            </div>
            <span v-if="selectedRegister?.uuid === reg.uuid" class="register-card__selected">
              Selected
            </span>
          </header>
          <p class="register-card__desc">{{ reg.description || 'No description' }}</p>

          <div class="category-chips">
            <span
              v-for="cat in reg.categories || []"
              :key="cat.uuid"
              class="category-chip"
            >
              {{ cat.name }}
              <em>{{ cat.entry_count || 0 }}</em>
            </span>
            <span v-if="!(reg.categories || []).length" class="category-empty">No categories yet</span>
          </div>

          <footer v-if="!readonly" class="register-card__foot" @click.stop>
            <button type="button" class="soft-link" @click="openCategoryDialog(reg)">
              <i class="fas fa-plus" aria-hidden="true"></i>
              Category
            </button>
            <button type="button" class="soft-link" @click="selectRegister(reg); activePane = 'entries'">
              <i class="fas fa-upload" aria-hidden="true"></i>
              Import
            </button>
            <button type="button" class="soft-link danger" @click="confirmDeleteRegister(reg)">
              Delete
            </button>
          </footer>
        </article>
      </div>
    </div>

    <!-- Entries pane -->
    <div v-else-if="!readonly && activePane === 'entries'" class="vm-pane">
      <div class="voter-toolbar">
        <div>
          <p class="vm-lead">
            <strong>{{ selectedRegister?.name }}</strong>
            — import CSV into a category or browse entries.
          </p>
        </div>
        <div v-if="!readonly" class="voter-actions">
          <button type="button" class="btn btn-ghost" @click="openCategoryDialog(selectedRegister)">
            Add category
          </button>
          <button type="button" class="btn btn-primary" @click="showImportDialog = true">
            <i class="fas fa-upload"></i>
            Import CSV
          </button>
        </div>
      </div>

      <div class="voter-toolbar">
        <div class="voter-search">
          <i class="fas fa-search" aria-hidden="true"></i>
          <input
            v-model="entrySearch"
            type="text"
            placeholder="Search voter ID or name…"
            autocomplete="off"
          />
        </div>
        <select v-model="entryCategoryFilter" class="filter-select">
          <option value="">All categories</option>
          <option
            v-for="cat in selectedRegister?.categories || []"
            :key="cat.uuid"
            :value="cat.uuid"
          >
            {{ cat.name }}
          </option>
        </select>
      </div>

      <div class="admin-table-wrap voter-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Voter ID</th>
              <th>Name</th>
              <th>Gender</th>
              <th>Category</th>
              <th>Linked account</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in filteredEntries" :key="entry.uuid">
              <td><span class="cell-title mono">{{ formatIndexDisplay(entry.voter_id) }}</span></td>
              <td>{{ entry.full_name }}</td>
              <td class="text-muted">{{ entry.gender || '—' }}</td>
              <td class="text-muted">{{ entry.category?.name || '—' }}</td>
              <td class="text-muted">
                {{ entry.user ? formatIndexDisplay(entry.user.index_number) : '—' }}
              </td>
            </tr>
            <tr v-if="!loadingEntries && !filteredEntries.length">
              <td colspan="5">
                <EmptyState
                  icon="fas fa-file-csv"
                  title="No entries yet"
                  message="Import a CSV with columns voter_id, name, gender into a category."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Approved election voter list. Sub EC receives this read-only view only. -->
    <div v-else class="vm-pane">
      <div class="voter-toolbar">
        <p class="vm-lead">
          Approved voters for this election. The register is managed by Main EC.
        </p>
        <button
          v-if="!readonly"
          type="button"
          class="btn btn-ghost"
          :disabled="loadingEligible"
          @click="fetchEligible"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loadingEligible }"></i>
          Refresh
        </button>
      </div>

      <div class="admin-table-wrap voter-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Index number</th>
              <th>Full name</th>
              <th>Phone number</th>
              <th v-if="!readonly" class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="voter in eligibleVoters" :key="voter.uuid">
              <td>
                <span class="cell-title mono">{{ formatIndexDisplay(voter.user?.index_number) }}</span>
              </td>
              <td>{{ eligibleName(voter) }}</td>
              <td class="text-muted">{{ voter.user?.phone_number || '—' }}</td>
              <td v-if="!readonly">
                <button
                  type="button"
                  class="admin-icon-btn"
                  title="Clear vote (allow revote)"
                  :disabled="clearingUuid === voter.user?.uuid"
                  @click="confirmClearVote(voter)"
                >
                  <i class="fas fa-redo-alt"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!loadingEligible && !eligibleVoters.length">
              <td :colspan="readonly ? 3 : 4">
                <EmptyState
                  icon="fas fa-user-check"
                  title="No eligible voters"
                  message="Main EC has not added approved voters to this election register."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>

    </div>

    <!-- Dialogs -->
    <Dialog v-model:visible="showRegisterDialog" :header="registerForm.uuid ? 'Edit register' : 'New register'" :modal="true" class="w-full max-w-md">
      <form class="dialog-form" @submit.prevent="saveRegister">
        <div>
          <label>Name</label>
          <InputText v-model="registerForm.name" class="w-full" required placeholder="e.g. Main Roll" />
        </div>
        <div>
          <label>Description</label>
          <InputText v-model="registerForm.description" class="w-full" placeholder="Optional" />
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" type="button" @click="showRegisterDialog = false" />
          <Button label="Save" type="submit" :loading="saving" />
        </div>
      </form>
    </Dialog>

    <Dialog v-model:visible="showCategoryDialog" header="Add category" :modal="true" class="w-full max-w-md">
      <form class="dialog-form" @submit.prevent="saveCategory">
        <div>
          <label>Name</label>
          <InputText v-model="categoryForm.name" class="w-full" required placeholder="e.g. Applied Sciences voters" />
        </div>
        <div>
          <label>Description</label>
          <InputText v-model="categoryForm.description" class="w-full" placeholder="Optional" />
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" type="button" @click="showCategoryDialog = false" />
          <Button label="Create" type="submit" :loading="saving" />
        </div>
      </form>
    </Dialog>

    <Dialog v-model:visible="showImportDialog" header="Import voters (CSV)" :modal="true" class="w-full max-w-md">
      <div class="dialog-form">
        <div>
          <label>Category</label>
          <Select
            v-model="importCategoryUuid"
            :options="selectedRegister?.categories || []"
            optionLabel="name"
            optionValue="uuid"
            placeholder="Select category"
            class="w-full"
          />
        </div>
        <div>
          <label>CSV file</label>
          <FileUpload mode="basic" accept=".csv" :maxFileSize="2097152" @select="onFileSelect" />
          <p class="field-hint">
            Required fields: <strong>index</strong>, <strong>full name</strong>. Optional: <strong>phone</strong>.
            Headers can be written as index number / index_number / index, full name / full_name / name,
            phone number / phone_number / phone — column order does not matter.
            <br />Example: index_number,full_name,phone_number<br />SC/2021/PL/001,Ama Mensah,0244123456
          </p>
        </div>
        <p v-if="importResult" class="import-result">
          Created {{ importResult.rows_created }} of {{ importResult.rows_processed }} rows.
          <span v-if="importResult.errors?.length"> {{ importResult.errors.length }} errors.</span>
        </p>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" type="button" @click="showImportDialog = false" />
          <Button label="Import" :loading="importing" @click="runImport" />
        </div>
      </div>
    </Dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { registerApi } from '@/api/registers'
import { eligibilityApi } from '@/api/eligibility'
import { votingApi } from '@/api/voting'
import { parseApiError } from '@/utils/apiError'
import { formatIndexDisplay } from '@/utils/index'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import FileUpload from 'primevue/fileupload'
import EmptyState from '@/components/admin/EmptyState.vue'

const props = defineProps({
  electionUuid: { type: String, required: true },
  readonly: { type: Boolean, default: false },
  initialRegisterUuid: { type: String, default: '' },
  openCreateRegister: { type: Boolean, default: false },
})

const emit = defineEmits(['deep-link-consumed'])

const activePane = ref('registers')
const registers = ref([])
const selectedRegister = ref(null)
const entries = ref([])
const eligibleVoters = ref([])

const loadingRegisters = ref(false)
const loadingEntries = ref(false)
const loadingEligible = ref(false)

const entrySearch = ref('')
const entryCategoryFilter = ref('')

const showRegisterDialog = ref(false)
const showCategoryDialog = ref(false)
const showImportDialog = ref(false)
const registerForm = ref({ uuid: null, name: '', description: '' })
const categoryForm = ref({ name: '', description: '' })
const categoryTarget = ref(null)
const importCategoryUuid = ref(null)
const selectedFile = ref(null)
const importResult = ref(null)
const formError = ref('')
const saving = ref(false)
const importing = ref(false)
const clearingUuid = ref('')

const filteredEntries = computed(() => {
  let list = entries.value
  if (entryCategoryFilter.value) {
    list = list.filter((e) => e.category?.uuid === entryCategoryFilter.value)
  }
  const q = entrySearch.value.trim().toLowerCase()
  if (!q) return list
  return list.filter(
    (e) =>
      (e.voter_id || '').toLowerCase().includes(q) ||
      (e.full_name || '').toLowerCase().includes(q),
  )
})

const eligibleName = (voter) => {
  const u = voter.user || {}
  const name = `${u.first_name || ''} ${u.last_name || ''}`.trim()
  return name || '—'
}

const fetchRegisters = async () => {
  loadingRegisters.value = true
  try {
    const { data } = await registerApi.list(props.electionUuid)
    registers.value = Array.isArray(data) ? data : (data.results || [])
    if (selectedRegister.value) {
      const fresh = registers.value.find((r) => r.uuid === selectedRegister.value.uuid)
      selectedRegister.value = fresh || null
    }
  } catch (error) {
    console.error(error)
  } finally {
    loadingRegisters.value = false
  }
}

const selectRegister = async (reg) => {
  selectedRegister.value = reg
  entryCategoryFilter.value = ''
  await fetchEntries()
}

const fetchEntries = async () => {
  if (!selectedRegister.value) {
    entries.value = []
    return
  }
  loadingEntries.value = true
  try {
    const { data } = await registerApi.listEntries(
      props.electionUuid,
      selectedRegister.value.uuid,
    )
    entries.value = Array.isArray(data) ? data : (data.results || [])
  } catch (error) {
    console.error(error)
    entries.value = []
  } finally {
    loadingEntries.value = false
  }
}

const fetchEligible = async () => {
  loadingEligible.value = true
  try {
    const { data } = await eligibilityApi.list(props.electionUuid)
    eligibleVoters.value = Array.isArray(data) ? data : (data.results || [])
  } catch (error) {
    console.error(error)
    eligibleVoters.value = []
  } finally {
    loadingEligible.value = false
  }
}

const openRegisterDialog = (reg = null) => {
  formError.value = ''
  registerForm.value = reg
    ? { uuid: reg.uuid, name: reg.name, description: reg.description || '' }
    : { uuid: null, name: '', description: '' }
  showRegisterDialog.value = true
}

const saveRegister = async () => {
  saving.value = true
  formError.value = ''
  try {
    if (registerForm.value.uuid) {
      await registerApi.update(props.electionUuid, registerForm.value.uuid, {
        name: registerForm.value.name,
        description: registerForm.value.description,
      })
    } else {
      await registerApi.create(props.electionUuid, {
        name: registerForm.value.name,
        description: registerForm.value.description,
      })
    }
    showRegisterDialog.value = false
    await fetchRegisters()
  } catch (error) {
    formError.value = parseApiError(error) || 'Could not save register.'
  } finally {
    saving.value = false
  }
}

const confirmDeleteRegister = async (reg) => {
  if (!confirm(`Delete register "${reg.name}" and all its entries?`)) return
  try {
    await registerApi.remove(props.electionUuid, reg.uuid)
    if (selectedRegister.value?.uuid === reg.uuid) {
      selectedRegister.value = null
      entries.value = []
    }
    await fetchRegisters()
  } catch (error) {
    alert(parseApiError(error) || 'Could not delete register.')
  }
}

const openCategoryDialog = (reg) => {
  formError.value = ''
  categoryTarget.value = reg
  categoryForm.value = { name: '', description: '' }
  showCategoryDialog.value = true
}

const saveCategory = async () => {
  if (!categoryTarget.value) return
  saving.value = true
  formError.value = ''
  try {
    await registerApi.createCategory(props.electionUuid, categoryTarget.value.uuid, {
      name: categoryForm.value.name,
      description: categoryForm.value.description,
    })
    showCategoryDialog.value = false
    await fetchRegisters()
    if (selectedRegister.value?.uuid === categoryTarget.value.uuid) {
      const fresh = registers.value.find((r) => r.uuid === categoryTarget.value.uuid)
      if (fresh) selectedRegister.value = fresh
    }
  } catch (error) {
    formError.value = parseApiError(error) || 'Could not create category.'
  } finally {
    saving.value = false
  }
}

const onFileSelect = (event) => {
  selectedFile.value = event.files?.[0] || null
  importResult.value = null
}

const runImport = async () => {
  formError.value = ''
  if (!selectedRegister.value) {
    formError.value = 'Select a register first.'
    return
  }
  if (!importCategoryUuid.value) {
    formError.value = 'Select a category.'
    return
  }
  if (!selectedFile.value) {
    formError.value = 'Choose a CSV file.'
    return
  }
  importing.value = true
  try {
    const { data } = await registerApi.importCsv(
      props.electionUuid,
      selectedRegister.value.uuid,
      { categoryUuid: importCategoryUuid.value, file: selectedFile.value },
    )
    importResult.value = data
    await fetchRegisters()
    await fetchEntries()
    await fetchEligible()
  } catch (error) {
    formError.value = parseApiError(error) || 'Import failed.'
  } finally {
    importing.value = false
  }
}

const confirmClearVote = async (voter) => {
  const userUuid = voter.user?.uuid
  if (!userUuid) return
  if (!confirm('Clear this student’s vote so they can vote again?')) return
  clearingUuid.value = userUuid
  try {
    await votingApi.clearStudentVote(props.electionUuid, userUuid)
  } catch (error) {
    alert(parseApiError(error) || 'Could not clear vote.')
  } finally {
    clearingUuid.value = ''
  }
}

watch(activePane, (pane) => {
  if (pane === 'entries' && selectedRegister.value) fetchEntries()
  if (pane === 'eligible') fetchEligible()
})

const applyDeepLink = async () => {
  const targetUuid = props.initialRegisterUuid
  if (targetUuid) {
    const match = registers.value.find((r) => r.uuid === targetUuid)
    if (match) {
      await selectRegister(match)
      activePane.value = 'registers'
    }
  } else if (registers.value.length && !selectedRegister.value) {
    await selectRegister(registers.value[0])
  }

  if (props.openCreateRegister && !props.readonly) {
    activePane.value = 'registers'
    openRegisterDialog()
  }

  if (props.initialRegisterUuid || props.openCreateRegister) {
    emit('deep-link-consumed')
  }
}

watch(
  () => [props.initialRegisterUuid, props.openCreateRegister],
  async ([uuid, create]) => {
    if (!uuid && !create) return
    if (!registers.value.length) await fetchRegisters()
    await applyDeepLink()
  },
)

onMounted(async () => {
  if (props.readonly) {
    activePane.value = 'eligible'
    await fetchEligible()
    return
  }
  await fetchRegisters()
  if (props.initialRegisterUuid || props.openCreateRegister) {
    await applyDeepLink()
  } else if (registers.value.length) {
    await selectRegister(registers.value[0])
  }
})
</script>

<style scoped>
.voter-manager {
  display: grid;
  grid-template-columns: 13.5rem minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}

.voter-manager.is-readonly {
  grid-template-columns: minmax(0, 1fr);
}

@media (max-width: 800px) {
  .voter-manager {
    grid-template-columns: 1fr;
  }
}

.vm-rail {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.45rem;
  border-radius: 1rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
  position: sticky;
  top: 0.75rem;
}

@media (max-width: 800px) {
  .vm-rail {
    flex-direction: row;
    overflow-x: auto;
    position: static;
  }
}

.vm-rail__item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.65rem;
  align-items: center;
  width: 100%;
  text-align: left;
  padding: 0.7rem 0.75rem;
  border: 1px solid transparent;
  border-radius: 0.8rem;
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  cursor: pointer;
  transition: all 0.15s ease;
}

@media (max-width: 800px) {
  .vm-rail__item {
    min-width: 10.5rem;
  }
}

.vm-rail__item:hover:not(:disabled) {
  background: #fff;
  color: var(--vb-ink, #1c1c1c);
}

.vm-rail__item.is-active {
  background: #fff;
  border-color: var(--vb-accent-border, #c5d4bc);
  color: var(--vb-ink, #1c1c1c);
  box-shadow: 0 6px 16px var(--vb-accent-shadow, rgba(61, 79, 68, 0.1));
}

.vm-rail__item:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.vm-rail__icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.6rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.78rem;
}

.vm-rail__item.is-active .vm-rail__icon {
  background: var(--vb-accent, #3d4f44);
  color: #fff;
}

.vm-rail__copy {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.vm-rail__copy strong {
  font-size: 0.82rem;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.vm-rail__copy small {
  font-size: 0.68rem;
  color: var(--vb-muted, #8a8a8a);
}

.vm-main {
  min-width: 0;
}

.vm-lead {
  margin: 0;
  font-size: 0.84rem;
  color: var(--vb-muted, #8a8a8a);
  line-height: 1.45;
  max-width: 38rem;
}

.voter-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.voter-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.voter-search {
  position: relative;
  flex: 1;
  min-width: 12rem;
}

.voter-search i {
  position: absolute;
  left: 0.8rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.75rem;
}

.voter-search input {
  width: 100%;
  padding: 0.6rem 0.85rem 0.6rem 2.15rem;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.8rem;
  font-size: 0.84rem;
  background: #fff;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.voter-search input:focus {
  outline: none;
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.14));
}

.filter-select {
  padding: 0.55rem 0.8rem;
  border-radius: 0.8rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
  font-size: 0.82rem;
}

.register-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
}

@media (min-width: 800px) {
  .register-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.register-card {
  position: relative;
  padding: 1.05rem 1.15rem 1rem;
  border-radius: 1.15rem;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  cursor: pointer;
  overflow: hidden;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.register-card:hover {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 10px 28px rgba(28, 28, 28, 0.05);
  transform: translateY(-1px);
}

.register-card.is-selected {
  border-color: var(--vb-accent, #3d4f44);
  box-shadow:
    0 0 0 1px var(--vb-accent, #3d4f44),
    0 14px 30px var(--vb-accent-shadow, rgba(61, 79, 68, 0.14));
}

.register-card__accent {
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg, var(--vb-gradient-from, #a3b18a), var(--vb-gradient-to, #3d4f44));
  opacity: 0;
  transition: opacity 0.18s ease;
}

.register-card.is-selected .register-card__accent,
.register-card:hover .register-card__accent {
  opacity: 1;
}

.register-card__head {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: flex-start;
}

.register-card__identity {
  display: flex;
  gap: 0.7rem;
  align-items: flex-start;
  min-width: 0;
}

.register-card__glyph {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--vb-accent-soft, #e8efe6);
  color: var(--vb-accent, #3d4f44);
  flex-shrink: 0;
}

.register-card__head h3 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--vb-ink, #1c1c1c);
}

.register-card__meta {
  display: block;
  margin-top: 0.2rem;
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
}

.register-card__selected {
  flex-shrink: 0;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--vb-accent, #3d4f44);
  color: #fff;
  font-size: 0.68rem;
  font-weight: 750;
}

.register-card__desc {
  margin: 0.7rem 0 0.75rem;
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
  line-height: 1.45;
}

.category-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}

.category-chip em {
  font-style: normal;
  color: var(--vb-muted, #8a8a8a);
  font-variant-numeric: tabular-nums;
}

.category-empty {
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
}

.register-card__foot {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem;
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--vb-line, #ebeae4);
}

.soft-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: none;
  background: none;
  padding: 0;
  color: var(--vb-accent, #3d4f44);
  font-size: 0.78rem;
  font-weight: 750;
  cursor: pointer;
}

.soft-link.danger {
  color: #be123c;
  margin-left: auto;
}

.dialog-form {
  display: grid;
  gap: 0.85rem;
}

.dialog-form label {
  display: block;
  margin-bottom: 0.3rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.25rem;
}

.field-hint,
.import-result {
  margin: 0.35rem 0 0;
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
  line-height: 1.45;
}

.form-error {
  margin: 0;
  color: #be123c;
  font-size: 0.8rem;
}

.vm-loading {
  padding: 1.5rem;
  text-align: center;
  color: var(--vb-muted, #8a8a8a);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8rem;
}

.vm-pane {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  animation: pane-in 0.22s ease;
}

@keyframes pane-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
